# @code-under-test: ../aware_meta/function/verb_policy.py
# @code-under-test: ../aware_meta/function/builder.py
# @code-under-test: ../aware_meta/class_/config/builder.py

from pathlib import Path
from uuid import UUID

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

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


READ_CODE = """
class User {
    fn get_profile read(public_key String) -> String {
        \"\"\"Read-only identity lookup.\"\"\"
    }
}
""".strip()


UNKNOWN_VERB_CODE = """
class User {
    fn mutate mutate(public_key String) -> String {
        \"\"\"Unknown verb should fail canonical validation.\"\"\"
    }
}
""".strip()


def test_meta_builder_rejects_read_verb(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "read_verbs.aware", READ_CODE)
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    with pytest.raises(ValueError, match="Unknown function verb"):
        build_object_config_graph_from_code(
            name="read_verbs",
            description="read_verbs",
            fqn_prefix="pkg",
            file_codes=[("read_verbs.aware", code)],
            namespace_by_code_id=ns,
        )


def test_meta_builder_rejects_unknown_verbs(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "unknown_verb.aware", UNKNOWN_VERB_CODE)
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )

    with pytest.raises(ValueError, match="Unknown function verb"):
        build_object_config_graph_from_code(
            name="unknown_verbs",
            description="unknown_verbs",
            fqn_prefix="pkg",
            file_codes=[("unknown_verb.aware", code)],
            namespace_by_code_id=ns,
        )
