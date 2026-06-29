from dataclasses import dataclass
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import UUID
import os

# Core Ontology
from aware_code_ontology.code.code import Code

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_overlay import (
    ObjectConfigGraphOverlay,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)

# Meta API
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)

# Content Runtime
from aware_content.builder import get_text

# Code Runtime
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter

# Meta Runtime
from aware_meta.graph.config.render.renderer_language import (
    ObjectConfigGraphRendererLanguage,
    ObjectConfigGraphRendererPolicy,
)
from aware_meta.graph.config.model_bootstrap import get_node_function_config

# Aware Utils
from aware_utils.logging import logger


OBJECT_CONFIG_GRAPH_RENDER_CANDIDATE_SCOPE_CONTRACT_VERSION = (
    "aware.meta.object-config-graph-render-candidate-scope.v1"
)


def _elapsed_s(started_at: float) -> float:
    return round(max(perf_counter() - started_at, 0.0), 6)


@dataclass
class RenderResult:
    """Result of rendering a single meta object or group of objects."""

    meta_objects: list[Any]  # List of meta objects rendered into this file
    code: Code  # The generated code object
    file_path: Path  # Path where this code should be written
    meta_types: list[
        str
    ]  # Types of meta objects in this file ('class', 'enum', or 'function')
    class_to_class_config_map: dict[UUID, ClassConfig] | None = (
        None  # Mapping from class ID to ClassConfig
    )

    def __post_init__(self):
        if self.class_to_class_config_map is None:
            self.class_to_class_config_map = {}


@dataclass(frozen=True, slots=True)
class ObjectConfigGraphRenderCandidateScope:
    """Output-file scope for renderer invocation pruning."""

    candidate_paths: frozenset[str]
    contract_version: str = OBJECT_CONFIG_GRAPH_RENDER_CANDIDATE_SCOPE_CONTRACT_VERSION

    @classmethod
    def from_paths(
        cls,
        *,
        candidate_paths: Iterable[str | Path],
        output_directory: Path,
    ) -> "ObjectConfigGraphRenderCandidateScope":
        normalized_paths: set[str] = set()
        resolved_output_directory = output_directory.resolve()
        for candidate_path in candidate_paths:
            normalized_paths.update(
                _candidate_scope_path_keys(
                    path=Path(candidate_path),
                    output_directory=resolved_output_directory,
                )
            )
        return cls(candidate_paths=frozenset(normalized_paths))

    def allows_file(
        self,
        *,
        file_path: Path,
        output_directory: Path,
    ) -> bool:
        if not self.candidate_paths:
            return False
        file_keys = _candidate_scope_path_keys(
            path=file_path,
            output_directory=output_directory.resolve(),
        )
        return bool(self.candidate_paths & file_keys)


class ObjectConfigGraphRenderer:
    """
    High-level renderer that coordinates the rendering of an entire ObjectConfigGraph
    to a set of files based on the specified language and layout strategy.

    This class is language-agnostic and delegates the actual code generation
    to a language-specific plugin.
    """

    def __init__(
        self,
        renderer_language: ObjectConfigGraphRendererLanguage,
        output_directory: Path,
        overwrite: bool = True,
        external_class_lookup: dict[UUID, ClassConfig] | None = None,
    ):
        """
        Initialize the GraphRenderer.

        Args:
            language_plugin: The language-specific plugin to use for code generation
            output_directory: Directory where files will be written
            overwrite: Whether to overwrite existing files
        """
        self.renderer_language = renderer_language
        self.output_directory = Path(output_directory)
        self.overwrite = overwrite
        self.external_class_lookup = external_class_lookup or {}
        self.external_graphs = []
        self._last_changed_files: list[Path] = []
        self._last_render_phase_timings: dict[str, float] = {}
        self._last_collect_render_phase_timings: dict[str, float] = {}

    @property
    def last_changed_files(self) -> list[Path]:
        return list(self._last_changed_files)

    def get_render_phase_timings(self) -> dict[str, float]:
        return dict(self._last_render_phase_timings)

    def set_policy(self, policy: ObjectConfigGraphRendererPolicy | None) -> None:
        """Inject a language-specific renderer policy (DTO vs ORM, etc.)."""
        self.renderer_language.set_policy(policy)

    def set_profile_inputs(self, profile_inputs: dict[str, object]) -> None:
        """Inject generic profile-scoped payloads resolved by env-artifacts."""
        self.renderer_language.bind_profile_inputs(profile_inputs)

    def set_external_class_lookup(
        self, external_class_lookup: dict[UUID, ClassConfig]
    ) -> None:
        """Set the external class lookup for the renderer."""
        self.external_class_lookup = external_class_lookup
        self.renderer_language.set_external_class_lookup(external_class_lookup)

    def set_external_graphs(self, external_graphs: list[ObjectConfigGraph]) -> None:
        """Set the external graphs for the renderer."""
        self.external_graphs = external_graphs
        self.renderer_language.set_external_graphs(external_graphs)

        # Provide external class lookup for cross-OCG type imports.
        external_class_lookup: dict[UUID, ClassConfig] = {}
        for g in external_graphs:
            for node in g.object_config_graph_nodes:
                if (
                    node.type == ObjectConfigGraphNodeType.class_
                    and node.class_config is not None
                ):
                    external_class_lookup[node.class_config.id] = node.class_config
        self.set_external_class_lookup(external_class_lookup)

    def render_graph(
        self,
        graph: ObjectConfigGraph,
        base_class_module: str | None = None,
        base_class_name: str | None = None,
        *,
        candidate_paths: Iterable[str | Path] | None = None,
    ) -> list[Path]:
        """
        Render the entire graph to files using a two-phase approach.

        Phase 1: Collect all renderings by grouping meta objects by file
        Phase 2: Write renderings to files

        Args:
            graph: The ObjectConfigGraph to render

        Returns:
            List of paths to the files that were written
        """
        total_started_at = perf_counter()
        phase_timings: dict[str, float] = {}
        self._last_render_phase_timings = {}
        self._last_collect_render_phase_timings = {}

        self.renderer_language.clear_warnings()

        # Allow layout strategies to derive deterministic state from the graph (optional).
        # This is required for languages that can introduce synthetic nodes (e.g. SQL join tables)
        # that do not have code provenance / template paths.
        phase_started_at = perf_counter()
        self.renderer_language.layout_strategy.bind_graph(graph)
        phase_timings["layout_bind_graph"] = _elapsed_s(phase_started_at)

        # Optional: allow language renderers to bind deterministic, graph-level state (annotations, indexes, etc.)
        # BEFORE file emission begins.
        #
        # This avoids per-file heuristics and keeps `.aware`/OCG annotations as SSOT.
        phase_started_at = perf_counter()
        self.renderer_language.bind_object_config_graph(graph)
        phase_timings["bind_object_config_graph"] = _elapsed_s(phase_started_at)

        phase_started_at = perf_counter()
        candidate_scope = (
            ObjectConfigGraphRenderCandidateScope.from_paths(
                candidate_paths=candidate_paths,
                output_directory=self.output_directory,
            )
            if candidate_paths is not None
            else None
        )
        phase_timings["candidate_scope"] = _elapsed_s(phase_started_at)

        # Phase 1: Collect all renderings
        phase_started_at = perf_counter()
        render_results = self._collect_render_results(
            graph,
            base_class_module,
            base_class_name,
            candidate_scope=candidate_scope,
        )
        phase_timings["collect_render_results"] = _elapsed_s(phase_started_at)
        phase_timings.update(self._last_collect_render_phase_timings)

        # Phase 2: Write renderings to files
        phase_started_at = perf_counter()
        written_files, changed_files = self._write_render_results(render_results)
        phase_timings["write_render_results"] = _elapsed_s(phase_started_at)
        self._last_changed_files = changed_files
        phase_started_at = perf_counter()
        self._log_written_files(written_files)
        phase_timings["log_written_files"] = _elapsed_s(phase_started_at)
        phase_timings["total"] = _elapsed_s(total_started_at)
        self._last_render_phase_timings = phase_timings
        return written_files

    def _namespace_from_output_path(self, file_path: Path) -> str:
        """Derive a namespace from the rendered file path."""

        try:
            relative = file_path.resolve().relative_to(self.output_directory.resolve())
        except ValueError:
            relative = file_path
        parent_parts = [
            part.strip().removesuffix("_")
            for part in relative.parent.parts
            if part.strip() and part != "."
        ]
        if parent_parts:
            return ".".join(parent_parts)
        return "default"

    def _collect_render_results(
        self,
        graph: ObjectConfigGraph,
        base_class_module: str | None = None,
        base_class_name: str | None = None,
        *,
        candidate_scope: ObjectConfigGraphRenderCandidateScope | None = None,
    ) -> list[RenderResult]:
        """
        Phase 1: Group meta objects by file and render each file.

        Args:
            graph: The ObjectConfigGraph to render
            base_class_module: Module name for the base class
            base_class_name: Name of the base class
        Returns:
            List of RenderResult objects
        """
        phase_timings: dict[str, float] = {}
        self._last_collect_render_phase_timings = phase_timings
        results = []

        logger.info(
            f"Collecting render results for {graph.name} with: "
            f"{len(graph.object_config_graph_nodes)} nodes"
        )

        # Group meta objects by file path based on layout strategy
        files_to_objects: dict[
            Path, list[ClassConfig | EnumConfig | FunctionConfig]
        ] = {}
        files_to_types: dict[Path, list[str]] = {}
        files_to_class_config_map: dict[Path, dict[UUID, ClassConfig]] = {}

        requires_metadata_hydration = (
            self.renderer_language.requires_graph_metadata_hydration()
        )
        if requires_metadata_hydration:
            phase_started_at = perf_counter()
            # Ensure parent/descriptor metadata is linked before rendering.
            self._hydrate_graph_metadata(graph)
            phase_timings["collect.metadata_hydration"] = _elapsed_s(phase_started_at)

        if self.renderer_language.renders_only_extra_output_paths():
            phase_started_at = perf_counter()
            results = self._collect_extra_output_render_results(
                base_class_module=base_class_module,
                base_class_name=base_class_name,
                candidate_scope=candidate_scope,
            )
            phase_timings["collect.extra_output_render_results"] = _elapsed_s(
                phase_started_at
            )
            phase_timings["collect.total"] = sum(phase_timings.values())
            return results

        # Group meta objects by file based on layout strategy
        phase_started_at = perf_counter()
        self._group_objects_by_file(
            graph, files_to_objects, files_to_types, files_to_class_config_map
        )
        phase_timings["collect.group_objects_by_file"] = _elapsed_s(phase_started_at)
        if candidate_scope is not None:
            phase_started_at = perf_counter()
            self._filter_grouped_files_by_candidate_scope(
                files_to_objects=files_to_objects,
                files_to_types=files_to_types,
                files_to_class_config_map=files_to_class_config_map,
                candidate_scope=candidate_scope,
            )
            phase_timings["collect.filter_candidate_scope"] = _elapsed_s(
                phase_started_at
            )

        # Render each file
        phase_started_at = perf_counter()
        for file_path, meta_objects in files_to_objects.items():
            try:
                namespace = self._namespace_from_output_path(file_path)

                # Create code object and writer
                code = self.renderer_language.create_empty_code()
                section_index = CodeSectionBuilderIndex()

                # Get the class to object config mapping for this file
                class_to_class_config_map = files_to_class_config_map.get(file_path, {})

                # Render the file
                with CodeSectionWriter(
                    code, section_index, indent_size=self.renderer_language.indent
                ) as writer:
                    # Let the language plugin emit all content with schema information and class-to-object mapping
                    self.renderer_language.emit_file(
                        meta_objects,
                        writer,
                        namespace,
                        class_to_class_config_map,
                        base_class_module,
                        base_class_name,
                    )

                # Add to results
                results.append(
                    RenderResult(
                        meta_objects=meta_objects,
                        code=code,
                        file_path=file_path,
                        meta_types=files_to_types[file_path],
                        class_to_class_config_map=class_to_class_config_map,
                    )
                )
                logger.debug(
                    f"Rendered file {file_path} with {len(meta_objects)} meta objects"
                )
            except Exception as e:
                logger.error(f"Error rendering file {file_path}: {e}")
                import traceback

                logger.error(traceback.format_exc())
                raise e

        phase_timings["collect.emit_files"] = _elapsed_s(phase_started_at)
        phase_timings["collect.total"] = sum(phase_timings.values())
        return results

    def _collect_extra_output_render_results(
        self,
        base_class_module: str | None = None,
        base_class_name: str | None = None,
        *,
        candidate_scope: ObjectConfigGraphRenderCandidateScope | None = None,
    ) -> list[RenderResult]:
        """Render only language-declared graph-level output files."""

        results: list[RenderResult] = []
        for file_path in self.renderer_language.extra_output_paths():
            if candidate_scope is not None and not candidate_scope.allows_file(
                file_path=file_path,
                output_directory=self.output_directory,
            ):
                continue

            code = self.renderer_language.create_empty_code()
            section_index = CodeSectionBuilderIndex()
            with CodeSectionWriter(
                code,
                section_index,
                indent_size=self.renderer_language.indent,
            ) as writer:
                self.renderer_language.emit_file(
                    [],
                    writer,
                    "default",
                    {},
                    base_class_module,
                    base_class_name,
                )

            results.append(
                RenderResult(
                    meta_objects=[],
                    code=code,
                    file_path=file_path,
                    meta_types=["generated"],
                    class_to_class_config_map={},
                )
            )
        return results

    def _filter_grouped_files_by_candidate_scope(
        self,
        *,
        files_to_objects: dict[Path, list[Any]],
        files_to_types: dict[Path, list[str]],
        files_to_class_config_map: dict[Path, dict[UUID, ClassConfig]],
        candidate_scope: ObjectConfigGraphRenderCandidateScope,
    ) -> None:
        skipped_paths: list[Path] = []
        for file_path in tuple(files_to_objects):
            if candidate_scope.allows_file(
                file_path=file_path,
                output_directory=self.output_directory,
            ):
                continue
            files_to_objects.pop(file_path, None)
            files_to_types.pop(file_path, None)
            files_to_class_config_map.pop(file_path, None)
            skipped_paths.append(file_path)
        if skipped_paths:
            logger.info(
                "Renderer candidate scope skipped %d files under %s",
                len(skipped_paths),
                self.output_directory,
            )

    def _group_objects_by_file(
        self,
        graph: ObjectConfigGraph,
        files_to_objects: dict[Path, list[Any]],
        files_to_types: dict[Path, list[str]],
        files_to_class_config_map: dict[Path, dict[UUID, ClassConfig]],
    ) -> None:
        """
        Group meta objects by file path based on layout strategy.

        Args:
            graph: The ObjectConfigGraph to render
            files_to_objects: Dictionary to populate with file paths -> meta objects
            files_to_types: Dictionary to populate with file paths -> meta types
            files_to_class_object_map: Dictionary to populate with file paths -> class ID to ObjectConfig mapping
        """
        # Collect classes to resolve parent classes
        classes_dict: dict[UUID, ClassConfig] = {}
        class_lookup: dict[UUID, ClassConfig] = dict(self.external_class_lookup)

        # Seed lookup with external graph objects/classes
        for ext_cls in self.external_class_lookup.values():
            # Track external objects so relationship targets resolve
            class_lookup.setdefault(ext_cls.id, ext_cls)

        # Get local nodes (object configs, enum configs, function configs)
        enum_configs: list[EnumConfig] = []
        class_configs: list[ClassConfig] = []
        function_configs: list[FunctionConfig] = []
        relationship_configs: list[ClassConfigRelationship] = []
        relationship_ids: set[UUID] = set()
        for graph_node in graph.object_config_graph_nodes:
            if graph_node.type == ObjectConfigGraphNodeType.class_:
                class_config = graph_node.class_config
                if class_config is None:
                    raise ValueError(
                        f"Class config is None for graph node {graph_node.id}"
                    )
                class_configs.append(class_config)
                class_lookup[class_config.id] = class_config
            elif graph_node.type == ObjectConfigGraphNodeType.enum:
                enum_config = graph_node.enum_config
                if enum_config is None:
                    raise ValueError(
                        f"Enum config is None for graph node {graph_node.id}"
                    )
                enum_configs.append(enum_config)
            elif graph_node.type == ObjectConfigGraphNodeType.function:
                function_config = get_node_function_config(graph_node)
                if function_config is None:
                    raise ValueError(
                        f"Function config is None for graph node {graph_node.id}"
                    )
                function_configs.append(function_config)
            elif graph_node.type == ObjectConfigGraphNodeType.relationship:
                rel = graph_node.class_config_relationship
                if rel is None:
                    raise ValueError(
                        f"Relationship config is None for graph node {graph_node.id}"
                    )
                relationship_configs.append(rel)
                relationship_ids.add(rel.id)

        # Cross-OCG relationships are stored in `object_config_graph_relationships` (not nodes) so
        # renderers can still:
        # - derive edge-backed sugar views (@property) for association relationships
        # - classify synthetic edge helper attributes under "# Edges"
        for ocg_rel in graph.object_config_graph_relationships:
            for rel in ocg_rel.class_config_relationships:
                if rel.id in relationship_ids:
                    continue
                relationship_configs.append(rel)
                relationship_ids.add(rel.id)

        # Sort by name before rendering for deterministic output
        enum_configs.sort(key=lambda x: x.name)
        class_configs.sort(key=lambda x: x.name)
        function_configs.sort(key=lambda x: x.name)
        relationship_configs.sort(key=lambda r: (str(r.class_config_id), str(r.id)))

        # 1. Process enum configs
        for enum_config in enum_configs:
            try:
                # Determine output path
                file_path = self.renderer_language.layout_strategy.get_enum_file_path(
                    enum_config
                )

                # Add to file mapping
                if file_path not in files_to_objects:
                    files_to_objects[file_path] = []
                    files_to_types[file_path] = []
                    files_to_class_config_map[file_path] = {}

                files_to_objects[file_path].append(enum_config)
                files_to_types[file_path].append("enum")
            except Exception as e:
                logger.error(
                    f"Error determining file path for enum {enum_config.name}: {e}"
                )
                raise e

        # 2. Process object configs and their class configs
        for class_config in class_configs:
            # Process all class configs for this object config
            # Determine output path based on class config
            file_path = self.renderer_language.layout_strategy.get_class_file_path(
                class_config
            )

            # Add to file mapping
            if file_path not in files_to_objects:
                files_to_objects[file_path] = []
                files_to_types[file_path] = []
                files_to_class_config_map[file_path] = {}

            # Add ClassConfig
            files_to_objects[file_path].append(class_config)
            files_to_types[file_path].append("class")

            # Create mapping from class ID to ObjectConfig
            files_to_class_config_map[file_path][class_config.id] = class_config

        # 2c. Attach relationships to the source class file (so renderers can emit relationship sections).
        for rel in relationship_configs:
            src = class_lookup.get(rel.class_config_id)
            if src is None:
                logger.warning(
                    f"Skipping relationship {rel.id}: source class {rel.class_config_id} not found"
                )
                continue
            file_path = self.renderer_language.layout_strategy.get_class_file_path(src)
            if file_path not in files_to_objects:
                files_to_objects[file_path] = []
                files_to_types[file_path] = []
                files_to_class_config_map[file_path] = {}
            files_to_objects[file_path].append(rel)
            files_to_types[file_path].append("relationship")

        # 3. Process function configs
        class_owned_function_ids: set[UUID] = set()
        for class_config in class_configs:
            for function_link in class_config.class_config_function_configs:
                function_id = function_link.function_config_id
                if function_id is None and function_link.function_config is not None:
                    function_id = function_link.function_config.id
                if function_id is not None:
                    class_owned_function_ids.add(function_id)

        for func_config in function_configs:
            # Class-owned functions are emitted through their owning class rails.
            # Standalone function files are only for truly global functions.
            if func_config.id in class_owned_function_ids:
                continue
            try:
                # Determine output path
                file_path = (
                    self.renderer_language.layout_strategy.get_function_file_path(
                        func_config
                    )
                )

                # Add to file mapping
                if file_path not in files_to_objects:
                    files_to_objects[file_path] = []
                    files_to_types[file_path] = []
                    files_to_class_config_map[file_path] = {}

                files_to_objects[file_path].append(func_config)
                files_to_types[file_path].append("function")
            except Exception as e:
                logger.error(
                    f"Error determining file path for function {func_config.name}: {e}"
                )
                raise e

        # 3c. Allow language renderers to request extra output files that are not anchored
        # to a specific meta object node (e.g., runtime handler registries).
        for extra_path in self.renderer_language.extra_output_paths():
            if extra_path not in files_to_objects:
                files_to_objects[extra_path] = []
                files_to_types[extra_path] = []
                files_to_class_config_map[extra_path] = {}
            if "generated" not in files_to_types[extra_path]:
                files_to_types[extra_path].append("generated")

        # 3b. Ensure class_to_class_config_map for each file can resolve ANY class
        # to its owning ClassConfig (not just classes rendered in that file).
        # This is required so renderers can reliably classify edge attributes using
        # ClassConfig.is_edge even when the edge class lives in a different file.
        global_class_to_class_config: dict[UUID, ClassConfig] = dict(
            self.external_class_lookup
        )
        for class_config in class_configs:
            global_class_to_class_config[class_config.id] = class_config
        for mapping in files_to_class_config_map.values():
            mapping.update(global_class_to_class_config)

        # 4. Resolve parent classes
        for class_config in classes_dict.values():
            if class_config.parent_class_id and class_config.parent_class is None:
                parent_class_config = classes_dict.get(class_config.parent_class_id)
                if not parent_class_config:
                    raise ValueError(
                        f"Parent class {class_config.parent_class_id} not found for class {class_config.name}"
                    )
                class_config.parent_class = parent_class_config

    def _hydrate_graph_metadata(self, graph: ObjectConfigGraph) -> None:
        """Resolve parent_class pointers and (best-effort) descriptor class refs across the graph.

        Canonical note:
        - The config-world SSOT is class-first; attribute descriptors may carry class_config_id
          without an embedded class_config object (exclude=True).
        - Renderers often need the class_config *object* to compute file paths/imports.
        - This hydrates class_config pointers for CLASS leaves where possible, without any heuristics.
        """

        class_lookup: dict[UUID, ClassConfig] = dict(self.external_class_lookup)
        function_nodes: list[FunctionConfig] = []

        # External classes
        for ext_cls in self.external_class_lookup.values():
            class_lookup[ext_cls.id] = ext_cls

        for node in graph.object_config_graph_nodes:
            if node.type == ObjectConfigGraphNodeType.class_:
                class_config = node.class_config
                if not class_config:
                    raise ValueError(f"Class config is None for graph node {node.id}")
                class_lookup[class_config.id] = class_config
            elif node.type == ObjectConfigGraphNodeType.function:
                node_function_config = get_node_function_config(node)
                if node_function_config is not None:
                    function_nodes.append(node_function_config)

        # 1) Parent pointers
        for class_cfg in class_lookup.values():
            if class_cfg.parent_class_id and class_cfg.parent_class is None:
                parent = class_lookup.get(class_cfg.parent_class_id)
                if parent:
                    class_cfg.parent_class = parent

        # 2) Descriptor class refs (strict by id; no guessing)
        def hydrate_descriptor(node: AttributeTypeDescriptor) -> None:
            if (
                node.kind == AttributeTypeDescriptorKind.class_
                and node.class_config is None
                and node.class_config_id
            ):
                resolved = class_lookup.get(node.class_config_id)
                if resolved is not None:
                    node.class_config = resolved
            for lk in node.child_links:
                hydrate_descriptor(lk.child)

        for class_cfg in class_lookup.values():
            for attr_link in class_cfg.class_config_attribute_configs:
                hydrate_descriptor(attr_link.attribute_config.type_descriptor)
            for fn_link in class_cfg.class_config_function_configs:
                for (
                    fn_attr_link
                ) in fn_link.function_config.function_config_attribute_configs:
                    hydrate_descriptor(fn_attr_link.attribute_config.type_descriptor)

        for fn_cfg in function_nodes:
            for fn_attr_link in fn_cfg.function_config_attribute_configs:
                hydrate_descriptor(fn_attr_link.attribute_config.type_descriptor)

    def _write_render_results(
        self, render_results: list[RenderResult]
    ) -> tuple[list[Path], list[Path]]:
        """
        Phase 2: Write collected renderings to files.

        Args:
            render_results: List of RenderResult objects

        Returns:
            List of paths to files that were written
        """
        self.output_directory.mkdir(parents=True, exist_ok=True)
        written_files = []
        changed_files = []

        for result in render_results:
            file_path = result.file_path
            # Layout strategies sometimes return absolute paths; avoid re-prepending output_directory
            if file_path.is_absolute():
                try:
                    output_path = file_path.relative_to(self.output_directory)
                    output_path = self.output_directory / output_path
                except ValueError:
                    output_path = file_path
            else:
                output_path = self.output_directory / file_path
            try:
                # Get the source code from Code object
                source_code = get_text(result.code.content_part_text)

                # Skip empty renderings to avoid clobbering existing files.
                # Language plugins use an empty Code object as a sentinel for
                # "no-op" files (e.g., Dart functions renderer on enum-only files).
                if not source_code.strip():
                    logger.debug(
                        f"Skipping write for {output_path} because generated source is empty"
                    )
                    continue

                # Create parent directory
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Check if file exists and handle preservation of user code
                existing: str | None = None
                if output_path.exists():
                    if not self.overwrite:
                        logger.warning(
                            f"Skipping existing file: {output_path} due to overwrite=False"
                        )
                        written_files.append(output_path)
                        continue
                    try:
                        existing = output_path.read_text(encoding="utf-8")
                        if existing == source_code:
                            # Avoid rewriting identical content (keeps mtimes stable).
                            written_files.append(output_path)
                            continue
                    except Exception:
                        raise

                source_code = self.renderer_language.canonicalize_generated_source(
                    relative_path=file_path,
                    source=source_code,
                )

                if existing is not None:
                    if existing == source_code:
                        # Avoid rewriting canonical-equivalent content (keeps mtimes stable).
                        written_files.append(output_path)
                        continue
                    self.renderer_language.validate_existing_output(
                        relative_path=file_path,
                        output_path=output_path,
                        generated_source=source_code,
                        existing_source=existing,
                    )

                # Write the file
                with output_path.open("w", encoding="utf-8") as f:
                    f.write(source_code)

                written_files.append(output_path)
                changed_files.append(output_path)

            except Exception as e:
                logger.error(f"Error writing file {output_path}: {e}")
                import traceback

                logger.error(traceback.format_exc())
                raise e
        return written_files, changed_files

    def _log_written_files(self, files: list[Path]) -> None:
        if not files:
            return
        if os.getenv("AWARE_RENDER_VERBOSE_FILES") == "1":
            for path in files:
                logger.info("Wrote file: %s", path)
            return

        total = len(files)
        head_counts: dict[str, int] = defaultdict(int)
        for path in files:
            try:
                rel = path.relative_to(self.output_directory)
            except ValueError:
                rel = path
            head = rel.parts[0] if rel.parts else str(rel)
            head_counts[head] += 1

        top_entries = sorted(head_counts.items(), key=lambda kv: kv[0])[:10]
        summary = ", ".join(f"{head}={count}" for head, count in top_entries)
        if summary:
            logger.info(
                "Rendered %d files to %s [%s]", total, self.output_directory, summary
            )
        else:
            logger.info("Rendered %d files to %s", total, self.output_directory)

    def get_warnings(self) -> list[str]:
        return self.renderer_language.get_warnings()

    def set_import_overrides(self, import_overrides: dict[str, str]) -> None:
        self.renderer_language.import_overrides = import_overrides

    def get_import_overrides(self) -> dict[str, str] | None:
        return self.renderer_language.import_overrides

    def clear_import_overrides(self) -> None:
        self.renderer_language.import_overrides = {}

    def set_language_overlay(self, overlay: ObjectConfigGraphOverlay) -> None:
        return self.renderer_language.set_language_overlay(overlay)


def _candidate_scope_path_keys(
    *,
    path: Path,
    output_directory: Path,
) -> set[str]:
    keys: set[str] = set()
    if path.is_absolute():
        resolved_path = path.resolve()
        keys.add(resolved_path.as_posix())
        try:
            keys.add(resolved_path.relative_to(output_directory).as_posix())
        except ValueError:
            pass
        return keys

    relative_path = Path(path.as_posix())
    keys.add(relative_path.as_posix())
    keys.add((output_directory / relative_path).resolve().as_posix())
    return keys
