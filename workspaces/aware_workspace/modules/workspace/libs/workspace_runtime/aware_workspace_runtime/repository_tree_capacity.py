"""Pre-spend envelope bounds; descriptive arithmetic never supplies authority."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from typing import Any

from aware_file_system import retained_tree_projection as native
from aware_workspace_sdk.repository_tree_projection import (
    WorkspaceTreeProjectionRefusal,
)
from aware_workspace_sdk.repository_tree_projection_codec import (
    repository_tree_projection_value_clone,
)
from aware_workspace_sdk.repository_tree_projection_values import (
    MAX_TREE_METADATA_BYTES,
    MAX_TREE_RECEIPTS,
    MAX_TREE_SUBEFFECTS,
    WorkspaceTreeProjectionBinding,
)

_NATIVE_TYPES = (
    native.ConfinedTreeCapacityForecast,
    native.ConfinedTreeCapacitySchedule,
    native.ConfinedTreeEncodingBounds,
    native.ConfinedTreePrefixCapacity,
)
_SLOTS = tuple(
    (cls, tuple((f.name, vars(cls)[f.name]) for f in fields(cls)))
    for cls in _NATIVE_TYPES
)
_FORECAST = vars(native.RetainedPhysicalTreeProjection)["observe_capacity_forecast"]
_FORECAST_CODE = _FORECAST.__code__
_FORECAST_DEFAULTS = _FORECAST.__defaults__
_FORECAST_KWDEFAULTS = _FORECAST.__kwdefaults__
_HANDLE_TYPE = native.RetainedPhysicalTreeProjection
_UINT64 = 2**64 - 1


@dataclass(frozen=True, slots=True)
class TreeCapacityBound:
    metadata_bytes: int
    resource_table_rows: int
    logical_resource_references: int
    completed_prefix: int


def _refuse() -> None:
    raise WorkspaceTreeProjectionRefusal("physical_refused")


def _wire(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def require_forecast_origin(method: object) -> None:
    """Check the definition-time original before dispatch; never execute a replacement."""
    if (
        native.RetainedPhysicalTreeProjection is not _HANDLE_TYPE
        or method is not _FORECAST
        or vars(_HANDLE_TYPE).get("observe_capacity_forecast") is not _FORECAST
        or _FORECAST.__code__ is not _FORECAST_CODE
        or _FORECAST.__defaults__ is not _FORECAST_DEFAULTS
        or _FORECAST.__kwdefaults__ is not _FORECAST_KWDEFAULTS
    ):
        _refuse()
    for cls, slots in _SLOTS:
        if vars(native).get(cls.__name__) is not cls or any(
            vars(cls).get(name) is not descriptor for name, descriptor in slots
        ):
            _refuse()


def _record(value: object, index: int) -> dict[str, Any]:
    cls, slots = _SLOTS[index]
    if type(value) is not cls:
        _refuse()
    try:
        return {name: descriptor.__get__(value, cls) for name, descriptor in slots}
    except AttributeError:
        _refuse()
        raise AssertionError("unreachable") from None


def _integers(row: dict[str, Any], excluded: tuple[str, ...] = ()) -> None:
    for name, value in row.items():
        if name not in excluded and (
            type(value) is not int or not 0 <= value <= _UINT64
        ):
            _refuse()


def validate_forecast(
    value: object, binding: WorkspaceTreeProjectionBinding
) -> dict[str, Any]:
    """Read only authenticated native slot descriptors, before JSON or comparisons."""
    require_forecast_origin(_FORECAST)
    binding = repository_tree_projection_value_clone(binding)
    row = _record(value, 0)
    _integers(
        row,
        (
            "schema",
            "preparation_ref",
            "request_ref",
            "request_digest",
            "root_identity",
            "transition_order",
            "schedule",
            "encoding",
            "prefixes",
        ),
    )
    for name in ("schema", "preparation_ref", "request_ref", "request_digest"):
        if type(row[name]) is not str:
            _refuse()
    root = row["root_identity"]
    order = row["transition_order"]
    count = binding.transition_count
    if (
        type(root) is not tuple
        or len(root) != 2
        or any(type(i) is not int or not 0 <= i <= _UINT64 for i in root)
    ):
        _refuse()
    if type(order) is not tuple or len(order) != count:
        _refuse()
    expected = tuple(
        (i, r.path, "directory_" + r.intent) for i, r in enumerate(binding.ancestors)
    ) + tuple(
        (i, r.path, r.kind) for i, r in enumerate(binding.files, len(binding.ancestors))
    )
    for item in order:
        if (
            type(item) is not tuple
            or len(item) != 3
            or (
                type(item[0]) is not int
                or type(item[1]) is not str
                or type(item[2]) is not str
            )
        ):
            _refuse()
    if (
        row["schema"] != "aware.filesystem.tree-capacity-forecast.v1"
        or row["preparation_ref"] != binding.physical_preparation_ref
        or row["request_ref"] != binding.physical_request_ref
        or row["request_digest"] != binding.physical_request_digest
        or root != binding.target_root_identity
        or order != expected
    ):
        _refuse()
    schedule = _record(row["schedule"], 1)
    _integers(schedule, ("profile",))
    if type(schedule["profile"]) is not str or schedule != {
        "profile": "native_tree_c_capacity_v1",
        "full_validation_calls_remaining": 1,
        "ordinal_validation_calls_remaining": count,
        "transition_calls_remaining": count,
        "finish_calls_remaining": 1,
        "consumed_validation_calls_remaining": 2,
        "release_attempts_remaining": 1,
    }:
        _refuse()
    encoding = _record(row["encoding"], 2)
    _integers(encoding)
    for name, expected_int in (
        ("maximum_ledger_diagnostics", 16),
        ("maximum_uncertain_resource_rows", 65),
        ("maximum_dispositions_per_resource", 5),
        ("maximum_subeffects_per_transition", 16),
        ("native_history_copy_count", 2),
    ):
        if encoding[name] != expected_int:
            _refuse()
    prefixes = row["prefixes"]
    if type(prefixes) is not tuple or len(prefixes) != count + 1:
        _refuse()
    converted = []
    for ordinal, prefix in enumerate(prefixes):
        p = _record(prefix, 3)
        _integers(p)
        if (
            p["completed_prefix"] != ordinal
            or not row["observed_acquisition_rows"]
            <= p["maximum_acquisition_history_rows"]
            <= row["observed_acquisition_rows"] + row["remaining_acquisition_rows"]
            or not row["observed_scratch_rows"]
            <= p["maximum_scratch_history_rows"]
            <= row["observed_scratch_rows"] + row["remaining_scratch_rows"]
            or p["maximum_resource_variant_rows"]
            < p["maximum_acquisition_history_rows"] + p["maximum_scratch_history_rows"]
            or p["maximum_effect_rows"] > ordinal * MAX_TREE_SUBEFFECTS
            or p["terminal_extra_resource_variant_rows"]
            < p["terminal_extra_acquisition_rows"]
        ):
            _refuse()
        if converted and any(
            p[name] < converted[-1][name]
            for name in (
                "maximum_acquisition_history_rows",
                "maximum_scratch_history_rows",
                "maximum_effect_rows",
                "maximum_effect_wire_bytes",
            )
        ):
            _refuse()
        converted.append(p)
    row.update(schedule=schedule, encoding=encoding, prefixes=converted)
    if row["forecast_wire_bytes"] != len(_wire(row)):
        _refuse()
    return row


_VALIDATOR_ORIGIN = (
    validate_forecast,
    validate_forecast.__code__,
    validate_forecast.__defaults__,
    validate_forecast.__kwdefaults__,
)


def enforce_capacity(bound: TreeCapacityBound, metadata_limit: int) -> None:
    if (
        type(bound) is not TreeCapacityBound
        or type(metadata_limit) is not int
        or not (0 < metadata_limit <= MAX_TREE_METADATA_BYTES)
    ):
        _refuse()
    if any(
        type(i) is not int or i < 0
        for i in (
            bound.metadata_bytes,
            bound.resource_table_rows,
            bound.logical_resource_references,
            bound.completed_prefix,
        )
    ):
        _refuse()
    if (
        bound.metadata_bytes > metadata_limit
        or bound.resource_table_rows > MAX_TREE_RECEIPTS
        or bound.logical_resource_references > MAX_TREE_RECEIPTS * 512
    ):
        raise WorkspaceTreeProjectionRefusal("quota_exceeded")


def capacity_bound(
    forecast: object, binding: WorkspaceTreeProjectionBinding
) -> TreeCapacityBound:
    """Bound every prefix carrier, including a last failed ordinal and duplicated refusal cleanup.

    Native resource order is original acquisition order followed by scratch order.
    Completed snapshots are prefixes of these two sequences; only the root can
    change after an already-completed snapshot. Terminal changed/uncertain rows
    are charged once. This is the existing codec's range transformation, not a
    second native lifecycle compiler. All logical references are charged regardless
    of whether the encoder selects plain or compact representation.
    """
    validator, code, defaults, kwdefaults = _VALIDATOR_ORIGIN
    if (
        validate_forecast is not validator
        or validator.__code__ is not code
        or validator.__defaults__ is not defaults
        or validator.__kwdefaults__ is not kwdefaults
    ):
        _refuse()
    # Dispatch the captured original, never reread the replaceable export.
    f = validator(forecast, binding)
    binding = repository_tree_projection_value_clone(binding)
    e = f["encoding"]
    # Workspace has four independent disposal owners (physical, retention,
    # capture and session). Keep their uncertain/error carriers and variants.
    own_resource_rows = 8
    own_resource_bytes = own_resource_rows * (128 + 1024)
    diagnostics_bytes = (
        130 + e["maximum_ledger_diagnostics"] * e["maximum_diagnostic_bytes"]
    )
    common = (
        len(_wire(asdict(binding))) + f["forecast_wire_bytes"] + 2 * own_resource_bytes
    )
    # Full outer result + resolution/refusal wrapper and two top-level cleanup
    # carriers; unknown enum widths and bounded owner diagnostics are included.
    common += 4096 + 3 * diagnostics_bytes
    prefix_receipt_bytes = 0
    prefix_references = 0
    prefix_range_bytes = 0
    prefix_minimum_references = 0
    started_scratch = 0
    scratch_ordinals = {r.ordinal for r in binding.scratch_effects}
    peak_wire = peak_rows = peak_references = peak_prefix = 0
    span_bytes = len(_wire([MAX_TREE_RECEIPTS - 1, MAX_TREE_RECEIPTS])) + 1
    # Future hashes are content digests; UUID correlations are fixed-width.
    consumption = "issue-tree-consumption:" + "f" * 32
    digest_ref = "workspace-repository-mutation-receipt:sha256:" + "f" * 64
    receipt_sizes = []
    originals = (*binding.ancestors, *binding.files)
    for index, path, kind in f["transition_order"]:
        receipt_sizes.append(
            len(
                _wire(
                    {
                        "binding_ref": binding.binding_ref,
                        "invocation_ref": binding.invocation_ref,
                        "consumption_ref": consumption,
                        "physical_preparation_ref": binding.physical_preparation_ref,
                        "ordinal": index,
                        "path": path,
                        "kind": kind,
                        "physical_effects": [],
                        "before": None,
                        "after": None,
                        "mutation_receipt_ref": digest_ref,
                        "capture_ref": digest_ref,
                        "delta_ref": digest_ref,
                        "effect_state": "unknown",
                        "completion_state": "incomplete",
                        "durability_confirmed": False,
                        "convergence_state": "not_verified",
                        "body_retention_state": "unavailable",
                        "index_state": "not_attempted",
                        "error_refs": [],
                        "cleanup": {
                            "binding_ref": None,
                            "resources": {"ranges": []},
                            "residual_scratch": [],
                            "cleanup_state": "not_attempted",
                            "ledger_complete": False,
                            "diagnostics": [],
                        },
                    }
                )
            )
            + len(_wire(asdict(originals[index].before)))
            + e["maximum_pin_bytes"]
            + 1
        )
    for ordinal, p in enumerate(f["prefixes"]):
        if ordinal:
            prefix_receipt_bytes += receipt_sizes[ordinal - 1]
            rows = (
                p["maximum_acquisition_history_rows"]
                + p["maximum_scratch_history_rows"]
            )
            prefix_references += rows
            changed = p["maximum_resource_variant_rows"] - rows
            prefix_range_bytes += (3 + 2 * changed) * span_bytes
            if ordinal - 1 in scratch_ordinals:
                started_scratch += 1
            prefix_minimum_references += 1 + started_scratch
        # Include one partially returned failing transition. Completed receipts
        # never acquire the terminal branch's error/held-row variants retroactively.
        terminal_rows = p["terminal_extra_resource_variant_rows"]
        resources = (
            p["maximum_resource_variant_rows"] + terminal_rows + own_resource_rows
        )
        final_rows = (
            p["maximum_acquisition_history_rows"]
            + p["maximum_scratch_history_rows"]
            + terminal_rows
        )
        failed = ordinal < binding.transition_count
        failure_receipt = (
            (
                receipt_sizes[ordinal]
                + MAX_TREE_SUBEFFECTS * e["maximum_effect_record_bytes"]
                + p["terminal_extra_wire_bytes"]
            )
            if failed
            else 0
        )
        references = prefix_references + 2 * (final_rows + own_resource_rows)
        if failed:
            references += final_rows
        table_bytes = (
            p["maximum_cleanup_wire_bytes"]
            + p["terminal_extra_wire_bytes"]
            + p["release_extra_wire_bytes"]
            + (terminal_rows + 1) * e["maximum_resource_record_bytes"]
        )
        ranges = (
            prefix_range_bytes
            + (2 + int(failed))
            * (3 + 2 * terminal_rows + own_resource_rows)
            * span_bytes
        )
        wire = (
            common
            + prefix_receipt_bytes
            + p["maximum_effect_wire_bytes"]
            + p["maximum_postimage_wire_bytes"]
            + failure_receipt
            + table_bytes
            + ranges
            + MAX_TREE_SUBEFFECTS * e["maximum_error_reference_bytes"]
        )
        # The encoder chooses by ACTUAL references, not our upper bound.
        # Until the original completed root/scratch history forces compact,
        # also bound any legal plain carrier (at most 8,192 resource references).
        if prefix_minimum_references + 1 <= MAX_TREE_RECEIPTS:
            plain_wire = (
                common
                + prefix_receipt_bytes
                + p["maximum_effect_wire_bytes"]
                + p["maximum_postimage_wire_bytes"]
                + failure_receipt
                + min(references, MAX_TREE_RECEIPTS)
                * e["maximum_resource_record_bytes"]
                + MAX_TREE_SUBEFFECTS * e["maximum_error_reference_bytes"]
            )
            wire = max(wire, plain_wire)
        peak_rows = max(peak_rows, resources)
        peak_references = max(peak_references, references)
        if wire > peak_wire:
            peak_wire, peak_prefix = wire, ordinal
    return TreeCapacityBound(peak_wire, peak_rows, peak_references, peak_prefix)
