"""V5 occurrence metadata and historical HEAD reads, without lineage authority.

An installed original issuer must independently validate protection, admission,
retirement and owner currentness. This component performs no CAS, reservation,
approval, Meta read or history traversal. An absent row never establishes genesis.
"""

from __future__ import annotations

import inspect
import json
from types import FunctionType, MethodType
from typing import cast

from aware_code_semantic_contract_runtime import ContentDigest, canonical_json_bytes
from aware_local_service_runtime import LocalOperationalStateRecord
from aware_local_service_runtime.contracts import _FrozenJsonArray, _FrozenJsonObject

from . import materialization_head_v5 as head_wire
from . import semantic_materialization_publication as publication

RECORD_CONTRACT = "aware.workspace.semantic-materialization-occurrence-record.v5"
CHECKPOINT_CONTRACT = "aware.workspace.semantic-materialization-lineage-checkpoint.v1"
_RECORD_FIELDS = frozenset(
    (
        "contract",
        "installation_digest",
        "occurrence_key",
        "occurrence",
        "incarnation_ref",
        "record_revision",
        "previous_record_digest",
        "state_tag",
        "public_head",
        "pending_operation",
        "confirmation",
        "retirement",
        "checkpoint",
        "record_digest",
    )
)
_PENDING_FIELDS = frozenset(
    (
        "operation_ref",
        "operation_digest",
        "idempotency_key",
        "source_epoch_digest",
        "expected_prior_record_revision",
        "expected_prior_head_digest",
        "claimed_prior_meta_pair_digest",
        "committed_meta_pair_digest",
        "proposed_head_digest",
        "phase",
    )
)
_CONFIRMATION_FIELDS = frozenset(
    (
        "operation_ref",
        "head_cas_revision",
        "head_digest",
        "head_wire_digest",
        "head_reread_evidence_digest",
        "meta_pair_body_digest",
        "source_epoch_digest",
    )
)
_RETIREMENT_FIELDS = frozenset(
    (
        "operation_ref",
        "operation_digest",
        "expected_head_digest",
        "terminal_meta_pair_body_digest",
        "declaration_evidence_digest",
        "reason",
    )
)
_MAX_RECORD_BYTES = 65_536


def _integer(value: object, *, zero: bool = False) -> int:
    if (
        type(value) is not int
        or not (0 if zero else 1) <= value <= publication._V5_MAX_INTEGER
    ):
        head_wire._reject("V5 occurrence exact bounded revision required")
    return value


def _optional_digest(value: object) -> str | None:
    return None if value is None else publication._v5_sha(value)


def _pending(value: object, *, revision: int) -> dict[str, object]:
    fields = publication._v5_fields(value, _PENDING_FIELDS)
    result: dict[str, object] = {
        "operation_ref": publication._v5_text(fields["operation_ref"], 192, token=True),
        "operation_digest": publication._v5_sha(fields["operation_digest"]),
        "idempotency_key": publication._v5_text(
            fields["idempotency_key"], 192, token=True
        ),
        "source_epoch_digest": publication._v5_sha(fields["source_epoch_digest"]),
        "expected_prior_record_revision": _integer(
            fields["expected_prior_record_revision"], zero=True
        ),
        **{
            name: _optional_digest(fields[name])
            for name in (
                "expected_prior_head_digest",
                "claimed_prior_meta_pair_digest",
                "committed_meta_pair_digest",
                "proposed_head_digest",
            )
        },
        "phase": publication._v5_text(fields["phase"], 192, token=True),
    }
    if cast(int, result["expected_prior_record_revision"]) >= revision:
        head_wire._reject("V5 pending prior revision must precede stored record")
    if (result["expected_prior_head_digest"] is None) != (
        result["claimed_prior_meta_pair_digest"] is None
    ):
        head_wire._reject("V5 pending predecessor head/pair must agree")
    phase = result["phase"]
    if phase not in ("reserved", "meta_committed", "head_stored"):
        head_wire._reject("V5 pending phase differs")
    if (phase == "reserved") != (result["committed_meta_pair_digest"] is None):
        head_wire._reject("V5 pending committed pair differs from phase")
    if (phase == "head_stored") != (result["proposed_head_digest"] is not None):
        head_wire._reject("V5 pending proposed HEAD differs from phase")
    return result


def _confirmation(value: object, *, revision: int) -> dict[str, object]:
    fields = publication._v5_fields(value, _CONFIRMATION_FIELDS)
    result: dict[str, object] = {
        "operation_ref": publication._v5_text(fields["operation_ref"], 192, token=True),
        "head_cas_revision": _integer(fields["head_cas_revision"]),
        **{
            name: publication._v5_sha(fields[name])
            for name in _CONFIRMATION_FIELDS - {"operation_ref", "head_cas_revision"}
        },
    }
    if cast(int, result["head_cas_revision"]) >= revision:
        head_wire._reject("V5 confirmation must follow its public HEAD CAS")
    return result


def _retirement(value: object) -> dict[str, object]:
    fields = publication._v5_fields(value, _RETIREMENT_FIELDS)
    result: dict[str, object] = {
        "operation_ref": publication._v5_text(fields["operation_ref"], 192, token=True),
        "reason": publication._v5_text(fields["reason"], 192, token=True),
        **{
            name: publication._v5_sha(fields[name])
            for name in _RETIREMENT_FIELDS - {"operation_ref", "reason"}
        },
    }
    if result["reason"] not in (
        "declaration_nonmembership",
        "explicit_owner_retirement",
    ):
        head_wire._reject("V5 retirement reason differs")
    return result


def _workspace_binding(
    value: object, *, role: str, owner: str, maximum: int
) -> dict[str, object]:
    binding = head_wire._binding(value, role=role)
    if binding["owner_contract"] != owner or cast(int, binding["body_size"]) > maximum:
        head_wire._reject("V5 occurrence binding contract or size differs")
    return binding


def encode_record(value: object) -> bytes:
    """Validate detached record meaning; never authenticate its protected store."""
    fields = publication._v5_fields(value, _RECORD_FIELDS)
    # Native-type checks use `is`, before the older shared metadata validator.
    # Foreign metaclass equality must never run during type-tuple membership.
    fields = cast(dict[str, object], _plain_state_value(fields))
    head_wire._native(fields, metadata_tokens=True)
    if fields["contract"] != RECORD_CONTRACT:
        head_wire._reject("V5 occurrence record contract differs")
    revision = _integer(fields["record_revision"])
    previous = _optional_digest(fields["previous_record_digest"])
    if (revision == 1) != (previous is None):
        head_wire._reject("V5 occurrence preceding record link differs")
    occurrence = json.loads(publication._encode_v5_occurrence(fields["occurrence"]))
    key = publication._v5_sha(fields["occurrence_key"])
    if key != publication._v5_occurrence_key(occurrence):
        head_wire._reject("V5 occurrence key differs from exact occurrence")
    state = publication._v5_text(fields["state_tag"], 192, token=True)
    if state not in (
        "reserved_genesis",
        "reserved_successor",
        "active_pending",
        "active",
        "retired",
    ):
        head_wire._reject("V5 occurrence state differs")
    pending_states = ("reserved_genesis", "reserved_successor", "active_pending")
    for name, present in (
        ("public_head", state != "reserved_genesis"),
        ("pending_operation", state in pending_states),
        ("confirmation", state in ("active", "retired")),
        ("retirement", state == "retired"),
    ):
        if (fields[name] is not None) != present:
            head_wire._reject("V5 occurrence state field presence differs")
    public_head = (
        None
        if fields["public_head"] is None
        else _workspace_binding(
            fields["public_head"],
            role="public_v5_head",
            owner=head_wire.HEAD_CONTRACT,
            maximum=262_144,
        )
    )
    pending = (
        None
        if fields["pending_operation"] is None
        else _pending(fields["pending_operation"], revision=revision)
    )
    confirmation = (
        None
        if fields["confirmation"] is None
        else _confirmation(fields["confirmation"], revision=revision)
    )
    retirement = (
        None if fields["retirement"] is None else _retirement(fields["retirement"])
    )
    if pending is not None:
        if (
            state == "reserved_genesis"
            and pending["expected_prior_head_digest"] is not None
        ):
            head_wire._reject("V5 genesis must have typed-empty prior head/pair")
        if state == "reserved_successor" and (
            pending["expected_prior_head_digest"] is None
            or public_head is None
            or pending["expected_prior_head_digest"] != public_head["coordinate_digest"]
        ):
            head_wire._reject("V5 successor must retain the exact historical HEAD")
        if (state == "active_pending") != (pending["phase"] == "head_stored"):
            head_wire._reject("V5 stored HEAD state differs from pending phase")
        if state == "active_pending" and (
            public_head is None
            or pending["proposed_head_digest"] != public_head["coordinate_digest"]
        ):
            head_wire._reject("V5 active-pending HEAD differs from proposed HEAD")
    if confirmation is not None and (
        public_head is None
        or (
            confirmation["head_digest"] != public_head["coordinate_digest"]
            or confirmation["head_wire_digest"] != public_head["body_digest"]
        )
    ):
        head_wire._reject("V5 confirmation differs from stored HEAD binding")
    if retirement is not None and (
        public_head is None
        or retirement["expected_head_digest"] != public_head["coordinate_digest"]
    ):
        head_wire._reject("V5 retirement differs from terminal HEAD")
    checkpoint = (
        None
        if fields["checkpoint"] is None
        else _workspace_binding(
            fields["checkpoint"],
            role="lineage_checkpoint",
            owner=CHECKPOINT_CONTRACT,
            maximum=16_384,
        )
    )
    payload: dict[str, object] = {
        "contract": RECORD_CONTRACT,
        "installation_digest": publication._v5_sha(fields["installation_digest"]),
        "occurrence_key": key,
        "occurrence": occurrence,
        "incarnation_ref": publication._v5_text(
            fields["incarnation_ref"], 192, token=True
        ),
        "record_revision": revision,
        "previous_record_digest": previous,
        "state_tag": state,
        "public_head": public_head,
        "pending_operation": pending,
        "confirmation": confirmation,
        "retirement": retirement,
        "checkpoint": checkpoint,
    }
    digest = publication._v5_sha(fields["record_digest"])
    if digest != publication._v5_digest(RECORD_CONTRACT, payload):
        head_wire._reject("V5 occurrence record digest differs")
    body = canonical_json_bytes({**payload, "record_digest": digest})
    if len(body) > _MAX_RECORD_BYTES:
        head_wire._reject("V5 occurrence record byte bound")
    return body


def decode_record(body: bytes) -> dict[str, object]:
    value = publication._v5_decode(body, _MAX_RECORD_BYTES)
    if encode_record(value) != body:
        head_wire._reject("V5 occurrence record is not canonical")
    return cast(dict[str, object], value)


def _plain_state_value(value: object) -> object:
    """Detach only native JSON and Service's exact original frozen JSON types."""
    remaining = 20_000

    def visit(item: object, depth: int) -> object:
        nonlocal remaining
        remaining -= 1
        if remaining < 0 or depth > 20:
            head_wire._reject("V5 state JSON traversal bound")
        kind = type(item)
        if item is None or kind is str or kind is int or kind is bool or kind is float:
            return item
        if kind is dict or kind is _FrozenJsonObject:
            result: dict[str, object] = {}
            for key, row in dict[object, object].items(
                cast(dict[object, object], item)
            ):
                if type(key) is not str:
                    head_wire._reject("V5 state JSON exact key required")
                result[key] = visit(row, depth + 1)
            return result
        if kind is list or kind is _FrozenJsonArray:
            return [
                visit(row, depth + 1)
                for row in list[object].__iter__(cast(list[object], item))
            ]
        head_wire._reject("V5 exact state JSON required")

    return visit(value, 0)


def _head_correspondence(
    record: dict[str, object], body: bytes, *, expected_output_roles: tuple[str, ...]
) -> None:
    head = head_wire.decode_head(body, expected_output_roles=expected_output_roles)
    binding = cast(dict[str, object], record["public_head"])
    if (
        head["head_digest"] != binding["coordinate_digest"]
        or head["incarnation_ref"] != record["incarnation_ref"]
        or canonical_json_bytes(head["package_occurrence"])
        != canonical_json_bytes(record["occurrence"])
    ):
        head_wire._reject("V5 retained HEAD occurrence or domain differs")
    pair = cast(dict[str, object], head["meta_pair_binding"])
    pending = record["pending_operation"]
    if type(pending) is dict:
        if record["state_tag"] == "reserved_successor":
            if pair["body_digest"] != pending["claimed_prior_meta_pair_digest"]:
                head_wire._reject("V5 reserved predecessor pair differs")
        elif record["state_tag"] == "active_pending":
            base = cast(dict[str, object], head["base_head"])
            request = cast(dict[str, object], base["request"])
            if (
                head["operation_ref"] != pending["operation_ref"]
                or head["operation_digest"] != pending["operation_digest"]
                or head["source_epoch_digest"] != pending["source_epoch_digest"]
                or pair["body_digest"] != pending["committed_meta_pair_digest"]
                or head["predecessor_head_digest"]
                != pending["expected_prior_head_digest"]
                or request["expected_head_revision"]
                != pending["expected_prior_record_revision"]
            ):
                head_wire._reject("V5 stored HEAD differs from pending operation")
    confirmation = record["confirmation"]
    if type(confirmation) is dict and (
        head["operation_ref"] != confirmation["operation_ref"]
        or head["source_epoch_digest"] != confirmation["source_epoch_digest"]
        or pair["body_digest"] != confirmation["meta_pair_body_digest"]
    ):
        head_wire._reject("V5 stored HEAD differs from confirmation")
    retirement = record["retirement"]
    if (
        type(retirement) is dict
        and pair["body_digest"] != retirement["terminal_meta_pair_body_digest"]
    ):
        head_wire._reject("V5 retired terminal pair differs")


def read_head_data(
    publisher: object,
    occurrence: object,
    *,
    expected_output_roles: tuple[str, ...],
) -> tuple[bytes, bytes | None] | None:
    """Read bounded historical metadata/HEAD only; no installed/current authority.

    The original selected issuer must independently authenticate its protected
    store and fresh approval. Neither active/confirmed data nor absence opens
    predecessor access. In particular, this does not return V3/V4 admission DTOs.
    """
    entrances: list[tuple[object, str, FunctionType, MethodType]] = []
    try:
        if type(publisher) is not publication.WorkspaceSemanticMaterializationPublisher:
            head_wire._reject("V5 exact publisher required")
        if type(expected_output_roles) is not tuple or len(expected_output_roles) > 64:
            head_wire._reject("V5 exact bounded role inventory required")
        roles = tuple(
            publication._v5_text(role, 192, token=True)
            for role in expected_output_roles
        )
        if len(set(roles)) != len(roles):
            head_wire._reject("V5 unique role inventory required")
        namespace = object.__getattribute__(publisher, "_state_namespace")
        if type(namespace) is not str or namespace != publication._V5_STATE_NAMESPACE:
            head_wire._reject("V5 occurrence publisher namespace differs")
        occurrence_body = publication._encode_v5_occurrence(occurrence)
        key = publication._v5_occurrence_key(json.loads(occurrence_body))
        state: object = object.__getattribute__(publisher, "_state_store")
        bodies: object = object.__getattribute__(publisher, "_body_store")
        for receiver, name in ((state, "read"), (bodies, "read_body")):
            descriptor = inspect.getattr_static(type(receiver), name, None)
            if (
                type(descriptor) is not FunctionType
                or inspect.getattr_static(receiver, name, None) is not descriptor
            ):
                head_wire._reject("V5 historical reader entrance substituted")
            entrances.append(
                (receiver, name, descriptor, MethodType(descriptor, receiver))
            )

        def check() -> None:
            try:
                current_namespace = object.__getattribute__(
                    publisher, "_state_namespace"
                )
                if (
                    object.__getattribute__(publisher, "_state_store") is not state
                    or object.__getattribute__(publisher, "_body_store") is not bodies
                    or type(current_namespace) is not str
                    or current_namespace != namespace
                ):
                    head_wire._reject("V5 historical reader resources changed")
                for receiver, name, descriptor, _method in entrances:
                    if (
                        inspect.getattr_static(receiver, name, None) is not descriptor
                        or inspect.getattr_static(type(receiver), name, None)
                        is not descriptor
                    ):
                        head_wire._reject("V5 historical reader entrance substituted")

            finally:
                receiver = descriptor = _method = current_namespace = None

        def read_record() -> tuple[bytes, dict[str, object]] | None:
            check()
            original = entrances[0][3](namespace, key, include_deleted=True)
            check()
            if original is None:
                return None
            if type(original) is not LocalOperationalStateRecord:
                head_wire._reject("V5 exact state record required")
            if (
                original.namespace != namespace
                or original.key != key
                or original.deleted
                or original.value is None
            ):
                head_wire._reject("V5 state record address or retained value differs")
            body = encode_record(_plain_state_value(original.value))
            decoded = decode_record(body)
            if (
                type(original.revision) is not int
                or decoded["record_revision"] != original.revision
            ):
                head_wire._reject("V5 record revision differs from state store")
            if (
                decoded["occurrence_key"] != key
                or canonical_json_bytes(decoded["occurrence"]) != occurrence_body
            ):
                head_wire._reject("V5 stored occurrence differs from request")
            return body, decoded

        first = read_record()
        head_body = None
        if first is not None and first[1]["public_head"] is not None:
            binding = cast(dict[str, object], first[1]["public_head"])
            check()
            head_body = entrances[1][3](binding["body_ref"])
            check()
            if (
                type(head_body) is not bytes
                or len(head_body) != binding["body_size"]
                or ContentDigest.of_bytes(head_body).value != binding["body_digest"]
            ):
                head_wire._reject("V5 retained HEAD body differs")
            _head_correspondence(
                first[1], head_body, expected_output_roles=expected_output_roles
            )
        final = read_record()
        if (first is None) != (final is None) or (
            first is not None and final is not None and first[0] != final[0]
        ):
            head_wire._reject("V5 occurrence changed during historical HEAD read")
        return None if first is None else (first[0], head_body)
    finally:
        entrances.clear()
        publisher = occurrence = state = bodies = receiver = descriptor = None
        binding = first = final = head_body = None
        del expected_output_roles
