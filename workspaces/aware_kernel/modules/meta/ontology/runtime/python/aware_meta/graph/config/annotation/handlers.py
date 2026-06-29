from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_annotation import (
    ObjectConfigGraphAnnotation,
)
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipSideLoadingStrategy,
)
from aware_meta_ontology.annotation.code_section_annotation_load import (
    CodeSectionAnnotationLoad,
)
from aware_meta_ontology.annotation.code_section_annotation_override import (
    CodeSectionAnnotationOverride,
)
from aware_meta_ontology.annotation.code_section_annotation_override_enums import (
    CodeSectionAnnotationOverrideTarget,
)
from aware_meta_ontology.annotation.code_section_annotation_discriminate import (
    CodeSectionAnnotationDiscriminate,
)
from aware_meta_ontology.annotation.code_section_annotation_index import (
    CodeSectionAnnotationIndex,
)
from aware_meta_ontology.annotation.code_section_annotation_storage import (
    CodeSectionAnnotationStorage,
)

# Meta Runtime
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.namespace.builder import (
    build_namespace_bundle_from_ocg_topology,
)
from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config_enums import ClassValueMode


def _namespace_required(value: object, *, context: str) -> str:
    namespace = getattr(value, "namespace", None)
    if not isinstance(namespace, str):
        raise ValueError(f"{context} requires namespace")
    return namespace.strip()


def _class_key_from_namespace(
    namespace: NamespacePath,
    class_name: str,
) -> tuple[str, str, str]:
    return (namespace.package, namespace.namespace, class_name)


def _class_key_from_view(value: object, *, context: str) -> tuple[str, str, str]:
    return (
        str(getattr(value, "fqn_prefix", "") or "").strip(),
        _namespace_required(value, context=context),
        str(getattr(value, "class_name", "") or "").strip(),
    )


def _class_fqn_from_key(key: tuple[str, str, str]) -> str:
    fqn_prefix, namespace, class_name = key
    if namespace:
        return f"{fqn_prefix}.{namespace}.{class_name}"
    return f"{fqn_prefix}.{class_name}"


def apply_fk_override_annotations_to_relationships(
    compiled_annotations: list[ObjectConfigGraphAnnotation],
    class_relationships: list[ClassConfigRelationship],
    cross_relationships_by_target_ocg: dict[UUID, list[ClassConfigRelationship]],
    class_configs: list[ClassConfig],
    namespace_by_class_config_id: dict[UUID, NamespacePath],
) -> None:
    """Apply compiled FK override annotations to canonical relationship requiredness.

    Canonical scope:
    - Non-association relationships only.
    - `ann ... override fk nullable` is an explicit opt-out from required FK truth.
    - Name-only FK overrides do not affect relationship requiredness.
    """
    override_views: list[CodeSectionAnnotationOverride] = [
        a.code_section_annotation_override
        for a in compiled_annotations
        if a.kind == ObjectConfigGraphAnnotationKind.override
        and a.code_section_annotation_override is not None
        and a.code_section_annotation_override.target == CodeSectionAnnotationOverrideTarget.fk
    ]
    if not override_views:
        return

    class_by_id: dict[UUID, ClassConfig] = {c.id: c for c in class_configs}

    attr_name_by_id: dict[UUID, tuple[UUID, str]] = {}
    for c in class_configs:
        for link in c.class_config_attribute_configs:
            if link.attribute_config is None:
                continue
            attr_name_by_id[link.attribute_config.id] = (
                c.id,
                link.attribute_config.name,
            )

    rel_by_key: dict[tuple[str, str, str, str, str | None], ClassConfigRelationship] = {}
    all_relationships: list[ClassConfigRelationship] = []
    seen_rel_ids: set[UUID] = set()
    for rel in class_relationships:
        if rel.id in seen_rel_ids:
            continue
        seen_rel_ids.add(rel.id)
        all_relationships.append(rel)
    for rels in cross_relationships_by_target_ocg.values():
        for rel in rels:
            if rel.id in seen_rel_ids:
                continue
            seen_rel_ids.add(rel.id)
            all_relationships.append(rel)

    for rel in all_relationships:
        src = class_by_id.get(rel.class_config_id)
        if src is None:
            raise ValueError(f"Cannot resolve source ClassConfig for relationship {rel.id}")

        ns = namespace_by_class_config_id.get(src.id)
        if ns is None:
            raise ValueError(
                f"Missing namespace for relationship source class {src.name} (class_id={src.id}). "
                "Expected namespace_by_class_config_id to be complete."
            )

        ref_attr_id: UUID | None = None
        for ra in rel.class_config_relationship_attributes:
            if (
                ra.direction == ClassConfigRelationshipDirection.forward
                and ra.role == ClassConfigRelationshipAttributeRole.reference
            ):
                ref_attr_id = ra.attribute_config_id
                break
        if ref_attr_id is None:
            raise ValueError(f"Relationship {rel.id} missing FORWARD+REFERENCE attribute binding")

        owner_and_name = attr_name_by_id.get(ref_attr_id)
        if owner_and_name is None:
            raise ValueError(
                f"Relationship {rel.id} reference attribute_config_id={ref_attr_id} not found on any class"
            )
        owner_class_id, attr_name = owner_and_name
        if owner_class_id != src.id:
            raise ValueError(
                f"Relationship {rel.id} reference attribute_config_id={ref_attr_id} is not owned by source class {src.name}"
            )

        assoc_name: str | None = None
        if rel.class_config_relationship_association_edge is not None:
            assoc_id = rel.class_config_relationship_association_edge.class_config_id
            if assoc_id is None:
                raise ValueError(f"Relationship {rel.id} has association with missing class_config_id")
            assoc_cls = class_by_id.get(assoc_id)
            if assoc_cls is None:
                raise ValueError(
                    f"Relationship {rel.id} association class_config_id={assoc_id} not found in graph class set"
                )
            assoc_name = assoc_cls.name

        key = (ns.package, ns.namespace, src.name, attr_name, assoc_name)
        prev = rel_by_key.get(key)
        if prev is not None and prev.id != rel.id:
            raise ValueError(
                f"Ambiguous relationship key {key}: relationship_id={rel.id} conflicts with relationship_id={prev.id}"
            )
        rel_by_key[key] = rel

    seen_keys: set[tuple[str, str, str, str, str | None]] = set()
    for v in override_views:
        key = (
            v.fqn_prefix,
            _namespace_required(v, context="FK override annotation"),
            v.class_name,
            v.attribute_name,
            v.edge_name,
        )
        rel = rel_by_key.get(key)
        if rel is None:
            raise ValueError(
                "FK override annotation did not resolve to a relationship: "
                + f"{_class_fqn_from_key(key[:3])}::{v.attribute_name}"
                + (f"::{v.edge_name}" if v.edge_name else "")
            )
        if key in seen_keys:
            raise ValueError(f"Duplicate FK override application for relationship key {key}")
        seen_keys.add(key)

        if bool(v.nullable) and rel.class_config_relationship_association_edge is None:
            rel.forward_required = False


def validate_discriminate_annotations(
    *,
    compiled_annotations: list[ObjectConfigGraphAnnotation],
    class_configs: list[ClassConfig],
    namespace_by_class_config_id: dict[UUID, NamespacePath],
    external_graphs: list[ObjectConfigGraph] | None = None,
) -> None:
    """
    Validate compiled DISCRIMINATE annotations against canonical class configs.

    Invariants:
    - Discriminate annotations must target an existing class (by resolved namespace+name).
    - Target attribute must exist on the class or be inherited from parent_class chain.
    - A base class may declare at most one `key` discriminator (one attribute).
    - A `tag` annotation must be on a subclass of a base with a `key` discriminator.
    - Tag values must be unique within the same base.
    - Discriminator keys/tags must not traverse external graph boundaries.
    """
    views: list[CodeSectionAnnotationDiscriminate] = [
        a.code_section_annotation_discriminate
        for a in compiled_annotations
        if a.kind == ObjectConfigGraphAnnotationKind.discriminate and a.code_section_annotation_discriminate is not None
    ]
    if not views:
        return

    class_by_id: dict[UUID, ClassConfig] = {c.id: c for c in class_configs}
    external_class_by_id: dict[UUID, ClassConfig] = {}
    external_namespace_by_class_config_id: dict[UUID, NamespacePath] = {}

    if external_graphs is not None:
        for external_graph in external_graphs:
            ns_bundle = build_namespace_bundle_from_ocg_topology(ocg=external_graph)
            external_namespace_by_class_config_id.update(ns_bundle.namespace_by_class_config_id)
            for node in external_graph.object_config_graph_nodes:
                if node.type != ObjectConfigGraphNodeType.class_:
                    continue
                if node.class_config is None:
                    raise ValueError("External class has no class_config")
                external_class_by_id[node.class_config.id] = node.class_config

    # Index classes by canonical resolution key.
    class_by_key: dict[tuple[str, str, str], ClassConfig] = {}
    for c in class_configs:
        ns = namespace_by_class_config_id.get(c.id)
        if ns is None:
            continue
        key = _class_key_from_namespace(ns, c.name)
        prev = class_by_key.get(key)
        if prev is not None and prev.id != c.id:
            raise ValueError(f"Ambiguous class key {key}: {c.id} conflicts with {prev.id}")
        class_by_key[key] = c

    def _format_class_fqn(cls: ClassConfig, ns_map: dict[UUID, NamespacePath]) -> str:
        ns = ns_map.get(cls.id)
        if ns is None:
            return cls.name
        return ns.fqn(cls.name)

    def _raise_external_base_error(*, child_cls: ClassConfig, base_cls: ClassConfig, attr_name: str) -> None:
        child_fqn = _format_class_fqn(child_cls, namespace_by_class_config_id)
        base_fqn = _format_class_fqn(base_cls, external_namespace_by_class_config_id)
        raise ValueError(
            "DISCRIMINATE annotation on "
            f"{child_fqn}::{attr_name} references external base class {base_fqn}. "
            "Discriminator keys/tags must live in the bus owner graph to keep unions closed; "
            "move the base and variants into the same graph as the discriminator."
        )

    def _has_attribute(cls: ClassConfig, attr_name: str) -> bool:
        cur: ClassConfig | None = cls
        seen: set[UUID] = set()
        while cur is not None and cur.id not in seen:
            seen.add(cur.id)
            for link in cur.class_config_attribute_configs:
                if link.attribute_config is None:
                    continue
                if link.attribute_config.name == attr_name:
                    return True
            parent_id = cur.parent_class_id
            if parent_id is None:
                break
            cur = class_by_id.get(parent_id)
            if cur is None and parent_id in external_class_by_id:
                _raise_external_base_error(
                    child_cls=cls,
                    base_cls=external_class_by_id[parent_id],
                    attr_name=attr_name,
                )
        return False

    # Base discriminator key per base class id.
    base_key_attr_by_base_id: dict[UUID, str] = {}

    # First pass: validate all keys and record base declarations.
    for v in views:
        key = _class_key_from_view(v, context="DISCRIMINATE annotation")
        cls = class_by_key.get(key)
        if cls is None:
            raise ValueError(f"DISCRIMINATE annotation targets unknown class {key}")
        if not _has_attribute(cls, v.attribute_name):
            raise ValueError(
                f"DISCRIMINATE annotation targets missing attribute "
                f"{_class_fqn_from_key(key)}::{v.attribute_name}"
            )
        mode = (v.mode or "").strip().lower()
        if mode == "key":
            prev_attr = base_key_attr_by_base_id.get(cls.id)
            if prev_attr is not None and prev_attr != v.attribute_name:
                raise ValueError(
                    f"DISCRIMINATE key already declared on {key}::{prev_attr}; cannot also declare {v.attribute_name}"
                )
            base_key_attr_by_base_id[cls.id] = v.attribute_name

    # Second pass: validate tags + uniqueness per base.
    tags_by_base: dict[UUID, dict[str, UUID]] = {}

    def _find_base_with_key(cls: ClassConfig, *, attr_name: str | None = None) -> tuple[UUID, str] | None:
        cur: ClassConfig | None = cls
        seen: set[UUID] = set()
        while cur is not None and cur.id not in seen:
            seen.add(cur.id)
            attr = base_key_attr_by_base_id.get(cur.id)
            if attr is not None:
                return cur.id, attr
            parent_id = cur.parent_class_id
            if parent_id is None:
                break
            cur = class_by_id.get(parent_id)
            if cur is None and parent_id in external_class_by_id:
                _raise_external_base_error(
                    child_cls=cls,
                    base_cls=external_class_by_id[parent_id],
                    attr_name=attr_name or "<unknown>",
                )
        return None

    for v in views:
        mode = (v.mode or "").strip().lower()
        if mode != "tag":
            continue
        key = _class_key_from_view(v, context="DISCRIMINATE tag annotation")
        cls = class_by_key.get(key)
        if cls is None:
            raise ValueError(f"DISCRIMINATE tag targets unknown class {key}")
        tag_value = (v.tag_value or "").strip()
        if not tag_value:
            raise ValueError(f"DISCRIMINATE tag missing tag_value for {key}::{v.attribute_name}")

        base = _find_base_with_key(cls, attr_name=v.attribute_name)
        if base is None:
            raise ValueError(
                f"DISCRIMINATE tag on {key}::{v.attribute_name} has no base class with a DISCRIMINATE key. Parent class ID: {cls.parent_class_id}"
            )
        base_id, base_attr = base
        if v.attribute_name != base_attr:
            raise ValueError(
                f"DISCRIMINATE tag on {key}::{v.attribute_name} does not match base discriminator attribute {base_attr}"
            )

        by_tag = tags_by_base.setdefault(base_id, {})
        prev_cls_id = by_tag.get(tag_value)
        if prev_cls_id is not None and prev_cls_id != cls.id:
            raise ValueError(
                f"Duplicate DISCRIMINATE tag {tag_value!r} for base_class_id={base_id} "
                f"(class_id={cls.id} conflicts with class_id={prev_cls_id})"
            )
        by_tag[tag_value] = cls.id


def validate_index_annotations(
    *,
    compiled_annotations: list[ObjectConfigGraphAnnotation],
    class_configs: list[ClassConfig],
    namespace_by_class_config_id: dict[UUID, NamespacePath],
) -> None:
    """
    Validate compiled INDEX annotations against canonical class configs.

    v0 constraints:
    - `member_names` must be non-empty and unique (order matters).
    - Each member must resolve to an attribute on the target class.
    - Only scalar members are supported:
      - primitives/enums (single value)
      - relationship pointers (Class kind, non-collection, graph_ref)
    """
    index_views: list[CodeSectionAnnotationIndex] = [
        a.code_section_annotation_index
        for a in compiled_annotations
        if a.kind == ObjectConfigGraphAnnotationKind.index and a.code_section_annotation_index is not None
    ]
    storage_annotation_kind = getattr(ObjectConfigGraphAnnotationKind, "storage", None)
    storage_views: list[CodeSectionAnnotationStorage] = (
        [
            getattr(a, "code_section_annotation_storage", None)
            for a in compiled_annotations
            if a.kind == storage_annotation_kind and getattr(a, "code_section_annotation_storage", None) is not None
        ]
        if storage_annotation_kind is not None
        else []
    )
    if not index_views and not storage_views:
        return

    # Index classes by canonical resolution key.
    class_by_key: dict[tuple[str, str, str], ClassConfig] = {}
    for c in class_configs:
        ns = namespace_by_class_config_id.get(c.id)
        if ns is None:
            continue
        key = _class_key_from_namespace(ns, c.name)
        prev = class_by_key.get(key)
        if prev is not None and prev.id != c.id:
            raise ValueError(f"Ambiguous class key {key}: {c.id} conflicts with {prev.id}")
        class_by_key[key] = c

    view_rows: list[tuple[str, str, str, str, str | None, tuple[str, ...]]] = []
    for v in index_views:
        class_key = _class_key_from_view(v, context="INDEX annotation")
        view_rows.append(
            (
                class_key[0],
                class_key[1],
                class_key[2],
                "index",
                None,
                tuple(str(m or "").strip() for m in (v.member_names or []) if str(m or "").strip()),
            )
        )
    for v in storage_views:
        class_key = _class_key_from_view(v, context="STORAGE annotation")
        view_rows.append(
            (
                class_key[0],
                class_key[1],
                class_key[2],
                v.operation.value,
                v.name,
                tuple(str(m or "").strip() for m in (v.member_names or []) if str(m or "").strip()),
            )
        )

    seen: set[tuple[str, str, str, str, tuple[str, ...]]] = set()
    seen_storage_names: set[tuple[str, str, str, str]] = set()
    for fqn_prefix, namespace, class_name, operation, name, member_tuple in view_rows:
        class_key = (fqn_prefix, namespace, class_name)
        members = list(member_tuple)
        if not members:
            raise ValueError(
                "INDEX annotation requires at least one member name: "
                f"{_class_fqn_from_key(class_key)}"
            )
        if len(set(members)) != len(members):
            raise ValueError(
                "INDEX annotation member_names must be unique (order-preserving): "
                f"{_class_fqn_from_key(class_key)} members={members!r}"
            )

        if name is not None:
            name_key = (fqn_prefix, namespace, class_name, name)
            if name_key in seen_storage_names:
                raise ValueError(f"Duplicate STORAGE annotation name for {name_key}.")
            seen_storage_names.add(name_key)

        key = (fqn_prefix, namespace, class_name, operation, tuple(members))
        if key in seen:
            if name is None:
                raise ValueError(f"Duplicate INDEX annotation for {key}.")
            raise ValueError(f"Duplicate STORAGE annotation for {key}.")
        seen.add(key)

        cls = class_by_key.get(class_key)
        if cls is None:
            raise ValueError(
                f"INDEX annotation targets unknown class {class_key}"
            )

        attr_by_name = {
            (link.attribute_config.name or "").strip(): link.attribute_config
            for link in cls.class_config_attribute_configs
            if link.attribute_config is not None
        }
        available = sorted([n for n in attr_by_name.keys() if n])

        for name in members:
            attr = attr_by_name.get(name)
            if attr is None:
                raise ValueError(
                    f"INDEX annotation references unknown member {name!r} on {cls.name} " f"(available={available})"
                )

            info = resolve_type_info(attr)
            if info.is_collection:
                raise ValueError(f"INDEX annotation does not support collection members yet: {cls.name}.{name}")

            if info.kind in {
                AttributeTypeDescriptorKind.primitive,
                AttributeTypeDescriptorKind.enum,
            }:
                continue

            if info.kind == AttributeTypeDescriptorKind.class_ and info.class_config is not None:
                if info.class_config.value_mode == ClassValueMode.inline_value:
                    raise ValueError(
                        f"INDEX annotation does not support inline_value members (JSON columns) yet: {cls.name}.{name}"
                    )
                continue

            raise ValueError(
                f"INDEX annotation does not support member kind {info.kind.value!r} yet: {cls.name}.{name}"
            )


def apply_load_annotations_to_relationships(
    compiled_annotations: list[ObjectConfigGraphAnnotation],
    class_relationships: list[ClassConfigRelationship],
    cross_relationships_by_target_ocg: dict[UUID, list[ClassConfigRelationship]],
    class_configs: list[ClassConfig],
    namespace_by_class_config_id: dict[UUID, NamespacePath],
) -> None:
    """Apply compiled LOAD annotations to relationship loading strategy fields.

    Matching key (canonical):
    - (fqn_prefix, namespace, source_class_name, source_attribute_name, edge_name?)
    """
    load_views: list[CodeSectionAnnotationLoad] = [
        a.code_section_annotation_load
        for a in compiled_annotations
        if a.kind == ObjectConfigGraphAnnotationKind.load and a.code_section_annotation_load is not None
    ]
    if not load_views:
        return

    class_by_id: dict[UUID, ClassConfig] = {c.id: c for c in class_configs}

    # Map AttributeConfig.id -> (owner_class_id, attr_name) deterministically.
    attr_name_by_id: dict[UUID, tuple[UUID, str]] = {}
    for c in class_configs:
        for link in c.class_config_attribute_configs:
            if link.attribute_config is None:
                continue
            attr_name_by_id[link.attribute_config.id] = (
                c.id,
                link.attribute_config.name,
            )

    # Build deterministic relationship index:
    # (pkg, namespace, source_class_name, source_attribute_name, edge_name?) -> relationship
    rel_by_key: dict[tuple[str, str, str, str, str | None], ClassConfigRelationship] = {}

    # Build a de-duplicated relationship list (same relationship may be returned in multiple
    # places by upstream builders; LOAD matching must treat that as one candidate).
    all_relationships: list[ClassConfigRelationship] = []
    seen_rel_ids: set[UUID] = set()
    for rel in class_relationships:
        if rel.id in seen_rel_ids:
            continue
        seen_rel_ids.add(rel.id)
        all_relationships.append(rel)
    for rels in cross_relationships_by_target_ocg.values():
        for rel in rels:
            if rel.id in seen_rel_ids:
                continue
            seen_rel_ids.add(rel.id)
            all_relationships.append(rel)

    for rel in all_relationships:
        src = class_by_id.get(rel.class_config_id)
        if src is None:
            raise ValueError(f"Cannot resolve source ClassConfig for relationship {rel.id}")

        ns = namespace_by_class_config_id.get(src.id)
        if ns is None:
            raise ValueError(
                f"Missing namespace for relationship source class {src.name} (class_id={src.id}). "
                "Expected namespace_by_class_config_id to be complete."
            )

        # Canonical relationships are single-sided; key by the FORWARD+REFERENCE attribute name.
        ref_attr_id: UUID | None = None
        for ra in rel.class_config_relationship_attributes:
            if (
                ra.direction == ClassConfigRelationshipDirection.forward
                and ra.role == ClassConfigRelationshipAttributeRole.reference
            ):
                ref_attr_id = ra.attribute_config_id
                break
        if ref_attr_id is None:
            raise ValueError(f"Relationship {rel.id} missing FORWARD+REFERENCE attribute binding")

        owner_and_name = attr_name_by_id.get(ref_attr_id)
        if owner_and_name is None:
            raise ValueError(
                f"Relationship {rel.id} reference attribute_config_id={ref_attr_id} not found on any class"
            )
        owner_class_id, attr_name = owner_and_name
        if owner_class_id != src.id:
            raise ValueError(
                f"Relationship {rel.id} reference attribute_config_id={ref_attr_id} is not owned by source class {src.name}"
            )

        assoc_name: str | None = None
        if rel.class_config_relationship_association_edge is not None:
            assoc_id = rel.class_config_relationship_association_edge.class_config_id
            if assoc_id is None:
                raise ValueError(f"Relationship {rel.id} has association with missing class_config_id")
            assoc_cls = class_by_id.get(assoc_id)
            if assoc_cls is None:
                raise ValueError(
                    f"Relationship {rel.id} association class_config_id={assoc_id} not found in graph class set"
                )
            assoc_name = assoc_cls.name

        key = (ns.package, ns.namespace, src.name, attr_name, assoc_name)
        prev = rel_by_key.get(key)
        if prev is not None and prev.id != rel.id:
            raise ValueError(
                f"Ambiguous relationship key {key}: relationship_id={rel.id} conflicts with relationship_id={prev.id}"
            )
        rel_by_key[key] = rel

    # Apply annotations: every LOAD must resolve to exactly one relationship key.
    seen_keys: set[tuple[str, str, str, str, str | None]] = set()
    for v in load_views:
        key = (
            v.fqn_prefix,
            _namespace_required(v, context="LOAD annotation"),
            v.class_name,
            v.attribute_name,
            v.edge_name or None,
        )
        if key in seen_keys:
            raise ValueError(f"Duplicate LOAD annotation for {key}. Canonical OCG requires a single declaration.")
        seen_keys.add(key)

        rel = rel_by_key.get(key)
        if rel is None:
            # If edge_name was omitted, allow resolution to a unique relationship for that attribute.
            # This supports ergonomics for association relationships where authors want:
            #   ann pkg.Domain.Schema.Class::attr load ...
            # without repeating the association edge class name, as long as it's unambiguous.
            if v.edge_name is None:
                base_key = (
                    v.fqn_prefix,
                    _namespace_required(v, context="LOAD annotation"),
                    v.class_name,
                    v.attribute_name,
                )
                # Derive candidates by scanning relationships directly (most robust).
                candidates: list[ClassConfigRelationship] = []
                for candidate in all_relationships:
                    cand_src = class_by_id.get(candidate.class_config_id)
                    if cand_src is None:
                        continue
                    cand_ns = namespace_by_class_config_id.get(cand_src.id)
                    if cand_ns is None:
                        continue

                    # Identify the declaring attribute name (FORWARD+REFERENCE).
                    cand_ref_attr_id: UUID | None = None
                    for ra in candidate.class_config_relationship_attributes:
                        if (
                            ra.direction == ClassConfigRelationshipDirection.forward
                            and ra.role == ClassConfigRelationshipAttributeRole.reference
                        ):
                            cand_ref_attr_id = ra.attribute_config_id
                            break
                    if cand_ref_attr_id is None:
                        continue
                    owner_and_name = attr_name_by_id.get(cand_ref_attr_id)
                    if owner_and_name is None:
                        continue
                    _, cand_attr_name = owner_and_name

                    cand_base_key = (
                        cand_ns.package,
                        cand_ns.namespace,
                        cand_src.name,
                        cand_attr_name,
                    )
                    if cand_base_key == base_key:
                        candidates.append(candidate)
                if len(candidates) == 1:
                    rel = candidates[0]
                elif len(candidates) > 1:
                    edge_names = []
                    for c in candidates:
                        assoc = c.class_config_relationship_association_edge
                        assoc_name = None
                        if assoc is not None and assoc.class_config_id is not None:
                            assoc_cls = class_by_id.get(assoc.class_config_id)
                            assoc_name = assoc_cls.name if assoc_cls is not None else None
                        edge_names.append(assoc_name)
                    raise ValueError(
                        f"LOAD annotation for {base_key} is ambiguous without ::edge. "
                        f"Candidates edge names: {edge_names!r}"
                    )
            if rel is None:
                raise ValueError(
                    f"LOAD annotation cannot be resolved to a relationship: {key}. "
                    f"Expected a relationship declared by {v.class_name}.{v.attribute_name} (edge={v.edge_name})."
                )

        # Semantics:
        # - `ann X::attr load ...` applies to the declared relationship (source -> association container when present).
        # - `ann X::attr::EdgeName load ...` applies to the association container's *target pointer* semantics.
        #   (Stored on ClassConfigRelationshipAssociation.*_loading_strategy for the transformer to consume.)
        if v.edge_name is not None:
            assoc = rel.class_config_relationship_association_edge
            if assoc is None:
                raise ValueError(
                    f"LOAD annotation specifies ::edge ({v.edge_name}) but relationship {rel.id} "
                    f"does not have an association container."
                )

            # When annotating association->target, treat a single 'load eager/lazy' (which parses as forward)
            # as applying to the target-side (reverse) pointer by default.
            if v.forward_strategy is not None and v.reverse_strategy is not None:
                assoc.forward_loading_strategy = ClassConfigRelationshipSideLoadingStrategy(v.forward_strategy.value)
                assoc.reverse_loading_strategy = ClassConfigRelationshipSideLoadingStrategy(v.reverse_strategy.value)
            else:
                strategy = v.forward_strategy or v.reverse_strategy
                if strategy is not None:
                    assoc.reverse_loading_strategy = ClassConfigRelationshipSideLoadingStrategy(strategy.value)
        else:
            if v.forward_strategy is not None:
                rel.forward_loading_strategy = ClassConfigRelationshipSideLoadingStrategy(v.forward_strategy.value)
            if v.reverse_strategy is not None:
                rel.reverse_loading_strategy = ClassConfigRelationshipSideLoadingStrategy(v.reverse_strategy.value)
