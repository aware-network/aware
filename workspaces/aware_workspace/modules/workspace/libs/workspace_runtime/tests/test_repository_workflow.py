"""Original profile planning over disposable repos; no distribution effects."""

from __future__ import annotations

import copy
import hashlib
import os
import pickle
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest
from aware_workspace_runtime import package_checkout
from aware_workspace_sdk.repository_workflow import (
    WorkspaceRepositoryWorkflowClient,
    WorkspaceRepositoryWorkflowPlan,
    WorkspaceRepositoryWorkflowRefusal,
)
from aware_workspace_sdk.repository_workflow_values import (
    WorkspaceRepositoryWorkflowRequest,
    WorkspaceWorkflowMarker,
)
from packaging.markers import default_environment


def git(root, *args):
    return (
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)
        .stdout.decode()
        .strip()
    )


def commit(root):
    git(root, "add", ".")
    git(
        root,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-qm",
        "disposable source",
    )
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "workflow-planning-test")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    source, target, state = (tmp_path / name for name in ("source", "target", "state"))
    for root in (source, target):
        root.mkdir()
        git(root, "init", "-q", "--initial-branch=main")
    (source / "aware.repo.toml").write_text(
        'aware_repo=1\n[repo]\nhandle="consumer"\nworkspaces_dir="workspaces"\n'
        '[[workspaces]]\nhandle="main"\npath="main"\n'
        '[[checkout_profile_sets]]\nkey="portable"\nversion=2\n'
        'package_selections=[{workspace="main",module="family",package="a"}]\n'
    )
    workspace = source / "workspaces/main"
    module = workspace / "modules/family"
    module.mkdir(parents=True)
    (workspace / "aware.workspace.toml").write_text(
        'aware=1\n[workspace]\nhandle="main"\n[[workspace.modules]]\n'
        'id="family"\npath="modules/family"\n'
    )
    (module / "aware.module.toml").write_text(
        'aware=1\n[[packages]]\nid="a"\nkind="code"\nmanifest="a/pyproject.toml"\n'
    )
    package = module / "a"
    package.mkdir()
    (package / "pyproject.toml").write_text(
        '[project]\nname="sample-a"\nversion="1.0"\ndependencies=[]\n'
    )
    (package / "source.py").write_text('VALUE="original"\n')
    revision = commit(source)
    request = WorkspaceRepositoryWorkflowRequest(
        "workflow:portable",
        "attempt:1",
        revision,
        "portable",
        "sha256:"
        + hashlib.sha256((source / "aware.repo.toml").read_bytes()).hexdigest(),
        tuple(
            WorkspaceWorkflowMarker(k, v)
            for k, v in sorted(default_environment().items())
        ),
        "refs/heads/main",
        None,
    )
    client = WorkspaceRepositoryWorkflowClient.filesystem(
        source_repository_root=source,
        target_repository_root=target,
        state_root=state,
        execution_id="codex-workflow-planning-test",
    )
    return source, target, state, package, client, request


def test_original_profile_unborn_target_and_no_effects(inputs):
    source, target, state, _, client, request = inputs
    original = package_checkout.PackageSourceCheckout.resolve
    calls = []
    # Original runtime captures this method at import; observe rather than replace it.
    assert original.__name__ == "resolve"
    source_head, target_head = (root / ".git/HEAD" for root in (source, target))
    before = source_head.read_bytes(), target_head.read_bytes()
    plan = client.plan_repository_workflow(request)
    observed = client.observe_repository_workflow_plan(plan)
    assert observed.expected_target_head is None
    assert observed.source_commit == request.source_commit
    assert observed.stages[0].stage == "source_capture"
    assert observed.stages[0].availability == "available"
    assert all(
        stage.availability
        == (
            "available"
            if stage.stage == "evidence_closeout"
            else "supplier_unavailable"
        )
        for stage in observed.stages[1:]
    )
    assert (source_head.read_bytes(), target_head.read_bytes()) == before
    assert not state.exists() and not (target / ".git/index").exists()
    assert calls == []


def test_plan_observation_is_detached(inputs):
    _, target, _, _, client, request = inputs
    plan = client.plan_repository_workflow(request)
    output = client.observe_repository_workflow_plan(plan)
    object.__setattr__(output, "expected_target_head", "a" * 40)
    assert client.observe_repository_workflow_plan(plan).expected_target_head is None
    (target / "foreign.txt").write_text("foreign")
    commit(target)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal, match="stale_target"):
        client.observe_repository_workflow_plan(plan)


@pytest.mark.parametrize("change", ["content", "mode", "untracked", "head"])
def test_selected_source_change_is_terminal(inputs, change):
    source, _, _, package, client, request = inputs
    plan = client.plan_repository_workflow(request)
    path = package / "source.py"
    before = path.read_bytes(), path.stat().st_mode
    if change == "content":
        path.write_text("changed")
    elif change == "mode":
        path.chmod(0o755)
    elif change == "untracked":
        (package / "extra.py").write_text("extra")
    else:
        (source / "unrelated.txt").write_text("new commit")
        commit(source)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.observe_repository_workflow_plan(plan)
    path.write_bytes(before[0])
    path.chmod(before[1])
    (package / "extra.py").unlink(missing_ok=True)
    with pytest.raises(
        WorkspaceRepositoryWorkflowRefusal, match="foreign_or_retired_handle"
    ):
        client.observe_repository_workflow_plan(plan)


def test_dirty_selected_bytes_cannot_claim_head_provenance(inputs):
    _, _, _, package, client, request = inputs
    (package / "source.py").write_text("dirty")
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal, match="stale_source"):
        client.plan_repository_workflow(request)


def test_unrelated_dirty_work_is_not_selected(inputs):
    source, _, _, _, client, request = inputs
    (source / "unrelated.py").write_text("untracked unrelated")
    plan = client.plan_repository_workflow(request)
    assert (
        client.observe_repository_workflow_plan(plan).source_commit
        == request.source_commit
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_commit", "f" * 40),
        ("profile_digest", "sha256:" + "0" * 64),
        ("profile_key", "absent"),
        ("target_reference", "refs/heads/other"),
        ("expected_target_head", "b" * 40),
        ("marker_environment", ()),
    ],
)
def test_substituted_request_refuses_before_plan(inputs, field, value):
    _, _, state, _, client, request = inputs
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.plan_repository_workflow(replace(request, **{field: value}))
    assert not state.exists()


def test_journal_open_spends_original_plan_and_preserves_evidence(inputs):
    from aware_workspace_sdk.repository_workflow_values import (
        WorkspaceRepositoryWorkflowAttemptObserveRequest,
    )

    _, _, state, _, client, request = inputs
    plan = client.plan_repository_workflow(request)
    observed = client.observe_repository_workflow_plan(plan)
    attempt = client.open_repository_workflow_attempt(plan)
    assert state.exists()
    with pytest.raises(
        WorkspaceRepositoryWorkflowRefusal, match="foreign_or_retired_handle"
    ):
        client.observe_repository_workflow_plan(plan)
    read = WorkspaceRepositoryWorkflowAttemptObserveRequest(
        observed.source_repository_binding_ref,
        observed.target_repository_binding_ref,
        request.attempt_ref,
        observed.binding_ref,
    )
    history = client.observe_repository_workflow_attempt(read)
    assert history.records == () and history.authority_state == "descriptive_only"
    assert client.release_repository_workflow(attempt).state == "completed"
    assert client.observe_repository_workflow_attempt(read).plan == observed
    with pytest.raises(
        WorkspaceRepositoryWorkflowRefusal, match="foreign_or_retired_handle"
    ):
        client.release_repository_workflow(object())


@pytest.mark.parametrize("copier", [copy.copy, copy.deepcopy, pickle.dumps])
def test_opaque_plans_cannot_copy_or_decode(inputs, copier):
    *_, client, request = inputs
    plan = client.plan_repository_workflow(request)
    with pytest.raises(TypeError):
        copier(plan)
    with pytest.raises(TypeError):
        WorkspaceRepositoryWorkflowPlan()


def test_known_restamped_plan_retires_without_affecting_other_family(inputs):
    *_, client, request = inputs
    one, two = (client.plan_repository_workflow(request) for _ in range(2))

    class Restamped:
        __slots__ = ("__weakref__",)

    object.__setattr__(one, "__class__", Restamped)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.observe_repository_workflow_plan(one)
    object.__setattr__(one, "__class__", WorkspaceRepositoryWorkflowPlan)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.observe_repository_workflow_plan(one)
    assert client.observe_repository_workflow_plan(two).binding_ref


def test_unknown_foreign_use_has_no_behavior_or_unrelated_revocation(inputs):
    *_, client, request = inputs
    plan = client.plan_repository_workflow(request)

    class Foreign:
        def __hash__(self):
            raise AssertionError("foreign hash")

        def __eq__(self, other):
            raise AssertionError("foreign equality")

    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.observe_repository_workflow_plan(Foreign())
    assert client.observe_repository_workflow_plan(plan).binding_ref


def test_source_entry_substitution_has_zero_calls(inputs, monkeypatch):
    *_, client, request = inputs
    invoked = []

    def foreign(*args, **kwargs):
        invoked.append(True)
        raise AssertionError("foreign reader")

    monkeypatch.setattr(package_checkout.PackageSourceCheckout, "resolve", foreign)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal, match="source_unavailable"):
        client.plan_repository_workflow(request)
    assert not invoked


def test_execution_change_retires_original_plan(inputs, monkeypatch):
    *_, client, request = inputs
    plan = client.plan_repository_workflow(request)
    monkeypatch.setenv("CODEX_THREAD_ID", "other")
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.observe_repository_workflow_plan(plan)
    monkeypatch.setenv("CODEX_THREAD_ID", "workflow-planning-test")
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.observe_repository_workflow_plan(plan)


def test_fork_rejects_before_io(inputs, monkeypatch):
    *_, client, request = inputs
    plan = client.plan_repository_workflow(request)
    original_pid = os.getpid()
    monkeypatch.setattr(os, "getpid", lambda: original_pid + 1)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.observe_repository_workflow_plan(plan)


def test_known_restamped_client_is_terminal(inputs):
    *_, client, request = inputs
    plan = client.plan_repository_workflow(request)

    class Restamped:
        __slots__ = ("__weakref__",)

    object.__setattr__(client, "__class__", Restamped)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        WorkspaceRepositoryWorkflowClient.observe_repository_workflow_plan(client, plan)
    object.__setattr__(client, "__class__", WorkspaceRepositoryWorkflowClient)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.observe_repository_workflow_plan(plan)


@pytest.mark.parametrize("name", ("check_current", "observe_plan"))
def test_retained_runtime_entry_substitution_has_zero_calls_and_is_terminal(
    inputs, monkeypatch, name
):
    from aware_workspace_runtime.repository_workflow import (
        WorkspaceRepositoryWorkflowRuntime,
    )

    *_, client, request = inputs
    plan = client.plan_repository_workflow(request)
    original = vars(WorkspaceRepositoryWorkflowRuntime)[name]
    calls = []

    def foreign(*args):
        calls.append(True)
        raise AssertionError("foreign runtime")

    monkeypatch.setattr(WorkspaceRepositoryWorkflowRuntime, name, foreign)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.observe_repository_workflow_plan(plan)
    monkeypatch.setattr(WorkspaceRepositoryWorkflowRuntime, name, original)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.observe_repository_workflow_plan(plan)
    assert calls == []


def test_two_clients_do_not_share_original_plan_families(inputs):
    source, target, state, _, one, request = inputs
    two = WorkspaceRepositoryWorkflowClient.filesystem(
        source_repository_root=source,
        target_repository_root=target,
        state_root=state,
        execution_id="codex-workflow-planning-test",
    )
    plan = one.plan_repository_workflow(request)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        two.observe_repository_workflow_plan(plan)
    assert one.observe_repository_workflow_plan(plan).binding_ref


def test_original_profile_includes_declared_dependency_sources(inputs):
    source, _, _, package, client, request = inputs
    module = package.parent
    (module / "aware.module.toml").write_text(
        'aware=1\n[[packages]]\nid="a"\nkind="code"\nmanifest="a/pyproject.toml"\n'
        '[[packages]]\nid="b"\nkind="code"\nmanifest="b/pyproject.toml"\n'
    )
    (package / "pyproject.toml").write_text(
        '[project]\nname="sample-a"\nversion="1.0"\ndependencies=["sample-b>=1,<2"]\n'
    )
    dependency = module / "b"
    dependency.mkdir()
    (dependency / "pyproject.toml").write_text(
        '[project]\nname="sample-b"\nversion="1.0"\ndependencies=[]\n'
    )
    (dependency / "source.py").write_text("original")
    request = replace(request, source_commit=commit(source))
    plan = client.plan_repository_workflow(request)
    assert client.observe_repository_workflow_plan(plan).selection_digest
    (dependency / "source.py").write_text("changed dependency")
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.observe_repository_workflow_plan(plan)


def test_existing_target_baseline_is_exact_and_never_auto_refreshed(inputs):
    _, target, _, _, client, request = inputs
    (target / "first.txt").write_text("first")
    initial = commit(target)
    plan = client.plan_repository_workflow(
        replace(request, expected_target_head=initial)
    )
    assert client.observe_repository_workflow_plan(plan).expected_target_head == initial
    (target / "second.txt").write_text("foreign")
    commit(target)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal, match="stale_target"):
        client.observe_repository_workflow_plan(plan)


def test_ambiguous_harness_and_state_inside_checkout_refuse(inputs, monkeypatch):
    source, target, state, _, _, _ = inputs
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        WorkspaceRepositoryWorkflowClient.filesystem(
            source_repository_root=source,
            target_repository_root=target,
            state_root=source / "state",
            execution_id="codex-workflow-planning-test",
        )
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "another-provider")
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        WorkspaceRepositoryWorkflowClient.filesystem(
            source_repository_root=source,
            target_repository_root=target,
            state_root=state,
            execution_id="codex-workflow-planning-test",
        )


def test_foreign_path_subclass_refuses_without_behavior(inputs):
    source, target, state, _, _, _ = inputs
    calls = []

    class ForeignPath(type(Path())):
        def is_absolute(self):
            calls.append(True)
            raise AssertionError

    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        WorkspaceRepositoryWorkflowClient.filesystem(
            source_repository_root=ForeignPath(source),
            target_repository_root=target,
            state_root=state,
            execution_id="codex-workflow-planning-test",
        )
    assert calls == []


def test_missing_root_is_terminal_after_same_inode_restoration(inputs):
    source, _, _, _, client, request = inputs
    plan = client.plan_repository_workflow(request)
    moved = source.with_name("temporarily_moved")
    source.rename(moved)
    try:
        with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
            client.observe_repository_workflow_plan(plan)
    finally:
        moved.rename(source)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.observe_repository_workflow_plan(plan)


def test_ambiguous_live_harness_is_terminal_after_restoration(inputs, monkeypatch):
    *_, client, request = inputs
    plan = client.plan_repository_workflow(request)
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "another-provider")
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.observe_repository_workflow_plan(plan)
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID")
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.observe_repository_workflow_plan(plan)


@pytest.mark.parametrize("failure", ("timeout", "os_error", "subprocess_error"))
@pytest.mark.parametrize("entrance", ("factory", "plan", "observe"))
def test_git_read_faults_are_typed_with_original_cause_and_no_effects(
    inputs, monkeypatch, failure, entrance
):
    source, target, state, _, client, request = inputs
    plan = client.plan_repository_workflow(request) if entrance == "observe" else None
    other = client.plan_repository_workflow(request)
    original_run = subprocess.run
    errors = {
        "timeout": subprocess.TimeoutExpired("git", 30),
        "os_error": OSError(5, "simulated read unavailable"),
        "subprocess_error": subprocess.CalledProcessError(1, "git"),
    }
    failure_object = errors[failure]
    before = (source / ".git/HEAD").read_bytes(), (target / ".git/HEAD").read_bytes()

    def fail_target(*args, **kwargs):
        if args[0][:3] == ["git", "-C", str(target)]:
            raise failure_object
        return original_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", fail_target)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal) as caught:
        if entrance == "factory":
            client.filesystem(
                source_repository_root=source,
                target_repository_root=target,
                state_root=state,
                execution_id="codex-workflow-planning-test",
            )
        elif entrance == "plan":
            client.plan_repository_workflow(request)
        else:
            client.observe_repository_workflow_plan(plan)
    refusal = caught.value
    assert refusal.code == "source_unavailable"
    assert refusal.__cause__ is failure_object
    assert refusal.evidence.stage == "source_capture"
    assert refusal.evidence.diagnostics == ("git_read_" + failure,)
    assert refusal.evidence.persistence_state == "not_written"
    assert refusal.evidence.cleanup.state == "completed"
    assert before == (
        (source / ".git/HEAD").read_bytes(),
        (target / ".git/HEAD").read_bytes(),
    )
    assert not state.exists()
    monkeypatch.setattr(subprocess, "run", original_run)
    if entrance == "observe":
        with pytest.raises(
            WorkspaceRepositoryWorkflowRefusal, match="foreign_or_retired_handle"
        ):
            client.observe_repository_workflow_plan(plan)
    assert client.observe_repository_workflow_plan(other).binding_ref
    assert client.observe_repository_workflow_plan(
        client.plan_repository_workflow(request)
    ).binding_ref


@pytest.mark.parametrize("failure", ("timeout", "os_error"))
def test_original_capture_read_failure_preserves_cause_and_releases_reader(
    inputs, monkeypatch, failure
):
    source, target, state, _, client, request = inputs
    plan = client.plan_repository_workflow(request)
    original_run = subprocess.run
    error = (
        subprocess.TimeoutExpired("git", 30)
        if failure == "timeout"
        else OSError(5, "simulated source read failure")
    )
    before = (source / ".git/HEAD").read_bytes(), (target / ".git/HEAD").read_bytes()
    descriptors = set(os.listdir("/proc/self/fd"))

    def fail_source(*args, **kwargs):
        if args[0][:3] == ["git", "-C", str(source)] and args[0][3] == "ls-files":
            raise error
        return original_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", fail_source)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal) as caught:
        client.observe_repository_workflow_plan(plan)
    assert caught.value.__cause__ is error
    assert caught.value.evidence.diagnostics == ("source_capture_read_failed",)
    assert caught.value.evidence.cleanup.state == "completed"
    assert set(os.listdir("/proc/self/fd")) == descriptors
    assert before == (
        (source / ".git/HEAD").read_bytes(),
        (target / ".git/HEAD").read_bytes(),
    )
    assert not state.exists()
    monkeypatch.setattr(subprocess, "run", original_run)
    with pytest.raises(
        WorkspaceRepositoryWorkflowRefusal, match="foreign_or_retired_handle"
    ):
        client.observe_repository_workflow_plan(plan)


@pytest.mark.parametrize("interruption", (KeyboardInterrupt, SystemExit))
@pytest.mark.parametrize("entrance", ("factory", "plan", "observe"))
def test_git_interruptions_remain_distinct_and_observation_is_terminal(
    inputs, monkeypatch, interruption, entrance
):
    source, target, state, _, client, request = inputs
    plan = client.plan_repository_workflow(request) if entrance == "observe" else None
    original_run = subprocess.run
    error = interruption("simulated interruption")
    before = (source / ".git/HEAD").read_bytes(), (target / ".git/HEAD").read_bytes()

    def interrupt(*args, **kwargs):
        if args[0][:3] == ["git", "-C", str(target)]:
            raise error
        return original_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", interrupt)
    with pytest.raises(interruption) as caught:
        if entrance == "factory":
            client.filesystem(
                source_repository_root=source,
                target_repository_root=target,
                state_root=state,
                execution_id="codex-workflow-planning-test",
            )
        elif entrance == "plan":
            client.plan_repository_workflow(request)
        else:
            client.observe_repository_workflow_plan(plan)
    assert caught.value is error and error.__cause__ is None
    assert before == (
        (source / ".git/HEAD").read_bytes(),
        (target / ".git/HEAD").read_bytes(),
    )
    assert not state.exists()
    monkeypatch.setattr(subprocess, "run", original_run)
    if entrance == "observe":
        with pytest.raises(
            WorkspaceRepositoryWorkflowRefusal, match="foreign_or_retired_handle"
        ):
            client.observe_repository_workflow_plan(plan)


def test_invalid_git_reference_remains_malformed_request_evidence(inputs):
    _, _, state, _, client, request = inputs
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal) as caught:
        client.plan_repository_workflow(
            replace(request, target_reference="refs/heads/invalid ref")
        )
    assert caught.value.code == "malformed_binding"
    assert caught.value.evidence.persistence_state == "not_written"
    assert not state.exists()


def journal_inputs(client, request):
    from aware_workspace_sdk.repository_workflow_values import (
        WorkspaceRepositoryWorkflowAttemptObserveRequest,
        WorkspaceRepositoryWorkflowEvidenceAppendRequest,
    )

    plan = client.plan_repository_workflow(request)
    observed = client.observe_repository_workflow_plan(plan)
    attempt = client.open_repository_workflow_attempt(plan)
    read = WorkspaceRepositoryWorkflowAttemptObserveRequest(
        observed.source_repository_binding_ref,
        observed.target_repository_binding_ref,
        request.attempt_ref,
        observed.binding_ref,
    )
    snapshot = client.observe_repository_workflow_attempt(read)
    event = WorkspaceRepositoryWorkflowEvidenceAppendRequest(
        observed.binding_ref,
        0,
        snapshot.last_verified_digest,
        "qualification",
        "invocation:1",
        (),
        (),
        (),
        (),
        "caller_reported",
        "not_dispatched",
        "none",
        "not_attempted",
        False,
        (),
    )
    return attempt, read, event


def test_public_journal_append_restart_and_release_are_not_new_authority(inputs):
    source, target, state, _, client, request = inputs
    attempt, read, event = journal_inputs(client, request)
    written = client.append_repository_workflow_evidence(attempt, event)
    assert written.persistence_state == "persisted" and written.observed_cursor == 1
    assert client.append_repository_workflow_evidence(attempt, event) == written
    client.release_repository_workflow(attempt)
    fresh = WorkspaceRepositoryWorkflowClient.filesystem(
        source_repository_root=source,
        target_repository_root=target,
        state_root=state,
        execution_id="codex-workflow-planning-test",
    )
    result = fresh.observe_repository_workflow_attempt(read)
    assert result.records == (event,) and result.authority_state == "descriptive_only"
    with pytest.raises(
        WorkspaceRepositoryWorkflowRefusal, match="foreign_or_retired_handle"
    ):
        fresh.append_repository_workflow_evidence(attempt, event)
    with pytest.raises(
        WorkspaceRepositoryWorkflowRefusal, match="foreign_or_retired_handle"
    ):
        client.append_repository_workflow_evidence(attempt, event)


def test_unknown_append_retains_claimed_effect_and_holds_until_release(
    inputs, monkeypatch
):
    from aware_workspace_fs_adapter import repository_workflow_evidence as physical

    *_, client, request = inputs
    attempt, read, event = journal_inputs(client, request)
    event = replace(event, dispatch_state="returned", effect_state="applied")
    original = physical.os.link

    def fail(*args, **kwargs):
        raise OSError("uncertain link")

    monkeypatch.setattr(physical.os, "link", fail)
    result = client.append_repository_workflow_evidence(attempt, event)
    assert result.persistence_state == "unknown" and result.effect_state == "applied"
    assert result.observed_cursor is None and result.cleanup_state == "incomplete"
    monkeypatch.setattr(physical.os, "link", original)
    with pytest.raises(
        WorkspaceRepositoryWorkflowRefusal, match="foreign_or_retired_handle"
    ):
        client.append_repository_workflow_evidence(attempt, event)
    history = client.observe_repository_workflow_attempt(read)
    assert history.integrity_state == "incomplete" and history.last_verified_cursor == 0
    assert client.release_repository_workflow(attempt).state == "completed"
    assert (
        client.observe_repository_workflow_attempt(read).integrity_state == "incomplete"
    )


def test_durable_journal_effect_survives_failed_alias_cleanup(inputs, monkeypatch):
    from aware_workspace_fs_adapter import repository_workflow_evidence as physical

    *_, client, request = inputs
    attempt, read, event = journal_inputs(client, request)
    original = physical.os.unlink

    def fail(*args, **kwargs):
        if str(args[0]).startswith(".pending-"):
            raise OSError("alias cleanup unavailable")
        return original(*args, **kwargs)

    monkeypatch.setattr(physical.os, "unlink", fail)
    result = client.append_repository_workflow_evidence(
        attempt, replace(event, dispatch_state="returned", effect_state="applied")
    )
    assert result.persistence_state == "persisted" and result.observed_cursor == 1
    assert result.effect_state == "applied" and result.cleanup_state == "incomplete"
    history = client.observe_repository_workflow_attempt(read)
    assert (
        history.last_verified_cursor == 1
        and history.records[0].effect_state == "applied"
    )
    client.release_repository_workflow(attempt)


@pytest.mark.parametrize("failure", ("grade", "binding", "class"))
def test_invalid_registered_attempt_is_terminal_but_preserves_unrelated_attempt(
    inputs, failure
):
    from aware_workspace_sdk.repository_workflow import (
        WorkspaceRepositoryWorkflowAttempt,
    )

    *_, client, request = inputs
    one, _, event = journal_inputs(client, request)
    two, _, two_event = journal_inputs(
        client, replace(request, attempt_ref="attempt:other")
    )
    if failure == "grade":
        event = replace(event, evidence_grade="owner_observed")
    elif failure == "binding":
        event = replace(event, attempt_binding_ref="substituted")
    else:

        class Restamped:
            __slots__ = ("__weakref__",)

        object.__setattr__(one, "__class__", Restamped)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.append_repository_workflow_evidence(one, event)
    if failure == "class":
        object.__setattr__(one, "__class__", WorkspaceRepositoryWorkflowAttempt)
    with pytest.raises(
        WorkspaceRepositoryWorkflowRefusal, match="foreign_or_retired_handle"
    ):
        client.append_repository_workflow_evidence(one, event)
    assert (
        client.append_repository_workflow_evidence(two, two_event).persistence_state
        == "persisted"
    )


def test_interrupted_append_holds_and_cannot_reuse_attempt_after_restoration(
    inputs, monkeypatch
):
    from aware_workspace_fs_adapter import repository_workflow_evidence as physical

    *_, client, request = inputs
    attempt, read, event = journal_inputs(client, request)
    original = physical.os.link

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt("interrupted metadata publication")

    monkeypatch.setattr(physical.os, "link", interrupt)
    with pytest.raises(KeyboardInterrupt):
        client.append_repository_workflow_evidence(attempt, event)
    monkeypatch.setattr(physical.os, "link", original)
    with pytest.raises(
        WorkspaceRepositoryWorkflowRefusal, match="foreign_or_retired_handle"
    ):
        client.append_repository_workflow_evidence(attempt, event)
    assert (
        client.observe_repository_workflow_attempt(read).integrity_state == "incomplete"
    )
    client.release_repository_workflow(attempt)


def test_postwrite_command_retirement_preserves_durable_journal_outcome(
    inputs, monkeypatch
):
    from aware_workspace_fs_adapter import repository_workflow_evidence as physical

    *_, client, request = inputs
    attempt, _, event = journal_inputs(client, request)
    original = physical.os.link

    def revoke_after_link(*args, **kwargs):
        result = original(*args, **kwargs)
        monkeypatch.setenv("CODEX_THREAD_ID", "retired-during-journal-write")
        return result

    monkeypatch.setattr(physical.os, "link", revoke_after_link)
    result = client.append_repository_workflow_evidence(attempt, event)
    assert result.persistence_state == "persisted" and result.observed_cursor == 1
    assert "journal_written_command_retired" in result.diagnostics
    monkeypatch.setenv("CODEX_THREAD_ID", "workflow-planning-test")
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.append_repository_workflow_evidence(attempt, event)


@pytest.mark.parametrize("phase", ("refusal", "interrupt"))
def test_durable_opening_survives_late_failure_without_active_attempt(
    inputs, monkeypatch, phase
):
    from aware_workspace_fs_adapter import repository_workflow_evidence as physical
    from aware_workspace_runtime.repository_workflow import (
        WorkspaceRepositoryWorkflowRuntime,
    )
    from aware_workspace_sdk.repository_workflow_values import (
        WorkspaceRepositoryWorkflowAttemptObserveRequest,
    )

    source, target, state, _, client, request = inputs
    plan = client.plan_repository_workflow(request)
    observed = client.observe_repository_workflow_plan(plan)
    original = physical._write
    check = WorkspaceRepositoryWorkflowRuntime.check_current
    writes = []
    interrupt = KeyboardInterrupt("late opening interruption")

    def fail_current(self):
        raise interrupt

    def fail_after_header(directory, name, body):
        result = original(directory, name, body)
        if name == "header.json":
            writes.append(body)
            if phase == "refusal":
                monkeypatch.setenv("CODEX_THREAD_ID", "retired-after-header")
            else:
                monkeypatch.setattr(
                    WorkspaceRepositoryWorkflowRuntime, "check_current", fail_current
                )
        return result

    monkeypatch.setattr(physical, "_write", fail_after_header)
    error_type = (
        WorkspaceRepositoryWorkflowRefusal if phase == "refusal" else KeyboardInterrupt
    )
    with pytest.raises(error_type) as caught:
        client.open_repository_workflow_attempt(plan)
    evidence = (
        caught.value.evidence if phase == "refusal" else caught.value.workflow_evidence
    )
    assert evidence.persistence_state == "persisted"
    assert evidence.stage == "evidence_closeout"
    assert evidence.cleanup.state == "completed"
    assert evidence.cleanup.attempt_binding_ref == observed.binding_ref
    (reference,) = evidence.original_evidence_refs
    (header,) = state.rglob("header.json")
    assert (
        reference.sha256 == "sha256:" + hashlib.sha256(header.read_bytes()).hexdigest()
    )
    assert reference.size_bytes == len(header.read_bytes())
    assert reference.coordinate.endswith("/header.json")
    if phase == "refusal":
        assert isinstance(caught.value.__cause__, WorkspaceRepositoryWorkflowRefusal)
    else:
        assert caught.value is interrupt
    monkeypatch.setenv("CODEX_THREAD_ID", "workflow-planning-test")
    monkeypatch.setattr(WorkspaceRepositoryWorkflowRuntime, "check_current", check)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.open_repository_workflow_attempt(plan)
    assert len(writes) == 1
    fresh = WorkspaceRepositoryWorkflowClient.filesystem(
        source_repository_root=source,
        target_repository_root=target,
        state_root=state,
        execution_id="codex-workflow-planning-test",
    )
    history = fresh.observe_repository_workflow_attempt(
        WorkspaceRepositoryWorkflowAttemptObserveRequest(
            observed.source_repository_binding_ref,
            observed.target_repository_binding_ref,
            request.attempt_ref,
            observed.binding_ref,
        )
    )
    assert history.persistence_state == "persisted"
    assert history.authority_state == "descriptive_only"


def test_durable_append_cleanup_refusal_preserves_binding_and_holds_family(
    inputs, monkeypatch
):
    from aware_workspace_fs_adapter import repository_workflow_evidence as physical

    *_, client, request = inputs
    attempt, read, event = journal_inputs(client, request)
    original = physical.os.close
    cause = OSError("lock close failed after release")
    armed = True

    def fail_lock(descriptor):
        nonlocal armed
        target = os.readlink(f"/proc/self/fd/{descriptor}")
        original(descriptor)
        if armed and target.endswith("/lock"):
            armed = False
            raise cause

    monkeypatch.setattr(physical.os, "close", fail_lock)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal) as caught:
        client.append_repository_workflow_evidence(attempt, event)
    assert caught.value.evidence.persistence_state == "persisted"
    assert caught.value.evidence.cleanup.state == "unknown"
    assert (
        caught.value.evidence.cleanup.attempt_binding_ref == event.attempt_binding_ref
    )
    assert caught.value.evidence.original_evidence_refs[0].coordinate.endswith(
        "/000001.json"
    )
    assert caught.value.__cause__.__cause__ is cause
    monkeypatch.setattr(physical.os, "close", original)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.append_repository_workflow_evidence(attempt, event)
    history = client.observe_repository_workflow_attempt(read)
    assert history.last_verified_cursor == 1
    assert history.persistence_state == "persisted"
    client.release_repository_workflow(attempt)


@pytest.mark.parametrize("phase", ("snapshot", "cleanup"))
def test_interrupted_open_after_durability_preserves_original_opening_evidence(
    inputs, monkeypatch, phase
):
    from aware_workspace_fs_adapter import repository_workflow_evidence as physical

    *_, client, request = inputs
    plan = client.plan_repository_workflow(request)
    observed = client.observe_repository_workflow_plan(plan)
    original_close = physical.os.close
    original_snapshot = physical.FilesystemWorkflowEvidence._snapshot
    interrupt = KeyboardInterrupt("interrupted after durable header")
    releases = []

    def fail_snapshot(*args, **kwargs):
        raise interrupt

    def fail_close(descriptor):
        path = os.readlink(f"/proc/self/fd/{descriptor}")
        original_close(descriptor)
        if path.endswith(("/lock", "/state")) or len(path.rsplit("/", 1)[-1]) == 64:
            releases.append(path)
        if phase == "cleanup" and path.endswith("/lock"):
            raise interrupt

    if phase == "snapshot":
        monkeypatch.setattr(
            physical.FilesystemWorkflowEvidence, "_snapshot", fail_snapshot
        )
    monkeypatch.setattr(physical.os, "close", fail_close)
    with pytest.raises(KeyboardInterrupt) as caught:
        client.open_repository_workflow_attempt(plan)
    assert caught.value is interrupt
    evidence = vars(interrupt)["workflow_evidence"]
    assert evidence.persistence_state == "persisted"
    assert evidence.cleanup.attempt_binding_ref == observed.binding_ref
    assert evidence.cleanup.state == ("unknown" if phase == "cleanup" else "completed")
    assert evidence.original_evidence_refs[0].coordinate.endswith("/header.json")
    assert len(releases) == 3
    monkeypatch.setattr(physical.os, "close", original_close)
    monkeypatch.setattr(
        physical.FilesystemWorkflowEvidence, "_snapshot", original_snapshot
    )
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.open_repository_workflow_attempt(plan)
