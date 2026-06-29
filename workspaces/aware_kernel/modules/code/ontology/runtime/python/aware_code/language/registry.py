"""Registry for managing language-specific code plugins.

This module provides a singleton registry that manages CodeLanguagePlugin instances,
similar to how MetaLanguagePluginRegistry manages MetaLanguagePlugin instances.
"""

from __future__ import annotations

from typing import cast

# Kernel Graph Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Code Runtime
from aware_code.language.plugin import CodeLanguagePlugin
from aware_code.node.adapter import CodeNodeAdapter
from aware_code.node.node import T_Node
from aware_code.primitive_codec import CodePrimitiveCodec
from aware_code.tree.adapter import CodeTreeAdapter

from aware_utils.logging import logger


class CodeLanguagePluginRegistry:
    """
    Singleton registry for CodeLanguagePlugin instances.

    Similar to MetaLanguagePluginRegistry but for code-layer operations:
    - Code building and parsing
    - Node adaptation
    - Tree sitter integration
    """

    _plugins: dict[CodeLanguage, CodeLanguagePlugin[object]] = {}
    _supported_languages: set[CodeLanguage] = set()

    @classmethod
    def register(cls, plugin: CodeLanguagePlugin[T_Node]) -> None:
        """
        Register a language plugin.

        Args:
            plugin: Complete language plugin containing all components
        """
        if plugin.language not in cls._supported_languages:
            cls._plugins[plugin.language] = cast(CodeLanguagePlugin[object], plugin)
            cls._supported_languages.add(plugin.language)

    @classmethod
    def get(cls, language: CodeLanguage) -> CodeLanguagePlugin[object]:
        """
        Get the language plugin for a specific language.

        Args:
            language: The language to get the plugin for

        Returns:
            CodeLanguagePlugin instance

        Raises:
            KeyError: If no plugin registered for the language
        """
        if language not in cls._plugins:
            raise KeyError(f"No language plugin registered for language: {language}")

        return cls._plugins[language]

    @classmethod
    def get_typed(cls, language: CodeLanguage) -> CodeLanguagePlugin[T_Node]:
        """Get the language plugin with caller-provided node typing."""
        return cast(CodeLanguagePlugin[T_Node], cls.get(language))

    @classmethod
    def get_language_from_extension(cls, extension: str) -> CodeLanguage | None:
        """Get the language from a file extension."""
        for language, plugin in cls._plugins.items():
            if extension in plugin.extensions:
                return language
        return None

    @classmethod
    def get_node_adapter(
        cls,
        language: CodeLanguage,
        section_type: CodeSectionType,
    ) -> CodeNodeAdapter[object] | None:
        """Get a node adapter for the specified language and type."""
        if language not in cls._supported_languages:
            logger.warning(f"Language {language} is not supported")
            return None

        plugin = cls._plugins.get(language)
        if not plugin:
            return None

        return plugin.node_adapters.get(section_type)

    @classmethod
    def get_tree_adapter(cls, language: CodeLanguage) -> CodeTreeAdapter[object] | None:
        """Get a tree adapter for the specified language."""
        plugin = cls._plugins.get(language)
        return plugin.tree_sitter_adapter if plugin else None

    @classmethod
    def get_code_primitive_codec(cls, language: CodeLanguage) -> CodePrimitiveCodec:
        """Get the code primitive codec for a given language."""
        return cls._plugins[language].primitive_codec

    @classmethod
    def get_supported_languages(cls) -> list[CodeLanguage]:
        """Get the list of supported languages."""
        return list(cls._supported_languages)

    @classmethod
    def has_language(cls, language: CodeLanguage) -> bool:
        """Check if a language is supported."""
        return language in cls._supported_languages

    @classmethod
    def clear(cls) -> None:
        """Clear all registered plugins (useful for testing)."""
        cls._plugins.clear()
        cls._supported_languages.clear()
        logger.info("Cleared all language plugins")
