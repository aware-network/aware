from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest

# Kernel Graph Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
)
from aware_meta_ontology.stable_ids import stable_class_instance_id

# Code Runtime
from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

# Aware Grammar
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

# Aware Kernel Meta
from aware_meta.enum.instance.option_resolver import build_enum_option_resolver
from aware_meta.enum.instance.option_resolver import EnumOptionResolutionError
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.graph.config.handlers import build_object_projection_graphs
from aware_meta.fqn_resolver import NamespacePath
from aware_grammar.transformers.aware_to_runtime_transformer import (
    AwareToRuntimeTransformer,
)
from aware_meta.graph.instance.builder import build_object_instance_graph
from aware_meta.graph.instance.validator_opg import (
    validate_object_instance_graph_against_opg,
)


COMMIT_SNIPPET = """
enum CommitStatus {
    applied
    local
}

class Commit {
    status CommitStatus = local
}

projection P {
    root commit.Commit
}
""".strip()

IDENTITY_SNIPPET_IDENTITY = """
enum IdentityType {
    agent
    human
    organization
}

class IdentityProfile {
    display_name String
}

class Identity {
    // Relationships
    human human.Human? unique
    identity_profile IdentityProfile? unique

    // Attributes
    public_key String
    type IdentityType
}

projection P {
    root identity.Identity
    identity.Identity::human
    identity.Identity::identity_profile
}
""".strip()

IDENTITY_SNIPPET_HUMAN = """
class Human { }
""".strip()


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


def _runtime_graph_with_opgs(graph, *, namespace_by_code_id):
    runtime = AwareToRuntimeTransformer(
        namespace_by_code_id=namespace_by_code_id
    ).transform(graph)
    runtime.object_projection_graphs = build_object_projection_graphs(runtime)
    return runtime


def _history_commit(*, status: object) -> object:
    from aware_history_ontology.commit.commit import Commit

    return Commit(
        key="test-commit",
        lane_id=uuid4(),
        author_id=uuid4(),
        status=status,
        created_at=datetime.now(timezone.utc),
    )


def test_enum_option_resolver_builds_oig_for_real_commit_model(tmp_path: Path) -> None:
    # Real model + real enum classes from kernel-graph-ontology Python package.
    from aware_history_ontology.commit.commit import Commit
    from aware_history_ontology.commit.commit_enums import CommitStatus

    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "commit.aware", COMMIT_SNIPPET)
    ns, domains = _ns(
        fqn_prefix="aware", namespace="history.commit", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="commit",
        description="commit",
        fqn_prefix="aware",
        file_codes=[("commit.aware", code)],
        namespace_by_code_id=ns,
    )
    ocg = _runtime_graph_with_opgs(res.graph, namespace_by_code_id=ns)
    opg = next(g for g in ocg.object_projection_graphs if g.name == "P")

    enum_resolver = build_enum_option_resolver(object_config_graph=ocg)

    commit = _history_commit(status=CommitStatus.applied)
    oig = build_object_instance_graph(
        root_instance=commit,
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="oig",
        description="oig",
        enum_option_resolver=enum_resolver,
    )
    validate_object_instance_graph_against_opg(
        graph=oig, object_config_graph=ocg, object_projection_graph=opg
    )

    commit_cc = next(
        n.class_config
        for n in ocg.object_config_graph_nodes
        if n.class_config and n.class_config.name == "Commit"
    )
    assert commit_cc is not None
    root_ci_id = stable_class_instance_id(
        object_instance_graph_id=oig.id,
        class_config_id=commit_cc.id,
        source_object_id=commit.id,
    )
    assert oig.root_class_instance_id == root_ci_id
    assert len(oig.class_instances) == 1
    root = oig.class_instances[0]
    assert root.id == root_ci_id
    assert len(root.attributes) == 1

    # Validate enum option id matches the EnumConfig option for applied.
    enum_cfg = next(
        n.enum_config
        for n in ocg.object_config_graph_nodes
        if n.enum_config and n.enum_config.name == "CommitStatus"
    )
    applied_opt = next(o for o in enum_cfg.enum_options if o.value == "applied")
    assert root.attributes[0].value_root is not None
    assert root.attributes[0].value_root.enum_option_id == applied_opt.id


def test_enum_option_resolver_accepts_wire_value_strings(tmp_path: Path) -> None:
    from aware_history_ontology.commit.commit import Commit

    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "commit.aware", COMMIT_SNIPPET)
    ns, domains = _ns(
        fqn_prefix="aware", namespace="history.commit", code_ids=[code.id]
    )
    ocg = _runtime_graph_with_opgs(
        build_object_config_graph_from_code(
            name="commit",
            description="commit",
            fqn_prefix="aware",
            file_codes=[("commit.aware", code)],
            namespace_by_code_id=ns,
        ).graph,
        namespace_by_code_id=ns,
    )
    opg = next(g for g in ocg.object_projection_graphs if g.name == "P")
    enum_resolver = build_enum_option_resolver(object_config_graph=ocg)

    # Pydantic will coerce string into CommitStatus Enum, but even if it doesn't,
    # the resolver supports raw strings.
    commit = _history_commit(status="applied")  # type: ignore[arg-type]
    oig = build_object_instance_graph(
        root_instance=commit,
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="oig",
        description="oig",
        enum_option_resolver=enum_resolver,
    )
    validate_object_instance_graph_against_opg(
        graph=oig, object_config_graph=ocg, object_projection_graph=opg
    )
    assert oig.class_instances[0].attributes[0].value_root is not None
    assert oig.class_instances[0].attributes[0].value_root.enum_option_id is not None


def test_enum_option_resolver_unknown_value_raises(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "commit.aware", COMMIT_SNIPPET)
    ns, domains = _ns(
        fqn_prefix="aware", namespace="history.commit", code_ids=[code.id]
    )
    ocg = build_object_config_graph_from_code(
        name="commit",
        description="commit",
        fqn_prefix="aware",
        file_codes=[("commit.aware", code)],
        namespace_by_code_id=ns,
    ).graph

    enum_resolver = build_enum_option_resolver(object_config_graph=ocg)

    # Minimal descriptor invocation: resolve directly through the resolver.
    enum_node = next(
        n.enum_config
        for n in ocg.object_config_graph_nodes
        if n.enum_config and n.enum_config.name == "CommitStatus"
    )
    enum_cfg_id = enum_node.id

    # Build a synthetic type descriptor pointing at the EnumConfig.
    desc = AttributeTypeDescriptor(kind=Kind.enum, enum_config_id=enum_cfg_id)

    with pytest.raises(EnumOptionResolutionError):
        enum_resolver(desc, "does_not_exist")


def test_enum_option_resolver_builds_oig_with_relationships_and_registry_fallback(
    tmp_path: Path,
) -> None:
    # Real model + real enum classes from kernel-graph-ontology Python package.
    from aware_identity_ontology.human.human import Human
    from aware_identity_ontology.identity.identity import Identity
    from aware_identity_ontology.identity.identity_enums import IdentityType
    from aware_identity_ontology.identity.identity_profile import IdentityProfile

    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code_identity = _build_code(tmp_path, "identity.aware", IDENTITY_SNIPPET_IDENTITY)
    code_human = _build_code(tmp_path, "human.aware", IDENTITY_SNIPPET_HUMAN)

    namespace_by_code_id = {
        code_identity.id: NamespacePath(package="aware", namespace="identity.identity"),
        code_human.id: NamespacePath(package="aware", namespace="identity.human"),
    }

    ocg = build_object_config_graph_from_code(
        name="identity",
        description="identity",
        fqn_prefix="aware",
        file_codes=[
            ("identity.aware", code_identity),
            ("human.aware", code_human),
        ],
        namespace_by_code_id=namespace_by_code_id,
    ).graph

    # Runtime IR is SSOT for deterministic FK bindings (no `<ref>_id` guessing).
    from aware_grammar.transformers.aware_to_runtime_transformer import (
        AwareToRuntimeTransformer,
    )

    ocg = AwareToRuntimeTransformer(
        namespace_by_code_id=namespace_by_code_id
    ).transform(ocg)
    from aware_meta.graph.config.handlers import build_object_projection_graphs

    opg = next(g for g in build_object_projection_graphs(ocg) if g.name == "P")
    enum_resolver = build_enum_option_resolver(object_config_graph=ocg)

    profile = IdentityProfile(
        id=uuid4(),
        bio=None,
        country_code="US",
        display_name="Luis",
        full_name="Luis F",
        language_code="en",
        public_handle="luis",
        image_id=None,
    )

    identity_id = uuid4()
    human = Human(id=uuid4(), actor_id=uuid4())

    identity = Identity(
        id=identity_id,
        public_key="pk",
        type=IdentityType.human,
        identity_profile_id=profile.id,  # FK present (relationship is not hydrated)
        organization_id=None,
        human=human,  # hydrated reference (no human_id FK exists)
    )

    oig = build_object_instance_graph(
        root_instance=identity,
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="oig",
        description="oig",
        enum_option_resolver=enum_resolver,
        instance_registry=[profile],
    )
    validate_object_instance_graph_against_opg(
        graph=oig, object_config_graph=ocg, object_projection_graph=opg
    )

    identity_cc = next(
        n.class_config
        for n in ocg.object_config_graph_nodes
        if n.class_config and n.class_config.name == "Identity"
    )
    human_cc = next(
        n.class_config
        for n in ocg.object_config_graph_nodes
        if n.class_config and n.class_config.name == "Human"
    )
    profile_cc = next(
        n.class_config
        for n in ocg.object_config_graph_nodes
        if n.class_config and n.class_config.name == "IdentityProfile"
    )
    assert identity_cc is not None and human_cc is not None and profile_cc is not None
    identity_ci_id = stable_class_instance_id(
        object_instance_graph_id=oig.id,
        class_config_id=identity_cc.id,
        source_object_id=identity.id,
    )
    human_ci_id = stable_class_instance_id(
        object_instance_graph_id=oig.id,
        class_config_id=human_cc.id,
        source_object_id=human.id,
    )
    profile_ci_id = stable_class_instance_id(
        object_instance_graph_id=oig.id,
        class_config_id=profile_cc.id,
        source_object_id=profile.id,
    )
    assert oig.root_class_instance_id == identity_ci_id
    assert {ci.id for ci in oig.class_instances} == {
        identity_ci_id,
        human_ci_id,
        profile_ci_id,
    }
    assert len(oig.class_instance_relationships) == 2

    # Identity attributes: includes data attrs, excludes relationship attrs.
    identity_cc = next(
        n.class_config
        for n in ocg.object_config_graph_nodes
        if n.class_config and n.class_config.name == "Identity"
    )
    attrs_by_name = {
        link.attribute_config.name: link.attribute_config.id
        for link in identity_cc.class_config_attribute_configs
        if link.attribute_config is not None
    }

    identity_ci = next(ci for ci in oig.class_instances if ci.id == identity_ci_id)
    identity_attr_ids = {a.attribute_config_id for a in identity_ci.attributes}
    assert attrs_by_name["public_key"] in identity_attr_ids
    assert attrs_by_name["type"] in identity_attr_ids
    assert attrs_by_name["human"] not in identity_attr_ids
    assert attrs_by_name["identity_profile"] not in identity_attr_ids

    # Enum option id matches the OCG EnumConfig option for human.
    enum_cfg = next(
        n.enum_config
        for n in ocg.object_config_graph_nodes
        if n.enum_config and n.enum_config.name == "IdentityType"
    )
    human_opt = next(o for o in enum_cfg.enum_options if o.value == "human")
    type_attr = next(
        a
        for a in identity_ci.attributes
        if a.attribute_config_id == attrs_by_name["type"]
    )
    assert type_attr.value_root is not None
    assert type_attr.value_root.enum_option_id == human_opt.id

    # IdentityProfile is resolved via registry fallback (`identity_profile_id`) and built as an instance.
    profile_cc = next(
        n.class_config
        for n in ocg.object_config_graph_nodes
        if n.class_config and n.class_config.name == "IdentityProfile"
    )
    display_name_attr_cfg_id = next(
        link.attribute_config.id
        for link in profile_cc.class_config_attribute_configs
        if link.attribute_config is not None
        and link.attribute_config.name == "display_name"
    )
    profile_ci = next(ci for ci in oig.class_instances if ci.id == profile_ci_id)
    display_name_attr = next(
        a
        for a in profile_ci.attributes
        if a.attribute_config_id == display_name_attr_cfg_id
    )
    assert display_name_attr.value_root is not None
    assert display_name_attr.value_root.primitive_value == {"value": "Luis"}
