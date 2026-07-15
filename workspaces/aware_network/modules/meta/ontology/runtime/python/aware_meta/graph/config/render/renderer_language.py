"""
Protocol for language plugins used by the ObjectConfigGraphRenderer.

This defines the contract that language-specific renderers must implement
to be used as plugins for the ObjectConfigGraphRenderer.
"""

from collections import defaultdict
import importlib
from pathlib import Path
from typing import Any, Mapping, Protocol, Union
from uuid import UUID

from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code.stable_ids import (
    stable_code_id,
    stable_code_package_code_id,
    stable_code_package_config_id,
    stable_code_package_id,
)
from aware_content.builder import build_content_part_text_inline


# Meta
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_overlay import (
    ObjectConfigGraphOverlay,
)

from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_overlay import ClassConfigOverlay
from aware_meta_ontology.function.function_config_overlay import FunctionConfigOverlay
from aware_meta_ontology.attribute.attribute_config_overlay import (
    AttributeConfigOverlay,
)
from aware_meta_ontology.enum.enum_config_overlay import EnumConfigOverlay
from aware_meta_ontology.enum.enum_option_overlay import EnumOptionOverlay

from aware_code.section.writer import CodeSectionWriter

from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)

OverlayEntity = Union[
    ClassConfigOverlay,
    FunctionConfigOverlay,
    AttributeConfigOverlay,
    EnumConfigOverlay,
    EnumOptionOverlay,
]


def build_renderer_empty_code(*, language: CodeLanguage, renderer_key: str) -> Code:
    """
    Build a deterministic synthetic Code shell for renderer-owned output assembly.

    Renderers use transient `Code` objects only as section assembly roots. They must
    still carry deterministic package-edge-scoped identity so child `CodeSection` ids
    remain stable under package-owned code truth.
    """

    normalized_renderer_key = renderer_key.strip()
    if not normalized_renderer_key:
        raise ValueError("build_renderer_empty_code requires non-empty renderer_key")
    relative_path = (
        f"aware/renderer/{language.value}/{normalized_renderer_key}.generated"
    )
    synthetic_package_id = stable_code_package_id(
        code_package_config_id=stable_code_package_config_id(
            config_key="synthetic:renderer",
        ),
        package_name=f"__aware_renderer__.{language.value}.{normalized_renderer_key.casefold()}",
        language=language.value,
    )
    synthetic_code_package_code_id = stable_code_package_code_id(
        code_package_id=synthetic_package_id,
        relative_path=relative_path,
    )
    cpt = build_content_part_text_inline("")
    return Code(
        id=stable_code_id(
            code_package_code_id=synthetic_code_package_code_id,
            relative_path=relative_path,
        ),
        code_package_code_id=synthetic_code_package_code_id,
        relative_path=relative_path,
        content_part_text=cpt,
        content_part_text_id=cpt.id,
        language=language,
    )


def _canonicalize_python_generated_source(
    *,
    relative_path: Path,
    source: str,
) -> str:
    path = Path(relative_path)
    if path.suffix not in {".py", ".pyi"} or not source.strip():
        return source
    try:
        black = importlib.import_module("black")
        file_mode = getattr(black, "FileMode")
        format_str = getattr(black, "format_str")
        mode = file_mode(line_length=120, is_pyi=(path.suffix == ".pyi"))
        return str(format_str(source, mode=mode))
    except Exception:
        return source


class ObjectConfigGraphRendererPolicy(Protocol):
    """Base type for renderer policies (language-specific concrete policies live in language plugins)."""


class ObjectConfigGraphRendererLanguage(Protocol):
    """
    Protocol defining the interface for language-specific renderer plugins.

    Each language plugin knows how to render meta-objects (ClassConfig, EnumConfig, etc.)
    into code for a specific programming language.
    """

    layout_strategy: ObjectConfigGraphRenderLayoutStrategy
    import_overrides: dict[str, str] | None
    profile_inputs: dict[str, object]
    overlays_by_entity_id: defaultdict[
        CodeSectionAnnotationOverlayEntity, dict[UUID, OverlayEntity]
    ] = defaultdict(dict)
    external_class_lookup: dict[UUID, ClassConfig]
    external_graphs: list[ObjectConfigGraph]

    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy):
        """
        Initialize the language renderer.

        Args:
            layout_strategy: Layout strategy for organizing files
        """
        self.layout_strategy = layout_strategy
        self.import_overrides = {}
        self.profile_inputs = {}
        # IMPORTANT: overlays must be per-renderer-instance, not a shared class-level default.
        # The previous class attribute default caused cross-run/language contamination (e.g. Dart overlays
        # leaking into Python renders), breaking determinism.
        self.overlays_by_entity_id = defaultdict(dict)
        self.external_class_lookup = {}
        self.external_graphs = []
        # Define assemblers
        self.define_assemblers()

    @property
    def language(self) -> CodeLanguage:
        """Return the language supported by this plugin."""
        ...

    @property
    def indent(self) -> int:
        """Return the indentation size for this language."""
        ...

    @property
    def comment_prefix(self) -> str:
        """Return the comment prefix for this language (e.g., # for Python, // for JavaScript)."""
        ...

    def canonicalize_generated_source(
        self,
        *,
        relative_path: Path,
        source: str,
    ) -> str:
        """Return source text in the post-step formatter's stable form before write comparison."""
        if self.language == CodeLanguage.python:
            return _canonicalize_python_generated_source(
                relative_path=relative_path,
                source=source,
            )
        return source

    def define_assemblers(self):
        """
        Define the assemblers for the renderer.
        """
        ...

    def set_policy(self, policy: ObjectConfigGraphRendererPolicy | None) -> None:
        """Inject a language-specific renderer policy (DTO vs ORM, etc.)."""
        pass

    def bind_profile_inputs(self, profile_inputs: Mapping[str, object]) -> None:
        """Bind generic profile-scoped payloads resolved by env-artifacts."""
        self.profile_inputs = dict(profile_inputs)

    def set_external_class_lookup(
        self, external_class_lookup: dict[UUID, ClassConfig]
    ) -> None:
        """Set the external class lookup for the renderer."""
        self.external_class_lookup = external_class_lookup

    def set_external_graphs(self, external_graphs: list[ObjectConfigGraph]) -> None:
        """Set the external graphs for the renderer."""
        self.external_graphs = external_graphs

    def emit_file(
        self,
        meta_objects: list[Any],
        writer: CodeSectionWriter,
        namespace: str = "default",
        class_to_class_config_map: dict[UUID, ClassConfig] | None = None,
        base_class_module: str | None = None,
        base_class_name: str | None = None,
    ) -> None:
        """
        Emit a complete file with all the given meta objects.

        Args:
            meta_objects: List of meta objects to render
            writer: CodeSectionWriter to use for writing the code
            namespace: Namespace for the objects in this file.
            class_to_class_config_map: Mapping from class ID to ClassConfig for accessing ClassConfig info
            base_class_module: Module name for the base class
            base_class_name: Name of the base class
        """
        ...

    def bind_object_config_graph(self, graph: ObjectConfigGraph) -> None:
        """
        Bind graph-level state required for renderer-language-specific functionality.
        """
        pass

    def extra_output_paths(self) -> list[Path]:
        """
        Optional hook: return additional output file paths to render once per graph.

        Motivation:
        - Some renderers need to emit a single registry/manifest module that is not anchored
          to a specific meta object node (e.g. runtime handler registries).
        - Keeping this explicit avoids file-path heuristics and keeps output deterministic.
        """
        return []

    def renders_only_extra_output_paths(self) -> bool:
        """
        Return True when this renderer intentionally emits only ``extra_output_paths``.

        Extra-output-only renderers can skip the generic node-to-file grouping pass;
        they still receive the bound ObjectConfigGraph before file emission.
        """
        return False

    def requires_graph_metadata_hydration(self) -> bool:
        """
        Return True when the generic renderer must hydrate parent/descriptor metadata.

        Extra-output-only renderers that only use their own bound graph indexes can
        override this to avoid a full descriptor walk before emitting graph-level
        files. Renderers that delegate to compiler/type lowering should keep the
        default.
        """
        return True

    def create_empty_code(self) -> Code:
        """
        Create an empty Code object for this language.

        Returns:
            An initialized Code object
        """
        ...

    def clear_warnings(self) -> None:
        """
        Clear any warnings generated by the renderer.
        """
        pass

    def get_warnings(self) -> list[str]:
        """
        Get any warnings generated by the renderer.

        Returns:
            List of warning messages
        """
        return []

    def validate_existing_output(
        self,
        *,
        relative_path: Path,
        output_path: Path,
        generated_source: str,
        existing_source: str,
    ) -> None:
        """
        Optional fail-closed hook invoked when the target output file already exists
        and differs from the newly generated source.

        Language renderers may raise to enforce strict drift gates.
        """
        _ = relative_path
        _ = output_path
        _ = generated_source
        _ = existing_source
        return

    def get_overlay_by_entity_id(
        self, entity: CodeSectionAnnotationOverlayEntity, id: UUID
    ) -> OverlayEntity | None:
        """
        Get the overlay entity for the given entity and ID.
        """
        return self.overlays_by_entity_id.get(entity, {}).get(id, None)

    def set_language_overlay(self, overlay: ObjectConfigGraphOverlay) -> None:
        """
        Attach a language overlay so that enums/fields/functions can be remapped.
        """
        # Overlays are a per-materialization concern; reset before applying a new one.
        self.overlays_by_entity_id = defaultdict(dict)
        for class_overlay in overlay.class_config_overlays:
            if not class_overlay.id:
                continue
            self.overlays_by_entity_id[CodeSectionAnnotationOverlayEntity.class_][
                class_overlay.class_config_id
            ] = class_overlay
        for func_overlay in overlay.function_config_overlays:
            if not func_overlay.id:
                continue
            self.overlays_by_entity_id[CodeSectionAnnotationOverlayEntity.function][
                func_overlay.function_config_id
            ] = func_overlay
        for attr_overlay in overlay.attribute_config_overlays:
            if not attr_overlay.id:
                continue
            self.overlays_by_entity_id[CodeSectionAnnotationOverlayEntity.attribute][
                attr_overlay.attribute_config_id
            ] = attr_overlay
        for enum_overlay in overlay.enum_config_overlays:
            if not enum_overlay.id:
                continue
            self.overlays_by_entity_id[CodeSectionAnnotationOverlayEntity.enum][
                enum_overlay.enum_config_id
            ] = enum_overlay

        for opt_overlay in overlay.enum_option_overlays:
            if not opt_overlay.id:
                continue
            self.overlays_by_entity_id[CodeSectionAnnotationOverlayEntity.enum_option][
                opt_overlay.enum_option_id
            ] = opt_overlay
