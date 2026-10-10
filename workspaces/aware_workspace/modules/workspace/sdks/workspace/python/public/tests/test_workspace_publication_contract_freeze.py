"""Publication contract preparation diagnostics; no executable admission/writer.

Signatures are checked as documentation AST. No contract block is executed and
no fake permit/provider is used to claim authorization or publication readiness.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "aware.repo.toml").is_file()
)
WORKSPACE = Path("workspaces/aware_workspace/modules/workspace")
WORKFLOW = Path("workspaces/aware_coordination/modules/workflow")
SDK = WORKSPACE / "sdks/workspace/python/public/aware_workspace_sdk"
INPUTS = Path("docs/reports/workspace-publication-sdk-contract-inputs-20261009.json")
REPORT = Path("docs/reports/workspace-publication-sdk-contract-freeze-20261009.md")
PINS = (
    Path("docs/reports/workspace-sdk-runtime-physical-split-inputs-20261009.json"),
    WORKSPACE / "aware.module.toml",
    WORKSPACE / "sdks/workspace/aware/workspace_sdk.aware",
    WORKSPACE / "sdks/workspace/python/public/pyproject.toml",
    WORKSPACE / "libs/workspace_runtime/pyproject.toml",
    WORKSPACE / "libs/workspace_operator/python/pyproject.toml",
    WORKSPACE / "libs/workspace_operator/python/aware_workspace_operator/models.py",
    WORKSPACE / "libs/workspace_operator/python/aware_workspace_operator/commit.py",
    WORKFLOW / "sdks/issue/python/pyproject.toml",
    WORKFLOW / "sdks/issue/python/aware_issue_sdk/operation.py",
    WORKFLOW / "sdks/issue/filesystem_adapter/python/pyproject.toml",
    WORKFLOW
    / "sdks/issue/filesystem_adapter/python/aware_issue_fs_adapter/provider.py",
    WORKFLOW / "libs/issue_runtime/pyproject.toml",
    WORKFLOW / "libs/issue_operational_runtime/pyproject.toml",
    WORKFLOW
    / "libs/issue_operational_runtime/aware_issue_operational_runtime/source_scope_policy.py",
)


def body(path: Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def snapshot() -> dict[str, object]:
    modules = {}
    for path in sorted((ROOT / SDK).rglob("*.py")):
        relative = path.relative_to(ROOT / SDK)
        suffix = relative.with_suffix("").as_posix().replace("/", ".")
        if suffix.endswith(".__init__"):
            suffix = suffix.removesuffix(".__init__")
        suffix = "" if suffix == "__init__" else "." + suffix
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = sorted(
            node.name
            for node in tree.body
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and not node.name.startswith("_")
        )
        modules["aware_workspace_sdk" + suffix] = {
            "source_path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "declared_public_bodies": names,
            "disposition": "rewrite_neutral_root"
            if not suffix
            else "move_internal_service_compatibility",
            "target_module": "aware_workspace_sdk"
            if not suffix
            else "aware_workspace_service_sdk_adapter" + suffix,
        }
    candidates = subprocess.run(
        ["rg", "-l", "aware_workspace_sdk", "workspaces", "tools", "--glob", "*.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    consumers = {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in sorted(candidates)
        if not Path(path).is_relative_to(SDK)
        and path != Path(__file__).relative_to(ROOT).as_posix()
    }
    return {
        "purpose": "bounded-publication-contract-predecessor-pins-and-legacy-sdk-disposition",
        "implemented": False,
        "pins": {
            path.as_posix(): hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in PINS
        },
        "sdk_modules": modules,
        "external_text_reference_candidates": consumers,
    }


def _signature_tree() -> ast.Module:
    signatures = body(REPORT).split("<!-- normative-signatures-start -->", 1)[1]
    signatures = signatures.split("<!-- normative-signatures-end -->", 1)[0]
    return ast.parse(signatures.split("```python\n", 1)[1].split("```", 1)[0])


def _class(name: str) -> ast.ClassDef:
    return next(
        node
        for node in _signature_tree().body
        if isinstance(node, ast.ClassDef) and node.name == name
    )


def _methods(name: str) -> dict[str, ast.FunctionDef]:
    return {
        node.name: node
        for node in _class(name).body
        if isinstance(node, ast.FunctionDef)
    }


def _fields(name: str) -> dict[str, str]:
    return {
        node.target.id: ast.unparse(node.annotation)
        for node in _class(name).body
        if isinstance(node, ast.AnnAssign)
    }


def _arguments(method: ast.FunctionDef) -> dict[str, str]:
    return {
        arg.arg: ast.unparse(arg.annotation)
        for arg in method.args.args
        if arg.annotation
    }


def test_all_fifteen_predecessor_pins_and_sdk_module_dispositions_are_current() -> None:
    assert json.loads(body(INPUTS)) == snapshot()


def test_no_old_sdk_module_or_declared_public_body_is_silently_dropped() -> None:
    rows = snapshot()["sdk_modules"]
    assert len(rows) == 173
    assert rows["aware_workspace_sdk"]["disposition"] == "rewrite_neutral_root"
    for source, row in rows.items():
        if source == "aware_workspace_sdk":
            continue
        assert row["target_module"] == source.replace(
            "aware_workspace_sdk", "aware_workspace_service_sdk_adapter", 1
        )
        assert row["disposition"] == "move_internal_service_compatibility"


def test_workspace_publication_and_recovery_are_explicit_sdk_methods() -> None:
    assert set(_methods("WorkspaceRepositoryPublicationClient")) == {
        "plan_repository_commit",
        "verify_repository_plan",
        "observe_repository_attempt",
        "publish_repository_commit",
        "finish_repository_publication",
        "observe_repository_publication",
        "reconcile_repository_index",
        "release_repository_plan",
        "release_publication_work_admission",
    }


def test_issue_admission_and_consumption_have_distinct_owner_ports() -> None:
    assert set(_methods("IssueRepositoryPublicationClient")) == {
        "admit_repository_publication",
        "bind_closeout_publication",
        "consume_repository_publication",
        "enroll_repository_publication",
        "finish_repository_publication",
        "observe_repository_publication_admission",
        "release_repository_publication_admission",
        "release_repository_publication_enrollment",
        "prepare_repository_closeout",
        "apply_repository_closeout_source",
        "finish_repository_closeout",
        "release_repository_closeout",
    }


def test_issue_closeout_requires_an_original_close_admission() -> None:
    method = _methods("IssueRepositoryPublicationClient")["bind_closeout_publication"]
    args = {
        arg.arg: ast.unparse(arg.annotation)
        for arg in method.args.args
        if arg.annotation
    }
    assert args["close_admission"] == "IssueCloseAdmission"
    assert args["binding"] == "IssueRepositoryPublicationBinding"


def test_fs_port_does_not_call_issue_or_workspace_sdk() -> None:
    methods = _methods("WorkspaceRepositoryPublicationPhysicalPort")
    assert set(methods) == {
        "capture",
        "begin",
        "publish",
        "observe",
        "reconcile",
        "release",
        "observe_transaction_release",
    }
    for method in methods.values():
        assert len(method.body) == 1
        assert isinstance(method.body[0], ast.Expr)
        assert isinstance(method.body[0].value, ast.Constant)
        assert method.body[0].value.value is Ellipsis


@pytest.mark.parametrize(
    "field",
    (
        "publication_state",
        "reference_update",
        "index_projection",
        "cleanup_state",
        "lock_release",
        "admission_completion",
        "ledger_complete",
    ),
)
def test_result_separates_publication_from_later_effects(field: str) -> None:
    fields = {
        node.target.id
        for node in _class("WorkspaceRepositoryCommitResult").body
        if isinstance(node, ast.AnnAssign)
    }
    assert field in fields


def test_commit_request_is_not_a_caller_authorization_boolean() -> None:
    fields = {
        node.target.id
        for node in _class("WorkspaceRepositoryCommitRequest").body
        if isinstance(node, ast.AnnAssign)
    }
    assert (
        not {
            "authorized",
            "issue_status",
            "ownership_scope",
            "owner_id",
            "admission_ref",
        }
        & fields
    )
    assert {"repository_ref", "target_paths", "message", "attempt_ref"} <= fields


def test_plan_verification_is_a_public_owner_port_without_publication_receipt() -> None:
    method = _methods("WorkspaceRepositoryPublicationClient")["verify_repository_plan"]
    assert _arguments(method) == {
        "request": "WorkspaceRepositoryPlanVerificationRequest"
    }
    assert ast.unparse(method.returns) == "WorkspaceRepositoryPlanVerification"
    assert _fields("WorkspaceRepositoryPlanVerificationRequest") == {
        "binding": "WorkspaceRepositoryPublicationBinding"
    }
    assert {
        "provider_ref",
        "provider_generation",
        "execution_id",
    } <= _fields("WorkspaceRepositoryPublicationBinding").keys()


def test_failed_attempt_observation_does_not_require_a_publication_receipt() -> None:
    assert _fields("WorkspaceRepositoryAttemptObserveRequest") == {
        "repository_ref": "str",
        "binding_ref": "str",
        "attempt_ref": "str",
        "provider_ref": "str",
        "provider_generation": "str",
        "execution_id": "str",
    }
    assert _fields("WorkspaceRepositoryAttemptObservation")["result"] == (
        "WorkspaceRepositoryCommitResult | None"
    )
    assert _fields("WorkspaceRepositoryAttemptObservation")["plan_observation"] == (
        "WorkspacePublicationPlanObservation | None"
    )


def test_genuine_issue_enrollment_bridges_to_workspace_owned_admission() -> None:
    method = _methods("WorkspaceIssuePublicationEnrollmentClient")[
        "enroll_issue_repository_publication"
    ]
    assert _arguments(method) == {
        "plan": "WorkspaceRepositoryCommitPlan",
        "admission": "IssueRepositoryPublicationAdmission",
    }
    assert ast.unparse(method.returns) == "WorkspacePublicationWorkAdmission"
    method = _methods("IssueRepositoryPublicationClient")[
        "enroll_repository_publication"
    ]
    assert _arguments(method) == {
        "admission": "IssueRepositoryPublicationAdmission",
        "request": "IssueRepositoryPublicationEnrollmentRequest",
    }
    assert ast.unparse(method.returns) == "IssueRepositoryPublicationEnrollment"
    consume = _methods("IssueRepositoryPublicationClient")[
        "consume_repository_publication"
    ]
    assert _arguments(consume) == {
        "enrollment": "IssueRepositoryPublicationEnrollment",
        "request": "IssueRepositoryPublicationConsumeRequest",
    }
    assert _fields("IssueRepositoryPublicationLease")["receipt_ref"] == "str"


def test_finish_continuation_accepts_original_admission_not_caller_result() -> None:
    method = _methods("WorkspaceRepositoryPublicationClient")[
        "finish_repository_publication"
    ]
    assert _arguments(method) == {"admission": "WorkspacePublicationWorkAdmission"}
    assert ast.unparse(method.returns) == "WorkspaceRepositoryCommitResult"


def test_repository_lock_release_is_explicit_original_transaction_evidence() -> None:
    fields = _fields("WorkspaceRepositoryLockReleaseObservation")
    assert fields == {
        "binding_ref": "str",
        "attempt_ref": "str",
        "provider_ref": "str",
        "provider_generation": "str",
        "transaction_ref": "str",
        "release_observation_ref": "str",
        "repository_lock_release": (
            "Literal['not_acquired', 'confirmed_released', 'not_released', 'unknown']"
        ),
        "diagnostics": "tuple[str, ...]",
    }
    assert _fields("WorkspacePublicationCleanupObservation")["lock_release"] == (
        "WorkspaceRepositoryLockReleaseObservation | None"
    )
    method = _methods("WorkspaceRepositoryPublicationPhysicalPort")[
        "observe_transaction_release"
    ]
    assert _arguments(method) == {
        "transaction": "WorkspacePublicationPhysicalTransaction"
    }


def test_contract_requires_release_confirmation_and_original_owner_verification() -> (
    None
):
    # Documentation guard only: the future owner/race tests are not simulated here.
    contract = body(REPORT)
    assert 'Only `repository_lock_release="confirmed_released"` permits reciprocal' in (
        contract
    )
    assert "no Issue finish/verification callback" in contract
    assert "without\na publication receipt" in contract
    assert "does not acquire the repository operation lock" in contract
    assert "must not begin a transaction, spend again, call the writer" in contract
    assert "must not switch to the receipt-based\nobserver" in contract
    assert (
        "repository-lock-free behavior is an explicit implementation qualification"
        in (contract)
    )


def test_neutral_writer_evidence_preserves_all_original_report_fields_and_types() -> (
    None
):
    original = next(
        node
        for node in ast.parse(
            body(
                WORKSPACE
                / "libs/workspace_operator/python/aware_workspace_operator/models.py"
            )
        ).body
        if isinstance(node, ast.ClassDef) and node.name == "WorkspaceCommitReport"
    )
    fields = {
        node.target.id: ast.dump(node.annotation)
        for node in original.body
        if isinstance(node, ast.AnnAssign)
    }
    successor = {
        node.target.id: ast.dump(node.annotation)
        for node in _class("WorkspaceRepositoryWriterObservation").body
        if isinstance(node, ast.AnnAssign)
    }
    assert fields == successor
    assert len(fields) == 32


def test_effect_carrier_has_typed_identity_mode_durability_and_no_opaque_object() -> (
    None
):
    annotations = {
        node.target.id: ast.unparse(node.annotation)
        for node in _class("WorkspaceRepositoryPhysicalEffect").body
        if isinstance(node, ast.AnnAssign)
    }
    assert {
        "before_identity",
        "after_identity",
        "mode",
        "durability_confirmed",
        "diagnostics",
    } <= annotations.keys()
    result = next(
        node
        for node in _class("WorkspaceRepositoryCommitResult").body
        if isinstance(node, ast.AnnAssign) and node.target.id == "effects"
    )
    assert (
        ast.unparse(result.annotation)
        == "tuple[WorkspaceRepositoryPhysicalEffect, ...]"
    )


def test_signatures_are_not_a_second_executable_operation_catalog() -> None:
    tree = _signature_tree()
    assert not any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in tree.body)
    assert all(isinstance(node, ast.ClassDef) for node in tree.body)
    assert json.loads(body(INPUTS))["implemented"] is False


@pytest.mark.parametrize(
    "name",
    (
        "WorkspaceRepositoryCommitPlan",
        "WorkspacePublicationWorkAdmission",
        "IssueRepositoryPublicationEnrollment",
        "IssueRepositoryPublicationAdmission",
        "IssueRepositoryPublicationLease",
        "WorkspacePublicationExecutionClaim",
        "IssueCloseAdmission",
    ),
)
def test_handles_are_separate_from_serializable_evidence(name: str) -> None:
    handle = _class(name)
    assert not handle.decorator_list
    assert not any(
        isinstance(node, ast.FunctionDef)
        and node.name in {"from_payload", "from_json", "decode"}
        for node in handle.body
    )


def test_existing_sdk_still_has_the_historical_service_generation() -> None:
    metadata = tomllib.loads(
        body(WORKSPACE / "sdks/workspace/python/public/pyproject.toml")
    )
    assert metadata["project"]["version"] == "0.1.0"
    assert "aware_workspace_service_api" in metadata["project"]["dependencies"]


if __name__ == "__main__":
    print(json.dumps(snapshot(), indent=2, sort_keys=True))
