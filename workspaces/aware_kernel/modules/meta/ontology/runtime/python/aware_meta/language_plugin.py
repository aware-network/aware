"""
Meta language plugin system for surgical code editing.

This module provides the unified plugin contract that aggregates all language-specific
components needed by the meta layer: code parsing, graph building, transformers, and renderers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Mapping
from pathlib import Path

# Primitive Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)

from aware_meta.reserved_keyword_policy import ReservedKeywordEntityPolicy

from aware_code.language.plugin import (
    CodeLanguageMaterializationOutputDescriptor,
    CodeLanguagePlugin,
)
from aware_code.section.builder_index import CodeSectionBuilderIndex

# OCG
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

# Annotation Compiler
from aware_meta.graph.config.annotation.protocol import MetaAnnotationCompiler

# OCG Transformer
from aware_meta.graph.config.transformer import (
    ObjectConfigGraphTransformer,
    ObjectConfigGraphTransformerPolicy,
)

# OCG Renderer
from aware_meta.graph.config.render.renderer import (
    ObjectConfigGraphRenderer,
)
from aware_meta.graph.config.render.renderer_language import (
    ObjectConfigGraphRendererLanguage,
    ObjectConfigGraphRendererPolicy,
)
# OCG Render Layout Strategy
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta.graph.config.render.layout_strategy_template import (
    ObjectConfigGraphRenderLayoutStrategyTemplate,
)
from aware_meta.graph.config.render.generated_ocg_node_manifest import (
    GeneratedObjectConfigGraphNodeManifest,
)
from aware_meta.graph.config.package_strategy import (
    ObjectConfigGraphPackageSpec,
    ObjectConfigGraphPackageStrategy,
)

# Granular renderers base
from aware_meta.renderer import MetaRenderer

# File system
from aware_file_system.config import FilterConfig

if TYPE_CHECKING:
    from aware_meta.materialization.deltas.language_renderer_contracts import (
        MetaLanguageGeneratedMaterializationDeltaRenderer,
        MetaLanguageGeneratedMaterializationDeltaRenderRequest,
        MetaLanguageGeneratedMaterializationDeltaRenderResult,
    )


@dataclass(frozen=True)
class RendererProfileInputContract:
    """Generic per-profile input requirements for backend materialization."""

    input_mode: str = "graph_only"
    required_keys: tuple[str, ...] = ()
    optional_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        allowed_modes = {"graph_only", "graph_plus_profile_inputs", "profile_inputs_first"}
        if self.input_mode not in allowed_modes:
            raise ValueError(
                f"RendererProfileInputContract.input_mode must be one of {sorted(allowed_modes)!r}, "
                + f"got {self.input_mode!r}"
            )
        overlap = set(self.required_keys).intersection(self.optional_keys)
        if overlap:
            raise ValueError(
                "RendererProfileInputContract keys cannot be both required and optional: "
                + ", ".join(sorted(overlap))
            )

    @property
    def declared_keys(self) -> tuple[str, ...]:
        return self.required_keys + self.optional_keys


@dataclass(frozen=True, slots=True)
class MetaLanguagePackageStrategyConfigurationRequest:
    """Generic context for language-owned package strategy configuration."""

    target_language_plugin_id: CodeLanguage
    strategy: ObjectConfigGraphPackageStrategy
    package_specs: tuple[ObjectConfigGraphPackageSpec, ...] = ()
    materialization_source: str | None = None
    renderer_profile: str | None = None
    renderer_kind: str | None = None
    package_kind: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class MetaLanguageMaterializationDestination:
    """Concrete destination where a language plugin may place declared outputs."""

    key: str
    kind: str
    root: Path
    package_name: str | None = None
    package_root: Path | None = None
    import_root: str | None = None
    file_paths: tuple[Path, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class MetaLanguageDeclaredOutputProducedFile:
    """File payload produced by a language plugin for a declared output."""

    output_key: str
    path: Path
    content_bytes: bytes | None = None
    content_text: str | None = None
    output_kind: str | None = None
    artifact_role: str | None = None
    producer_step: str = "plugin_declared_output_producer"
    provider_payload: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.content_bytes is not None and self.content_text is not None:
            raise ValueError("Produced file cannot provide both bytes and text content.")


@dataclass(frozen=True)
class MetaLanguageDeclaredOutputProducerRequest:
    """Generic context passed to a language-owned declared-output producer."""

    output_root: Path
    source_graph: ObjectConfigGraph
    runtime_graph: ObjectConfigGraph
    language_graph: ObjectConfigGraph
    generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None = None
    destinations: tuple[MetaLanguageMaterializationDestination, ...] = ()
    language_external_graphs: tuple[ObjectConfigGraph, ...] = ()
    descriptors: tuple[CodeLanguageMaterializationOutputDescriptor, ...] = ()
    generated_file_paths: tuple[Path, ...] = ()
    package_name: str | None = None
    import_root: str | None = None
    package_dependency_import_roots: tuple[str, ...] = ()
    renderer_profile: str | None = None
    renderer_kind: str | None = None
    materialization_source: str | None = None
    entity_file_paths: Mapping[str, Path] = field(default_factory=dict)
    profile_inputs: Mapping[str, object] = field(default_factory=dict)
    import_overrides: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class MetaLanguageDeclaredOutputProducerResult:
    """Files and diagnostics returned by a language-owned output producer."""

    produced_files: tuple[MetaLanguageDeclaredOutputProducedFile, ...] = ()
    warnings: tuple[str, ...] = ()
    metrics: Mapping[str, object] = field(default_factory=dict)


@dataclass
class MetaLanguagePlugin:
    """
    Unified plugin for all language-specific meta operations.

    Aggregates all language-specific hooks that the meta layer needs:
    - Code-level parsing (via CodeLanguagePlugin)
    - Graph generation (transformers)
    - Surgical rendering (entity renderers)
    - File filtering and other utilities

    One instance per language, registered at startup.
    """

    language: CodeLanguage

    # ---------- File system ----------
    file_filter_config_factory: Callable[[], FilterConfig]

    # ---------- Code-level parsing ----------
    code_plugin: CodeLanguagePlugin[Any]  # Reuse existing primitive layer plugin

    # ---------- Surgical rendering ----------
    surgical_renderers: Mapping[type[object], type[MetaRenderer]]  # Entity type -> Renderer class

    # ---------- Annotation compilation ----------
    # Compile CodeSectionAnnotation entries into ObjectConfigGraphAnnotation wrappers (verb-specific views).
    # This keeps the canonical OCG builder grammar-agnostic while allowing languages to extend annotation semantics.
    annotation_compiler: MetaAnnotationCompiler | None = None

    # ---------- Full ObjectConfigGraph Rendering ----------
    language_renderers: Mapping[str, type[ObjectConfigGraphRendererLanguage]] | None = None
    # Renderers to run when a workflow does not specify `renderer_kind`.
    #
    # This list is intentionally explicit to avoid the historical ambiguity of
    # "run all renderers" (which breaks once a language adds non-default outputs
    # like representation-only helpers).
    default_renderer_names: tuple[str, ...] = ()
    # Optional profile-specific default renderers (e.g., api_runtime vs orm_runtime).
    # When provided and a profile is supplied, the matching renderer set is used.
    default_renderer_names_by_profile: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    # Optional profile-specific renderer policy (language-defined).
    renderer_policies_by_profile: Mapping[str, ObjectConfigGraphRendererPolicy] = field(default_factory=dict)
    # Optional profile-specific transformer policy (language-defined).
    transformer_policies_by_profile: Mapping[str, ObjectConfigGraphTransformerPolicy] = field(default_factory=dict)
    # Optional profile-specific input requirements consumed by env-artifacts.
    renderer_profile_input_contracts: Mapping[str, RendererProfileInputContract] = field(default_factory=dict)
    declared_output_producer: Callable[
        [MetaLanguageDeclaredOutputProducerRequest],
        MetaLanguageDeclaredOutputProducerResult,
    ] | None = None
    # Optional profile-scoped generated-materialization delta renderers.
    #
    # These are the delta-first counterpart to full language renderers: Meta
    # feature providers describe what changed, while language plugins lower
    # that semantic intent into Code generated-materialization delta evidence.
    generated_delta_renderers: Mapping[
        str,
        Callable[[], MetaLanguageGeneratedMaterializationDeltaRenderer],
    ] = field(default_factory=dict)
    default_generated_delta_renderer_names_by_profile: Mapping[
        str,
        tuple[str, ...],
    ] = field(default_factory=dict)

    # ---------- Capabilities ----------
    supports_full_file_recreation: bool = False
    # When True, `import pkg.sub.module` (no explicit alias) creates an implicit prefix binding
    # for the first segment (e.g. `pkg -> pkg.sub.module`) during meta resolution.
    #
    # Canonical Aware policy sets this to False: imports only affect resolution when an
    # explicit alias is provided (`import X as a`).
    imports_bind_unaliased_module_head: bool = True

    # ---------- Layout strategy ----------
    layout_strategy: type[ObjectConfigGraphRenderLayoutStrategy] | None = None
    package_strategy_factory: Callable[[Path], ObjectConfigGraphPackageStrategy] | None = None
    package_strategy_configurator: Callable[
        [MetaLanguagePackageStrategyConfigurationRequest],
        None,
    ] | None = None

    # ---------- Reserved keywords / invalid identifiers ----------
    #
    # Language plugins may provide per-entity identifier rules that the meta layer compiles into
    # ObjectConfigGraphOverlay entries (second-pass) so renderers never rename directly.
    reserved_keyword_policies: Mapping[CodeSectionAnnotationOverlayEntity, ReservedKeywordEntityPolicy] = field(
        default_factory=dict
    )

    # ---------- Runtime IR -> Language (optional) ----------
    #
    # Some languages may need a lowering step after runtime IR is derived
    # (e.g., SQL join-table materialization / DB constraints).
    #
    # Python/Dart typically do not (renderer is emit-only over runtime IR).
    runtime_to_language_transformer: type[ObjectConfigGraphTransformer] | None = None

    # ---------- Language -> Runtime IR (optional) ----------
    #
    # Reserved for future bidirectional workflows (e.g., migrations):
    # when taking a language-specific graph and normalizing it into runtime IR.
    #
    # Canonical policy:
    # - There is exactly one runtime IR derivation per source language.
    # - Consumer-specific behavior must be expressed in the graph (e.g., ClassValueMode),
    #   not via pipeline profiles.
    language_to_runtime_transformer: type[ObjectConfigGraphTransformer] | None = None

    # Future extensions can be added here:
    # - Formatters, linters, test runners, etc.

    def get_renderer(
        self,
        output_directory: Path,
        layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
        overwrite: bool = True,
        kind: str | None = None,
        profile: str | None = None,
    ) -> ObjectConfigGraphRenderer:
        """
        Get an ObjectConfigGraphRenderer instance for this language.

        If multiple renderers are registered (language_renderers), `kind` selects
        which one to use. When omitted, the default renderer set must contain
        exactly one entry (otherwise `kind` is required).
        """
        if not self.language_renderers:
            raise ValueError("No renderers registered for language {self.language}")
        if kind is None:
            if len(self.default_renderer_names) != 1:
                raise ValueError(
                    "Renderer kind is required when multiple default renderers are configured; "
                    f"default_renderer_names={self.default_renderer_names!r}"
                )
            kind = self.default_renderer_names[0]
        renderer_cls = self.language_renderers.get(kind)
        if renderer_cls is None:
            raise KeyError(f"No renderer registered for kind '{kind}' in language {self.language}")
        language_renderer = renderer_cls(layout_strategy=layout_strategy)

        renderer = ObjectConfigGraphRenderer(
            renderer_language=language_renderer,
            output_directory=output_directory,
            overwrite=overwrite,
        )
        if profile is not None:
            policy = self.renderer_policies_by_profile.get(profile)
            if policy is not None:
                renderer.set_policy(policy)
        return renderer

    def get_default_renderers(
        self,
        output_directory: Path,
        layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
        overwrite: bool = True,
        profile: str | None = None,
    ) -> dict[str, ObjectConfigGraphRenderer]:
        """
        Instantiate the configured default renderers for this language.

        Returns a mapping from renderer name to ObjectConfigGraphRenderer.
        """
        if not self.language_renderers:
            raise ValueError("language_renderers is configured but empty")
        renderer_names = self.default_renderer_names
        if profile is not None:
            profile_key = profile.strip()
            if profile_key and self.default_renderer_names_by_profile:
                if profile_key not in self.default_renderer_names_by_profile:
                    raise ValueError(
                        f"default renderer set not configured for profile {profile_key!r} "
                        f"in language {self.language}"
                    )
                renderer_names = self.default_renderer_names_by_profile[profile_key]
        if not renderer_names:
            raise ValueError(
                f"default_renderer_names must be configured for language {self.language} when language_renderers exist"
            )

        renderers: dict[str, ObjectConfigGraphRenderer] = {}
        for name in renderer_names:
            renderer_cls = self.language_renderers.get(name)
            if renderer_cls is None:
                raise KeyError(f"Default renderer '{name}' is not registered for language {self.language}")
            language_renderer = renderer_cls(layout_strategy=layout_strategy)
            renderer = ObjectConfigGraphRenderer(
                renderer_language=language_renderer,
                output_directory=output_directory,
                overwrite=overwrite,
            )
            if profile is not None:
                policy = self.renderer_policies_by_profile.get(profile)
                if policy is not None:
                    renderer.set_policy(policy)
            renderers[name] = renderer
        return renderers

    def get_renderer_profile_input_contract(self, profile: str | None) -> RendererProfileInputContract:
        """Return generic backend input requirements for a renderer profile."""
        if profile is None:
            return RendererProfileInputContract()
        return self.renderer_profile_input_contracts.get(profile, RendererProfileInputContract())

    def get_generated_delta_renderers(
        self,
        *,
        profile: str | None = None,
        kind: str | None = None,
    ) -> dict[str, MetaLanguageGeneratedMaterializationDeltaRenderer]:
        """Instantiate generated-materialization delta renderers for a profile."""

        if not self.generated_delta_renderers:
            return {}
        if kind is not None:
            renderer_factory = self.generated_delta_renderers.get(kind)
            if renderer_factory is None:
                raise KeyError(
                    f"No generated delta renderer registered for kind {kind!r} "
                    f"in language {self.language}"
                )
            return {kind: renderer_factory()}

        renderer_names = tuple(self.generated_delta_renderers.keys())
        if profile is not None:
            profile_key = profile.strip()
            if (
                profile_key
                and self.default_generated_delta_renderer_names_by_profile
            ):
                renderer_names = (
                    self.default_generated_delta_renderer_names_by_profile.get(
                        profile_key,
                        (),
                    )
                )
        renderers: dict[str, MetaLanguageGeneratedMaterializationDeltaRenderer] = {}
        for name in renderer_names:
            renderer_factory = self.generated_delta_renderers.get(name)
            if renderer_factory is None:
                raise KeyError(
                    f"Default generated delta renderer {name!r} is not "
                    f"registered for language {self.language}"
                )
            renderers[name] = renderer_factory()
        return renderers

    def render_generated_materialization_delta(
        self,
        request: MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    ) -> MetaLanguageGeneratedMaterializationDeltaRenderResult:
        """Lower a provider semantic operation through language-owned delta renderers."""

        from aware_meta.materialization.deltas.language_renderer_contracts import (  # noqa: WPS433
            MetaLanguageGeneratedMaterializationDeltaRenderResult,
        )

        renderers = self.get_generated_delta_renderers(
            profile=request.renderer_profile,
            kind=request.capability_key,
        )
        if not renderers:
            return MetaLanguageGeneratedMaterializationDeltaRenderResult.unhandled(
                reason="meta_language_generated_delta_renderer_not_registered",
            )
        for renderer in renderers.values():
            if not renderer.supports_generated_materialization_delta(request):
                continue
            return renderer.render_generated_materialization_delta(request)
        return MetaLanguageGeneratedMaterializationDeltaRenderResult.unhandled(
            reason="meta_language_generated_delta_renderer_not_supported",
        )

    def get_surgical_renderer(
        self,
        entity_type: type[object],
        section_index: CodeSectionBuilderIndex,
        layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
        baseline_graph: ObjectConfigGraph | None = None,
        new_graph: ObjectConfigGraph | None = None,
        namespace: str = "default",
    ) -> MetaRenderer:
        """
        Get a renderer instance for the given entity type.

        Args:
            entity_type: The type of entity to render
            section_index: Index for looking up existing sections
            layout_strategy: Strategy for determining file paths
            baseline_graph: The baseline ObjectConfigGraph for lookups
            new_graph: The new ObjectConfigGraph for lookups
            namespace: Default namespace for annotations

        Returns:
            Renderer instance with injected dependencies

        Raises:
            KeyError: If no renderer found for entity type
        """
        renderer_cls = self.surgical_renderers[entity_type]
        return renderer_cls(
            renderers=self.surgical_renderers,
            section_index=section_index,
            layout_strategy=layout_strategy,
            baseline_graph=baseline_graph,
            new_graph=new_graph,
            namespace=namespace,
            comment_prefix=self.code_plugin.comment_prefix,  # Propagate from code plugin
        )

    def get_file_filter_config(self) -> FilterConfig:
        """
        Get the file filter configuration for this language.

        Returns:
            FilterConfig instance
        """
        return self.file_filter_config_factory()

    def create_layout_strategy(
        self,
        base_dir: Path,
        template_paths: dict[str, Path] | None = None,
        entity_template_paths: dict[str, Path] | None = None,
        generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None = None,
        import_root: str | None = None,
    ) -> ObjectConfigGraphRenderLayoutStrategy | None:
        """Instantiate the layout strategy for this language."""

        if self.layout_strategy is None:
            return None
        if issubclass(self.layout_strategy, ObjectConfigGraphRenderLayoutStrategyTemplate):
            return self.layout_strategy(
                base_dir=base_dir,
                template_paths=template_paths,
                entity_template_paths=entity_template_paths,
                generated_ocg_node_manifest=generated_ocg_node_manifest,
                import_root=import_root,
            )
        return self.layout_strategy(
            base_dir=base_dir,
            generated_ocg_node_manifest=generated_ocg_node_manifest,
            import_root=import_root,
        )

    def create_package_strategy(self, base_dir: Path) -> ObjectConfigGraphPackageStrategy | None:
        if self.package_strategy_factory is None:
            return None
        return self.package_strategy_factory(base_dir)

    def configure_package_strategy(
        self,
        request: MetaLanguagePackageStrategyConfigurationRequest,
    ) -> None:
        """Allow the language plugin to configure package strategy policy."""
        if self.package_strategy_configurator is None:
            return
        self.package_strategy_configurator(request)

    @property
    def supported_entity_types(self) -> list[type[object]]:
        """Get list of supported entity types for rendering."""
        return list(self.surgical_renderers.keys())
