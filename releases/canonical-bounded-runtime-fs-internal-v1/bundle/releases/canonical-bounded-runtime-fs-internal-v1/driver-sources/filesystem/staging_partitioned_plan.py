"""Explicit detached partition metadata; not writable capacity or root custody.

Every partition uses the unchanged original validator and ceilings. The new
group profile bounds logical aggregate input only; it admits no physical IO.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields
from enum import StrEnum

from . import staging_plan as original

_VALIDATE = original.validate_staging_plan
_CEILINGS = original._CEILINGS
MAX_GROUPS = MAX_PARTITIONS = 2


class StagingMetadataProfile(StrEnum):
    TWO_GROUP_PARTITIONED_V1 = "aware.filesystem.partitioned-staging-metadata.v1"


@dataclass(frozen=True, slots=True)
class StagingPlanGroup:
    namespace: str
    partitions: tuple[original.StagingPlan, ...]


@dataclass(frozen=True, slots=True)
class PartitionedStagingPlan:
    groups: tuple[StagingPlanGroup, ...]


@dataclass(frozen=True, slots=True)
class PartitionedStagingSummary:
    plan_digest: str
    profile: StagingMetadataProfile
    partition_summaries: tuple[original.StagingPlanSummary, ...]
    occurrence_count: int
    unique_member_count: int
    repeated_directory_count: int
    total_file_bytes: int
    encoded_bytes: int
    physical_capacity_available: bool = False
    authorizes_dispatch: bool = False
    roots_bound: bool = False


class PartitionedStagingRefusal(ValueError):
    def __init__(
        self,
        request,
        profile,
        phase,
        coordinate,
        returned,
        accepted,
        raw_returns,
        snapshot,
        validation_input,
        invocation,
        cause,
    ):
        super().__init__("partitioned_staging_metadata_refused")
        self.original_request = request
        self.original_profile = profile
        self.phase = phase
        self.coordinate = coordinate
        self.original_return = returned
        self.original_returns = tuple(raw_returns)
        self.validated_summaries = tuple(row[1] for row in accepted)
        self.validated_summary_snapshots = tuple(row[2] for row in accepted)
        self.captured_partition_snapshots = tuple(row[4] for row in accepted)
        self.last_partition_snapshot = snapshot
        self.original_validation_input = validation_input
        self.validation_invocation = invocation
        self.primary_cause = cause
        self.interruption = isinstance(cause, (KeyboardInterrupt, InterruptedError))
        self.authorizes_dispatch = False
        self.physical_capacity_available = False


def _snapshot(plan):
    if (
        type(plan) is not original.StagingPlan
        or type(plan.limits) is not original.StagingPlanLimits
    ):
        raise TypeError("original_staging_partition_required")
    if type(plan.members) is not tuple or len(plan.members) > _CEILINGS[0]:
        raise ValueError("bounded_partition_members_required")
    rows = []
    for value in plan.members:
        if type(value) is original.StagingDirectory:
            rows.append(("directory", value.path, value.mode))
        elif type(value) is original.StagingFile:
            rows.append(
                ("file", value.path, value.mode, value.size_bytes, value.content_digest)
            )
        else:
            raise TypeError("original_partition_member_required")
    return tuple(getattr(plan.limits, f.name) for f in fields(plan.limits)), tuple(rows)


def _captured_plan(snapshot):
    limits, rows = snapshot
    members = tuple(
        original.StagingDirectory(*row[1:])
        if row[0] == "directory"
        else original.StagingFile(*row[1:])
        for row in rows
    )
    return original.StagingPlan(original.StagingPlanLimits(*limits), members)


def validate_partitioned_staging_plan(request, *, profile):
    """Pure logical binding; no disk reservation, usable handles or backend."""
    coordinate = None
    phase = "selection"
    returned = None
    accepted = []
    raw_returns = []
    snapshot = None
    validation_input = None
    invocation = "not_invoked"
    try:
        if type(profile) is not StagingMetadataProfile:
            raise ValueError("explicit_staging_metadata_profile_required")
        if (
            type(request) is not PartitionedStagingPlan
            or type(request.groups) is not tuple
            or not 1 <= len(request.groups) <= MAX_GROUPS
            or original.validate_staging_plan is not _VALIDATE
            or original._CEILINGS != _CEILINGS
        ):
            raise ValueError("original_bounded_staging_groups_required")
        groups = request.groups
        names = set()
        group_seals = []
        frame = []
        occurrences = physical = repeated = total = encoded = 0
        for group_index, group in enumerate(groups):
            phase = "group"
            coordinate = group_index, None
            returned = snapshot = None
            validation_input = None
            invocation = "not_invoked"
            if (
                type(group) is not StagingPlanGroup
                or type(group.namespace) is not str
                or len(group.namespace) > 64
                or type(group.partitions) is not tuple
                or not 1 <= len(group.partitions) <= MAX_PARTITIONS
            ):
                raise ValueError("exact_staging_group_required")
            name, partitions = group.namespace, group.partitions
            group_seals.append((group, name, partitions))
            original._read_text(name, 64)
            original._relative_path(name)
            if "/" in name or name in names:
                raise ValueError("unique_staging_namespace_required")
            names.add(name)
            entries = {}
            group_digests = []
            for partition_index, partition in enumerate(partitions):
                phase = "partition_snapshot"
                coordinate = group_index, partition_index
                returned = None
                validation_input = None
                invocation = "not_invoked"
                snapshot = _snapshot(partition)
                validation_input = _captured_plan(snapshot)
                phase = "original_validation"
                invocation = "unknown"
                returned = _VALIDATE(validation_input)
                invocation = "returned"
                raw_returns.append((coordinate, validation_input, returned))
                phase = "partition_receiving"
                if (
                    type(returned) is not original.StagingPlanSummary
                    or snapshot != _snapshot(partition)
                    or snapshot != _snapshot(validation_input)
                ):
                    raise ValueError("original_partition_return_or_snapshot_changed")
                summary_seal = tuple(
                    getattr(returned, f.name) for f in fields(returned)
                )
                accepted.append(
                    (coordinate, returned, summary_seal, partition, snapshot)
                )
                occurrences += summary_seal[1]
                total += summary_seal[2]
                encoded += summary_seal[3]
                phase = "aggregate_capacity"
                if (
                    occurrences > _CEILINGS[0]
                    or total > MAX_GROUPS * _CEILINGS[2]
                    or encoded > _CEILINGS[5]
                ):
                    raise ValueError("staging_group_aggregate_limit")
                phase = "namespace_correlation"
                for row in snapshot[1]:
                    path = row[1]
                    if path in entries:
                        if row[0] != "directory" or entries[path] != row:
                            raise ValueError("staging_partition_collision")
                        repeated += 1
                    else:
                        entries[path] = row
                        physical += 1
                group_digests.append(summary_seal[0])
            frame.append((name, group_digests))
            if group.namespace != name or group.partitions is not partitions:
                raise ValueError("staging_group_changed")
        phase = "encoding"
        body = json.dumps(
            [profile.value, frame],
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        encoded += len(body)
        if encoded > _CEILINGS[5]:
            raise ValueError("staging_group_encoded_limit")
        phase = "final_correlation"
        if (
            request.groups is not groups
            or any(_snapshot(row[3]) != row[4] for row in accepted)
            or any(
                group.namespace != name or group.partitions is not parts
                for group, name, parts in group_seals
            )
            or any(
                tuple(getattr(row[1], f.name) for f in fields(row[1])) != row[2]
                for row in accepted
            )
            or original.validate_staging_plan is not _VALIDATE
            or original._CEILINGS != _CEILINGS
        ):
            raise ValueError("staging_group_input_changed")
        phase = "summary"
        return PartitionedStagingSummary(
            "sha256:" + hashlib.sha256(body).hexdigest(),
            profile,
            tuple(row[1] for row in accepted),
            occurrences,
            physical,
            repeated,
            total,
            encoded,
        )
    except (
        BaseException
    ) as cause:  # Preserve original validation/interruption and prefix.
        raise PartitionedStagingRefusal(
            request,
            profile,
            phase,
            coordinate,
            returned,
            accepted,
            raw_returns,
            snapshot,
            validation_input,
            invocation,
            cause,
        ) from cause
