# @code-under-test: ../aware_meta/fqn_resolver.py

from pathlib import Path
from uuid import UUID

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info
from aware_meta.fqn_resolver import NamespacePath, authored_ref_from_fqn
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


def _namespaces(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }


def test_authored_ref_from_fqn_omits_default_namespace_segments() -> None:
    assert (
        authored_ref_from_fqn("aware_home.default.home.Home") == "aware_home.home.Home"
    )
    assert (
        authored_ref_from_fqn("aware_demo.default.default.Device")
        == "aware_demo.Device"
    )


DEP_CODE = """
class Actor {
    id String
}
""".strip()


LOCAL_CODE = """
class OwnershipCreator {
    actor aware_identity.actor.Actor
}
""".strip()


def test_fqn_resolver_allows_package_namespace_name_shorthand_for_external_graph(
    tmp_path: Path,
) -> None:
    """
    Cross-package type reference ergonomics:

    When an external dependency graph is present, allow referencing a class by
    package plus namespace plus name.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    dep_code = _build_code(tmp_path, "dep_actor.aware", DEP_CODE)
    dep_ns = _namespaces(
        fqn_prefix="aware_identity",
        namespace="actor",
        code_ids=[dep_code.id],
    )
    dep_res = build_object_config_graph_from_code(
        name="dep",
        description="dep",
        fqn_prefix="aware_identity",
        file_codes=[("dep_actor", dep_code)],
        namespace_by_code_id=dep_ns,
    )

    local_code = _build_code(tmp_path, "local_owner.aware", LOCAL_CODE)
    local_ns = _namespaces(
        fqn_prefix="aware_meta_ontology",
        namespace="meta.ownership",
        code_ids=[local_code.id],
    )
    local_res = build_object_config_graph_from_code(
        name="local",
        description="local",
        fqn_prefix="aware_meta_ontology",
        file_codes=[("local_owner", local_code)],
        namespace_by_code_id=local_ns,
        external_graphs=[dep_res.graph],
    )

    owner_cc = next(
        n.class_config
        for n in local_res.graph.object_config_graph_nodes
        if n.class_config is not None and n.class_config.name == "OwnershipCreator"
    )
    actor_attr = next(
        link.attribute_config
        for link in owner_cc.class_config_attribute_configs
        if link.attribute_config is not None and link.attribute_config.name == "actor"
    )
    type_info = resolve_type_info(actor_attr)
    assert type_info.kind.value == "class"
    assert type_info.class_config is not None
    assert type_info.class_config.name == "Actor"

    dep_actor_cc = next(
        n.class_config
        for n in dep_res.graph.object_config_graph_nodes
        if n.class_config is not None and n.class_config.name == "Actor"
    )
    assert type_info.class_config.id == dep_actor_cc.id


def test_fqn_resolver_uses_persisted_external_class_fqn_without_domain_topology(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    dep_code = _build_code(tmp_path, "dep_actor_fqn.aware", DEP_CODE)
    dep_ns = _namespaces(
        fqn_prefix="aware_identity",
        namespace="actor",
        code_ids=[dep_code.id],
    )
    dep_res = build_object_config_graph_from_code(
        name="dep",
        description="dep",
        fqn_prefix="aware_identity",
        file_codes=[("dep_actor_fqn", dep_code)],
        namespace_by_code_id=dep_ns,
    )
    dep_runtime = dep_res.graph.model_copy(deep=True)

    dep_actor_cc = next(
        n.class_config
        for n in dep_runtime.object_config_graph_nodes
        if n.class_config is not None and n.class_config.name == "Actor"
    )
    assert dep_actor_cc.class_fqn == "aware_identity.actor.Actor"

    local_code = _build_code(tmp_path, "local_owner_fqn.aware", LOCAL_CODE)
    local_ns = _namespaces(
        fqn_prefix="aware_meta_ontology",
        namespace="meta.ownership",
        code_ids=[local_code.id],
    )
    local_res = build_object_config_graph_from_code(
        name="local",
        description="local",
        fqn_prefix="aware_meta_ontology",
        file_codes=[("local_owner_fqn", local_code)],
        namespace_by_code_id=local_ns,
        external_graphs=[dep_runtime],
    )

    owner_cc = next(
        n.class_config
        for n in local_res.graph.object_config_graph_nodes
        if n.class_config is not None and n.class_config.name == "OwnershipCreator"
    )
    actor_attr = next(
        link.attribute_config
        for link in owner_cc.class_config_attribute_configs
        if link.attribute_config is not None and link.attribute_config.name == "actor"
    )
    type_info = resolve_type_info(actor_attr)
    assert type_info.kind.value == "class"
    assert type_info.class_config is not None
    assert type_info.class_config.id == dep_actor_cc.id
