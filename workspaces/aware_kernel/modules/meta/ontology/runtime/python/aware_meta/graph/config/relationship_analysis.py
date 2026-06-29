"""OCG Relationship Analysis (class-first, deterministic).

This module exists to support transformers (e.g. OOP projection) that need to
materialize representation attributes (foreign keys, reverse views, edge helpers).

Important:
- No ObjectConfig SSOT concepts.
- No table_schema/table_name.
- No "invert" heuristics.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_relationship import (
    ObjectConfigGraphRelationship,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_annotation_enums import (
    ObjectConfigGraphAnnotationKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassIdentityMode
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipIdentityRail,
    ClassConfigRelationshipSideLoadingStrategy,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_invocation_enums import FunctionInvocationKind
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.annotation.code_section_annotation_override_enums import (
    CodeSectionAnnotationOverrideTarget,
)

# Meta Runtime
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.model_bootstrap import (
    get_object_config_graph_node_class_config_id,
)

from aware_meta.graph.config.stable_ids import ocg_stable_uuid
from aware_meta.class_.config.relationship_side_loading_config import (
    ClassConfigRelationshipSideLoadingConfig,
    ClassConfigRelationshipSideLoadingOverrides,
)

# Aware Utils
from aware_utils.logging import logger
from aware_utils.string_transform import to_snake_case


@dataclass(frozen=True, slots=True)
class ObjectConfigGraphRelationshipAnalysis:
    """Convenience bundle describing FK ownership + association needs for a ClassConfigRelationship."""

    relationship: ClassConfigRelationship
    relationship_type: ClassConfigRelationshipType
    identity_rail: ClassConfigRelationshipIdentityRail

    source_class: ClassConfig
    target_class: ClassConfig
    association_class: ClassConfig | None
    construct_target_class: ClassConfig | None
    construct_target_is_association: bool

    # Canonical anchor attribute (FORWARD+REFERENCE).
    forward_reference_attr: AttributeConfig
    # Declared relationship requiredness (schema truth) captured at analysis time.
    #
    # Transformers are allowed to mutate `forward_reference_attr.is_required` to express
    # representation semantics (e.g., load/serialization behavior). FK requiredness logic must
    # therefore depend on this stable relationship value, not the potentially mutated AttributeConfig field.
    forward_required: bool

    # Optional non-canonical representations (may be added by transformers).
    reverse_reference_attr: AttributeConfig | None

    forward_is_list: bool
    reverse_is_list: bool

    requires_join_table: bool
    fk_owner_side: ClassConfigRelationshipDirection | None
    fk_owner_class: ClassConfig | None
    fk_target_class: ClassConfig | None
    fk_column_name: str | None

    # For override resolution (no table_*; namespace comes from graph mapping)
    source_namespace: NamespacePath | None


@dataclass(frozen=True, slots=True)
class FkOverrideKey:
    """Deterministic key for resolving FK overrides for a relationship.

    Matches the compiler output (namespace + class/member identity).
    """

    fqn_prefix: str | None
    namespace: str | None
    class_name: str
    attribute_name: str
    edge_name: str | None


@dataclass(frozen=True, slots=True)
class FkOverrideSpec:
    """FK override directives derived from `ann ... override fk ...`."""

    nullable: bool
    name: str | None


def _class_identity_mode(*, cls: ClassConfig) -> ClassIdentityMode:
    raw_mode = getattr(cls, "identity_mode", None)
    if isinstance(raw_mode, ClassIdentityMode):
        return raw_mode
    raw_value = getattr(raw_mode, "value", raw_mode)
    token = str(raw_value or "").strip().casefold()
    if token == ClassIdentityMode.standalone.value:
        return ClassIdentityMode.standalone
    return ClassIdentityMode.contained


@dataclass(frozen=True, slots=True)
class FkMaterializationPlan:
    """Derived FK plan for a relationship (post override resolution).

    This is a pure, reusable representation for transformers (OOP/SQL/etc) to
    materialize FKs without duplicating requiredness + override logic.
    """

    owner_side: ClassConfigRelationshipDirection
    owner_class: ClassConfig
    target_class: ClassConfig
    name: str
    name_is_override: bool
    # Runtime/input semantics for generated Python models.
    runtime_required: bool
    # DB semantics for SQL/materializers (NOT derived from loading strategy).
    db_required: bool
    unique: bool


@dataclass(frozen=True, slots=True)
class ObjectConfigGraphAnalysisBundle:
    """
    ObjectConfigGraph analysis bundle.

    This bundle is computed once on the ObjectConfigGraph (after annotation compilation + load/override resolution),
    then passed through the pipeline so Runtime->Language transformers do NOT need to re-derive rules
    such as DB nullability vs runtime requiredness.
    """

    analyses_by_relationship_id: dict[UUID, ObjectConfigGraphRelationshipAnalysis]
    # Non-join FK materialization facts (relationship_id -> ...)
    non_join_fk_owner_class_id_by_relationship_id: dict[UUID, UUID]
    non_join_fk_db_required_by_relationship_id: dict[UUID, bool]
    non_join_fk_runtime_required_by_relationship_id: dict[UUID, bool]
    # Association/join-table relationships (relationship_id -> association_class_id)
    association_class_id_by_relationship_id: dict[UUID, UUID]


def build_object_config_graph_analysis_bundle(
    graph: ObjectConfigGraph,
    *,
    namespace_by_code_id: dict[UUID, NamespacePath] | None = None,
    external_graphs_by_id: dict[UUID, ObjectConfigGraph] | None = None,
) -> ObjectConfigGraphAnalysisBundle:
    """
    Build the ObjectConfigGraph analysis bundle for a graph.

    Requirements:
    - Must run on the ObjectConfigGraph (before runtime synthesis mutates representation fields).
    - MUST NOT depend on runtime-only semantics for DB truth.
    """
    overrides_by_key = index_fk_override_annotations(graph)
    analyses = analyze_relationships(
        graph,
        namespace_by_code_id=namespace_by_code_id,
        external_graphs_by_id=external_graphs_by_id,
    )

    analyses_by_relationship_id: dict[UUID, ObjectConfigGraphRelationshipAnalysis] = {
        a.relationship.id: a for a in analyses
    }
    non_join_fk_owner_class_id_by_relationship_id: dict[UUID, UUID] = {}
    non_join_fk_db_required_by_relationship_id: dict[UUID, bool] = {}
    non_join_fk_runtime_required_by_relationship_id: dict[UUID, bool] = {}
    association_class_id_by_relationship_id: dict[UUID, UUID] = {}

    for a in analyses:
        rel_id = a.relationship.id
        if a.association_class is not None:
            # Association edges are reified at runtime into two relationships:
            #   source -> association_class
            #   association_class -> target
            #
            # Runtime->language transformers (e.g. SQL) operate on the runtime relationship ids,
            # so the analysis bundle must recognize both the canonical relationship id *and*
            # the stable reified relationship ids.
            assoc_id = a.association_class.id
            association_class_id_by_relationship_id[rel_id] = assoc_id
            association_class_id_by_relationship_id[
                stable_reified_association_source_relationship_id(relationship_id=rel_id)
            ] = assoc_id
            association_class_id_by_relationship_id[
                stable_reified_association_target_relationship_id(relationship_id=rel_id)
            ] = assoc_id
            continue

        # Non-join FK facts only when the analysis indicates a concrete FK owner/target.
        if a.fk_owner_class is None or a.fk_owner_side is None:
            continue
        if a.fk_target_class is None or a.fk_column_name is None:
            continue

        runtime_required = fk_runtime_requiredness_from_relationship_semantics(a)
        db_required = fk_db_requiredness_from_relationship_semantics(a)
        override = resolve_fk_override(a, overrides_by_key=overrides_by_key)
        if override is not None and override.nullable:
            runtime_required = False
            db_required = False

        non_join_fk_owner_class_id_by_relationship_id[rel_id] = a.fk_owner_class.id
        non_join_fk_db_required_by_relationship_id[rel_id] = db_required
        non_join_fk_runtime_required_by_relationship_id[rel_id] = runtime_required

    return ObjectConfigGraphAnalysisBundle(
        analyses_by_relationship_id=analyses_by_relationship_id,
        non_join_fk_owner_class_id_by_relationship_id=non_join_fk_owner_class_id_by_relationship_id,
        non_join_fk_db_required_by_relationship_id=non_join_fk_db_required_by_relationship_id,
        non_join_fk_runtime_required_by_relationship_id=non_join_fk_runtime_required_by_relationship_id,
        association_class_id_by_relationship_id=association_class_id_by_relationship_id,
    )


def index_fk_override_annotations(
    graph: ObjectConfigGraph,
) -> dict[FkOverrideKey, FkOverrideSpec]:
    """Index `override fk` compiled annotations into a typed lookup table."""
    by_key: dict[FkOverrideKey, FkOverrideSpec] = {}

    for a in graph.object_config_graph_annotations:
        if a.kind != ObjectConfigGraphAnnotationKind.override:
            continue
        ov = a.code_section_annotation_override
        if ov is None:
            continue
        if ov.target != CodeSectionAnnotationOverrideTarget.fk:
            continue

        key = FkOverrideKey(
            fqn_prefix=ov.fqn_prefix,
            namespace=_annotation_namespace(ov),
            class_name=ov.class_name,
            attribute_name=ov.attribute_name,
            edge_name=ov.edge_name,
        )
        by_key[key] = FkOverrideSpec(nullable=bool(ov.nullable), name=ov.name)

    return by_key


def index_relationship_name_override_annotations(
    graph: ObjectConfigGraph,
) -> dict[FkOverrideKey, str]:
    """
    Index `override relationship name ...` compiled annotations into a typed lookup table.

    Primary use-case: association (edge container) self-relationships where default
    endpoint naming would collide (e.g., CodePrimitiveType -> CodePrimitiveType).
    """
    by_key: dict[FkOverrideKey, str] = {}

    for a in graph.object_config_graph_annotations:
        if a.kind != ObjectConfigGraphAnnotationKind.override:
            continue
        ov = a.code_section_annotation_override
        if ov is None:
            continue
        if ov.target != CodeSectionAnnotationOverrideTarget.relationship:
            continue
        if not ov.name:
            continue

        key = FkOverrideKey(
            fqn_prefix=ov.fqn_prefix,
            namespace=_annotation_namespace(ov),
            class_name=ov.class_name,
            attribute_name=ov.attribute_name,
            edge_name=ov.edge_name,
        )
        by_key[key] = ov.name

    return by_key


def _annotation_namespace(annotation: object) -> str:
    namespace = getattr(annotation, "namespace", None)
    if not isinstance(namespace, str):
        raise ValueError("Annotation relationship analysis requires namespace")
    return namespace.strip()


def fk_override_key_for_analysis(
    analysis: ObjectConfigGraphRelationshipAnalysis,
) -> FkOverrideKey:
    ns = analysis.source_namespace
    edge_name = analysis.association_class.name if analysis.association_class is not None else None
    return FkOverrideKey(
        fqn_prefix=(ns.package if ns is not None else None),
        namespace=(ns.namespace if ns is not None else None),
        class_name=analysis.source_class.name,
        attribute_name=analysis.forward_reference_attr.name,
        edge_name=edge_name,
    )


def resolve_fk_override(
    analysis: ObjectConfigGraphRelationshipAnalysis,
    *,
    overrides_by_key: dict[FkOverrideKey, FkOverrideSpec],
) -> FkOverrideSpec | None:
    """Resolve FK override by analysis, with a namespace-less fallback for tests/callers."""
    key = fk_override_key_for_analysis(analysis)
    hit = overrides_by_key.get(key)
    if hit is not None:
        return hit
    fallback_key = FkOverrideKey(
        fqn_prefix=None,
        namespace=None,
        class_name=key.class_name,
        attribute_name=key.attribute_name,
        edge_name=key.edge_name,
    )
    hit = overrides_by_key.get(fallback_key)
    if hit is not None:
        return hit

    # Final fallback for contexts that cannot resolve source namespace metadata
    # (for example SQL lowering from runtime-only OCGs): match by structural key.
    matches = [
        spec
        for candidate_key, spec in overrides_by_key.items()
        if candidate_key.class_name == key.class_name
        and candidate_key.attribute_name == key.attribute_name
        and candidate_key.edge_name == key.edge_name
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        logger.warning(
            "Ambiguous FK override match for class=%s attribute=%s edge=%s; skipping namespace-less fallback",
            key.class_name,
            key.attribute_name,
            key.edge_name,
        )
    return None


def fk_runtime_requiredness_from_relationship_semantics(
    analysis: ObjectConfigGraphRelationshipAnalysis,
) -> bool:
    """
    Canonical FK *runtime* requiredness rule:
    - Runtime requiredness models language serialization ergonomics.
    - EAGER pointer loading keeps FK optional in generated language models
      (both forward-owned and reverse-owned FK sides).
    - Otherwise, requiredness follows declared relationship truth (`forward_required`).
    - Join-table/association FKs are handled separately.

    Note: this only applies to non-join FKs materialized onto a class.
    """
    if analysis.fk_owner_side is None:
        return False

    if analysis.fk_owner_side == ClassConfigRelationshipDirection.forward:
        strategy = analysis.relationship.forward_loading_strategy or ClassConfigRelationshipSideLoadingStrategy.lazy
    else:
        strategy = analysis.relationship.reverse_loading_strategy or ClassConfigRelationshipSideLoadingStrategy.lazy

    if strategy == ClassConfigRelationshipSideLoadingStrategy.eager:
        return False
    return bool(analysis.forward_required)


def fk_db_requiredness_from_relationship_semantics(
    analysis: ObjectConfigGraphRelationshipAnalysis,
) -> bool:
    """
    DB FK nullability rule (schema truth).

    Important:
    - MUST NOT depend on loading strategy.
    - Based on declared relationship optionality + relationship type.

    Canonical rule set:
    - Non-join FK requiredness is owned by declared relationship requiredness
      (`relationship.forward_required`) regardless of owner side.
    - Owner side determines where FK lives, not whether it is required.

    Note: join-table FKs are handled separately on the association class.
    """
    if analysis.fk_owner_side is None:
        return False
    return bool(analysis.forward_required)


def compute_fk_materialization_plan(
    analysis: ObjectConfigGraphRelationshipAnalysis,
    *,
    overrides_by_key: dict[FkOverrideKey, FkOverrideSpec],
    validate_unique: Callable[[ClassConfig, str], str],
) -> FkMaterializationPlan | None:
    """
    Compute an FK materialization plan for a relationship analysis.

    - Returns None when the relationship does not materialize a non-join FK.
    - Applies SSOT requiredness rules + deterministic override resolution.
    - Validates no naming collision via `validate_unique(cls, base) -> str`.
    """
    if analysis.fk_owner_class is None or analysis.fk_column_name is None or analysis.fk_owner_side is None:
        return None
    if analysis.fk_target_class is None:
        # Non-join FK plans always have a target class (join-table FKs handled elsewhere).
        return None

    runtime_required = fk_runtime_requiredness_from_relationship_semantics(analysis)
    db_required = fk_db_requiredness_from_relationship_semantics(analysis)
    override = resolve_fk_override(analysis, overrides_by_key=overrides_by_key)
    if override is not None and override.nullable:
        runtime_required = False
        db_required = False

    if override is not None and override.name is not None:
        name_is_override = True
        name = override.name
    else:
        name_is_override = False
        name = validate_unique(analysis.fk_owner_class, analysis.fk_column_name)

    # Ensure deterministic uniqueness policy for ONE_TO_ONE.
    unique = analysis.relationship_type == ClassConfigRelationshipType.one_to_one

    return FkMaterializationPlan(
        owner_side=analysis.fk_owner_side,
        owner_class=analysis.fk_owner_class,
        target_class=analysis.fk_target_class,
        name=name,
        name_is_override=name_is_override,
        runtime_required=runtime_required,
        db_required=db_required,
        unique=unique,
    )


def _collect_construct_target_class_ids_by_relationship_id(
    graph: ObjectConfigGraph,
    *,
    external_graphs_by_id: dict[UUID, ObjectConfigGraph] | None = None,
) -> dict[UUID, frozenset[UUID]]:
    """Collect constructed class ids per relationship for construct traversal propagation.

    The authored relationship id still names the rail, but the constructed class is resolved
    from the invoked constructor owner. That lets analysis distinguish:
    - source -> target containment, and
    - source -> association-edge containment for `A::rel Target @Edge`.
    """

    class_by_id: dict[UUID, ClassConfig] = {}
    function_configs: list[FunctionConfig] = []
    function_by_id: dict[UUID, FunctionConfig] = {}
    function_owner_class_id_by_id: dict[UUID, UUID] = {}
    relevant_relationship_ids: set[UUID] = set()
    seen_function_ids: set[UUID] = set()

    def _register_graph_functions(source_graph: ObjectConfigGraph) -> None:
        for node in source_graph.object_config_graph_nodes:
            if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
                continue
            cls = node.class_config
            class_by_id[cls.id] = node.class_config
            for link in cls.class_config_function_configs:
                fn = link.function_config
                if fn.id in seen_function_ids:
                    continue
                function_configs.append(fn)
                function_by_id[fn.id] = fn
                function_owner_class_id_by_id[fn.id] = cls.id
                seen_function_ids.add(fn.id)

    _register_graph_functions(graph)
    for node in graph.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.relationship or node.class_config_relationship is None:
            continue
        relevant_relationship_ids.add(node.class_config_relationship.id)

    for ocg_rel in graph.object_config_graph_relationships:
        target_graph = _relationship_target_graph(
            ocg_rel,
            external_graphs_by_id=external_graphs_by_id,
        )
        for rel in ocg_rel.class_config_relationships:
            relevant_relationship_ids.add(rel.id)
        if target_graph is None:
            continue
        _register_graph_functions(target_graph)

    relationship_target_class_ids: dict[UUID, set[UUID]] = {}
    for fn in function_configs:
        for invocation in fn.invocations:
            if invocation.kind.value.strip().lower() != FunctionInvocationKind.construct.value:
                continue
            relationship_id = invocation.class_config_relationship_id
            if relationship_id is None and invocation.class_config_relationship is not None:
                relationship_id = invocation.class_config_relationship.id
            if relationship_id is None:
                continue
            if relationship_id not in relevant_relationship_ids:
                continue
            target_function = invocation.target_function_config
            if target_function is None:
                target_function = function_by_id.get(invocation.target_function_config_id)
            if target_function is None:
                source_function_ref = f"{fn.name}"
                function_owner_class_id = function_owner_class_id_by_id.get(fn.id)
                if function_owner_class_id:
                    class_owner = class_by_id.get(function_owner_class_id)
                    if class_owner:
                        source_function_ref = f"{class_owner.name}.{source_function_ref}"
                raise ValueError(
                    "Source function: "
                    f"{source_function_ref} construct propagation target function is missing from graph "
                    + f"(relationship_id={relationship_id}, invocation_id={invocation.id})"
                )
            target_owner_class_id = function_owner_class_id_by_id.get(target_function.id)
            if target_owner_class_id is None:
                raise ValueError(
                    "construct propagation target function is not owned by a class "
                    + f"(relationship_id={relationship_id}, function_id={target_function.id}, "
                    + f"function_name={target_function.name!r})"
                )
            relationship_target_class_ids.setdefault(relationship_id, set()).add(target_owner_class_id)
    return {
        relationship_id: frozenset(class_ids) for relationship_id, class_ids in relationship_target_class_ids.items()
    }


def analyze_relationships(
    graph: ObjectConfigGraph,
    *,
    namespace_by_code_id: dict[UUID, NamespacePath] | None = None,
    external_graphs_by_id: dict[UUID, ObjectConfigGraph] | None = None,
) -> list[ObjectConfigGraphRelationshipAnalysis]:
    """Compute RelationshipAnalysis entries for every relationship in the graph.

    Includes:
    - local relationship nodes (ObjectConfigGraphNodeType.relationship)
    - cross-OCG relationships materialized via `ObjectConfigGraph.object_config_graph_relationships`
      (source->external target). These are required so runtime synthesis can materialize
    association/join-table semantics even when the target class lives in an external package.
    """
    class_by_id: dict[UUID, ClassConfig] = {}
    attr_by_id: dict[UUID, AttributeConfig] = {}

    namespace_by_class_config_id: dict[UUID, NamespacePath] = {}

    for node in graph.object_config_graph_nodes:
        if node.type == ObjectConfigGraphNodeType.class_ and node.class_config is not None:
            cls = node.class_config
            class_by_id[cls.id] = cls
            namespace = _namespace_from_class_fqn(
                fqn_prefix=graph.fqn_prefix,
                class_fqn=cls.class_fqn,
            )
            if namespace is not None:
                namespace_by_class_config_id[cls.id] = NamespacePath(
                    package=graph.fqn_prefix,
                    namespace=namespace,
                )
            for link in cls.class_config_attribute_configs:
                attr_by_id[link.attribute_config.id] = link.attribute_config

    # Include external class configs (for cross-OCG relationship analysis).
    for ocg_rel in graph.object_config_graph_relationships:
        tgt = _relationship_target_graph(
            ocg_rel,
            external_graphs_by_id=external_graphs_by_id,
        )
        if tgt is None:
            continue
        for n in tgt.object_config_graph_nodes:
            if n.type != ObjectConfigGraphNodeType.class_ or n.class_config is None:
                continue
            cls = n.class_config
            _ = class_by_id.setdefault(cls.id, cls)
            for link in cls.class_config_attribute_configs:
                _ = attr_by_id.setdefault(link.attribute_config.id, link.attribute_config)

    construct_target_class_ids_by_relationship_id = _collect_construct_target_class_ids_by_relationship_id(
        graph,
        external_graphs_by_id=external_graphs_by_id,
    )

    analyses: list[ObjectConfigGraphRelationshipAnalysis] = []
    seen_relationship_ids: set[UUID] = set()
    # Local relationship nodes
    for node in graph.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.relationship or node.class_config_relationship is None:
            continue
        analysis = _analyze_relationship(
            node.class_config_relationship,
            class_by_id,
            attr_by_id,
            construct_target_class_ids_by_relationship_id=construct_target_class_ids_by_relationship_id,
            namespace_by_code_id=namespace_by_code_id,
            namespace_by_class_config_id=namespace_by_class_config_id,
        )
        if analysis is not None:
            analyses.append(analysis)
            seen_relationship_ids.add(analysis.relationship.id)

    # Cross-OCG relationships (detached on relationship objects; not nodes)
    for ocg_rel in graph.object_config_graph_relationships:
        for rel in ocg_rel.class_config_relationships:
            # If a relationship is already materialized as a RELATIONSHIP node in this graph
            # (canonical SSOT for projections/annotations), do not analyze it twice.
            if rel.id in seen_relationship_ids:
                continue
            analysis = _analyze_relationship(
                rel,
                class_by_id,
                attr_by_id,
                construct_target_class_ids_by_relationship_id=construct_target_class_ids_by_relationship_id,
                namespace_by_code_id=namespace_by_code_id,
                namespace_by_class_config_id=namespace_by_class_config_id,
            )
            if analysis is not None:
                analyses.append(analysis)
    # Deterministic ordering so downstream transformers (FK + reverse view synthesis) are stable.
    analyses.sort(
        key=lambda a: (
            str(a.relationship.id),
            str(a.source_class.id),
            str(a.target_class.id),
        )
    )
    return analyses


def _relationship_target_graph(
    ocg_rel: ObjectConfigGraphRelationship,
    *,
    external_graphs_by_id: dict[UUID, ObjectConfigGraph] | None,
) -> ObjectConfigGraph | None:
    if external_graphs_by_id is not None:
        target_graph = external_graphs_by_id.get(ocg_rel.target_object_config_graph_id)
        if target_graph is not None:
            return target_graph
    return ocg_rel.target_object_config_graph


def stable_reified_association_source_relationship_id(*, relationship_id: UUID) -> UUID:
    """Stable id for the runtime relationship from source → association (edge) class.

    This is derived deterministically from the canonical relationship id so:
    - runtime IR topology is reproducible across builds
    - OPG edges can be translated from canonical ids without heuristics
    """

    return ocg_stable_uuid(f"runtime_rel:assoc_source:{relationship_id}")


def stable_reified_association_target_relationship_id(*, relationship_id: UUID) -> UUID:
    """Stable id for the runtime relationship from association (edge) class → target class."""

    return ocg_stable_uuid(f"runtime_rel:assoc_target:{relationship_id}")


def _analyze_relationship(
    relationship: ClassConfigRelationship,
    class_by_id: dict[UUID, ClassConfig],
    attr_by_id: dict[UUID, AttributeConfig],
    *,
    construct_target_class_ids_by_relationship_id: dict[UUID, frozenset[UUID]],
    namespace_by_code_id: dict[UUID, NamespacePath] | None,
    namespace_by_class_config_id: dict[UUID, NamespacePath],
) -> ObjectConfigGraphRelationshipAnalysis | None:
    source_class = class_by_id.get(relationship.class_config_id)
    target_class = class_by_id.get(relationship.target_class_config_id)
    if source_class is None or target_class is None:
        logger.warning(f"Source or target class missing for relationship {relationship.id}")
        return None

    association_class = None
    if relationship.class_config_relationship_association_edge is not None:
        assoc_id = relationship.class_config_relationship_association_edge.class_config_id
        association_class = class_by_id.get(assoc_id)

    forward_ref = _pick_relationship_attr(
        relationship,
        direction=ClassConfigRelationshipDirection.forward,
        role=ClassConfigRelationshipAttributeRole.reference,
    )
    if forward_ref is None:
        logger.warning(f"No FORWARD+REFERENCE attribute for relationship {relationship.id}")
        return None

    forward_reference_attr = attr_by_id.get(forward_ref.attribute_config_id)
    if forward_reference_attr is None:
        logger.warning(
            f"Forward reference AttributeConfig missing for relationship {relationship.id}: "
            + f"attribute_config_id={forward_ref.attribute_config_id}"
        )
        return None

    reverse_ref = _pick_relationship_attr(
        relationship,
        direction=ClassConfigRelationshipDirection.reverse,
        role=ClassConfigRelationshipAttributeRole.reference,
    )
    reverse_reference_attr = attr_by_id.get(reverse_ref.attribute_config_id) if reverse_ref else None

    forward_is_list = _attr_is_list(forward_reference_attr)
    reverse_is_list = _attr_is_list(reverse_reference_attr) if reverse_reference_attr else False

    # SSOT: if a relationship has an association (join-table / edge-container) class,
    # it requires a join table regardless of MANY_TO_MANY vs ONE_TO_MANY.
    requires_join_table = bool(association_class is not None) or (
        relationship.relationship_type == ClassConfigRelationshipType.many_to_many
    )

    construct_target_class: ClassConfig | None = None
    construct_target_is_association = False
    construct_target_is_standalone = False
    construct_target_class_ids = set(construct_target_class_ids_by_relationship_id.get(relationship.id, ()))
    if len(construct_target_class_ids) > 1:
        target_names = ", ".join(
            sorted(class_by_id[class_id].name for class_id in construct_target_class_ids if class_id in class_by_id)
        )
        raise ValueError(
            "construct propagation is ambiguous: relationship constructs multiple target classes "
            + f"(relationship_id={relationship.id}, classes=[{target_names}])"
        )
    if construct_target_class_ids:
        construct_target_class_id = next(iter(construct_target_class_ids))
        allowed_target_class_ids = {target_class.id}
        if association_class is not None:
            allowed_target_class_ids.add(association_class.id)
        if construct_target_class_id not in allowed_target_class_ids:
            target_name = (
                class_by_id[construct_target_class_id].name
                if construct_target_class_id in class_by_id
                else str(construct_target_class_id)
            )
            allowed_names = ", ".join(
                sorted(class_by_id[class_id].name for class_id in allowed_target_class_ids if class_id in class_by_id)
            )
            raise ValueError(
                "construct propagation target does not match authored relationship target rail "
                + f"(relationship_id={relationship.id}, constructed_class={target_name!r}, allowed=[{allowed_names}])"
            )
        construct_target_class = class_by_id.get(construct_target_class_id)
        if construct_target_class is None:
            raise ValueError(
                "construct propagation target class is missing from relationship analysis graph "
                + f"(relationship_id={relationship.id}, class_id={construct_target_class_id})"
            )
        construct_target_is_association = (
            association_class is not None and construct_target_class_id == association_class.id
        )
        construct_target_is_standalone = (
            _class_identity_mode(cls=construct_target_class) is ClassIdentityMode.standalone
        )

    has_construct_propagation = construct_target_class is not None and not construct_target_is_standalone
    relationship.identity_rail = (
        ClassConfigRelationshipIdentityRail.containment
        if has_construct_propagation
        else ClassConfigRelationshipIdentityRail.reference
    )

    if (
        has_construct_propagation
        and not construct_target_is_association
        and relationship.relationship_type
        in {
            ClassConfigRelationshipType.many_to_one,
            ClassConfigRelationshipType.many_to_many,
        }
    ):
        raise ValueError(
            "containment relationship cardinality is not allowed for propagation identity rails "
            + (
                f"(relationship_id={relationship.id}, "
                f"relationship_type={relationship.relationship_type.value!r}, "
                f"source_class={source_class.name!r}, "
                f"attribute={forward_reference_attr.name!r}, "
                f"target_class={target_class.name!r}). "
            )
            + "Containment rails must be one_to_one or one_to_many."
        )

    fk_owner_side: ClassConfigRelationshipDirection | None = None
    fk_owner_class: ClassConfig | None = None
    fk_target_class: ClassConfig | None = None
    fk_column_name: str | None = None

    if requires_join_table:
        # Join table semantics are handled by the association class when present.
        # Do not materialize non-join FKs onto source/target classes when an association exists.
        fk_owner_side = None
        fk_owner_class = association_class
        fk_target_class = None
        fk_column_name = None
    elif relationship.identity_rail == ClassConfigRelationshipIdentityRail.containment:
        # Containment rails always anchor parent identity on the child.
        # This includes one_to_one containment relationships.
        fk_owner_side = ClassConfigRelationshipDirection.reverse
        fk_owner_class = target_class
        fk_target_class = source_class
        fk_column_name = f"{to_snake_case(source_class.name)}_id"
    elif relationship.relationship_type in {
        ClassConfigRelationshipType.many_to_one,
        ClassConfigRelationshipType.one_to_one,
    }:
        fk_owner_side = ClassConfigRelationshipDirection.forward
        fk_owner_class = source_class
        fk_target_class = target_class
        fk_column_name = f"{forward_reference_attr.name}_id"
    elif relationship.relationship_type == ClassConfigRelationshipType.one_to_many:
        # Forward side is a list → FK lives on the target pointing back to the source.
        fk_owner_side = ClassConfigRelationshipDirection.reverse
        fk_owner_class = target_class
        fk_target_class = source_class
        fk_column_name = f"{to_snake_case(source_class.name)}_id"

    source_namespace = _namespace_for_class(
        source_class,
        namespace_by_code_id=namespace_by_code_id,
        namespace_by_class_config_id=namespace_by_class_config_id,
    )

    return ObjectConfigGraphRelationshipAnalysis(
        relationship=relationship,
        relationship_type=relationship.relationship_type,
        identity_rail=relationship.identity_rail,
        source_class=source_class,
        target_class=target_class,
        association_class=association_class,
        construct_target_class=construct_target_class,
        construct_target_is_association=construct_target_is_association,
        forward_reference_attr=forward_reference_attr,
        forward_required=bool(relationship.forward_required),
        reverse_reference_attr=reverse_reference_attr,
        forward_is_list=forward_is_list,
        reverse_is_list=reverse_is_list,
        requires_join_table=requires_join_table,
        fk_owner_side=fk_owner_side,
        fk_owner_class=fk_owner_class,
        fk_target_class=fk_target_class,
        fk_column_name=fk_column_name,
        source_namespace=source_namespace,
    )


def compute_relationship_side_loading_overrides(
    config: ClassConfigRelationshipSideLoadingConfig | None,
    analysis: ObjectConfigGraphRelationshipAnalysis,
) -> ClassConfigRelationshipSideLoadingOverrides:
    """Resolve override config using schema + (class, attribute) or (edge) keys.

    Note: this does not mutate the graph; transformers apply the overrides.
    """
    if config is None:
        return ClassConfigRelationshipSideLoadingOverrides()

    namespace = analysis.source_namespace.namespace if analysis.source_namespace else None
    forward_override = None
    reverse_override = None

    if analysis.association_class is not None:
        overrides = config.resolve_for_edge(namespace=namespace, edge_name=analysis.association_class.name)
        if overrides.forward is not None:
            forward_override = overrides.forward
        if overrides.reverse is not None:
            reverse_override = overrides.reverse

    # Canonical key: only the source attribute declares the relationship.
    overrides = config.resolve_for_attribute(
        namespace=namespace,
        class_name=analysis.source_class.name,
        attribute_name=analysis.forward_reference_attr.name,
    )
    if overrides.forward is not None:
        forward_override = overrides.forward
    if overrides.reverse is not None:
        reverse_override = overrides.reverse

    return ClassConfigRelationshipSideLoadingOverrides(forward=forward_override, reverse=reverse_override)


def _pick_relationship_attr(
    relationship: ClassConfigRelationship,
    *,
    direction: ClassConfigRelationshipDirection,
    role: ClassConfigRelationshipAttributeRole,
) -> ClassConfigRelationshipAttribute | None:
    matches = [
        a for a in relationship.class_config_relationship_attributes if a.direction == direction and a.role == role
    ]
    if not matches:
        return None
    if len(matches) > 1:
        # Canonical builder should avoid this; transformers should keep it stable.
        logger.warning(
            f"Multiple relationship attributes for {relationship.id} direction={direction} role={role}; "
            + "using the first deterministically"
        )
    return matches[0]


def _attr_is_list(attr: AttributeConfig) -> bool:
    # Canonical builder uses COLLECTION root for list relationships, but keep a defensive traversal.
    if attr.type_descriptor.kind == AttributeTypeDescriptorKind.collection:
        return True
    return False


def _namespace_for_class(
    cls: ClassConfig,
    *,
    namespace_by_code_id: dict[UUID, NamespacePath] | None,
    namespace_by_class_config_id: dict[UUID, NamespacePath],
) -> NamespacePath | None:
    ns = namespace_by_class_config_id.get(cls.id)
    if ns is not None:
        return ns
    cs = cls.code_section_class
    if cs is None:
        return None
    if namespace_by_code_id is None:
        return None
    code_id = cs.code_section.code_id
    return namespace_by_code_id.get(code_id)


def _namespace_from_class_fqn(*, fqn_prefix: str, class_fqn: str) -> str | None:
    parts = [part.strip() for part in class_fqn.split(".") if part.strip()]
    if len(parts) < 2 or parts[0] != fqn_prefix:
        return None
    return ".".join(parts[1:-1])


__all__ = [
    "FkOverrideKey",
    "FkOverrideSpec",
    "FkMaterializationPlan",
    "ObjectConfigGraphRelationshipAnalysis",
    "analyze_relationships",
    "compute_fk_materialization_plan",
    "compute_relationship_side_loading_overrides",
    "fk_override_key_for_analysis",
    "fk_db_requiredness_from_relationship_semantics",
    "fk_runtime_requiredness_from_relationship_semantics",
    "index_fk_override_annotations",
    "index_relationship_name_override_annotations",
    "resolve_fk_override",
]
