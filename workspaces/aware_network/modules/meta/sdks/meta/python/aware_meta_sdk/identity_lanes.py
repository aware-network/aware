from __future__ import annotations

import inspect
from collections.abc import Mapping
from uuid import UUID


async def validate_compiler_identity_lanes_seeded(
    *,
    index: object,
    store: object,
) -> None:
    """Validate compiler-owned OCGI/OPGI identity lanes are commit-backed.

    Environment hosts use this as a read-only readiness gate over the Meta SDK
    lane store. The helper intentionally does not synthesize missing identities:
    runtime bundles must carry compiler-attached OCGI/OPGI truth.
    """

    ocg = _required_attr(index, "ocg", label="graph catalog")
    opgs = tuple(getattr(ocg, "object_projection_graphs", ()) or ())

    ocgi_seed_opg = _required_named_opg(
        opgs,
        "ObjectConfigGraphIdentity",
    )
    opgi_seed_opg = _required_named_opg(
        opgs,
        "ObjectProjectionGraphIdentity",
    )

    ocgi = getattr(ocg, "object_config_graph_identity", None)
    ocgi_id = _optional_uuid(getattr(ocgi, "id", None)) if ocgi is not None else None
    if ocgi is None or ocgi_id is None:
        raise RuntimeError(
            "Missing required OCGI on runtime bundle (compiler must attach it)"
        )

    await _require_lane_head(
        store=store,
        branch_id=ocgi_id,
        projection_hash=_projection_hash(ocgi_seed_opg),
        lane_label="OCGI identity lane",
    )

    for opg in opgs:
        projection_name = str(getattr(opg, "name", "") or "").strip()
        if not projection_name:
            continue

        opgi = _resolve_attached_opgi(ocgi=ocgi, opg=opg)
        opgi_id = (
            _optional_uuid(getattr(opgi, "id", None)) if opgi is not None else None
        )
        if opgi is None or opgi_id is None:
            raise RuntimeError(
                "Missing required OPGI on runtime bundle (compiler must attach it): "
                + f"projection_name={projection_name!r} "
                + f"projection_hash={_projection_hash(opg)}"
            )

        await _require_lane_head(
            store=store,
            branch_id=opgi_id,
            projection_hash=_projection_hash(opgi_seed_opg),
            lane_label="OPGI identity lane",
            projection_name=projection_name,
        )


def _required_attr(target: object, attr_name: str, *, label: str) -> object:
    value = getattr(target, attr_name, None)
    if value is None:
        raise RuntimeError(f"Missing required {attr_name} on {label}.")
    return value


def _required_named_opg(opgs: tuple[object, ...], name: str) -> object:
    for opg in opgs:
        if str(getattr(opg, "name", "") or "").strip() == name:
            if not _projection_hash(opg):
                break
            return opg
    raise RuntimeError(f"Missing required OPG in runtime bundle: {name}")


def _projection_hash(opg: object) -> str:
    return str(getattr(opg, "projection_hash", "") or "").strip()


def _resolve_attached_opgi(*, ocgi: object, opg: object) -> object | None:
    opg_id = _optional_uuid(getattr(opg, "id", None))
    if opg_id is None:
        return None

    direct = getattr(opg, "object_projection_graph_identity", None)
    if _optional_uuid(getattr(direct, "object_projection_graph_id", None)) == opg_id:
        return direct

    ocgi_id = _optional_uuid(getattr(ocgi, "id", None))
    container_candidate: object | None = None
    for candidate in getattr(ocgi, "object_projection_graph_identities", ()) or ():
        if (
            _optional_uuid(getattr(candidate, "object_projection_graph_id", None))
            != opg_id
        ):
            continue
        candidate_ocgi_id = _optional_uuid(
            getattr(candidate, "object_config_graph_identity_id", None)
        )
        if candidate_ocgi_id is not None and candidate_ocgi_id != ocgi_id:
            return candidate
        if container_candidate is None:
            container_candidate = candidate
    return container_candidate


async def _require_lane_head(
    *,
    store: object,
    branch_id: UUID,
    projection_hash: str,
    lane_label: str,
    projection_name: str | None = None,
) -> None:
    reader = getattr(store, "head", None)
    if not callable(reader):
        raise TypeError("Meta lane store must expose head().")

    head = reader(branch_id=branch_id, projection_hash=projection_hash)
    if inspect.isawaitable(head):
        head = await head

    head_commit_id = _payload_uuid(head, "commit_id") if head is not None else None
    if head_commit_id is None:
        message = (
            f"Missing compiler-owned {lane_label} HEAD (no commit). "
            + f"branch_id={branch_id} projection_hash={projection_hash}"
        )
        if projection_name is not None:
            message += f" projection_name={projection_name!r}"
        raise RuntimeError(message)

    head_oig_id = (
        _payload_uuid(head, "object_instance_graph_id") if head is not None else None
    )
    if head_oig_id is not None and head_oig_id != branch_id:
        raise RuntimeError(
            f"{lane_label} head has mismatched object_instance_graph_id: "
            + f"branch_id={branch_id} head_object_instance_graph_id={head_oig_id}"
        )


def _payload_uuid(payload: object, key: str) -> UUID | None:
    if isinstance(payload, Mapping):
        return _optional_uuid(payload.get(key))
    return _optional_uuid(getattr(payload, key, None))


def _optional_uuid(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return UUID(value)
        except ValueError:
            return None
    return None


__all__ = ["validate_compiler_identity_lanes_seeded"]
