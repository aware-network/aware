"""Original fresh-root enrollment, persistence, restart and no-Issue boundaries.

This is enrollment qualification, not a Project constructor or publication proof.
All effects are confined to disposable customer repositories.
"""

from __future__ import annotations

import copy
import json
import os
import pickle
import subprocess
import sys
from dataclasses import replace

import pytest
from aware_workspace_sdk.initial_authoring import (
    InitialAuthoringEnrollment,
    InitialAuthoringEnrollmentEvidence,
)
from aware_workspace_sdk.repository_preparation import (
    RepositoryPrepareRequest,
    WorkspaceRepositoryPreparationClient,
)
from aware_workspace_sdk.repository_publication import (
    WorkspaceRepositoryCommitRequest,
    WorkspaceRepositoryPublicationClient,
)


@pytest.fixture
def fresh(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "initial-authoring-test")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    root = tmp_path / "customer"
    preparation = WorkspaceRepositoryPreparationClient.filesystem(
        repository_root=str(root),
        execution_id="codex-initial-authoring-test",
    )
    request = RepositoryPrepareRequest(str(root), True)
    with preparation.plan_repository_preparation(request) as plan:
        admission = preparation.admit_repository_preparation(plan)
        result = preparation.prepare_repository(request, admission=admission)
    publication = WorkspaceRepositoryPublicationClient.filesystem(
        repository_root=str(root)
    )
    return root, preparation, publication, result


def _record(root):
    return root / ".git/aware-initial-authoring-v1/enrollment.json"


def test_original_enrollment_and_same_evidence_after_fresh_selection(fresh):
    root, preparation, publication, result = fresh
    handle = publication.enroll_initial_authoring(preparation)
    evidence = handle.observe()
    assert evidence.preparation_attempt_ref == result.attempt_ref
    assert evidence.issuer_ref == publication._provider._provider_ref
    assert evidence.issuer_generation == publication._provider._generation
    assert evidence.assurance == "local_fresh_repository_execution_correlation"
    assert evidence.profile == "repository_initial_authoring_v1"
    assert (
        InitialAuthoringEnrollmentEvidence.from_wire(
            json.loads(_record(root).read_bytes())
        )
        == evidence
    )
    restored = WorkspaceRepositoryPublicationClient.filesystem(
        repository_root=str(root)
    )
    assert restored.restore_initial_authoring_enrollment().observe() == evidence
    assert list(root.iterdir()) == [root / ".git"]
    assert not (root / ".git/index").exists()
    assert not (root / "docs").exists()
    assert (
        subprocess.run(
            ["git", "-C", str(root), "show-ref"], capture_output=True, check=False
        ).returncode
        == 1
    )


def test_restart_recovers_original_enrollment_not_new_identity(fresh):
    root, preparation, publication, _ = fresh
    original = publication.enroll_initial_authoring(preparation).observe()
    body = """
import json, sys
from aware_workspace_sdk.repository_publication import WorkspaceRepositoryPublicationClient
client = WorkspaceRepositoryPublicationClient.filesystem(repository_root=sys.argv[1])
print(json.dumps(client.restore_initial_authoring_enrollment().observe().to_wire(), sort_keys=True))
"""
    completed = subprocess.run(
        [sys.executable, "-B", "-c", body, str(root)],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
    )
    assert completed.returncode == 0, completed.stderr
    assert (
        InitialAuthoringEnrollmentEvidence.from_wire(json.loads(completed.stdout))
        == original
    )


@pytest.mark.parametrize("operation", [copy.copy, copy.deepcopy, pickle.dumps])
def test_handle_copy_and_transport_refuse(fresh, operation):
    _, preparation, publication, _ = fresh
    handle = publication.enroll_initial_authoring(preparation)
    with pytest.raises(TypeError):
        operation(handle)


def test_forged_and_decoded_enrollment_cannot_enter_publisher(fresh):
    root, preparation, publication, _ = fresh
    handle = publication.enroll_initial_authoring(preparation)
    with pytest.raises(TypeError):
        InitialAuthoringEnrollment()
    with pytest.raises(ValueError):
        object.__new__(InitialAuthoringEnrollment).observe()
    evidence = InitialAuthoringEnrollmentEvidence.from_wire(handle.observe().to_wire())
    # No files exist to stage, but even a genuine enrollment cannot stand in
    # for the original Issue-work admission on the existing publication port.
    plan = publication.plan_repository_commit(
        WorkspaceRepositoryCommitRequest(
            str(root),
            ("project-test.toml",),
            "must not publish",
            "enrollment-is-not-admission",
        )
    )
    for substitute in (handle, evidence, evidence.to_wire()):
        with pytest.raises(ValueError):
            publication.publish_repository_commit(plan, substitute)
    publication.release_repository_plan(plan)
    assert not (root / ".git/index").exists()


def test_decoded_or_mutated_preparation_result_is_not_witness(fresh):
    root, preparation, publication, result = fresh
    for substitute in (result, replace(result), {"result": result}):
        with pytest.raises(ValueError, match="original_preparation_client"):
            publication.enroll_initial_authoring(substitute)
    # An independently selected existing-root preparation client has no witness.
    other = WorkspaceRepositoryPreparationClient.filesystem(
        repository_root=str(root),
        execution_id=result.execution_id,
    )
    other._provider().last_original_result = result
    with pytest.raises(ValueError, match="original_fresh_root_witness"):
        publication.enroll_initial_authoring(other)
    assert publication.enroll_initial_authoring(preparation).observe()


@pytest.mark.parametrize("change", ["worktree", "ref", "index", "remote", "branch"])
def test_changes_before_enrollment_refuse_and_cannot_refresh_witness(fresh, change):
    root, preparation, publication, _ = fresh
    if change == "worktree":
        (root / "foreign.txt").write_bytes(b"keep")
    elif change == "index":
        (root / ".git/index").write_bytes(b"foreign")
    elif change == "remote":
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "remote",
                "add",
                "origin",
                "https://example.invalid/repo",
            ],
            check=True,
        )
    elif change == "branch":
        subprocess.run(
            ["git", "-C", str(root), "symbolic-ref", "HEAD", "refs/heads/other"],
            check=True,
        )
    else:
        # Exact original publisher remains the only writer under qualification;
        # this fixture's raw metadata mutation is an adversarial outside effect.
        (root / ".git/refs/tags/foreign").write_text("1" * 40 + "\n")
    with pytest.raises((ValueError, OSError)):
        publication.enroll_initial_authoring(preparation)
    with pytest.raises(ValueError, match="original_fresh_root_witness"):
        publication.enroll_initial_authoring(preparation)
    assert not _record(root).exists()


@pytest.mark.parametrize(
    "change",
    [
        "truncate",
        "missing",
        "extra",
        "symlink",
        "hardlink",
        "mode",
        "redigest",
        "duplicate",
    ],
)
def test_lost_or_substituted_retention_cannot_reenroll(fresh, change):
    root, preparation, publication, _ = fresh
    handle = publication.enroll_initial_authoring(preparation)
    record = _record(root)
    if change == "truncate":
        record.write_bytes(b'{"schema_id":')
    elif change == "missing":
        record.unlink()
    elif change == "extra":
        (record.parent / "foreign").write_bytes(b"keep")
    elif change == "symlink":
        outside = root.parent / "copied.json"
        outside.write_bytes(record.read_bytes())
        record.unlink()
        record.symlink_to(outside)
    elif change == "hardlink":
        os.link(record, root.parent / "linked.json")
    elif change == "mode":
        record.chmod(0o644)
    elif change == "duplicate":
        # JSON duplicate keys must not decode into the canonical retained bytes.
        record.write_bytes(b'{"profile":"wrong",' + record.read_bytes()[1:])
    else:
        wire = json.loads(record.read_bytes())
        wire["metadata_inode"] += 1
        from aware_workspace_sdk.initial_authoring.values import enrollment_evidence

        wire.pop("enrollment_ref")
        wire.pop("schema_id")
        wire.pop("profile")
        from aware_workspace_sdk.initial_authoring.values import _canonical

        record.write_bytes(_canonical(enrollment_evidence(**wire).to_wire()) + b"\n")
    with pytest.raises((ValueError, OSError)):
        handle.observe()
    with pytest.raises((ValueError, OSError)):
        WorkspaceRepositoryPublicationClient.filesystem(
            repository_root=str(root)
        ).restore_initial_authoring_enrollment()
    with pytest.raises(ValueError, match="original_fresh_root_witness"):
        publication.enroll_initial_authoring(preparation)


@pytest.mark.parametrize("change", ["execution", "ambiguous", "fork"])
def test_execution_or_process_changes_refuse_inherited_handles(
    fresh, monkeypatch, change
):
    root, preparation, publication, _ = fresh
    handle = publication.enroll_initial_authoring(preparation)
    if change == "fork":
        child = os.fork()
        if child == 0:
            try:
                handle.observe()
            except ValueError:
                os._exit(0)
            os._exit(1)
        _, status = os.waitpid(child, 0)
        assert os.waitstatus_to_exitcode(status) == 0
        assert handle.observe()
    else:
        monkeypatch.setenv(
            "CODEX_THREAD_ID" if change == "execution" else "CLAUDE_CODE_SESSION_ID",
            "foreign",
        )
        with pytest.raises(ValueError):
            handle.observe()
        if change == "execution":
            other = WorkspaceRepositoryPublicationClient.filesystem(
                repository_root=str(root)
            )
            with pytest.raises(ValueError, match="execution_mismatch"):
                other.restore_initial_authoring_enrollment()


def test_failed_durability_does_not_return_handle_or_retry_original_creation(
    fresh, monkeypatch
):
    root, preparation, publication, _ = fresh
    original = os.fsync

    def fail(_fd):
        raise OSError("controlled fsync failure")

    monkeypatch.setattr(os, "fsync", fail)
    with pytest.raises(OSError):
        publication.enroll_initial_authoring(preparation)
    monkeypatch.setattr(os, "fsync", original)
    with pytest.raises((ValueError, OSError)):
        publication.restore_initial_authoring_enrollment()
    with pytest.raises(ValueError, match="original_fresh_root_witness"):
        publication.enroll_initial_authoring(preparation)
    assert not _record(root).exists()  # Partial directory is intentionally retained.


def test_enrollment_does_not_require_or_import_issue_service_or_goal(
    fresh, monkeypatch
):
    root, preparation, publication, _ = fresh
    import importlib.abc

    class Deny(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.startswith(
                ("aware_issue", "aware_goal", "aware_ontology", "aware_service")
            ):
                raise AssertionError("foreign issuer: " + fullname)

    guard = Deny()
    monkeypatch.setattr(sys, "meta_path", [guard, *sys.meta_path])
    before = len(os.listdir("/proc/self/fd"))
    handle = publication.enroll_initial_authoring(preparation)
    assert handle.observe()
    assert len(os.listdir("/proc/self/fd")) == before
    assert not (root / "docs").exists()


def test_root_replacement_refuses_preserving_original(fresh):
    root, preparation, publication, _ = fresh
    handle = publication.enroll_initial_authoring(preparation)
    original = root.parent / "original"
    root.rename(original)
    root.mkdir()
    with pytest.raises((ValueError, OSError)):
        handle.observe()
    assert _record(original).is_file()
    assert not list(root.iterdir())


def test_physical_enrollment_refuses_detached_creation_result(fresh):
    root, _, publication, result = fresh
    for claim in (None, result, result.__class__, object()):
        with pytest.raises(ValueError, match="original_initial_enrollment_claim"):
            publication._provider._physical.enroll_initial_authoring(claim)
    assert not _record(root).exists()


@pytest.mark.parametrize("point", ["file", "directory", "metadata", "root"])
def test_restart_after_complete_record_but_interrupted_durability_reuses_original(
    fresh, monkeypatch, point
):
    root, preparation, publication, _ = fresh
    original = os.fsync
    # Calls after writing the record: file, containing directory, metadata, root.
    fail_at = {"file": 2, "directory": 3, "metadata": 4, "root": 5}[point]
    count = 0

    def interrupted(fd):
        nonlocal count
        count += 1
        if count == fail_at:
            raise OSError("controlled durability interruption")
        return original(fd)

    monkeypatch.setattr(os, "fsync", interrupted)
    with pytest.raises(OSError):
        publication.enroll_initial_authoring(preparation)
    retained = _record(root).read_bytes()
    monkeypatch.setattr(os, "fsync", original)
    restored = publication.restore_initial_authoring_enrollment().observe()
    assert restored.to_wire() == json.loads(retained)
    assert _record(root).read_bytes() == retained
    with pytest.raises(ValueError, match="original_fresh_root_witness"):
        publication.enroll_initial_authoring(preparation)


def test_parallel_enrollment_spends_one_original_preparation_witness(fresh):
    from concurrent.futures import ThreadPoolExecutor

    root, preparation, publication, _ = fresh

    def invoke(_index):
        try:
            return (
                publication.enroll_initial_authoring(preparation)
                .observe()
                .enrollment_ref
            )
        except ValueError as error:
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(invoke, range(2)))
    assert (
        sum(value.startswith("workspace-initial-enrollment:") for value in results) == 1
    )
    assert results.count("original_fresh_root_witness_required") == 1
    assert _record(root).is_file()


@pytest.mark.parametrize(
    "kind", ["bool_integer", "unknown_field", "wrong_profile", "bad_ref"]
)
def test_enrollment_evidence_is_strict_but_decoding_never_issues_handle(fresh, kind):
    _, preparation, publication, _ = fresh
    wire = publication.enroll_initial_authoring(preparation).observe().to_wire()
    if kind == "bool_integer":
        wire["root_inode"] = True
    elif kind == "unknown_field":
        wire["authorized"] = True
    elif kind == "wrong_profile":
        wire["profile"] = "issue_work"
    else:
        wire["enrollment_ref"] = "workspace-initial-enrollment:sha256:" + "0" * 64
    with pytest.raises(ValueError):
        InitialAuthoringEnrollmentEvidence.from_wire(wire)


def test_retention_directory_replacement_during_read_refuses(fresh, monkeypatch):
    root, preparation, publication, _ = fresh
    handle = publication.enroll_initial_authoring(preparation)
    directory = _record(root).parent
    original = os.read
    swapped = False

    def read(fd, count):
        nonlocal swapped
        body = original(fd, count)
        if body.startswith(b'{"assurance"') and not swapped:
            swapped = True
            directory.rename(directory.parent / "retained-old-directory")
            directory.mkdir(mode=0o700)
            _record(root).write_bytes(body)
            _record(root).chmod(0o600)
        return body

    monkeypatch.setattr(os, "read", read)
    with pytest.raises(ValueError, match="retention_directory_changed"):
        handle.observe()


def test_successful_enrollment_can_be_read_with_network_and_issue_imports_unavailable(
    fresh,
):
    root, preparation, publication, _ = fresh
    original = publication.enroll_initial_authoring(preparation).observe()
    body = """
import importlib.abc, json, socket, sys
class Deny(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(('aware_issue', 'aware_goal', 'aware_ontology', 'aware_service')):
            raise AssertionError(fullname)
sys.meta_path.insert(0, Deny())
def refused(*args, **kwargs):
    raise AssertionError('network unavailable')
socket.socket = refused
from aware_workspace_sdk.repository_publication import WorkspaceRepositoryPublicationClient
client = WorkspaceRepositoryPublicationClient.filesystem(repository_root=sys.argv[1])
print(json.dumps(client.restore_initial_authoring_enrollment().observe().to_wire()))
"""
    completed = subprocess.run(
        [sys.executable, "-B", "-c", body, str(root)],
        env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert (
        InitialAuthoringEnrollmentEvidence.from_wire(json.loads(completed.stdout))
        == original
    )


def test_foreign_publisher_cannot_consume_original_roots_witness(fresh):
    root, preparation, publication, result = fresh
    second = root.parent / "second"
    other_preparation = WorkspaceRepositoryPreparationClient.filesystem(
        repository_root=str(second),
        execution_id=result.execution_id,
    )
    request = RepositoryPrepareRequest(str(second), True)
    with other_preparation.plan_repository_preparation(request) as plan:
        admission = other_preparation.admit_repository_preparation(plan)
        other_preparation.prepare_repository(request, admission=admission)
    other = WorkspaceRepositoryPublicationClient.filesystem(repository_root=str(second))
    with pytest.raises(ValueError, match="preparation_root_mismatch"):
        other.enroll_initial_authoring(preparation)
    assert publication.enroll_initial_authoring(preparation).observe()
    assert other.enroll_initial_authoring(other_preparation).observe()


def _configuration(fresh):
    from aware_protocol_fs_adapter.project_bootstrap import (
        prepare_project_configuration,
    )

    root, preparation, publication, _ = fresh
    enrollment = publication.enroll_initial_authoring(preparation)
    protocol_plan = prepare_project_configuration(
        repository_root=str(root),
        issue_root="customer/issues",
        goal_root="customer/goals",
        project_root="customer/projects",
    )
    return enrollment, protocol_plan


def _author(monkeypatch):
    for name, value in (
        ("GIT_AUTHOR_NAME", "Source canary"),
        ("GIT_COMMITTER_NAME", "Source canary"),
        ("GIT_AUTHOR_EMAIL", "canary@example.invalid"),
        ("GIT_COMMITTER_EMAIL", "canary@example.invalid"),
    ):
        monkeypatch.setenv(name, value)


def _published_configuration(fresh, monkeypatch):
    _author(monkeypatch)
    enrollment, protocol = _configuration(fresh)
    client = fresh[2]
    plan = client.plan_initial_configuration(
        enrollment, protocol, idempotency_key="project-configuration"
    )
    original = client.publish_initial_configuration(
        client.admit_initial_configuration(plan)
    )
    assert original.publication_state == "published"
    return protocol, original


def test_configuration_guarded_projection_and_genuine_protocol_admission(
    fresh, monkeypatch
):
    from aware_protocol_fs_adapter.project_resolver import (
        admit_project_resolver,
        require_project_resolver,
    )

    root, _, client, _ = fresh
    protocol, original = _published_configuration(fresh, monkeypatch)
    projected = client.project_initial_configuration(
        protocol, idempotency_key="project-configuration"
    )
    assert projected["projection_state"] == "installed", projected
    assert projected["original_result"] == original
    assert projected["projection"]["effect"]["durability_confirmed"] is True
    assert (
        client.project_initial_configuration(
            protocol, idempotency_key="project-configuration"
        )
        == projected
    )
    restored = WorkspaceRepositoryPublicationClient.filesystem(
        repository_root=str(root)
    )
    assert (
        restored.project_initial_configuration(
            protocol, idempotency_key="project-configuration"
        )
        == projected
    )
    admission = admit_project_resolver(
        repository_root=root, manifest_path=root / "aware.protocol.toml"
    )
    assert admission.capability is not None
    capability = require_project_resolver(admission.capability)
    assert capability.project_root == "customer/projects"
    assert capability.goal_capability.repository_root == root
    assert set(root.iterdir()) == {root / ".git", root / "aware.protocol.toml"}
    assert (
        subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            capture_output=True,
            check=True,
        ).stdout
        == b""
    )
    assert (
        subprocess.run(
            ["git", "-C", str(root), "rev-list", "--count", "HEAD"],
            capture_output=True,
            check=True,
        ).stdout.strip()
        == b"1"
    )


@pytest.mark.parametrize("kind", ["matching", "foreign", "symlink", "hardlink"])
def test_projection_does_not_adopt_or_replace_preexisting_target(
    fresh, monkeypatch, kind
):
    from aware_protocol_fs_adapter.project_bootstrap import (
        require_project_configuration,
    )

    root, _, client, _ = fresh
    protocol, original = _published_configuration(fresh, monkeypatch)
    target = root / "aware.protocol.toml"
    outside = root.parent / "outside"
    outside.write_bytes(b"outside-preserved")
    if kind == "symlink":
        target.symlink_to(outside)
    elif kind == "hardlink":
        os.link(outside, target)
    else:
        target.write_bytes(
            require_project_configuration(protocol).content
            if kind == "matching"
            else b"foreign"
        )
    before = target.lstat()
    response = client.project_initial_configuration(
        protocol, idempotency_key="project-configuration"
    )
    assert response["projection_state"] == "uncertain"
    assert response["original_result"] == original
    assert "foreign_target" in response["diagnostics"][0]
    assert target.lstat() == before
    assert outside.read_bytes() == b"outside-preserved"
    assert not (
        root / ".git/aware-initial-authoring-v1/configuration/projection-start.json"
    ).exists()


@pytest.mark.parametrize("fault", ["index", "head"])
def test_projection_requires_exact_current_publication_and_index(
    fresh, monkeypatch, fault
):
    root, _, client, _ = fresh
    protocol, original = _published_configuration(fresh, monkeypatch)
    if fault == "index":
        (root / ".git/index").write_bytes(b"foreign-index")
    else:
        subprocess.run(
            ["git", "-C", str(root), "symbolic-ref", "HEAD", "refs/heads/foreign"],
            check=True,
        )
    response = client.project_initial_configuration(
        protocol, idempotency_key="project-configuration"
    )
    assert response["projection_state"] == "uncertain"
    assert response["original_result"] == original
    assert not (root / "aware.protocol.toml").exists()
    assert not (
        root / ".git/aware-initial-authoring-v1/configuration/projection-start.json"
    ).exists()


@pytest.mark.parametrize("point", ["intent", "physical", "result"])
def test_projection_interruption_never_authorizes_new_attempt(
    fresh, monkeypatch, point
):
    import aware_workspace_fs_adapter.initial_authoring as owner
    from aware_file_system.retained_bootstrap import RetainedBootstrapCreation

    root, _, client, _ = fresh
    protocol, original = _published_configuration(fresh, monkeypatch)
    write = owner._write_record
    create = RetainedBootstrapCreation.create_next_file

    def fail_write(directory, name, value):
        if name == (
            "projection-start.json" if point == "intent" else "projection-result.json"
        ):
            write(directory, name, value)
            raise OSError("interrupted projection durability")
        return write(directory, name, value)

    def fail_create(handle):
        create(handle)
        raise OSError("interrupted after physical publication")

    with monkeypatch.context() as patch:
        if point == "physical":
            patch.setattr(RetainedBootstrapCreation, "create_next_file", fail_create)
        else:
            patch.setattr(owner, "_write_record", fail_write)
        response = client.project_initial_configuration(
            protocol, idempotency_key="project-configuration"
        )
    assert response["projection_state"] == "uncertain"
    assert response["original_result"] == original
    if point == "physical":
        assert response["projection_effects"][0]["state"] == "applied"
    with monkeypatch.context() as patch:
        patch.setattr(
            RetainedBootstrapCreation,
            "create_next_file",
            lambda *args: pytest.fail("must not repeat physical creation"),
        )
        restored = WorkspaceRepositoryPublicationClient.filesystem(
            repository_root=str(root)
        )
        again = restored.project_initial_configuration(
            protocol, idempotency_key="project-configuration"
        )
    assert again["projection_state"] == (
        "installed" if point == "result" else "uncertain"
    )
    assert again["original_result"] == original
    assert (root / "aware.protocol.toml").exists() == (point != "intent")


@pytest.mark.parametrize(
    "kind", ["bytes", "replacement", "symlink", "hardlink", "mode"]
)
def test_projection_restart_rejects_changed_original_file(fresh, monkeypatch, kind):
    root, _, client, _ = fresh
    protocol, original = _published_configuration(fresh, monkeypatch)
    result = client.project_initial_configuration(
        protocol, idempotency_key="project-configuration"
    )
    assert result["projection_state"] == "installed"
    target = root / "aware.protocol.toml"
    content = target.read_bytes()
    if kind == "bytes":
        target.write_bytes(b"other")
    elif kind == "mode":
        target.chmod(0o600)
    elif kind == "hardlink":
        os.link(target, root / "alias")
    else:
        replacement = root / "replacement"
        if kind == "symlink":
            replacement.symlink_to(root / "outside")
        else:
            replacement.write_bytes(content)
        replacement.replace(target)
    restored = WorkspaceRepositoryPublicationClient.filesystem(
        repository_root=str(root)
    )
    response = restored.project_initial_configuration(
        protocol, idempotency_key="project-configuration"
    )
    assert response["projection_state"] == "uncertain"
    assert response["original_result"] == original


def test_configuration_projection_genuine_restart(fresh, monkeypatch):
    root, _, client, _ = fresh
    protocol, original = _published_configuration(fresh, monkeypatch)
    result = client.project_initial_configuration(
        protocol, idempotency_key="project-configuration"
    )
    body = """
import json, sys
from aware_workspace_sdk.repository_publication import WorkspaceRepositoryPublicationClient
from aware_protocol_fs_adapter.project_bootstrap import prepare_project_configuration
client = WorkspaceRepositoryPublicationClient.filesystem(repository_root=sys.argv[1])
plan = prepare_project_configuration(repository_root=sys.argv[1], issue_root='customer/issues', goal_root='customer/goals', project_root='customer/projects')
result = client.project_initial_configuration(plan, idempotency_key='project-configuration')
print(json.dumps({'state': result['projection_state'], 'projection': result['projection'], 'commit':result['original_result'].commit_hash}))
"""
    completed = subprocess.run(
        [sys.executable, "-B", "-c", body, str(root)],
        env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "state": "installed",
        "projection": result["projection"],
        "commit": original.commit_hash,
    }


def test_projection_intent_persistence_failure_prevents_file_creation(
    fresh, monkeypatch
):
    import aware_workspace_fs_adapter.initial_authoring as owner

    root, _, client, _ = fresh
    protocol, original = _published_configuration(fresh, monkeypatch)
    write = owner._write_record

    def fail(directory, name, value):
        if name == "projection-start.json":
            raise OSError("no durable intent")
        return write(directory, name, value)

    monkeypatch.setattr(owner, "_write_record", fail)
    response = client.project_initial_configuration(
        protocol, idempotency_key="project-configuration"
    )
    assert response["projection_state"] == "uncertain"
    assert response["original_result"] == original
    assert not (root / "aware.protocol.toml").exists()


@pytest.mark.parametrize("point", ["intent", "physical", "result"])
def test_configuration_projection_hard_exit_recovery(fresh, monkeypatch, point):
    root, _, _, _ = fresh
    protocol, original = _published_configuration(fresh, monkeypatch)
    body = """
import os, sys
from aware_workspace_sdk.repository_publication import WorkspaceRepositoryPublicationClient
from aware_protocol_fs_adapter.project_bootstrap import prepare_project_configuration
from aware_file_system.retained_bootstrap import RetainedBootstrapCreation
import aware_workspace_fs_adapter.initial_authoring as owner
root, point = sys.argv[1:]
write = owner._write_record
def stop_write(directory, name, value):
    write(directory, name, value)
    if (point == 'intent' and name == 'projection-start.json') or (point == 'result' and name == 'projection-result.json'):
        os._exit(82)
owner._write_record = stop_write
create = RetainedBootstrapCreation.create_next_file
def stop_create(handle):
    create(handle)
    os._exit(82)
if point == 'physical':
    RetainedBootstrapCreation.create_next_file = stop_create
client = WorkspaceRepositoryPublicationClient.filesystem(repository_root=root)
protocol = prepare_project_configuration(repository_root=root, issue_root='customer/issues', goal_root='customer/goals', project_root='customer/projects')
client.project_initial_configuration(protocol, idempotency_key='project-configuration')
raise AssertionError('fault did not run')
"""
    completed = subprocess.run(
        [sys.executable, "-B", "-c", body, str(root), point],
        env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 82, completed.stderr
    from aware_file_system.retained_bootstrap import RetainedBootstrapCreation

    monkeypatch.setattr(
        RetainedBootstrapCreation,
        "create_next_file",
        lambda *args: pytest.fail("restart must not recreate"),
    )
    restored = WorkspaceRepositoryPublicationClient.filesystem(
        repository_root=str(root)
    )
    response = restored.project_initial_configuration(
        protocol, idempotency_key="project-configuration"
    )
    assert response["projection_state"] == (
        "installed" if point == "result" else "uncertain"
    )
    assert response["original_result"] == original
    assert response["authorizes_redispatch"] is False
    assert (root / "aware.protocol.toml").exists() == (point != "intent")


@pytest.mark.parametrize(
    "mutation", ["intent", "effect", "boolean", "reference", "unknown"]
)
def test_projection_retained_redigested_substitutions_refuse(
    fresh, monkeypatch, mutation
):
    from aware_workspace_sdk.initial_authoring.values import initial_reference

    root, _, client, _ = fresh
    protocol, original = _published_configuration(fresh, monkeypatch)
    client.project_initial_configuration(
        protocol, idempotency_key="project-configuration"
    )
    path = root / ".git/aware-initial-authoring-v1/configuration/projection-result.json"
    record = json.loads(path.read_bytes())
    if mutation == "intent":
        record["intent"]["request_ref"] = "workspace-initial-request:sha256:" + "a" * 64
    elif mutation == "effect":
        record["effect"]["durability_confirmed"] = False
    elif mutation == "boolean":
        record["file"]["stat"][3] = True
    elif mutation == "unknown":
        record["extra"] = "not allowed"
    record["projection_ref"] = initial_reference(
        "workspace-initial-configuration-projection",
        {key: value for key, value in record.items() if key != "projection_ref"},
    )
    if mutation == "reference":
        record["projection_ref"] = (
            "workspace-initial-configuration-projection:sha256:" + "b" * 64
        )
    path.write_text(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    response = client.project_initial_configuration(
        protocol, idempotency_key="project-configuration"
    )
    assert response["projection_state"] == "uncertain"
    assert response["original_result"] == original


def test_projection_terminal_head_change_during_index_check_refuses(fresh, monkeypatch):
    root, _, client, _ = fresh
    protocol, original = _published_configuration(fresh, monkeypatch)
    port = client._provider._physical
    git = port._git

    def advance(*args, **kwargs):
        value = git(*args, **kwargs)
        if args[:2] == ("ls-files", "--stage"):
            subprocess.run(
                ["git", "-C", str(root), "symbolic-ref", "HEAD", "refs/heads/foreign"],
                check=True,
            )
        return value

    monkeypatch.setattr(port, "_git", advance)
    response = client.project_initial_configuration(
        protocol, idempotency_key="project-configuration"
    )
    assert response["projection_state"] == "uncertain"
    assert response["original_result"] == original
    assert not (root / "aware.protocol.toml").exists()


def test_projection_preserves_unrelated_customer_work_and_index(fresh, monkeypatch):
    root, _, client, _ = fresh
    protocol, _ = _published_configuration(fresh, monkeypatch)
    (root / "foreign.txt").write_bytes(b"customer work")
    # Disposable customer repository, not governance of the aware-dev checkout.
    subprocess.run(["git", "-C", str(root), "add", "--", "foreign.txt"], check=True)
    before = (root / ".git/index").read_bytes()
    response = client.project_initial_configuration(
        protocol, idempotency_key="project-configuration"
    )
    assert response["projection_state"] == "installed"
    assert (root / ".git/index").read_bytes() == before
    assert (root / "foreign.txt").read_bytes() == b"customer work"


def test_projection_busy_attempt_refuses_before_effect(fresh, monkeypatch):
    root, _, client, _ = fresh
    protocol, _ = _published_configuration(fresh, monkeypatch)
    from aware_workspace_sdk.initial_authoring.values import configuration_request

    port = client._provider._physical
    evidence = port.observe_initial_authoring_enrollment(_attempt=True)
    config = port.require_initial_configuration_source(protocol)
    request = configuration_request(evidence, config, "project-configuration")
    other = WorkspaceRepositoryPublicationClient.filesystem(repository_root=str(root))
    with (
        port.initial_configuration_attempt(request),
        pytest.raises(ValueError, match="attempt_busy"),
    ):
        other.project_initial_configuration(
            protocol, idempotency_key="project-configuration"
        )
    assert not (root / "aware.protocol.toml").exists()


@pytest.mark.parametrize("substitution", ["key", "execution", "producer"])
def test_projection_requires_original_execution_request_and_producer(
    fresh, monkeypatch, substitution
):
    from aware_protocol_fs_adapter.project_bootstrap import (
        require_project_configuration,
    )

    root, _, client, _ = fresh
    protocol, _ = _published_configuration(fresh, monkeypatch)
    key = "project-configuration"
    if substitution == "key":
        key = "foreign-attempt"
    elif substitution == "execution":
        monkeypatch.setenv("CODEX_THREAD_ID", "foreign-execution")
        client = WorkspaceRepositoryPublicationClient.filesystem(
            repository_root=str(root)
        )
    else:
        protocol = require_project_configuration(protocol)
    with pytest.raises((ValueError, TypeError)):
        client.project_initial_configuration(protocol, idempotency_key=key)
    assert not (root / "aware.protocol.toml").exists()
    assert not (
        root / ".git/aware-initial-authoring-v1/configuration/projection-start.json"
    ).exists()


def test_protocol_capability_revalidation_is_not_replaced_by_projection_receipt(
    fresh, monkeypatch
):
    from aware_protocol_fs_adapter.project_resolver import (
        admit_project_resolver,
        require_project_resolver,
    )

    root, _, client, _ = fresh
    protocol, _ = _published_configuration(fresh, monkeypatch)
    projected = client.project_initial_configuration(
        protocol, idempotency_key="project-configuration"
    )
    admitted = admit_project_resolver(
        repository_root=root, manifest_path=root / "aware.protocol.toml"
    )
    assert admitted.capability is not None
    with pytest.raises(ValueError):
        require_project_resolver(projected["projection"])
    (root / "aware.protocol.toml").write_bytes(b"changed configuration")
    with pytest.raises(ValueError):
        require_project_resolver(admitted.capability)


def test_original_configuration_cas_has_no_customer_issue_and_exact_retry(
    fresh, monkeypatch
):
    root, _, publication, _ = fresh
    _author(monkeypatch)
    enrollment, protocol_plan = _configuration(fresh)
    plan = publication.plan_initial_configuration(
        enrollment, protocol_plan, idempotency_key="customer-init"
    )
    assert plan.request.to_wire()["preimage"] == "absent"
    assert not (root / ".git/aware-initial-authoring-v1/configuration").exists()
    assert not (root / "aware.protocol.toml").exists()
    admission = publication.admit_initial_configuration(plan)
    pending = root / ".git/aware-initial-authoring-v1/configuration/admission.json"
    assert pending.is_file()
    result = publication.publish_initial_configuration(admission)
    assert result.publication_state == "published", result
    assert result.reference_update == "cas_applied"
    assert result.admission_completion == "completed"
    assert result.ledger_complete
    assert result.original_writer_report.issue_tag is None
    assert publication.publish_initial_configuration(admission) == result
    recovery = publication.recover_initial_configuration(
        protocol_plan, idempotency_key="customer-init"
    )
    assert recovery["original_result"] == result
    assert recovery["disposition"] == "recorded"
    # This is repository-only publication: no unsafe post-CAS file installation.
    assert not (root / "aware.protocol.toml").exists()
    assert not (root / "customer").exists()
    body = subprocess.run(
        ["git", "-C", str(root), "show", "HEAD:aware.protocol.toml"],
        capture_output=True,
        check=True,
    ).stdout
    assert b'profile = "aware.collaboration.fs_v3"' in body
    message = subprocess.run(
        ["git", "-C", str(root), "show", "-s", "--format=%B", "HEAD"],
        capture_output=True,
        check=True,
    ).stdout
    assert b"Aware-Initial-Authoring:" in message and b"Issue-Tag:" not in message
    assert (
        subprocess.run(
            ["git", "-C", str(root), "rev-list", "--count", "HEAD"],
            capture_output=True,
            check=True,
        ).stdout.strip()
        == b"1"
    )


def test_original_workspace_binding_mutation_cannot_requalify_plan(fresh):
    from aware_workspace_sdk.initial_authoring.authority import _CONFIGURATION_STATES

    root, _, publication, _ = fresh
    enrollment, protocol = _configuration(fresh)
    plan = publication.plan_initial_configuration(
        enrollment, protocol, idempotency_key="binding-mutation"
    )
    state = _CONFIGURATION_STATES[plan]
    object.__setattr__(
        state.workspace_plan.binding, "message_digest", "sha256:" + "f" * 64
    )
    with pytest.raises(ValueError, match="plan_mutated"):
        publication.admit_initial_configuration(plan)
    assert not (root / ".git/aware-initial-authoring-v1/configuration").exists()


def test_configuration_recovery_in_new_process_uses_original_result(fresh, monkeypatch):
    root, _, publication, _ = fresh
    _author(monkeypatch)
    enrollment, protocol_plan = _configuration(fresh)
    plan = publication.plan_initial_configuration(
        enrollment, protocol_plan, idempotency_key="restart"
    )
    admission = publication.admit_initial_configuration(plan)
    original = publication.publish_initial_configuration(admission)
    body = """
import json, sys
from aware_workspace_sdk.repository_publication import WorkspaceRepositoryPublicationClient
from aware_protocol_fs_adapter.project_bootstrap import prepare_project_configuration
from aware_workspace_sdk.repository_publication.codec import repository_publication_value_to_payload
client = WorkspaceRepositoryPublicationClient.filesystem(repository_root=sys.argv[1])
plan = prepare_project_configuration(repository_root=sys.argv[1], issue_root='customer/issues', goal_root='customer/goals', project_root='customer/projects')
result = client.recover_initial_configuration(plan, idempotency_key='restart')
print(json.dumps(repository_publication_value_to_payload(result['original_result']), sort_keys=True))
"""
    completed = subprocess.run(
        [sys.executable, "-B", "-c", body, str(root)],
        env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    from aware_workspace_sdk.repository_publication.codec import (
        repository_publication_value_to_payload,
    )

    assert json.loads(completed.stdout) == repository_publication_value_to_payload(
        original
    )


def test_configuration_admission_is_distinct_from_enrollment_and_issue_work(fresh):
    root, _, publication, _ = fresh
    enrollment, protocol_plan = _configuration(fresh)
    plan = publication.plan_initial_configuration(
        enrollment, protocol_plan, idempotency_key="separate"
    )
    for fake in (enrollment, plan.request, plan.request.to_wire()):
        with pytest.raises(ValueError):
            publication.publish_initial_configuration(fake)
    admission = publication.admit_initial_configuration(plan)
    with pytest.raises(ValueError):
        publication.publish_repository_commit(plan, admission)
    assert not (root / ".git/index").exists()


def test_pending_recovery_never_dispatches_or_refreshes(fresh):
    root, _, publication, _ = fresh
    enrollment, protocol_plan = _configuration(fresh)
    plan = publication.plan_initial_configuration(
        enrollment, protocol_plan, idempotency_key="pending"
    )
    publication.admit_initial_configuration(plan)
    recovery = publication.recover_initial_configuration(
        protocol_plan, idempotency_key="pending"
    )
    assert recovery["disposition"] == "pending"
    assert recovery["original_result"] is None
    assert not (root / ".git/index").exists()
    with pytest.raises(ValueError):
        publication.recover_initial_configuration(
            protocol_plan, idempotency_key="changed"
        )


@pytest.mark.parametrize(
    "point,expected,count",
    [
        ("admitted", "pending", 0),
        ("before_begin", "uncertain", 0),
        ("after_cas", "uncertain", 1),
        ("after_result", "recorded", 1),
    ],
)
def test_hard_exit_recovery_never_republishes(
    tmp_path, monkeypatch, point, expected, count
):
    _author(monkeypatch)
    root = tmp_path / "hard-exit-customer"
    body = """
import os,sys
from aware_workspace_sdk.repository_preparation import RepositoryPrepareRequest, WorkspaceRepositoryPreparationClient
from aware_workspace_sdk.repository_publication import WorkspaceRepositoryPublicationClient
from aware_protocol_fs_adapter.project_bootstrap import prepare_project_configuration
root, point = sys.argv[1:]
preparation = WorkspaceRepositoryPreparationClient.filesystem(repository_root=root, execution_id='codex-initial-authoring-test')
request = RepositoryPrepareRequest(root, True)
with preparation.plan_repository_preparation(request) as plan:
    preparation.prepare_repository(request, admission=preparation.admit_repository_preparation(plan))
client = WorkspaceRepositoryPublicationClient.filesystem(repository_root=root)
enrollment = client.enroll_initial_authoring(preparation)
protocol = prepare_project_configuration(repository_root=root, issue_root='issues', goal_root='goals', project_root='projects')
plan = client.plan_initial_configuration(enrollment, protocol, idempotency_key='hard-exit')
admission = client.admit_initial_configuration(plan)
if point == 'admitted':
    os._exit(81)
if point == 'before_begin':
    def die(*args, **kwargs):
        os._exit(81)
    client._provider._physical.begin = die
if point == 'after_cas':
    original = client._provider._physical.publish
    def die(*args, **kwargs):
        original(*args, **kwargs)
        os._exit(81)
    client._provider._physical.publish = die
if point == 'after_result':
    from aware_workspace_fs_adapter.initial_authoring import ConfigurationAttempt
    original = ConfigurationAttempt.finish
    def die(self, result):
        original(self, result)
        os._exit(81)
    ConfigurationAttempt.finish = die
client.publish_initial_configuration(admission)
raise AssertionError('fault did not run')
"""
    completed = subprocess.run(
        [sys.executable, "-B", "-c", body, str(root), point],
        env={
            **os.environ,
            "CODEX_THREAD_ID": "initial-authoring-test",
            "CLAUDE_CODE_SESSION_ID": "",
            "PYTHONPATH": os.pathsep.join(sys.path),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 81, completed.stderr
    monkeypatch.setenv("CODEX_THREAD_ID", "initial-authoring-test")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    from aware_protocol_fs_adapter.project_bootstrap import (
        prepare_project_configuration,
    )

    client = WorkspaceRepositoryPublicationClient.filesystem(repository_root=str(root))
    protocol = prepare_project_configuration(
        repository_root=str(root),
        issue_root="issues",
        goal_root="goals",
        project_root="projects",
    )
    for _ in range(2):
        recovered = client.recover_initial_configuration(
            protocol, idempotency_key="hard-exit"
        )
        assert recovered["disposition"] == expected
        assert recovered["authorizes_redispatch"] is False
        assert (recovered["original_result"] is not None) == (point == "after_result")
    head = subprocess.run(
        ["git", "-C", str(root), "rev-list", "--count", "HEAD"],
        capture_output=True,
        check=False,
    )
    assert (int(head.stdout.strip()) if head.returncode == 0 else 0) == count
    assert not (root / "aware.protocol.toml").exists()
    assert not (root / "issues").exists()


def test_dispatch_lock_excludes_recovery_and_other_live_dispatchers(fresh, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    root, _, publication, _ = fresh
    _author(monkeypatch)
    enrollment, protocol = _configuration(fresh)
    plan = publication.plan_initial_configuration(
        enrollment, protocol, idempotency_key="serialized"
    )
    admission = publication.admit_initial_configuration(plan)
    entered, release = Event(), Event()
    original = publication._provider._physical.publish

    def paused(*args):
        entered.set()
        assert release.wait(10)
        return original(*args)

    monkeypatch.setattr(publication._provider._physical, "publish", paused)
    with ThreadPoolExecutor(max_workers=1) as executor:
        running = executor.submit(publication.publish_initial_configuration, admission)
        try:
            assert entered.wait(10)
            other = WorkspaceRepositoryPublicationClient.filesystem(
                repository_root=str(root)
            )
            with pytest.raises(ValueError, match="attempt_busy"):
                other.recover_initial_configuration(
                    protocol, idempotency_key="serialized"
                )
            with pytest.raises(ValueError, match="attempt_busy"):
                publication.publish_initial_configuration(admission)
        finally:
            release.set()
        result = running.result(timeout=10)
    assert result.publication_state == "published"


def test_dispatch_durability_failure_invokes_no_git_writer(fresh, monkeypatch):
    root, _, publication, _ = fresh
    enrollment, protocol = _configuration(fresh)
    plan = publication.plan_initial_configuration(
        enrollment, protocol, idempotency_key="failed-durability"
    )
    admission = publication.admit_initial_configuration(plan)
    original = os.fsync

    def fail(_fd):
        raise OSError("dispatch durability unavailable")

    def forbidden(*args):
        raise AssertionError("physical begin before durable dispatch")

    monkeypatch.setattr(os, "fsync", fail)
    monkeypatch.setattr(publication._provider._physical, "begin", forbidden)
    result = publication.publish_initial_configuration(admission)
    assert result.publication_state == "unknown"
    monkeypatch.setattr(os, "fsync", original)
    assert (
        publication.recover_initial_configuration(
            protocol, idempotency_key="failed-durability"
        )["disposition"]
        == "uncertain"
    )
    assert not (root / ".git/index").exists()
    with pytest.raises(ValueError, match="uncertain_no_redispatch"):
        publication.publish_initial_configuration(admission)


def test_changed_target_after_admission_refuses_without_overwriting(fresh):
    root, _, publication, _ = fresh
    enrollment, protocol = _configuration(fresh)
    plan = publication.plan_initial_configuration(
        enrollment, protocol, idempotency_key="stale-target"
    )
    admission = publication.admit_initial_configuration(plan)
    (root / "aware.protocol.toml").write_bytes(b"foreign keep\n")
    result = publication.publish_initial_configuration(admission)
    assert result.publication_state != "published"
    assert (root / "aware.protocol.toml").read_bytes() == b"foreign keep\n"
    assert not (root / ".git/index").exists()


def test_reservation_requires_original_claim_not_detached_request(fresh):
    root, _, publication, _ = fresh
    enrollment, protocol = _configuration(fresh)
    plan = publication.plan_initial_configuration(
        enrollment, protocol, idempotency_key="claim"
    )
    for fake in (plan.request, plan.request.to_wire(), enrollment):
        with pytest.raises(
            ValueError, match="original_configuration_reservation_claim"
        ):
            publication._provider._physical.reserve_initial_configuration(fake)
    assert not (root / ".git/aware-initial-authoring-v1/configuration").exists()


def test_expired_exact_admission_cannot_dispatch(fresh, monkeypatch):
    from aware_workspace_runtime import initial_authoring as runtime

    root, _, publication, _ = fresh
    enrollment, protocol = _configuration(fresh)
    plan = publication.plan_initial_configuration(
        enrollment, protocol, idempotency_key="expired"
    )
    admission = publication.admit_initial_configuration(plan)
    original = runtime.time.monotonic
    monkeypatch.setattr(runtime.time, "monotonic", lambda: original() + 301)
    with pytest.raises(ValueError, match="admission_expired"):
        publication.publish_initial_configuration(admission)
    assert not (
        root / ".git/aware-initial-authoring-v1/configuration/dispatch.json"
    ).exists()


def test_redigested_pending_binding_does_not_modify_live_admission(fresh):
    from aware_workspace_sdk.initial_authoring.values import (
        _canonical,
        initial_reference,
    )

    root, _, publication, _ = fresh
    enrollment, protocol = _configuration(fresh)
    plan = publication.plan_initial_configuration(
        enrollment, protocol, idempotency_key="tamper-pending"
    )
    admission = publication.admit_initial_configuration(plan)
    path = root / ".git/aware-initial-authoring-v1/configuration/admission.json"
    wire = json.loads(path.read_bytes())
    wire["binding"]["binding_ref"] = "workspace-plan:copied"
    body = {key: value for key, value in wire.items() if key != "admission_ref"}
    wire["admission_ref"] = initial_reference("workspace-initial-admission", body)
    path.write_bytes(_canonical(wire) + b"\n")
    with pytest.raises(ValueError, match="retained_content_changed"):
        publication.publish_initial_configuration(admission)
    assert not (path.parent / "dispatch.json").exists()


@pytest.mark.parametrize(
    "field",
    [
        "commit_hash",
        "requested_paths",
        "admission_ref",
        "request_ref",
        "lock_release",
        "publication_state",
    ],
)
def test_redigested_original_result_substitutions_refuse(fresh, monkeypatch, field):
    from aware_workspace_sdk.initial_authoring.values import (
        _canonical,
        initial_reference,
    )

    root, _, publication, _ = fresh
    _author(monkeypatch)
    enrollment, protocol = _configuration(fresh)
    plan = publication.plan_initial_configuration(
        enrollment, protocol, idempotency_key="tamper-result"
    )
    admission = publication.admit_initial_configuration(plan)
    result = publication.publish_initial_configuration(admission)
    assert result.publication_state == "published"
    path = root / ".git/aware-initial-authoring-v1/configuration/result.json"
    wire = json.loads(path.read_bytes())
    if field == "commit_hash":
        wire["original_result"]["commit_hash"] = "0" * 40
    elif field == "requested_paths":
        wire["original_result"]["original_writer_report"]["requested_paths"] = [
            "source.py"
        ]
    elif field == "lock_release":
        wire["original_result"]["lock_release"]["provider_generation"] = "substituted"
    elif field == "publication_state":
        wire["original_result"]["publication_state"] = "not_published"
    else:
        wire[field] = "substitution"
    body = {key: value for key, value in wire.items() if key != "publication_ref"}
    wire["publication_ref"] = initial_reference("workspace-initial-publication", body)
    path.write_bytes(_canonical(wire) + b"\n")
    with pytest.raises(ValueError):
        publication.recover_initial_configuration(
            protocol, idempotency_key="tamper-result"
        )


def test_foreign_target_index_refuses_cas_and_preserves_index(fresh, monkeypatch):
    root, _, publication, _ = fresh
    enrollment, protocol = _configuration(fresh)
    plan = publication.plan_initial_configuration(
        enrollment, protocol, idempotency_key="foreign-index"
    )
    admission = publication.admit_initial_configuration(plan)
    # Adversarial fixture staging, not the customer's supported publication rail.
    blob = (
        subprocess.run(
            ["git", "-C", str(root), "hash-object", "-w", "--stdin"],
            input=b"foreign",
            capture_output=True,
            check=True,
        )
        .stdout.decode()
        .strip()
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "update-index",
            "--add",
            "--cacheinfo",
            f"100644,{blob},aware.protocol.toml",
        ],
        check=True,
    )
    before = (root / ".git/index").read_bytes()
    result = publication.publish_initial_configuration(admission)
    assert result.publication_state != "published"
    assert (root / ".git/index").read_bytes() == before


def test_unrelated_customer_work_and_staging_survive_exact_configuration(
    fresh, monkeypatch
):
    root, _, publication, _ = fresh
    _author(monkeypatch)
    enrollment, protocol = _configuration(fresh)
    plan = publication.plan_initial_configuration(
        enrollment, protocol, idempotency_key="unrelated"
    )
    admission = publication.admit_initial_configuration(plan)
    (root / "foreign.txt").write_bytes(b"preserve customer work")
    subprocess.run(["git", "-C", str(root), "add", "foreign.txt"], check=True)
    before = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--stage", "--", "foreign.txt"],
        capture_output=True,
        check=True,
    ).stdout
    result = publication.publish_initial_configuration(admission)
    assert result.publication_state == "published"
    assert (root / "foreign.txt").read_bytes() == b"preserve customer work"
    assert (
        subprocess.run(
            ["git", "-C", str(root), "ls-files", "--stage", "--", "foreign.txt"],
            capture_output=True,
            check=True,
        ).stdout
        == before
    )
    assert (
        subprocess.run(
            ["git", "-C", str(root), "ls-tree", "-r", "--name-only", "HEAD"],
            capture_output=True,
            check=True,
        ).stdout.strip()
        == b"aware.protocol.toml"
    )


def test_late_retention_fence_preserves_known_publication_receipt(fresh, monkeypatch):
    from aware_workspace_fs_adapter.initial_authoring import ConfigurationAttempt

    root, _, publication, _ = fresh
    _author(monkeypatch)
    enrollment, protocol = _configuration(fresh)
    plan = publication.plan_initial_configuration(
        enrollment, protocol, idempotency_key="late-fence"
    )
    admission = publication.admit_initial_configuration(plan)
    original = ConfigurationAttempt.finish
    directory = root / ".git/aware-initial-authoring-v1/configuration"

    def substitute(self, result):
        completed = original(self, result)
        directory.rename(directory.parent / "retained-original-configuration")
        directory.mkdir(mode=0o700)
        return completed

    monkeypatch.setattr(ConfigurationAttempt, "finish", substitute)
    result = publication.publish_initial_configuration(admission)
    assert result.publication_state == "published"
    assert result.commit_hash is not None
    assert not result.ledger_complete
    assert result.admission_completion == "unknown"
    assert "initial_attempt_terminal_fence_failed" in result.diagnostics
    assert (directory.parent / "retained-original-configuration/result.json").is_file()


@pytest.mark.parametrize(
    "field,value",
    [
        ("operation_key", "create_project_context"),
        ("target_path", "source.py"),
        ("expected_head", False),
        ("selected_ref", "refs/heads/other"),
        ("preimage", "supplied"),
        ("profile", "issue_work"),
    ],
)
def test_redigested_request_cannot_broaden_exact_effect(fresh, field, value):
    from aware_workspace_sdk.initial_authoring.values import (
        InitialConfigurationRequest,
        initial_reference,
    )

    _, _, publication, _ = fresh
    enrollment, protocol = _configuration(fresh)
    plan = publication.plan_initial_configuration(
        enrollment, protocol, idempotency_key="request"
    )
    wire = plan.request.to_wire()
    wire[field] = value
    body = {key: value for key, value in wire.items() if key != "request_ref"}
    wire["request_ref"] = initial_reference("workspace-initial-request", body)
    with pytest.raises(ValueError):
        InitialConfigurationRequest.from_wire(wire)


def test_recovery_requires_fresh_durability_barriers_without_republication(
    fresh, monkeypatch
):
    root, _, publication, _ = fresh
    _author(monkeypatch)
    enrollment, protocol = _configuration(fresh)
    plan = publication.plan_initial_configuration(
        enrollment, protocol, idempotency_key="recovery-durability"
    )
    admission = publication.admit_initial_configuration(plan)
    original_result = publication.publish_initial_configuration(admission)
    original = os.fsync

    def fail(_fd):
        raise OSError("recovery durability unavailable")

    monkeypatch.setattr(os, "fsync", fail)
    with pytest.raises(OSError):
        publication.recover_initial_configuration(
            protocol, idempotency_key="recovery-durability"
        )
    monkeypatch.setattr(os, "fsync", original)
    assert (
        publication.recover_initial_configuration(
            protocol, idempotency_key="recovery-durability"
        )["original_result"]
        == original_result
    )
    assert (
        subprocess.run(
            ["git", "-C", str(root), "rev-list", "--count", "HEAD"],
            capture_output=True,
            check=True,
        ).stdout.strip()
        == b"1"
    )
