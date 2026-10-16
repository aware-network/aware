"""Real original suppliers through the public SDK and Agent command; no fake issuer."""

from __future__ import annotations

import argparse
import gc
import importlib
import json
import os
import weakref
from pathlib import Path

import pytest
from aware_issue_sdk.workspace_setup_admission import (
    IssueWorkspaceSetupAdmissionClient,
    IssueWorkspaceSetupRefusal,
)
from aware_issue_sdk.workspace_setup_admission_values import IssueWorkspaceSetupRequest
from aware_workspace_command.architecture_setup_a1_command import run_a1
from aware_workspace_command.architecture_setup_a1_command_values import (
    WorkspaceSetupA1CommandEvidence,
    command_value_from_payload,
)
from aware_workspace_command.architecture_setup_command import (
    configure_workspace_setup_parser,
)
from aware_workspace_sdk.architecture_setup import (
    ArchitectureSetupError,
    ArchitectureSetupRequest,
    WorkspaceSetupClient,
)
from aware_workspace_sdk.architecture_setup_admission import observe_original_setup_plan

REPO = Path(__file__).resolve().parents[7]
ISSUE = "docs/issues/2026/10/14/fb-2026-10-14-a1-proof.md"


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "a1-original-supplier-test")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    (tmp_path / "docs/goals").mkdir(parents=True)
    (tmp_path / ISSUE).parent.mkdir(parents=True)
    (tmp_path / "AGENTS.md").write_text("# disposable A1 proof\n")
    (tmp_path / "aware.protocol.toml").write_bytes(
        (REPO / "aware.protocol.toml").read_bytes()
    )
    (tmp_path / ISSUE).write_text(
        "# Issue: A1\n\n- Slug: a1-proof\n- Tag: fb/2026-10-14/a1-proof\n- Status: In Progress\n- Owner: codex-a1-original-supplier-test\n- Priority: P1\n- Captured: 2026-10-14\n- Recorder: codex-a1-original-supplier-test\n- Source: disposable proof\n\n## Ownership Scope\n- `aware.repo.toml`\n- `libs`\n"
    )
    return tmp_path


def files(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }


def arguments(root, *extra):
    parser = argparse.ArgumentParser()
    configure_workspace_setup_parser(parser)
    return parser.parse_args(
        [
            "repository",
            "--repository-root",
            str(root),
            "--name",
            "example",
            "--license-expression",
            "MIT",
            "--governed",
            "--issue-ref",
            ISSUE,
            "--authority-manifest",
            "aware.protocol.toml",
            "--client-intent-id",
            "intent:original",
            *extra,
        ]
    )


def prepared(root):
    workspace = WorkspaceSetupClient.filesystem(repository_root=root)
    issuer = IssueWorkspaceSetupAdmissionClient.filesystem(
        repository_root=root,
        execution_id="codex-a1-original-supplier-test",
        authority_manifest_locator="aware.protocol.toml",
    )
    request = ArchitectureSetupRequest(
        "repository", name="example", license_expression="MIT"
    )
    plan = workspace.prepare_setup(
        request, expected_plan_sha256=workspace.preview(request).plan_sha256
    )
    binding = observe_original_setup_plan(plan).binding
    scope(root, binding)
    sources = issuer.observe_authority_sources(issue_ref=ISSUE)
    issue_plan = issuer.prepare_setup_admission(
        IssueWorkspaceSetupRequest(
            ISSUE,
            sources.issue_source.content_sha256,
            None,
            None,
            "intent:original",
            "workspace_setup_a1_v1",
            sources.authority_manifest_source.content_sha256,
        ),
        workspace_plan=plan,
        expected_binding=binding,
    )
    admission = workspace.enroll_setup_admission(
        plan, issue_admission=issuer.admit_setup(issue_plan)
    )
    return workspace, issuer, plan, issue_plan, admission


def scope(root, binding):
    paths = sorted(
        {
            path
            for step in binding.ordered_effects
            for path in (step.primary_path, *step.auxiliary_paths)
        }
    )
    with (root / ISSUE).open("a") as stream:
        for path in paths:
            stream.write("- `" + path + "`\n")


def test_agent_preview_apply_real_creation_and_closed_receipts(root, capsys):
    agent = importlib.import_module("aware_agent_cli.main")
    raw = [
        "repository",
        "--repository-root",
        str(root),
        "--name",
        "example",
        "--license-expression",
        "MIT",
        "--governed",
        "--issue-ref",
        ISSUE,
        "--authority-manifest",
        "aware.protocol.toml",
        "--client-intent-id",
        "intent:original",
        "--json",
    ]
    before = files(root)
    assert agent.main(["workspace", "setup", *raw]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert files(root) == before
    view = command_value_from_payload(WorkspaceSetupA1CommandEvidence, preview)
    assert view.command_status == "preview_completed"
    assert view.issue_observation is None
    scope(root, view.workspace_observation.binding)
    evidence, code = run_a1(arguments(root))
    assert code == 0
    guards = evidence.review_guards
    assert (
        evidence.workspace_observation.binding.file_transitions[0].scratch_path
        == view.workspace_observation.binding.file_transitions[0].scratch_path
    )
    apply = [
        "--apply",
        "--allowed-path",
        "aware.repo.toml",
        "--issue-source-sha256",
        guards.issue_source_sha256,
        "--authority-manifest-sha256",
        guards.authority_manifest_sha256,
        "--expected-plan-sha256",
        guards.plan_sha256,
    ]
    assert agent.main(["workspace", "setup", *raw, *apply]) == 0
    result = command_value_from_payload(
        WorkspaceSetupA1CommandEvidence, json.loads(capsys.readouterr().out)
    )
    assert result.command_status == "apply_completed" and result.completion_verified
    assert result.issue_observation.consumption_ref is not None
    assert (
        result.issue_observation.verified_effect_ordinal
        == len(result.workspace_observation.binding.ordered_effects) - 1
    )
    assert result.workspace_result.original_receipt.written_paths == (
        "aware.repo.toml",
    )
    assert (
        result.plan_cleanup.release == result.admission_cleanup.outcome == "confirmed"
    )
    assert (
        result.client_cleanup.issue.outcome
        == result.client_cleanup.workspace.outcome
        == "confirmed"
    )
    assert not tuple(root.glob(".aware-cas-*"))
    assert agent.main(["workspace", "setup", *raw, *apply]) == 2
    replay = json.loads(capsys.readouterr().out)
    assert not replay["completion_verified"] and not replay["authorizes_retry"]
    assert replay["workspace_result"] is None


def test_original_admission_replay_and_data_only_binding_refuse(root):
    workspace, issuer, plan, issue_plan, admission = prepared(root)
    try:
        with pytest.raises(IssueWorkspaceSetupRefusal):
            issuer.admit_setup(issue_plan)
        with pytest.raises(ArchitectureSetupError):
            workspace.apply_setup_plan(plan, admission=admission)
        assert not (root / "aware.repo.toml").exists()
    finally:
        assert workspace.release_setup_plan(plan).release == "confirmed"
        assert issuer.release_setup_admission(issue_plan).outcome == "confirmed"
        assert (
            issuer.release_client().outcome
            == workspace.release_client().outcome
            == "confirmed"
        )


@pytest.mark.parametrize("target", ["issue", "manifest", "input"])
def test_drift_refuses_without_namespace_effects_and_cleanup_survives(root, target):
    workspace, issuer, plan, issue_plan, admission = prepared(root)
    path = root / (
        ISSUE
        if target == "issue"
        else "aware.protocol.toml"
        if target == "manifest"
        else "aware.repo.toml"
    )
    path.write_bytes((path.read_bytes() if path.exists() else b"") + b"\n# drift\n")
    changed = path.read_bytes()
    try:
        with pytest.raises(ArchitectureSetupError):
            workspace.apply_setup_plan(plan, admission=admission)
        assert path.read_bytes() == changed
        if target != "input":
            assert not (root / "aware.repo.toml").exists()
        assert not tuple(root.glob(".aware-cas-*"))
        assert workspace.release_setup_plan(plan).release == "confirmed"
        assert issuer.release_setup_admission(issue_plan).outcome == "confirmed"
    finally:
        issuer.release_client()
        workspace.release_client()


def test_issue_client_collection_revokes_family_while_plan_exists(root):
    workspace, issuer, plan, _issue_plan, admission = prepared(root)
    ref = weakref.ref(issuer)
    del issuer
    gc.collect()
    assert ref() is None
    with pytest.raises(ArchitectureSetupError):
        workspace.apply_setup_plan(plan, admission=admission)
    assert not (root / "aware.repo.toml").exists()
    assert workspace.release_client().outcome == "confirmed"


def test_workspace_client_collection_closes_original_root_and_sequence(root):
    workspace, issuer, _plan, issue_plan, _admission = prepared(root)
    from aware_workspace_sdk import architecture_setup_admission as custody

    state = custody._CLIENTS[id(workspace)][1]
    physical = state.physical
    ref = weakref.ref(workspace)
    del workspace
    gc.collect()
    assert ref() is None and physical.fd == -1
    assert state.cleanup.outcome == "confirmed"
    assert issuer.release_setup_admission(issue_plan).outcome == "confirmed"
    issuer.release_client()


def test_issue_original_dispatch_substitution_never_calls_foreign(root, monkeypatch):
    workspace, issuer, plan, issue_plan, admission = prepared(root)
    from aware_issue_operational_runtime.workspace_setup_admission import (
        IssueWorkspaceSetupRuntime,
    )

    calls = []
    monkeypatch.setattr(
        IssueWorkspaceSetupRuntime, "consume", lambda *a, **k: calls.append(True)
    )
    try:
        with pytest.raises(ArchitectureSetupError):
            workspace.apply_setup_plan(plan, admission=admission)
        assert not calls and not (root / "aware.repo.toml").exists()
        assert issuer.release_setup_admission(issue_plan).outcome == "confirmed"
        assert issuer.release_client().outcome == "confirmed"
    finally:
        workspace.release_client()


def test_wrong_review_guard_and_actor_pair_are_pre_effect_refusals(root):
    evidence, code = run_a1(arguments(root, "--actor-ref", "declared:actor"))
    assert code == 2 and not evidence.completion_verified
    assert not (root / "aware.repo.toml").exists()


def test_original_lease_busy_has_typed_confirmed_zero_consumption(root):
    import fcntl

    workspace, issuer, plan, issue_plan, admission = prepared(root)
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        with pytest.raises(ArchitectureSetupError):
            workspace.apply_setup_plan(plan, admission=admission)
        assert issuer.observe_setup_admission(issue_plan).consumption_ref is None
        cleanup = workspace.release_client()
        lease = next(row for row in cleanup.resources if row.kind == "lease")
        assert lease.ownership == "released" and lease.release_outcome == "confirmed"
        assert not (root / "aware.repo.toml").exists()
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)
        issuer.release_client()


def test_governed_four_layers_and_alignment_use_the_same_original_algorithm(root):
    requests = (
        ArchitectureSetupRequest(
            "repository", name="example", license_expression="MIT"
        ),
        ArchitectureSetupRequest("workspace", name="application", path="application"),
        ArchitectureSetupRequest(
            "module", name="domain", workspace="application", path="modules/domain"
        ),
        ArchitectureSetupRequest(
            "python_package",
            name="scalar",
            workspace="application",
            module="domain",
            path="libs/scalar/python",
            distribution="example-scalar",
            import_root="example_scalar",
            owner="module",
        ),
        ArchitectureSetupRequest("package_manager"),
    )
    for index, request in enumerate(requests):
        workspace = WorkspaceSetupClient.filesystem(repository_root=root)
        issuer = IssueWorkspaceSetupAdmissionClient.filesystem(
            repository_root=root,
            execution_id="codex-a1-original-supplier-test",
            authority_manifest_locator="aware.protocol.toml",
        )
        plan = workspace.prepare_setup(
            request, expected_plan_sha256=workspace.preview(request).plan_sha256
        )
        binding = observe_original_setup_plan(plan).binding
        scope(root, binding)
        sources = issuer.observe_authority_sources(issue_ref=ISSUE)
        issued = issuer.prepare_setup_admission(
            IssueWorkspaceSetupRequest(
                ISSUE,
                sources.issue_source.content_sha256,
                None,
                None,
                "intent:layer:" + str(index),
                "workspace_setup_a1_v1",
                sources.authority_manifest_source.content_sha256,
            ),
            workspace_plan=plan,
            expected_binding=binding,
        )
        admission = workspace.enroll_setup_admission(
            plan, issue_admission=issuer.admit_setup(issued)
        )
        try:
            result = workspace.apply_setup_plan(plan, admission=admission)
            assert result.original_receipt.status in ("succeeded", "unchanged")
            historical = workspace.observe_setup_result(result)
            assert historical.release == "unknown" and historical.ledger_complete
            assert issuer.observe_setup_admission(issued).consumption_ref is not None
        finally:
            assert workspace.release_setup_plan(plan).release == "confirmed"
            assert issuer.release_setup_admission(issued).outcome == "confirmed"
            assert (
                issuer.release_client().outcome
                == workspace.release_client().outcome
                == "confirmed"
            )
        assert result.release == historical.release == "unknown"
    assert (
        root / "workspaces/application/modules/domain/libs/scalar/python/pyproject.toml"
    ).is_file()
    assert (
        root
        / "workspaces/application/modules/domain/libs/scalar/python/src/example_scalar/__init__.py"
    ).is_file()
    assert (root / "pyproject.toml").is_file()
    assert not tuple(root.rglob(".aware-cas-*"))


def test_lost_original_publish_return_keeps_unknown_prefix_without_rollback(root):
    import sys

    from aware_file_system import retained_file_sequence as physical

    workspace, issuer, plan, issue_plan, admission = prepared(root)
    original_code = physical._run_original_step.__code__
    triggered = []

    def interrupt(frame, event, _):
        if (
            frame.f_code is original_code
            and event == "return"
            and frame.f_locals["step"].kind == "target_link"
            and not triggered
        ):
            triggered.append(True)
            raise OSError(
                "test: original syscall returned but owner return was interrupted"
            )
        return interrupt

    previous = sys.gettrace()
    try:
        sys.settrace(interrupt)
        with pytest.raises(ArchitectureSetupError) as caught:
            workspace.apply_setup_plan(plan, admission=admission)
    finally:
        sys.settrace(previous)
    assert triggered and (root / "aware.repo.toml").is_file()
    result = caught.value.result
    effect = next(row for row in result.effects if row.kind == "target_link")
    assert effect.dispatch_state == "attempted" and effect.effect_state == "unknown"
    assert result.original_receipt.status == "uncertain"
    assert result.original_receipt.written_paths == ()
    cleanup = workspace.release_setup_plan(plan)
    assert cleanup.release == "confirmed" and not tuple(root.glob(".aware-cas-*"))
    assert (
        root / "aware.repo.toml"
    ).is_file()  # Observation/cleanup never rolls back publication.
    assert issuer.observe_setup_admission(issue_plan).consumption_ref is not None
    issuer.release_client()
    workspace.release_client()


def test_replaced_issue_port_is_refused_before_foreign_call(root, monkeypatch):
    workspace, issuer, plan, _issue_plan, admission = prepared(root)
    from aware_issue_sdk import workspace_setup_admission as ports

    calls = []
    monkeypatch.setattr(
        ports, "consume_workspace_setup_admission", lambda *a, **k: calls.append(True)
    )
    try:
        with pytest.raises(ArchitectureSetupError):
            workspace.apply_setup_plan(plan, admission=admission)
        assert not calls and not (root / "aware.repo.toml").exists()
    finally:
        issuer.release_client()
        workspace.release_client()


def test_unknown_issue_read_cleanup_is_retained_and_not_retried(root):
    import sys

    from aware_file_system import confined_mutation as native

    issuer = IssueWorkspaceSetupAdmissionClient.filesystem(
        repository_root=root,
        execution_id="codex-a1-original-supplier-test",
        authority_manifest_locator="aware.protocol.toml",
    )
    import inspect

    code = native._ReadLedger.close.__code__
    lines, start = inspect.getsourcelines(native._ReadLedger.close)
    interrupted_line = start + next(
        index for index, line in enumerate(lines) if "self.closed += 1" in line
    )
    original = sys.gettrace()
    calls = []

    def lost_return(frame, event, _):
        if (
            frame.f_code is code
            and event == "line"
            and frame.f_lineno == interrupted_line
            and not calls
        ):
            calls.append(True)
            raise OSError(
                "test: descriptor close returned without admitted cleanup evidence"
            )
        return lost_return

    try:
        sys.settrace(lost_return)
        with pytest.raises(native.ConfinedFileObservationError):
            issuer.observe_authority_sources(issue_ref=ISSUE)
    finally:
        sys.settrace(original)
    cleanup = issuer.release_client()
    assert calls and not cleanup.ledger_complete and cleanup.outcome == "unknown"
    assert cleanup.resources and any(
        row.release_outcome == "unknown" for row in cleanup.resources
    )
    assert issuer.release_client() is cleanup
    assert not (root / "aware.repo.toml").exists()


def test_consumption_and_ordinal_checks_never_call_workspace_in_the_lease(root):
    import sys

    from aware_issue_sdk.workspace_setup_admission import (
        consume_workspace_setup_admission,
        verify_workspace_setup_consumption,
    )
    from aware_workspace_sdk import architecture_setup_admission as owner

    workspace, issuer, plan, _issue_plan, _admission = prepared(root)
    state = owner._PLANS[id(plan)][1]
    observed = []
    forbidden = (
        "aware_workspace_runtime",
        "aware_workspace_fs_adapter",
        "aware_workspace_sdk.architecture_setup_admission",
    )

    def audit(frame, event, _):
        if event == "call" and (
            frame.f_globals.get("__name__", "").startswith(forbidden[:2])
            or frame.f_globals.get("__name__") == forbidden[2]
        ):
            observed.append(frame.f_code.co_name)

    prior = sys.getprofile()
    try:
        with state.client.physical.lease_a1():
            sys.setprofile(audit)
            consumed = consume_workspace_setup_admission(
                state.enrollment, expected_binding=state.binding
            )
            view = verify_workspace_setup_consumption(
                consumed, expected_binding=state.binding, next_effect_ordinal=0
            )
            sys.setprofile(prior)
            assert view.verified_effect_ordinal == 0
        assert observed == []
        with pytest.raises(IssueWorkspaceSetupRefusal):
            verify_workspace_setup_consumption(
                consumed, expected_binding=state.binding, next_effect_ordinal=0
            )
        assert not (root / "aware.repo.toml").exists()
    finally:
        sys.setprofile(prior)
        issuer.release_client()
        workspace.release_client()


def test_partial_client_construction_preserves_original_root_cleanup(root, monkeypatch):
    import inspect
    import sys

    from aware_workspace_fs_adapter.architecture_setup import (
        FilesystemArchitectureSetup,
    )

    original_code = FilesystemArchitectureSetup.__init__.__code__
    lines, start = inspect.getsourcelines(FilesystemArchitectureSetup.__init__)
    stop_line = start + next(
        index
        for index, line in enumerate(lines)
        if "current = os.fstat(self.fd)" in line
    )
    interrupted = []
    previous = sys.gettrace()

    def stop(frame, event, _):
        if (
            event == "line"
            and frame.f_code is original_code
            and frame.f_lineno == stop_line
            and not interrupted
        ):
            interrupted.append(frame.f_locals["self"].fd)
            raise OSError("test: root acquired before construction failure")
        return stop

    try:
        sys.settrace(stop)
        evidence, code = run_a1(arguments(root))
    finally:
        sys.settrace(previous)
    assert code == 2 and interrupted
    assert evidence.client_cleanup.workspace.outcome == "confirmed"
    assert evidence.client_cleanup.workspace.resources[0].release_attempted
    with pytest.raises(OSError):
        os.fstat(interrupted[0])
    assert not (root / "aware.repo.toml").exists()


def test_execution_drift_terminally_revokes_original_issue_right(root, monkeypatch):
    from aware_issue_sdk.workspace_setup_admission import (
        consume_workspace_setup_admission,
    )
    from aware_workspace_sdk import architecture_setup_admission as owner

    workspace, issuer, plan, _issue_plan, admission = prepared(root)
    state = owner._PLANS[id(plan)][1]
    monkeypatch.setenv("CODEX_THREAD_ID", "different-execution")
    with pytest.raises(ArchitectureSetupError):
        workspace.apply_setup_plan(plan, admission=admission)
    monkeypatch.setenv("CODEX_THREAD_ID", "a1-original-supplier-test")
    with pytest.raises(IssueWorkspaceSetupRefusal):
        consume_workspace_setup_admission(
            state.enrollment, expected_binding=state.binding
        )
    assert not (root / "aware.repo.toml").exists()
    issuer.release_client()
    workspace.release_client()
