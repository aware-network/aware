from pathlib import Path
from uuid import UUID

import pytest

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
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.graph.projection.stable_ids import stable_object_projection_graph_id


def _build_code(tmp_path: Path, name: str, content: str):
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
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


def test_projection_declarations_compile_into_ocg_declarations_and_seed_observables(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "projection_observables.aware",
        (
            "class Identity {\n"
            "}\n"
            "\n"
            "class ActorFocusRequest {\n"
            "    sender Identity\n"
            "}\n"
            "\n"
            "projection Identity is_branchable {\n"
            "    root Identity\n"
            "    view onboarding {\n"
            "        view welcome construct default {\n"
            '            """\n'
            "            Welcome view.\n"
            '            """\n'
            "        }\n"
            "    }\n"
            "}\n"
            "\n"
            "projection ActorFocus {\n"
            "    root ActorFocusRequest\n"
            "    ActorFocusRequest::sender Identity\n"
            "}\n"
        ),
    )

    ns, domains = _ns(
        fqn_prefix="proj_pkg",
        namespace="main",
        code_ids=[code.id],
    )

    res = build_object_config_graph_from_code(
        name="proj_graph",
        description="proj_graph",
        fqn_prefix="proj_pkg",
        file_codes=[("projection_observables.aware", code)],
        namespace_by_code_id=ns,
    )

    ocg = res.graph
    assert ocg.object_config_graph_identity is not None

    decls_by_name = {
        (d.projection_name or "").strip(): d
        for d in ocg.object_projection_graph_declarations
        if (d.projection_name or "").strip()
    }
    assert "Identity" in decls_by_name
    assert "ActorFocus" in decls_by_name

    identity_decl = decls_by_name["Identity"]
    assert identity_decl.is_branchable is True

    assert not ocg.object_projection_graphs

    opgis_by_opg_id = {
        UUID(str(opgi.object_projection_graph_id)): opgi
        for opgi in ocg.object_config_graph_identity.object_projection_graph_identities
    }

    identity_opg_id = stable_object_projection_graph_id(
        object_config_graph_id=ocg.id,
        name="Identity",
    )
    actor_focus_opg_id = stable_object_projection_graph_id(
        object_config_graph_id=ocg.id,
        name="ActorFocus",
    )
    identity_opgi = opgis_by_opg_id[identity_opg_id]
    assert identity_opgi.is_branchable is True
    observables = identity_opgi.object_projection_graph_observables
    assert any(v.observable_key == "onboarding.welcome" for v in observables)
    welcome = next(v for v in observables if v.observable_key == "onboarding.welcome")
    assert welcome.kind == "construct"
    assert welcome.is_default is True
    assert (welcome.description or "").strip() == "Welcome view."

    dumped = ocg.model_dump(mode="python", exclude_none=True)
    dumped_ocgi = dumped.get("object_config_graph_identity") or {}
    dumped_opgis = dumped_ocgi.get("object_projection_graph_identities") or []
    dumped_opgi = next(
        o
        for o in dumped_opgis
        if UUID(str(o.get("object_projection_graph_id"))) == identity_opg_id
    )
    dumped_views = dumped_opgi.get("object_projection_graph_observables") or []
    assert any(
        (v.get("observable_key") or "").strip() == "onboarding.welcome"
        for v in dumped_views
    )

    assert actor_focus_opg_id in opgis_by_opg_id


def test_projection_observable_multiple_defaults_fails_during_compile(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "projection_multi_default.aware",
        (
            "class Identity {\n"
            "}\n"
            "\n"
            "projection Identity {\n"
            "    root Identity\n"
            "    view onboarding {\n"
            "        view a instance default { }\n"
            "        view b construct default { }\n"
            "    }\n"
            "}\n"
        ),
    )

    ns, domains = _ns(
        fqn_prefix="proj_pkg",
        namespace="main",
        code_ids=[code.id],
    )

    with pytest.raises(ValueError) as excinfo:
        build_object_config_graph_from_code(
            name="proj_graph",
            description="proj_graph",
            fqn_prefix="proj_pkg",
            file_codes=[("projection_multi_default.aware", code)],
            namespace_by_code_id=ns,
        )

    assert "multiple default observables" in str(excinfo.value)


def test_projection_observable_without_explicit_default_seeds_first_observable(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "projection_implicit_default.aware",
        (
            "class Identity {\n"
            "}\n"
            "\n"
            "projection Identity {\n"
            "    root Identity\n"
            "    view onboarding {\n"
            "        view first instance { }\n"
            "        view second construct { }\n"
            "    }\n"
            "}\n"
        ),
    )

    ns, domains = _ns(
        fqn_prefix="proj_pkg",
        namespace="main",
        code_ids=[code.id],
    )

    res = build_object_config_graph_from_code(
        name="proj_graph",
        description="proj_graph",
        fqn_prefix="proj_pkg",
        file_codes=[("projection_implicit_default.aware", code)],
        namespace_by_code_id=ns,
    )

    opgi = next(
        identity
        for identity in res.graph.object_config_graph_identity.object_projection_graph_identities
        if UUID(str(identity.object_projection_graph_id))
        == stable_object_projection_graph_id(
            object_config_graph_id=res.graph.id,
            name="Identity",
        )
    )
    observables = sorted(
        opgi.object_projection_graph_observables,
        key=lambda v: (
            v.position if v.position is not None else 0,
            v.observable_key or "",
        ),
    )
    assert [v.observable_key for v in observables] == [
        "onboarding.first",
        "onboarding.second",
    ]
    assert observables[0].is_default is True
    assert observables[1].is_default is False
