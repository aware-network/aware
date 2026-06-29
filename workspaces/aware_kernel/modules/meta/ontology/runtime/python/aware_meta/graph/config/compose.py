from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
import time
from typing import Any, Protocol, TypeVar
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta Ontology
from aware_meta_ontology.attribute.attribute_config_overlay import (
    AttributeConfigOverlay,
)
from aware_meta_ontology.class_.class_config_overlay import ClassConfigOverlay
from aware_meta_ontology.enum.enum_config_overlay import EnumConfigOverlay
from aware_meta_ontology.enum.enum_option_overlay import EnumOptionOverlay
from aware_meta_ontology.function.function_config_overlay import FunctionConfigOverlay
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_identity import (
    ObjectConfigGraphIdentity,
)
from aware_meta_ontology.graph.config.object_config_graph_overlay import (
    ObjectConfigGraphOverlay,
)
from aware_meta_ontology.graph.config.object_config_graph_relationship import (
    ObjectConfigGraphRelationship,
)
from aware_meta.graph.config.stable_ids import (
    stable_object_config_graph_identity_id,
)


TModel = TypeVar("TModel", bound=BaseModel)


class SeedTimings(Protocol):
    def add(self, name: str, duration_s: float) -> object: ...

    def metric(self, key: str, value: object) -> object: ...


@contextmanager
def maybe_timed(timings: SeedTimings | None, name: str) -> Iterator[None]:
    if timings is None:
        yield
        return
    start = time.perf_counter()
    try:
        yield
    finally:
        try:
            _ = timings.add(name, time.perf_counter() - start)
        except Exception:
            pass


def maybe_metric(timings: SeedTimings | None, key: str, value: object) -> None:
    if timings is None or not key:
        return
    try:
        _ = timings.metric(key, value)
    except Exception:
        pass


def _ensure_composite_ocg_identity(
    *, ocg: ObjectConfigGraph, source_ocgs: Sequence[ObjectConfigGraph]
) -> None:
    """Attach a deterministic OCGI to the composed OCG without mutating module OPGI identities.

    The composed environment is a container view over multiple module OCGs. Projection identities
    (OPGI) are owned by their source modules and must remain stable in the composed view.
    """

    ocg_key = (ocg.fqn_prefix or "").strip()
    if not ocg_key:
        raise ValueError("Composed OCG requires fqn_prefix to derive OCGI")

    ocgi_id = stable_object_config_graph_identity_id(key=ocg_key)
    ocgi = ocg.object_config_graph_identity
    if ocgi is None or ocgi.id != ocgi_id:
        ocgi = ObjectConfigGraphIdentity(
            id=ocgi_id, key=ocg_key, label=f"ocg:{ocg_key}"
        )
        ocg.object_config_graph_identity = ocgi

    projection_identities_by_graph_id: dict[UUID, Any] = {}
    for source_ocg in source_ocgs:
        source_ocgi = source_ocg.object_config_graph_identity
        if source_ocgi is None:
            continue
        for source_opgi in (
            getattr(source_ocgi, "object_projection_graph_identities", []) or []
        ):
            object_projection_graph_id = getattr(
                source_opgi, "object_projection_graph_id", None
            )
            if not isinstance(object_projection_graph_id, UUID):
                continue
            existing = projection_identities_by_graph_id.get(object_projection_graph_id)
            candidate = source_opgi.model_copy(deep=True)
            candidate.object_instance_graph_identities = []
            if existing is not None:
                existing_payload = _stable_projection_identity_payload(existing)
                candidate_payload = _stable_projection_identity_payload(candidate)
                if existing_payload != candidate_payload:
                    existing_base_payload = _projection_identity_base_payload(existing)
                    candidate_base_payload = _projection_identity_base_payload(
                        candidate
                    )
                    if existing_base_payload == candidate_base_payload:
                        existing_is_composite = _is_composite_projection_identity(
                            existing,
                            composite_object_config_graph_identity_id=ocgi_id,
                        )
                        candidate_is_composite = _is_composite_projection_identity(
                            candidate,
                            composite_object_config_graph_identity_id=ocgi_id,
                        )
                        if existing_is_composite and not candidate_is_composite:
                            projection_identities_by_graph_id[
                                object_projection_graph_id
                            ] = candidate
                            continue
                        if candidate_is_composite or existing_is_composite:
                            continue
                    existing_semantic_payload = _semantic_projection_identity_payload(
                        existing
                    )
                    candidate_semantic_payload = _semantic_projection_identity_payload(
                        candidate
                    )
                    if existing_semantic_payload == candidate_semantic_payload:
                        existing_is_composite = _is_composite_projection_identity(
                            existing,
                            composite_object_config_graph_identity_id=ocgi_id,
                        )
                        candidate_is_composite = _is_composite_projection_identity(
                            candidate,
                            composite_object_config_graph_identity_id=ocgi_id,
                        )
                        if existing_is_composite and not candidate_is_composite:
                            projection_identities_by_graph_id[
                                object_projection_graph_id
                            ] = candidate
                            continue
                        if candidate_is_composite or existing_is_composite:
                            continue
                    conflicting_fields = sorted(
                        key
                        for key in set(existing_payload) | set(candidate_payload)
                        if existing_payload.get(key) != candidate_payload.get(key)
                    )
                    raise ValueError(
                        "Conflicting object_projection_graph_identity entry "
                        + f"for object_projection_graph_id={object_projection_graph_id} "
                        + f"conflicting_fields={conflicting_fields}"
                    )
                continue
            projection_identities_by_graph_id[object_projection_graph_id] = candidate
    ocgi.object_projection_graph_identities = list(
        projection_identities_by_graph_id.values()
    )

    ocg.object_config_graph_identity_id = ocgi.id


def _stable_model_payload(
    model: BaseModel, *, exclude: set[str] | None = None
) -> Mapping[str, Any]:
    return model.model_dump(mode="python", exclude_none=True, exclude=exclude or set())


def _stable_projection_identity_payload(model: BaseModel) -> Mapping[str, Any]:
    """Compare only the compiler-owned OPGI descriptor, not runtime OIGI children."""

    return _stable_model_payload(
        model,
        exclude={"ObjectProjectionGraph", "object_instance_graph_identities"},
    )


def _projection_identity_base_payload(model: BaseModel) -> Mapping[str, Any]:
    """Compare the OPGI binding independent of owner scope and observable children."""

    return _stable_model_payload(
        model,
        exclude={
            "id",
            "object_config_graph_identity_id",
            "object_instance_graph_identities",
            "ObjectProjectionGraph",
            "object_projection_graph_observables",
        },
    )


def _semantic_projection_identity_payload(model: BaseModel) -> Mapping[str, Any]:
    payload = dict(_projection_identity_base_payload(model))
    observables = []
    for observable in getattr(model, "object_projection_graph_observables", []) or []:
        if not isinstance(observable, BaseModel):
            continue
        observables.append(
            _stable_model_payload(
                observable,
                exclude={"id", "object_projection_graph_identity_id"},
            )
        )
    payload["object_projection_graph_observables"] = sorted(observables, key=repr)
    return payload


def _is_composite_projection_identity(
    model: BaseModel,
    *,
    composite_object_config_graph_identity_id: UUID,
) -> bool:
    return (
        getattr(model, "object_config_graph_identity_id", None)
        == composite_object_config_graph_identity_id
    )


def _merge_models_by_id(items: Iterable[TModel], *, key: str) -> list[TModel]:
    merged: dict[UUID, TModel] = {}
    order: list[UUID] = []
    for item in items:
        item_id = getattr(item, "id", None)
        if not isinstance(item_id, UUID):
            raise ValueError(
                f"Cannot compose {key}: missing UUID id on {type(item).__name__}"
            )
        existing = merged.get(item_id)
        if existing is not None:
            if _stable_model_payload(existing) != _stable_model_payload(item):
                raise ValueError(f"Conflicting {key} entry id={item_id}")
            continue
        merged[item_id] = item
        order.append(item_id)
    return [merged[item_id] for item_id in order]


def _compose_timing_key(prefix: str, name: str) -> str:
    normalized_prefix = prefix.strip(".")
    return f"{normalized_prefix}.{name}" if normalized_prefix else name


def _record_compose_input_metrics(
    *,
    ocgs: Sequence[ObjectConfigGraph],
    timings: SeedTimings | None,
    timing_prefix: str,
) -> None:
    if timings is None:
        return
    metric_prefix = _compose_timing_key(timing_prefix, "input")
    node_counts = [len(ocg.object_config_graph_nodes) for ocg in ocgs]
    opg_counts = [len(ocg.object_projection_graphs) for ocg in ocgs]
    relationship_counts = [len(ocg.object_config_graph_relationships) for ocg in ocgs]

    maybe_metric(timings, f"{metric_prefix}_ocg_count", len(ocgs))
    maybe_metric(timings, f"{metric_prefix}_node_count", sum(node_counts))
    maybe_metric(
        timings, f"{metric_prefix}_node_count_max", max(node_counts, default=0)
    )
    maybe_metric(timings, f"{metric_prefix}_opg_count", sum(opg_counts))
    maybe_metric(timings, f"{metric_prefix}_opg_count_max", max(opg_counts, default=0))
    maybe_metric(
        timings,
        f"{metric_prefix}_relationship_count",
        sum(relationship_counts),
    )
    maybe_metric(
        timings,
        f"{metric_prefix}_relationship_count_max",
        max(relationship_counts, default=0),
    )


def _rebind_object_config_graph_id(
    items: Iterable[TModel], *, composite_ocg_id: UUID
) -> list[TModel]:
    """Clone items and rebind `object_config_graph_id` to the composite OCG id when present.

    In composed runtime views, the composite OCG is the owning container. Many config records
    (nodes, mirrors, annotations, OPGs, etc.) include an optional `object_config_graph_id`.
    When left pointing at a source-module OCG id, the seed diff can produce conflicting
    relationship-derived FK assignments (source vs composite). Rebinding keeps the graph
    internally consistent and matches the composite container semantics.
    """
    out: list[TModel] = []
    for item in items:
        item_copy = item.model_copy(deep=True)
        if hasattr(item_copy, "object_config_graph_id"):
            setattr(item_copy, "object_config_graph_id", composite_ocg_id)
        out.append(item_copy)
    return out


def _normalize_object_config_graph_relationships(
    relationships: Iterable[ObjectConfigGraphRelationship],
    *,
    composite_ocg_id: UUID,
    graphs_by_id: Mapping[UUID, ObjectConfigGraph],
) -> list[ObjectConfigGraphRelationship]:
    """Normalize cross-OCG relationship containers before duplicate comparison."""

    out: list[ObjectConfigGraphRelationship] = []
    for rel in relationships:
        out.append(
            _normalize_object_config_graph_relationship(
                rel,
                composite_ocg_id=composite_ocg_id,
                graphs_by_id=graphs_by_id,
            )
        )
    return out


def _normalize_object_config_graph_relationship(
    rel: ObjectConfigGraphRelationship,
    *,
    composite_ocg_id: UUID,
    graphs_by_id: Mapping[UUID, ObjectConfigGraph],
) -> ObjectConfigGraphRelationship:
    rel_copy = rel.model_copy(deep=False)
    rel_copy.object_config_graph_id = composite_ocg_id
    rel_copy.class_config_relationships = list(rel.class_config_relationships)
    rel_copy.object_config_graph_relationship_classes = list(
        rel.object_config_graph_relationship_classes
    )
    target = graphs_by_id.get(rel_copy.target_object_config_graph_id)
    if target is None:
        target = rel.target_object_config_graph
    rel_copy.target_object_config_graph = (
        _thin_object_config_graph_ref(target) if target is not None else None
    )
    return rel_copy


def _thin_object_config_graph_ref(
    target: ObjectConfigGraph,
) -> ObjectConfigGraph:
    return ObjectConfigGraph(
        id=target.id,
        name=target.name,
        description=target.description,
        hash=target.hash,
        layout_hash=target.layout_hash,
        fqn_prefix=target.fqn_prefix,
        language=target.language,
    )


def _merge_object_config_graph_relationships(
    relationships: Iterable[ObjectConfigGraphRelationship],
    *,
    composite_ocg_id: UUID,
    graphs_by_id: Mapping[UUID, ObjectConfigGraph],
) -> list[ObjectConfigGraphRelationship]:
    merged: dict[UUID, ObjectConfigGraphRelationship] = {}
    payloads: dict[UUID, Mapping[str, Any]] = {}
    order: list[UUID] = []
    for relationship in relationships:
        relationship_id = getattr(relationship, "id", None)
        if not isinstance(relationship_id, UUID):
            raise ValueError(
                "Cannot compose object_config_graph_relationship: missing UUID id "
                + f"on {type(relationship).__name__}"
            )
        normalized = _normalize_object_config_graph_relationship(
            relationship,
            composite_ocg_id=composite_ocg_id,
            graphs_by_id=graphs_by_id,
        )
        existing = merged.get(relationship_id)
        if existing is not None:
            existing_payload = payloads.get(relationship_id)
            if existing_payload is None:
                existing_payload = _object_config_graph_relationship_payload(existing)
                payloads[relationship_id] = existing_payload
            if existing_payload != _object_config_graph_relationship_payload(
                normalized
            ):
                raise ValueError(
                    "Conflicting object_config_graph_relationship entry "
                    + f"id={relationship_id}"
                )
            continue
        merged[relationship_id] = normalized
        order.append(relationship_id)
    return [merged[relationship_id] for relationship_id in order]


def _object_config_graph_relationship_payload(
    relationship: ObjectConfigGraphRelationship,
) -> Mapping[str, Any]:
    return {
        "id": relationship.id,
        "object_config_graph_id": relationship.object_config_graph_id,
        "target_object_config_graph_id": relationship.target_object_config_graph_id,
        "class_config_relationships": tuple(
            sorted(
                (
                    _stable_model_payload(
                        child,
                        exclude={
                            "target_class_config",
                            "reified_from_relationship",
                            "class_config_relationship_association",
                        },
                    )
                    for child in relationship.class_config_relationships
                ),
                key=repr,
            )
        ),
        "object_config_graph_relationship_classes": tuple(
            sorted(
                (
                    _stable_model_payload(child, exclude={"class_config"})
                    for child in relationship.object_config_graph_relationship_classes
                ),
                key=repr,
            )
        ),
    }


def _overlay_id(*, composite_ocg_id: UUID, language: CodeLanguage) -> UUID:
    return uuid5(
        NAMESPACE_URL, f"aware:ocg:{composite_ocg_id}:overlay:{language.value}"
    )


def _overlay_entry_id(*, overlay_id: UUID, kind: str, entity_id: UUID) -> UUID:
    return uuid5(NAMESPACE_URL, f"aware:ocg_overlay:{overlay_id}:{kind}:{entity_id}")


def _merge_overlay_entries(
    *,
    overlay_id: UUID,
    kind: str,
    entries: Iterable[TModel],
    entity_id_field: str,
    exclude_fields: set[str],
) -> list[TModel]:
    merged: dict[UUID, Mapping[str, Any]] = {}
    out: list[TModel] = []

    for entry in entries:
        entity_id = getattr(entry, entity_id_field, None)
        if not isinstance(entity_id, UUID):
            raise ValueError(
                f"Cannot compose overlay {kind}: missing {entity_id_field} on {type(entry).__name__}"
            )

        payload = dict(_stable_model_payload(entry, exclude=exclude_fields))
        existing = merged.get(entity_id)
        if existing is not None:
            if existing != payload:
                raise ValueError(
                    f"Conflicting overlay {kind} for {entity_id_field}={entity_id}"
                )
            continue

        merged[entity_id] = payload
        payload["id"] = _overlay_entry_id(
            overlay_id=overlay_id, kind=kind, entity_id=entity_id
        )
        payload["object_config_graph_overlay_id"] = overlay_id
        out.append(type(entry).model_validate(payload))

    return out


def _compose_overlays(
    *, ocgs: Sequence[ObjectConfigGraph], composite_ocg_id: UUID
) -> list[ObjectConfigGraphOverlay]:
    overlays_by_language: dict[CodeLanguage, list[ObjectConfigGraphOverlay]] = {}
    for ocg in ocgs:
        for overlay in ocg.object_config_graph_overlays:
            overlays_by_language.setdefault(overlay.language, []).append(overlay)

    composed: list[ObjectConfigGraphOverlay] = []
    for language, overlays in overlays_by_language.items():
        oid = _overlay_id(composite_ocg_id=composite_ocg_id, language=language)
        exclude_fields = {
            "id",
            "object_config_graph_overlay_id",
            "class_config",
            "function_config",
            "attribute_config",
            "enum_config",
            "enum_option",
        }

        class_overlays = _merge_overlay_entries(
            overlay_id=oid,
            kind="class",
            entries=(co for o in overlays for co in o.class_config_overlays),
            entity_id_field="class_config_id",
            exclude_fields=exclude_fields,
        )
        function_overlays = _merge_overlay_entries(
            overlay_id=oid,
            kind="function",
            entries=(fo for o in overlays for fo in o.function_config_overlays),
            entity_id_field="function_config_id",
            exclude_fields=exclude_fields,
        )
        attribute_overlays = _merge_overlay_entries(
            overlay_id=oid,
            kind="attribute",
            entries=(ao for o in overlays for ao in o.attribute_config_overlays),
            entity_id_field="attribute_config_id",
            exclude_fields=exclude_fields,
        )
        enum_overlays = _merge_overlay_entries(
            overlay_id=oid,
            kind="enum",
            entries=(eo for o in overlays for eo in o.enum_config_overlays),
            entity_id_field="enum_config_id",
            exclude_fields=exclude_fields,
        )
        enum_option_overlays = _merge_overlay_entries(
            overlay_id=oid,
            kind="enum_option",
            entries=(eo for o in overlays for eo in o.enum_option_overlays),
            entity_id_field="enum_option_id",
            exclude_fields=exclude_fields,
        )

        composed.append(
            ObjectConfigGraphOverlay(
                id=oid,
                language=language,
                object_config_graph_id=composite_ocg_id,
                class_config_overlays=[
                    ClassConfigOverlay.model_validate(x) for x in class_overlays
                ],
                function_config_overlays=[
                    FunctionConfigOverlay.model_validate(x) for x in function_overlays
                ],
                attribute_config_overlays=[
                    AttributeConfigOverlay.model_validate(x) for x in attribute_overlays
                ],
                enum_config_overlays=[
                    EnumConfigOverlay.model_validate(x) for x in enum_overlays
                ],
                enum_option_overlays=[
                    EnumOptionOverlay.model_validate(x) for x in enum_option_overlays
                ],
            )
        )

    composed.sort(key=lambda o: o.language.value)
    return composed


def _prune_inbound_class_config_relationships(*, ocg: ObjectConfigGraph) -> None:
    """Ensure `ClassConfig.class_config_relationships` only contains outbound relationships.

    Canonical relationship instances (ClassConfigRelationship) are owned by exactly one
    ClassConfig via `ClassConfigRelationship.class_config_id`. Some generated graphs
    currently populate `ClassConfig.class_config_relationships` with both inbound and
    outbound relationships for convenience, but this violates the FK semantics used by
    ORM persistence (and produces ambiguous FK assignments during seeding).
    """
    for node in ocg.object_config_graph_nodes:
        class_config = node.class_config
        if class_config is None:
            continue
        rels = class_config.class_config_relationships
        if not rels:
            continue
        class_config.class_config_relationships = [
            rel for rel in rels if rel.class_config_id == class_config.id
        ]


def compose_object_config_graphs(
    *,
    ocgs: Sequence[ObjectConfigGraph],
    composite_id: UUID,
    composite_name: str,
    composite_hash: str,
    composite_fqn_prefix: str,
    validate_portals: bool = True,
    timings: SeedTimings | None = None,
    timing_prefix: str = "compose_object_config_graphs",
) -> ObjectConfigGraph:
    """Compose multiple ObjectConfigGraphs into a single composite graph view.

    v0 composition semantics (strict):
    - All OCGs must share the same canonical language.
    - Lists are merged by `id` with fail-fast conflict detection.
    - `object_config_graph_overlays` are merged by language (one overlay per language).
    - `ObjectProjectionGraph.projection_hash` must be unique across the composed graph.
    """
    if not ocgs:
        raise ValueError("No OCGs provided for composition")
    normalized_composite_fqn_prefix = (composite_fqn_prefix or "").strip()
    if not normalized_composite_fqn_prefix:
        raise ValueError(
            "compose_object_config_graphs requires explicit composite_fqn_prefix"
        )

    _record_compose_input_metrics(
        ocgs=ocgs,
        timings=timings,
        timing_prefix=timing_prefix,
    )

    with maybe_timed(timings, _compose_timing_key(timing_prefix, "validate_language")):
        language = ocgs[0].language
        for ocg in ocgs:
            if ocg.language != language:
                raise ValueError(
                    "Cannot compose OCGs across different canonical languages "
                    f"(first={language!r} other={ocg.language!r})"
                )

    with maybe_timed(timings, _compose_timing_key(timing_prefix, "merge_annotations")):
        annotations = _merge_models_by_id(
            _rebind_object_config_graph_id(
                (a for ocg in ocgs for a in ocg.object_config_graph_annotations),
                composite_ocg_id=composite_id,
            ),
            key="annotation",
        )
    with maybe_timed(timings, _compose_timing_key(timing_prefix, "merge_mirrors")):
        mirrors = _merge_models_by_id(
            _rebind_object_config_graph_id(
                (m for ocg in ocgs for m in ocg.object_config_graph_mirrors),
                composite_ocg_id=composite_id,
            ),
            key="mirror",
        )
    with maybe_timed(timings, _compose_timing_key(timing_prefix, "merge_nodes")):
        nodes = _merge_models_by_id(
            _rebind_object_config_graph_id(
                (n for ocg in ocgs for n in ocg.object_config_graph_nodes),
                composite_ocg_id=composite_id,
            ),
            key="node",
        )
    with maybe_timed(
        timings, _compose_timing_key(timing_prefix, "merge_relationships")
    ):
        graphs_by_id = {g.id: g for g in ocgs if g.id is not None}
        relationships = _merge_object_config_graph_relationships(
            (r for ocg in ocgs for r in ocg.object_config_graph_relationships),
            composite_ocg_id=composite_id,
            graphs_by_id=graphs_by_id,
        )
    with maybe_timed(
        timings,
        _compose_timing_key(timing_prefix, "merge_projection_graphs"),
    ):
        projection_graphs = _merge_models_by_id(
            _rebind_object_config_graph_id(
                (p for ocg in ocgs for p in ocg.object_projection_graphs),
                composite_ocg_id=composite_id,
            ),
            key="opg",
        )
    # Validate portal relationships (OPG -> target OPG) are resolvable within this composed view.
    #
    # Composition is a strict merge operation: it must not "repair" or silently drop portals.
    # Cross-module portals must be provisioned during module build using `external_graphs` so
    # their `target_object_projection_graph_id` matches the target module's stable OPG id.
    if validate_portals:
        with maybe_timed(
            timings,
            _compose_timing_key(timing_prefix, "validate_portal_relationships"),
        ):
            opg_ids = {opg.id for opg in projection_graphs if opg.id is not None}
            for opg in projection_graphs:
                for rel in opg.object_projection_graph_relationships:
                    if rel.target_object_projection_graph_id not in opg_ids:
                        raise ValueError(
                            "Dangling portal relationship in composed environment: "
                            f"source_opg={opg.name!r} source_opg_id={opg.id} "
                            f"source_projection_hash={opg.projection_hash} "
                            f"target_opg_id={rel.target_object_projection_graph_id} "
                            f"class_config_relationship_id={rel.class_config_relationship_id}. "
                            "Fix by ensuring the target module provides the referenced projection and "
                            "rebuilding module artifacts so portal targets resolve via external graphs."
                        )

    # Fail-fast on projection-hash collisions (runtime routing uses projection_hash as lane identity).
    with maybe_timed(
        timings,
        _compose_timing_key(timing_prefix, "validate_projection_hashes"),
    ):
        hashes: dict[str, UUID] = {}
        for opg in projection_graphs:
            prev = hashes.get(opg.projection_hash)
            if prev is not None and prev != opg.id:
                raise ValueError(
                    f"Duplicate ObjectProjectionGraph.projection_hash={opg.projection_hash}"
                )
            hashes[opg.projection_hash] = opg.id

    with maybe_timed(timings, _compose_timing_key(timing_prefix, "compose_overlays")):
        overlays = _compose_overlays(ocgs=ocgs, composite_ocg_id=composite_id)

    with maybe_timed(
        timings, _compose_timing_key(timing_prefix, "construct_composite")
    ):
        composite = ObjectConfigGraph(
            id=composite_id,
            name=composite_name,
            description=None,
            hash=composite_hash,
            fqn_prefix=normalized_composite_fqn_prefix,
            language=language,
            object_config_graph_annotations=annotations,
            object_config_graph_mirrors=mirrors,
            object_config_graph_nodes=nodes,
            object_config_graph_overlays=overlays,
            object_config_graph_relationships=relationships,
            object_projection_graphs=projection_graphs,
        )

    with maybe_timed(timings, _compose_timing_key(timing_prefix, "ensure_identity")):
        _ensure_composite_ocg_identity(ocg=composite, source_ocgs=ocgs)
    with maybe_timed(
        timings,
        _compose_timing_key(timing_prefix, "prune_inbound_relationships"),
    ):
        _prune_inbound_class_config_relationships(ocg=composite)
    return composite


__all__ = ["compose_object_config_graphs"]
