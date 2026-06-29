from pathlib import Path
from abc import ABC

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta.graph.config.render.layout_strategy_template import (
    ObjectConfigGraphRenderLayoutStrategyTemplate,
)
from aware_utils.string_transform import to_snake_case

from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)

from aware_meta.graph.config.namespace.bundle import ObjectConfigGraphNamespaceBundle
from aware_meta.graph.config.namespace.builder import (
    build_namespace_bundle_from_ocg_topology,
)
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.render.generated_ocg_node_manifest import (
    GeneratedObjectConfigGraphNodeManifest,
    GeneratedObjectConfigGraphNodeFilePolicy,
)
from typing_extensions import override


class SQLLayoutStrategy(ObjectConfigGraphRenderLayoutStrategy, ABC):
    """Base layout strategy for SQL outputs (Postgres-first)."""

    def __init__(
        self,
        base_dir: Path,
        generated_ocg_node_manifest: (
            GeneratedObjectConfigGraphNodeManifest | None
        ) = None,
        import_root: str | None = None,
    ) -> None:
        # import_root unused for SQL, but keep signature consistent across languages.
        super().__init__(
            base_dir,
            generated_ocg_node_manifest=generated_ocg_node_manifest,
            import_root=import_root,
        )

    @property
    @override
    def language(self) -> CodeLanguage:
        return CodeLanguage.sql

    @override
    def get_file_extension(self) -> str:
        return ".sql"


class SQLLayoutStrategyNamespace(ObjectConfigGraphRenderLayoutStrategyTemplate):
    """
    Namespace-driven SQL layout strategy (B).

    Contract:
    - SQL outputs must be layoutable without any CodeSection provenance because runtime→SQL can
      synthesize classes (join tables) that have no source file.
    - We therefore compute file paths from the graph's namespace bundle.
    """

    def __init__(
        self,
        base_dir: Path,
        template_paths: dict[str, Path] | None = None,
        entity_template_paths: dict[str, Path] | None = None,
        generated_ocg_node_manifest: (
            GeneratedObjectConfigGraphNodeManifest | None
        ) = None,
        import_root: str | None = None,
    ) -> None:
        ObjectConfigGraphRenderLayoutStrategyTemplate.__init__(
            self,
            base_dir=base_dir,
            template_paths=template_paths,
            entity_template_paths=entity_template_paths,
            generated_ocg_node_manifest=generated_ocg_node_manifest,
            import_root=import_root,
        )
        self._namespace_bundle: ObjectConfigGraphNamespaceBundle | None = None
        self._graph: ObjectConfigGraph | None = None
        # Canonical-resolved entity template paths (meta-id keyed) passed from the pipeline.
        # Keys are expected to be stringified UUIDs.
        self._entity_template_paths: dict[str, Path] = dict(self.entity_template_paths)
        # Precomputed anchor directories for synthetic join classes (join_class_id -> dir)
        self._join_anchor_dir_by_class_id: dict[str, Path] = {}
        self._generated_ocg_node_manifest: (
            GeneratedObjectConfigGraphNodeManifest | None
        ) = generated_ocg_node_manifest
        # Optional canonical container grouping: code_id -> preferred file path.
        # This allows SQL to replicate canonical `.aware` file boundaries (enum + class in one file)
        # when code provenance exists, while remaining compatible with synthetic classes (no code_id).
        self._preferred_file_by_code_id: dict[str, Path] = {}

    @property
    @override
    def language(self) -> CodeLanguage:
        return CodeLanguage.sql

    @override
    def get_file_extension(self) -> str:
        return ".sql"

    @override
    def bind_graph(self, graph: ObjectConfigGraph) -> None:
        super().bind_graph(graph)

        # Compute bundle from topology so SQL can layout generated entities without code provenance.
        self._namespace_bundle = build_namespace_bundle_from_ocg_topology(ocg=graph)
        self._graph = graph

        # Synthetic join placement MUST be driven by explicit transformer intent.
        # (No inference via relationship probing in the layout layer.)
        join_anchor: dict[str, Path] = {}
        manifest = self._generated_ocg_node_manifest
        if manifest is not None:
            # node_id -> class_config_id lookup
            class_id_by_node_id: dict[str, str] = {}
            for node in graph.object_config_graph_nodes:
                if (
                    node.type == ObjectConfigGraphNodeType.class_
                    and node.class_config is not None
                ):
                    class_id_by_node_id[str(node.id)] = str(node.class_config.id)

            for intent in manifest.intents_by_node_id.values():
                if intent.node_type != ObjectConfigGraphNodeType.class_:
                    continue
                if (
                    intent.file_policy
                    != GeneratedObjectConfigGraphNodeFilePolicy.OWN_FILE
                ):
                    continue
                if intent.anchor_node_id is None:
                    continue
                anchor_class_id = class_id_by_node_id.get(str(intent.anchor_node_id))
                join_class_id = class_id_by_node_id.get(str(intent.node_id))
                if anchor_class_id is None or join_class_id is None:
                    continue
                anchor_path = self._entity_template_paths.get(anchor_class_id)
                if anchor_path is None:
                    anchor_path = self.entity_layout_paths.get(anchor_class_id)
                if anchor_path is None:
                    continue
                join_anchor[join_class_id] = Path(anchor_path).parent
        self._join_anchor_dir_by_class_id = join_anchor

        # Build preferred file path per code_id from classes (canonical container SSOT).
        preferred: dict[str, Path] = {}
        for node in graph.object_config_graph_nodes:
            if (
                node.type != ObjectConfigGraphNodeType.class_
                or node.class_config is None
            ):
                continue
            cc = node.class_config
            code_section_class = cc.code_section_class
            if code_section_class is None:
                continue
            code_id = code_section_class.code_section.code_id

            # Prefer canonical template mapping when present; otherwise fall back to namespace.
            path = self._template_path_for_entity(cc.id)
            if path is None:
                path = self.entity_layout_paths.get(str(cc.id))
            if path is None:
                ns = self._ns_for_class(cc)
                rel_root = self._relative_root_for_namespace(ns)
                path = (rel_root / to_snake_case(cc.name)).with_suffix(
                    self.get_file_extension()
                )
            _ = preferred.setdefault(str(code_id), path)
        self._preferred_file_by_code_id = preferred

    def _template_path_for_entity(self, entity_id: object) -> Path | None:
        try:
            key = str(entity_id)
        except Exception:
            return None
        return self._entity_template_paths.get(key)

    def _ns_for_class(self, class_config: ClassConfig) -> NamespacePath:
        if self._namespace_bundle is None:
            raise ValueError(
                "SQLLayoutStrategyNamespace missing namespace bundle; bind_graph() was not called"
            )
        ns = self._namespace_bundle.namespace_for_class(class_config.id)
        if ns is None:
            return self._fallback_namespace()
        return ns

    def _ns_for_enum(self, enum_config: EnumConfig) -> NamespacePath:
        if self._namespace_bundle is None:
            raise ValueError(
                "SQLLayoutStrategyNamespace missing namespace bundle; bind_graph() was not called"
            )
        ns = self._namespace_bundle.namespace_for_enum(enum_config.id)
        if ns is None:
            return self._fallback_namespace()
        return ns

    def _ns_for_function(self, function_config: FunctionConfig) -> NamespacePath:
        if self._namespace_bundle is None:
            raise ValueError(
                "SQLLayoutStrategyNamespace missing namespace bundle; bind_graph() was not called"
            )
        ns = self._namespace_bundle.namespace_for_function(function_config.id)
        if ns is None:
            return self._fallback_namespace()
        return ns

    def _fallback_namespace(self) -> NamespacePath:
        graph = self._graph
        package = (
            (getattr(graph, "fqn_prefix", "") or "").strip()
            if graph is not None
            else ""
        )
        return NamespacePath(
            package=package or "default",
            namespace="default",
        )

    @staticmethod
    def _relative_root_for_namespace(ns: NamespacePath) -> Path:
        namespace = (ns.namespace or "").strip(".")
        if not namespace or namespace == "default":
            return Path(".")
        return Path(*[part for part in namespace.split(".") if part])

    @override
    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        # 1) Prefer canonical template resolution (meta-id keyed).
        templ = self._template_path_for_entity(class_config.id)
        if templ is not None:
            return templ

        # 2) Prefer OCG node layout paths from source provenance.
        layout_path = self.entity_layout_paths.get(str(class_config.id))
        if layout_path is not None:
            return layout_path.with_suffix(self.get_file_extension())

        # 3) Synthetic join table: anchor next to canonical source class directory.
        anchor_dir = self._join_anchor_dir_by_class_id.get(str(class_config.id))
        if anchor_dir is not None:
            return (anchor_dir / to_snake_case(class_config.name)).with_suffix(
                self.get_file_extension()
            )

        # 4) Fallback to namespace-based layout (works without code provenance).
        ns = self._ns_for_class(class_config)
        rel_root = self._relative_root_for_namespace(ns)
        rel = rel_root / to_snake_case(class_config.name)
        return rel.with_suffix(self.get_file_extension())

    @override
    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        templ = self._template_path_for_entity(enum_config.id)
        if templ is not None:
            return templ

        layout_path = self.entity_layout_paths.get(str(enum_config.id))
        if layout_path is not None:
            return layout_path.with_suffix(self.get_file_extension())

        # If enum was declared in the same canonical `.aware` file as a class, keep them together.
        if enum_config.code_section_enum is not None:
            code_id = enum_config.code_section_enum.code_section.code_id
            preferred = self._preferred_file_by_code_id.get(str(code_id))
            if preferred is not None:
                return preferred

        ns = self._ns_for_enum(enum_config)
        rel_root = self._relative_root_for_namespace(ns)
        rel = rel_root / to_snake_case(enum_config.name)
        return rel.with_suffix(self.get_file_extension())

    @override
    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        templ = self._template_path_for_entity(function_config.id)
        if templ is not None:
            return templ

        layout_path = self.entity_layout_paths.get(str(function_config.id))
        if layout_path is not None:
            return layout_path.with_suffix(self.get_file_extension())

        # Same canonical container grouping for functions (when code provenance exists).
        if function_config.code_section_function is not None:
            code_id = function_config.code_section_function.code_section.code_id
            preferred = self._preferred_file_by_code_id.get(str(code_id))
            if preferred is not None:
                return preferred
        ns = self._ns_for_function(function_config)
        rel_root = self._relative_root_for_namespace(ns)
        rel = rel_root / to_snake_case(function_config.name)
        return rel.with_suffix(self.get_file_extension())


class SQLLayoutStrategyTemplateMixin(ObjectConfigGraphRenderLayoutStrategyTemplate):
    """Template-aware layout strategy for SQL outputs (mirrors canonical `.aware` structure)."""

    def __init__(
        self,
        base_dir: Path,
        template_paths: dict[str, Path] | None = None,
        entity_template_paths: dict[str, Path] | None = None,
        generated_ocg_node_manifest: (
            GeneratedObjectConfigGraphNodeManifest | None
        ) = None,
        import_root: str | None = None,
    ) -> None:
        ObjectConfigGraphRenderLayoutStrategyTemplate.__init__(
            self,
            base_dir,
            template_paths=template_paths,
            entity_template_paths=entity_template_paths,
            generated_ocg_node_manifest=generated_ocg_node_manifest,
            import_root=import_root,
        )

    @property
    @override
    def language(self) -> CodeLanguage:
        return CodeLanguage.sql

    @override
    def get_file_extension(self) -> str:
        return ".sql"


__all__ = [
    "SQLLayoutStrategy",
    "SQLLayoutStrategyNamespace",
    "SQLLayoutStrategyTemplateMixin",
]
