"""
Meta plugin registry for managing language-specific meta plugins.

This module provides a singleton registry that manages MetaLanguagePlugin instances,
similar to how CodeBuilderFactory manages CodeLanguagePlugins.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

# Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

# Code
from aware_code.language.plugin import StructuralFilterDecision
from aware_code.section.builder_index import CodeSectionBuilderIndex


# Meta
from aware_meta.language_plugin import MetaLanguagePlugin

if TYPE_CHECKING:
    # Heavy render/transform dependencies are type-only; keep import side effects out of kernel build paths.
    from aware_meta.graph.config.render.renderer import ObjectConfigGraphRenderer
    from aware_meta.graph.config.transformer import ObjectConfigGraphTransformer
    from aware_meta.graph.config.render.layout_strategy import (
        ObjectConfigGraphRenderLayoutStrategy,
    )
    from aware_meta.graph.config.render.generated_ocg_node_manifest import (
        GeneratedObjectConfigGraphNodeManifest,
    )
    from aware_meta.graph.config.package_strategy import (
        ObjectConfigGraphPackageStrategy,
    )
    from aware_meta.language_plugin import (
        MetaLanguagePackageStrategyConfigurationRequest,
    )
    from aware_meta.renderer import MetaRenderer

# File system
from aware_file_system.config import FilterConfig

# Utils
from aware_utils.logging import logger


class MetaLanguagePluginRegistry:
    """
    Singleton registry for MetaLanguagePlugin instances.

    Similar to CodeBuilderFactory but for meta-layer operations:
    - Graph building and transformation
    - Surgical rendering
    - File filtering
    """

    _plugins: dict[CodeLanguage, MetaLanguagePlugin] = {}
    _supported_languages: set[CodeLanguage] = set()
    _file_filter_overrides: dict[CodeLanguage, FilterConfig] = {}
    _structural_filter_overrides: dict[CodeLanguage, Callable[[str, str | None], StructuralFilterDecision]] = {}

    @classmethod
    def register(cls, plugin: MetaLanguagePlugin) -> None:
        """
        Register a meta language plugin.

        Args:
            plugin: Complete meta language plugin containing all components
        """
        if plugin.language not in cls._supported_languages:
            cls._plugins[plugin.language] = plugin
            cls._supported_languages.add(plugin.language)

    @classmethod
    def get(cls, language: CodeLanguage) -> MetaLanguagePlugin:
        """
        Get the meta plugin for a specific language.

        Args:
            language: The language to get the plugin for

        Returns:
            MetaLanguagePlugin instance

        Raises:
            KeyError: If no plugin registered for the language
        """
        if language not in cls._plugins:
            raise KeyError(f"No meta plugin registered for language: {language}")

        return cls._plugins[language]

    @classmethod
    def get_renderer(
        cls,
        language: CodeLanguage,
        output_directory: Path,
        layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
        overwrite: bool = True,
        kind: str | None = None,
        profile: str | None = None,
    ) -> ObjectConfigGraphRenderer:
        """
        Get a renderer for a specific language.
        """
        plugin = cls.get(language)
        return plugin.get_renderer(output_directory, layout_strategy, overwrite, kind=kind, profile=profile)

    @classmethod
    def get_default_renderers(
        cls,
        language: CodeLanguage,
        output_directory: Path,
        layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
        overwrite: bool = True,
        profile: str | None = None,
    ) -> dict[str, ObjectConfigGraphRenderer]:
        """
        Get the configured default renderers for a specific language.

        Returns a mapping of renderer name -> ObjectConfigGraphRenderer.
        """
        plugin = cls.get(language)
        return plugin.get_default_renderers(output_directory, layout_strategy, overwrite, profile=profile)

    @classmethod
    def get_surgical_renderer(
        cls,
        entity_config: Any,
        language: CodeLanguage,
        section_index: CodeSectionBuilderIndex,
        layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
        baseline_graph: ObjectConfigGraph | None = None,
        new_graph: ObjectConfigGraph | None = None,
        namespace: str = "default",
    ) -> MetaRenderer:
        """
        Get a renderer for a specific entity and language.

        Args:
            entity_config: The entity configuration object
            language: The target language
            section_index: Index for looking up existing sections
            layout_strategy: Strategy for determining file paths
            baseline_graph: The baseline ObjectConfigGraph for lookups
            new_graph: The new ObjectConfigGraph for lookups
            namespace: Default namespace for annotations

        Returns:
            MetaRenderer instance with all dependencies injected

        Raises:
            KeyError: If no plugin or renderer found for the entity type
        """
        plugin = cls.get(language)
        entity_type = type(entity_config)
        return plugin.get_surgical_renderer(
            entity_type,
            section_index=section_index,
            layout_strategy=layout_strategy,
            baseline_graph=baseline_graph,
            new_graph=new_graph,
            namespace=namespace,
        )

    # -----------------------------------------------------------------------------
    # Canonical (AWARE) -> Runtime IR -> Language
    # -----------------------------------------------------------------------------

    @classmethod
    def get_runtime_to_language_transformer(
        cls,
        target_language: CodeLanguage,
        profile: str | None = None,
        **kwargs,
    ) -> ObjectConfigGraphTransformer | None:
        """
        Return the runtime IR -> target language transformer, if registered for that language.

        When not present, callers should treat this as an identity step.
        """
        plugin = cls.get(target_language)
        tx_cls = getattr(plugin, "runtime_to_language_transformer", None)
        if tx_cls is None:
            return None
        transformer = tx_cls(**kwargs)
        if profile is not None:
            profile_key = profile.strip()
            if profile_key:
                policy = plugin.transformer_policies_by_profile.get(profile_key)
                if policy is not None:
                    transformer.set_policy(policy)
        return transformer

    @classmethod
    def get_language_to_runtime_transformer(
        cls,
        source_language: CodeLanguage,
        **kwargs,
    ) -> ObjectConfigGraphTransformer | None:
        """
        Return the source language -> runtime IR transformer, if registered for that language.

        Reserved for future bidirectional workflows.
        """
        plugin = cls.get(source_language)
        tx_cls = getattr(plugin, "language_to_runtime_transformer", None)
        if tx_cls is None:
            return None
        return tx_cls(**kwargs)

    @classmethod
    def get_file_filter_config(cls, language: CodeLanguage):
        """
        Get file filter configuration for a specific language.

        Args:
            language: The language to get the filter config for

        Returns:
            FilterConfig instance
        """
        plugin = cls.get(language)
        cfg = plugin.get_file_filter_config()
        override = cls._file_filter_overrides.get(language)
        if override:
            # Merge overrides by copying and extending regex/limits if provided
            merged = cfg.model_copy(update=override.model_dump(exclude_unset=True))
            # Ensure regex lists are combined (model_copy replaces list)
            try:
                base_regex = list(cfg.regex or [])
                over_regex = list(override.regex or [])
                merged.regex = base_regex + over_regex
            except Exception:
                pass
            return merged
        return cfg

    @classmethod
    def has_language(cls, language: CodeLanguage) -> bool:
        """
        Check if a language is supported.

        Args:
            language: The language to check

        Returns:
            True if the language is supported, False otherwise
        """
        return language in cls._supported_languages

    @classmethod
    def get_supported_languages(cls) -> list[CodeLanguage]:
        """
        Get the list of supported languages.

        Returns:
            List of supported CodeLanguage values
        """
        return list(cls._supported_languages)

    @classmethod
    def get_supported_entity_types(cls, language: CodeLanguage) -> list[type[object]]:
        """
        Get the list of supported entity types for a language.

        Args:
            language: The language to get entity types for

        Returns:
            List of supported entity types

        Raises:
            KeyError: If language is not supported
        """
        plugin = cls.get(language)
        return plugin.supported_entity_types

    @classmethod
    def get_layout_strategy(cls, language: CodeLanguage) -> type[ObjectConfigGraphRenderLayoutStrategy] | None:
        """
        Get the layout strategy for a specific language.
        """
        plugin = cls.get(language)
        return plugin.layout_strategy

    @classmethod
    def create_layout_strategy(
        cls,
        language: CodeLanguage,
        base_dir: Path,
        template_paths: dict[str, Path] | None = None,
        entity_template_paths: dict[str, Path] | None = None,
        generated_ocg_node_manifest: GeneratedObjectConfigGraphNodeManifest | None = None,
        import_root: str | None = None,
    ) -> ObjectConfigGraphRenderLayoutStrategy:
        """Create a layout strategy instance using the registered plugin."""

        plugin = cls.get(language)
        layout = plugin.create_layout_strategy(
            base_dir,
            template_paths,
            entity_template_paths,
            generated_ocg_node_manifest,
            import_root=import_root,
        )
        if layout is None:
            raise ValueError(f"No layout strategy registered for {language}")
        return layout

    @classmethod
    def create_package_strategy(
        cls,
        language: CodeLanguage,
        base_dir: Path,
    ) -> ObjectConfigGraphPackageStrategy | None:
        plugin = cls.get(language)
        return plugin.create_package_strategy(base_dir)

    @classmethod
    def configure_package_strategy(
        cls,
        language: CodeLanguage,
        request: "MetaLanguagePackageStrategyConfigurationRequest",
    ) -> None:
        plugin = cls.get(language)
        plugin.configure_package_strategy(request)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered plugins (useful for testing)."""
        cls._plugins.clear()
        cls._supported_languages.clear()
        cls._file_filter_overrides.clear()
        cls._structural_filter_overrides.clear()
        logger.info("Cleared all meta plugins")
