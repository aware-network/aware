from pathlib import Path
from uuid import UUID

import pytest

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta Ontology
from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)
from aware_meta_ontology.annotation.code_section_annotation_reference_enums import (
    CodeSectionAnnotationReferenceMode,
)
from aware_meta_ontology.annotation.code_section_annotation_storage_enums import (
    CodeSectionAnnotationStorageOperation,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipType,
)
from aware_meta_ontology.class_.class_config_enums import ClassIdentityMode
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
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
from aware_meta.fqn_resolver import NamespacePath

DEF_SAMPLE_CODE_LOAD_PROJECT = """class User {
    id UUID
    name String
    posts Post[]
}

class Post {
    id UUID
    title String
}

ann default.User::posts load forward eager reverse lazy

projection UserCard {
    root default.User
    default.User::posts
}

projection UserCardFqn {
    root ann_pkg.main_domain.default.User
}
"""

DEF_SAMPLE_CODE_BAD_LOAD_NO_REL = """
class User {
    id UUID
    name String
}

ann default.User::name load forward eager
"""

DEF_SAMPLE_CODE_DUP_LOAD = """
class User {
    posts Post[]
}
class Post { title String }

ann default.User::posts load forward eager
ann default.User::posts load forward lazy
"""


DEF_SAMPLE_CODE_OVERLAY = """
enum Status {
    active
    inactive
}

class User {
    posts Post[]
}

class Post {
    title String
}

ann default.User overlay entity "class" language "python" rename UserDTO wire_name user_dto
ann default.User::posts overlay entity "attribute" language "python" rename postsDTO
ann default.Status overlay entity "enum" language "python" rename StatusEnum
ann default.Status::active overlay entity "enum_option" language "python" rename active_enum
"""

DEF_SAMPLE_CODE_OVERRIDE_FK = """
class User {
    posts Post[]
}

class Post {
    title String
}

ann default.User::posts override fk nullable name user_id
"""

DEF_SAMPLE_CODE_OVERRIDE_RELATIONSHIP = """
class Node {
    links Node[] @NodeLink many
}

edge NodeLink {
    position Int?
}

ann default.Node::links::NodeLink override relationship name target_node
"""

DEF_SAMPLE_CODE_LOAD_EDGE = """
class User {
    name String
}

class Group {
    name String
}

class Membership {
    users User[] @UserGroupEdge many
}

edge UserGroupEdge {
    status String
}

ann default.Membership::users::UserGroupEdge load both eager
"""

DEF_SAMPLE_CODE_LOAD_EDGE_NO_EDGE_NAME = """
class User {
    name String
}

class Group {
    name String
}

class Membership {
    users User[] @UserGroupEdge many
}

edge UserGroupEdge {
    status String
}

// Edge name omitted: should still resolve because Membership.users is unambiguous.
ann default.Membership::users load both eager
"""

DEF_SAMPLE_CODE_REFERENCE = """
class Actor {
    authored_commits Commit[]
}

class Commit {
    author_id UUID
    other_id UUID
}

ann default.Commit::author_id reference port
ann default.Actor::authored_commits reference bind "default.Commit::author_id"
"""

DEF_SAMPLE_CODE_IDENTITY = """
class ReusableAttribute {
    owner_key String key
    name String key
}

ann default.ReusableAttribute identity standalone
"""

DEF_SAMPLE_CODE_IDENTITY_STRUCTURAL = """
class DescriptorLink {
    child Descriptor key
    role String key
    position Int key = 0
}

class Descriptor {
    child_links DescriptorLink[]
    kind String key
}

ann default.Descriptor identity standalone structural child_links
"""

DEF_SAMPLE_CODE_INDEX = """
class Organization {
    name String
}

class User {
    email String
    org Organization
}

ann default.User::email index
ann default.User index org email
"""

DEF_SAMPLE_CODE_STORAGE = """
class Organization {
    name String
}

class User {
    email String
    org Organization
}

ann default.User storage index by_email email
ann default.User storage unique by_org_email org email
"""

DEF_SAMPLE_CODE_DUP_INDEX = """
class User {
    email String
}

ann default.User::email index
ann default.User::email  index
"""

DEF_SAMPLE_CODE_BAD_INDEX_UNKNOWN_MEMBER = """
class User {
    email String
}

ann default.User::missing index
"""

DEF_SAMPLE_CODE_BAD_INDEX_COLLECTION = """
class User {
    posts Post[]
}

class Post {
    title String
}

ann default.User::posts index
"""

DEF_SAMPLE_CODE_DUP_STORAGE_NAME = """
class User {
    email String
    handle String
}

ann default.User storage index by_identity email
ann default.User storage unique by_identity handle
"""

DEF_SAMPLE_CODE_BAD_STORAGE_DUP_MEMBER = """
class User {
    email String
}

ann default.User storage unique by_email email email
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


def test_canonical_ocg_compiles_ann_annotations(tmp_path: Path) -> None:
    # Ensure code plugin is registered so `ann` is parsed into CodeSectionAnnotation sections.
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path, "ann_basic.aware", DEF_SAMPLE_CODE_LOAD_PROJECT.strip()
    )
    ns, domains = _ns(
        fqn_prefix="ann_pkg",
        namespace="main_domain",
        code_ids=[code.id],
    )

    res = build_object_config_graph_from_code(
        name="ann_graph",
        description="ann_graph",
        fqn_prefix="ann_pkg",
        file_codes=[("ann_basic.aware", code)],
        namespace_by_code_id=ns,
    )

    graph = res.graph
    annos = list(graph.object_config_graph_annotations)
    assert annos, "Expected compiled ObjectConfigGraphAnnotations on canonical graph"

    load_annos = [
        a
        for a in annos
        if a.kind == ObjectConfigGraphAnnotationKind.load
        and a.code_section_annotation_load is not None
    ]
    assert load_annos, "Expected at least one LOAD annotation"
    la = load_annos[0].code_section_annotation_load
    assert la is not None
    assert la.fqn_prefix == "ann_pkg"
    assert la.domain_name == "main_domain"
    assert la.schema_name == "default"
    assert la.class_name == "User"

    # Load strategies must be applied to the relationship SSOT during OCG build (not in transformers).
    class_by_id = {
        n.class_config.id: n.class_config
        for n in graph.object_config_graph_nodes
        if n.class_config is not None and n.class_config.id is not None
    }
    rels = [
        n.class_config_relationship
        for n in graph.object_config_graph_nodes
        if n.class_config_relationship is not None
    ]
    assert rels

    # Deterministically identify the relationship for User.posts by finding the forward REFERENCE attribute name.
    def _forward_ref_name(rel) -> str | None:
        src = (
            class_by_id.get(rel.class_config_id)
            if rel.class_config_id is not None
            else None
        )
        if src is None:
            return None
        for ra in rel.class_config_relationship_attributes:
            if ra.direction.value != "forward" or ra.role.value != "reference":
                continue
            for acc in src.class_config_attribute_configs:
                if (
                    acc.attribute_config is None
                    or acc.attribute_config.id != ra.attribute_config_id
                ):
                    continue
                return acc.attribute_config.name
        return None

    user_posts = next(
        r
        for r in rels
        if class_by_id.get(r.class_config_id).name == "User"  # type: ignore[union-attr]
        and _forward_ref_name(r) == "posts"
    )
    assert user_posts.forward_loading_strategy is not None
    assert user_posts.reverse_loading_strategy is not None
    assert user_posts.forward_loading_strategy.value.lower() == "eager"
    assert user_posts.reverse_loading_strategy.value.lower() == "lazy"

    decls_by_name = {
        (d.projection_name or "").strip(): d
        for d in graph.object_projection_graph_declarations
        if (d.projection_name or "").strip()
    }
    assert "UserCard" in decls_by_name
    assert "UserCardFqn" in decls_by_name

    user_card = decls_by_name["UserCard"]
    root_user = next(
        b
        for b in user_card.object_projection_graph_bindings
        if b.attribute_name is None and not (b.target_projection_name or "").strip()
    )
    assert root_user.class_name == "User"

    edge_posts = next(
        b
        for b in user_card.object_projection_graph_bindings
        if b.attribute_name == "posts" and not (b.target_projection_name or "").strip()
    )
    assert edge_posts.attribute_name == "posts"


def test_legacy_ann_project_is_rejected(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "ann_project.aware",
        """
class User { id UUID }

ann default.User project name "user_card"
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg",
        namespace="default",
        code_ids=[code.id],
    )

    with pytest.raises(ValueError, match=r"Legacy .*project.* is not supported"):
        build_object_config_graph_from_code(
            name="ann_project",
            description="ann_project",
            fqn_prefix="pkg",
            file_codes=[("ann_project.aware", code)],
            namespace_by_code_id=ns,
        )


def test_canonical_ocg_compiles_reference_annotations(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path, "ann_reference.aware", DEF_SAMPLE_CODE_REFERENCE.strip()
    )
    ns, domains = _ns(
        fqn_prefix="pkg",
        namespace="default",
        code_ids=[code.id],
    )

    res = build_object_config_graph_from_code(
        name="ann_reference",
        description="ann_reference",
        fqn_prefix="pkg",
        file_codes=[("ann_reference.aware", code)],
        namespace_by_code_id=ns,
    )
    graph = res.graph
    annos = list(graph.object_config_graph_annotations)

    refs = [
        a.code_section_annotation_reference
        for a in annos
        if a.kind == ObjectConfigGraphAnnotationKind.reference
        and a.code_section_annotation_reference is not None
    ]
    assert refs

    port = next(r for r in refs if r.mode == CodeSectionAnnotationReferenceMode.port)
    assert port.class_name == "Commit"
    assert port.attribute_name == "author_id"

    bind = next(r for r in refs if r.mode == CodeSectionAnnotationReferenceMode.bind)
    assert bind.class_name == "Actor"
    assert bind.attribute_name == "authored_commits"
    assert bind.target_class_name == "Commit"
    assert bind.target_attribute_name == "author_id"


def test_canonical_ocg_compiles_identity_annotations(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "ann_identity.aware", DEF_SAMPLE_CODE_IDENTITY.strip())
    ns, domains = _ns(
        fqn_prefix="pkg",
        namespace="default",
        code_ids=[code.id],
    )

    res = build_object_config_graph_from_code(
        name="ann_identity",
        description="ann_identity",
        fqn_prefix="pkg",
        file_codes=[("ann_identity.aware", code)],
        namespace_by_code_id=ns,
    )
    graph = res.graph
    annos = list(graph.object_config_graph_annotations)

    identities = [
        a.code_section_annotation_identity
        for a in annos
        if a.kind == ObjectConfigGraphAnnotationKind.identity
        and a.code_section_annotation_identity is not None
    ]
    assert len(identities) == 1
    identity = identities[0]
    assert identity.class_name == "ReusableAttribute"
    assert identity.mode == ClassIdentityMode.standalone

    reusable = next(
        node.class_config
        for node in graph.object_config_graph_nodes
        if node.class_config is not None
        and node.class_config.name == "ReusableAttribute"
    )
    assert reusable.identity_mode == ClassIdentityMode.standalone


def test_canonical_ocg_compiles_structural_identity_annotations(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "ann_identity_structural.aware",
        DEF_SAMPLE_CODE_IDENTITY_STRUCTURAL.strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg",
        namespace="default",
        code_ids=[code.id],
    )

    res = build_object_config_graph_from_code(
        name="ann_identity_structural",
        description="ann_identity_structural",
        fqn_prefix="pkg",
        file_codes=[("ann_identity_structural.aware", code)],
        namespace_by_code_id=ns,
    )
    graph = res.graph
    annos = list(graph.object_config_graph_annotations)

    identities = [
        a.code_section_annotation_identity
        for a in annos
        if a.kind == ObjectConfigGraphAnnotationKind.identity
        and a.code_section_annotation_identity is not None
    ]
    assert len(identities) == 1
    identity = identities[0]
    assert identity.class_name == "Descriptor"
    assert identity.mode == ClassIdentityMode.standalone
    assert identity.structural_relation_name == "child_links"


def test_overlay_class_attribute_enum_option_compiles(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "overlay.aware",
        DEF_SAMPLE_CODE_OVERLAY.strip(),
    )

    ns, domains = _ns(
        fqn_prefix="ann_pkg", namespace="main_domain", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="overlay_graph",
        description="overlay_graph",
        fqn_prefix="ann_pkg",
        file_codes=[("overlay.aware", code)],
        namespace_by_code_id=ns,
    )

    graph = res.graph
    overlays = [
        a.code_section_annotation_overlay
        for a in graph.object_config_graph_annotations
        if a.kind == ObjectConfigGraphAnnotationKind.overlay
        and a.code_section_annotation_overlay is not None
    ]
    assert overlays

    # CLASS overlay
    class_over = next(
        o
        for o in overlays
        if o.entity == CodeSectionAnnotationOverlayEntity.class_
        and o.class_name == "User"
    )
    assert class_over.fqn_prefix == "ann_pkg"
    assert class_over.domain_name == "main_domain"
    assert class_over.schema_name == "default"
    assert class_over.rename == "UserDTO"
    assert class_over.wire_name == "user_dto"

    # ATTRIBUTE overlay
    attr_over = next(
        o
        for o in overlays
        if o.entity == CodeSectionAnnotationOverlayEntity.attribute
        and o.class_name == "User"
        and o.attribute_name == "posts"
    )
    assert attr_over.rename == "postsDTO"

    # ENUM overlay
    enum_over = next(
        o
        for o in overlays
        if o.entity == CodeSectionAnnotationOverlayEntity.enum
        and o.enum_name == "Status"
    )
    assert enum_over.rename == "StatusEnum"

    # ENUM_OPTION overlay
    opt_over = next(
        o
        for o in overlays
        if o.entity == CodeSectionAnnotationOverlayEntity.enum_option
        and o.enum_name == "Status"
        and o.enum_option_name == "active"
    )
    assert opt_over.rename == "active_enum"


def test_overlay_edge_endpoint_path_compiles(tmp_path: Path) -> None:
    """
    Overlay path extension:
    - Source::relationship_attr::EdgeName::edge_member
    - Source::relationship_attr::EdgeName::edge_fn::edge_fn_attr
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "overlay_edge.aware",
        """
class A {
    bs B[] @AB
}

class B {}

edge AB {
    fn build construct(a_id UUID, b B) -> AB {}
}

ann default.A::bs::AB::b overlay entity "attribute" language "python" rename b_ wire_name b
ann default.A::bs::AB::build::b overlay entity "attribute" language "python" rename b_ wire_name b
        """.strip(),
    )

    ns, domains = _ns(
        fqn_prefix="ann_pkg", namespace="main_domain", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="overlay_edge_graph",
        description="overlay_edge_graph",
        fqn_prefix="ann_pkg",
        file_codes=[("overlay_edge.aware", code)],
        namespace_by_code_id=ns,
    )

    overlays = [
        a.code_section_annotation_overlay
        for a in res.graph.object_config_graph_annotations
        if a.kind == ObjectConfigGraphAnnotationKind.overlay
        and a.code_section_annotation_overlay is not None
    ]
    assert overlays
    assert any(
        o.class_name == "AB" and o.attribute_name == "b" and o.function_name is None
        for o in overlays
    )
    assert any(
        o.class_name == "AB" and o.attribute_name == "b" and o.function_name == "build"
        for o in overlays
    )


def test_load_with_edge_association_compiles_edge_name(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "edge_load.aware",
        DEF_SAMPLE_CODE_LOAD_EDGE.strip(),
    )

    ns, domains = _ns(
        fqn_prefix="ann_pkg", namespace="main_domain", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="edge_load_graph",
        description="edge_load_graph",
        fqn_prefix="ann_pkg",
        file_codes=[("edge_load.aware", code)],
        namespace_by_code_id=ns,
    )

    loads = [
        a.code_section_annotation_load
        for a in res.graph.object_config_graph_annotations
        if a.kind == ObjectConfigGraphAnnotationKind.load
        and a.code_section_annotation_load is not None
    ]
    assert loads
    entry = next(
        l for l in loads if l.class_name == "Membership" and l.attribute_name == "users"
    )
    assert entry.edge_name == "UserGroupEdge"

    # Edge load (with ::EdgeName) applies to the association->target semantics, not the relationship container.
    rels = [
        n.class_config_relationship
        for n in res.graph.object_config_graph_nodes
        if n.class_config_relationship is not None
    ]
    assert rels
    rel = next(
        r
        for r in rels
        if r.relationship_type == ClassConfigRelationshipType.many_to_many
    )
    # Relationship container strategy remains at its canonical default (typically LAZY) because
    # the edge-qualified load targets association->target semantics.
    assert rel.forward_loading_strategy is not None
    assert rel.class_config_relationship_association_edge is not None
    assert (
        rel.class_config_relationship_association_edge.reverse_loading_strategy
        is not None
    )
    assert (
        rel.class_config_relationship_association_edge.reverse_loading_strategy.value.lower()
        == "eager"
    )


def test_load_with_edge_association_resolves_without_edge_name_when_unambiguous(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "edge_load_no_edge_name.aware",
        DEF_SAMPLE_CODE_LOAD_EDGE_NO_EDGE_NAME.strip(),
    )

    ns, domains = _ns(
        fqn_prefix="ann_pkg", namespace="main_domain", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="edge_load_no_edge_name_graph",
        description="edge_load_no_edge_name_graph",
        fqn_prefix="ann_pkg",
        file_codes=[("edge_load_no_edge_name.aware", code)],
        namespace_by_code_id=ns,
    )

    # The LOAD annotation should compile (edge_name=None).
    loads = [
        a.code_section_annotation_load
        for a in res.graph.object_config_graph_annotations
        if a.kind == ObjectConfigGraphAnnotationKind.load
        and a.code_section_annotation_load is not None
    ]
    assert loads
    entry = next(
        l for l in loads if l.class_name == "Membership" and l.attribute_name == "users"
    )
    assert entry.edge_name is None
    assert entry.forward_strategy is not None
    assert entry.reverse_strategy is not None

    # And it must be applied to the relationship even though the relationship uses an edge.
    rels = [
        n.class_config_relationship
        for n in res.graph.object_config_graph_nodes
        if n.class_config_relationship is not None
    ]
    assert rels
    rel = next(
        r
        for r in rels
        if r.relationship_type == ClassConfigRelationshipType.many_to_many
    )
    assert rel.forward_loading_strategy is not None
    assert rel.reverse_loading_strategy is not None


def test_override_fk_compiles_nullable_and_name(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "override_fk.aware",
        DEF_SAMPLE_CODE_OVERRIDE_FK.strip(),
    )
    ns, domains = _ns(
        fqn_prefix="ann_pkg",
        namespace="main_domain",
        code_ids=[code.id],
    )

    res = build_object_config_graph_from_code(
        name="override_fk_graph",
        description="override_fk_graph",
        fqn_prefix="ann_pkg",
        file_codes=[("override_fk.aware", code)],
        namespace_by_code_id=ns,
    )

    annos = list(res.graph.object_config_graph_annotations)
    overrides = [
        a.code_section_annotation_override
        for a in annos
        if a.kind == ObjectConfigGraphAnnotationKind.override
        and a.code_section_annotation_override is not None
    ]
    assert overrides
    ov = overrides[0]
    assert ov is not None
    assert ov.fqn_prefix == "ann_pkg"
    assert ov.domain_name == "main_domain"
    assert ov.schema_name == "default"
    assert ov.class_name == "User"
    assert ov.attribute_name == "posts"
    assert ov.edge_name is None
    assert ov.nullable is True
    assert ov.name == "user_id"


def test_override_relationship_compiles_name(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "override_rel.aware",
        DEF_SAMPLE_CODE_OVERRIDE_RELATIONSHIP.strip(),
    )
    ns, domains = _ns(
        fqn_prefix="ann_pkg",
        namespace="main_domain",
        code_ids=[code.id],
    )

    res = build_object_config_graph_from_code(
        name="override_rel_graph",
        description="override_rel_graph",
        fqn_prefix="ann_pkg",
        file_codes=[("override_rel.aware", code)],
        namespace_by_code_id=ns,
    )

    annos = list(res.graph.object_config_graph_annotations)
    overrides = [
        a.code_section_annotation_override
        for a in annos
        if a.kind == ObjectConfigGraphAnnotationKind.override
        and a.code_section_annotation_override is not None
    ]
    assert overrides
    ov = overrides[0]
    assert ov is not None
    assert ov.target.value == "relationship"
    assert ov.class_name == "Node"
    assert ov.attribute_name == "links"
    assert ov.edge_name == "NodeLink"
    assert ov.name == "target_node"


def test_load_annotation_missing_relationship_raises(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path, "bad_load.aware", DEF_SAMPLE_CODE_BAD_LOAD_NO_REL.strip()
    )
    ns, domains = _ns(
        fqn_prefix="ann_pkg", namespace="main_domain", code_ids=[code.id]
    )
    with pytest.raises(ValueError):
        build_object_config_graph_from_code(
            name="bad_load_graph",
            description="bad_load_graph",
            fqn_prefix="ann_pkg",
            file_codes=[("bad_load.aware", code)],
            namespace_by_code_id=ns,
        )


def test_duplicate_load_annotation_raises(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(tmp_path, "dup_load.aware", DEF_SAMPLE_CODE_DUP_LOAD.strip())
    ns, domains = _ns(
        fqn_prefix="ann_pkg", namespace="main_domain", code_ids=[code.id]
    )
    with pytest.raises(ValueError):
        build_object_config_graph_from_code(
            name="dup_load_graph",
            description="dup_load_graph",
            fqn_prefix="ann_pkg",
            file_codes=[("dup_load.aware", code)],
            namespace_by_code_id=ns,
        )


def test_canonical_ocg_compiles_ann_index_annotations(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(tmp_path, "index.aware", DEF_SAMPLE_CODE_INDEX.strip())
    ns, domains = _ns(
        fqn_prefix="ann_pkg", namespace="main_domain", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="index_graph",
        description="index_graph",
        fqn_prefix="ann_pkg",
        file_codes=[("index.aware", code)],
        namespace_by_code_id=ns,
    )

    annos = list(res.graph.object_config_graph_annotations)
    index_annos = [
        a
        for a in annos
        if a.kind == ObjectConfigGraphAnnotationKind.index
        and a.code_section_annotation_index is not None
    ]
    assert index_annos

    by_class = {
        (
            a.code_section_annotation_index.class_name,
            tuple(a.code_section_annotation_index.member_names),
        ): a
        for a in index_annos
    }
    assert ("User", ("email",)) in by_class
    assert ("User", ("org", "email")) in by_class


def test_canonical_ocg_compiles_storage_annotations(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(tmp_path, "storage.aware", DEF_SAMPLE_CODE_STORAGE.strip())
    ns, domains = _ns(
        fqn_prefix="ann_pkg", namespace="main_domain", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="storage_graph",
        description="storage_graph",
        fqn_prefix="ann_pkg",
        file_codes=[("storage.aware", code)],
        namespace_by_code_id=ns,
    )

    storage_annos = [
        a.code_section_annotation_storage
        for a in res.graph.object_config_graph_annotations
        if a.kind == ObjectConfigGraphAnnotationKind.storage
        and a.code_section_annotation_storage is not None
    ]
    assert len(storage_annos) == 2

    by_name = {a.name: a for a in storage_annos}
    by_email = by_name["by_email"]
    assert by_email.class_name == "User"
    assert by_email.operation == CodeSectionAnnotationStorageOperation.index
    assert by_email.member_names == ["email"]

    by_org_email = by_name["by_org_email"]
    assert by_org_email.class_name == "User"
    assert by_org_email.operation == CodeSectionAnnotationStorageOperation.unique
    assert by_org_email.member_names == ["org", "email"]


def test_duplicate_index_annotation_raises(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(tmp_path, "dup_index.aware", DEF_SAMPLE_CODE_DUP_INDEX.strip())
    ns, domains = _ns(
        fqn_prefix="ann_pkg", namespace="main_domain", code_ids=[code.id]
    )
    with pytest.raises(ValueError, match="Duplicate INDEX annotation"):
        build_object_config_graph_from_code(
            name="dup_index_graph",
            description="dup_index_graph",
            fqn_prefix="ann_pkg",
            file_codes=[("dup_index.aware", code)],
            namespace_by_code_id=ns,
        )


def test_index_annotation_unknown_member_raises(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path, "bad_index.aware", DEF_SAMPLE_CODE_BAD_INDEX_UNKNOWN_MEMBER.strip()
    )
    ns, domains = _ns(
        fqn_prefix="ann_pkg", namespace="main_domain", code_ids=[code.id]
    )
    with pytest.raises(ValueError, match="INDEX annotation references unknown member"):
        build_object_config_graph_from_code(
            name="bad_index_graph",
            description="bad_index_graph",
            fqn_prefix="ann_pkg",
            file_codes=[("bad_index.aware", code)],
            namespace_by_code_id=ns,
        )


def test_duplicate_storage_annotation_name_raises(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path, "dup_storage_name.aware", DEF_SAMPLE_CODE_DUP_STORAGE_NAME.strip()
    )
    ns, domains = _ns(
        fqn_prefix="ann_pkg", namespace="main_domain", code_ids=[code.id]
    )
    with pytest.raises(ValueError, match="Duplicate STORAGE annotation name"):
        build_object_config_graph_from_code(
            name="dup_storage_name_graph",
            description="dup_storage_name_graph",
            fqn_prefix="ann_pkg",
            file_codes=[("dup_storage_name.aware", code)],
            namespace_by_code_id=ns,
        )


def test_storage_annotation_duplicate_member_raises(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "bad_storage_dup_member.aware",
        DEF_SAMPLE_CODE_BAD_STORAGE_DUP_MEMBER.strip(),
    )
    ns, domains = _ns(
        fqn_prefix="ann_pkg", namespace="main_domain", code_ids=[code.id]
    )
    with pytest.raises(ValueError, match="duplicate member name"):
        build_object_config_graph_from_code(
            name="bad_storage_dup_member_graph",
            description="bad_storage_dup_member_graph",
            fqn_prefix="ann_pkg",
            file_codes=[("bad_storage_dup_member.aware", code)],
            namespace_by_code_id=ns,
        )


def test_index_annotation_collection_member_raises(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(
        tmp_path,
        "bad_index_collection.aware",
        DEF_SAMPLE_CODE_BAD_INDEX_COLLECTION.strip(),
    )
    ns, domains = _ns(
        fqn_prefix="ann_pkg", namespace="main_domain", code_ids=[code.id]
    )
    with pytest.raises(ValueError, match="does not support collection"):
        build_object_config_graph_from_code(
            name="bad_index_collection_graph",
            description="bad_index_collection_graph",
            fqn_prefix="ann_pkg",
            file_codes=[("bad_index_collection.aware", code)],
            namespace_by_code_id=ns,
        )


def test_project_can_target_external_package_via_fqn(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    dep = _build_code(
        tmp_path,
        "dep.aware",
        """
class Base {
    id String
}
""".strip(),
    )
    dep_ns, dep_domains = _ns(
        fqn_prefix="dep_pkg",
        namespace="dep_schema",
        code_ids=[dep.id],
    )
    dep_res = build_object_config_graph_from_code(
        name="dep_graph",
        description="dep_graph",
        fqn_prefix="dep_pkg",
        file_codes=[("dep.aware", dep)],
        namespace_by_code_id=dep_ns,
    )

    local = _build_code(
        tmp_path,
        "local.aware",
        """
class User {
    id String
}

projection Dep {
    root dep_pkg.dep_domain.dep_schema.Base
}
""".strip(),
    )
    local_ns, local_domains = _ns(
        fqn_prefix="main_pkg",
        namespace="main_domain",
        code_ids=[local.id],
    )
    local_res = build_object_config_graph_from_code(
        name="local_graph",
        description="local_graph",
        fqn_prefix="main_pkg",
        file_codes=[("local.aware", local)],
        namespace_by_code_id=local_ns,
        external_graphs=[dep_res.graph],
    )

    dep_decl = next(
        d
        for d in local_res.graph.object_projection_graph_declarations
        if d.projection_name == "Dep"
    )
    dep_root = next(
        b
        for b in dep_decl.object_projection_graph_bindings
        if b.attribute_name is None and not (b.target_projection_name or "").strip()
    )
    assert dep_root.fqn_prefix == "dep_pkg"
    assert dep_root.domain_name == "dep_domain"
    assert dep_root.schema_name == "dep_schema"
    assert dep_root.class_name == "Base"


def test_schema_name_ambiguity_raises(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    # Two code files define the same class name under the same schema but different domains.
    # Annotation uses schema.Name (2-part identifier), which is ambiguous and must error.
    c1 = _build_code(
        tmp_path,
        "a.aware",
        "class User { id String }\nprojection P { root default.User }\n",
    )
    c2 = _build_code(tmp_path, "b.aware", "class User { id String }\n")

    ns_a, domains_a = _ns(
        fqn_prefix="pkg", namespace="dom_a", code_ids=[c1.id]
    )
    ns_b, domains_b = _ns(
        fqn_prefix="pkg", namespace="dom_b", code_ids=[c2.id]
    )
    ns = {**ns_a, **ns_b}
    domains = [*domains_a, *domains_b]

    with pytest.raises(ValueError):
        build_object_config_graph_from_code(
            name="amb",
            description="amb",
            fqn_prefix="pkg",
            file_codes=[("a.aware", c1), ("b.aware", c2)],
            namespace_by_code_id=ns,
        )
