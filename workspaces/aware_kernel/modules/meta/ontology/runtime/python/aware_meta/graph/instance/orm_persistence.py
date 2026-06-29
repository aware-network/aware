"""Meta-owned ORM projection staging helpers.

Handlers must not call `push()` directly. Meta stages DB writes after:
OIG(post) capture → diff → policy decisions.

This module stages DB writes as a **projection** from OIG commits:
- OIG commits are SSOT for truth.
- DB writes are derived, rebuildable, and lane-scoped (branch_id + projection_hash).
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, cast
from uuid import UUID

# History Api
from aware_history_ontology.change.change_enums import ChangeType, ChangeDeltaKind

# History Ontology
from aware_history_ontology.change.change_delta import ChangeDelta

# Meta Ontology
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.attribute.attribute_config import AttributeConfig

# ORM
from aware_orm.registry import ORMModelRegistry
from aware_orm.session.current_session_ctx import set_session
from aware_orm.session.session import Session


class MetaOrmProjectionIndex(Protocol):
    """Minimal Meta graph index contract needed for OIG -> ORM projection."""

    ocg: Any
    attribute_configs_by_id: Mapping[UUID, AttributeConfig]


def _resolve_backend_name(session: Session) -> str:
    raw = getattr(session, "_backend_name", None)
    if isinstance(raw, str) and raw.strip():
        return raw.strip().lower()
    env = os.getenv("AWARE_PERSISTENCE_BACKEND", "").strip().lower()
    if env:
        return env
    return "noop" if session.skip_db else "db"


def _build_enum_option_value_by_id(index: MetaOrmProjectionIndex) -> dict[UUID, str]:
    """Build enum option id → value mapping from the installed runtime OCG."""
    out: dict[UUID, str] = {}
    try:
        ocg = index.ocg
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Failed to read runtime OCG for enum mapping: {exc}") from exc

    enum_configs: list[EnumConfig] = []
    for node in ocg.object_config_graph_nodes:
        enum_cfg = node.enum_config
        if enum_cfg is not None:
            enum_configs.append(enum_cfg)

    for enum_cfg in enum_configs:
        for opt in enum_cfg.enum_options:
            opt_id = opt.id
            if opt_id in out:
                continue
            out[opt_id] = opt.value
    return out


def _iter_class_instance_changes(changes: Iterable[ObjectInstanceGraphChange]):
    for root in changes:
        for ci_change in root.class_instance_changes:
            yield ci_change


@dataclass(frozen=True)
class _ForeignKeySpec:
    field_name: str
    referenced_class_config_id: UUID
    is_required: bool


@dataclass(frozen=True)
class _RelationshipFkSpec:
    owner_side: ClassConfigRelationshipDirection
    owner_class_config_id: UUID
    target_class_config_id: UUID
    field_name: str
    db_required: bool


@dataclass(frozen=True)
class DomainPersistencePlan:
    """Deterministic DB staging plan derived from OCG FK metadata."""

    class_config_by_instance_id: dict[UUID, UUID]
    create_order: list[UUID]
    update_order: list[UUID]
    delete_order: list[UUID]
    deferred_create_fk_fields_by_instance_id: dict[UUID, dict[str, UUID]]


async def stage_domain_persistence(
    *,
    index: MetaOrmProjectionIndex,
    session: Session,
    branch_id: UUID,
    projection_hash: str,
    before_oig: ObjectInstanceGraph,
    after_oig: ObjectInstanceGraph,
    changes: list[ObjectInstanceGraphChange],
) -> None:
    """Stage ORM writes for the provided change set into the given Session."""
    if session.skip_db:
        return

    backend = _resolve_backend_name(session)
    if backend not in {"db", "fs"}:
        # noop/offline backends do not persist projection rows.
        return

    # Canonical: plan-driven projection writes (OIG → SQL) after FS commit append.
    # The same staging path is used for db and fs backends; backend-specific write/read
    # behavior is handled by Session persistence backends.
    from aware_meta.graph.instance.orm_projector import stage_lane_projection_writes
    from aware_orm.projection.runtime import ProjectionRuntime

    proj_hash = (projection_hash or "").strip()
    if not proj_hash:
        raise ValueError("projection_hash is required for projection staging")

    try:
        plan = ProjectionRuntime.require_plan(dialect="postgres", projection_hash=proj_hash)
    except KeyError:
        if backend == "fs":
            # Test/local fs lanes can run with minimal bundles that do not install
            # SQL projection plans. In that case, keep commit rails as SSOT and
            # skip derived projection writes.
            return
        raise

    enum_option_value_by_id = _build_enum_option_value_by_id(index=index)

    _ = stage_lane_projection_writes(
        session=session,
        plan=plan,
        branch_id=branch_id,
        projection_hash=proj_hash,
        before_oig=before_oig,
        after_oig=after_oig,
        changes=changes,
        enum_option_value_by_id=enum_option_value_by_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
    )
    return


async def compute_domain_persistence_plan(
    *,
    session: Session,
    before_oig: ObjectInstanceGraph,
    changes: list[ObjectInstanceGraphChange],
) -> DomainPersistencePlan:
    """Compute a deterministic DB staging plan from change graphs and OCG FK metadata.

    Notes
    -----
    - This is delta-first: it does not require OIG(post).
    - FK dependency edges are derived **only** from OCG `FOREIGN_KEY` relationship attributes
      (no naming heuristics).
    """

    def _delta_value(delta: ChangeDelta) -> object:
        return delta.payload.get("value")

    def _as_uuid(value: object, *, context: str) -> UUID:
        if isinstance(value, UUID):
            return value
        if isinstance(value, str):
            return UUID(value)
        raise TypeError(f"Expected UUID/str for {context}, got {type(value)}")

    class_config_by_instance_id: dict[UUID, UUID] = {}
    for ci in before_oig.class_instances:
        class_config_by_instance_id[ci.id] = ci.class_config_id

    created_ids: set[UUID] = set()
    updated_ids: set[UUID] = set()
    deleted_ids: set[UUID] = set()

    for ci_change in _iter_class_instance_changes(changes):
        ch = ci_change.change
        instance_id = ci_change.class_instance_id
        if ch.type == ChangeType.delete:
            deleted_ids.add(instance_id)
        elif ch.type == ChangeType.create:
            created_ids.add(instance_id)
        else:
            updated_ids.add(instance_id)

    # Created instances are not present in OIG(pre); read their class_config_id from the CREATE
    # change deltas so persistence staging does not require OIG(post).
    for ci_change in _iter_class_instance_changes(changes):
        ch = ci_change.change
        if ch.type != ChangeType.create:
            continue
        class_config_id: UUID | None = None
        for cd in ch.change_deltas:
            if cd.kind != ChangeDeltaKind.scalar_set or cd.property != "class_config_id":
                continue
            raw = _delta_value(cd)
            if raw is None:
                continue
            class_config_id = _as_uuid(raw, context="CREATE.class_config_id")
            break
        if class_config_id is None:
            raise RuntimeError(
                "CREATE ClassInstanceChange missing required class_config_id scalar_set delta: "
                + f"instance_id={ci_change.class_instance_id}"
            )
        class_config_by_instance_id[ci_change.class_instance_id] = class_config_id

    def _stable_key(instance_id: UUID) -> tuple[str, str]:
        cc_id = class_config_by_instance_id.get(instance_id)
        if cc_id is None:
            raise RuntimeError(f"Missing class_config_id for instance {instance_id}")
        return str(cc_id), str(instance_id)

    # Limit FK analysis to classes actually present in this change set so unrelated
    # kernel/module bindings cannot affect domain persistence planning.
    relevant_cc_ids: set[UUID] = {
        class_config_by_instance_id[i]
        for i in sorted({*created_ids, *updated_ids, *deleted_ids}, key=str)
        if i in class_config_by_instance_id
    }
    fk_specs_by_owner_cc = _build_fk_specs_by_owner_cc_id(only_class_config_ids=relevant_cc_ids)
    fk_specs_by_relationship_id = _build_fk_specs_by_relationship_id(only_class_config_ids=relevant_cc_ids)

    async def _dependencies_for(instance_id: UUID, *, population: set[UUID]) -> set[UUID]:
        cc_id = class_config_by_instance_id.get(instance_id)
        if cc_id is None:
            raise RuntimeError(f"Missing class_config_id for instance {instance_id}")
        orm_class = ORMModelRegistry.get_class_by_class_config_id(cc_id)
        if orm_class is None:
            raise RuntimeError(f"ORM class not found for ClassConfig {cc_id} (instance_id={instance_id})")
        orm_model = await orm_class.get_by_id(instance_id, cache_valid=True, eager=False)
        if orm_model is None:
            raise RuntimeError(
                f"ORM model not found for persistence planning: class_config_id={cc_id} id={instance_id}"
            )

        deps: set[UUID] = set()
        for spec in fk_specs_by_owner_cc.get(cc_id, ()):
            if not spec.is_required:
                continue
            raw = cast(object | None, getattr(orm_model, spec.field_name, None))
            if raw is None:
                continue
            ref_id = _as_uuid(raw, context=f"{cc_id}.{spec.field_name}")
            if ref_id == instance_id:
                continue
            if ref_id in population:
                ref_cc_id = class_config_by_instance_id.get(ref_id)
                if ref_cc_id is None:
                    raise RuntimeError(f"Missing class_config_id for FK target {ref_id} (from {instance_id})")
                if ref_cc_id != spec.referenced_class_config_id:
                    raise RuntimeError(
                        "FK references unexpected ClassConfig for dependency ordering: "
                        + f"owner_instance_id={instance_id} fk_field={spec.field_name} "
                        + f"expected_class_config_id={spec.referenced_class_config_id} "
                        + f"target_instance_id={ref_id} target_class_config_id={ref_cc_id}"
                    )
                deps.add(ref_id)
        return deps

    async def _deferred_optional_fks_for(instance_id: UUID, *, population: set[UUID]) -> dict[str, UUID]:
        cc_id = class_config_by_instance_id.get(instance_id)
        if cc_id is None:
            raise RuntimeError(f"Missing class_config_id for instance {instance_id}")
        orm_class = ORMModelRegistry.get_class_by_class_config_id(cc_id)
        if orm_class is None:
            raise RuntimeError(f"ORM class not found for ClassConfig {cc_id} (instance_id={instance_id})")
        orm_model = await orm_class.get_by_id(instance_id, cache_valid=True, eager=False)
        if orm_model is None:
            raise RuntimeError(
                f"ORM model not found for persistence planning: class_config_id={cc_id} id={instance_id}"
            )

        deferred: dict[str, UUID] = {}
        fk_field_names = {spec.field_name for spec in fk_specs_by_owner_cc.get(cc_id, ())}
        for spec in fk_specs_by_owner_cc.get(cc_id, ()):
            if spec.is_required:
                continue
            raw = cast(object | None, getattr(orm_model, spec.field_name, None))
            if raw is None:
                continue
            ref_id = _as_uuid(raw, context=f"{cc_id}.{spec.field_name}")
            if ref_id == instance_id:
                continue
            if ref_id not in population:
                continue
            ref_cc_id = class_config_by_instance_id.get(ref_id)
            if ref_cc_id is None:
                raise RuntimeError(f"Missing class_config_id for FK target {ref_id} (from {instance_id})")
            if ref_cc_id != spec.referenced_class_config_id:
                raise RuntimeError(
                    f"FK references unexpected ClassConfig for dependency ordering: owner_instance_id={instance_id} "
                    + f"fk_field={spec.field_name} expected_class_config_id={spec.referenced_class_config_id} "
                    + f"target_instance_id={ref_id} target_class_config_id={ref_cc_id}"
                )
            deferred[spec.field_name] = ref_id

        # Fallback: defer nullable `*_id` fields that reference other newly-created objects.
        #
        # This is a defensive bridge for bootstrap/config graphs where some relationships
        # are represented in SQL as FK columns but do not yet surface `FOREIGN_KEY` role
        # bindings in `ClassConfigRelationshipAttribute` metadata.
        #
        # Contract:
        # - Only considers optional fields (`FieldInfo.is_required() == False`).
        # - Only defers when the value points at another created instance (`population`).
        # - Required FKs remain enforced via ordering and will not be nulled here.
        for field_name, info in orm_model.__class__.model_fields.items():
            if field_name in deferred:
                continue
            if field_name in fk_field_names:
                continue
            if not field_name.endswith("_id"):
                continue
            if info.is_required():
                continue
            raw = cast(object | None, getattr(orm_model, field_name, None))
            if raw is None:
                continue
            try:
                ref_id = _as_uuid(raw, context=f"{cc_id}.{field_name}")
            except Exception:
                continue
            if ref_id == instance_id:
                continue
            if ref_id not in population:
                continue
            deferred[field_name] = ref_id
        return deferred

    def _toposort(nodes: set[UUID], deps_by_node: dict[UUID, set[UUID]]) -> list[UUID]:
        import heapq

        in_degree: dict[UUID, int] = {n: 0 for n in nodes}
        dependents_by_parent: dict[UUID, set[UUID]] = {n: set() for n in nodes}
        for node, deps in deps_by_node.items():
            if node not in nodes:
                continue
            for dep in deps:
                if dep not in nodes:
                    continue
                in_degree[node] += 1
                dependents_by_parent[dep].add(node)

        heap: list[tuple[tuple[str, str], UUID]] = [(_stable_key(n), n) for n, d in in_degree.items() if d == 0]
        heapq.heapify(heap)
        out: list[UUID] = []

        while heap:
            _, node = heapq.heappop(heap)
            out.append(node)
            for dependent in dependents_by_parent[node]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    heapq.heappush(heap, (_stable_key(dependent), dependent))

        if len(out) != len(nodes):
            remaining = sorted((n for n, d in in_degree.items() if d > 0), key=_stable_key)
            details = {str(n): sorted((str(d) for d in deps_by_node.get(n, set())), key=str) for n in remaining}
            raise RuntimeError(f"FK dependency cycle detected in persistence plan: {details}")
        return out

    with set_session(session):
        create_deps: dict[UUID, set[UUID]] = {}
        for iid in sorted(created_ids, key=_stable_key):
            deps = await _dependencies_for(iid, population=created_ids)
            if deps:
                create_deps[iid] = deps

        delete_deps: dict[UUID, set[UUID]] = {}
        for iid in sorted(deleted_ids, key=_stable_key):
            deps = await _dependencies_for(iid, population=deleted_ids)
            if deps:
                delete_deps[iid] = deps

        deferred_create_fks: dict[UUID, dict[str, UUID]] = {}
        for iid in sorted(created_ids, key=_stable_key):
            deferred = await _deferred_optional_fks_for(iid, population=created_ids)
            if deferred:
                deferred_create_fks[iid] = deferred

        # Augment create dependencies + deferrals using explicit relationship changes.
        for root in changes:
            for rel_change in root.class_instance_relationship_changes:
                change = rel_change.change
                if change.type != ChangeType.create:
                    continue
                rel_id = rel_change.class_config_relationship_id
                spec = fk_specs_by_relationship_id.get(rel_id)
                if spec is None:
                    continue

                if spec.owner_side == ClassConfigRelationshipDirection.forward:
                    owner_id = rel_change.source_class_instance_id
                    target_id = rel_change.target_class_instance_id
                else:
                    owner_id = rel_change.target_class_instance_id
                    target_id = rel_change.source_class_instance_id

                if owner_id not in created_ids or target_id not in created_ids:
                    continue

                if spec.db_required:
                    create_deps.setdefault(owner_id, set()).add(target_id)
                else:
                    existing = deferred_create_fks.setdefault(owner_id, {})
                    prior = existing.get(spec.field_name)
                    if prior is None:
                        existing[spec.field_name] = target_id
                    elif prior != target_id:
                        raise RuntimeError(
                            "Conflicting deferred FK values derived from relationship changes: "
                            + f"owner_instance_id={owner_id} "
                            + f"field={spec.field_name} prior={prior} new={target_id}"
                        )

    create_order = _toposort(created_ids, create_deps)

    # Stage updates deterministically after creates (FKs can reference newly created ids).
    update_order = sorted(updated_ids - created_ids, key=_stable_key)

    delete_topo = _toposort(deleted_ids, delete_deps)
    delete_order = list(reversed(delete_topo))

    return DomainPersistencePlan(
        class_config_by_instance_id=class_config_by_instance_id,
        create_order=create_order,
        update_order=update_order,
        delete_order=delete_order,
        deferred_create_fk_fields_by_instance_id=deferred_create_fks,
    )


def _build_fk_specs_by_owner_cc_id(
    *, only_class_config_ids: set[UUID] | None = None
) -> dict[UUID, tuple[_ForeignKeySpec, ...]]:
    """Build a deterministic FK spec index from bound ClassConfig relationship metadata.

    Args:
        only_class_config_ids: Optional filter limiting analysis to a subset of ClassConfig ids.
            This is used by the runtime to avoid scanning unrelated kernel/module bindings when
            planning persistence for a single operation.
    """

    # Collect ClassConfig + relationship metadata from bound ORM model classes.
    relationships_by_id: dict[UUID, ClassConfigRelationship] = {}
    attribute_names_by_id: dict[UUID, str] = {}
    owner_cc_by_attr_id: dict[UUID, UUID] = {}

    for orm_class in ORMModelRegistry.get_all_fqn_to_class().values():
        try:
            cc = orm_class.get_class_config()
        except Exception:
            cc = None
        if cc is None:
            continue
        cc_id = cc.id
        if only_class_config_ids is not None and cc_id not in only_class_config_ids:
            continue
        for link in cc.class_config_attribute_configs:
            ac = link.attribute_config
            ac_id = ac.id
            ac_name = ac.name
            attribute_names_by_id[ac_id] = ac_name
            prev_owner = owner_cc_by_attr_id.get(ac_id)
            if prev_owner is not None and prev_owner != cc_id:
                raise RuntimeError(
                    f"AttributeConfig {ac_id} owned by multiple ClassConfigs ({prev_owner} vs {cc_id})"
                )
            owner_cc_by_attr_id[ac_id] = cc_id

        for rel in cc.class_config_relationships:
            relationships_by_id[rel.id] = rel

    specs_by_owner: dict[UUID, list[_ForeignKeySpec]] = {}

    for rel in relationships_by_id.values():
        rel_id = rel.id

        source_cc_id = rel.class_config_id
        target_cc_id = rel.target_class_config_id

        assoc_edge = rel.class_config_relationship_association_edge
        if assoc_edge is not None and rel.reified_from_relationship_id is None:
            # Canonical association relationships are metadata-only for runtime persistence.
            # FK planning must use the reified edges (source->association, association->target).
            continue

        for rel_attr in rel.class_config_relationship_attributes:
            if rel_attr.role != ClassConfigRelationshipAttributeRole.foreign_key:
                continue
            direction = rel_attr.direction
            attr_id = rel_attr.attribute_config_id

            if direction == ClassConfigRelationshipDirection.forward:
                expected_owner_cc_id = source_cc_id
                referenced_cc_id = target_cc_id
            elif direction == ClassConfigRelationshipDirection.reverse:
                expected_owner_cc_id = target_cc_id
                referenced_cc_id = source_cc_id
            else:
                raise RuntimeError(
                    f"Unsupported relationship direction for FOREIGN_KEY: class_config_relationship_id={rel_id} "
                    + f"direction={direction}"
                )

            # When a filter is provided, skip FOREIGN_KEY attributes owned by out-of-scope
            # ClassConfigs. We only need FK metadata for classes participating in this plan.
            if only_class_config_ids is not None and expected_owner_cc_id not in only_class_config_ids:
                continue

            owner_cc_id = owner_cc_by_attr_id.get(attr_id)
            if owner_cc_id is None:
                raise RuntimeError(
                    "Relationship FOREIGN_KEY attribute_config_id not found on any bound ClassConfig: "
                    + f"class_config_relationship_id={rel_id} attribute_config_id={attr_id} "
                    + f"expected_owner={expected_owner_cc_id}"
                )
            if owner_cc_id != expected_owner_cc_id:
                raise RuntimeError(
                    "Relationship FOREIGN_KEY must be owned by the expected ClassConfig: "
                    + f"class_config_relationship_id={rel_id} owner={owner_cc_id} expected={expected_owner_cc_id}"
                )

            field_name = attribute_names_by_id.get(attr_id)
            if not field_name:
                raise RuntimeError(
                    "Relationship FOREIGN_KEY attribute_config_id missing AttributeConfig.name: "
                    + f"class_config_relationship_id={rel_id} attribute_config_id={attr_id}"
                )
            # DB-requiredness follows relationship semantics.
            #
            # Canonical many-to-many edges are represented as:
            # - a metadata-only canonical relationship (skipped above), and
            # - two reified relationships (source->association, association->target).
            #
            # For reified association relationships, the FK columns live on the association
            # edge class and are always DB-required (a join row must reference both endpoints).
            if rel.reified_from_relationship_id is not None:
                is_required = True
            elif direction == ClassConfigRelationshipDirection.forward:
                is_required = bool(rel.forward_required)
            else:
                is_required = False

            specs_by_owner.setdefault(owner_cc_id, []).append(
                _ForeignKeySpec(
                    field_name=field_name,
                    referenced_class_config_id=referenced_cc_id,
                    is_required=is_required,
                )
            )

    # Deterministic: sort within each owner by (field_name, referenced_cc_id).
    out: dict[UUID, tuple[_ForeignKeySpec, ...]] = {}
    for owner_cc_id, specs in specs_by_owner.items():
        out[owner_cc_id] = tuple(
            sorted(
                specs,
                key=lambda s: (
                    s.field_name,
                    str(s.referenced_class_config_id),
                    0 if s.is_required else 1,
                ),
            )
        )
    return out


def _build_fk_specs_by_relationship_id(
    *, only_class_config_ids: set[UUID] | None = None
) -> dict[UUID, _RelationshipFkSpec]:
    """Build FK relationship specs keyed by ClassConfigRelationship.id.

    This is used by the persistence planner to derive ordering and deferrals
    from explicit relationship changes (canonical edges), without relying on
    ORM FK field state.
    """

    relationships_by_id: dict[UUID, ClassConfigRelationship] = {}
    attribute_names_by_id: dict[UUID, str] = {}
    owner_cc_by_attr_id: dict[UUID, UUID] = {}

    for orm_class in ORMModelRegistry.get_all_fqn_to_class().values():
        try:
            cc = orm_class.get_class_config()
        except Exception:
            cc = None
        if cc is None:
            continue
        cc_id = cc.id
        if only_class_config_ids is not None and cc_id not in only_class_config_ids:
            continue
        for link in cc.class_config_attribute_configs:
            ac = link.attribute_config
            ac_id = ac.id
            ac_name = ac.name
            attribute_names_by_id[ac_id] = ac_name
            prev_owner = owner_cc_by_attr_id.get(ac_id)
            if prev_owner is not None and prev_owner != cc_id:
                raise RuntimeError(
                    f"AttributeConfig {ac_id} owned by multiple ClassConfigs ({prev_owner} vs {cc_id})"
                )
            owner_cc_by_attr_id[ac_id] = cc_id

        for rel in cc.class_config_relationships:
            relationships_by_id[rel.id] = rel

    out: dict[UUID, _RelationshipFkSpec] = {}

    for rel in relationships_by_id.values():
        rel_id = rel.id

        source_cc_id = rel.class_config_id
        target_cc_id = rel.target_class_config_id

        assoc_edge = rel.class_config_relationship_association_edge
        if assoc_edge is not None and rel.reified_from_relationship_id is None:
            # Canonical association relationships are metadata-only for runtime persistence.
            # FK planning must use the reified edges (source->association, association->target).
            continue

        fk_attr_id: UUID | None = None
        fk_direction: ClassConfigRelationshipDirection | None = None
        for rel_attr in rel.class_config_relationship_attributes:
            if rel_attr.role == ClassConfigRelationshipAttributeRole.foreign_key:
                fk_attr_id = rel_attr.attribute_config_id
                fk_direction = rel_attr.direction

        if fk_attr_id is None or fk_direction is None:
            continue

        if fk_direction == ClassConfigRelationshipDirection.forward:
            owner_cc_id = source_cc_id
            target_cc_id_for_fk = target_cc_id
        elif fk_direction == ClassConfigRelationshipDirection.reverse:
            owner_cc_id = target_cc_id
            target_cc_id_for_fk = source_cc_id

        if only_class_config_ids is not None and owner_cc_id not in only_class_config_ids:
            continue

        owner_cc = owner_cc_by_attr_id.get(fk_attr_id)
        if owner_cc is None:
            raise RuntimeError(
                "Relationship FOREIGN_KEY attribute_config_id not found on any bound ClassConfig: "
                + f"class_config_relationship_id={rel_id} attribute_config_id={fk_attr_id} expected_owner={owner_cc_id}"
            )
        if owner_cc != owner_cc_id:
            raise RuntimeError(
                "Relationship FOREIGN_KEY must be owned by the expected ClassConfig: "
                + f"class_config_relationship_id={rel_id} owner={owner_cc} expected={owner_cc_id}"
            )

        field_name = attribute_names_by_id.get(fk_attr_id)
        if not field_name:
            raise RuntimeError(
                "Relationship FOREIGN_KEY attribute_config_id missing AttributeConfig.name: "
                + f"class_config_relationship_id={rel_id} attribute_config_id={fk_attr_id}"
            )

        if rel.reified_from_relationship_id is not None:
            db_required = True
        elif fk_direction == ClassConfigRelationshipDirection.forward:
            db_required = bool(rel.forward_required)
        else:
            db_required = bool(rel.forward_required)

        out[rel_id] = _RelationshipFkSpec(
            owner_side=fk_direction,
            owner_class_config_id=owner_cc_id,
            target_class_config_id=target_cc_id_for_fk,
            field_name=field_name,
            db_required=db_required,
        )

    return out


__all__ = [
    "DomainPersistencePlan",
    "MetaOrmProjectionIndex",
    "compute_domain_persistence_plan",
    "stage_domain_persistence",
]
