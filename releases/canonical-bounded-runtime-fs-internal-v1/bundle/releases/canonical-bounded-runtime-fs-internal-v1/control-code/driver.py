"""Bounded outer/retained-inner staging role for the original driver.

Qualified callers supply the genuine shared-loader module/handle and original
source request/plan. This is not a loader authenticator, installer, parser,
simultaneous filesystem snapshot or authority to execute the staged payload.
Both stage roots remain live for separately explicit original-owner release.
"""

from __future__ import annotations

import re
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROFILE = "aware.release.original-driver-staging.v1"
COMPACT_PROFILE = "aware.release.original-driver-compact-staging.v1"
RECORDED_PROFILE = "aware.release.original-driver-recorded-staging.v1"
COMPRESSED_PROFILE = "aware.release.original-driver-compressed-staging.v1"
BORROWED_PROFILE = "aware.release.original-driver-borrowed-directory-staging.v1"
RECEIPT_PROFILE = "aware.release.original-driver-observation-receipts.v1"
RETIRED_PROFILE = "aware.release.original-driver-retired-member-staging.v1"


@dataclass(frozen=True, slots=True, eq=False)
class DriverStagingRequest:
    original_loader: types.ModuleType
    source_handle: object
    outer_request: Any  # Exact class comes from the qualified captured owner.
    partitioned_plan: object
    retention_parent: Path
    payload_member: str
    payload_sha256: str
    maximum_outer_decoded_bytes: int
    maximum_inner_decoded_bytes: int
    operation_ref: str


@dataclass(frozen=True, slots=True, eq=False)
class DriverStagingResult:
    original_request: DriverStagingRequest
    original_plan_snapshot: tuple
    original_outer: object
    original_inner_request: object
    original_inner: object
    original_completion_validations: tuple
    original_root_bindings: tuple
    retained_source_and_notices: Path
    inner_directory: Path
    source_binding_retired: bool = False
    parent_cleanup: str = "not_released"
    authorizes_installation: bool = False


@dataclass
class _Attempt:
    request: object
    phase: str = "inputs"
    ports: list = field(default_factory=list)
    modules: dict = field(default_factory=dict)
    snapshot: tuple = ()
    request_snapshot: tuple = ()
    outer_source_snapshot: tuple = ()
    outer: Any = None
    inner_request: object = None
    inner: Any = None
    validations: list = field(default_factory=list)
    root_bindings: list = field(default_factory=list)


class DriverStagingError(RuntimeError):
    def __init__(self, attempt, cause):
        super().__init__("original_driver_staging_" + attempt.phase)
        self.original_attempt = attempt
        self.original_request = attempt.request
        self.original_plan_snapshot = attempt.snapshot
        self.original_outer = attempt.outer
        self.original_inner_request = attempt.inner_request
        self.original_inner = attempt.inner
        self.original_completion_validations = tuple(attempt.validations)
        self.original_root_bindings = tuple(attempt.root_bindings)
        self.original_cause = cause
        self.parent_cleanup = "not_released"
        self.authorizes_retry = self.authorizes_installation = False


def _request_snapshot(request):
    values = (
        request.original_loader,
        request.source_handle,
        request.outer_request,
        request.partitioned_plan,
        request.retention_parent,
        request.payload_member,
        request.payload_sha256,
        request.maximum_outer_decoded_bytes,
        request.maximum_inner_decoded_bytes,
        request.operation_ref,
    )
    return tuple(
        (type(value), id(value), value) if index < 5 else (type(value), value)
        for index, value in enumerate(values)
    )


def _source_snapshot(request):
    return tuple(
        (type(value), value)
        for value in (request.path, request.sha256, request.size_bytes)
    )


def _group_root(snapshot, namespace):
    group = next(value for value in snapshot if value[0] == namespace)
    roots = {pin[1].split("/", 1)[0] for _, members in group[1] for pin in members}
    if len(roots) != 1:
        raise ValueError("single_original_archive_root_required")
    return next(iter(roots))


def _current(attempt):
    request = attempt.request
    if _request_snapshot(request) != attempt.request_snapshot:
        raise ValueError("original_driver_staging_request_changed")
    for module, name, original in attempt.ports:
        if getattr(module, name) is not original:
            raise ValueError("original_driver_staging_port_changed")
    for name, original in attempt.modules.items():
        if (
            request.original_loader.bound_module(request.source_handle, name)
            is not original
        ):
            raise ValueError("original_driver_staging_module_changed")
    stage = attempt.modules["release.product_staging"]
    owner = attempt.modules["release.whole_envelope"]
    if (
        stage._snapshot(request.partitioned_plan) != attempt.snapshot
        or _source_snapshot(request.outer_request) != attempt.outer_source_snapshot
        or type(request.outer_request) is not owner.ArchiveBodyRequest
    ):
        raise ValueError("original_driver_staging_inputs_changed")


def _receive_group(attempt, value, namespace):
    stage = attempt.modules["release.product_staging"]
    owner = attempt.modules["release.whole_envelope"]
    request = attempt.request
    expected_source = (
        request.outer_request if namespace == "outer" else attempt.inner_request
    )
    maximum = (
        request.maximum_outer_decoded_bytes
        if namespace == "outer"
        else request.maximum_inner_decoded_bytes
    )
    if type(value) is not stage.StagedProductGroup:
        raise TypeError("original_driver_stage_return_required")
    if (
        value.original_plan_snapshot != attempt.snapshot
        or value.group_namespace != namespace
        or value.authorizes_installation is not False
        or value.parent_cleanup != "not_released"
        or value.original_request is not expected_source
        or value.original_flow.original_flow.original_member_account.root
        != _group_root(attempt.snapshot, namespace)
    ):
        raise ValueError("original_driver_stage_return_mismatch")
    binding = stage.root.validate_staging_root_binding(
        value.stage_handle,
        expected_absolute_root=str(request.retention_parent / namespace),
        expected_operation_ref=request.operation_ref + ":" + namespace,
        expected_partitioned_plan=request.partitioned_plan,
        expected_group_namespace=namespace,
    )
    attempt.root_bindings.append(binding)
    # Reuse the original IO-free source correlation. This temporary historical
    # check record is not enrolled and cannot authorize another flow or retry.
    stage.receiving._OriginalFlowReceiver._correlate(
        stage.receiving._Record(
            expected_source,
            owner._guarded_file_snapshot(expected_source),
            maximum,
            returned=value.original_flow.original_flow.original_flow,
        )
    )
    if (
        value.original_preparation.handle is not value.stage_handle
        or value.original_preparation.request_digest != binding.request_digest
        or value.original_preparation.plan_digest != binding.plan_digest
    ):
        raise ValueError("original_driver_preparation_binding_mismatch")
    original = stage.complete.validate_stage_completion(
        value.stage_handle,
        expected_request_digest=binding.request_digest,
        expected_plan_digest=binding.plan_digest,
    )
    attempt.validations.append(original)
    if original != value.original_completion or original.group_namespace != namespace:
        raise ValueError("original_driver_completion_mismatch")


def stage_for_original_driver(request, *, profile, explicit_staging_intent):
    """Complete outer staging before consuming its exact retained payload.

    No install.sh, venv, pip, native loading, implicit cleanup or module retirement.
    Failure retains both earlier effects and original failed-owner handles/errors.
    """
    attempt = _Attempt(request)
    try:
        if (
            type(request) is not DriverStagingRequest
            or type(profile) is not str
            or profile
            not in (
                PROFILE,
                COMPACT_PROFILE,
                RECORDED_PROFILE,
                COMPRESSED_PROFILE,
                BORROWED_PROFILE,
                RETIRED_PROFILE,
                RECEIPT_PROFILE,
            )
            or explicit_staging_intent is not True
            or type(request.original_loader) is not types.ModuleType
            or type(request.retention_parent) is not type(Path())
            or not request.retention_parent.is_absolute()
            or ".." in request.retention_parent.parts
            or type(request.payload_member) is not str
            or type(request.payload_sha256) is not str
            or re.fullmatch("[0-9a-f]{64}", request.payload_sha256) is None
            or type(request.operation_ref) is not str
            or type(request.maximum_outer_decoded_bytes) is not int
            or request.maximum_outer_decoded_bytes <= 0
            or type(request.maximum_inner_decoded_bytes) is not int
            or request.maximum_inner_decoded_bytes <= 0
        ):
            raise ValueError("explicit_original_driver_staging_inputs_required")
        attempt.request_snapshot = _request_snapshot(request)
        loader = request.original_loader
        attempt.ports.append((loader, "bound_module", loader.bound_module))
        for name in ("release.product_staging", "release.whole_envelope"):
            attempt.modules[name] = loader.bound_module(request.source_handle, name)
        stage, owner = (
            attempt.modules[name]
            for name in ("release.product_staging", "release.whole_envelope")
        )
        observation_options = {}
        if profile == RECEIPT_PROFILE:
            if request.source_handle is None:
                raise ValueError("original_receipt_source_handle_required")
            # These exact owner ports are retained/rechecked alongside all
            # existing driver ports. They neither read nor renew guards.
            for module, name in (
                (stage.member, "CLOSED_TERMINAL_PROFILE"),
                (stage.complete.entry, "OBSERVATION_RECEIPT_PROFILE"),
                (stage.complete.entry, "validate_confined_entry_receipt"),
                (stage.complete.entry, "confined_entry_receipt_seal"),
                (stage.complete.entry, "confined_entry_receipt_coordinate"),
            ):
                attempt.ports.append((module, name, getattr(module, name)))
            observation_options = {
                "observation_profile": stage.complete.entry.OBSERVATION_RECEIPT_PROFILE
            }
        staging_profile = (
            stage.RETIRED_PROFILE
            if profile in (RETIRED_PROFILE, RECEIPT_PROFILE)
            else stage.BORROWED_PROFILE
            if profile in (BORROWED_PROFILE, RETIRED_PROFILE)
            else stage.COMPRESSED_PROFILE
            if profile == COMPRESSED_PROFILE
            else stage.RECORDED_PROFILE
            if profile == RECORDED_PROFILE
            else stage.COMPACT_PROFILE
            if profile == COMPACT_PROFILE
            else stage.PROFILE
        )
        if profile in (
            COMPACT_PROFILE,
            RECORDED_PROFILE,
            COMPRESSED_PROFILE,
            BORROWED_PROFILE,
            RETIRED_PROFILE,
            RECEIPT_PROFILE,
        ):
            for module, name in (
                (
                    stage,
                    "RETIRED_PROFILE"
                    if profile in (RETIRED_PROFILE, RECEIPT_PROFILE)
                    else "BORROWED_PROFILE"
                    if profile in (BORROWED_PROFILE, RETIRED_PROFILE)
                    else "COMPRESSED_PROFILE"
                    if profile == COMPRESSED_PROFILE
                    else "RECORDED_PROFILE"
                    if profile == RECORDED_PROFILE
                    else "COMPACT_PROFILE",
                ),
                (stage.member, "PROGRESS_PROFILE"),
                (stage.member, "validate_member_progress"),
            ):
                attempt.ports.append((module, name, getattr(module, name)))
        if type(request.outer_request) is not owner.ArchiveBodyRequest:
            raise TypeError("original_outer_request_required")
        for module, name in (
            (stage, "stage_product_group"),
            (stage, "_snapshot"),
            (stage, "complete"),
            (stage, "root"),
            (stage, "receiving"),
            (stage, "StagedProductGroup"),
            (owner, "ArchiveBodyRequest"),
            (owner, "_guarded_file_snapshot"),
            (stage.root, "validate_staging_root_binding"),
            (stage.receiving, "_Record"),
            (stage.receiving, "_OriginalFlowReceiver"),
            (stage.receiving._OriginalFlowReceiver, "_correlate"),
            (stage.complete, "validate_stage_completion"),
        ):
            attempt.ports.append((module, name, getattr(module, name)))
        attempt.snapshot = stage._snapshot(request.partitioned_plan)
        if tuple(group[0] for group in attempt.snapshot) != ("outer", "inner"):
            raise ValueError("explicit_outer_then_inner_groups_required")
        attempt.outer_source_snapshot = _source_snapshot(request.outer_request)
        _current(attempt)
        attempt.phase = "outer"
        attempt.outer = stage.stage_product_group(
            request.outer_request,
            profile=staging_profile,
            absolute_root=str(request.retention_parent / "outer"),
            operation_ref=request.operation_ref + ":outer",
            partitioned_plan=request.partitioned_plan,
            group_namespace="outer",
            maximum_decoded_bytes=request.maximum_outer_decoded_bytes,
            explicit_create_intent=True,
            **observation_options,
        )
        _current(attempt)
        _receive_group(attempt, attempt.outer, "outer")
        outer_root = _group_root(attempt.snapshot, "outer")
        member_path = outer_root + "/" + request.payload_member
        pins = [
            pin
            for _, members in attempt.snapshot[0][1]
            for pin in members
            if pin[1] == member_path
        ]
        if (
            len(pins) != 1
            or pins[0][0] != "file"
            or pins[0][4] != "sha256:" + request.payload_sha256
        ):
            raise ValueError("exact_retained_payload_member_required")
        # The complete outer group includes the compressed child itself.
        # Its original digest/size are verified again by the original inner flow.
        attempt.inner_request = owner.ArchiveBodyRequest(
            request.retention_parent / "outer" / member_path,
            request.payload_sha256,
            pins[0][3],
        )
        attempt.phase = "inner"
        _current(attempt)
        attempt.inner = stage.stage_product_group(
            attempt.inner_request,
            profile=staging_profile,
            absolute_root=str(request.retention_parent / "inner"),
            operation_ref=request.operation_ref + ":inner",
            partitioned_plan=request.partitioned_plan,
            group_namespace="inner",
            maximum_decoded_bytes=request.maximum_inner_decoded_bytes,
            explicit_create_intent=True,
            **observation_options,
        )
        attempt.phase = "receiving"
        _current(attempt)
        _receive_group(attempt, attempt.outer, "outer")
        _receive_group(attempt, attempt.inner, "inner")
        inner_root = _group_root(attempt.snapshot, "inner")
        return DriverStagingResult(
            request,
            attempt.snapshot,
            attempt.outer,
            attempt.inner_request,
            attempt.inner,
            tuple(attempt.validations),
            tuple(attempt.root_bindings),
            request.retention_parent / "outer" / outer_root,
            request.retention_parent / "inner" / inner_root,
        )
    except BaseException as cause:
        raise DriverStagingError(attempt, cause) from cause
