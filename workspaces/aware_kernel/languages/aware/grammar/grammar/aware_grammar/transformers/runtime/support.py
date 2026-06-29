"""Concrete runtime support owner for topology and output stage behavior."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType

from aware_meta.attribute.config.type_descriptor_builder import ensure_stable_descriptor_tree_ids
from aware_meta.class_.config.relationship_side_loading_config import (
    ClassConfigRelationshipSideLoadingConfig,
)
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.namespace.bundle import ObjectConfigGraphNamespaceBundle
from aware_meta.graph.config.namespace.builder import (
    build_namespace_bundle_from_code_provenance,
    build_namespace_bundle_from_ocg_topology,
)
from aware_meta.graph.config.relationship_analysis import (
    FkOverrideKey,
    FkOverrideSpec,
    ObjectConfigGraphRelationshipAnalysis,
    compute_fk_materialization_plan,
    compute_relationship_side_loading_overrides,
    stable_reified_association_source_relationship_id,
    stable_reified_association_target_relationship_id,
)
from aware_meta.graph.config.stable_ids import (
    stable_attribute_config_id,
    stable_class_config_attribute_config_id,
    stable_class_relationship_attribute_id,
)
from aware_meta.primitive.config.builder import build_primitive_config
from aware_meta_ontology.annotation.code_section_annotation_reference_enums import (
    CodeSectionAnnotationReferenceMode,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
    AttributeTypeDescriptorRole,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_link import AttributeTypeDescriptorLink
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import ClassConfigAttributeConfig
from aware_meta_ontology.class_.class_config_enums import ClassIdentityMode
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipIdentityRail,
    ClassConfigRelationshipReifiedRole,
    ClassConfigRelationshipSideLoadingStrategy,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)
from aware_meta_ontology.graph.config.object_config_graph_relationship import ObjectConfigGraphRelationship

from aware_grammar.primitive_codec import AwarePrimitiveCodec
from aware_utils.logging import logger
from aware_utils.string_transform import pluralize, singularize, to_snake_case

ReferencePortKey = tuple[str, str, str, str]
ReferenceBindKey = tuple[str | None, str | None, str, str]
ReferenceBindTarget = tuple[str, str, str, str]


def _annotation_namespace(annotation: object) -> str:
    namespace = getattr(annotation, "namespace", None)
    namespace_text = str(namespace).strip() if namespace is not None else ""
    if not namespace_text:
        raise ValueError(
            f"{type(annotation).__name__} requires namespace; retired annotation pair fields are not accepted."
        )
    return namespace_text


def _annotation_target_namespace(annotation: object) -> str | None:
    namespace = getattr(annotation, "target_namespace", None)
    if namespace is not None:
        namespace_text = str(namespace).strip()
        return namespace_text or None
    return None


@dataclass(slots=True)
class RuntimeTransformSupport:
    """Own shared runtime-topology/output support outside the transformer shell."""

    relationship_loading_config: ClassConfigRelationshipSideLoadingConfig | None = None
    namespace_by_code_id: dict[UUID, NamespacePath] | None = None
    external_graphs_by_id: dict[UUID, ObjectConfigGraph] | None = None
    primitive_codec: AwarePrimitiveCodec = field(default_factory=AwarePrimitiveCodec)

    def resolve_namespace_bundle_for_derived_graph(
        self,
        *,
        source_graph: ObjectConfigGraph,
        derived_class_configs: list[ClassConfig],
        derived_relationships: list[ClassConfigRelationship],
        derived_enum_configs: list[EnumConfig],
        derived_function_configs: list[FunctionConfig],
        namespace_by_code_id: dict[UUID, NamespacePath],
    ) -> ObjectConfigGraphNamespaceBundle:
        """Resolve runtime namespace ownership for the derived graph."""

        base: ObjectConfigGraphNamespaceBundle | None = None

        base = build_namespace_bundle_from_ocg_topology(ocg=source_graph)
        if not base.namespace_by_class_config_id:
            base = None

        if base is None:
            base = build_namespace_bundle_from_code_provenance(
                namespace_by_code_id=namespace_by_code_id,
                class_configs=derived_class_configs,
                enum_configs=derived_enum_configs,
                function_configs=derived_function_configs,
            )

        by_class = dict(base.namespace_by_class_config_id)
        by_enum = dict(base.namespace_by_enum_config_id)
        by_fn = dict(base.namespace_by_function_config_id)

        for rel in derived_relationships:
            assoc = rel.class_config_relationship_association_edge
            assoc_class_id = assoc.class_config_id if assoc is not None else None
            if assoc_class_id is None or assoc_class_id in by_class:
                continue
            src_ns = by_class.get(rel.class_config_id)
            tgt_ns = by_class.get(rel.target_class_config_id)
            inferred = src_ns or tgt_ns
            if inferred is not None:
                by_class[assoc_class_id] = inferred

        local_fallback_ns = next(iter(by_class.values()), None)
        self._merge_external_namespace_mappings(
            namespace_by_class=by_class,
            namespace_by_enum=by_enum,
            namespace_by_function=by_fn,
        )

        for rel in derived_relationships:
            assoc = rel.class_config_relationship_association_edge
            assoc_class_id = assoc.class_config_id if assoc is not None else None
            if assoc_class_id is None or assoc_class_id in by_class:
                continue
            src_ns = by_class.get(rel.class_config_id)
            tgt_ns = by_class.get(rel.target_class_config_id)
            inferred = src_ns or tgt_ns
            if inferred is not None:
                by_class[assoc_class_id] = inferred

        fallback_ns = local_fallback_ns
        if fallback_ns is not None:
            for cls in derived_class_configs:
                _ = by_class.setdefault(cls.id, fallback_ns)

        for cls in derived_class_configs:
            cls_ns = by_class.get(cls.id)
            if cls_ns is None:
                continue
            for fn_link in cls.class_config_function_configs:
                _ = by_fn.setdefault(fn_link.function_config.id, cls_ns)

        return ObjectConfigGraphNamespaceBundle(
            namespace_by_class_config_id=by_class,
            namespace_by_enum_config_id=by_enum,
            namespace_by_function_config_id=by_fn,
        )

    def _merge_external_namespace_mappings(
        self,
        *,
        namespace_by_class: dict[UUID, NamespacePath],
        namespace_by_enum: dict[UUID, NamespacePath],
        namespace_by_function: dict[UUID, NamespacePath],
    ) -> None:
        """Attach exact namespaces for classes owned by explicit external graphs."""

        for graph in (self.external_graphs_by_id or {}).values():
            bundle = build_namespace_bundle_from_ocg_topology(ocg=graph)
            for class_config_id, namespace in bundle.namespace_by_class_config_id.items():
                namespace_by_class.setdefault(class_config_id, namespace)
            for enum_config_id, namespace in bundle.namespace_by_enum_config_id.items():
                namespace_by_enum.setdefault(enum_config_id, namespace)
            for function_config_id, namespace in bundle.namespace_by_function_config_id.items():
                namespace_by_function.setdefault(function_config_id, namespace)

    def normalize_attribute_positions(
        self,
        *,
        class_configs: list[ClassConfig],
        analyses: list[ObjectConfigGraphRelationshipAnalysis],
    ) -> None:
        """Assign deterministic positions for synthetic runtime attributes."""

        attr_pos_by_id: dict[UUID, int] = {}
        for cls in class_configs:
            for acc in cls.class_config_attribute_configs:
                attr_pos_by_id[acc.attribute_config.id] = int(acc.position)

        synth_key_by_attr_id: dict[UUID, tuple[int, int, int]] = {}
        for analysis in analyses:
            rel = analysis.relationship
            forward_ref_id = analysis.forward_reference_attr.id
            declaring_ref_pos = attr_pos_by_id.get(forward_ref_id, 10**9)

            for rel_attr in rel.class_config_relationship_attributes:
                if rel_attr.role == ClassConfigRelationshipAttributeRole.foreign_key:
                    inverted_first = 0 if rel_attr.direction == ClassConfigRelationshipDirection.reverse else 1
                    synth_key_by_attr_id[rel_attr.attribute_config_id] = (0, inverted_first, declaring_ref_pos)
                elif rel_attr.role == ClassConfigRelationshipAttributeRole.auxiliary:
                    synth_key_by_attr_id[rel_attr.attribute_config_id] = (1, 1, declaring_ref_pos)
                elif (
                    rel_attr.role == ClassConfigRelationshipAttributeRole.reference
                    and rel_attr.direction == ClassConfigRelationshipDirection.reverse
                ):
                    synth_key_by_attr_id[rel_attr.attribute_config_id] = (2, 1, declaring_ref_pos)

        for cls in class_configs:
            source_links: list[ClassConfigAttributeConfig] = []
            synth_links: list[ClassConfigAttributeConfig] = []

            for acc in cls.class_config_attribute_configs:
                if acc.attribute_config.id in synth_key_by_attr_id:
                    synth_links.append(acc)
                else:
                    source_links.append(acc)

            used_positions = [int(acc.position) for acc in source_links]
            start_pos = (max(used_positions) + 1) if used_positions else len(source_links)

            def synth_sort_key(acc: ClassConfigAttributeConfig) -> tuple[int, int, int, str]:
                base = synth_key_by_attr_id.get(acc.attribute_config.id, (9, 9, 10**9))
                return (*base, acc.attribute_config.name)

            synth_links.sort(key=synth_sort_key)

            pos = start_pos
            for acc in synth_links:
                acc.position = pos
                pos += 1

    def apply_relationship_loading_overrides(
        self,
        analyses: list[ObjectConfigGraphRelationshipAnalysis],
    ) -> None:
        """Apply configured loading overrides onto analyzed relationships."""

        if not self.relationship_loading_config:
            return
        for analysis in analyses:
            overrides = compute_relationship_side_loading_overrides(self.relationship_loading_config, analysis)
            if overrides.forward is not None:
                analysis.relationship.forward_loading_strategy = overrides.forward
            if overrides.reverse is not None:
                analysis.relationship.reverse_loading_strategy = overrides.reverse

    def materialize_reverse_views(self, analyses: list[ObjectConfigGraphRelationshipAnalysis]) -> None:
        """Materialize reverse relationship views required by runtime traversal."""

        for analysis in analyses:
            rel = analysis.relationship
            if rel.reverse_loading_strategy is None or analysis.reverse_reference_attr is not None:
                continue

            target = analysis.target_class
            source = analysis.source_class
            if rel.relationship_type in {
                ClassConfigRelationshipType.many_to_one,
                ClassConfigRelationshipType.many_to_many,
            }:
                collection = AttributeCollectionType.list
            else:
                collection = AttributeCollectionType.single

            is_lazy = rel.reverse_loading_strategy == ClassConfigRelationshipSideLoadingStrategy.lazy
            is_required = (not is_lazy) if collection == AttributeCollectionType.single else False

            base_name = to_snake_case(source.name)
            name = self.validate_unique(target, base_name)

            attr = AttributeConfig(
                owner_key=self.attribute_owner_key(target),
                name=name,
                description=f"Reverse view for {source.name}.{analysis.forward_reference_attr.name}",
                is_public=True,
                is_required=is_required,
                exclude_serialization=is_lazy,
                is_unique=False,
                is_virtual=False,
                type_descriptor=self._build_class_descriptor(source, collection),
            )
            self.attach_attribute(target, attr)

            rel.class_config_relationship_attributes.append(
                ClassConfigRelationshipAttribute(
                    id=stable_class_relationship_attribute_id(
                        relationship_id=rel.id,
                        attribute_config_id=attr.id,
                        direction=ClassConfigRelationshipDirection.reverse.value,
                        role=ClassConfigRelationshipAttributeRole.reference.value,
                    ),
                    class_config_relationship_id=rel.id,
                    attribute_config_id=attr.id,
                    direction=ClassConfigRelationshipDirection.reverse,
                    role=ClassConfigRelationshipAttributeRole.reference,
                )
            )

    def apply_forward_pointer_representation_semantics(
        self,
        analyses: list[ObjectConfigGraphRelationshipAnalysis],
    ) -> None:
        """Apply loading-driven requiredness and serialization semantics."""

        for analysis in analyses:
            rel = analysis.relationship
            attr = analysis.forward_reference_attr
            strategy = rel.forward_loading_strategy or ClassConfigRelationshipSideLoadingStrategy.lazy
            is_lazy = strategy == ClassConfigRelationshipSideLoadingStrategy.lazy
            declared_required = bool(rel.forward_required)

            attr.exclude_serialization = is_lazy
            if is_lazy:
                attr.is_required = False
                attr.default_value = self.primitive_codec.to_literal_string(None)
            else:
                attr.is_required = declared_required

    def materialize_foreign_keys_and_edges(
        self,
        analyses: list[ObjectConfigGraphRelationshipAnalysis],
        *,
        code_primitive_type: type[CodePrimitiveType] | None,
        fk_overrides_by_key: dict[FkOverrideKey, FkOverrideSpec],
        rel_name_overrides_by_key: dict[FkOverrideKey, str],
        local_class_ids: set[UUID],
        reference_ports: set[ReferencePortKey],
        reference_binds: dict[ReferenceBindKey, ReferenceBindTarget],
    ) -> None:
        """Materialize FK rails and edge helper attributes for runtime topology."""

        for analysis in analyses:
            rel = analysis.relationship
            reference_identity_key_requested = self._relationship_reference_identity_key_requested(analysis=analysis)
            if (
                reference_identity_key_requested
                and analysis.forward_is_list
                and not (analysis.requires_join_table and analysis.association_class is not None)
            ):
                raise ValueError(
                    "relationship reference identity key is unsupported for list relationships; "
                    + "use association-edge list relationships or scalar reference keys only "
                    + f"(source_class={analysis.source_class.name!r}, "
                    + f"attribute={analysis.forward_reference_attr.name!r}, relationship_id={analysis.relationship.id})"
                )

            if analysis.requires_join_table and analysis.association_class is not None:
                self._ensure_association_target_reference(
                    analysis,
                    rel_name_overrides_by_key=rel_name_overrides_by_key,
                )
                src_fk_id, tgt_fk_id = self._materialize_association_foreign_keys(
                    analysis,
                    code_primitive_type=code_primitive_type,
                    rel_name_overrides_by_key=rel_name_overrides_by_key,
                )
                self._mark_association_foreign_key_identity_from_constructors(
                    analysis,
                    source_fk_id=src_fk_id,
                    target_fk_id=tgt_fk_id,
                )
                if reference_identity_key_requested:
                    self.mark_class_attribute_identity_key(
                        cls=analysis.association_class,
                        attribute_config_id=src_fk_id,
                    )
                    self.mark_class_attribute_identity_key(
                        cls=analysis.association_class,
                        attribute_config_id=tgt_fk_id,
                    )
                    self._clear_relationship_reference_identity_key(analysis=analysis)
                self._materialize_edge_helper_attribute(analysis)
                continue

            if analysis.fk_owner_class is None or analysis.fk_column_name is None or analysis.fk_owner_side is None:
                continue

            bound_target = self._bound_reference_target(analysis, binds=reference_binds)
            if bound_target is not None:
                bound_fk_attribute_id = self._attach_bound_foreign_key(
                    analysis,
                    target=bound_target,
                    ports=reference_ports,
                )
                if reference_identity_key_requested:
                    self.mark_class_attribute_identity_key(
                        cls=analysis.fk_owner_class,
                        attribute_config_id=bound_fk_attribute_id,
                    )
                    self._clear_relationship_reference_identity_key(analysis=analysis)
                continue

            plan = compute_fk_materialization_plan(
                analysis,
                overrides_by_key=fk_overrides_by_key,
                validate_unique=self.validate_unique,
            )
            if plan is None:
                continue
            rel.forward_required = plan.db_required
            if plan.owner_class.id not in local_class_ids:
                logger.debug(
                    "Skipping FK synthesis onto external class "
                    + f"{plan.owner_class.name} for relationship "
                    + f"{analysis.source_class.name}.{analysis.forward_reference_attr.name} "
                    + f"(relationship_id={analysis.relationship.id})"
                )
                continue
            if plan.name_is_override:
                self._assert_name_available(plan.owner_class, plan.name)

            fk_attr = AttributeConfig(
                owner_key=self.attribute_owner_key(plan.owner_class),
                name=plan.name,
                description=f"Foreign key for {analysis.source_class.name}.{analysis.forward_reference_attr.name}",
                is_public=False,
                is_required=plan.runtime_required,
                is_unique=plan.unique,
                is_virtual=False,
                is_primary=reference_identity_key_requested,
                type_descriptor=self.build_uuid_primitive_descriptor(code_primitive_type),
            )
            self.attach_attribute(plan.owner_class, fk_attr)

            rel.class_config_relationship_attributes.append(
                ClassConfigRelationshipAttribute(
                    id=stable_class_relationship_attribute_id(
                        relationship_id=rel.id,
                        attribute_config_id=fk_attr.id,
                        direction=analysis.fk_owner_side.value,
                        role=ClassConfigRelationshipAttributeRole.foreign_key.value,
                    ),
                    class_config_relationship_id=rel.id,
                    attribute_config_id=fk_attr.id,
                    direction=analysis.fk_owner_side,
                    role=ClassConfigRelationshipAttributeRole.foreign_key,
                )
            )
            if reference_identity_key_requested:
                self.mark_class_attribute_identity_key(
                    cls=plan.owner_class,
                    attribute_config_id=fk_attr.id,
                )
                self._clear_relationship_reference_identity_key(analysis=analysis)

    def reify_association_edges(
        self,
        *,
        analyses: list[ObjectConfigGraphRelationshipAnalysis],
        relationships: list[ClassConfigRelationship],
        object_config_graph_relationships: list[ObjectConfigGraphRelationship],
        local_class_ids: set[UUID],
    ) -> tuple[list[ClassConfigRelationship], list[ObjectConfigGraphRelationship]]:
        """Reify association edges into explicit runtime traversal relationships."""

        target_ocg_id_by_relationship_id: dict[UUID, UUID] = {}
        for ocg_rel in object_config_graph_relationships:
            target_id = ocg_rel.target_object_config_graph_id
            for rel in ocg_rel.class_config_relationships:
                target_ocg_id_by_relationship_id[rel.id] = target_id

        reified_local: list[ClassConfigRelationship] = []
        reified_detached_by_target_ocg: dict[UUID, list[ClassConfigRelationship]] = {}

        for analysis in analyses:
            if not analysis.requires_join_table or analysis.association_class is None:
                continue

            assoc_cls = analysis.association_class
            rel = analysis.relationship
            analysis.forward_reference_attr.is_virtual = True

            edge_helper_attr_id: UUID | None = None
            assoc_target_ref_attr_id: UUID | None = None
            src_fk_attr_id: UUID | None = None
            tgt_fk_attr_id: UUID | None = None

            for rel_attr in rel.class_config_relationship_attributes:
                if rel_attr.role == ClassConfigRelationshipAttributeRole.auxiliary:
                    if rel_attr.direction == ClassConfigRelationshipDirection.forward:
                        edge_helper_attr_id = edge_helper_attr_id or rel_attr.attribute_config_id
                    elif rel_attr.direction == ClassConfigRelationshipDirection.reverse:
                        assoc_target_ref_attr_id = assoc_target_ref_attr_id or rel_attr.attribute_config_id
                elif rel_attr.role == ClassConfigRelationshipAttributeRole.foreign_key:
                    if rel_attr.direction == ClassConfigRelationshipDirection.forward:
                        src_fk_attr_id = src_fk_attr_id or rel_attr.attribute_config_id
                    elif rel_attr.direction == ClassConfigRelationshipDirection.reverse:
                        tgt_fk_attr_id = tgt_fk_attr_id or rel_attr.attribute_config_id

            if edge_helper_attr_id is None:
                raise ValueError(
                    "Association reification requires an edge helper attribute on the source class: "
                    + f"relationship_id={rel.id}"
                )
            if assoc_target_ref_attr_id is None:
                raise ValueError(
                    "Association reification requires a target reference attribute on the association class: "
                    + f"relationship_id={rel.id}"
                )
            if src_fk_attr_id is None or tgt_fk_attr_id is None:
                raise ValueError(
                    "Association reification requires both join FKs on the association class: "
                    + f"relationship_id={rel.id}"
                )

            edge_helper_attr_name = next(
                (
                    link.attribute_config.name
                    for link in analysis.source_class.class_config_attribute_configs
                    if link.attribute_config.id == edge_helper_attr_id
                ),
                None,
            )
            if edge_helper_attr_name is None:
                raise ValueError(
                    "Association reification requires the edge helper attribute to remain attached on the source class: "
                    + f"relationship_id={rel.id}, attribute_id={edge_helper_attr_id}"
                )
            assoc_target_ref_attr_name = next(
                (
                    link.attribute_config.name
                    for link in assoc_cls.class_config_attribute_configs
                    if link.attribute_config.id == assoc_target_ref_attr_id
                ),
                None,
            )
            if assoc_target_ref_attr_name is None:
                raise ValueError(
                    "Association reification requires the target reference attribute to remain attached on the association class: "
                    + f"relationship_id={rel.id}, attribute_id={assoc_target_ref_attr_id}"
                )
            edge_helper_attr = next(
                (
                    link.attribute_config
                    for link in analysis.source_class.class_config_attribute_configs
                    if link.attribute_config.id == edge_helper_attr_id
                ),
                None,
            )
            assoc_target_ref_attr = next(
                (
                    link.attribute_config
                    for link in assoc_cls.class_config_attribute_configs
                    if link.attribute_config.id == assoc_target_ref_attr_id
                ),
                None,
            )
            src_fk_attr = next(
                (
                    link.attribute_config
                    for link in assoc_cls.class_config_attribute_configs
                    if link.attribute_config.id == src_fk_attr_id
                ),
                None,
            )
            tgt_fk_attr = next(
                (
                    link.attribute_config
                    for link in assoc_cls.class_config_attribute_configs
                    if link.attribute_config.id == tgt_fk_attr_id
                ),
                None,
            )
            if edge_helper_attr is None or assoc_target_ref_attr is None or src_fk_attr is None or tgt_fk_attr is None:
                raise ValueError(
                    "Association reification requires live attribute objects for all synthesized edge members: "
                    + f"relationship_id={rel.id}"
                )

            rel_source_id = stable_reified_association_source_relationship_id(relationship_id=rel.id)
            rel_source = ClassConfigRelationship(
                id=rel_source_id,
                relationship_key=edge_helper_attr_name,
                relationship_type=(
                    ClassConfigRelationshipType.one_to_many
                    if analysis.forward_is_list
                    else ClassConfigRelationshipType.one_to_one
                ),
                identity_rail=ClassConfigRelationshipIdentityRail.containment,
                forward_required=bool(rel.forward_required),
                forward_loading_strategy=rel.forward_loading_strategy,
                reverse_loading_strategy=None,
                class_config_id=analysis.source_class.id,
                target_class_config=assoc_cls,
                target_class_config_id=assoc_cls.id,
                reified_from_relationship_id=rel.id,
                reified_role=ClassConfigRelationshipReifiedRole.source_to_association,
            )
            rel_source.class_config_relationship_attributes = [
                ClassConfigRelationshipAttribute(
                    id=stable_class_relationship_attribute_id(
                        relationship_id=rel_source_id,
                        attribute_config_id=edge_helper_attr_id,
                        direction=ClassConfigRelationshipDirection.forward.value,
                        role=ClassConfigRelationshipAttributeRole.reference.value,
                    ),
                    class_config_relationship_id=rel_source_id,
                    attribute_config_id=edge_helper_attr_id,
                    attribute_config=edge_helper_attr,
                    direction=ClassConfigRelationshipDirection.forward,
                    role=ClassConfigRelationshipAttributeRole.reference,
                ),
                ClassConfigRelationshipAttribute(
                    id=stable_class_relationship_attribute_id(
                        relationship_id=rel_source_id,
                        attribute_config_id=src_fk_attr_id,
                        direction=ClassConfigRelationshipDirection.reverse.value,
                        role=ClassConfigRelationshipAttributeRole.foreign_key.value,
                    ),
                    class_config_relationship_id=rel_source_id,
                    attribute_config_id=src_fk_attr_id,
                    attribute_config=src_fk_attr,
                    direction=ClassConfigRelationshipDirection.reverse,
                    role=ClassConfigRelationshipAttributeRole.foreign_key,
                ),
            ]

            rel_target_id = stable_reified_association_target_relationship_id(relationship_id=rel.id)
            rel_target_type = self._reified_association_target_relationship_type(analysis)
            rel_target = ClassConfigRelationship(
                id=rel_target_id,
                relationship_key=assoc_target_ref_attr_name,
                relationship_type=rel_target_type,
                identity_rail=ClassConfigRelationshipIdentityRail.reference,
                forward_required=True,
                forward_loading_strategy=(
                    rel.class_config_relationship_association_edge.reverse_loading_strategy
                    if rel.class_config_relationship_association_edge is not None
                    and rel.class_config_relationship_association_edge.reverse_loading_strategy is not None
                    else ClassConfigRelationshipSideLoadingStrategy.lazy
                ),
                reverse_loading_strategy=None,
                class_config_id=assoc_cls.id,
                target_class_config=analysis.target_class,
                target_class_config_id=analysis.target_class.id,
                reified_from_relationship_id=rel.id,
                reified_role=ClassConfigRelationshipReifiedRole.association_to_target,
            )
            rel_target.class_config_relationship_attributes = [
                ClassConfigRelationshipAttribute(
                    id=stable_class_relationship_attribute_id(
                        relationship_id=rel_target_id,
                        attribute_config_id=assoc_target_ref_attr_id,
                        direction=ClassConfigRelationshipDirection.forward.value,
                        role=ClassConfigRelationshipAttributeRole.reference.value,
                    ),
                    class_config_relationship_id=rel_target_id,
                    attribute_config_id=assoc_target_ref_attr_id,
                    attribute_config=assoc_target_ref_attr,
                    direction=ClassConfigRelationshipDirection.forward,
                    role=ClassConfigRelationshipAttributeRole.reference,
                ),
                ClassConfigRelationshipAttribute(
                    id=stable_class_relationship_attribute_id(
                        relationship_id=rel_target_id,
                        attribute_config_id=tgt_fk_attr_id,
                        direction=ClassConfigRelationshipDirection.forward.value,
                        role=ClassConfigRelationshipAttributeRole.foreign_key.value,
                    ),
                    class_config_relationship_id=rel_target_id,
                    attribute_config_id=tgt_fk_attr_id,
                    attribute_config=tgt_fk_attr,
                    direction=ClassConfigRelationshipDirection.forward,
                    role=ClassConfigRelationshipAttributeRole.foreign_key,
                ),
            ]

            reified_local.append(rel_source)
            if analysis.target_class.id in local_class_ids:
                reified_local.append(rel_target)
            else:
                target_ocg_id = target_ocg_id_by_relationship_id.get(rel.id)
                if target_ocg_id is None:
                    raise ValueError(
                        f"Cross-OCG association reification requires a target OCG mapping for relationship {rel.id}"
                    )
                reified_detached_by_target_ocg.setdefault(target_ocg_id, []).append(rel_target)

        relationships.extend(reified_local)
        if reified_detached_by_target_ocg:
            for ocg_rel in object_config_graph_relationships:
                add = reified_detached_by_target_ocg.get(ocg_rel.target_object_config_graph_id)
                if add:
                    ocg_rel.class_config_relationships.extend(add)

        return relationships, object_config_graph_relationships

    def sync_class_relationship_views(
        self,
        *,
        class_configs: list[ClassConfig],
        relationships: list[ClassConfigRelationship],
        analyses: list[ObjectConfigGraphRelationshipAnalysis] | None = None,
        object_config_graph_relationships: list[ObjectConfigGraphRelationship] | None = None,
    ) -> None:
        """Align class-owned relationship views with canonical relationship nodes."""

        relationship_by_source_and_id: dict[
            UUID, dict[UUID, ClassConfigRelationship]
        ] = {}

        def _index_relationship(relationship: ClassConfigRelationship) -> None:
            relationship_by_source_and_id.setdefault(
                relationship.class_config_id, {}
            )[relationship.id] = relationship

        for relationship in relationships:
            _index_relationship(relationship)
        for analysis in analyses or ():
            analysis.relationship.target_class_config = analysis.target_class
            self._hydrate_descriptor_class_config(
                descriptor=analysis.forward_reference_attr.type_descriptor,
                target_class=analysis.target_class,
            )
            if analysis.reverse_reference_attr is not None:
                self._hydrate_descriptor_class_config(
                    descriptor=analysis.reverse_reference_attr.type_descriptor,
                    target_class=analysis.source_class,
                )
            _index_relationship(analysis.relationship)
        for ocg_rel in object_config_graph_relationships or []:
            for relationship in ocg_rel.class_config_relationships:
                _index_relationship(relationship)

        for cls in class_configs:
            cls.class_config_relationships = sorted(
                relationship_by_source_and_id.get(cls.id, {}).values(),
                key=lambda rel: (
                    str(rel.relationship_key or "").casefold(),
                    str(rel.id),
                ),
            )

    def _hydrate_descriptor_class_config(
        self,
        *,
        descriptor: AttributeTypeDescriptor | None,
        target_class: ClassConfig,
    ) -> None:
        if descriptor is None:
            return
        if (
            descriptor.kind == AttributeTypeDescriptorKind.class_
            and descriptor.class_config_id == target_class.id
        ):
            descriptor.class_config = target_class
        for child_link in descriptor.child_links:
            self._hydrate_descriptor_class_config(
                descriptor=child_link.child,
                target_class=target_class,
            )

    def index_reference_ports(self, root: ObjectConfigGraph) -> set[ReferencePortKey]:
        """Index reference-port annotations reachable from the runtime graph inputs."""

        ports: set[ReferencePortKey] = set()
        port_graph_ids_by_key: dict[ReferencePortKey, UUID] = {}
        graphs_by_id: dict[UUID, ObjectConfigGraph] = {}
        for graph in self._iter_reachable_graphs(root):
            graphs_by_id[graph.id] = graph
        for graph in (self.external_graphs_by_id or {}).values():
            graphs_by_id[graph.id] = graph

        for graph in graphs_by_id.values():
            graph_id = graph.id or UUID(int=0)
            for ann in graph.object_config_graph_annotations:
                if ann.kind != ObjectConfigGraphAnnotationKind.reference:
                    continue
                ref = ann.code_section_annotation_reference
                if ref is None or ref.mode != CodeSectionAnnotationReferenceMode.port:
                    continue
                key = (
                    ref.fqn_prefix,
                    _annotation_namespace(ref),
                    ref.class_name,
                    ref.attribute_name,
                )
                existing_graph_id = port_graph_ids_by_key.get(key)
                if existing_graph_id is not None:
                    if existing_graph_id == graph_id:
                        raise ValueError(
                            f"Duplicate reference port annotation for {key}"
                        )
                    continue
                if key in ports:
                    raise ValueError(f"Duplicate reference port annotation for {key}")
                ports.add(key)
                port_graph_ids_by_key[key] = graph_id
        return ports

    def index_reference_binds(
        self,
        graph: ObjectConfigGraph,
    ) -> dict[ReferenceBindKey, ReferenceBindTarget]:
        """Index reference-bind annotations declared on the root graph."""

        binds: dict[ReferenceBindKey, ReferenceBindTarget] = {}
        for ann in graph.object_config_graph_annotations:
            if ann.kind != ObjectConfigGraphAnnotationKind.reference:
                continue
            ref = ann.code_section_annotation_reference
            if ref is None or ref.mode != CodeSectionAnnotationReferenceMode.bind:
                continue
            target_namespace = _annotation_target_namespace(ref)
            if (
                ref.target_fqn_prefix is None
                or target_namespace is None
                or ref.target_class_name is None
                or ref.target_attribute_name is None
            ):
                raise ValueError(
                    "reference bind annotation missing namespace-native target fields"
                )
            key = (
                ref.fqn_prefix,
                _annotation_namespace(ref),
                ref.class_name,
                ref.attribute_name,
            )
            target = (
                ref.target_fqn_prefix,
                target_namespace,
                ref.target_class_name,
                ref.target_attribute_name,
            )
            if key in binds and binds[key] != target:
                raise ValueError(
                    f"Duplicate reference bind annotation for {key} with different targets"
                )
            binds[key] = target
        return binds

    def attribute_owner_key(self, cls: ClassConfig) -> str:
        """Resolve the semantic owner key for transformer-synthesized attributes."""

        class_fqn = (cls.class_fqn or "").strip()
        if class_fqn:
            return class_fqn

        if cls.code_section_class is not None and self.namespace_by_code_id is not None:
            code_id = cls.code_section_class.code_section.code_id
            namespace = self.namespace_by_code_id.get(code_id)
            if namespace is not None:
                owner_key = namespace.fqn(cls.name).strip()
                if owner_key:
                    return owner_key

        raise ValueError(
            "Transformer cannot synthesize AttributeConfig without a semantic owner_key "
            + f"(class_id={cls.id}, class_name={cls.name!r})"
        )

    def attach_attribute(self, cls: ClassConfig, attr: AttributeConfig) -> None:
        """Attach a stable synthesized attribute to a class."""

        if attr.code_section_attribute is None:
            attr.owner_key = self.attribute_owner_key(cls)
            attr.id = stable_attribute_config_id(owner_key=attr.owner_key, name=attr.name)
            attr.type_descriptor = ensure_stable_descriptor_tree_ids(attr.type_descriptor)
            attr.type_descriptor_id = attr.type_descriptor.id

        link = ClassConfigAttributeConfig(
            id=stable_class_config_attribute_config_id(
                class_config_id=cls.id,
                attribute_config_id=attr.id,
            ),
            class_config_id=cls.id,
            attribute_config=attr,
            attribute_config_id=attr.id,
        )
        link.position = self._next_attribute_position(cls)
        cls.class_config_attribute_configs.append(link)

    def validate_unique(self, cls: ClassConfig, base: str) -> str:
        """Validate that a synthesized attribute name is unique for the class."""

        existing = {acc.attribute_config.name for acc in cls.class_config_attribute_configs if acc.attribute_config}
        if base not in existing:
            return base

        fqn: str | None = None
        if cls.code_section_class is not None and self.namespace_by_code_id is not None:
            code_id = cls.code_section_class.code_section.code_id
            namespace = self.namespace_by_code_id.get(code_id)
            if namespace is not None:
                fqn = namespace.fqn(cls.name)

        class_name = fqn or cls.name
        raise Exception(f"Class: {class_name}, Attribute name {base} already exists")

    def mark_class_attribute_identity_key(
        self,
        *,
        cls: ClassConfig,
        attribute_config_id: UUID,
    ) -> None:
        """Mark the class-owned attribute link as an identity key."""

        for link in cls.class_config_attribute_configs:
            if link.attribute_config_id == attribute_config_id:
                link.is_identity_key = True
                return
        raise ValueError(
            "propagation identity annotation failed: FK attribute link missing on target class "
            + f"(class={cls.name!r}, attribute_config_id={attribute_config_id})"
        )

    def class_identity_mode(self, *, cls: ClassConfig) -> ClassIdentityMode:
        """Resolve identity mode defensively from serialized or live enum values."""

        raw_mode = getattr(cls, "identity_mode", None)
        if isinstance(raw_mode, ClassIdentityMode):
            return raw_mode
        raw_value = getattr(raw_mode, "value", raw_mode)
        token = str(raw_value or "").strip().casefold()
        if token == ClassIdentityMode.standalone.value:
            return ClassIdentityMode.standalone
        return ClassIdentityMode.contained

    def build_uuid_primitive_descriptor(
        self,
        _code_primitive_type: type[CodePrimitiveType] | None,
    ) -> AttributeTypeDescriptor:
        """Build a canonical UUID primitive descriptor for synthesized runtime FKs."""

        prim_type = CodePrimitiveType(
            signature=CodePrimitiveBaseType.uuid.value,
            base_type=CodePrimitiveBaseType.uuid,
            constraints=None,
        )
        prim = build_primitive_config(prim_type)
        descriptor = AttributeTypeDescriptor(
            kind=AttributeTypeDescriptorKind.primitive,
            primitive_config=prim,
            primitive_config_id=prim.id,
        )
        return ensure_stable_descriptor_tree_ids(descriptor)

    def _iter_reachable_graphs(self, root: ObjectConfigGraph) -> list[ObjectConfigGraph]:
        graphs: list[ObjectConfigGraph] = []
        seen: set[UUID] = set()
        stack: list[ObjectConfigGraph] = [root]
        while stack:
            graph = stack.pop()
            if graph.id in seen:
                continue
            seen.add(graph.id)
            graphs.append(graph)
            for rel in graph.object_config_graph_relationships:
                if rel.target_object_config_graph is not None:
                    stack.append(rel.target_object_config_graph)
        return graphs

    def _relationship_reference_identity_key_requested(
        self,
        *,
        analysis: ObjectConfigGraphRelationshipAnalysis,
    ) -> bool:
        link = self._class_attribute_link(
            cls=analysis.source_class,
            attribute_config_id=analysis.forward_reference_attr.id,
        )
        if link is None:
            return bool(analysis.forward_reference_attr.is_primary)
        return bool(link.is_identity_key) or bool(analysis.forward_reference_attr.is_primary)

    def _clear_relationship_reference_identity_key(
        self,
        *,
        analysis: ObjectConfigGraphRelationshipAnalysis,
    ) -> None:
        link = self._class_attribute_link(
            cls=analysis.source_class,
            attribute_config_id=analysis.forward_reference_attr.id,
        )
        if link is None:
            raise ValueError(
                "relationship identity key remap failed: source reference attribute link is missing "
                + f"(class={analysis.source_class.name!r}, attribute={analysis.forward_reference_attr.name!r}, "
                + f"relationship_id={analysis.relationship.id})"
            )
        link.is_identity_key = False
        link.attribute_config.is_primary = False
        analysis.forward_reference_attr.is_primary = False

    def _class_attribute_link(
        self,
        *,
        cls: ClassConfig,
        attribute_config_id: UUID,
    ) -> ClassConfigAttributeConfig | None:
        for link in cls.class_config_attribute_configs:
            if link.attribute_config_id == attribute_config_id:
                return link
        return None

    def _bound_reference_target(
        self,
        analysis: ObjectConfigGraphRelationshipAnalysis,
        *,
        binds: dict[ReferenceBindKey, ReferenceBindTarget],
    ) -> ReferenceBindTarget | None:
        ns = analysis.source_namespace
        full_key = self._reference_bind_key_for_analysis(analysis)
        hit = binds.get(full_key)
        if hit is not None:
            return hit
        fallback_key = (None, None, full_key[2], full_key[3])
        return binds.get(fallback_key)

    def _reference_bind_key_for_analysis(
        self,
        analysis: ObjectConfigGraphRelationshipAnalysis,
    ) -> ReferenceBindKey:
        ns = analysis.source_namespace
        return (
            (ns.package if ns is not None else None),
            (ns.namespace if ns is not None else None),
            analysis.source_class.name,
            analysis.forward_reference_attr.name,
        )

    def _attach_bound_foreign_key(
        self,
        analysis: ObjectConfigGraphRelationshipAnalysis,
        *,
        target: ReferenceBindTarget,
        ports: set[ReferencePortKey],
    ) -> UUID:
        if analysis.fk_owner_class is None or analysis.fk_owner_side is None:
            raise ValueError(
                "reference bind cannot apply to relationship without FK ownership: "
                + f"relationship_id={analysis.relationship.id}"
            )
        if analysis.requires_join_table:
            raise ValueError(
                f"reference bind cannot apply to join-table relationships: relationship_id={analysis.relationship.id}"
            )

        tgt_fqn_prefix, tgt_namespace, tgt_class, tgt_attr = target
        port_key = (tgt_fqn_prefix, tgt_namespace, tgt_class, tgt_attr)
        if port_key not in ports:
            raise ValueError(
                f"reference bind target must be declared as a reference port: {port_key} "
                + f"(relationship_id={analysis.relationship.id})"
            )

        owner_fqn = NamespacePath(package=tgt_fqn_prefix, namespace=tgt_namespace).fqn(tgt_class)
        actual_owner_fqn = (analysis.fk_owner_class.class_fqn or "").strip()
        if actual_owner_fqn != owner_fqn:
            raise ValueError(
                "reference bind target class does not match FK owner class for relationship "
                + f"{analysis.source_class.name}.{analysis.forward_reference_attr.name}: "
                + f"expected_fk_owner={owner_fqn} actual_fk_owner={analysis.fk_owner_class.name}"
            )

        expected_attr_id = stable_attribute_config_id(owner_key=owner_fqn, name=tgt_attr)
        bound_attr: AttributeConfig | None = None
        for link in analysis.fk_owner_class.class_config_attribute_configs:
            if link.attribute_config.id == expected_attr_id:
                bound_attr = link.attribute_config
                break
        if bound_attr is None:
            raise ValueError(f"reference bind target attribute not found on FK owner class: {owner_fqn}::{tgt_attr}")

        td = bound_attr.type_descriptor

        def is_uuid_or_optional_uuid(descriptor: AttributeTypeDescriptor | None) -> bool:
            if descriptor is None:
                return False
            if descriptor.kind == AttributeTypeDescriptorKind.primitive:
                prim = descriptor.primitive_config
                base = prim.primitive_type.base_type if prim is not None else None
                return base == CodePrimitiveBaseType.uuid
            if descriptor.kind == AttributeTypeDescriptorKind.union:
                bases: set[CodePrimitiveBaseType] = set()
                for link in descriptor.child_links:
                    if link.role != AttributeTypeDescriptorRole.member:
                        continue
                    child = link.child
                    if child.kind != AttributeTypeDescriptorKind.primitive:
                        return False
                    prim = child.primitive_config
                    base = prim.primitive_type.base_type if prim is not None else None
                    if base is None:
                        return False
                    bases.add(base)
                return bases == {CodePrimitiveBaseType.uuid, CodePrimitiveBaseType.null}
            return False

        if not is_uuid_or_optional_uuid(td):
            raise ValueError(
                f"reference port attribute must be a UUID primitive (or UUID?): {owner_fqn}::{tgt_attr} "
                + f"(kind={td.kind})"
            )

        existing = [
            rel_attr
            for rel_attr in analysis.relationship.class_config_relationship_attributes
            if rel_attr.role == ClassConfigRelationshipAttributeRole.foreign_key
            and rel_attr.direction == analysis.fk_owner_side
        ]
        if existing:
            mismatch = [rel_attr for rel_attr in existing if rel_attr.attribute_config_id != bound_attr.id]
            if mismatch:
                raise ValueError(
                    "Relationship already has a different FOREIGN_KEY attribute: "
                    + f"relationship_id={analysis.relationship.id}"
                )
            return bound_attr.id

        analysis.relationship.class_config_relationship_attributes.append(
            ClassConfigRelationshipAttribute(
                id=stable_class_relationship_attribute_id(
                    relationship_id=analysis.relationship.id,
                    attribute_config_id=bound_attr.id,
                    direction=analysis.fk_owner_side.value,
                    role=ClassConfigRelationshipAttributeRole.foreign_key.value,
                ),
                class_config_relationship_id=analysis.relationship.id,
                attribute_config_id=bound_attr.id,
                direction=analysis.fk_owner_side,
                role=ClassConfigRelationshipAttributeRole.foreign_key,
            )
        )
        return bound_attr.id

    def _materialize_association_foreign_keys(
        self,
        analysis: ObjectConfigGraphRelationshipAnalysis,
        *,
        code_primitive_type: type[CodePrimitiveType] | None,
        rel_name_overrides_by_key: dict[FkOverrideKey, str],
    ) -> tuple[UUID, UUID]:
        assoc_cls = analysis.association_class
        if assoc_cls is None:
            raise ValueError(
                "association FK materialization requires an association class "
                + f"(relationship_id={analysis.relationship.id})"
            )

        src_fk_name = f"{to_snake_case(analysis.source_class.name)}_id"
        member_role_name = self._association_member_role_name(
            analysis,
            rel_name_overrides_by_key=rel_name_overrides_by_key,
        )
        tgt_fk_name = f"{member_role_name}_id"

        src_fk = AttributeConfig(
            owner_key=self.attribute_owner_key(assoc_cls),
            name=self.validate_unique(assoc_cls, src_fk_name),
            description=f"Join FK to {analysis.source_class.name}",
            is_public=False,
            is_required=True,
            is_unique=False,
            is_virtual=False,
            type_descriptor=self.build_uuid_primitive_descriptor(code_primitive_type),
        )
        self.attach_attribute(assoc_cls, src_fk)
        analysis.relationship.class_config_relationship_attributes.append(
            ClassConfigRelationshipAttribute(
                id=stable_class_relationship_attribute_id(
                    relationship_id=analysis.relationship.id,
                    attribute_config_id=src_fk.id,
                    direction=ClassConfigRelationshipDirection.forward.value,
                    role=ClassConfigRelationshipAttributeRole.foreign_key.value,
                ),
                class_config_relationship_id=analysis.relationship.id,
                attribute_config_id=src_fk.id,
                direction=ClassConfigRelationshipDirection.forward,
                role=ClassConfigRelationshipAttributeRole.foreign_key,
            )
        )

        assoc_edge = analysis.relationship.class_config_relationship_association_edge
        assoc_target_strategy = None
        if assoc_edge is not None:
            assoc_target_strategy = assoc_edge.reverse_loading_strategy or assoc_edge.forward_loading_strategy
        tgt_fk_is_required = assoc_target_strategy != ClassConfigRelationshipSideLoadingStrategy.eager

        tgt_fk = AttributeConfig(
            owner_key=self.attribute_owner_key(assoc_cls),
            name=self.validate_unique(assoc_cls, tgt_fk_name),
            description=f"Join FK to {analysis.target_class.name}",
            is_public=False,
            is_required=tgt_fk_is_required,
            is_unique=False,
            is_virtual=False,
            type_descriptor=self.build_uuid_primitive_descriptor(code_primitive_type),
        )
        self.attach_attribute(assoc_cls, tgt_fk)
        analysis.relationship.class_config_relationship_attributes.append(
            ClassConfigRelationshipAttribute(
                id=stable_class_relationship_attribute_id(
                    relationship_id=analysis.relationship.id,
                    attribute_config_id=tgt_fk.id,
                    direction=ClassConfigRelationshipDirection.reverse.value,
                    role=ClassConfigRelationshipAttributeRole.foreign_key.value,
                ),
                class_config_relationship_id=analysis.relationship.id,
                attribute_config_id=tgt_fk.id,
                direction=ClassConfigRelationshipDirection.reverse,
                role=ClassConfigRelationshipAttributeRole.foreign_key,
            )
        )
        return src_fk.id, tgt_fk.id

    def _mark_association_foreign_key_identity_from_constructors(
        self,
        analysis: ObjectConfigGraphRelationshipAnalysis,
        *,
        source_fk_id: UUID,
        target_fk_id: UUID,
    ) -> None:
        assoc_cls = analysis.association_class
        if assoc_cls is None:
            return

        fk_attr_id_by_name: dict[str, UUID] = {}
        for link in assoc_cls.class_config_attribute_configs:
            attr = link.attribute_config
            if attr.id not in {source_fk_id, target_fk_id}:
                continue
            fk_attr_id_by_name[attr.name] = attr.id

        if not fk_attr_id_by_name:
            return

        for fn_link in assoc_cls.class_config_function_configs:
            fn = fn_link.function_config
            if not fn_link.is_constructor:
                continue
            for edge in fn.function_config_attribute_configs:
                if edge.type != FunctionAttributeType.input:
                    continue
                if not (bool(edge.is_identity_key) or bool(edge.attribute_config.is_primary)):
                    continue
                fk_attr_id = fk_attr_id_by_name.get(edge.attribute_config.name)
                if fk_attr_id is not None:
                    self.mark_class_attribute_identity_key(
                        cls=assoc_cls,
                        attribute_config_id=fk_attr_id,
                    )

    def _materialize_edge_helper_attribute(self, analysis: ObjectConfigGraphRelationshipAnalysis) -> None:
        assoc = analysis.association_class
        if assoc is None:
            return
        src = analysis.source_class

        base = to_snake_case(assoc.name)
        if analysis.forward_is_list:
            name = pluralize(base)
            collection = AttributeCollectionType.list
        else:
            name = base
            collection = AttributeCollectionType.single

        existing = {acc.attribute_config.name for acc in src.class_config_attribute_configs if acc.attribute_config}
        if name in existing:
            suffix = "_edges" if analysis.forward_is_list else "_edge"
            name = f"{name}{suffix}"

        name = self.validate_unique(src, name)
        attr = AttributeConfig(
            owner_key=self.attribute_owner_key(src),
            name=name,
            description=f"Edge association helper for {analysis.forward_reference_attr.name}",
            is_public=True,
            is_required=False,
            exclude_serialization=(
                (analysis.relationship.forward_loading_strategy or ClassConfigRelationshipSideLoadingStrategy.lazy)
                == ClassConfigRelationshipSideLoadingStrategy.lazy
            ),
            is_unique=False,
            is_virtual=False,
            type_descriptor=self._build_class_descriptor(assoc, collection),
        )
        self.attach_attribute(src, attr)

        analysis.relationship.class_config_relationship_attributes.append(
            ClassConfigRelationshipAttribute(
                id=stable_class_relationship_attribute_id(
                    relationship_id=analysis.relationship.id,
                    attribute_config_id=attr.id,
                    direction=ClassConfigRelationshipDirection.forward.value,
                    role=ClassConfigRelationshipAttributeRole.auxiliary.value,
                ),
                class_config_relationship_id=analysis.relationship.id,
                attribute_config_id=attr.id,
                direction=ClassConfigRelationshipDirection.forward,
                role=ClassConfigRelationshipAttributeRole.auxiliary,
            )
        )

    def _association_member_role_name(
        self,
        analysis: ObjectConfigGraphRelationshipAnalysis,
        *,
        rel_name_overrides_by_key: dict[FkOverrideKey, str],
    ) -> str:
        key = FkOverrideKey(
            fqn_prefix=(analysis.source_namespace.package if analysis.source_namespace else None),
            namespace=(analysis.source_namespace.namespace if analysis.source_namespace else None),
            class_name=analysis.source_class.name,
            attribute_name=analysis.forward_reference_attr.name,
            edge_name=(analysis.association_class.name if analysis.association_class is not None else None),
        )
        override = rel_name_overrides_by_key.get(key)
        if override is None:
            fallback_key = FkOverrideKey(
                fqn_prefix=None,
                namespace=None,
                class_name=key.class_name,
                attribute_name=key.attribute_name,
                edge_name=key.edge_name,
            )
            override = rel_name_overrides_by_key.get(fallback_key)
        if override:
            return to_snake_case(override)
        if analysis.source_class.id == analysis.target_class.id:
            base = singularize(analysis.forward_reference_attr.name) or analysis.forward_reference_attr.name
            return to_snake_case(base)
        return to_snake_case(analysis.target_class.name)

    def _reified_association_target_relationship_type(
        self,
        analysis: ObjectConfigGraphRelationshipAnalysis,
    ) -> ClassConfigRelationshipType:
        """Preserve authored target reuse semantics on Edge -> Target runtime rails."""

        return (
            ClassConfigRelationshipType.one_to_one
            if analysis.relationship.relationship_type
            in {
                ClassConfigRelationshipType.one_to_one,
                ClassConfigRelationshipType.one_to_many,
            }
            else ClassConfigRelationshipType.many_to_one
        )

    def _ensure_association_target_reference(
        self,
        analysis: ObjectConfigGraphRelationshipAnalysis,
        *,
        rel_name_overrides_by_key: dict[FkOverrideKey, str],
    ) -> None:
        assoc_cls = analysis.association_class
        if assoc_cls is None:
            return

        target = analysis.target_class
        base_name = self._association_member_role_name(
            analysis,
            rel_name_overrides_by_key=rel_name_overrides_by_key,
        )
        if any(
            acc.attribute_config and acc.attribute_config.name == base_name
            for acc in assoc_cls.class_config_attribute_configs
        ):
            return
        name = self.validate_unique(assoc_cls, base_name)

        assoc_edge = analysis.relationship.class_config_relationship_association_edge
        assoc_target_strategy = None
        if assoc_edge is not None:
            assoc_target_strategy = assoc_edge.reverse_loading_strategy or assoc_edge.forward_loading_strategy
        is_lazy = (
            assoc_target_strategy or ClassConfigRelationshipSideLoadingStrategy.lazy
        ) == ClassConfigRelationshipSideLoadingStrategy.lazy

        attr = AttributeConfig(
            owner_key=self.attribute_owner_key(assoc_cls),
            name=name,
            description=f"Association target reference to {target.name}",
            is_public=True,
            is_required=not is_lazy,
            exclude_serialization=is_lazy,
            is_unique=self._reified_association_target_relationship_type(analysis)
            == ClassConfigRelationshipType.one_to_one,
            is_virtual=False,
            type_descriptor=self._build_class_descriptor(target, AttributeCollectionType.single),
        )
        if is_lazy:
            attr.default_value = self.primitive_codec.to_literal_string(None)
        self.attach_attribute(assoc_cls, attr)
        analysis.relationship.class_config_relationship_attributes.append(
            ClassConfigRelationshipAttribute(
                id=stable_class_relationship_attribute_id(
                    relationship_id=analysis.relationship.id,
                    attribute_config_id=attr.id,
                    direction=ClassConfigRelationshipDirection.reverse.value,
                    role=ClassConfigRelationshipAttributeRole.auxiliary.value,
                ),
                class_config_relationship_id=analysis.relationship.id,
                attribute_config_id=attr.id,
                direction=ClassConfigRelationshipDirection.reverse,
                role=ClassConfigRelationshipAttributeRole.auxiliary,
            )
        )

    def _next_attribute_position(self, cls: ClassConfig) -> int:
        positions = [acc.position for acc in cls.class_config_attribute_configs]
        return (max(positions) + 1) if positions else len(cls.class_config_attribute_configs)

    def _assert_name_available(self, cls: ClassConfig, name: str) -> None:
        existing = {acc.attribute_config.name for acc in cls.class_config_attribute_configs if acc.attribute_config}
        if name in existing:
            raise ValueError(f"Override name {name!r} already exists on class {cls.name}")

    def _build_class_descriptor(
        self,
        target: ClassConfig,
        collection: AttributeCollectionType,
    ) -> AttributeTypeDescriptor:
        class_node = AttributeTypeDescriptor(
            kind=AttributeTypeDescriptorKind.class_,
            class_config=target,
            class_config_id=target.id,
        )
        if collection == AttributeCollectionType.single:
            return ensure_stable_descriptor_tree_ids(class_node)
        collection_node = AttributeTypeDescriptor(
            kind=AttributeTypeDescriptorKind.collection,
            collection_kind=collection,
        )
        link = AttributeTypeDescriptorLink(
            attribute_type_descriptor_id=collection_node.id,
            child=class_node,
            child_id=class_node.id,
            role=AttributeTypeDescriptorRole.element,
            position=0,
        )
        collection_node.child_links.append(link)
        return ensure_stable_descriptor_tree_ids(collection_node)


__all__ = ["RuntimeTransformSupport"]
