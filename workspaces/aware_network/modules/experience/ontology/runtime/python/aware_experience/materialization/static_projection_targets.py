from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import importlib
from types import ModuleType
from typing import cast
from uuid import UUID

from aware_experience import stable_ids as experience_stable_ids
from aware_experience.graph.ontology import (
    ExperienceGraphOntologyIdentityOperation,
    ExperienceGraphOntologyPlan,
    decode_graph_ontology_plan_payload,
)
from aware_experience.materialization.snapshot_commit import (
    ExperienceProjectionNodeClassIdentitySnapshot,
    ExperienceProjectionNodeSnapshot,
    ExperienceProjectionOIGISnapshot,
)
from aware_experience.materialization.source_module_ontology import valid_import_root
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_id,
    stable_object_instance_graph_identity_id,
)

StableIdFunction = Callable[..., object]


class StaticProjectionTargetNotDerivable(ValueError):
    """Raised when a projection identity needs runtime values to bind a target."""


def projection_oigi_snapshots_for_materialization(
    *,
    index: MetaGraphRuntimeIndex,
    opg: ObjectProjectionGraph,
    object_projection_graph_identity_id: UUID,
    experience_name: str,
    projection_node_snapshots: Sequence[ExperienceProjectionNodeSnapshot],
    compile_plan_payloads: Sequence[Mapping[str, object]],
    dto_stable_ids_import_roots_by_module_id: Mapping[str, tuple[str, ...]],
) -> tuple[ExperienceProjectionOIGISnapshot, ...]:
    graph_plans = _graph_ontology_plans_for_experience(
        experience_name=experience_name,
        compile_plan_payloads=compile_plan_payloads,
    )
    if not graph_plans:
        return ()
    if opg.id is None:
        return ()

    projection_experience_id = experience_stable_ids.stable_projection_experience_id(
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        name=experience_name,
    )
    opg_nodes_by_id = {
        node.id: node for node in (opg.object_projection_graph_nodes or ()) if node.id
    }
    projection_node_identity_ids = _projection_node_identity_ids_by_source_key(
        projection_experience_id=projection_experience_id,
        projection_node_snapshots=projection_node_snapshots,
    )

    snapshots: list[ExperienceProjectionOIGISnapshot] = []
    for graph_plan in graph_plans:
        object_instance_graph_id = stable_object_instance_graph_id(
            object_projection_graph_id=opg.id,
            key=graph_plan.graph.graph_name,
        )
        object_instance_graph_identity_id = stable_object_instance_graph_identity_id(
            object_projection_graph_identity_id=object_projection_graph_identity_id,
            object_instance_graph_id=object_instance_graph_id,
        )
        derived_source_object_ids: dict[str, UUID] = {}
        parent_ref_by_child_ref = {
            edge.child_ref: edge.parent_ref for edge in graph_plan.node_identity_edges
        }
        identities_by_ref = {
            identity.ref: identity for identity in graph_plan.identities
        }
        node_class_identities: list[ExperienceProjectionNodeClassIdentitySnapshot] = []
        for identity in sorted(
            graph_plan.identities,
            key=lambda item: (item.key, item.ref, item.node_name, item.identity_key),
        ):
            projection_node_identity_id = projection_node_identity_ids.get(
                (identity.node_name.casefold(), identity.identity_key.casefold())
            )
            if projection_node_identity_id is None:
                continue
            node_snapshot = _projection_node_snapshot_by_source_name(
                projection_node_snapshots=projection_node_snapshots,
                node_name=identity.node_name,
            )
            if node_snapshot is None:
                continue
            opg_node = opg_nodes_by_id.get(
                node_snapshot.object_projection_graph_node_id
            )
            class_config_id = getattr(opg_node, "class_config_id", None)
            if class_config_id is None:
                continue
            try:
                source_object_id = derive_static_projection_source_object_id(
                    identity_ref=identity.ref,
                    identities_by_ref=identities_by_ref,
                    parent_ref_by_child_ref=parent_ref_by_child_ref,
                    class_config_id_by_ref={
                        item.ref: _class_config_id_for_graph_identity(
                            opg_nodes_by_id=opg_nodes_by_id,
                            projection_node_snapshots=projection_node_snapshots,
                            identity_node_name=item.node_name,
                        )
                        for item in graph_plan.identities
                    },
                    derived_source_object_ids=derived_source_object_ids,
                    dto_stable_ids_import_roots_by_module_id=(
                        dto_stable_ids_import_roots_by_module_id
                    ),
                )
            except StaticProjectionTargetNotDerivable:
                continue
            node_class_identities.append(
                ExperienceProjectionNodeClassIdentitySnapshot(
                    projection_experience_node_identity_id=(
                        projection_node_identity_id
                    ),
                    class_config_id=class_config_id,
                    source_object_id=source_object_id,
                    key=identity.identity_key,
                )
            )
        if node_class_identities:
            snapshots.append(
                ExperienceProjectionOIGISnapshot(
                    object_instance_graph_id=object_instance_graph_id,
                    object_instance_graph_identity_id=(
                        object_instance_graph_identity_id
                    ),
                    key=graph_plan.graph.graph_name,
                    node_class_identities=tuple(node_class_identities),
                )
            )
    return tuple(snapshots)


def derive_static_projection_source_object_id(
    *,
    identity_ref: str,
    identities_by_ref: Mapping[str, ExperienceGraphOntologyIdentityOperation],
    parent_ref_by_child_ref: Mapping[str, str],
    class_config_id_by_ref: Mapping[str, UUID | None],
    derived_source_object_ids: dict[str, UUID],
    dto_stable_ids_import_roots_by_module_id: Mapping[str, tuple[str, ...]],
) -> UUID:
    existing = derived_source_object_ids.get(identity_ref)
    if existing is not None:
        return existing

    identity = identities_by_ref.get(identity_ref)
    if identity is None:
        raise StaticProjectionTargetNotDerivable(identity_ref)
    class_config_id = class_config_id_by_ref.get(identity_ref)
    if class_config_id is None:
        raise StaticProjectionTargetNotDerivable(identity_ref)
    stable_fn, arg_names = stable_source_id_binding_for_node(
        node_name=identity.node_name,
        class_config_id=class_config_id,
        dto_stable_ids_import_roots_by_module_id=(
            dto_stable_ids_import_roots_by_module_id
        ),
    )
    kwargs: dict[str, object] = {}
    parent_source_object_id: UUID | None = None
    parent_ref = parent_ref_by_child_ref.get(identity_ref)
    for arg_name in arg_names:
        if arg_name.endswith("_id"):
            if parent_source_object_id is None:
                if not parent_ref:
                    raise StaticProjectionTargetNotDerivable(identity_ref)
                parent_source_object_id = derive_static_projection_source_object_id(
                    identity_ref=parent_ref,
                    identities_by_ref=identities_by_ref,
                    parent_ref_by_child_ref=parent_ref_by_child_ref,
                    class_config_id_by_ref=class_config_id_by_ref,
                    derived_source_object_ids=derived_source_object_ids,
                    dto_stable_ids_import_roots_by_module_id=(
                        dto_stable_ids_import_roots_by_module_id
                    ),
                )
            kwargs[arg_name] = parent_source_object_id
            continue
        kwargs[arg_name] = _static_identity_arg_value(
            arg_name=arg_name,
            identity_key=identity.identity_key,
        )
    try:
        source_object_id = stable_fn(**kwargs)
    except Exception as exc:
        raise StaticProjectionTargetNotDerivable(identity_ref) from exc
    if not isinstance(source_object_id, UUID):
        raise StaticProjectionTargetNotDerivable(identity_ref)
    derived_source_object_ids[identity_ref] = source_object_id
    return source_object_id


def stable_source_id_binding_for_node(
    *,
    node_name: str,
    class_config_id: UUID,
    dto_stable_ids_import_roots_by_module_id: Mapping[str, tuple[str, ...]],
) -> tuple[StableIdFunction, tuple[str, ...]]:
    module_id = module_id_from_projection_node_name(node_name=node_name)
    for import_root in dto_stable_ids_import_roots_by_module_id.get(module_id, ()):
        module = import_declared_stable_ids_module(import_root=import_root)
        if module is None:
            continue
        bindings = getattr(
            module, "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID", {}
        )
        if not isinstance(bindings, Mapping):
            continue
        binding = bindings.get(str(class_config_id))
        if binding is None:
            continue
        stable_fn_name, arg_names_raw = binding
        stable_fn = getattr(module, str(stable_fn_name), None)
        if not callable(stable_fn):
            continue
        if not isinstance(arg_names_raw, Sequence) or isinstance(
            arg_names_raw, (str, bytes)
        ):
            continue
        arg_names = tuple(
            str(item).strip() for item in arg_names_raw if str(item).strip()
        )
        if arg_names:
            return stable_fn, arg_names
    raise StaticProjectionTargetNotDerivable(str(class_config_id))


def import_declared_stable_ids_module(*, import_root: str) -> ModuleType | None:
    if not valid_import_root(import_root):
        return None
    module_name = f"{import_root}.stable_ids"
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        missing_name = exc.name or ""
        if missing_name == import_root or missing_name == module_name:
            return None
        if missing_name.startswith(f"{module_name}."):
            return None
        raise
    return None


def module_id_from_projection_node_name(*, node_name: str) -> str:
    token = (node_name or "").split(".", 1)[0].strip()
    if token.startswith("aware_"):
        token = token.removeprefix("aware_").strip()
    if not token or not all(ch.isalnum() or ch == "_" for ch in token):
        raise StaticProjectionTargetNotDerivable(node_name)
    return token


def _graph_ontology_plans_for_experience(
    *,
    experience_name: str,
    compile_plan_payloads: Sequence[Mapping[str, object]],
) -> tuple[ExperienceGraphOntologyPlan, ...]:
    plans: list[ExperienceGraphOntologyPlan] = []
    for payload in compile_plan_payloads:
        graph_payload = payload.get("graph_ontology")
        if not isinstance(graph_payload, Sequence) or isinstance(
            graph_payload, (str, bytes)
        ):
            continue
        plans.extend(decode_graph_ontology_plan_payload(payload=graph_payload))
    experience_key = experience_name.strip().casefold()
    return tuple(
        plan
        for plan in plans
        if plan.graph.experience.strip().casefold() == experience_key
    )


def _projection_node_identity_ids_by_source_key(
    *,
    projection_experience_id: UUID,
    projection_node_snapshots: Sequence[ExperienceProjectionNodeSnapshot],
) -> dict[tuple[str, str], UUID]:
    resolved: dict[tuple[str, str], UUID] = {}
    for snapshot in projection_node_snapshots:
        projection_node_id = experience_stable_ids.stable_projection_experience_node_id(
            projection_experience_id=projection_experience_id,
            object_projection_graph_node_id=snapshot.object_projection_graph_node_id,
            key=snapshot.key,
        )
        for identity_key in snapshot.identity_keys:
            resolved[(snapshot.key.casefold(), identity_key.casefold())] = (
                experience_stable_ids.stable_projection_experience_node_identity_id(
                    projection_experience_node_id=projection_node_id,
                    key=identity_key,
                )
            )
    return resolved


def _projection_node_snapshot_by_source_name(
    *,
    projection_node_snapshots: Sequence[ExperienceProjectionNodeSnapshot],
    node_name: str,
) -> ExperienceProjectionNodeSnapshot | None:
    node_name_key = node_name.strip().casefold()
    for snapshot in projection_node_snapshots:
        if snapshot.key.strip().casefold() == node_name_key:
            return snapshot
    return None


def _class_config_id_for_graph_identity(
    *,
    opg_nodes_by_id: Mapping[UUID, object],
    projection_node_snapshots: Sequence[ExperienceProjectionNodeSnapshot],
    identity_node_name: str,
) -> UUID | None:
    node_snapshot = _projection_node_snapshot_by_source_name(
        projection_node_snapshots=projection_node_snapshots,
        node_name=identity_node_name,
    )
    if node_snapshot is None:
        return None
    opg_node = opg_nodes_by_id.get(node_snapshot.object_projection_graph_node_id)
    return cast(UUID | None, getattr(opg_node, "class_config_id", None))


def _static_identity_arg_value(*, arg_name: str, identity_key: str) -> object:
    normalized_arg = arg_name.strip().casefold()
    value = identity_key.strip()
    if not value:
        raise StaticProjectionTargetNotDerivable(arg_name)
    if normalized_arg in {"name", "label", "key", "slug"}:
        return value
    if value.isdigit():
        return int(value)
    raise StaticProjectionTargetNotDerivable(arg_name)


__all__ = [
    "derive_static_projection_source_object_id",
    "import_declared_stable_ids_module",
    "module_id_from_projection_node_name",
    "projection_oigi_snapshots_for_materialization",
    "StableIdFunction",
    "stable_source_id_binding_for_node",
    "StaticProjectionTargetNotDerivable",
]
