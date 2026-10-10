"""Real owner composition; Git calls and identity substitutions are fixtures only."""

from __future__ import annotations

import copy
import os
import pickle
import subprocess
import threading
from dataclasses import replace

import pytest
from aware_protocol_fs_adapter import admit_protocol_manifest
from aware_protocol_fs_adapter import bootstrap as fs
from aware_protocol_runtime import ProtocolAdmissionOutcomeKind
from aware_protocol_sdk import bootstrap as sdk
from aware_protocol_sdk.bootstrap import (
    _CLIENTS,
    ProtocolBootstrapClient,
    ProtocolBootstrapError,
    ProtocolBootstrapRequest,
    protocol_bootstrap_value_to_payload,
)


@pytest.fixture(autouse=True)
def execution(monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "protocol-bootstrap-test")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    return "codex-protocol-bootstrap-test"


def _git(root, *arguments):
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def _fds():
    return len(os.listdir("/proc/self/fd"))


@pytest.fixture
def selected(tmp_path, execution):
    root = tmp_path / "customer"
    root.mkdir(mode=0o750)
    assert _git(root, "init", "--initial-branch=main").returncode == 0
    client = ProtocolBootstrapClient.filesystem(
        repository_root=str(root), execution_id=execution
    )
    return root, client


def _apply(client, request):
    with client.plan_initialization(request) as plan:
        admission = client.admit_initialization(plan)
        return client.initialize_profile(request, admission=admission)


@pytest.mark.parametrize("templates", [False, True])
@pytest.mark.parametrize("existing_directories", [False, True])
def test_real_preview_apply_and_admission(selected, templates, existing_directories):
    root, client = selected
    if existing_directories:
        (root / "docs/issues").mkdir(parents=True, mode=0o750)
    (root / "foreign.txt").write_text("preserve\n")
    assert _git(root, "add", "foreign.txt").returncode == 0
    index = (root / ".git/index").read_bytes()
    baseline = _fds()
    preview = client.prepare_bootstrap_request(install_agent_contract=templates)
    observation = client.initialize_profile(preview)
    assert observation.outcome == "planned" and not observation.effects
    assert not (root / "aware.protocol.toml").exists()
    request = client.prepare_bootstrap_request(
        install_agent_contract=templates, dry_run=False
    )
    result = _apply(client, request)
    assert result.outcome == "initialized" and result.provider_invoked
    assert result.attempt_ref and result.cleanup_state == "completed"
    assert all(item.state == "applied" for item in result.effects)
    assert not result.authorizes_retry and result.ledger_complete
    assert (root / ".git/index").read_bytes() == index
    assert (root / "foreign.txt").read_text() == "preserve\n"
    assert _git(root, "rev-parse", "--verify", "HEAD").returncode != 0
    assert not _git(root, "remote").stdout
    assert (root / "AGENTS.md").exists() is templates
    assert (root / "docs/issues/PROTOCOL.md").exists() is templates
    assert root.stat().st_mode & 0o777 == 0o750
    assert _fds() == baseline
    admitted = admit_protocol_manifest(
        manifest_path=root / "aware.protocol.toml", repository_root=root
    )
    assert admitted.outcome is ProtocolAdmissionOutcomeKind.CANONICAL_V1
    assert admitted.source_sha256 == result.manifest_source_sha256
    assert admitted.manifest.digest == result.manifest_semantic_digest
    roles = {item.record_key: item.role.value for item in admitted.manifest.records}
    assert roles == {
        "issue": "authority",
        "goal": "unavailable",
        "feed": "unavailable",
        "specification": "unavailable",
        "evidence": "unavailable",
    }
    with pytest.raises(ProtocolBootstrapError):
        _apply(client, request)
    assert (root / ".git/index").read_bytes() == index


def test_absent_root_can_render_but_cannot_admit(tmp_path, execution):
    root = tmp_path / "absent"
    client = ProtocolBootstrapClient.filesystem(
        repository_root=str(root), execution_id=execution
    )
    request = client.prepare_bootstrap_request(dry_run=False)
    assert request.directory_paths == ("docs", "docs/issues")
    assert len(client.render_bootstrap_input(request).files) == 3
    with pytest.raises(ProtocolBootstrapError):
        client.plan_initialization(request)
    assert not root.exists()


@pytest.mark.parametrize(
    "issue_root",
    [
        "../outside",
        ".git",
        "a/.git",
        "AGENTS.md",
        "AGENTS.md/sub",
        "aware.protocol.toml",
        "/absolute",
        "a//b",
        "./issues",
    ],
)
def test_bad_coordinates_refuse_before_effects(selected, issue_root):
    root, client = selected
    with pytest.raises((ValueError, ProtocolBootstrapError)):
        client.prepare_bootstrap_request(issue_root=issue_root)
    assert not (root / "aware.protocol.toml").exists()


@pytest.mark.parametrize(
    "path", ["AGENTS.md", "aware.protocol.toml", "docs/issues/PROTOCOL.md"]
)
@pytest.mark.parametrize("kind", ["file", "directory", "symlink"])
def test_existing_targets_never_adopt_or_overwrite(selected, path, kind):
    root, client = selected
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if kind == "file":
        target.write_text("foreign\n")
    elif kind == "directory":
        target.mkdir()
    else:
        target.symlink_to(root / "missing")
    request = client.prepare_bootstrap_request(dry_run=False)
    baseline = _fds()
    with pytest.raises(ProtocolBootstrapError):
        client.plan_initialization(request)
    assert _fds() == baseline
    if kind == "file":
        assert target.read_text() == "foreign\n"
    elif kind == "symlink":
        assert target.is_symlink()
    else:
        assert target.is_dir()


def test_explicit_ancestors_no_live_flag_or_raw_writer(selected):
    root, client = selected
    request = client.prepare_bootstrap_request(dry_run=False)
    with pytest.raises(ProtocolBootstrapError):
        client.initialize_profile(request)
    with pytest.raises(ProtocolBootstrapError):
        client.plan_initialization(replace(request, directory_paths=("docs/issues",)))
    runtime = _CLIENTS[client]
    physical = runtime.physical.retain(client.render_bootstrap_input(request))
    try:
        with pytest.raises(ValueError, match="claim"):
            physical.apply(claim=None)
        assert not (root / "aware.protocol.toml").exists()
    finally:
        physical.release()


@pytest.mark.parametrize("method", ["observe", "admit", "apply"])
def test_stale_original_handle_retires_and_preserves_foreign_target(selected, method):
    root, client = selected
    baseline = _fds()
    request = client.prepare_bootstrap_request(dry_run=False)
    plan = client.plan_initialization(request)
    admission = client.admit_initialization(plan) if method == "apply" else None
    (root / "aware.protocol.toml").write_text("racing foreign\n")
    with pytest.raises(ProtocolBootstrapError):
        if method == "observe":
            plan.observe()
        elif method == "admit":
            client.admit_initialization(plan)
        else:
            client.initialize_profile(request, admission=admission)
    assert plan.observe().phase == "retired"
    assert (root / "aware.protocol.toml").read_text() == "racing foreign\n"
    assert _fds() == baseline


@pytest.mark.parametrize("method", ["observe", "admit", "apply"])
def test_interrupted_freshness_is_terminal(selected, monkeypatch, method):
    root, client = selected
    request = client.prepare_bootstrap_request(dry_run=False)
    plan = client.plan_initialization(request)
    runtime = _CLIENTS[client]
    admission = client.admit_initialization(plan) if method == "apply" else None
    physical = runtime.plans[plan].physical
    baseline = _fds() - 1

    def interrupt():
        raise KeyboardInterrupt("controlled freshness interruption")

    monkeypatch.setattr(physical, "validate_current", interrupt)
    with pytest.raises(ProtocolBootstrapError):
        if method == "observe":
            plan.observe()
        elif method == "admit":
            client.admit_initialization(plan)
        else:
            client.initialize_profile(request, admission=admission)
    assert plan.observe().phase == "retired"
    assert not (root / "aware.protocol.toml").exists()
    assert _fds() == baseline


@pytest.mark.parametrize(
    "mutation",
    ["caller", "nested_request", "effect", "diagnostics", "attempt", "cleanup"],
)
def test_actual_creation_malformed_return_keeps_original_ledger(
    selected, monkeypatch, mutation
):
    root, client = selected
    request = client.prepare_bootstrap_request(dry_run=False)
    runtime = _CLIENTS[client]
    original = runtime.initialize_profile
    captured = None

    def corrupt(invocation, *, admission=None):
        nonlocal captured
        result = original(invocation, admission=admission)
        captured = protocol_bootstrap_value_to_payload(result)
        if mutation == "caller":
            object.__setattr__(request, "repository_root", "/foreign")
        elif mutation == "nested_request":
            object.__setattr__(result.request, "repository_root", "/foreign")
        elif mutation == "effect":
            object.__setattr__(result.effects[-1], "state", "none")
        elif mutation == "diagnostics":
            result = replace(result, outcome="refused", diagnostics=())
        elif mutation == "attempt":
            result = replace(result, attempt_ref=None)
        else:
            result = replace(result, cleanup_state="unknown")
        return result

    monkeypatch.setattr(runtime, "initialize_profile", corrupt)
    with client.plan_initialization(request) as plan:
        admission = client.admit_initialization(plan)
        with pytest.raises(ProtocolBootstrapError) as raised:
            client.initialize_profile(request, admission=admission)
        evidence = protocol_bootstrap_value_to_payload(raised.value.evidence)
        for field in ("request", "attempt_ref", "effects", "cleanup_state"):
            assert evidence[field] == captured[field]
        assert evidence["provider_invoked"] and not evidence["authorizes_retry"]
        assert not evidence["ledger_complete"] and evidence["reported_result"]
        assert (root / "aware.protocol.toml").is_file()
        with pytest.raises(ProtocolBootstrapError):
            client.initialize_profile(
                client.prepare_bootstrap_request(dry_run=False), admission=admission
            )


@pytest.mark.parametrize("failure", ["after_manifest", "unknown_file", "release"])
def test_partial_publication_and_unknown_cleanup_are_never_upgraded(
    selected, monkeypatch, failure
):
    from aware_file_system.retained_bootstrap import RetainedBootstrapCreation

    root, client = selected
    request = client.prepare_bootstrap_request(dry_run=False)
    baseline = _fds()
    original = RetainedBootstrapCreation.create_next_file

    def failed_file(handle):
        effect = original(handle)
        if effect.path == "aware.protocol.toml":
            raise KeyboardInterrupt("controlled interruption after actual publication")
        return effect

    def failed_link(*args, **kwargs):
        raise KeyboardInterrupt("controlled submitted link uncertainty")

    if failure == "after_manifest":
        monkeypatch.setattr(RetainedBootstrapCreation, "create_next_file", failed_file)
    elif failure == "unknown_file":
        monkeypatch.setattr(os, "link", failed_link)
    with client.plan_initialization(request) as plan:
        admission = client.admit_initialization(plan)
        if failure == "release":
            physical = _CLIENTS[client].plans[plan].physical
            original_finish = physical._creation.finish

            def failed_finish():
                original_finish()
                raise KeyboardInterrupt("controlled finish observation interruption")

            monkeypatch.setattr(
                physical._creation.__class__, "finish", lambda handle: failed_finish()
            )
        with pytest.raises(ProtocolBootstrapError) as raised:
            client.initialize_profile(request, admission=admission)
        evidence = raised.value.evidence
        assert evidence.provider_invoked and evidence.attempt_ref
        assert evidence.effects and not evidence.authorizes_retry
        assert evidence.cleanup_state == "unknown" and not evidence.ledger_complete
        if failure != "unknown_file":
            assert (root / "aware.protocol.toml").is_file()
            assert any(
                item.path == "aware.protocol.toml" and item.state == "applied"
                for item in evidence.effects
            )
        else:
            assert any(item.state == "unknown" for item in evidence.effects)
        plan.release()
        assert _CLIENTS[client].plans[plan].physical.cleanup_state == "unknown"
    assert _fds() == baseline


def test_independent_plans_foreign_handles_and_once_only_concurrency(
    selected, tmp_path, execution
):
    root, client = selected
    request = client.prepare_bootstrap_request(dry_run=False)
    first = client.plan_initialization(request)
    with client.plan_initialization(request) as second:
        first.release()
        assert second.observe().phase == "planned"
        for clone in (copy.copy, copy.deepcopy, pickle.dumps):
            with pytest.raises(TypeError):
                clone(second)
        admission = client.admit_initialization(second)
        other = ProtocolBootstrapClient.filesystem(
            repository_root=str(tmp_path / "other"), execution_id=execution
        )
        with pytest.raises(ProtocolBootstrapError):
            other.initialize_profile(
                ProtocolBootstrapRequest(str(tmp_path / "other"), dry_run=False),
                admission=admission,
            )
        results = []

        def apply():
            try:
                results.append(
                    client.initialize_profile(request, admission=admission).outcome
                )
            except ProtocolBootstrapError:
                results.append("refused")

        threads = [threading.Thread(target=apply) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
            assert not thread.is_alive()
        assert sorted(results) == ["initialized", "refused"]
        assert (root / "aware.protocol.toml").is_file()


def test_pure_manifest_validation_does_not_admit_a_symlink_topology(selected, tmp_path):
    root, client = selected
    request = client.prepare_bootstrap_request()
    manifest = client.render_bootstrap_input(request).files[0].content_utf8.encode()
    assert (
        fs.validate_protocol_manifest_content(source=manifest).outcome
        is ProtocolAdmissionOutcomeKind.CANONICAL_V1
    )
    (root / "docs").symlink_to(tmp_path, target_is_directory=True)
    from aware_protocol_fs_adapter import admit_protocol_manifest_bytes

    assert (
        admit_protocol_manifest_bytes(source=manifest, repository_root=root).outcome
        is ProtocolAdmissionOutcomeKind.MALFORMED_V1
    )


def test_same_runtime_can_consume_accepted_workspace_preparation(tmp_path, execution):
    from aware_workspace_sdk.repository_preparation import (
        RepositoryPrepareRequest,
        WorkspaceRepositoryPreparationClient,
    )

    root = tmp_path / "new-customer"
    protocol = ProtocolBootstrapClient.filesystem(
        repository_root=str(root), execution_id=execution
    )
    prospective = protocol.prepare_bootstrap_request(dry_run=False)
    assert len(protocol.render_bootstrap_input(prospective).files) == 3
    repository = WorkspaceRepositoryPreparationClient.filesystem(
        repository_root=str(root), execution_id=execution
    )
    request = RepositoryPrepareRequest(str(root), True)
    with repository.plan_repository_preparation(request) as plan:
        created = repository.prepare_repository(
            request, admission=repository.admit_repository_preparation(plan)
        )
    assert created.outcome == "created" and created.cleanup_state == "completed"
    # Fresh Protocol authority follows repository preparation; no receipt used as admission.
    result = _apply(protocol, protocol.prepare_bootstrap_request(dry_run=False))
    assert result.outcome == "initialized" and not _git(root, "ls-files").stdout


def test_changed_postimage_after_confirmed_disposal_is_not_success(
    selected, monkeypatch
):
    root, client = selected
    request = client.prepare_bootstrap_request(dry_run=False)
    baseline = _fds()
    with client.plan_initialization(request) as plan:
        admission = client.admit_initialization(plan)
        physical = _CLIENTS[client].plans[plan].physical
        original = physical._creation.__class__.finish

        def substitute_after_finish(handle):
            original(handle)
            (root / "AGENTS.md").write_text("changed after verified disposal\n")

        monkeypatch.setattr(
            physical._creation.__class__, "finish", substitute_after_finish
        )
        with pytest.raises(ProtocolBootstrapError) as raised:
            client.initialize_profile(request, admission=admission)
        evidence = raised.value.evidence
        assert evidence.provider_invoked and evidence.attempt_ref
        assert evidence.cleanup_state == "completed" and not evidence.ledger_complete
        assert len(evidence.effects) == 5 and not evidence.authorizes_retry
        assert (root / "AGENTS.md").read_text() == "changed after verified disposal\n"
        with pytest.raises(ProtocolBootstrapError):
            client.initialize_profile(request, admission=admission)
    assert _fds() == baseline


def test_no_replace_race_preserves_foreign_file_and_directory_effects(
    selected, monkeypatch
):
    root, client = selected
    request = client.prepare_bootstrap_request(dry_run=False)
    original = os.link

    def insert_competitor(source, destination, **options):
        if destination == "aware.protocol.toml":
            (root / destination).write_text("foreign race winner\n")
        return original(source, destination, **options)

    baseline = _fds()
    monkeypatch.setattr(os, "link", insert_competitor)
    with pytest.raises(ProtocolBootstrapError) as raised:
        _apply(client, request)
    evidence = raised.value.evidence
    assert evidence.provider_invoked and evidence.attempt_ref
    assert not evidence.authorizes_retry and not evidence.ledger_complete
    assert any(
        item.kind == "directory" and item.state == "applied"
        for item in evidence.effects
    )
    assert (root / "aware.protocol.toml").read_text() == "foreign race winner\n"
    assert not (root / "AGENTS.md").exists()
    assert _fds() == baseline


def test_plan_failure_preserves_unknown_original_disposal(selected, monkeypatch):
    root, client = selected
    request = client.prepare_bootstrap_request(dry_run=False)
    baseline = _fds()
    original_retain = fs.FilesystemProtocolBootstrapPort.retain

    def interrupted_plan(owner, rendered):
        physical = original_retain(owner, rendered)
        original_release = physical._creation.__class__.release

        def interrupted_release(handle):
            original_release(handle)
            raise KeyboardInterrupt("controlled disposal observation interruption")

        monkeypatch.setattr(
            physical._creation.__class__, "release", interrupted_release
        )
        return physical

    def failed_digest(physical):
        raise ValueError("controlled plan observation failure")

    monkeypatch.setattr(fs.FilesystemProtocolBootstrapPort, "retain", interrupted_plan)
    monkeypatch.setattr(fs._Retained, "plan_digest", failed_digest)
    with pytest.raises(ProtocolBootstrapError) as raised:
        client.plan_initialization(request)
    evidence = raised.value.evidence
    assert evidence.cleanup_state == "unknown" and not evidence.provider_invoked
    assert not evidence.effects and not evidence.authorizes_retry
    assert not (root / "aware.protocol.toml").exists() and _fds() == baseline


def test_foreign_process_cannot_spend_original_parent_admission(selected):
    root, client = selected
    request = client.prepare_bootstrap_request(dry_run=False)
    baseline = _fds()
    with client.plan_initialization(request) as plan:
        admission = client.admit_initialization(plan)
        read_end, write_end = os.pipe()
        child = os.fork()
        if child == 0:
            try:
                os.close(read_end)
                try:
                    client.initialize_profile(request, admission=admission)
                except ProtocolBootstrapError as error:
                    assert (
                        not error.evidence.provider_invoked
                        and not error.evidence.effects
                    )
                    os.write(write_end, b"refused")
                else:
                    os.write(write_end, b"unexpected success")
            finally:
                os._exit(0)
        os.close(write_end)
        try:
            assert os.read(read_end, 128) == b"refused"
            assert os.waitpid(child, 0)[1] == 0
        finally:
            os.close(read_end)
        assert not (root / "aware.protocol.toml").exists()
        assert (
            client.initialize_profile(request, admission=admission).outcome
            == "initialized"
        )
    assert _fds() == baseline


def test_modified_rendering_cannot_become_original_physical_plan(selected):
    root, client = selected
    request = client.prepare_bootstrap_request(dry_run=False)
    rendered = client.render_bootstrap_input(request)
    physical = _CLIENTS[client].physical
    with pytest.raises(ValueError, match="bootstrap_original_rendering_required"):
        physical.retain(replace(rendered, diagnostics=("forged rendering",)))
    assert not (root / "aware.protocol.toml").exists()


def test_execution_change_at_sdk_return_preserves_original_publication(
    selected, monkeypatch
):
    root, client = selected
    request = client.prepare_bootstrap_request(dry_run=False)
    original = _CLIENTS[client].initialize_profile

    def change_execution_after_dispatch(provider, invocation, *, admission=None):
        result = original(invocation, admission=admission)
        monkeypatch.setenv("CODEX_THREAD_ID", "different-returning-execution")
        return result

    baseline = _fds()
    monkeypatch.setattr(
        _CLIENTS[client].__class__,
        "initialize_profile",
        change_execution_after_dispatch,
    )
    with pytest.raises(ProtocolBootstrapError) as raised:
        _apply(client, request)
    evidence = raised.value.evidence
    assert (
        evidence.request == request
        and evidence.execution_id == "codex-protocol-bootstrap-test"
    )
    assert (
        evidence.provider_invoked
        and evidence.attempt_ref
        and len(evidence.effects) == 5
    )
    assert evidence.cleanup_state == "completed" and not evidence.ledger_complete
    assert not evidence.authorizes_retry and evidence.reported_result is not None
    assert (root / "aware.protocol.toml").exists() and _fds() == baseline


@pytest.mark.parametrize("missing_field", ["request", "effects"])
def test_missing_return_field_cannot_destroy_original_ledger(
    selected, monkeypatch, missing_field
):
    root, client = selected
    request = client.prepare_bootstrap_request(dry_run=False)
    original = _CLIENTS[client].initialize_profile

    def broken_return(provider, invocation, *, admission=None):
        result = original(invocation, admission=admission)
        object.__delattr__(result, missing_field)
        return result

    baseline = _fds()
    monkeypatch.setattr(_CLIENTS[client].__class__, "initialize_profile", broken_return)
    with pytest.raises(ProtocolBootstrapError) as raised:
        _apply(client, request)
    evidence = raised.value.evidence
    assert evidence.request == request and len(evidence.effects) == 5
    assert evidence.attempt_ref and evidence.provider_invoked
    assert evidence.reported_result[missing_field] == {
        "unvalidated_missing_field": True
    }
    assert evidence.cleanup_state == "completed" and not evidence.ledger_complete
    assert (root / "aware.protocol.toml").exists() and _fds() == baseline


@pytest.mark.parametrize(
    "failure",
    [
        "missing_root",
        "missing_directories",
        "interrupt",
        "copy_interrupt",
        "copy_attribute",
        "invalid_value",
    ],
)
def test_initial_snapshot_failure_retires_original_admission(
    selected, monkeypatch, failure
):
    root, client = selected
    request = client.prepare_bootstrap_request(dry_run=False)
    provider = _CLIENTS[client]
    baseline = _fds()
    plan = client.plan_initialization(request)
    valid = plan.observe().request
    admission = client.admit_initialization(plan)
    original_dispatch = provider.initialize_profile
    dispatched = []

    def observe_dispatch(owner, invocation, *, admission=None):
        dispatched.append(invocation)
        return original_dispatch(invocation, admission=admission)

    monkeypatch.setattr(provider.__class__, "initialize_profile", observe_dispatch)
    if failure.startswith("missing_"):
        object.__delattr__(
            request,
            "repository_root" if failure == "missing_root" else "directory_paths",
        )
    elif failure == "invalid_value":
        object.__setattr__(request, "dry_run", 1)
    else:
        original_snapshot = sdk.detached
        calls = 0

        def failed_snapshot(value):
            nonlocal calls
            calls += 1
            if calls == (1 if failure == "interrupt" else 2):
                if failure == "copy_attribute":
                    raise AttributeError("controlled second snapshot field failure")
                raise KeyboardInterrupt("controlled snapshot interruption")
            return original_snapshot(value)

        monkeypatch.setattr(sdk, "detached", failed_snapshot)
    try:
        with pytest.raises(ProtocolBootstrapError) as raised:
            client.initialize_profile(request, admission=admission)
        evidence = raised.value.evidence
        assert evidence.code == "protocol_bootstrap_request_snapshot_failed"
        assert evidence.phase == "snapshot" and evidence.request == valid
        assert evidence.execution_id == provider.execution_id
        assert not evidence.provider_invoked and evidence.attempt_ref is None
        assert not evidence.effects and evidence.cleanup_state == "completed"
        assert not evidence.ledger_complete and not evidence.authorizes_retry
        assert evidence.reported_result is not None
        assert not dispatched and plan.observe().phase == "retired"
        assert _fds() == baseline and not (root / "aware.protocol.toml").exists()
        with pytest.raises(ProtocolBootstrapError):
            client.initialize_profile(valid, admission=admission)
        with pytest.raises(ProtocolBootstrapError):
            client.admit_initialization(plan)
        assert not (root / "aware.protocol.toml").exists() and _fds() == baseline
    finally:
        plan.release()


def test_snapshot_retirement_preserves_independent_plan(selected):
    root, client = selected
    request = client.prepare_bootstrap_request(dry_run=False)
    baseline = _fds()
    with (
        client.plan_initialization(request) as first,
        client.plan_initialization(request) as second,
    ):
        admission = client.admit_initialization(first)
        object.__delattr__(request, "repository_root")
        with pytest.raises(ProtocolBootstrapError):
            client.initialize_profile(request, admission=admission)
        assert (
            first.observe().phase == "retired" and second.observe().phase == "planned"
        )
        result = client.initialize_profile(
            second.observe().request, admission=client.admit_initialization(second)
        )
        assert result.outcome == "initialized"
    assert (root / "aware.protocol.toml").exists() and _fds() == baseline


def test_snapshot_retirement_does_not_upgrade_interrupted_release(
    selected, monkeypatch
):
    root, client = selected
    request = client.prepare_bootstrap_request(dry_run=False)
    baseline = _fds()
    with client.plan_initialization(request) as plan:
        admission = client.admit_initialization(plan)
        physical = _CLIENTS[client].plans[plan].physical
        original = physical._creation.__class__.release
        calls = 0

        def interrupted_release(handle):
            nonlocal calls
            calls += 1
            original(handle)
            raise KeyboardInterrupt("controlled disposal observation failure")

        monkeypatch.setattr(
            physical._creation.__class__, "release", interrupted_release
        )
        object.__delattr__(request, "directory_paths")
        with pytest.raises(ProtocolBootstrapError) as raised:
            client.initialize_profile(request, admission=admission)
        evidence = raised.value.evidence
        assert not evidence.provider_invoked and not evidence.effects
        assert evidence.cleanup_state == "unknown" and not evidence.authorizes_retry
        assert plan.observe().phase == "retired" and _fds() == baseline
        plan.release()
        assert physical.cleanup_state == "unknown" and calls == 1
        with pytest.raises(ProtocolBootstrapError):
            client.initialize_profile(plan.observe().request, admission=admission)
    assert not (root / "aware.protocol.toml").exists() and _fds() == baseline


def test_failed_snapshot_with_foreign_admission_does_not_retire_its_owner(
    selected, tmp_path, execution
):
    root, owner = selected
    original = owner.prepare_bootstrap_request(dry_run=False)
    with owner.plan_initialization(original) as plan:
        admission = owner.admit_initialization(plan)
        foreign = ProtocolBootstrapClient.filesystem(
            repository_root=str(tmp_path / "foreign"), execution_id=execution
        )
        malformed = original.__class__(str(tmp_path / "foreign"), dry_run=False)
        object.__delattr__(malformed, "repository_root")
        with pytest.raises(ProtocolBootstrapError) as raised:
            foreign.initialize_profile(malformed, admission=admission)
        evidence = raised.value.evidence
        assert "request_is_selected_root_context_not_invocation" in evidence.diagnostics
        assert not evidence.provider_invoked and not evidence.effects
        assert plan.observe().phase == "admitted"
        assert (
            owner.initialize_profile(original, admission=admission).outcome
            == "initialized"
        )
    assert (root / "aware.protocol.toml").exists()
