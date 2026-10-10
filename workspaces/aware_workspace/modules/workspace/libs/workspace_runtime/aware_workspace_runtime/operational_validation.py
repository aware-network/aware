"""Dependency-clean contracts for source-bound operational validation.

These values describe validation over one maintained repository source state.
They do not create WorkspaceRevision, CodePackage, ontology, ORM, release, or
publication authority.  Later semantic adapters may retain their refs without
reinterpreting the operational result.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import PurePosixPath

WORKSPACE_OPERATIONAL_VALIDATION_CONTRACT = "aware.workspace.operational-validation.v1"


class OperationalValidationError(ValueError):
    """Raised when an operational validation value is not exact."""


def validate_test_resource_outcome(
    value: Mapping[str, object], output_tail: str
) -> dict[str, object]:
    """Validate portable observations; never issue allocation/cleanup authority."""
    counters = (
        "capture_limit_bytes",
        "stdout_observed_bytes",
        "stderr_observed_bytes",
        "stdout_retained_bytes",
        "stderr_retained_bytes",
        "stdout_dropped_bytes",
        "stderr_dropped_bytes",
        "output_tail_bytes",
    )
    keys = set(counters) | {
        "contract",
        "capture_status",
        "output_tail_digest",
        "cleanup_status",
        "cleanup_reason",
        "allocation_status",
        "retention_status",
        "diagnostic_code",
    }
    if not isinstance(value, Mapping) or set(value) != keys:
        raise OperationalValidationError("resource_outcome_fields_invalid")
    result = dict(value)
    if (
        type(output_tail) is not str
        or any(
            type(result[key]) is not str
            for key in (
                "contract",
                "capture_status",
                "output_tail_digest",
                "cleanup_status",
                "allocation_status",
                "retention_status",
            )
        )
        or any(
            result[key] is not None and type(result[key]) is not str
            for key in ("cleanup_reason", "diagnostic_code")
        )
    ):
        raise OperationalValidationError("resource_outcome_scalar_invalid")
    if result["contract"] != "aware.code.test-resource-outcome.v1":
        raise OperationalValidationError("resource_outcome_contract_invalid")
    for key in counters:
        count = result[key]
        if type(count) is not int or not 0 <= count <= (2**63 - 1):
            raise OperationalValidationError("resource_outcome_counter_invalid")
    limit = result["capture_limit_bytes"]
    assert isinstance(limit, int)
    if not 256 <= limit <= 1_000_000:
        raise OperationalValidationError("resource_outcome_limit_invalid")
    status = result["capture_status"]
    if status not in {"complete", "incomplete", "failed"}:
        raise OperationalValidationError("resource_outcome_capture_invalid")
    if (
        result["diagnostic_code"]
        != {
            "complete": None,
            "incomplete": "capture_incomplete",
            "failed": "capture_failed",
        }[str(status)]
    ):
        raise OperationalValidationError("resource_outcome_diagnostic_invalid")
    for stream, budget in (
        ("stdout", (limit - 1) // 2),
        ("stderr", limit - 1 - (limit - 1) // 2),
    ):
        observed = result[f"{stream}_observed_bytes"]
        retained = result[f"{stream}_retained_bytes"]
        dropped = result[f"{stream}_dropped_bytes"]
        assert (
            isinstance(observed, int)
            and isinstance(retained, int)
            and isinstance(dropped, int)
        )
        if observed != retained + dropped or retained > budget:
            raise OperationalValidationError("resource_outcome_arithmetic_invalid")
    encoded = output_tail.encode("utf-8")
    if (
        len(encoded) > limit
        or result["output_tail_bytes"] != len(encoded)
        or _digest(str(result["output_tail_digest"]), "output_tail_digest")
        != "sha256:" + hashlib.sha256(encoded).hexdigest()
    ):
        raise OperationalValidationError("resource_outcome_output_invalid")
    allocation = result["allocation_status"]
    if allocation == "not_created":
        if (
            result["cleanup_status"],
            result["cleanup_reason"],
            result["retention_status"],
        ) != ("not_created", None, "none"):
            raise OperationalValidationError("resource_outcome_not_created_invalid")
    elif allocation == "unadmitted_compatibility_scratch":
        if (
            result["cleanup_status"] != "cleanup_pending"
            or result["retention_status"] != "retained_pending"
            or result["cleanup_reason"]
            not in {"writer_exclusion_unavailable", "termination_unconfirmed"}
        ):
            raise OperationalValidationError("resource_outcome_cleanup_invalid")
    else:
        raise OperationalValidationError("resource_outcome_allocation_invalid")
    return result


class ValidationEffectClass(StrEnum):
    PURE = "pure"
    TEMPORARY_FILESYSTEM = "temporary_filesystem"
    EPHEMERAL_LOCAL_SERVICE = "ephemeral_local_service"
    RESIDENT_READ_ONLY = "resident_read_only"
    RESIDENT_MUTATING_CANARY = "resident_mutating_canary"
    HOST_OR_RELEASE_EFFECT = "host_or_release_effect"


class ValidationExecutionStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    UNSUPPORTED = "unsupported"
    INFRASTRUCTURE_FAILED = "infrastructure_failed"


class ValidationCurrentnessStatus(StrEnum):
    CURRENT = "current"
    STALE = "stale"
    UNKNOWN = "unknown"


class ValidationCurrentnessPolicy(StrEnum):
    FULL_REPOSITORY = "full_repository"
    AUTHORED_COMPLETE_SELECTION = "authored_complete_selection"


@dataclass(frozen=True, slots=True)
class WorkspaceValidationSourceCoordinate:
    """One exact neutral Workspace repository observation coordinate."""

    repository_binding_ref: str
    epoch: str
    cursor: int
    snapshot_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "repository_binding_ref",
            _required(self.repository_binding_ref, "repository_binding_ref"),
        )
        object.__setattr__(self, "epoch", _required(self.epoch, "epoch"))
        if isinstance(self.cursor, bool) or self.cursor < 0:
            raise OperationalValidationError("cursor must be non-negative")
        object.__setattr__(
            self,
            "snapshot_digest",
            _digest(self.snapshot_digest, "snapshot_digest"),
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "repository_binding_ref": self.repository_binding_ref,
            "epoch": self.epoch,
            "cursor": self.cursor,
            "snapshot_digest": self.snapshot_digest,
        }


@dataclass(frozen=True, slots=True)
class SourcePackageCoordinate:
    """Portable source package coordinate, never canonical CodePackage truth."""

    package_root: str
    manifest_path: str
    manifest_digest: str
    language_key: str
    toolchain_key: str
    canonical_code_package_ref: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "package_root", _path(self.package_root, allow_dot=True)
        )
        object.__setattr__(self, "manifest_path", _path(self.manifest_path))
        object.__setattr__(
            self,
            "manifest_digest",
            _digest(self.manifest_digest, "manifest_digest"),
        )
        object.__setattr__(
            self, "language_key", _required(self.language_key, "language_key")
        )
        object.__setattr__(
            self, "toolchain_key", _required(self.toolchain_key, "toolchain_key")
        )
        if self.canonical_code_package_ref is not None:
            object.__setattr__(
                self,
                "canonical_code_package_ref",
                _required(
                    self.canonical_code_package_ref,
                    "canonical_code_package_ref",
                ),
            )

    def to_payload(self) -> dict[str, object]:
        return {
            "package_root": self.package_root,
            "manifest_path": self.manifest_path,
            "manifest_digest": self.manifest_digest,
            "language_key": self.language_key,
            "toolchain_key": self.toolchain_key,
            "canonical_code_package_ref": self.canonical_code_package_ref,
        }


@dataclass(frozen=True, slots=True)
class OperationalValidationSourceSelection:
    """Authored package/path selection without canonical CodePackage claims."""

    key: str
    package_root: str
    manifest_path: str
    language_key: str
    toolchain_key: str
    source_paths: tuple[str, ...]
    test_paths: tuple[str, ...]
    selection_digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", _required(self.key, "selection key"))
        root = _path(self.package_root, allow_dot=True)
        manifest = _path(self.manifest_path)
        source_paths = tuple(sorted({_path(path) for path in self.source_paths}))
        test_paths = tuple(sorted({_path(path) for path in self.test_paths}))
        if not source_paths or not test_paths:
            raise OperationalValidationError(
                "source selection requires source and test paths"
            )
        for path in (manifest, *source_paths, *test_paths):
            if not _path_is_under(path, root):
                raise OperationalValidationError(
                    "source selection paths must remain under package_root"
                )
        if not set(test_paths).issubset(source_paths):
            raise OperationalValidationError(
                "selected test paths must also be selected source paths"
            )
        object.__setattr__(self, "package_root", root)
        object.__setattr__(self, "manifest_path", manifest)
        object.__setattr__(
            self, "language_key", _required(self.language_key, "language_key")
        )
        object.__setattr__(
            self, "toolchain_key", _required(self.toolchain_key, "toolchain_key")
        )
        object.__setattr__(self, "source_paths", source_paths)
        object.__setattr__(self, "test_paths", test_paths)
        object.__setattr__(
            self, "selection_digest", content_digest(self.identity_payload())
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "key": self.key,
            "package_root": self.package_root,
            "manifest_path": self.manifest_path,
            "language_key": self.language_key,
            "toolchain_key": self.toolchain_key,
            "source_paths": list(self.source_paths),
            "test_paths": list(self.test_paths),
        }

    def to_payload(self) -> dict[str, object]:
        return {
            **self.identity_payload(),
            "selection_digest": self.selection_digest,
        }


@dataclass(frozen=True, slots=True)
class OperationalValidationSuite:
    key: str
    project_root: str
    interpreter_path: str
    test_paths: tuple[str, ...]
    effect_class: ValidationEffectClass
    timeout_seconds: float
    source_first: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", _required(self.key, "suite key"))
        object.__setattr__(
            self, "project_root", _path(self.project_root, allow_dot=True)
        )
        object.__setattr__(self, "interpreter_path", _path(self.interpreter_path))
        paths = tuple(_path(path) for path in self.test_paths)
        if not paths or len(paths) != len(set(paths)):
            raise OperationalValidationError(
                "suite test paths must be non-empty and unique"
            )
        if self.timeout_seconds <= 0:
            raise OperationalValidationError("suite timeout must be positive")
        object.__setattr__(self, "test_paths", paths)
        object.__setattr__(
            self, "effect_class", ValidationEffectClass(self.effect_class)
        )

    @property
    def command(self) -> tuple[str, ...]:
        return (
            self.interpreter_path,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            *self.test_paths,
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "key": self.key,
            "project_root": self.project_root,
            "interpreter_path": self.interpreter_path,
            "test_paths": list(self.test_paths),
            "effect_class": self.effect_class.value,
            "timeout_seconds": self.timeout_seconds,
            "source_first": self.source_first,
            "command": list(self.command),
        }


@dataclass(frozen=True, slots=True)
class OperationalValidationProfile:
    key: str
    revision: str
    suites: tuple[OperationalValidationSuite, ...]
    lock_paths: tuple[str, ...]
    source_selections: tuple[OperationalValidationSourceSelection, ...]
    currentness_policy: ValidationCurrentnessPolicy
    profile_digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", _required(self.key, "profile key"))
        object.__setattr__(
            self, "revision", _required(self.revision, "profile revision")
        )
        suites = tuple(self.suites)
        suite_keys = tuple(suite.key for suite in suites)
        if not suites or len(suite_keys) != len(set(suite_keys)):
            raise OperationalValidationError(
                "profile suites must be non-empty with unique keys"
            )
        lock_paths = tuple(sorted({_path(path) for path in self.lock_paths}))
        selections = tuple(self.source_selections)
        selection_keys = tuple(selection.key for selection in selections)
        if not selections or len(selection_keys) != len(set(selection_keys)):
            raise OperationalValidationError(
                "profile source selections must be non-empty with unique keys"
            )
        selected_tests = {
            path for selection in selections for path in selection.test_paths
        }
        suite_tests = {
            _project_path(suite.project_root, path)
            for suite in suites
            for path in suite.test_paths
        }
        if suite_tests != selected_tests:
            raise OperationalValidationError(
                "profile suites must exactly cover selected test paths"
            )
        if not lock_paths:
            raise OperationalValidationError("profile requires declared lock paths")
        object.__setattr__(self, "suites", suites)
        object.__setattr__(self, "lock_paths", lock_paths)
        object.__setattr__(self, "source_selections", selections)
        object.__setattr__(
            self,
            "currentness_policy",
            ValidationCurrentnessPolicy(self.currentness_policy),
        )
        object.__setattr__(
            self,
            "profile_digest",
            content_digest(self.identity_payload()),
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "contract": WORKSPACE_OPERATIONAL_VALIDATION_CONTRACT,
            "key": self.key,
            "revision": self.revision,
            "suites": [suite.to_payload() for suite in self.suites],
            "lock_paths": list(self.lock_paths),
            "source_selections": [
                selection.to_payload() for selection in self.source_selections
            ],
            "currentness_policy": self.currentness_policy.value,
        }

    def to_payload(self) -> dict[str, object]:
        return {**self.identity_payload(), "profile_digest": self.profile_digest}

    @property
    def source_paths(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    path
                    for selection in self.source_selections
                    for path in selection.source_paths
                }
            )
        )

    @property
    def currentness_paths(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    *self.source_paths,
                    *self.lock_paths,
                    *(item.manifest_path for item in self.source_selections),
                }
            )
        )


@dataclass(frozen=True, slots=True)
class OperationalValidationPlan:
    source: WorkspaceValidationSourceCoordinate
    profile: OperationalValidationProfile
    selected_source_digests: tuple[tuple[str, str], ...]
    package_coordinates: tuple[SourcePackageCoordinate, ...]
    lock_digests: tuple[tuple[str, str], ...]
    runner_fingerprint: str
    environment_fingerprint: str
    plan_digest: str = field(init=False)
    plan_ref: str = field(init=False)
    selection_state_digest: str = field(init=False)
    currentness_state_digest: str = field(init=False)

    def __post_init__(self) -> None:
        coordinates = tuple(self.package_coordinates)
        if len(coordinates) != len(self.profile.source_selections):
            raise OperationalValidationError(
                "plan package coordinates must match profile selections"
            )
        for selection, coordinate in zip(
            self.profile.source_selections, coordinates, strict=True
        ):
            if (
                coordinate.package_root != selection.package_root
                or coordinate.manifest_path != selection.manifest_path
                or coordinate.language_key != selection.language_key
                or coordinate.toolchain_key != selection.toolchain_key
                or coordinate.canonical_code_package_ref is not None
            ):
                raise OperationalValidationError(
                    "plan package coordinate differs from authored selection"
                )
        object.__setattr__(self, "package_coordinates", coordinates)
        selected_source_digests = tuple(sorted(self.selected_source_digests))
        if (
            tuple(path for path, _ in selected_source_digests)
            != self.profile.currentness_paths
        ):
            raise OperationalValidationError(
                "plan source digests must match profile currentness paths"
            )
        for path, digest in selected_source_digests:
            _ = _path(path)
            _ = _digest(digest, f"selected source digest for {path}")
        object.__setattr__(self, "selected_source_digests", selected_source_digests)
        selected_digest_by_path = dict(selected_source_digests)
        for coordinate in coordinates:
            if (
                selected_digest_by_path[coordinate.manifest_path]
                != coordinate.manifest_digest
            ):
                raise OperationalValidationError(
                    "package manifest digest differs from selected source"
                )
        object.__setattr__(
            self,
            "selection_state_digest",
            content_digest(
                [
                    {"path": path, "digest": digest}
                    for path, digest in selected_source_digests
                ]
            ),
        )
        object.__setattr__(
            self,
            "currentness_state_digest",
            (
                self.source.snapshot_digest
                if self.profile.currentness_policy
                is ValidationCurrentnessPolicy.FULL_REPOSITORY
                else self.selection_state_digest
            ),
        )
        lock_digests = tuple(sorted(self.lock_digests))
        if tuple(path for path, _ in lock_digests) != self.profile.lock_paths:
            raise OperationalValidationError(
                "plan lock digests must match the profile lock paths"
            )
        for path, digest in lock_digests:
            _ = _path(path)
            _ = _digest(digest, f"lock digest for {path}")
        object.__setattr__(self, "lock_digests", lock_digests)
        object.__setattr__(
            self,
            "runner_fingerprint",
            _digest(self.runner_fingerprint, "runner_fingerprint"),
        )
        object.__setattr__(
            self,
            "environment_fingerprint",
            _digest(self.environment_fingerprint, "environment_fingerprint"),
        )
        plan_digest = content_digest(self.identity_payload())
        object.__setattr__(self, "plan_digest", plan_digest)
        object.__setattr__(self, "plan_ref", f"validation-plan:{plan_digest}")

    def identity_payload(self) -> dict[str, object]:
        return {
            "contract": WORKSPACE_OPERATIONAL_VALIDATION_CONTRACT,
            "source": self.source.to_payload(),
            "profile_key": self.profile.key,
            "profile_revision": self.profile.revision,
            "profile_digest": self.profile.profile_digest,
            "suites": [suite.to_payload() for suite in self.profile.suites],
            "package_coordinates": [
                coordinate.to_payload() for coordinate in self.package_coordinates
            ],
            "selected_source_digests": [
                {"path": path, "digest": digest}
                for path, digest in self.selected_source_digests
            ],
            "selection_state_digest": self.selection_state_digest,
            "currentness_state_digest": self.currentness_state_digest,
            "lock_digests": [
                {"path": path, "digest": digest} for path, digest in self.lock_digests
            ],
            "runner_fingerprint": self.runner_fingerprint,
            "environment_fingerprint": self.environment_fingerprint,
        }

    def to_payload(self) -> dict[str, object]:
        return {
            **self.identity_payload(),
            "plan_digest": self.plan_digest,
            "plan_ref": self.plan_ref,
        }


@dataclass(frozen=True, slots=True)
class OperationalValidationSuiteReceipt:
    suite_key: str
    status: ValidationExecutionStatus
    command: tuple[str, ...]
    exit_code: int | None
    duration_ms: int
    output_tail: str
    diagnostic_code: str | None = None
    resource_outcome: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "suite_key", _required(self.suite_key, "suite_key"))
        object.__setattr__(self, "status", ValidationExecutionStatus(self.status))
        command = tuple(_required(item, "command item") for item in self.command)
        if not command:
            raise OperationalValidationError("suite receipt command is empty")
        if self.duration_ms < 0:
            raise OperationalValidationError("suite duration must be non-negative")
        if self.diagnostic_code is not None:
            object.__setattr__(
                self,
                "diagnostic_code",
                _required(self.diagnostic_code, "diagnostic_code"),
            )
        object.__setattr__(self, "command", command)

        if self.resource_outcome is not None:
            object.__setattr__(
                self,
                "resource_outcome",
                validate_test_resource_outcome(self.resource_outcome, self.output_tail),
            )

    @property
    def resource_outcome_posture(self) -> str:
        return (
            "resource_outcome_unobserved"
            if self.resource_outcome is None
            else "observed"
        )

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "suite_key": self.suite_key,
            "status": self.status.value,
            "command": list(self.command),
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "output_tail": self.output_tail,
            "diagnostic_code": self.diagnostic_code,
        }
        if self.resource_outcome is not None:
            payload["resource_outcome"] = validate_test_resource_outcome(
                self.resource_outcome, self.output_tail
            )
        return payload


@dataclass(frozen=True, slots=True)
class OperationalValidationReceipt:
    plan: OperationalValidationPlan
    status: ValidationExecutionStatus
    suite_receipts: tuple[OperationalValidationSuiteReceipt, ...]
    completed_source: WorkspaceValidationSourceCoordinate | None
    completed_currentness_state_digest: str | None
    started_at: str
    completed_at: str
    worker_generation_ref: str
    diagnostic_code: str | None = None
    receipt_ref: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", ValidationExecutionStatus(self.status))
        suite_receipts = tuple(self.suite_receipts)
        if tuple(item.suite_key for item in suite_receipts) != tuple(
            suite.key for suite in self.plan.profile.suites
        ):
            raise OperationalValidationError(
                "suite receipts must match plan suite order"
            )
        object.__setattr__(self, "suite_receipts", suite_receipts)
        if self.completed_currentness_state_digest is not None:
            object.__setattr__(
                self,
                "completed_currentness_state_digest",
                _digest(
                    self.completed_currentness_state_digest,
                    "completed_currentness_state_digest",
                ),
            )
        if self.status is ValidationExecutionStatus.PASSED and (
            self.completed_source is None
            or self.completed_currentness_state_digest
            != self.plan.currentness_state_digest
        ):
            raise OperationalValidationError(
                "passed receipt requires stable selected source"
            )
        for name, value in (
            ("started_at", self.started_at),
            ("completed_at", self.completed_at),
            ("worker_generation_ref", self.worker_generation_ref),
        ):
            object.__setattr__(self, name, _required(value, name))
        if self.diagnostic_code is not None:
            object.__setattr__(
                self,
                "diagnostic_code",
                _required(self.diagnostic_code, "diagnostic_code"),
            )
        object.__setattr__(
            self,
            "receipt_ref",
            f"validation-receipt:{content_digest(self.identity_payload())}",
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "contract": WORKSPACE_OPERATIONAL_VALIDATION_CONTRACT,
            "plan_ref": self.plan.plan_ref,
            "plan_digest": self.plan.plan_digest,
            "profile_key": self.plan.profile.key,
            "source": self.plan.source.to_payload(),
            "completed_source": (
                None
                if self.completed_source is None
                else self.completed_source.to_payload()
            ),
            "selection_state_digest": self.plan.selection_state_digest,
            "currentness_state_digest": self.plan.currentness_state_digest,
            "completed_currentness_state_digest": (
                self.completed_currentness_state_digest
            ),
            "status": self.status.value,
            "suite_receipts": [item.to_payload() for item in self.suite_receipts],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "worker_generation_ref": self.worker_generation_ref,
            "diagnostic_code": self.diagnostic_code,
        }

    def to_payload(self) -> dict[str, object]:
        return {
            **self.plan.to_payload(),
            **self.identity_payload(),
            "receipt_ref": self.receipt_ref,
        }

    @staticmethod
    def validate_payload_identity(
        payload: Mapping[str, object], *, expected_ref: str
    ) -> str:
        """Pure canonical join; no admission or currentness is conferred."""
        plan_fields = (
            "contract",
            "source",
            "profile_key",
            "profile_revision",
            "profile_digest",
            "suites",
            "package_coordinates",
            "selected_source_digests",
            "selection_state_digest",
            "currentness_state_digest",
            "lock_digests",
            "runner_fingerprint",
            "environment_fingerprint",
        )
        receipt_fields = (
            "contract",
            "plan_ref",
            "plan_digest",
            "profile_key",
            "source",
            "completed_source",
            "selection_state_digest",
            "currentness_state_digest",
            "completed_currentness_state_digest",
            "status",
            "suite_receipts",
            "started_at",
            "completed_at",
            "worker_generation_ref",
            "diagnostic_code",
        )
        if any(
            key not in payload for key in (*plan_fields, *receipt_fields, "receipt_ref")
        ):
            raise OperationalValidationError("stored_receipt_identity_fields_missing")
        if payload["contract"] != WORKSPACE_OPERATIONAL_VALIDATION_CONTRACT:
            raise OperationalValidationError("stored_receipt_contract_invalid")
        suites = payload["suite_receipts"]
        if not isinstance(suites, list):
            raise OperationalValidationError("stored_receipt_suites_invalid")
        for item in suites:
            if not isinstance(item, Mapping):
                raise OperationalValidationError("stored_receipt_suite_invalid")
            if "resource_outcome" in item:
                resource, output = item["resource_outcome"], item.get("output_tail")
                if not isinstance(resource, Mapping) or type(output) is not str:
                    raise OperationalValidationError("stored_receipt_resource_invalid")
                _ = validate_test_resource_outcome(resource, output)
        try:
            plan_digest = content_digest({key: payload[key] for key in plan_fields})
            receipt_digest = content_digest(
                {key: payload[key] for key in receipt_fields}
            )
        except (TypeError, ValueError) as error:
            raise OperationalValidationError(
                "stored_receipt_encoding_invalid"
            ) from error
        derived_ref = f"validation-receipt:{receipt_digest}"
        if (
            payload["plan_digest"] != plan_digest
            or payload["plan_ref"] != f"validation-plan:{plan_digest}"
            or payload["receipt_ref"] != derived_ref
            or expected_ref != derived_ref
        ):
            raise OperationalValidationError("stored_receipt_identity_mismatch")
        return derived_ref


def content_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def source_coordinate_from_payload(
    payload: Mapping[str, object],
) -> WorkspaceValidationSourceCoordinate:
    binding = payload.get("binding_key")
    epoch = payload.get("epoch")
    cursor = payload.get("cursor")
    snapshot_digest = payload.get("snapshot_digest")
    if (
        not isinstance(binding, str)
        or not isinstance(epoch, str)
        or not isinstance(cursor, int)
        or isinstance(cursor, bool)
        or not isinstance(snapshot_digest, str)
    ):
        raise OperationalValidationError("source coordinate payload fields are invalid")
    return WorkspaceValidationSourceCoordinate(
        repository_binding_ref=binding,
        epoch=epoch,
        cursor=cursor,
        snapshot_digest=snapshot_digest,
    )


def _required(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OperationalValidationError(f"{name} must be non-empty text")
    return value.strip()


def _digest(value: str, name: str) -> str:
    text = _required(value, name)
    if not text.startswith("sha256:") or len(text) != len("sha256:") + 64:
        raise OperationalValidationError(f"{name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in text[7:]):
        raise OperationalValidationError(f"{name} must be lowercase sha256")
    return text


def _path(value: str, *, allow_dot: bool = False) -> str:
    text = _required(value, "path")
    if allow_dot and text == ".":
        return text
    path = PurePosixPath(text)
    if (
        path.is_absolute()
        or path.as_posix() != text
        or "\\" in text
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise OperationalValidationError("path must be canonical repository-relative")
    return text


def _path_is_under(path: str, root: str) -> bool:
    if root == ".":
        return True
    return path == root or path.startswith(f"{root}/")


def _project_path(project_root: str, path: str) -> str:
    return path if project_root == "." else f"{project_root}/{path}"


__all__ = [
    "WORKSPACE_OPERATIONAL_VALIDATION_CONTRACT",
    "OperationalValidationError",
    "OperationalValidationPlan",
    "OperationalValidationProfile",
    "OperationalValidationReceipt",
    "OperationalValidationSourceSelection",
    "OperationalValidationSuite",
    "OperationalValidationSuiteReceipt",
    "SourcePackageCoordinate",
    "ValidationCurrentnessPolicy",
    "ValidationCurrentnessStatus",
    "ValidationEffectClass",
    "ValidationExecutionStatus",
    "WorkspaceValidationSourceCoordinate",
    "content_digest",
    "source_coordinate_from_payload",
    "validate_test_resource_outcome",
]
