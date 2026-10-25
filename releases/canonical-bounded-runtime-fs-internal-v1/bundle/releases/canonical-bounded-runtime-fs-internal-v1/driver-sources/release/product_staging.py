"""Explicit original-reader/FS staging composition, never installation authority.

The caller supplies an exact ordered FS plan and guarded source request. All
writes, including directories/empty files, are provisional effects until the
original enclosing flow and whole-stage receiving complete. Implicit directory
modes are unavailable in this profile, not invented from the host umask.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields

from aware_file_system import staging_complete as complete
from aware_file_system import staging_member as member
from aware_file_system import staging_partitioned_plan as metadata
from aware_file_system import staging_root as root

from . import _product_bulk_consumption as bulk
from . import _product_stream_receiving as receiving

PROFILE = "aware.release.original-product-staging.v1"
COMPACT_PROFILE = "aware.release.original-product-staging-compact.v1"
RECORDED_PROFILE = "aware.release.original-recorded-staging.v1"
COMPRESSED_PROFILE = "aware.release.original-compressed-staging.v1"
BORROWED_PROFILE = "aware.release.original-borrowed-directory-staging.v1"
RETIRED_PROFILE = "aware.release.original-retired-member-staging.v1"
values = metadata.original


def _scalar(value):
    # Preserve exact original scalar types across snapshot comparisons: Python
    # equality alone would accept True/1 or 1.0/1. Limits remain owner-validated.
    if type(value) not in (str, int):
        raise TypeError("exact_original_plan_scalar_required")
    return value


def _pin(value):
    if type(value) is values.StagingDirectory:
        return "directory", _scalar(value.path), _scalar(value.mode)
    if type(value) is values.StagingFile:
        return (
            "file",
            _scalar(value.path),
            _scalar(value.mode),
            _scalar(value.size_bytes),
            _scalar(value.content_digest),
        )
    raise TypeError("original_staging_member_required")


def _snapshot(plan):
    return tuple(
        (
            _scalar(group.namespace),
            tuple(
                (
                    tuple(
                        _scalar(getattr(partition.limits, f.name))
                        for f in fields(values.StagingPlanLimits)
                    ),
                    tuple(_pin(value) for value in partition.members),
                )
                for partition in group.partitions
            ),
        )
        for group in plan.groups
    )


@dataclass
class _Attempt:
    request: object
    plan: object
    namespace: str
    absolute_root: str
    operation: str
    profile: str = PROFILE
    observation_profile: str | None = None
    phase: str = "plan"
    source_snapshot: tuple = ()
    maximum_decoded_bytes: int = 0
    snapshot: tuple = ()
    rows: tuple = ()
    cursor: int = 0
    preparation: root.StagingRootPreparation | None = None
    stage: object = None
    creation: object = None
    handles: list = field(default_factory=list)
    acquisitions: list = field(default_factory=list)
    writes: list = field(default_factory=list)
    terminals: list = field(default_factory=list)
    flow: object = None
    completion: object = None


@dataclass(frozen=True, slots=True, eq=False)
class StagedProductGroup:
    original_request: object
    original_plan_snapshot: tuple
    group_namespace: str
    original_preparation: object
    stage_handle: object
    original_creation: object
    member_handles: tuple
    original_acquisitions: tuple
    original_writes: tuple
    original_terminals: tuple
    original_flow: object
    original_completion: object
    parent_cleanup: str = "not_released"
    authorizes_installation: bool = False
    profile: str = PROFILE


class ProductStagingError(RuntimeError):
    def __init__(self, attempt, cause):
        super().__init__("original_product_staging_" + attempt.phase)
        self.original_attempt = attempt
        self.original_request = attempt.request
        self.original_plan = attempt.plan
        self.original_plan_snapshot = attempt.snapshot
        self.stage_handle = attempt.stage
        self.original_creation = attempt.creation
        self.member_handles = self.original_acquisitions = ()
        self.original_writes = self.original_terminals = ()
        self.failure_capture_complete = False
        self.unavailable_capture_fields = (
            "member_handles",
            "original_acquisitions",
            "original_writes",
            "original_terminals",
        )
        self.failure_capture_error = None
        try:
            self.member_handles = tuple(attempt.handles)
            self.unavailable_capture_fields = self.unavailable_capture_fields[1:]
            self.original_acquisitions = tuple(attempt.acquisitions)
            self.unavailable_capture_fields = self.unavailable_capture_fields[1:]
            self.original_writes = tuple(attempt.writes)
            self.unavailable_capture_fields = self.unavailable_capture_fields[1:]
            self.original_terminals = tuple(attempt.terminals)
            self.unavailable_capture_fields = ()
            self.failure_capture_complete = True
        except BaseException as capture_error:  # noqa: BLE001 - retain primary failure before independent diagnostic capture
            # Never replace the primary storage/guard/cleanup failure with a
            # secondary diagnostic allocation/interruption. The exact original
            # lists remain in original_attempt; missing projections are explicit.
            self.failure_capture_error = capture_error
        self.original_flow = attempt.flow
        self.original_completion = attempt.completion
        self.original_cause = cause
        self.parent_cleanup = "not_released"
        self.authorizes_retry = self.authorizes_installation = False


def _current(attempt):
    if attempt.profile in (BORROWED_PROFILE, RETIRED_PROFILE):
        if not root._plan_matches(attempt.plan, attempt.snapshot):
            raise ValueError("original_staging_plan_changed")
    elif _snapshot(attempt.plan) != attempt.snapshot:
        raise ValueError("original_staging_plan_changed")


def _enter(attempt):
    if attempt.stage is not None:
        return
    _current(attempt)
    attempt.preparation = root.prepare_stage(
        profile=root.PROFILE,
        absolute_root=attempt.absolute_root,
        operation_ref=attempt.operation,
        partitioned_plan=attempt.plan,
        group_namespace=attempt.namespace,
        **(
            {
                "history_profile": (
                    root.RETIRED_MEMBER_PROFILE
                    if attempt.profile == RETIRED_PROFILE
                    else root.RETAINED_DIRECTORY_PROFILE
                    if attempt.profile in (BORROWED_PROFILE, RETIRED_PROFILE)
                    else root.history.COMPRESSED_PROFILE
                    if attempt.profile == COMPRESSED_PROFILE
                    else root.history.PROFILE
                )
            }
            if attempt.profile
            in (RECORDED_PROFILE, COMPRESSED_PROFILE, BORROWED_PROFILE, RETIRED_PROFILE)
            else {}
        ),
        **(
            {"stat_block_storage": True}
            if attempt.observation_profile is not None
            else {}
        ),
    )
    # Retain the original handle before admission, including failed acquisition.
    attempt.stage = attempt.preparation.handle
    returned = root.admit_stage(
        attempt.stage,
        expected_request_digest=attempt.preparation.request_digest,
        expected_plan_digest=attempt.preparation.plan_digest,
        explicit_create_intent=True,
    )
    attempt.creation = returned
    if returned[0] is not attempt.stage:
        raise ValueError("original_stage_admission_handle_changed")


def _begin(attempt, row):
    _enter(attempt)
    coordinate, pin = row
    try:
        returned = member.begin_ordered_member(
            attempt.stage,
            profile=member.ORDERED_PROFILE,
            partition_ordinal=coordinate[0],
            member_ordinal=coordinate[1],
            expected_member_pin=pin,
            **(
                {"terminal_profile": member.CLOSED_TERMINAL_PROFILE}
                if attempt.observation_profile is not None
                else {}
            ),
        )
    except member.StagingMemberRefusal as cause:
        if cause.handle is not None:
            attempt.handles.append(cause.handle)
        raise
    attempt.acquisitions.append(returned)
    attempt.handles.append(returned[0])
    return returned[0]


def _finish(attempt, handle, pin):
    returned = member.finish_member(handle, expected_member_pin=pin)
    attempt.terminals.append(returned)
    attempt.cursor += 1


def _advance_metadata(attempt, stop):
    while attempt.cursor < stop:
        row = attempt.rows[attempt.cursor]
        pin = row[1]
        if pin[0] == "file" and pin[3] != 0:
            raise ValueError("original_staging_nonempty_file_order_mismatch")
        handle = _begin(attempt, row)
        _finish(attempt, handle, pin)


def _consumer(attempt, index):
    row = attempt.rows[index]
    pin = row[1]
    handle = None
    validate_progress = (
        member.validate_member_progress
        if attempt.profile
        in (
            COMPACT_PROFILE,
            RECORDED_PROFILE,
            COMPRESSED_PROFILE,
            BORROWED_PROFILE,
            RETIRED_PROFILE,
        )
        else None
    )

    def write(span):
        nonlocal handle
        _current(attempt)
        if handle is None:
            _advance_metadata(attempt, index)
            if attempt.cursor != index:
                raise ValueError("original_staging_file_order_mismatch")
            handle = _begin(attempt, row)
        extra = (
            {"progress_profile": member.PROGRESS_PROFILE}
            if attempt.profile
            in (
                COMPACT_PROFILE,
                RECORDED_PROFILE,
                COMPRESSED_PROFILE,
                BORROWED_PROFILE,
                RETIRED_PROFILE,
            )
            else {}
        )
        returned = member.write_span(
            handle,
            source_span_key=span.key,
            body=span.body,
            source_offset=span.body_offset,
            length=len(span.body) - span.body_offset,
            expected_member_offset=span.key.write_offset,
            **extra,
        )
        # Original progress key + original FS return, not the successful body.
        # A failed original call retains its stopping span in original custody.
        attempt.writes.append((span.key, returned))
        count, evidence = returned
        if attempt.profile in (
            COMPACT_PROFILE,
            RECORDED_PROFILE,
            COMPRESSED_PROFILE,
            BORROWED_PROFILE,
            RETIRED_PROFILE,
        ):
            if validate_progress is None:
                raise ValueError("original_compact_progress_validator_required")
            progress = validate_progress(
                handle, evidence, expected_source_span_key=span.key
            )
            if count != progress.accepted_prefix - progress.prior_prefix:
                raise ValueError("original_staging_progress_count_mismatch")
        if evidence.accepted_prefix == pin[3]:
            _finish(attempt, handle, pin)
        return bulk.member.WriteAcknowledgement(span.key, count)

    return bulk.PinnedConsumer(
        (pin[1], pin[3], pin[4][7:]), bulk.member.MemberConsumer(object(), write)
    )


def _receive_source(attempt, consumers):
    value = attempt.flow
    if type(value) is not bulk.ProvisionalBulkConsumption:
        raise TypeError("original_bulk_result_required")
    source = value.original_flow
    # Reuse the original IO-free flow/terminal receiving checks. This temporary
    # historical record is not enrolled and grants no live receiver authority.
    receiving._OriginalFlowReceiver._correlate(
        receiving._Record(
            attempt.request,
            attempt.source_snapshot,
            attempt.maximum_decoded_bytes,
            returned=source.original_flow,
        )
    )
    account = source.original_member_account
    if (
        source.compressed_flow_correlated is not True
        or source.tar_framing_confirmed is not True
        or account.member_checksums_matched is not True
    ):
        raise ValueError("original_enclosing_flow_incomplete")
    expected = {pin[1]: pin for _, pin in attempt.rows}
    observed = {row.name: row for row in account.entries}
    if len(observed) != len(account.entries) or observed.keys() != expected.keys():
        raise ValueError("original_source_roster_mismatch")
    for path, pin in expected.items():
        original = observed[path]
        if type(original) is not bulk.catalog._Entry or original.kind != pin[0]:
            raise ValueError("original_source_kind_mismatch")
        if not original.explicit or original.snapshot is None:
            raise ValueError("explicit_source_mode_required")
        if bulk.catalog._snapshot(original.original_item) != original.snapshot:
            raise ValueError("original_source_header_changed")
        if original.snapshot[3] != pin[2]:
            raise ValueError("original_source_mode_mismatch")
        if pin[0] == "file" and (original.size, original.sha256) != (
            pin[3],
            pin[4][7:],
        ):
            raise ValueError("original_source_file_pin_mismatch")
    if len(value.original_members) != len(consumers):
        raise ValueError("original_source_member_receipts_incomplete")
    for selected, returned in zip(consumers, value.original_members, strict=True):
        if (
            returned.original_pin != selected.pin
            or returned.acknowledged_bytes != selected.pin[1]
        ):
            raise ValueError("original_source_member_receipt_mismatch")


def _receive_completion(attempt):
    value = attempt.completion
    if type(value) is not complete.StageCompletionEvidence:
        raise TypeError("original_stage_completion_required")
    observed = complete.validate_stage_completion(
        attempt.stage,
        expected_request_digest=attempt.preparation.request_digest,
        expected_plan_digest=attempt.preparation.plan_digest,
    )  # IO-free original-owner validation against retained pre-settlement seals.
    if (
        value != observed
        or value.complete is not True
        or value.capture_complete is not True
        or value.observation_cleanup != "confirmed"
        or value.request_digest != attempt.preparation.request_digest
        or value.plan_digest != attempt.preparation.plan_digest
        or value.group_namespace != attempt.namespace
        or value.authorizes_installation is not False
    ):
        raise ValueError("original_stage_completion_binding_mismatch")
    for returned, original in (
        (value.postimages, observed.postimages),
        (value.original_returns, observed.original_returns),
    ):
        if type(original) is root.history.RecordedHistory:
            # The original owner seals this opaque prefix. Iteration produces
            # detached historical values, so element identity is inapplicable.
            if (
                returned is not original
                or root.history.history_seal(returned)
                != root.history.history_seal(original)
                or not original.capture_complete
            ):
                raise ValueError("original_stage_completion_carriers_substituted")
        elif len(returned) != len(original) or any(
            a is not b for a, b in zip(returned, original, strict=True)
        ):
            raise ValueError("original_stage_completion_carriers_substituted")


def stage_product_group(
    request,
    *,
    profile,
    absolute_root,
    operation_ref,
    partitioned_plan,
    group_namespace,
    maximum_decoded_bytes,
    explicit_create_intent,
    observation_profile=None,
):
    """Stage one declared group; never dispatch install, release, retry or deletion.

    FS directories/zero files may be created before their source item appears.
    They stay provisional: original bulk selection/EOF, exact source roster and
    original whole-stage receiving must all succeed before this result exists.
    """
    attempt = _Attempt(
        request, partitioned_plan, group_namespace, absolute_root, operation_ref
    )
    try:
        if type(profile) is not str or profile not in (
            PROFILE,
            COMPACT_PROFILE,
            RECORDED_PROFILE,
            COMPRESSED_PROFILE,
            BORROWED_PROFILE,
            RETIRED_PROFILE,
        ):
            raise ValueError("explicit_original_product_staging_profile_required")
        if observation_profile is not None and (
            profile != RETIRED_PROFILE
            or observation_profile != complete.entry.OBSERVATION_RECEIPT_PROFILE
        ):
            raise ValueError("explicit_original_observation_receipt_profile_required")
        attempt.profile = profile
        attempt.observation_profile = observation_profile
        if explicit_create_intent is not True:
            raise ValueError("explicit_staging_intent_required")
        if type(group_namespace) is not str:
            raise TypeError("exact_group_namespace_required")
        attempt.source_snapshot = receiving.original._guarded_file_snapshot(request)
        attempt.maximum_decoded_bytes = maximum_decoded_bytes
        metadata.validate_partitioned_staging_plan(
            partitioned_plan,
            profile=metadata.StagingMetadataProfile.TWO_GROUP_PARTITIONED_V1,
        )
        attempt.snapshot = _snapshot(partitioned_plan)
        group = next(row for row in attempt.snapshot if row[0] == group_namespace)
        attempt.rows = tuple(
            ((p, m), pin)
            for p, partition in enumerate(group[1])
            for m, pin in enumerate(partition[1])
        )
        consumers = tuple(
            _consumer(attempt, i)
            for i, (_, pin) in enumerate(attempt.rows)
            if pin[0] == "file"
        )
        attempt.phase = "source_flow"
        attempt.flow = bulk.observe_bulk_consumption(
            request,
            consumers,
            maximum_decoded_bytes=maximum_decoded_bytes,
            **(
                {"comparison_profile": bulk.DIRECT_CURRENTNESS_PROFILE}
                if profile in (BORROWED_PROFILE, RETIRED_PROFILE)
                else {}
            ),
            **(
                {"history_profile": bulk.flow.flow.COMPACT_HISTORY_PROFILE}
                if profile
                in (
                    RECORDED_PROFILE,
                    COMPRESSED_PROFILE,
                    BORROWED_PROFILE,
                    RETIRED_PROFILE,
                )
                else {}
            ),
        )
        attempt.phase = "source_receiving"
        _current(attempt)
        _receive_source(attempt, consumers)
        attempt.phase = "trailing_directory_and_empty_members"
        _advance_metadata(attempt, len(attempt.rows))
        attempt.phase = "complete_stage_receiving"
        if attempt.preparation is None:
            raise ValueError("original_stage_preparation_missing")
        attempt.completion = complete.finish_stage(
            attempt.stage,
            profile=complete.PROFILE,
            expected_request_digest=attempt.preparation.request_digest,
            expected_plan_digest=attempt.preparation.plan_digest,
            **(
                {"observation_profile": attempt.observation_profile}
                if attempt.observation_profile is not None
                else {}
            ),
        )
        _current(attempt)
        _receive_source(attempt, consumers)
        _receive_completion(attempt)
        return StagedProductGroup(
            request,
            attempt.snapshot,
            group_namespace,
            attempt.preparation,
            attempt.stage,
            attempt.creation,
            tuple(attempt.handles),
            tuple(attempt.acquisitions),
            tuple(attempt.writes),
            tuple(attempt.terminals),
            attempt.flow,
            attempt.completion,
            profile=profile,
        )
    except BaseException as cause:
        raise ProductStagingError(attempt, cause) from cause
