"""Real read-only capture/original owner tests; no writer qualification."""

from __future__ import annotations

import copy
import os
import pickle
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from aware_workspace_runtime.repository_publication import (
    WorkspaceRepositoryPublicationRuntime,
)
from aware_workspace_sdk.repository_publication.authority import (
    WorkspacePublicationHandleRefusal,
    WorkspaceRepositoryCommitPlan,
    WorkspaceRepositoryPublicationClient,
)
from aware_workspace_sdk.repository_publication.values import (
    WorkspaceRepositoryAttemptObserveRequest,
    WorkspaceRepositoryCommitRequest,
    WorkspaceRepositoryPlanVerificationRequest,
)


def selected_client(root, monkeypatch):
    # Source qualification explicitly selects the new, not-yet-installed port.
    # This is not a production launcher or selected operational CLI change.
    package = Path(__file__).resolve().parents[3] / "filesystem_adapter/python"
    monkeypatch.syspath_prepend(str(package))
    return WorkspaceRepositoryPublicationClient.filesystem(repository_root=root)


@pytest.fixture
def candidate(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "publication-example")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    subprocess.run(
        ("git", "init", "-q", "--initial-branch=main", str(tmp_path)), check=True
    )
    (tmp_path / "source.txt").write_text("candidate\n")
    client = selected_client(tmp_path, monkeypatch)
    request = WorkspaceRepositoryCommitRequest(
        str(tmp_path), ("source.txt",), "Approved candidate", "attempt:1"
    )
    return tmp_path, client, request


def attempt(plan):
    b = plan.binding
    return WorkspaceRepositoryAttemptObserveRequest(
        b.repository_ref,
        b.binding_ref,
        b.attempt_ref,
        b.provider_ref,
        b.provider_generation,
        b.execution_id,
    )


def test_real_capture_is_original_and_receipt_free(candidate, monkeypatch):
    root, client, request = candidate
    before = (root / ".git/HEAD").read_bytes()
    plan = client.plan_repository_commit(request)
    assert plan.phase == "planned"
    assert plan.binding.expected_head is None
    assert plan.binding.publication_reference == "refs/heads/main"
    assert (root / ".git/HEAD").read_bytes() == before
    assert not (root / ".git/index").exists()

    def forbidden(*args, **kwargs):
        raise AssertionError("Verification must not touch repository IO")

    monkeypatch.setattr(client._provider._physical, "capture_candidate", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    assert client.verify_repository_plan(
        WorkspaceRepositoryPlanVerificationRequest(plan.binding)
    ).original_plan_recognized
    observed = client.observe_repository_attempt(attempt(plan))
    assert observed.attempt_recognized and observed.result is None
    assert observed.lock_release is None


@pytest.mark.parametrize(
    "field",
    [
        "binding_ref",
        "attempt_ref",
        "repository_ref",
        "publication_reference",
        "expected_head",
        "target_paths",
        "postimages_digest",
        "message_digest",
        "provider_ref",
        "provider_generation",
        "execution_id",
    ],
)
def test_detached_correlations_cannot_forge_plan(candidate, field):
    _, client, request = candidate
    plan = client.plan_repository_commit(request)
    changed = (
        ("other.txt",)
        if field == "target_paths"
        else "sha256:" + "0" * 64
        if field.endswith("digest")
        else "other"
    )
    altered = replace(plan.binding, **{field: changed})
    observed = client._provider.verify_repository_plan(
        WorkspaceRepositoryPlanVerificationRequest(altered)
    )
    assert not observed.original_plan_recognized


@pytest.mark.parametrize("operation", [copy.copy, copy.deepcopy, pickle.dumps])
def test_handles_cannot_be_copied(candidate, operation):
    _, client, request = candidate
    plan = client.plan_repository_commit(request)
    with pytest.raises(TypeError):
        operation(plan)


def test_unissued_foreign_replayed_and_released_handles_refuse(candidate, monkeypatch):
    root, client, request = candidate
    plan = client.plan_repository_commit(request)
    with pytest.raises(TypeError):
        WorkspaceRepositoryCommitPlan()
    with pytest.raises(WorkspacePublicationHandleRefusal):
        client.release_repository_plan(object.__new__(WorkspaceRepositoryCommitPlan))
    foreign = selected_client(root, monkeypatch)
    with pytest.raises(WorkspacePublicationHandleRefusal):
        foreign.release_repository_plan(plan)
    with pytest.raises(WorkspacePublicationHandleRefusal, match="already_recorded"):
        client.plan_repository_commit(request)
    observed_request = attempt(plan)
    first = client.release_repository_plan(plan)
    assert first.cleanup_state == "completed"
    assert client.release_repository_plan(plan).cleanup_state == "completed"
    assert not client.verify_repository_plan(
        WorkspaceRepositoryPlanVerificationRequest(plan.binding)
    ).original_plan_recognized
    assert (
        client.observe_repository_attempt(
            observed_request
        ).plan_observation.resource_ownership
        == "released"
    )


@pytest.mark.parametrize(
    "bad", ["../escape", "/absolute", "a//b", "a/./b", "a\\b", "e\u0301", "a\u0080b"]
)
def test_public_candidate_port_refuses_noncanonical_paths(candidate, bad):
    _, client, request = candidate
    with pytest.raises(ValueError):
        client._provider._physical.capture_candidate(
            replace(request, target_paths=(bad,))
        )


@pytest.mark.parametrize("kind", ["fifo", "symlink", "directory", "hardlink"])
def test_nonregular_capture_refuses_without_index_effects(candidate, kind):
    root, client, request = candidate
    path = root / "source.txt"
    path.unlink()
    if kind == "fifo":
        os.mkfifo(path)
    elif kind == "symlink":
        path.symlink_to(root / "outside")
    elif kind == "directory":
        path.mkdir()
    else:
        (root / "other").write_bytes(b"linked")
        os.link(root / "other", path)
    with pytest.raises((ValueError, OSError)):
        client.plan_repository_commit(request)
    assert not (root / ".git/index").exists()


@pytest.mark.parametrize("kind", ["missing", "ambiguous", "changed", "fork"])
def test_execution_and_process_entrances_refuse(candidate, monkeypatch, kind):
    _, client, request = candidate
    plan = client.plan_repository_commit(request)
    if kind == "missing":
        monkeypatch.delenv("CODEX_THREAD_ID")
    elif kind == "ambiguous":
        monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "another")
    elif kind == "changed":
        monkeypatch.setenv("CODEX_THREAD_ID", "changed")
    else:
        client._provider._pid += 1
    with pytest.raises(WorkspacePublicationHandleRefusal):
        client.verify_repository_plan(
            WorkspaceRepositoryPlanVerificationRequest(plan.binding)
        )


def test_callback_provider_is_not_selected(candidate):
    _, _, _request = candidate
    with pytest.raises(TypeError):
        WorkspaceRepositoryPublicationRuntime(object())
    with pytest.raises(TypeError):
        WorkspaceRepositoryPublicationClient(object())


def test_real_capture_restores_descriptors_and_changed_postimages_bind_differently(
    candidate,
):
    root, client, request = candidate
    before = len(os.listdir("/proc/self/fd"))
    first = client.plan_repository_commit(request)
    (root / "source.txt").write_bytes(b"different approved candidate\n")
    second = client.plan_repository_commit(replace(request, attempt_ref="attempt:2"))
    assert first.binding.postimages_digest != second.binding.postimages_digest
    assert first.binding.message_digest == second.binding.message_digest
    assert len(os.listdir("/proc/self/fd")) == before


def test_real_fork_refuses_parent_plan_without_retiring_original(candidate):
    _, client, request = candidate
    plan = client.plan_repository_commit(request)
    pid = os.fork()
    if pid == 0:
        try:
            client.release_repository_plan(plan)
        except WorkspacePublicationHandleRefusal:
            os._exit(0)
        except BaseException:  # noqa: BLE001 - child must report failures to the parent
            os._exit(2)
        os._exit(3)
    _, status = os.waitpid(pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
    assert plan.phase == "planned"


def test_successor_facades_are_lazy_and_handles_are_not_descriptive_roots():
    script = """
import sys
import aware_workspace_sdk.repository_publication as workspace
import aware_issue_sdk.repository_publication as issue
from aware_workspace_sdk.repository_publication import values, ports, codec
assert len(values.PUBLICATION_VALUE_TYPES + ports.PUBLICATION_PORT_VALUE_TYPES) == 19
assert len(issue._VALUE_TYPES) == 12
for api in (workspace, issue):
    assert len(api.__all__) == len(set(api.__all__))
    assert all(hasattr(api, name) for name in api.__all__)
for api, names in ((workspace, ('WorkspaceRepositoryCommitPlan',)),
                   (issue, ('IssueRepositoryPublicationAdmission', 'IssueRepositoryPublicationLease'))):
    for name in names:
        handle = getattr(api, name)
        try:
            handle()
        except TypeError:
            pass
        else:
            raise AssertionError('Public construction restored authority')
        try:
            api.repository_publication_value_from_payload(handle, {})
        except ValueError:
            pass
        else:
            raise AssertionError('Decoding restored authority')
for name in ('aware_workspace_runtime', 'aware_workspace_operator', 'aware_issue_runtime',
             'aware_issue_operational_runtime', 'aware_issue_fs_adapter', 'aware_orm',
             'aware_workspace_service_api', 'aware_workspace_service_dto', 'pydantic'):
    assert not any(item == name or item.startswith(name + '.') for item in sys.modules), name
"""
    result = subprocess.run(
        (sys.executable, "-c", script), capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "owner,entries,digest",
    [
        (
            "workspace",
            273,
            "8cd52313bea8cfd5d49a4ec308f03ed2cb14cedc87ff81786283adbeda4bc674",
        ),
        (
            "issue",
            234,
            "3f0206e535f16ef476a9b9b4f8d18c8cebf52ee7fb9d15c0ebf57980c1c247d3",
        ),
    ],
)
def test_successor_preserves_accepted_authored_meaning_and_value_roots(
    owner, entries, digest
):
    from aware_issue_sdk import repository_publication as issue
    from aware_workspace_sdk.repository_publication import ports, values
    from test_workspace_publication_port_codec import lower

    meaning = lower(owner)
    assert len(meaning.entries) == entries
    assert meaning.canonical_sha256 == digest
    records = (
        values.PUBLICATION_VALUE_TYPES + ports.PUBLICATION_PORT_VALUE_TYPES
        if owner == "workspace"
        else issue._VALUE_TYPES
    )
    assert len(records) == (19 if owner == "workspace" else 12)
    symbols = {entry.fqn for entry in meaning.entries if entry.kind == "symbol"}
    assert all(f"aware_{owner}_sdk.{record.__name__}" in symbols for record in records)
