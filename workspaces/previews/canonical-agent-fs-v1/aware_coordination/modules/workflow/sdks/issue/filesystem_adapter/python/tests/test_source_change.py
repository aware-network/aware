from __future__ import annotations

import copy
import hashlib
import os
import pickle
import stat
from dataclasses import replace

import aware_file_system.retained_mutation as physical
import aware_issue_fs_adapter.source_change as issuer
import pytest
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_sdk import (
    IssueSourceChangeClient,
    IssueSourceChangeRefusal,
    IssueSourceChangeRequest,
)
from test_provider import ISSUE_REF, _repository


def digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "source-test-session")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    repository = _repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    text = issue.read_text().replace("codex-example", "codex-source-test-session")
    start = text.index("## Ownership Scope")
    end = text.index("\n## ", start + 3)
    text = (
        text[:start]
        + "## Ownership Scope\n- `aware.protocol.toml`\n- `docs/public`\n"
        + text[end:]
    )
    issue.write_text(text)
    manifest = repository / "aware.protocol.toml"
    candidate = manifest.read_bytes() + b"\n# approved source candidate\n"
    request = IssueSourceChangeRequest(
        issue_ref=ISSUE_REF,
        expected_issue_sha256=digest(issue.read_bytes()),
        manifest_locator="aware.protocol.toml",
        expected_manifest_sha256=digest(manifest.read_bytes()),
        candidate=candidate,
        directory_paths=("docs/public", "docs/public/specs"),
        client_intent_id="test-setup-1",
    )
    provider = FilesystemIssueOperationProvider(repository_root=repository)
    return repository, issue, manifest, request, provider


def complete(handle):
    handle.prepare_next_directory()
    handle.prepare_next_directory()
    handle.replace_manifest()
    return handle.finish()


def test_real_issue_issuer_and_actual_physical_consumer_are_single_use(setup):
    _repository, issue, manifest, request, provider = setup
    issue_before = issue.read_bytes()
    handle = IssueSourceChangeClient(provider).admit(request)
    receipt = complete(handle)
    assert handle.phase == "consumed"
    assert manifest.read_bytes() == request.candidate
    assert issue.read_bytes() == issue_before
    assert receipt.execution_ref == "codex-source-test-session"
    assert receipt.authority_grade == "filesystem_harness_observed_v1"
    assert receipt.ordered_effect_paths == (
        *request.directory_paths,
        "aware.protocol.toml",
    )
    assert receipt.manifest_postimage_sha256 == digest(request.candidate)
    assert [effect.state for effect in receipt.effects] == ["applied"] * 3
    assert receipt.effects[-1].after_identity == (
        manifest.stat().st_dev,
        manifest.stat().st_ino,
    )
    for operation in (
        "validate_current",
        "prepare_next_directory",
        "replace_manifest",
        "finish",
    ):
        with pytest.raises(IssueSourceChangeRefusal, match="terminal"):
            getattr(handle, operation)()
    with pytest.raises(IssueSourceChangeRefusal, match="not_issued"):
        issuer._issued(receipt)


def test_absolute_manifest_coordinate_resolves_to_same_admitted_source(setup):
    _, _, manifest, request, provider = setup
    handle = provider.admit_source_change(
        replace(request, manifest_locator=str(manifest))
    )
    complete(handle)


@pytest.mark.parametrize(
    "failure",
    [
        "owner",
        "status",
        "scope",
        "issue_digest",
        "manifest_digest",
        "locator",
        "ancestor",
    ],
)
def test_issuance_refuses_without_source_effects(setup, failure):
    repository, issue, manifest, request, provider = setup
    if failure == "owner":
        issue.write_text(
            issue.read_text().replace("codex-source-test-session", "codex-foreign")
        )
    elif failure == "status":
        issue.write_text(issue.read_text().replace("In Progress", "Closed"))
    elif failure == "scope":
        issue.write_text(issue.read_text().replace("- `docs/public`", "- `unrelated`"))
    if failure in {"owner", "status", "scope"}:
        request = replace(request, expected_issue_sha256=digest(issue.read_bytes()))
    elif failure == "issue_digest":
        request = replace(request, expected_issue_sha256="sha256:" + "0" * 64)
    elif failure == "manifest_digest":
        request = replace(request, expected_manifest_sha256="sha256:" + "0" * 64)
    elif failure == "locator":
        request = replace(request, manifest_locator="other.toml")
    elif failure == "ancestor":
        request = replace(request, directory_paths=("docs/public/specs",))
    before = manifest.read_bytes()
    with pytest.raises(IssueSourceChangeRefusal):
        provider.admit_source_change(request)
    assert manifest.read_bytes() == before
    assert not (repository / "docs/public").exists()


@pytest.mark.parametrize("operation", [copy.copy, copy.deepcopy, pickle.dumps])
def test_admission_cannot_be_copied_or_serialized(setup, operation):
    *_, request, provider = setup
    handle = provider.admit_source_change(request)
    with pytest.raises(TypeError):
        operation(handle)
    handle.release()


def test_forged_admission_and_structural_request_are_not_permits(setup):
    *_, request, _ = setup
    with pytest.raises(TypeError):
        issuer.FilesystemIssueSourceChangeAdmission()
    forged = object.__new__(issuer.FilesystemIssueSourceChangeAdmission)
    with pytest.raises(IssueSourceChangeRefusal, match="not_issued"):
        forged.replace_manifest()
    with pytest.raises(IssueSourceChangeRefusal, match="not_issued"):
        issuer._issued(request)


@pytest.mark.parametrize(
    "operation",
    ["validate_current", "prepare_next_directory", "replace_manifest", "finish"],
)
def test_issue_changes_retire_each_public_entrance_and_preserve_effects(
    setup, operation
):
    repository, issue, _manifest, request, provider = setup
    handle = provider.admit_source_change(request)
    handle.prepare_next_directory()
    if operation == "finish":
        handle.prepare_next_directory()
        handle.replace_manifest()
    prior = handle.effects
    issue.write_text(issue.read_text() + "\nChanged authority\n")
    with pytest.raises(IssueSourceChangeRefusal) as failure:
        getattr(handle, operation)()
    assert handle.phase == "retired"
    assert failure.value.effects == prior
    assert (repository / "docs/public").exists()
    for replay in (
        "validate_current",
        "prepare_next_directory",
        "replace_manifest",
        "finish",
    ):
        with pytest.raises(IssueSourceChangeRefusal, match="terminal"):
            getattr(handle, replay)()


@pytest.mark.parametrize(
    "operation",
    [
        "admit_source_change",
        "validate_current",
        "prepare_next_directory",
        "replace_manifest",
        "finish",
    ],
)
@pytest.mark.parametrize("substitution", [False, True])
def test_fifo_issue_refuses_without_blocking_or_descriptor_leaks(
    setup, monkeypatch, operation, substitution
):
    repository, issue, manifest, request, provider = setup
    handle = None
    active = set()
    if operation != "admit_source_change":
        handle = provider.admit_source_change(request)
        handle.prepare_next_directory()
        if operation in {"replace_manifest", "finish"}:
            handle.prepare_next_directory()
        if operation == "finish":
            handle.replace_manifest()
        active.add(physical._issued(issuer._issued(handle).physical).root_fd)
    prior = handle.effects if handle is not None else ()
    manifest_before = manifest.read_bytes()
    directories_before = tuple(
        (repository / p).exists() for p in request.directory_paths
    )
    original_open, original_dup, original_close = os.open, os.dup, os.close
    leaf_opens = []

    def opened(path, flags, *args, **kwargs):
        if path == issue.name:
            leaf_opens.append(flags)
            # Fail rather than hang if a regression reintroduces blocking open.
            assert flags & os.O_NONBLOCK
            if substitution:
                issue.unlink()
                os.mkfifo(issue)
        descriptor = original_open(path, flags, *args, **kwargs)
        active.add(descriptor)
        return descriptor

    def duplicated(descriptor):
        result = original_dup(descriptor)
        active.add(result)
        return result

    def closed(descriptor):
        original_close(descriptor)
        active.discard(descriptor)

    if not substitution:
        issue.unlink()
        os.mkfifo(issue)
    monkeypatch.setattr(os, "open", opened)
    monkeypatch.setattr(os, "dup", duplicated)
    monkeypatch.setattr(os, "close", closed)
    with pytest.raises(
        IssueSourceChangeRefusal, match="issue_regular_bounded_authority_required"
    ) as failure:
        if handle is None:
            provider.admit_source_change(request)
        else:
            getattr(handle, operation)()
    assert stat.S_ISFIFO(issue.stat().st_mode)
    assert bool(leaf_opens) is substitution
    assert active == set()
    assert failure.value.effects == prior
    assert manifest.read_bytes() == manifest_before
    assert (
        tuple((repository / p).exists() for p in request.directory_paths)
        == directories_before
    )
    if handle is not None:
        assert handle.phase == "retired"
        with pytest.raises(IssueSourceChangeRefusal):
            handle.validate_current()


@pytest.mark.parametrize("failure_kind", ["missing", "denied_open", "denied_read"])
def test_initial_issue_io_failures_are_typed_and_effect_free(
    setup, monkeypatch, failure_kind
):
    repository, issue, manifest, request, provider = setup
    before = manifest.read_bytes()
    issue_inode = issue.stat().st_ino
    active = set()
    original_open, original_read, original_close = os.open, os.read, os.close

    def opened(path, flags, *args, **kwargs):
        if path == issue.name and failure_kind == "denied_open":
            raise PermissionError("Issue open denied")
        descriptor = original_open(path, flags, *args, **kwargs)
        active.add(descriptor)
        return descriptor

    def read(descriptor, size):
        if failure_kind == "denied_read" and os.fstat(descriptor).st_ino == issue_inode:
            raise PermissionError("Issue read denied")
        return original_read(descriptor, size)

    def closed(descriptor):
        original_close(descriptor)
        active.discard(descriptor)

    def unexpected_physical(**kwargs):
        pytest.fail("Initial Issue refusal must precede physical admission")

    if failure_kind == "missing":
        issue.unlink()
    monkeypatch.setattr(os, "open", opened)
    monkeypatch.setattr(os, "read", read)
    monkeypatch.setattr(os, "close", closed)
    monkeypatch.setattr(
        issuer, "retain_confined_manifest_replacement", unexpected_physical
    )
    with pytest.raises(
        IssueSourceChangeRefusal, match="source_admission_failed"
    ) as failure:
        provider.admit_source_change(request)
    expected = FileNotFoundError if failure_kind == "missing" else PermissionError
    assert isinstance(failure.value.__cause__, expected)
    assert failure.value.effects == () and active == set()
    assert manifest.read_bytes() == before
    assert not (repository / "docs/public").exists()


def test_issue_regular_leaf_substitution_during_open_refuses(setup, monkeypatch):
    repository, issue, manifest, request, provider = setup
    before = manifest.read_bytes()
    body = issue.read_bytes()
    replacement = issue.with_suffix(".replacement")
    replacement.write_bytes(body)
    original_open = os.open

    def opened(path, flags, *args, **kwargs):
        if path == issue.name:
            replacement.replace(issue)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", opened)
    with pytest.raises(IssueSourceChangeRefusal, match="issue_changed_during_open"):
        provider.admit_source_change(request)
    assert manifest.read_bytes() == before
    assert not (repository / "docs/public").exists()


def test_invalid_admission_requests_preserve_request_error_boundary(setup):
    _, _, _, request, provider = setup
    with pytest.raises(TypeError):
        provider.admit_source_change(object())
    object.__setattr__(request, "candidate", "not bytes")
    with pytest.raises((TypeError, ValueError)):
        provider.admit_source_change(request)


@pytest.mark.parametrize(
    "operation",
    ["validate_current", "prepare_next_directory", "replace_manifest", "finish"],
)
def test_issue_read_interruption_retires_and_closes_original_physical_root(
    setup, monkeypatch, operation
):
    *_, request, provider = setup
    handle = provider.admit_source_change(request)
    handle.prepare_next_directory()
    if operation == "finish":
        handle.prepare_next_directory()
        handle.replace_manifest()
    state = issuer._issued(handle)
    physical_state = physical._issued(state.physical)
    descriptor = physical_state.root_fd
    prior = handle.effects

    def interrupt(*args):
        raise KeyboardInterrupt("Issue read interrupted")

    monkeypatch.setattr(issuer, "_read_issue", interrupt)
    with pytest.raises(IssueSourceChangeRefusal) as failure:
        getattr(handle, operation)()
    assert handle.phase == "retired" and physical_state.root_fd is None
    assert failure.value.effects == prior
    with pytest.raises(OSError):
        os.fstat(descriptor)
    with pytest.raises(IssueSourceChangeRefusal, match="terminal"):
        handle.validate_current()


def test_issue_equal_byte_substitution_and_restoration_cannot_revive_admission(setup):
    _, issue, _, request, provider = setup
    handle = provider.admit_source_change(request)
    original = issue.read_bytes()
    replacement = issue.with_suffix(".replacement")
    replacement.write_bytes(original)
    replacement.replace(issue)
    with pytest.raises(IssueSourceChangeRefusal, match="identity_changed"):
        handle.validate_current()
    issue.write_bytes(original)
    with pytest.raises(IssueSourceChangeRefusal, match="terminal"):
        handle.replace_manifest()


def test_original_provider_binding_cannot_be_substituted(setup):
    *_, request, provider = setup
    handle = provider.admit_source_change(request)
    provider._protocol_source_ref = "foreign.toml"
    with pytest.raises(
        IssueSourceChangeRefusal, match="original_issue_provider_changed"
    ):
        handle.replace_manifest()


def test_public_owner_port_refuses_foreign_provider_and_structural_permit(setup):
    repository, _, _, request, provider = setup
    client = IssueSourceChangeClient(provider)
    handle = client.admit(request)
    client.validate(handle)
    with pytest.raises(IssueSourceChangeRefusal, match="not_issued"):
        client.validate(request)
    foreign = FilesystemIssueOperationProvider(repository_root=repository)
    with pytest.raises(IssueSourceChangeRefusal, match="foreign_issue_provider"):
        foreign.validate_source_change(handle)
    assert handle.phase == "retired"


def test_execution_is_observed_not_supplied_and_ambiguity_refuses(setup, monkeypatch):
    *_, request, provider = setup
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "other-session")
    with pytest.raises(IssueSourceChangeRefusal, match="identity_unavailable"):
        provider.admit_source_change(request)


def test_foreign_process_and_released_admissions_refuse(setup, monkeypatch):
    *_, request, provider = setup
    handle = provider.admit_source_change(request)
    actual_pid = os.getpid()
    with monkeypatch.context() as process:
        process.setattr(os, "getpid", lambda: actual_pid + 1)
        with pytest.raises(IssueSourceChangeRefusal, match="foreign_process"):
            handle.replace_manifest()
    assert handle.phase == "retired"
    released = provider.admit_source_change(request)
    released.release()
    with pytest.raises(IssueSourceChangeRefusal, match="terminal"):
        released.validate_current()


def test_issue_changes_at_actual_replace_leave_applied_effect_but_no_success(
    setup, monkeypatch
):
    _, issue, manifest, request, provider = setup
    handle = provider.admit_source_change(request)
    handle.prepare_next_directory()
    handle.prepare_next_directory()
    original = os.replace

    def replace_then_change_issue(*args, **kwargs):
        result = original(*args, **kwargs)
        issue.write_text(issue.read_text() + "\nChanged during write\n")
        return result

    monkeypatch.setattr(os, "replace", replace_then_change_issue)
    with pytest.raises(IssueSourceChangeRefusal) as failure:
        handle.replace_manifest()
    assert handle.phase == "retired"
    assert manifest.read_bytes() == request.candidate
    assert failure.value.effects[-1].state == "applied"


def test_candidate_is_pinned_independently_of_callers_request_object(setup):
    _, _, manifest, request, provider = setup
    original_candidate = request.candidate
    handle = provider.admit_source_change(request)
    object.__setattr__(request, "candidate", b"substituted")
    complete(handle)
    assert manifest.read_bytes() == original_candidate


def test_issue_change_after_physical_consumption_refuses_receipt(setup, monkeypatch):
    _, issue, manifest, request, provider = setup
    handle = provider.admit_source_change(request)
    handle.prepare_next_directory()
    handle.prepare_next_directory()
    handle.replace_manifest()
    original = physical.RetainedPhysicalMutation.finish

    def finish_then_change(current):
        result = original(current)
        issue.write_text(issue.read_text() + "\nChanged at completion\n")
        return result

    monkeypatch.setattr(physical.RetainedPhysicalMutation, "finish", finish_then_change)
    with pytest.raises(IssueSourceChangeRefusal) as failure:
        handle.finish()
    assert handle.phase == "retired" and failure.value.effects[-1].state == "applied"
    assert manifest.read_bytes() == request.candidate


def test_post_consumption_source_substitution_at_final_issue_read_refuses(
    setup, monkeypatch
):
    repository, _, manifest, request, provider = setup
    handle = provider.admit_source_change(request)
    handle.prepare_next_directory()
    handle.prepare_next_directory()
    handle.replace_manifest()
    original_read = issuer._read_issue
    original_finish = physical.RetainedPhysicalMutation.finish
    consumed = False

    def mark_finished(current):
        nonlocal consumed
        result = original_finish(current)
        consumed = True
        return result

    def read_then_substitute(*args):
        result = original_read(*args)
        if consumed:
            substitute = repository / "substitute.toml"
            substitute.write_bytes(request.candidate)
            substitute.replace(manifest)
        return result

    monkeypatch.setattr(physical.RetainedPhysicalMutation, "finish", mark_finished)
    monkeypatch.setattr(issuer, "_read_issue", read_then_substitute)
    with pytest.raises(
        IssueSourceChangeRefusal, match="identity_or_bytes_changed"
    ) as failure:
        handle.finish()
    assert handle.phase == "retired" and failure.value.effects[-1].state == "applied"


@pytest.mark.parametrize(
    "operation",
    ["validate_current", "prepare_next_directory", "replace_manifest", "finish"],
)
def test_actual_issue_file_read_interruption_closes_every_descriptor(
    setup, monkeypatch, operation
):
    _, issue, _, request, provider = setup
    handle = provider.admit_source_change(request)
    handle.prepare_next_directory()
    if operation == "finish":
        handle.prepare_next_directory()
        handle.replace_manifest()
    physical_state = physical._issued(issuer._issued(handle).physical)
    active = {physical_state.root_fd}
    original_open, original_dup, original_close, original_read = (
        os.open,
        os.dup,
        os.close,
        os.read,
    )
    issue_inode = issue.stat().st_ino
    prior = handle.effects

    def opened(*args, **kwargs):
        fd = original_open(*args, **kwargs)
        active.add(fd)
        return fd

    def duplicated(fd):
        result = original_dup(fd)
        active.add(result)
        return result

    def closed(fd):
        original_close(fd)
        active.discard(fd)

    def interrupted_read(fd, size):
        if os.fstat(fd).st_ino == issue_inode:
            raise KeyboardInterrupt("actual Issue read")
        return original_read(fd, size)

    monkeypatch.setattr(os, "open", opened)
    monkeypatch.setattr(os, "dup", duplicated)
    monkeypatch.setattr(os, "close", closed)
    monkeypatch.setattr(os, "read", interrupted_read)
    with pytest.raises(IssueSourceChangeRefusal) as failure:
        getattr(handle, operation)()
    assert handle.phase == "retired" and active == set()
    assert failure.value.effects == prior


def test_noop_preserves_manifest_identity_and_existing_directory_modes(setup):
    repository, _, manifest, request, provider = setup
    (repository / "docs/public/specs").mkdir(parents=True, mode=0o755)
    inode = manifest.stat().st_ino
    request = replace(request, candidate=manifest.read_bytes())
    receipt = complete(provider.admit_source_change(request))
    assert manifest.stat().st_ino == inode
    assert all(effect.state == "none" for effect in receipt.effects)
    assert (repository / "docs/public/specs").stat().st_mode & 0o777 == 0o755


def test_issue_descriptor_cleanup_fault_attempts_all_cleanup_and_retires(
    setup, monkeypatch
):
    _, issue, _, request, provider = setup
    handle = provider.admit_source_change(request)
    handle.prepare_next_directory()
    prior = handle.effects
    active = {physical._issued(issuer._issued(handle).physical).root_fd}
    issue_inode = issue.stat().st_ino
    original_open, original_dup, original_close = os.open, os.dup, os.close

    def opened(*args, **kwargs):
        descriptor = original_open(*args, **kwargs)
        active.add(descriptor)
        return descriptor

    def duplicated(descriptor):
        result = original_dup(descriptor)
        active.add(result)
        return result

    def close_then_fail(descriptor):
        is_issue = os.fstat(descriptor).st_ino == issue_inode
        original_close(descriptor)
        active.discard(descriptor)
        if is_issue:
            raise OSError("Issue close completion unavailable")

    monkeypatch.setattr(os, "open", opened)
    monkeypatch.setattr(os, "dup", duplicated)
    monkeypatch.setattr(os, "close", close_then_fail)
    with pytest.raises(
        IssueSourceChangeRefusal, match="descriptor_cleanup_failed"
    ) as failure:
        handle.validate_current()
    assert handle.phase == "retired" and active == set()
    assert failure.value.effects == prior
