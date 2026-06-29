# @code-under-test: ../aware_meta/graph/config/relationship_analysis.py

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta Ontology
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipType,
)

# Code Runtime
from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

# Aware Grammar (canonical plugins)
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

# Meta Runtime
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.graph.config.relationship_analysis import analyze_relationships
from aware_meta.graph.config.relationship_analysis import (
    ClassConfigRelationshipIdentityRail,
    build_object_config_graph_analysis_bundle,
    compute_fk_materialization_plan,
    fk_db_requiredness_from_relationship_semantics,
    fk_runtime_requiredness_from_relationship_semantics,
    index_fk_override_annotations,
    resolve_fk_override,
    stable_reified_association_source_relationship_id,
    stable_reified_association_target_relationship_id,
)
from aware_meta.fqn_resolver import NamespacePath
from aware_meta_ontology.graph.config.object_config_graph_relationship import (
    ObjectConfigGraphRelationship,
)

DEFAULT_CODE = """
class User {
    profile Profile unique
    posts Post[]
    org Organization
}

class Profile { id String }
class Post { id String }
class Organization { id String }

class Group { id String }
class Membership {
    users User[] @UserGroupEdge many
}
edge UserGroupEdge { status String }
"""

DEFAULT_CODE_WITH_OVERRIDES = """
class User {
    posts Post[]
    org Organization
    opt_org Organization?
}

class Post { id String }
class Organization { id String }

ann default.User::org load forward eager
ann default.User::posts load reverse eager
ann default.User::org override fk nullable name org_id_custom
"""

CONTAINMENT_ONE_TO_ONE_CODE = """
class Parent {
    child Child unique

    fn add_child(value String) -> UUID {
        let built = construct child.build(value = value)
    }
}

class Child {
    fn build construct(value String) -> Child {
    }
}
"""

CONTAINMENT_MANY_TO_ONE_FORBIDDEN_CODE = """
class Parent {
    child Child

    fn add_child(value String) -> UUID {
        let built = construct child.build(value = value)
    }
}

class Child {
    fn build construct(value String) -> Child {
    }
}
"""

ASSOCIATION_EDGE_CONTAINMENT_MANY_TO_ONE_CODE = """
class Parent {
    child Child? @ParentChildEdge

    fn attach_child(child_id UUID) -> UUID {
        let edge = construct child.build(child_id = child_id)
    }
}

class Child { id String }

edge ParentChildEdge {
    fn build construct(child_id UUID key) -> ParentChildEdge {
    }
}
"""

STANDALONE_EDGE_CONSTRUCT_REFERENCE_CODE = """
class Parent {
    attrs ParentAttributeEdge[]

    fn add_attr(owner_key String, name String) -> UUID {
        let edge = construct attrs.build(owner_key = owner_key, name = name)
    }
}

edge ParentAttributeEdge {
    attribute_config AttributeConfig

    fn build construct(owner_key String, name String) -> ParentAttributeEdge {
        let created = construct attribute_config.create(owner_key = owner_key, name = name)
    }
}

class AttributeConfig {
    owner_key String key
    name String key

    fn create construct(owner_key String key, name String key) -> AttributeConfig {
    }
}

ann default.AttributeConfig identity standalone
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


def test_relationship_type_derivation_is_purely_grammar_driven(tmp_path: Path) -> None:
    """
    Aware grammar encodes relationship cardinality via:
    - list marker `[]`
    - `many` keyword (many-to-many)
    - `unique` keyword (one-to-one)

    Kernel-meta builder turns that into relationship_type with no heuristics:
    - CLASS[] many   => MANY_TO_MANY
    - CLASS[]        => ONE_TO_MANY
    - CLASS unique   => ONE_TO_ONE
    - CLASS          => MANY_TO_ONE
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "rels.aware",
        DEFAULT_CODE.strip(),
    )

    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="rels",
        description="rels",
        fqn_prefix="pkg",
        file_codes=[("rels.aware", code)],
        namespace_by_code_id=ns,
    )

    analyses = analyze_relationships(res.graph, namespace_by_code_id=ns)
    assert analyses

    by_sig = {
        (a.source_class.name, a.forward_reference_attr.name, a.target_class.name): a
        for a in analyses
    }

    # profile Profile unique -> ONE_TO_ONE, FK on source (forward)
    a_profile = by_sig[("User", "profile", "Profile")]
    assert a_profile.relationship_type == ClassConfigRelationshipType.one_to_one
    assert a_profile.fk_owner_side == ClassConfigRelationshipDirection.forward
    assert a_profile.fk_owner_class and a_profile.fk_owner_class.name == "User"
    assert a_profile.fk_column_name == "profile_id"

    # posts Post[] -> ONE_TO_MANY, FK on target (reverse)
    a_posts = by_sig[("User", "posts", "Post")]
    assert a_posts.relationship_type == ClassConfigRelationshipType.one_to_many
    assert a_posts.fk_owner_side == ClassConfigRelationshipDirection.reverse
    assert a_posts.fk_owner_class and a_posts.fk_owner_class.name == "Post"
    assert a_posts.fk_column_name == "user_id"

    # org Organization -> MANY_TO_ONE, FK on source (forward)
    a_org = by_sig[("User", "org", "Organization")]
    assert a_org.relationship_type == ClassConfigRelationshipType.many_to_one
    assert a_org.fk_owner_side == ClassConfigRelationshipDirection.forward
    assert a_org.fk_owner_class and a_org.fk_owner_class.name == "User"
    assert a_org.fk_column_name == "org_id"

    # users User[] many @UserGroupEdge -> MANY_TO_MANY, association present, join-table required
    a_users = by_sig[("Membership", "users", "User")]
    assert a_users.relationship_type == ClassConfigRelationshipType.many_to_many
    assert a_users.requires_join_table is True
    assert a_users.association_class is not None
    assert a_users.association_class.name == "UserGroupEdge"
    assert a_users.fk_owner_side is None

    # Analysis bundle must recognize association edges under BOTH:
    # - the canonical relationship id (pre-reification), and
    # - the stable reified runtime relationship ids (post-reification).
    bundle = build_object_config_graph_analysis_bundle(
        res.graph, namespace_by_code_id=ns
    )
    assoc_id = a_users.association_class.id
    assert (
        bundle.association_class_id_by_relationship_id[a_users.relationship.id]
        == assoc_id
    )
    assert (
        bundle.association_class_id_by_relationship_id[
            stable_reified_association_source_relationship_id(
                relationship_id=a_users.relationship.id
            )
        ]
        == assoc_id
    )
    assert (
        bundle.association_class_id_by_relationship_id[
            stable_reified_association_target_relationship_id(
                relationship_id=a_users.relationship.id
            )
        ]
        == assoc_id
    )


def test_containment_one_to_one_is_child_fk_owned(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "containment_one_to_one.aware",
        CONTAINMENT_ONE_TO_ONE_CODE.strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="containment_one_to_one",
        description="containment_one_to_one",
        fqn_prefix="pkg",
        file_codes=[("containment_one_to_one.aware", code)],
        namespace_by_code_id=ns,
    )

    analyses = analyze_relationships(res.graph, namespace_by_code_id=ns)
    by_sig = {
        (a.source_class.name, a.forward_reference_attr.name, a.target_class.name): a
        for a in analyses
    }
    rel = by_sig[("Parent", "child", "Child")]

    assert rel.identity_rail == ClassConfigRelationshipIdentityRail.containment
    assert rel.relationship_type == ClassConfigRelationshipType.one_to_one
    assert rel.fk_owner_side == ClassConfigRelationshipDirection.reverse
    assert rel.fk_owner_class and rel.fk_owner_class.name == "Child"
    assert rel.fk_target_class and rel.fk_target_class.name == "Parent"
    assert rel.fk_column_name == "parent_id"


def test_containment_many_to_one_fails_closed(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "containment_many_to_one_forbidden.aware",
        CONTAINMENT_MANY_TO_ONE_FORBIDDEN_CODE.strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="containment_many_to_one_forbidden",
        description="containment_many_to_one_forbidden",
        fqn_prefix="pkg",
        file_codes=[("containment_many_to_one_forbidden.aware", code)],
        namespace_by_code_id=ns,
    )

    with pytest.raises(
        ValueError, match="Containment rails must be one_to_one or one_to_many"
    ):
        analyze_relationships(res.graph, namespace_by_code_id=ns)


def test_association_edge_construct_many_to_one_targets_edge_not_authored_target(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "association_edge_containment_many_to_one.aware",
        ASSOCIATION_EDGE_CONTAINMENT_MANY_TO_ONE_CODE.strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="association_edge_containment_many_to_one",
        description="association_edge_containment_many_to_one",
        fqn_prefix="pkg",
        file_codes=[("association_edge_containment_many_to_one.aware", code)],
        namespace_by_code_id=ns,
    )

    analyses = analyze_relationships(res.graph, namespace_by_code_id=ns)
    by_sig = {
        (a.source_class.name, a.forward_reference_attr.name, a.target_class.name): a
        for a in analyses
    }
    rel = by_sig[("Parent", "child", "Child")]

    assert rel.relationship_type == ClassConfigRelationshipType.many_to_one
    assert rel.identity_rail == ClassConfigRelationshipIdentityRail.containment
    assert rel.association_class is not None
    assert rel.association_class.name == "ParentChildEdge"
    assert rel.construct_target_class is not None
    assert rel.construct_target_class.name == "ParentChildEdge"
    assert rel.construct_target_is_association is True
    assert rel.fk_owner_class is not None
    assert rel.fk_owner_class.name == "ParentChildEdge"
    assert rel.fk_owner_side is None


def test_standalone_construct_target_does_not_flip_many_to_one_to_containment(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "standalone_edge_construct_reference.aware",
        STANDALONE_EDGE_CONSTRUCT_REFERENCE_CODE.strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="standalone_edge_construct_reference",
        description="standalone_edge_construct_reference",
        fqn_prefix="pkg",
        file_codes=[("standalone_edge_construct_reference.aware", code)],
        namespace_by_code_id=ns,
    )

    analyses = analyze_relationships(res.graph, namespace_by_code_id=ns)
    by_sig = {
        (a.source_class.name, a.forward_reference_attr.name, a.target_class.name): a
        for a in analyses
    }
    rel = by_sig[("ParentAttributeEdge", "attribute_config", "AttributeConfig")]

    assert rel.relationship_type == ClassConfigRelationshipType.many_to_one
    assert rel.identity_rail == ClassConfigRelationshipIdentityRail.reference
    assert rel.construct_target_class is not None
    assert rel.construct_target_class.name == "AttributeConfig"
    assert rel.fk_owner_side == ClassConfigRelationshipDirection.forward
    assert rel.fk_owner_class is not None
    assert rel.fk_owner_class.name == "ParentAttributeEdge"
    assert rel.fk_target_class is not None
    assert rel.fk_target_class.name == "AttributeConfig"
    assert rel.fk_column_name == "attribute_config_id"


def test_fk_requiredness_runtime_vs_db_and_overrides(tmp_path: Path) -> None:
    """
    Validate the explicit split:
    - runtime_required keeps eager FK optional (representation ergonomics)
      for both forward-owned and reverse-owned FK sides
    - db_required follows relationship schema truth for both owner sides
    - override fk nullable/name applies to both runtimes + DB semantics
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path, "rels_override.aware", DEFAULT_CODE_WITH_OVERRIDES.strip()
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="rels_override",
        description="rels_override",
        fqn_prefix="pkg",
        file_codes=[("rels_override.aware", code)],
        namespace_by_code_id=ns,
    )

    analyses = analyze_relationships(res.graph, namespace_by_code_id=ns)
    assert analyses
    by_sig = {
        (a.source_class.name, a.forward_reference_attr.name, a.target_class.name): a
        for a in analyses
    }

    a_org = by_sig[("User", "org", "Organization")]
    assert a_org.relationship_type == ClassConfigRelationshipType.many_to_one
    assert a_org.fk_owner_side == ClassConfigRelationshipDirection.forward
    assert a_org.forward_required is False
    # Forward eager keeps runtime FK optional (serialization ergonomics),
    # and `override fk nullable` clears DB truth requiredness as well.
    assert fk_runtime_requiredness_from_relationship_semantics(a_org) is False
    assert fk_db_requiredness_from_relationship_semantics(a_org) is False

    a_opt_org = by_sig[("User", "opt_org", "Organization")]
    assert a_opt_org.relationship_type == ClassConfigRelationshipType.many_to_one
    assert fk_db_requiredness_from_relationship_semantics(a_opt_org) is False

    # ONE_TO_MANY: list on source -> FK lives on target; requiredness follows relationship truth.
    a_posts = by_sig[("User", "posts", "Post")]
    assert a_posts.relationship_type == ClassConfigRelationshipType.one_to_many
    assert a_posts.fk_owner_side == ClassConfigRelationshipDirection.reverse
    # Reverse eager keeps runtime FK optional (serialization ergonomics),
    # while DB truth remains required from relationship schema.
    assert fk_runtime_requiredness_from_relationship_semantics(a_posts) is False
    assert fk_db_requiredness_from_relationship_semantics(a_posts) is True

    fk_overrides = index_fk_override_annotations(res.graph)
    ov = resolve_fk_override(a_org, overrides_by_key=fk_overrides)
    assert ov is not None
    assert ov.nullable is True
    assert ov.name == "org_id_custom"

    # Materialization plan should reflect override: both runtime+db become nullable and name is strict.
    def _dedupe(_cls, base: str) -> str:
        return base

    plan = compute_fk_materialization_plan(
        a_org, overrides_by_key=fk_overrides, validate_unique=_dedupe
    )
    assert plan is not None
    assert plan.name_is_override is True
    assert plan.name == "org_id_custom"
    assert plan.runtime_required is False
    assert plan.db_required is False


def test_fk_requiredness_reverse_lazy_remains_required_by_truth(tmp_path: Path) -> None:
    """
    Reverse-owned FK requiredness remains truth-driven when reverse side is LAZY
    (default strategy).
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "rels_reverse_lazy.aware",
        DEFAULT_CODE.strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="rels_reverse_lazy",
        description="rels_reverse_lazy",
        fqn_prefix="pkg",
        file_codes=[("rels_reverse_lazy.aware", code)],
        namespace_by_code_id=ns,
    )

    analyses = analyze_relationships(res.graph, namespace_by_code_id=ns)
    by_sig = {
        (a.source_class.name, a.forward_reference_attr.name, a.target_class.name): a
        for a in analyses
    }

    a_posts = by_sig[("User", "posts", "Post")]
    assert a_posts.fk_owner_side == ClassConfigRelationshipDirection.reverse
    assert fk_runtime_requiredness_from_relationship_semantics(a_posts) is True
    assert fk_db_requiredness_from_relationship_semantics(a_posts) is True


def test_fk_overrides_resolve_without_code_provenance(tmp_path: Path) -> None:
    """
    Regression:
    `code_section_*` relationships are intentionally excluded from persisted artifacts and fast-cloned graphs.

    FK override annotations are keyed by (fqn_prefix, domain, schema, class, attribute, edge_name), so
    relationship analysis must be able to resolve namespaces from Domain/Schema membership metadata alone.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path, "rels_override_roundtrip.aware", DEFAULT_CODE_WITH_OVERRIDES.strip()
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="rels_override_roundtrip",
        description="rels_override_roundtrip",
        fqn_prefix="pkg",
        file_codes=[("rels_override_roundtrip.aware", code)],
        namespace_by_code_id=ns,
    )

    # Simulate persisted-artifact / fast-clone behavior: drops `exclude=True` relationships (e.g. CodeSection pointers).
    graph = res.graph.model_validate_json(
        res.graph.model_dump_json(exclude_none=True, by_alias=True)
    )

    # No `namespace_by_code_id` available in persisted artifacts.
    analyses = analyze_relationships(graph)
    by_sig = {
        (a.source_class.name, a.forward_reference_attr.name, a.target_class.name): a
        for a in analyses
    }
    a_org = by_sig[("User", "org", "Organization")]

    fk_overrides = index_fk_override_annotations(graph)

    def _dedupe(_cls, base: str) -> str:
        return base

    plan = compute_fk_materialization_plan(
        a_org, overrides_by_key=fk_overrides, validate_unique=_dedupe
    )
    assert plan is not None
    assert plan.name_is_override is True
    assert plan.name == "org_id_custom"
    assert plan.runtime_required is False
    assert plan.db_required is False


def test_analyze_relationships_dedupes_when_cross_relationship_is_also_a_node(
    tmp_path: Path,
) -> None:
    """
    Regression for cross-OCG projections:
    When cross-OCG relationships are materialized as RELATIONSHIP nodes in the *source* OCG,
    `analyze_relationships` must not double-count them via `object_config_graph_relationships`.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    src = """
class User {
    org Organization
}
class Organization { id String }
""".strip()
    code = _build_code(tmp_path, "dedupe.aware", src)
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="dedupe",
        description="dedupe",
        fqn_prefix="pkg",
        file_codes=[("dedupe.aware", code)],
        namespace_by_code_id=ns,
    )
    g = res.graph

    # Find the relationship node (User.org -> Organization)
    rel = next(
        n.class_config_relationship
        for n in g.object_config_graph_nodes
        if n.type.value == "relationship" and n.class_config_relationship is not None
    )
    assert rel is not None

    # Simulate kernel-structure link phase also attaching it as a cross-OCG relationship entry.
    g.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            object_config_graph_id=g.id,
            target_object_config_graph_id=g.id,
            class_config_relationships=[rel],
        )
    )

    analyses = analyze_relationships(g, namespace_by_code_id=ns)
    hits = [a for a in analyses if a.relationship.id == rel.id]
    assert len(hits) == 1


def test_relationship_analysis_hydrates_cross_ocg_targets_via_external_graphs_by_id(
    tmp_path: Path,
) -> None:
    """
    Regression:
    `ObjectConfigGraphRelationship.target_object_config_graph` is intentionally excluded from
    persisted environment.json artifacts. Relationship analysis must therefore be able to
    resolve cross-OCG endpoints via the provided external graphs mapping.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    history_code = _build_code(
        tmp_path,
        "history.aware",
        """
class Branch {}
""".strip(),
    )
    history_ns, history_domains = _ns(
        fqn_prefix="aware_history",
        namespace="branch",
        code_ids=[history_code.id],
    )
    history_graph = build_object_config_graph_from_code(
        name="history",
        description="history",
        fqn_prefix="aware_history",
        file_codes=[("history.aware", history_code)],
        namespace_by_code_id=history_ns,
    ).graph

    meta_code = _build_code(
        tmp_path,
        "meta.aware",
        """
class ObjectInstanceGraphBranch {
    branch aware_history.branch.Branch
}
""".strip(),
    )
    meta_ns, meta_domains = _ns(
        fqn_prefix="aware_meta",
        namespace="graph.instance",
        code_ids=[meta_code.id],
    )
    meta_build = build_object_config_graph_from_code(
        name="meta",
        description="meta",
        fqn_prefix="aware_meta",
        file_codes=[("meta.aware", meta_code)],
        namespace_by_code_id=meta_ns,
        external_graphs=[history_graph],
    )
    meta_graph = meta_build.graph
    cross_rels = meta_build.cross_relationships_by_target_ocg.get(history_graph.id)
    assert cross_rels is not None and len(cross_rels) == 1

    meta_graph.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            object_config_graph_id=meta_graph.id,
            target_object_config_graph_id=history_graph.id,
            class_config_relationships=[cross_rels[0]],
        )
    )
    meta_graph_loaded = meta_graph.model_validate_json(
        meta_graph.model_dump_json(exclude_none=True, by_alias=True)
    )

    bundle = build_object_config_graph_analysis_bundle(
        meta_graph_loaded,
        namespace_by_code_id=meta_ns,
        external_graphs_by_id={history_graph.id: history_graph},
    )
    assert cross_rels[0].id in bundle.analyses_by_relationship_id


def test_relationship_analysis_resolves_cross_ocg_construct_target_functions(
    tmp_path: Path,
) -> None:
    """
    Regression for cross-OCG construct propagation:
    when a source class constructs an external target through a cross-graph relationship,
    the analyzer must resolve the target constructor owner class from the external graph.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    content_code = _build_code(
        tmp_path,
        "content.aware",
        """
class ContentChain {
    key String key = "default"

    fn build construct(
        key String key = "default",
    ) -> ContentChain {
    }
}
""".strip(),
    )
    content_ns, content_domains = _ns(
        fqn_prefix="aware_content",
        namespace="chain",
        code_ids=[content_code.id],
    )
    content_graph = build_object_config_graph_from_code(
        name="content",
        description="content",
        fqn_prefix="aware_content",
        file_codes=[("content.aware", content_code)],
        namespace_by_code_id=content_ns,
    ).graph

    conversation_code = _build_code(
        tmp_path,
        "conversation.aware",
        """
class Conversation {
    content_chain aware_content.chain.ContentChain unique

    fn build construct() -> Conversation {
        construct content_chain.build()
    }
}
""".strip(),
    )
    conversation_ns, conversation_domains = _ns(
        fqn_prefix="aware_conversation",
        namespace="conversation",
        code_ids=[conversation_code.id],
    )
    conversation_build = build_object_config_graph_from_code(
        name="conversation",
        description="conversation",
        fqn_prefix="aware_conversation",
        file_codes=[("conversation.aware", conversation_code)],
        namespace_by_code_id=conversation_ns,
        external_graphs=[content_graph],
    )
    conversation_graph = conversation_build.graph
    cross_rels = conversation_build.cross_relationships_by_target_ocg.get(
        content_graph.id
    )
    assert cross_rels is not None and len(cross_rels) == 1

    conversation_graph.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            object_config_graph_id=conversation_graph.id,
            target_object_config_graph_id=content_graph.id,
            class_config_relationships=[cross_rels[0]],
        )
    )
    conversation_graph_loaded = conversation_graph.model_validate_json(
        conversation_graph.model_dump_json(exclude_none=True, by_alias=True)
    )
    stale_embedded_content_graph = content_graph.model_copy(deep=True)
    stale_embedded_content_graph.object_config_graph_nodes = []
    conversation_graph_loaded.object_config_graph_relationships[
        0
    ].target_object_config_graph = stale_embedded_content_graph

    analyses = analyze_relationships(
        conversation_graph_loaded,
        namespace_by_code_id=conversation_ns,
        external_graphs_by_id={content_graph.id: content_graph},
    )
    by_sig = {
        (a.source_class.name, a.forward_reference_attr.name, a.target_class.name): a
        for a in analyses
    }
    analysis = by_sig[("Conversation", "content_chain", "ContentChain")]
    assert analysis.construct_target_class is not None
    assert analysis.construct_target_class.name == "ContentChain"
