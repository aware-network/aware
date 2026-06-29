from pathlib import Path
from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta Ontology

# Code Runtime
from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

# Aware Grammar (canonical plugins)
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

# Meta Runtime
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.fqn_resolver import NamespacePath


DEF_SAMPLE_CODE = """
class User {
    posts Post[]
}

class Post {
    title String
}
"""

DEF_SAMPLE_CODE_REFERENCE_BASE = """
class Actor {
    authored_commits Commit[]
}

class Commit {
    author_id UUID
    other_id UUID
}
"""

DEF_SAMPLE_CODE_IDENTITY_BASE = """
class ReusableAttribute {
    owner_key String key
    name String key
}
"""

DEF_SAMPLE_CODE_ENUM_BASE = """
enum Status {
    active
    inactive
}
"""

DEF_SAMPLE_CODE_ENUM_EXTENDED = """
enum Status {
    active
    inactive
    pending
}
"""


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


def test_ocg_hash_changes_when_projection_declarations_change(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    base_topology = DEF_SAMPLE_CODE.strip()

    code_a = _build_code(
        tmp_path,
        "a.aware",
        base_topology + "\n\nprojection P1 { root default.User }\n",
    )
    code_b = _build_code(
        tmp_path,
        "b.aware",
        base_topology + "\n\nprojection P2 { root default.User }\n",
    )

    ns_a, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code_a.id]
    )
    ns_b, _ = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code_b.id]
    )

    g1 = build_object_config_graph_from_code(
        name="g1",
        description="g1",
        fqn_prefix="pkg",
        file_codes=[("a.aware", code_a)],
        namespace_by_code_id=ns_a,
    ).graph
    g2 = build_object_config_graph_from_code(
        name="g2",
        description="g2",
        fqn_prefix="pkg",
        file_codes=[("b.aware", code_b)],
        namespace_by_code_id=ns_b,
    ).graph

    assert (
        g1.hash != g2.hash
    ), "Changing projection declaration semantics must change the OCG hash"


def test_ocg_hash_changes_when_load_strategy_changes(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    base_topology = DEF_SAMPLE_CODE.strip()

    code_a = _build_code(
        tmp_path,
        "a.aware",
        base_topology + "\n\nann default.User::posts load forward eager reverse lazy\n",
    )
    code_b = _build_code(
        tmp_path,
        "b.aware",
        base_topology + "\n\nann default.User::posts load forward lazy reverse eager\n",
    )

    ns_a, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code_a.id]
    )
    ns_b, _ = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code_b.id]
    )

    g1 = build_object_config_graph_from_code(
        name="g1",
        description="g1",
        fqn_prefix="pkg",
        file_codes=[("a.aware", code_a)],
        namespace_by_code_id=ns_a,
    ).graph
    g2 = build_object_config_graph_from_code(
        name="g2",
        description="g2",
        fqn_prefix="pkg",
        file_codes=[("b.aware", code_b)],
        namespace_by_code_id=ns_b,
    ).graph

    assert (
        g1.hash != g2.hash
    ), "Changing relationship load strategies must change the OCG hash"


def test_ocg_hash_changes_when_reference_binding_changes(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    base = DEF_SAMPLE_CODE_REFERENCE_BASE.strip()

    code_a = _build_code(
        tmp_path,
        "a_ref.aware",
        base
        + "\n\nann default.Commit::author_id reference port\n"
        + 'ann default.Actor::authored_commits reference bind "default.Commit::author_id"\n',
    )
    code_b = _build_code(
        tmp_path,
        "b_ref.aware",
        base
        + "\n\nann default.Commit::other_id reference port\n"
        + 'ann default.Actor::authored_commits reference bind "default.Commit::other_id"\n',
    )

    ns_a, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code_a.id]
    )
    ns_b, _ = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code_b.id]
    )

    g1 = build_object_config_graph_from_code(
        name="g1",
        description="g1",
        fqn_prefix="pkg",
        file_codes=[("a_ref.aware", code_a)],
        namespace_by_code_id=ns_a,
    ).graph
    g2 = build_object_config_graph_from_code(
        name="g2",
        description="g2",
        fqn_prefix="pkg",
        file_codes=[("b_ref.aware", code_b)],
        namespace_by_code_id=ns_b,
    ).graph

    assert (
        g1.hash != g2.hash
    ), "Changing reference binding semantics must change the OCG hash"


def test_ocg_hash_changes_when_identity_scope_changes(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    base = DEF_SAMPLE_CODE_IDENTITY_BASE.strip()

    code_a = _build_code(
        tmp_path,
        "a_identity.aware",
        base + "\n\nann default.ReusableAttribute identity contained\n",
    )
    code_b = _build_code(
        tmp_path,
        "b_identity.aware",
        base + "\n\nann default.ReusableAttribute identity standalone\n",
    )

    ns_a, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code_a.id]
    )
    ns_b, _ = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code_b.id]
    )

    g1 = build_object_config_graph_from_code(
        name="g1",
        description="g1",
        fqn_prefix="pkg",
        file_codes=[("a_identity.aware", code_a)],
        namespace_by_code_id=ns_a,
    ).graph
    g2 = build_object_config_graph_from_code(
        name="g2",
        description="g2",
        fqn_prefix="pkg",
        file_codes=[("b_identity.aware", code_b)],
        namespace_by_code_id=ns_b,
    ).graph

    assert (
        g1.hash != g2.hash
    ), "Changing identity scope semantics must change the OCG hash"


def test_ocg_hash_changes_when_enum_options_change(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code_a = _build_code(
        tmp_path,
        "a_enum.aware",
        DEF_SAMPLE_CODE_ENUM_BASE.strip(),
    )
    code_b = _build_code(
        tmp_path,
        "b_enum.aware",
        DEF_SAMPLE_CODE_ENUM_EXTENDED.strip(),
    )

    ns_a, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code_a.id]
    )
    ns_b, _ = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code_b.id]
    )

    g1 = build_object_config_graph_from_code(
        name="g1",
        description="g1",
        fqn_prefix="pkg",
        file_codes=[("a_enum.aware", code_a)],
        namespace_by_code_id=ns_a,
    ).graph
    g2 = build_object_config_graph_from_code(
        name="g2",
        description="g2",
        fqn_prefix="pkg",
        file_codes=[("b_enum.aware", code_b)],
        namespace_by_code_id=ns_b,
    ).graph

    assert (
        g1.hash != g2.hash
    ), "Changing enum option membership must change the OCG hash"
