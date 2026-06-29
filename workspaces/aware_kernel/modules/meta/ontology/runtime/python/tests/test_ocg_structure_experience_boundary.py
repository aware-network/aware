# @code-under-test: ../aware_meta/graph/config/builder.py

from pathlib import Path
from uuid import UUID

import pytest

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Code Runtime
from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

# Aware Grammar (canonical plugins)
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

# Meta Ontology

# Meta Runtime
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code


def _build_code(tmp_path: Path, name: str, content: str):
    p = tmp_path / name
    p.write_text(content)
    sections_index = CodeSectionBuilderIndex()
    return build_code_from_file(
        sections_index=sections_index,
        file_path=str(p),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _ns(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }, []


def test_ocg_builder_rejects_event_sections_in_structure_packages(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "event_token.aware",
        """
class Conversation {
    title String
}

event ConversationCreated name "conversation.created" renderer "conversation.created" title "Conversation Created" description "Conversation creation domain event." {
    bind conversation boundary.Conversation create
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="boundary", namespace="default", code_ids=[code.id]
    )

    with pytest.raises(ValueError, match="Structure package boundary violation"):
        build_object_config_graph_from_code(
            name="boundary",
            description="boundary",
            fqn_prefix="boundary",
            file_codes=[("event_token.aware", code)],
            namespace_by_code_id=ns,
        )


def test_ocg_builder_rejects_program_sections_in_structure_packages(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "program_token.aware",
        """
class Conversation {
    title String
}

program ConversationTurn_v1(conversation_id UUID) {
    let label = "turn"
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="boundary", namespace="default", code_ids=[code.id]
    )

    with pytest.raises(ValueError, match="Structure package boundary violation"):
        build_object_config_graph_from_code(
            name="boundary",
            description="boundary",
            fqn_prefix="boundary",
            file_codes=[("program_token.aware", code)],
            namespace_by_code_id=ns,
        )
