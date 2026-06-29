from __future__ import annotations

from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.tree.tree import CodeTree
from aware_code_ontology.code.code_enums import CodeLanguage


def parse_content_tree(*, content: str, language: CodeLanguage) -> CodeTree[object]:
    language_plugin = CodeLanguagePluginRegistry.get_typed(language)
    code_tree = language_plugin.tree_sitter_adapter.parse_content(content)
    if not code_tree:
        raise ValueError("Failed to parse content directly")
    return code_tree
