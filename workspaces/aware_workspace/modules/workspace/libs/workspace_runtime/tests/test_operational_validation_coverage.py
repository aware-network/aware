from __future__ import annotations

from dataclasses import replace

import pytest
from aware_workspace_runtime.operational_validation import (
    OperationalValidationError,
    OperationalValidationPlan,
    OperationalValidationProfile,
    OperationalValidationReceipt,
    OperationalValidationSourceSelection,
    OperationalValidationSuite,
    OperationalValidationSuiteReceipt,
    SourcePackageCoordinate,
    ValidationCurrentnessPolicy,
    ValidationEffectClass,
    ValidationExecutionStatus,
    WorkspaceValidationSourceCoordinate,
    _digest,
    _path,
    _path_is_under,
    _project_path,
    _required,
    source_coordinate_from_payload,
)


def _sha(character: str) -> str:
    return "sha256:" + character * 64


def _suite(**changes: object) -> OperationalValidationSuite:
    values: dict[str, object] = {
        "key": "governance",
        "project_root": ".",
        "interpreter_path": ".venv/bin/python",
        "test_paths": ("tests/test_governance.py",),
        "effect_class": ValidationEffectClass.TEMPORARY_FILESYSTEM,
        "timeout_seconds": 30,
    }
    values.update(changes)
    return OperationalValidationSuite(**values)  # type: ignore[arg-type]


def _selection(**changes: object) -> OperationalValidationSourceSelection:
    values: dict[str, object] = {
        "key": "root",
        "package_root": ".",
        "manifest_path": "pyproject.toml",
        "language_key": "python",
        "toolchain_key": "uv-pytest",
        "source_paths": ("tests/test_governance.py",),
        "test_paths": ("tests/test_governance.py",),
    }
    values.update(changes)
    return OperationalValidationSourceSelection(**values)  # type: ignore[arg-type]


def _profile(**changes: object) -> OperationalValidationProfile:
    values: dict[str, object] = {
        "key": "agent-operational-core",
        "revision": "v1",
        "suites": (_suite(),),
        "lock_paths": ("uv.lock",),
        "source_selections": (_selection(),),
        "currentness_policy": ValidationCurrentnessPolicy.AUTHORED_COMPLETE_SELECTION,
    }
    values.update(changes)
    return OperationalValidationProfile(**values)  # type: ignore[arg-type]


def _coordinate(**changes: object) -> WorkspaceValidationSourceCoordinate:
    values: dict[str, object] = {
        "repository_binding_ref": "local-root:test",
        "epoch": "epoch:one",
        "cursor": 1,
        "snapshot_digest": _sha("a"),
    }
    values.update(changes)
    return WorkspaceValidationSourceCoordinate(**values)  # type: ignore[arg-type]


def _package(**changes: object) -> SourcePackageCoordinate:
    values: dict[str, object] = {
        "package_root": ".",
        "manifest_path": "pyproject.toml",
        "manifest_digest": _sha("b"),
        "language_key": "python",
        "toolchain_key": "uv-pytest",
    }
    values.update(changes)
    return SourcePackageCoordinate(**values)  # type: ignore[arg-type]


def _plan(**changes: object) -> OperationalValidationPlan:
    values: dict[str, object] = {
        "source": _coordinate(),
        "profile": _profile(),
        "selected_source_digests": (
            ("pyproject.toml", _sha("b")),
            ("tests/test_governance.py", _sha("c")),
            ("uv.lock", _sha("d")),
        ),
        "package_coordinates": (_package(),),
        "lock_digests": (("uv.lock", _sha("d")),),
        "runner_fingerprint": _sha("e"),
        "environment_fingerprint": _sha("f"),
    }
    values.update(changes)
    return OperationalValidationPlan(**values)  # type: ignore[arg-type]


def _suite_receipt(**changes: object) -> OperationalValidationSuiteReceipt:
    values: dict[str, object] = {
        "suite_key": "governance",
        "status": ValidationExecutionStatus.PASSED,
        "command": _suite().command,
        "exit_code": 0,
        "duration_ms": 1,
        "output_tail": "passed",
    }
    values.update(changes)
    return OperationalValidationSuiteReceipt(**values)  # type: ignore[arg-type]


def _receipt(**changes: object) -> OperationalValidationReceipt:
    plan_value = changes.pop("plan", _plan())
    assert isinstance(plan_value, OperationalValidationPlan)
    plan = plan_value
    values: dict[str, object] = {
        "plan": plan,
        "status": ValidationExecutionStatus.PASSED,
        "suite_receipts": (_suite_receipt(),),
        "completed_source": plan.source,
        "completed_currentness_state_digest": plan.currentness_state_digest,
        "started_at": "2026-08-30T00:00:00+00:00",
        "completed_at": "2026-08-30T00:00:01+00:00",
        "worker_generation_ref": "validation-worker:one",
    }
    values.update(changes)
    return OperationalValidationReceipt(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("cursor", [True, -1])
def test_source_coordinate_rejects_invalid_cursor(cursor: object) -> None:
    with pytest.raises(OperationalValidationError, match="cursor"):
        _coordinate(cursor=cursor)


def test_source_package_accepts_explicit_canonical_reference() -> None:
    coordinate = _package(canonical_code_package_ref="code-package:one")
    assert coordinate.canonical_code_package_ref == "code-package:one"
    with pytest.raises(OperationalValidationError, match="non-empty"):
        _package(canonical_code_package_ref="")


@pytest.mark.parametrize(
    "changes",
    [
        {"source_paths": ()},
        {"test_paths": ()},
        {
            "source_paths": ("src/one.py",),
            "test_paths": ("tests/test_one.py",),
        },
    ],
)
def test_source_selection_rejects_incomplete_or_noncovered_tests(
    changes: dict[str, object],
) -> None:
    with pytest.raises(OperationalValidationError):
        _selection(**changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"test_paths": ()},
        {"test_paths": ("tests/test_governance.py", "tests/test_governance.py")},
        {"timeout_seconds": 0},
    ],
)
def test_suite_rejects_empty_duplicate_or_nonpositive_inputs(
    changes: dict[str, object],
) -> None:
    with pytest.raises(OperationalValidationError):
        _suite(**changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"suites": ()},
        {"suites": (_suite(), _suite())},
        {"source_selections": ()},
        {"source_selections": (_selection(), _selection())},
        {"lock_paths": ()},
        {"suites": (replace(_suite(), test_paths=("tests/other.py",)),)},
    ],
)
def test_profile_rejects_incomplete_or_mismatched_contract(
    changes: dict[str, object],
) -> None:
    with pytest.raises(OperationalValidationError):
        _profile(**changes)


def test_profile_payload_and_path_unions_are_explicit() -> None:
    profile = _profile()
    payload = profile.to_payload()
    assert payload["profile_digest"] == profile.profile_digest
    assert profile.source_paths == ("tests/test_governance.py",)
    assert profile.currentness_paths == (
        "pyproject.toml",
        "tests/test_governance.py",
        "uv.lock",
    )


def test_plan_rejects_coordinate_count_and_authored_coordinate_drift() -> None:
    with pytest.raises(OperationalValidationError, match="match profile"):
        _plan(package_coordinates=())
    for coordinate in (
        _package(package_root="other"),
        _package(manifest_path="other.toml"),
        _package(language_key="rust"),
        _package(toolchain_key="cargo"),
        _package(canonical_code_package_ref="code-package:one"),
    ):
        with pytest.raises(OperationalValidationError, match="authored selection"):
            _plan(package_coordinates=(coordinate,))


def test_plan_rejects_source_set_and_manifest_digest_drift() -> None:
    with pytest.raises(OperationalValidationError, match="currentness paths"):
        _plan(selected_source_digests=(("pyproject.toml", _sha("b")),))
    with pytest.raises(OperationalValidationError, match="manifest digest"):
        _plan(package_coordinates=(_package(manifest_digest=_sha("9")),))


def test_suite_receipt_rejects_empty_command_and_negative_duration() -> None:
    with pytest.raises(OperationalValidationError, match="command"):
        _suite_receipt(command=())
    with pytest.raises(OperationalValidationError, match="duration"):
        _suite_receipt(duration_ms=-1)
    receipt = _suite_receipt(diagnostic_code="test_failed")
    assert receipt.to_payload()["diagnostic_code"] == "test_failed"


def test_receipt_rejects_suite_order_and_unstable_pass() -> None:
    with pytest.raises(OperationalValidationError, match="suite receipts"):
        _receipt(suite_receipts=())
    with pytest.raises(OperationalValidationError, match="stable selected source"):
        _receipt(completed_source=None)
    with pytest.raises(OperationalValidationError, match="stable selected source"):
        _receipt(completed_currentness_state_digest=_sha("0"))


def test_nonpassed_receipt_accepts_absent_source_and_diagnostic() -> None:
    receipt = _receipt(
        status=ValidationExecutionStatus.INFRASTRUCTURE_FAILED,
        completed_source=None,
        completed_currentness_state_digest=None,
        diagnostic_code="source_unavailable",
    )
    assert receipt.identity_payload()["completed_source"] is None
    assert receipt.to_payload()["diagnostic_code"] == "source_unavailable"


def test_source_coordinate_payload_accepts_exact_shape_and_rejects_invalid() -> None:
    coordinate = source_coordinate_from_payload(
        {
            "binding_key": "local-root:test",
            "epoch": "epoch:one",
            "cursor": 1,
            "snapshot_digest": _sha("a"),
        }
    )
    assert coordinate.repository_binding_ref == "local-root:test"
    for payload in (
        {},
        {
            "binding_key": "local-root:test",
            "epoch": "epoch:one",
            "cursor": True,
            "snapshot_digest": _sha("a"),
        },
    ):
        with pytest.raises(OperationalValidationError, match="payload fields"):
            source_coordinate_from_payload(payload)


@pytest.mark.parametrize("value", [None, 1, "", "   "])
def test_required_rejects_non_text_or_empty(value: object) -> None:
    with pytest.raises(OperationalValidationError, match="non-empty"):
        _required(value, "field")


def test_required_normalizes_surrounding_whitespace() -> None:
    assert _required(" value ", "field") == "value"


@pytest.mark.parametrize(
    "value",
    ["md5:" + "0" * 64, "sha256:short", "sha256:" + "G" * 64],
)
def test_digest_rejects_noncanonical_values(value: str) -> None:
    with pytest.raises(OperationalValidationError, match="sha256"):
        _digest(value, "digest")


@pytest.mark.parametrize(
    "value",
    ["/absolute", "non\\posix", "a/../b", "a/./b"],
)
def test_path_rejects_noncanonical_values(value: str) -> None:
    with pytest.raises(OperationalValidationError, match="canonical"):
        _path(value)


def test_path_relationship_and_project_join_cover_root_and_nested_packages() -> None:
    assert _path(".", allow_dot=True) == "."
    assert _path_is_under("anything", ".")
    assert _path_is_under("workspaces/example", "workspaces/example")
    assert _path_is_under("workspaces/example/test.py", "workspaces/example")
    assert not _path_is_under("workspaces/other/test.py", "workspaces/example")
    assert _project_path(".", "tests/test.py") == "tests/test.py"
    assert _project_path("workspaces/example", "tests/test.py") == (
        "workspaces/example/tests/test.py"
    )
