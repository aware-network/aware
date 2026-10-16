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


def workflow_source(inputs):
    from aware_workspace_sdk.repository_workflow import (
        observe_original_repository_workflow_source,
    )

    client, request = inputs[-2:]
    attempt = client.open_repository_workflow_attempt(
        client.plan_repository_workflow(request)
    )
    source = client.retain_repository_workflow_source(attempt)
    return attempt, source, observe_original_repository_workflow_source(source)


def test_original_source_path_verification_is_nonallocating_and_bodyless_safe(inputs):
    from aware_workspace_sdk.repository_workflow import (
        verify_original_repository_workflow_source,
        verify_original_repository_workflow_source_paths,
    )

    attempt, source, observed = workflow_source(inputs)
    for paths in ((), (observed.files[0].output_path,)):
        assert (
            verify_original_repository_workflow_source_paths(
                source, expected_binding=observed.binding, output_paths=paths
            )
            is None
        )
    verify_original_repository_workflow_source(
        source, expected_binding=observed.binding
    )
    assert inputs[-2].release_repository_workflow(attempt).state == "completed"
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        verify_original_repository_workflow_source_paths(
            source, expected_binding=observed.binding, output_paths=()
        )


@pytest.mark.parametrize("paths", [None, [], (True,), ("unknown",), ("../outside",)])
def test_original_source_path_bad_selection_is_terminal(inputs, paths):
    from aware_workspace_sdk.repository_workflow import (
        verify_original_repository_workflow_source_paths,
    )

    _parent, source, observed = workflow_source(inputs)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        verify_original_repository_workflow_source_paths(
            source, expected_binding=observed.binding, output_paths=paths
        )
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        verify_original_repository_workflow_source_paths(
            source,
            expected_binding=observed.binding,
            output_paths=(observed.files[0].output_path,),
        )


@pytest.mark.parametrize("change", ["body", "mode"])
def test_original_source_path_drift_cannot_resume_after_restoration(inputs, change):
    from aware_workspace_sdk.repository_workflow import (
        verify_original_repository_workflow_source_paths,
    )

    _parent, source, observed = workflow_source(inputs)
    selected = next(
        row for row in observed.files if row.source_path.endswith("source.py")
    )
    path = inputs[0] / selected.source_path
    original, mode = path.read_bytes(), path.stat().st_mode & 0o777
    if change == "body":
        path.write_bytes(b"drift")
    else:
        path.chmod(0o755)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        verify_original_repository_workflow_source_paths(
            source,
            expected_binding=observed.binding,
            output_paths=(selected.output_path,),
        )
    path.write_bytes(original)
    path.chmod(mode)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        verify_original_repository_workflow_source_paths(
            source,
            expected_binding=observed.binding,
            output_paths=(selected.output_path,),
        )


@pytest.mark.parametrize("replacement", ["foreign", "code", "instance"])
def test_original_source_path_reader_substitution_has_zero_dispatch(
    inputs, monkeypatch, replacement
):
    from aware_workspace_sdk.repository_workflow import (
        verify_original_repository_workflow_source_paths,
    )

    _parent, source, observed = workflow_source(inputs)
    original = package_checkout.PackageSourceCheckout.revalidate_paths
    calls = []

    def foreign(_reader, _paths):
        calls.append(True)

    def foreign_code(_reader, _paths):
        raise AssertionError("foreign reader code executed")

    with monkeypatch.context() as patch:
        if replacement == "foreign":
            patch.setattr(
                package_checkout.PackageSourceCheckout, "revalidate_paths", foreign
            )
        elif replacement == "code":
            patch.setattr(original, "__code__", foreign_code.__code__)
        else:
            from aware_workspace_sdk import repository_workflow as sdk

            runtime = next(
                record[0] for handle, record in sdk._SOURCES.items() if handle is source
            )
            patch.setattr(runtime._sources[-1][1].reader, "revalidate_paths", foreign)
        with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
            verify_original_repository_workflow_source_paths(
                source, expected_binding=observed.binding, output_paths=()
            )
    assert calls == []
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        verify_original_repository_workflow_source_paths(
            source, expected_binding=observed.binding, output_paths=()
        )


@pytest.mark.parametrize("entry", ["membership", "capture", "read"])
@pytest.mark.parametrize("behavior", ["return", "raise", "restore"])
def test_original_source_path_nested_io_substitution_is_terminal(
    inputs, monkeypatch, entry, behavior
):
    import sys

    from aware_workspace_sdk.repository_workflow import (
        verify_original_repository_workflow_source_paths,
    )

    _parent, source, observed = workflow_source(inputs)
    selected = next(
        row for row in observed.files if row.source_path.endswith("source.py")
    )
    if entry == "membership":
        owner, name = package_checkout.PackageSourceCheckout, "_tracked_exact_sources"
    elif entry == "capture":
        owner, name = package_checkout, "capture_exact_paths"
    else:
        owner, name = package_checkout.os, "read"
    original = getattr(owner, name)
    changed, calls = [], []
    previous = sys.getprofile()

    def foreign(*args, **kwargs):
        calls.append(True)
        if behavior == "restore":
            setattr(owner, name, original)
        if behavior == "raise":
            raise AssertionError("foreign reader invoked")

    with monkeypatch.context() as patch:

        def profile(frame, event, _arg):
            if (
                event == "return"
                and frame.f_code is package_checkout._git.__code__
                and not changed
            ):
                # The first real HEAD read completed; poison the next nested entrance.
                patch.setattr(owner, name, foreign)
                changed.append(True)

        try:
            sys.setprofile(profile)
            with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
                verify_original_repository_workflow_source_paths(
                    source,
                    expected_binding=observed.binding,
                    output_paths=(selected.output_path,),
                )
        finally:
            sys.setprofile(previous)
    assert changed == [True] and calls == []
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        verify_original_repository_workflow_source_paths(
            source,
            expected_binding=observed.binding,
            output_paths=(selected.output_path,),
        )


@pytest.mark.parametrize(
    "entry,in_place",
    [
        (entry, in_place)
        for entry in ("selected", "check", "membership", "git", "capture", "close")
        for in_place in (False, True)
    ]
    + [("registry", False)],
)
@pytest.mark.parametrize("behavior", ["return", "raise", "restore"])
@pytest.mark.parametrize("after_io", [False, True])
def test_original_source_path_default_substitution_is_terminal(
    inputs, monkeypatch, entry, in_place, behavior, after_io
):
    import sys

    from aware_workspace_sdk import repository_workflow as sdk
    from aware_workspace_sdk.repository_workflow import (
        verify_original_repository_workflow_source_paths,
    )

    _parent, source, observed = workflow_source(inputs)
    selected = next(
        row for row in observed.files if row.source_path.endswith("source.py")
    )
    method, key = {
        "selected": (package_checkout.PackageSourceCheckout.revalidate_paths, "_guard"),
        "check": (package_checkout.PackageSourceCheckout._check, "_guard"),
        "membership": (
            package_checkout.PackageSourceCheckout._tracked_exact_sources,
            "_guard",
        ),
        "git": (package_checkout._read_git, "_guard"),
        "capture": (package_checkout.capture_exact_paths, "_verify"),
        "close": (package_checkout.PackageSourceCheckout.close, "_close"),
        "registry": (package_checkout._check_retained_reader, "_registry"),
    }[entry]
    attribute = "__defaults__" if entry == "registry" else "__kwdefaults__"
    original = getattr(method, attribute)
    record = next(
        registered[0]._sources[-1][1]
        for handle, registered in sdk._SOURCES.items()
        if handle is source
    )
    calls, changed = [], []
    previous = sys.getprofile()

    def foreign(*args, **kwargs):
        calls.append(True)
        if behavior == "restore":
            setattr(method, attribute, original)
            if in_place:
                original[key] = original_value
        if behavior == "raise":
            raise AssertionError("foreign default dispatched")
        if entry == "registry":
            return original[0].items()

    # A foreign registry can dispatch behavior through .items(), even though
    # its default is positional rather than a guard keyword.
    foreign.items = foreign
    original_value = original[key] if entry != "registry" else None

    with monkeypatch.context() as patch:

        def poison():
            if in_place:
                patch.setitem(original, key, foreign)
            else:
                replacement = (
                    (foreign,) if entry == "registry" else {**original, key: foreign}
                )
                patch.setattr(method, attribute, replacement)
            changed.append(True)

        def profile(frame, event, _arg):
            if (
                event == "return"
                and frame.f_code is package_checkout._git.__code__
                and not changed
            ):
                poison()

        try:
            if after_io:
                sys.setprofile(profile)
            else:
                poison()
            with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
                verify_original_repository_workflow_source_paths(
                    source,
                    expected_binding=observed.binding,
                    output_paths=(selected.output_path,),
                )
        finally:
            sys.setprofile(previous)

    assert changed == [True] and calls == []
    assert record.status == "terminal" and record.parent.status == "held"
    assert record.reader is None and record.descriptor == -1
    assert record.state == () and record.reader_data == {}
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        verify_original_repository_workflow_source_paths(
            source,
            expected_binding=observed.binding,
            output_paths=(selected.output_path,),
        )


def test_original_source_path_default_refusal_preserves_unrelated_family(
    inputs, monkeypatch
):
    from aware_workspace_sdk.repository_workflow import (
        observe_original_repository_workflow_source,
        verify_original_repository_workflow_source_paths,
    )

    _parent, source, observed = workflow_source(inputs)
    client, request = inputs[-2:]
    other_parent = client.open_repository_workflow_attempt(
        client.plan_repository_workflow(replace(request, attempt_ref="attempt:other"))
    )
    other = client.retain_repository_workflow_source(other_parent)
    before = observe_original_repository_workflow_source(other)
    original = package_checkout.PackageSourceCheckout.revalidate_paths.__kwdefaults__
    calls = []

    def foreign(*args, **kwargs):
        calls.append(True)

    with monkeypatch.context() as patch:
        patch.setitem(original, "_guard", foreign)
        with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
            verify_original_repository_workflow_source_paths(
                source, expected_binding=observed.binding, output_paths=()
            )
    assert calls == []
    assert observe_original_repository_workflow_source(other).binding == before.binding
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        verify_original_repository_workflow_source_paths(
            source, expected_binding=observed.binding, output_paths=()
        )
    assert client.release_repository_workflow(other_parent).state == "completed"


@pytest.mark.parametrize("replacement", ["module", "default", "both"])
@pytest.mark.parametrize("behavior", ["return", "raise", "restore"])
@pytest.mark.parametrize("after_io", [False, True])
def test_original_source_path_registry_origin_substitution_is_terminal(
    inputs, monkeypatch, replacement, behavior, after_io
):
    import sys

    from aware_workspace_sdk import repository_workflow as sdk
    from aware_workspace_sdk.repository_workflow import (
        verify_original_repository_workflow_source_paths,
    )

    _parent, source, observed = workflow_source(inputs)
    method = package_checkout._check_retained_reader
    original = package_checkout._RETAINED_READER_GUARDS
    defaults = method.__defaults__
    record = next(
        registered[0]._sources[-1][1]
        for handle, registered in sdk._SOURCES.items()
        if handle is source
    )
    descriptor = record.descriptor
    calls, changed = [], []
    previous = sys.getprofile()

    class ForeignRegistry:
        def items(self):
            calls.append(True)
            if behavior == "restore":
                package_checkout._RETAINED_READER_GUARDS = original
                method.__defaults__ = defaults
            if behavior == "raise":
                raise AssertionError("foreign registry dispatched")
            return original.items()

    with monkeypatch.context() as patch:

        def poison():
            foreign = ForeignRegistry()
            if replacement in ("module", "both"):
                patch.setattr(package_checkout, "_RETAINED_READER_GUARDS", foreign)
            if replacement in ("default", "both"):
                patch.setattr(method, "__defaults__", (foreign,))
            changed.append(True)

        def profile(frame, event, _arg):
            if (
                event == "return"
                and frame.f_code is package_checkout._git.__code__
                and not changed
            ):
                poison()

        try:
            if after_io:
                sys.setprofile(profile)
            else:
                poison()
            with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
                verify_original_repository_workflow_source_paths(
                    source,
                    expected_binding=observed.binding,
                    output_paths=(observed.files[0].output_path,),
                )
        finally:
            sys.setprofile(previous)
    assert changed == [True] and calls == []
    assert record.status == "terminal" and record.parent.status == "held"
    assert record.reader is None and record.descriptor == -1
    assert record.state == () and record.reader_data == {}
    assert record.cleanup == "completed"
    with pytest.raises(OSError):
        os.fstat(descriptor)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        verify_original_repository_workflow_source_paths(
            source, expected_binding=observed.binding, output_paths=()
        )


def test_original_source_path_registry_origin_refusal_preserves_other_family(
    inputs, monkeypatch
):
    import sys

    from aware_workspace_sdk.repository_workflow import (
        observe_original_repository_workflow_source,
        verify_original_repository_workflow_source_paths,
    )

    _parent, source, observed = workflow_source(inputs)
    client, request = inputs[-2:]
    other_parent = client.open_repository_workflow_attempt(
        client.plan_repository_workflow(replace(request, attempt_ref="attempt:other"))
    )
    other = client.retain_repository_workflow_source(other_parent)
    before = observe_original_repository_workflow_source(other)
    calls, changed = [], []
    previous = sys.getprofile()

    class ForeignRegistry:
        def items(self):
            calls.append(True)
            raise AssertionError("foreign registry dispatched")

    with monkeypatch.context() as patch:

        def profile(frame, event, _arg):
            if (
                event == "return"
                and frame.f_code is package_checkout._git.__code__
                and not changed
            ):
                foreign = ForeignRegistry()
                patch.setattr(package_checkout, "_RETAINED_READER_GUARDS", foreign)
                patch.setattr(
                    package_checkout._check_retained_reader, "__defaults__", (foreign,)
                )
                changed.append(True)

        try:
            sys.setprofile(profile)
            with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
                verify_original_repository_workflow_source_paths(
                    source, expected_binding=observed.binding, output_paths=()
                )
        finally:
            sys.setprofile(previous)
    assert changed == [True] and calls == []
    assert observe_original_repository_workflow_source(other).binding == before.binding
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        verify_original_repository_workflow_source_paths(
            source, expected_binding=observed.binding, output_paths=()
        )
    assert client.release_repository_workflow(other_parent).state == "completed"


@pytest.mark.parametrize("entry", ["selected", "registry"])
def test_original_source_path_default_refusal_does_not_retain_foreign_callback(
    inputs, monkeypatch, entry
):
    import gc
    import sys
    import weakref

    from aware_workspace_sdk.repository_workflow import (
        verify_original_repository_workflow_source_paths,
    )

    class Payload:
        pass

    _parent, source, observed = workflow_source(inputs)
    method = (
        package_checkout.PackageSourceCheckout.revalidate_paths
        if entry == "selected"
        else package_checkout._check_retained_reader
    )
    payload = Payload()
    reference = weakref.ref(payload)
    calls = []

    def foreign(*args, _payload=payload, **kwargs):
        calls.append(_payload)

    foreign.items = foreign
    changed = []
    previous = sys.getprofile()
    with monkeypatch.context() as patch:

        def profile(frame, event, _arg, _target=foreign):
            if (
                event == "return"
                and frame.f_code is package_checkout._git.__code__
                and not changed
            ):
                patch.setattr(method, "__defaults__", (_target,))
                changed.append(True)

        try:
            if entry == "selected":
                patch.setattr(method, "__kwdefaults__", {"_guard": foreign})
            else:
                sys.setprofile(profile)
            with pytest.raises(WorkspaceRepositoryWorkflowRefusal) as caught:
                verify_original_repository_workflow_source_paths(
                    source,
                    expected_binding=observed.binding,
                    output_paths=(observed.files[0].output_path,),
                )
        finally:
            sys.setprofile(previous)
    if entry == "registry":
        assert changed == [True]
    # Discard the profile closure as well; it legitimately borrowed the callback
    # while injecting the fault. Keep the original refusal traceback alive.
    del profile
    del foreign, payload
    gc.collect()
    assert caught.value.__traceback__ is not None
    assert calls == [] and reference() is None


def test_workflow_source_original_bytes_and_complete_request(inputs):
    from aware_workspace_sdk.repository_workflow import (
        read_original_repository_workflow_source,
        release_original_repository_workflow_source,
        verify_original_repository_workflow_source,
    )

    attempt, source, observation = workflow_source(inputs)
    request = inputs[-1]
    assert observation.binding.marker_environment == request.marker_environment
    assert observation.binding.source_commit == request.source_commit
    paths = tuple(row.output_path for row in observation.files)
    result = read_original_repository_workflow_source(
        source, expected_binding=observation.binding, output_paths=paths
    )
    assert len(result.bodies) == len(paths)
    for item in result.bodies:
        assert item.body == (inputs[0] / item.file.source_path).read_bytes()
        assert (
            item.file.content_digest
            == "sha256:" + hashlib.sha256(item.body).hexdigest()
        )
    verify_original_repository_workflow_source(
        source, expected_binding=observation.binding
    )
    assert release_original_repository_workflow_source(source).state == "completed"
    assert inputs[-2].release_repository_workflow(attempt).state == "completed"
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        verify_original_repository_workflow_source(
            source, expected_binding=observation.binding
        )


@pytest.mark.parametrize("drift", ("body", "mode", "membership", "commit"))
def test_workflow_source_drift_terminal_and_restoration(inputs, drift):
    from aware_workspace_sdk.repository_workflow import (
        verify_original_repository_workflow_source,
    )

    attempt, source, observation = workflow_source(inputs)
    path = inputs[3] / "source.py"
    before = path.read_bytes()
    if drift == "body":
        path.write_bytes(b"changed")
    elif drift == "mode":
        path.chmod(0o755)
    elif drift == "membership":
        (inputs[3] / "new.py").write_bytes(b"new")
    else:
        (inputs[3] / "new.py").write_bytes(b"new")
        commit(inputs[0])
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        verify_original_repository_workflow_source(
            source, expected_binding=observation.binding
        )
    path.write_bytes(before)
    path.chmod(0o644)
    with pytest.raises(
        WorkspaceRepositoryWorkflowRefusal, match="foreign_or_retired_handle"
    ):
        verify_original_repository_workflow_source(
            source, expected_binding=observation.binding
        )
    assert attempt is not None


@pytest.mark.parametrize(
    "field",
    (
        "source_commit",
        "profile_key",
        "selection_digest",
        "output_layout_digest",
        "marker_environment",
    ),
)
def test_workflow_source_binding_substitution_is_terminal(inputs, field):
    from aware_workspace_sdk.repository_workflow import (
        verify_original_repository_workflow_source,
    )

    attempt, source, observation = workflow_source(inputs)
    value = observation.binding
    changes = {
        "source_commit": "0" * 40,
        "profile_key": "other",
        "selection_digest": "sha256:" + "0" * 64,
        "output_layout_digest": "sha256:" + "0" * 64,
        "marker_environment": value.marker_environment[:-1],
    }
    wrong = replace(value, **{field: changes[field]})
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        verify_original_repository_workflow_source(source, expected_binding=wrong)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        verify_original_repository_workflow_source(source, expected_binding=value)
    assert attempt is not None


@pytest.mark.parametrize("kind", ("return", "raise", "restore"))
@pytest.mark.parametrize(
    "entry",
    (
        "_check",
        "_tracked_sources",
        "_tracked_exact_sources",
        "revalidate",
        "capture_exact_paths",
        "read",
        "run",
    ),
)
@pytest.mark.parametrize("phase", ("retain", "reread"))
def test_workflow_source_reader_substitution_zero_calls(
    inputs, monkeypatch, kind, entry, phase
):
    from aware_workspace_sdk.repository_workflow import (
        verify_original_repository_workflow_source,
    )

    client, request = inputs[-2:]
    attempt = client.open_repository_workflow_attempt(
        client.plan_repository_workflow(request)
    )
    source = observation = None
    if phase == "reread":
        from aware_workspace_sdk.repository_workflow import (
            observe_original_repository_workflow_source,
        )

        source = client.retain_repository_workflow_source(attempt)
        observation = observe_original_repository_workflow_source(source)
    owner = (
        package_checkout.PackageSourceCheckout
        if entry.startswith("_") or entry == "revalidate"
        else package_checkout
        if entry == "capture_exact_paths"
        else os
        if entry == "read"
        else subprocess
    )
    original = getattr(owner, entry)
    calls = []

    def hostile(*args, **kwargs):
        calls.append(entry)
        if kind == "restore":
            monkeypatch.setattr(owner, entry, original)
        if kind == "raise":
            raise AssertionError("foreign reader must never run")

    monkeypatch.setattr(owner, entry, hostile)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        if phase == "retain":
            client.retain_repository_workflow_source(attempt)
        else:
            verify_original_repository_workflow_source(
                source, expected_binding=observation.binding
            )
    assert calls == []
    monkeypatch.setattr(owner, entry, original)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        if phase == "retain":
            client.retain_repository_workflow_source(attempt)
        else:
            verify_original_repository_workflow_source(
                source, expected_binding=observation.binding
            )


def test_workflow_source_mapping_aliases_identical_origins_and_executable(inputs):
    from aware_workspace_sdk.repository_workflow import (
        read_original_repository_workflow_source,
    )

    root, _, _, package, _, request = inputs
    (package / "same.py").write_bytes((package / "source.py").read_bytes())
    (package / "run.sh").write_bytes(b"#!/bin/sh\n")
    (package / "run.sh").chmod(0o755)
    # Profile-declared repository file mapping comes from the same canonical selector.
    (root / "readme.md").write_bytes(b"original mapped document")
    manifest = root / "aware.repo.toml"
    text = (
        manifest.read_text()
        + '\n[[repository_files]]\nrole="documentation"\nsource_path="readme.md"\ntarget_path="README.md"\n'
    )
    manifest.write_text(text)
    request = replace(
        request,
        source_commit=commit(root),
        profile_digest="sha256:" + hashlib.sha256(manifest.read_bytes()).hexdigest(),
    )
    updated = (*inputs[:-1], request)
    attempt, source, observation = workflow_source(updated)
    by_output = {row.output_path: row for row in observation.files}
    mapped = by_output["README.md"]
    assert mapped.source_path == "readme.md"
    same = [
        row
        for row in observation.files
        if row.output_path.endswith(("source.py", "same.py"))
    ]
    assert len(same) == 2 and same[0].content_digest == same[1].content_digest
    assert same[0].source_path != same[1].source_path
    executable = next(
        row for row in observation.files if row.output_path.endswith("run.sh")
    )
    assert executable.git_mode == "100755" and executable.projected_mode == 0o755
    result = read_original_repository_workflow_source(
        source, expected_binding=observation.binding, output_paths=("README.md",)
    )
    assert result.bodies[0].body == b"original mapped document"
    assert attempt is not None


def test_workflow_source_unknown_held_error_does_not_pin_known_family(inputs):
    import gc
    import weakref

    from aware_workspace_sdk.repository_workflow import (
        observe_original_repository_workflow_source,
    )

    attempt, source, _ = workflow_source(inputs)
    reference = weakref.ref(source)
    try:
        observe_original_repository_workflow_source(object())
    except WorkspaceRepositoryWorkflowRefusal as error:
        held = error
    del source
    gc.collect()
    assert reference() is None
    assert held is not None and attempt is not None


def test_workflow_source_restamp_releases_and_cannot_resume(inputs):
    from aware_workspace_sdk.repository_workflow import (
        WorkspaceRepositoryWorkflowSource,
        observe_original_repository_workflow_source,
    )

    class Restamped(WorkspaceRepositoryWorkflowSource):
        __slots__ = ()

    attempt, source, _ = workflow_source(inputs)
    source.__class__ = Restamped
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        observe_original_repository_workflow_source(source)
    source.__class__ = WorkspaceRepositoryWorkflowSource
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        observe_original_repository_workflow_source(source)
    assert attempt is not None


def test_workflow_source_parent_release_retires_borrowed_source(inputs):
    from aware_workspace_sdk.repository_workflow import (
        observe_original_repository_workflow_source,
    )

    attempt, source, _ = workflow_source(inputs)
    inputs[-2].release_repository_workflow(attempt)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        observe_original_repository_workflow_source(source)


@pytest.mark.parametrize("phase", ("retain", "reread"))
@pytest.mark.parametrize("kind", ("return", "raise", "restore"))
@pytest.mark.parametrize("entry", ("_tracked_sources", "capture_exact_paths", "read"))
def test_workflow_source_substitution_after_real_io(
    inputs, monkeypatch, phase, kind, entry
):
    import sys

    from aware_workspace_runtime import source_observation_io
    from aware_workspace_sdk.repository_workflow import (
        observe_original_repository_workflow_source,
        verify_original_repository_workflow_source,
    )

    client, request = inputs[-2:]
    attempt = client.open_repository_workflow_attempt(
        client.plan_repository_workflow(request)
    )
    source = observation = None
    if phase == "reread":
        source = client.retain_repository_workflow_source(attempt)
        observation = observe_original_repository_workflow_source(source)
    owner = (
        package_checkout.PackageSourceCheckout
        if entry.startswith("_")
        else package_checkout
        if entry == "capture_exact_paths"
        else os
    )
    original = getattr(owner, entry)
    calls, injected = [], []

    def hostile(*args, **kwargs):
        calls.append(entry)
        if kind == "restore":
            monkeypatch.setattr(owner, entry, original)
        if kind == "raise":
            raise AssertionError("nested foreign entrance ran")

    # Fault injection happens after genuine captured IO, without making an
    # untrusted replacement into an authenticated original primitive.
    code = source_observation_io.capture_exact_paths.__code__
    anchor = next(
        i
        for i, line in enumerate(
            Path(source_observation_io.__file__).read_text().splitlines(), 1
        )
        if line.strip() == 'body = b"".join(chunks)' and i >= code.co_firstlineno
    )

    def trace(frame, event, arg):
        if (
            event == "line"
            and frame.f_code is code
            and frame.f_lineno == anchor
            and not injected
        ):
            injected.append(True)
            monkeypatch.setattr(owner, entry, hostile)
        return trace

    previous = sys.gettrace()
    try:
        sys.settrace(trace)
        with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
            if phase == "retain":
                client.retain_repository_workflow_source(attempt)
            else:
                verify_original_repository_workflow_source(
                    source, expected_binding=observation.binding
                )
    finally:
        sys.settrace(previous)
        monkeypatch.setattr(owner, entry, original)
    assert injected and calls == []
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        if phase == "retain":
            client.retain_repository_workflow_source(attempt)
        else:
            verify_original_repository_workflow_source(
                source, expected_binding=observation.binding
            )


def test_workflow_source_known_failure_does_not_keep_source_in_held_exception(inputs):
    import gc
    import weakref

    from aware_workspace_sdk.repository_workflow import (
        verify_original_repository_workflow_source,
    )

    attempt, source, observation = workflow_source(inputs)
    reference = weakref.ref(source)
    (inputs[3] / "source.py").write_bytes(b"drifted")
    try:
        verify_original_repository_workflow_source(
            source, expected_binding=observation.binding
        )
    except WorkspaceRepositoryWorkflowRefusal as error:
        held = error
    del source
    gc.collect()
    assert reference() is None and held is not None and attempt is not None


def test_workflow_source_fork_refuses_without_parent_cleanup(inputs):
    if not hasattr(os, "fork"):
        pytest.fail("declared source qualification requires POSIX fork")
    from aware_workspace_sdk.repository_workflow import (
        observe_original_repository_workflow_source,
    )

    attempt, source, observation = workflow_source(inputs)
    pid = os.fork()
    if pid == 0:
        try:
            try:
                observe_original_repository_workflow_source(source)
            except WorkspaceRepositoryWorkflowRefusal:
                os._exit(0)
            os._exit(1)
        except BaseException:  # noqa: BLE001 -- fork child reports failure without running inherited finalizers
            os._exit(2)
    _, status = os.waitpid(pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
    assert (
        observe_original_repository_workflow_source(source).binding
        == observation.binding
    )
    assert attempt is not None


def test_workflow_source_missing_body_state_refuses_terminal(inputs):
    from aware_workspace_sdk.repository_workflow import (
        _SOURCES,
        observe_original_repository_workflow_source,
    )

    attempt, source, _ = workflow_source(inputs)
    runtime = _SOURCES[source][0]
    reader = runtime._sources[-1][1].reader
    original = reader._bodies
    reader._bodies = original[:-1]
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        observe_original_repository_workflow_source(source)
    reader._bodies = original
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        observe_original_repository_workflow_source(source)
    assert attempt is not None


def test_workflow_source_interruption_retires_family_and_preserves_identity(inputs):
    import sys

    from aware_workspace_runtime import source_observation_io
    from aware_workspace_sdk.repository_workflow import (
        verify_original_repository_workflow_source,
    )

    attempt, source, observation = workflow_source(inputs)
    interruption = KeyboardInterrupt("source read interrupted")
    code = source_observation_io.capture_exact_paths.__code__
    raised = []

    def trace(frame, event, arg):
        if event == "line" and frame.f_code is code and not raised:
            raised.append(True)
            raise interruption
        return trace

    previous = sys.gettrace()
    try:
        sys.settrace(trace)
        with pytest.raises(KeyboardInterrupt) as caught:
            verify_original_repository_workflow_source(
                source, expected_binding=observation.binding
            )
    finally:
        sys.settrace(previous)
    assert caught.value is interruption
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        verify_original_repository_workflow_source(
            source, expected_binding=observation.binding
        )
    assert attempt is not None


def test_workflow_source_failure_preserves_original_durable_opening(inputs):
    from aware_workspace_sdk.repository_workflow import (
        verify_original_repository_workflow_source,
    )

    attempt, source, observation = workflow_source(inputs)
    (inputs[3] / "source.py").write_bytes(b"source changed")
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal) as caught:
        verify_original_repository_workflow_source(
            source, expected_binding=observation.binding
        )
    evidence = caught.value.evidence
    assert evidence.persistence_state == "persisted"
    assert evidence.cleanup.attempt_binding_ref == observation.binding.binding_ref
    assert evidence.original_evidence_refs
    assert evidence.cleanup.state == "completed"
    assert attempt is not None


def test_workflow_source_close_failure_clears_custody_without_retry(inputs):
    from aware_workspace_sdk.repository_workflow import (
        _SOURCES,
        release_original_repository_workflow_source,
    )

    attempt, source, _ = workflow_source(inputs)
    runtime = _SOURCES[source][0]
    record = runtime._sources[-1][1]
    descriptor = record.reader._fd
    os.close(
        descriptor
    )  # actual late physical failure, not a fabricated cleanup callback
    cleanup = release_original_repository_workflow_source(source)
    assert cleanup.state == "unknown"
    assert record.reader is None and record.state == ()
    assert release_original_repository_workflow_source(source).state == "unknown"
    assert inputs[-2].release_repository_workflow(attempt).state == "unknown"


def test_workflow_source_binding_equality_is_not_dispatched(inputs, monkeypatch):
    from aware_workspace_sdk.repository_workflow import (
        verify_original_repository_workflow_source,
    )
    from aware_workspace_sdk.repository_workflow_source_values import (
        WorkspaceWorkflowSourceBinding,
    )

    attempt, source, observation = workflow_source(inputs)
    calls = []

    def hostile(*args, **kwargs):
        calls.append("equality")
        raise AssertionError("model equality is not original validation")

    monkeypatch.setattr(WorkspaceWorkflowSourceBinding, "__eq__", hostile)
    verify_original_repository_workflow_source(
        source, expected_binding=observation.binding
    )
    assert not calls and attempt is not None


def test_workflow_source_descriptor_substitution_conserves_foreign_custody(inputs):
    from aware_workspace_sdk.repository_workflow import (
        _SOURCES,
        observe_original_repository_workflow_source,
    )

    attempt, source, _ = workflow_source(inputs)
    reader = _SOURCES[source][0]._sources[-1][1].reader
    original = reader._fd
    foreign = os.open(inputs[3] / "source.py", os.O_RDONLY)
    try:
        reader._fd = foreign
        with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
            observe_original_repository_workflow_source(source)
        assert os.fstat(foreign).st_size > 0
        with pytest.raises(OSError):
            os.fstat(original)
    finally:
        os.close(foreign)
    assert attempt is not None


def test_workflow_source_unknown_error_does_not_pin_multiple_families(inputs):
    import gc
    import weakref

    from aware_workspace_sdk.repository_workflow import (
        observe_original_repository_workflow_source,
    )

    client, request = inputs[-2:]
    first = client.open_repository_workflow_attempt(
        client.plan_repository_workflow(request)
    )
    second = client.open_repository_workflow_attempt(
        client.plan_repository_workflow(replace(request, attempt_ref="attempt:2"))
    )
    source_a = client.retain_repository_workflow_source(first)
    source_b = client.retain_repository_workflow_source(second)
    references = weakref.ref(source_a), weakref.ref(source_b)
    before = observe_original_repository_workflow_source(source_b)
    try:
        observe_original_repository_workflow_source(object())
    except WorkspaceRepositoryWorkflowRefusal as error:
        held = error
    assert (
        observe_original_repository_workflow_source(source_b).binding == before.binding
    )
    del source_a, source_b
    gc.collect()
    assert all(reference() is None for reference in references)
    assert held is not None


def workflow_source_root_descriptors(root):
    """Only descriptors pointing at this disposable source root, not runner IO."""
    found = set()
    for name in os.listdir("/proc/self/fd"):
        try:
            if os.readlink("/proc/self/fd/" + name) == str(root):
                found.add(int(name))
        except FileNotFoundError:
            pass
    return found


@pytest.mark.parametrize("failure", ("interrupt", "exit", "os_error", "guard_error"))
@pytest.mark.parametrize("cleanup_failure", (False, True))
def test_workflow_source_direct_partial_acquisition_cleanup(
    inputs, failure, cleanup_failure
):
    source = inputs[0]
    before = workflow_source_root_descriptors(source)
    error = {
        "interrupt": KeyboardInterrupt("root acquisition interrupted"),
        "exit": SystemExit(41),
        "os_error": OSError(5, "root acquisition failed"),
        "guard_error": ValueError("post-acquisition guard failed"),
    }[failure]
    calls = []

    def guard():
        acquired = workflow_source_root_descriptors(source) - before
        if acquired:
            calls.extend(acquired)
            if cleanup_failure:
                # Real once-only release failure: the injected acquisition fault
                # already consumed the physical descriptor. No callback substitute.
                for descriptor in acquired:
                    os.close(descriptor)
            raise error

    with pytest.raises(type(error)) as caught:
        package_checkout.PackageSourceCheckout(source, _workflow_guard=guard)
    assert caught.value is error
    assert len(calls) == 1
    assert workflow_source_root_descriptors(source) == before
    assert vars(error)["workspace_source_acquisition_cleanup"] == (
        "unknown" if cleanup_failure else "completed"
    )
    assert error.__cause__ is None
    if cleanup_failure:
        cleanup_error = vars(error)["workspace_source_acquisition_cleanup_error"]
        assert type(cleanup_error) is OSError and cleanup_error.errno == 9
    assert error.__traceback__ is not None  # keep it held while checking conservation


@pytest.mark.parametrize("failure", ("interrupt", "exit", "os_error", "guard_error"))
@pytest.mark.parametrize("cleanup_failure", (False, True))
def test_workflow_source_sdk_partial_acquisition_cleanup(
    inputs, monkeypatch, failure, cleanup_failure
):
    from aware_workspace_runtime import repository_workflow as runtime

    source, _, _, _, client, request = inputs
    attempt = client.open_repository_workflow_attempt(
        client.plan_repository_workflow(request)
    )
    before = workflow_source_root_descriptors(source)
    error = {
        "interrupt": KeyboardInterrupt("SDK root acquisition interrupted"),
        "exit": SystemExit(42),
        "os_error": OSError(5, "SDK root acquisition failed"),
        "guard_error": ValueError("SDK post-acquisition guard failed"),
    }[failure]
    original = runtime._reader_entries_current
    acquired = []

    def guard():
        original()
        new = workflow_source_root_descriptors(source) - before
        if new:
            acquired.extend(new)
            if cleanup_failure:
                for descriptor in new:
                    os.close(descriptor)
            raise error

    monkeypatch.setattr(runtime, "_reader_entries_current", guard)
    raised = (
        type(error)
        if failure in ("interrupt", "exit")
        else WorkspaceRepositoryWorkflowRefusal
    )
    with pytest.raises(raised) as caught:
        client.retain_repository_workflow_source(attempt)
    assert len(acquired) == 1
    assert workflow_source_root_descriptors(source) == before
    if failure in ("interrupt", "exit"):
        assert caught.value is error
        evidence = vars(error)["workflow_evidence"]
    else:
        evidence = caught.value.evidence
        current = caught.value
        while current is not error and current.__cause__ is not None:
            current = current.__cause__
        assert current is error
    assert evidence.cleanup.state == ("unknown" if cleanup_failure else "completed")
    assert evidence.persistence_state == "persisted" and evidence.original_evidence_refs
    monkeypatch.setattr(runtime, "_reader_entries_current", original)
    with pytest.raises(WorkspaceRepositoryWorkflowRefusal):
        client.retain_repository_workflow_source(attempt)
    assert workflow_source_root_descriptors(source) == before
    client.release_repository_workflow(attempt)


def test_workflow_source_direct_partial_fstat_failure_releases_root(
    inputs, monkeypatch
):
    source = inputs[0]
    before = workflow_source_root_descriptors(source)
    original = os.fstat
    error = OSError(5, "original fstat failure")

    def fail(fd):
        if fd in workflow_source_root_descriptors(source) - before:
            raise error
        return original(fd)

    monkeypatch.setattr(os, "fstat", fail)
    with pytest.raises(OSError) as caught:
        package_checkout.PackageSourceCheckout(source)
    assert caught.value is error
    assert vars(error)["workspace_source_acquisition_cleanup"] == "completed"
    assert workflow_source_root_descriptors(source) == before
