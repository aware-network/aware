"""Genuine private retention, Issue scope and original Workspace apply joins."""

from __future__ import annotations

import dataclasses
import gc
import os
import threading
import weakref
from pathlib import Path

import pytest
from aware_issue_fs_adapter.provider import FilesystemIssueOperationProvider
from aware_issue_sdk.operation import IssueSdkOperationClient
from aware_workspace_sdk import architecture_setup_review_values as v
from aware_workspace_sdk.architecture_setup import ArchitectureSetupRequest
from aware_workspace_sdk.architecture_setup_review import (
    WorkspaceSetupReviewClient,
    concise_result,
)
from aware_workspace_sdk.architecture_setup_review_codec import review_value_to_payload

REPOSITORY = Path(__file__).resolve().parents[8]
ISSUE = "docs/issues/2026/10/16/fb-2026-10-16-review-proof.md"
TAG = "fb/2026-10-16/review-proof"
EXECUTION = "codex-review-joined-proof"


@pytest.fixture
def context(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "review-joined-proof")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / ISSUE).parent.mkdir(parents=True)
    (repository / "docs/goals").mkdir(parents=True)
    (repository / "AGENTS.md").write_text("# Disposable original-owner proof\n")
    # Use the selected real declaration; this fixture does not invent a policy.
    source = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "aware.protocol.toml").is_file()
    )
    (repository / "aware.protocol.toml").write_bytes(
        (source / "aware.protocol.toml").read_bytes()
    )
    (repository / ISSUE).write_text(
        "# Issue: review proof\n\n- Slug: review-proof\n- Tag: "
        + TAG
        + "\n- Status: In Progress\n- Owner: "
        + EXECUTION
        + "\n- Priority: P1\n- Captured: 2026-10-16\n- Recorder: "
        + EXECUTION
        + "\n- Source: disposable proof\n\n## Ownership Scope\n- `keep-original`\n"
    )
    evidence = tmp_path / "evidence"
    evidence.mkdir(mode=0o700)
    client = WorkspaceSetupReviewClient.filesystem(
        repository_root=repository,
        evidence_root=evidence,
        execution_id=EXECUTION,
        authority_manifest_locator="aware.protocol.toml",
    )
    request = v.SetupReviewRequest(
        v.SetupTarget(str(repository), TAG, ISSUE, "aware.protocol.toml"),
        ArchitectureSetupRequest(
            "repository", name="example", license_expression="MIT"
        ),
        EXECUTION,
        "intent:preview-first",
        EXECUTION,
        "evidence:declared",
        True,
    )
    issuer = IssueSdkOperationClient(
        FilesystemIssueOperationProvider(repository_root=repository)
    )
    try:
        yield repository, evidence, client, request, issuer
    finally:
        client.release_client()


def test_genuine_two_review_workflow(context):
    repository, evidence, client, request, issuer = context
    first = client.preview_review(request)
    assert first.record.ready_for_decision
    assert concise_result(first).decision_required == "scope_review"
    assert concise_result(first).retention_status == "captured"
    assert not (repository / "aware.repo.toml").exists()
    scope = client.record_review_decision(
        first.reference,
        decision=v.SetupScopeDecision(
            first.reference, "accept_reviewed_effect_scope", EXECUTION, "intent:scope"
        ),
    )
    assert "keep-original" in scope.record.scope_paths
    assert set(first.record.physical_scope) <= set(scope.record.scope_paths)
    assert (evidence / scope.intent_ref.locator).is_file()
    actual = issuer.bind_issue_scope_paths(scope.record.request)
    completion = client.record_scope_outcome(scope, outcome=actual)
    assert completion.status == "continuation_ready"
    second = client.preview_review(
        dataclasses.replace(request, client_intent_id="intent:preview-second"),
        scope_continuation=completion.continuation,
    )
    assert second.record.correspondence_sha256 == first.record.correspondence_sha256
    assert second.record.scope_outcome_ref == completion.reference
    assert concise_result(second).decision_required == "apply_review"
    inputs = client.record_review_decision(
        second.reference,
        decision=v.SetupApplyDecision(
            second.reference, "accept_reviewed_final_files", EXECUTION, "intent:apply"
        ),
    )
    assert inputs.record.final_files == second.record.final_files
    outcome = client.apply_reviewed(inputs, client_intent_id="intent:apply")
    assert outcome.product_status == "apply_completed"
    assert outcome.original_evidence.completion_verified
    concise = concise_result(outcome)
    assert concise.reference == outcome.reference
    assert concise.decision_required == "none"
    assert concise.product_status == "apply_completed"
    assert not concise.authorizes_retry
    assert (repository / "aware.repo.toml").is_file()
    raw = client.read_evidence(outcome.reference, expected_target=request.target)
    from aware_workspace_sdk.architecture_setup_command_values import (
        command_value_to_json,
    )

    assert raw.raw_bytes == command_value_to_json(outcome.original_evidence).encode()
    review_value_to_payload(outcome.retention)
    assert all(
        item.sequence.release == "confirmed"
        for item in outcome.retention.sequence_cleanup
    )
    cleanup = client.release_client()
    assert cleanup.ledger_complete
    assert cleanup.directory.release == "confirmed"
    assert cleanup.workspace.outcome == cleanup.issue.outcome == "confirmed"
    assert client.release_client() is cleanup


def scope_ready(context):
    _, _, client, request, issuer = context
    first = client.preview_review(request)
    inputs = client.record_review_decision(
        first.reference,
        decision=v.SetupScopeDecision(
            first.reference, "accept_reviewed_effect_scope", EXECUTION, "intent:scope"
        ),
    )
    return first, inputs, issuer.bind_issue_scope_paths(inputs.record.request)


def apply_ready(context):
    _, _, client, request, _ = context
    first, scope, result = scope_ready(context)
    completion = client.record_scope_outcome(scope, outcome=result)
    second = client.preview_review(
        dataclasses.replace(request, client_intent_id="intent:preview-second"),
        scope_continuation=completion.continuation,
    )
    inputs = client.record_review_decision(
        second.reference,
        decision=v.SetupApplyDecision(
            second.reference, "accept_reviewed_final_files", EXECUTION, "intent:apply"
        ),
    )
    return first, second, inputs


@pytest.mark.parametrize("choice", ["scope", "apply"])
def test_decisions_are_explicit_and_second_review_is_required(context, choice):
    repository, _, client, request, _ = context
    first = client.preview_review(request)
    bad = (
        v.SetupScopeDecision(first.reference, "accept", EXECUTION, "intent:bad")
        if choice == "scope"
        else v.SetupApplyDecision(
            first.reference, "accept_reviewed_final_files", EXECUTION, "intent:bad"
        )
    )
    with pytest.raises(v.SetupReviewError):
        client.record_review_decision(first.reference, decision=bad)
    assert not (repository / "aware.repo.toml").exists()


def test_scope_inputs_cannot_be_reconstructed_from_detached_data(context):
    _, _, client, _, _ = context
    _, inputs, result = scope_ready(context)
    with pytest.raises(v.SetupReviewError):
        client.record_scope_outcome(dataclasses.replace(inputs), outcome=result)
    assert (
        client.record_scope_outcome(inputs, outcome=result).status
        == "continuation_ready"
    )
    with pytest.raises(v.SetupReviewError):
        client.record_scope_outcome(inputs, outcome=result)


@pytest.mark.parametrize("drift", ["issue", "manifest", "source"])
def test_intervening_source_drift_refuses_without_setup(context, drift):
    repository, _, client, _, _ = context
    _, second, inputs = apply_ready(context)
    if drift == "issue":
        target = repository / ISSUE
    elif drift == "manifest":
        target = repository / "aware.protocol.toml"
    else:
        target = (
            repository
            / second.original_evidence.workspace_observation.binding.input_bindings[
                0
            ].path
        )
    before = target.read_bytes() if target.exists() else b""
    changed = before + b"\n# drift\n"
    target.write_bytes(changed)
    outcome = None
    try:
        outcome = client.apply_reviewed(inputs, client_intent_id="intent:apply")
    except v.SetupReviewError:
        pass
    assert outcome is None or outcome.product_status in ("refused", "incomplete")
    assert target.read_bytes() == changed
    if target.name != "aware.repo.toml":
        assert not (repository / "aware.repo.toml").exists()


def test_second_preview_rejects_intervening_issue_edit(context):
    repository, _, client, request, _ = context
    _, inputs, result = scope_ready(context)
    completed = client.record_scope_outcome(inputs, outcome=result)
    path = repository / ISSUE
    path.write_bytes(path.read_bytes() + b"\n## unexpected edit\n")
    with pytest.raises(v.SetupReviewError):
        client.preview_review(
            dataclasses.replace(request, client_intent_id="intent:preview-second"),
            scope_continuation=completed.continuation,
        )
    assert not (repository / "aware.repo.toml").exists()


@pytest.mark.parametrize("failure", ["failure", "unknown", "incomplete_result"])
def test_unsuccessful_scope_outcomes_are_retained_without_continuation(
    context, failure
):
    from aware_issue_sdk import operation as issue

    _, evidence, client, _, _ = context
    _, inputs, result = scope_ready(context)
    if failure == "unknown":
        result = v.SetupUnknownScopeOutcome(
            "unknown", "LostReturn", True, ("scope_return_unavailable",)
        )
    elif failure == "failure":
        result = issue.IssueMutationError(
            "provider_invocation_failed",
            "provider",
            issue.ISSUE_BIND_SCOPE_OPERATION_REF,
            TAG,
            True,
            "unknown",
            issue.IssueProviderReport(None, ()),
        )
    else:
        result = dataclasses.replace(result, source_sha256_before="sha256:" + "b" * 64)
    completed = client.record_scope_outcome(inputs, outcome=result)
    assert completed.original_outcome is result
    assert completed.continuation is None
    assert completed.reference is not None
    assert (evidence / completed.reference.locator).exists()


def test_failed_scope_retention_keeps_actual_success_and_refuses_retry(
    context, monkeypatch
):
    _, _, client, _, _ = context
    _, inputs, result = scope_ready(context)

    def failed(*args, **kwargs):
        raise OSError("disposable retention failure")

    monkeypatch.setattr(client._runtime.store, "write_capture", failed)
    completed = client.record_scope_outcome(inputs, outcome=result)
    assert completed.status == "incomplete"
    assert completed.original_outcome is result
    assert completed.continuation is None
    assert not completed.retention.ledger_complete
    with pytest.raises(v.SetupReviewError):
        client.record_scope_outcome(inputs, outcome=result)


@pytest.mark.parametrize("stage", ["scope", "apply"])
def test_intent_failure_exposes_no_dispatch(context, monkeypatch, stage):
    repository, _, client, request, _ = context
    if stage == "scope":
        review = client.preview_review(request)
    else:
        _, review, inputs = apply_ready(context)
    original = client._runtime.store.write_metadata

    def failed(name, raw):
        if name.endswith("-intent.json"):
            raise OSError("intent unavailable")
        return original(name, raw)

    monkeypatch.setattr(client._runtime.store, "write_metadata", failed)
    with pytest.raises(v.SetupReviewError) as error:
        if stage == "scope":
            client.record_review_decision(
                review.reference,
                decision=v.SetupScopeDecision(
                    review.reference,
                    "accept_reviewed_effect_scope",
                    EXECUTION,
                    "intent:scope",
                ),
            )
        else:
            client.apply_reviewed(inputs, client_intent_id="intent:apply")
    assert error.value.failure.outcome is None
    assert not (repository / "aware.repo.toml").exists()


def test_apply_return_retention_failure_preserves_actual_effect(context, monkeypatch):
    repository, evidence, client, _, _ = context
    _, _, inputs = apply_ready(context)
    original = client._runtime.store.write_metadata

    def failed(name, raw):
        if name.endswith("-outcome.json"):
            raise OSError("outcome marker unavailable")
        return original(name, raw)

    monkeypatch.setattr(client._runtime.store, "write_metadata", failed)
    with pytest.raises(v.SetupReviewError) as error:
        client.apply_reviewed(inputs, client_intent_id="intent:apply")
    prefix = error.value.failure
    assert prefix.outcome.product_status == "apply_completed"
    assert prefix.outcome.original_evidence.completion_verified
    assert prefix.retention.intent_ref is not None
    assert (evidence / prefix.retention.intent_ref.locator).exists()
    assert (repository / "aware.repo.toml").exists()
    assert not prefix.retention.ledger_complete
    with pytest.raises(v.SetupReviewError):
        client.apply_reviewed(inputs, client_intent_id="intent:apply")


def test_replay_refuses_locally_and_from_a_new_client(context):
    repository, evidence, client, _, _ = context
    _, second, inputs = apply_ready(context)
    assert (
        client.apply_reviewed(inputs, client_intent_id="intent:apply").product_status
        == "apply_completed"
    )
    with pytest.raises(v.SetupReviewError):
        client.apply_reviewed(inputs, client_intent_id="intent:apply")
    with WorkspaceSetupReviewClient.filesystem(
        repository_root=repository,
        evidence_root=evidence,
        execution_id=EXECUTION,
        authority_manifest_locator="aware.protocol.toml",
    ) as other:
        # A new decision intent cannot evade the original review's fixed action key.
        new = other.record_review_decision(
            second.reference,
            decision=v.SetupApplyDecision(
                second.reference,
                "accept_reviewed_final_files",
                EXECUTION,
                "intent:another-apply",
            ),
        )
        with pytest.raises(v.SetupReviewError) as error:
            other.apply_reviewed(new, client_intent_id="intent:another-apply")
        assert error.value.failure.outcome is None
    assert (repository / "aware.repo.toml").exists()


@pytest.mark.parametrize(
    "tamper", ["metadata", "capture", "reference", "root_identity"]
)
def test_history_integrity_and_target_binding(context, tamper):
    _, evidence, client, request, _ = context
    first = client.preview_review(request)
    reference = first.reference
    if tamper in ("metadata", "capture"):
        path = evidence / (
            reference.locator
            if tamper == "metadata"
            else first.record.capture.chunks[0].locator
        )
        raw = path.read_bytes()
        path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
    elif tamper == "reference":
        reference = dataclasses.replace(
            reference,
            target=dataclasses.replace(
                request.target, issue_tag="fb/2026-10-16/foreign"
            ),
        )
    else:
        reference = dataclasses.replace(
            reference, root_identity=v.DirectoryIdentity(1, 2)
        )
    with pytest.raises(v.SetupReviewError):
        client.read_review(reference, expected_target=request.target, purpose="history")


def test_history_after_issue_change_does_not_renew_current_use(context):
    repository, _, client, request, _ = context
    first = client.preview_review(request)
    path = repository / ISSUE
    path.write_bytes(path.read_bytes() + b"\n## later change\n")
    assert (
        client.read_review(
            first.reference, expected_target=request.target, purpose="history"
        ).record
        == first.record
    )
    with pytest.raises(v.SetupReviewError):
        client.read_review(
            first.reference, expected_target=request.target, purpose="current_use"
        )


def test_cancellation_preserves_type_known_prefix_and_cleanup(context, monkeypatch):
    _, _, client, request, _ = context

    class Cancel(BaseException):
        pass

    error = Cancel("disposable cancellation")

    def interrupted(*args, **kwargs):
        raise error

    monkeypatch.setattr(client._runtime.store, "write_capture", interrupted)
    with pytest.raises(Cancel) as caught:
        client.preview_review(request)
    assert caught.value is error
    assert error.setup_review_failure.interruption
    assert error.setup_review_failure.outcome.product_status == "preview_completed"
    assert client.release_client().directory.release == "confirmed"


def test_foreign_thread_cannot_change_original_action_evidence(context):
    _, _, client, request, _ = context
    first = client.preview_review(request)
    previous = client._runtime.store.retention()
    errors = []

    def foreign():
        try:
            client.read_review(
                first.reference, expected_target=request.target, purpose="history"
            )
        except v.SetupReviewError as error:
            errors.append(error)

    thread = threading.Thread(target=foreign)
    thread.start()
    thread.join()
    assert len(errors) == 1
    assert client._runtime.store.retention() == previous
    assert (
        client.read_review(
            first.reference, expected_target=request.target, purpose="current_use"
        ).record
        == first.record
    )


def test_collection_releases_original_private_descriptor(context):
    _, _, client, _, _ = context
    from aware_file_system import private_directory as private

    directory = client._runtime.store.directory
    fd = private._DIRECTORIES[id(directory)][1].fd
    reference = weakref.ref(directory)
    del directory
    cleanup = client.release_client()
    gc.collect()
    assert reference() is None
    assert cleanup.directory.release == "confirmed"
    with pytest.raises(OSError):
        os.fstat(fd)


@pytest.mark.parametrize(
    "placement", ["inside", "parent", "missing", "mode", "symlink"]
)
def test_factory_refuses_unsafe_roots_without_creating_or_repairing(context, placement):
    repository, evidence, _, _, _ = context
    if placement == "inside":
        root = repository / "private"
        root.mkdir(mode=0o700)
    elif placement == "parent":
        root = repository.parent
    elif placement == "missing":
        root = evidence.parent / "not-created"
    elif placement == "mode":
        root = evidence.parent / "public"
        root.mkdir(mode=0o755)
    else:
        root = evidence.parent / "alias"
        root.symlink_to(evidence, target_is_directory=True)
    with pytest.raises(v.SetupReviewError):
        WorkspaceSetupReviewClient.filesystem(
            repository_root=repository,
            evidence_root=root,
            execution_id=EXECUTION,
            authority_manifest_locator="aware.protocol.toml",
        )
    assert not list(evidence.iterdir())
    if placement == "missing":
        assert not root.exists()
    if placement == "mode":
        assert root.stat().st_mode & 0o777 == 0o755


def test_private_drift_and_restore_cannot_revive_client(context):
    repository, evidence, client, request, _ = context
    first = client.preview_review(request)
    evidence.chmod(0o755)
    with pytest.raises(v.SetupReviewError) as caught:
        client.read_review(
            first.reference, expected_target=request.target, purpose="history"
        )
    assert caught.value.failure.retention.physical_refusal is not None
    evidence.chmod(0o700)
    with pytest.raises(v.SetupReviewError):
        client.record_review_decision(
            first.reference,
            decision=v.SetupScopeDecision(
                first.reference,
                "accept_reviewed_effect_scope",
                EXECUTION,
                "intent:scope",
            ),
        )
    assert not (repository / "aware.repo.toml").exists()


def test_scope_cancellation_keeps_actual_return_and_consumption(context, monkeypatch):
    _, _, client, _, _ = context
    _, inputs, actual = scope_ready(context)

    class Cancel(BaseException):
        pass

    error = Cancel()

    def interrupted(*args, **kwargs):
        raise error

    monkeypatch.setattr(client._runtime.store, "write_capture", interrupted)
    with pytest.raises(Cancel) as caught:
        client.record_scope_outcome(inputs, outcome=actual)
    assert caught.value is error
    assert error.setup_scope_completion.original_outcome is actual
    assert error.setup_scope_completion.continuation is None
    with pytest.raises(v.SetupReviewError):
        client.record_scope_outcome(inputs, outcome=actual)


def test_apply_cancellation_retains_original_driver_evidence(context, monkeypatch):
    from aware_workspace_runtime import architecture_setup_a1_driver as original

    repository, evidence, client, _, _ = context
    _, _, inputs = apply_ready(context)

    class Cancel(BaseException):
        pass

    cancellation = Cancel()
    run = original.run_setup_a1

    def interrupted(*args, **kwargs):
        assert list(evidence.glob("*-intent.json"))
        result, _ = run(*args, **kwargs)
        cancellation.setup_command_evidence = result
        raise cancellation

    monkeypatch.setattr(original, "run_setup_a1", interrupted)
    with pytest.raises(Cancel):
        client.apply_reviewed(inputs, client_intent_id="intent:apply")
    assert cancellation.setup_review_failure.outcome.product_status == "apply_completed"
    assert (
        cancellation.setup_review_failure.outcome.original_evidence.completion_verified
    )
    assert (repository / "aware.repo.toml").is_file()
    with pytest.raises(v.SetupReviewError):
        client.apply_reviewed(inputs, client_intent_id="intent:apply")


def test_idempotent_scope_result_can_continue_with_equal_before_after(context):
    repository, _, client, request, issuer = context
    first = client.preview_review(request)
    chosen = tuple(
        sorted(
            set(first.record.existing_scope)
            | set(first.record.physical_scope)
            | {ISSUE}
        )
    )
    source = (repository / ISSUE).read_text().split("## Ownership Scope", 1)[0]
    (repository / ISSUE).write_text(
        source
        + "## Ownership Scope\n"
        + "".join("- `" + path + "`\n" for path in chosen)
    )
    review = client.preview_review(
        dataclasses.replace(request, client_intent_id="intent:idempotent-preview")
    )
    inputs = client.record_review_decision(
        review.reference,
        decision=v.SetupScopeDecision(
            review.reference,
            "accept_reviewed_effect_scope",
            EXECUTION,
            "intent:idempotent-scope",
        ),
    )
    actual = issuer.bind_issue_scope_paths(inputs.record.request)
    assert actual.source_sha256_before == actual.source_sha256_after
    assert (
        client.record_scope_outcome(inputs, outcome=actual).status
        == "continuation_ready"
    )


def test_concurrent_clients_expose_at_most_one_scope_intent(context):
    repository, evidence, client, request, _ = context
    first = client.preview_review(request)
    barrier = threading.Barrier(2)
    inputs, failures = [], []

    def contender(index):
        with WorkspaceSetupReviewClient.filesystem(
            repository_root=repository,
            evidence_root=evidence,
            execution_id=EXECUTION,
            authority_manifest_locator="aware.protocol.toml",
        ) as contender_client:
            barrier.wait(timeout=10)
            try:
                result = contender_client.record_review_decision(
                    first.reference,
                    decision=v.SetupScopeDecision(
                        first.reference,
                        "accept_reviewed_effect_scope",
                        EXECUTION,
                        "intent:contender-" + str(index),
                    ),
                )
            except v.SetupReviewError as error:
                failures.append(error)
            else:
                inputs.append(result)

    threads = [threading.Thread(target=contender, args=(index,)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
        assert not thread.is_alive()
    assert len(inputs) == len(failures) == 1
    assert len(list(evidence.glob("*-intent.json"))) == 1
    assert not (repository / "aware.repo.toml").exists()


def test_context_cleanup_does_not_replace_original_cancellation(context, monkeypatch):
    _, _, client, request, _ = context

    class Cancel(BaseException):
        pass

    cancellation = Cancel()
    release = client._runtime.store.release

    def lost_cleanup_return():
        release()
        raise OSError("cleanup return lost")

    monkeypatch.setattr(client._runtime.store, "release", lost_cleanup_return)
    with pytest.raises(Cancel) as caught, client:
        client.preview_review(request)
        raise cancellation
    assert caught.value is cancellation
    assert type(cancellation.setup_review_cleanup_failure) is v.SetupReviewError
    assert not cancellation.setup_review_client_cleanup.ledger_complete
    assert cancellation.setup_review_client_cleanup.directory.release == "confirmed"
    assert client.release_client() is cancellation.setup_review_client_cleanup


def test_root_cleanup_cannot_upgrade_unknown_product_owner(context):
    _, _, client, request, _ = context
    client.preview_review(request)
    original = client._runtime._workspace_cleanup
    client._runtime._workspace_cleanup = dataclasses.replace(
        original, outcome="unknown", ledger_complete=False
    )
    cleanup = client.release_client()
    assert not cleanup.ledger_complete
    assert cleanup.workspace.outcome == "unknown"
    assert cleanup.directory.release == "confirmed"


@pytest.mark.parametrize("primary_kind", ["cancel", "error", "none"])
@pytest.mark.parametrize(
    "cleanup_kind", ["raised", "interrupted", "unknown", "incomplete"]
)
def test_authority_read_keeps_primary_and_independent_cleanup(
    context, monkeypatch, primary_kind, cleanup_kind
):
    from aware_issue_sdk.workspace_setup_admission import (
        IssueWorkspaceSetupAdmissionClient,
    )

    repository, _, client, request, _ = context
    first = client.preview_review(request)

    class Cancel(BaseException):
        pass

    primary = {"cancel": Cancel("read cancelled"), "error": OSError("read failed")}.get(
        primary_kind
    )
    cleanup_error = (
        Cancel("cleanup interrupted")
        if cleanup_kind == "interrupted"
        else OSError("cleanup return lost")
    )
    observe = IssueWorkspaceSetupAdmissionClient.observe_authority_sources
    release = IssueWorkspaceSetupAdmissionClient.release_client
    releases, cleanup_returns = [], []

    def observe_then_fail(issuer, **kwargs):
        sources = observe(issuer, **kwargs)
        if primary is not None:
            raise primary
        return sources

    def dispose_then_fail(issuer):
        owner = issuer._owner
        actual = release(issuer)
        releases.append(owner)
        assert owner.closed
        assert actual.outcome == "confirmed" and actual.ledger_complete
        if cleanup_kind in ("raised", "interrupted"):
            raise cleanup_error
        returned = dataclasses.replace(
            actual,
            outcome="unknown" if cleanup_kind == "unknown" else "confirmed",
            ledger_complete=cleanup_kind == "unknown",
        )
        cleanup_returns.append(returned)
        return returned

    monkeypatch.setattr(
        IssueWorkspaceSetupAdmissionClient,
        "observe_authority_sources",
        observe_then_fail,
    )
    monkeypatch.setattr(
        IssueWorkspaceSetupAdmissionClient, "release_client", dispose_then_fail
    )
    expected = (
        Cancel
        if primary_kind == "cancel" or primary is None and cleanup_kind == "interrupted"
        else v.SetupReviewError
    )
    with pytest.raises(expected) as caught:
        client.read_review(
            first.reference, expected_target=request.target, purpose="current_use"
        )
    reported = caught.value
    original = (
        primary
        if primary is not None
        else (reported if expected is Cancel else reported.__cause__)
    )
    if primary_kind == "cancel":
        assert reported is primary
    elif primary_kind == "error":
        assert reported.__cause__ is primary
    failure = (
        reported.failure
        if type(reported) is v.SetupReviewError
        else reported.setup_review_failure
    )
    assert failure.phase == "read_review"
    assert failure.interruption is (expected is Cancel)
    attached = original.setup_review_issue_cleanup_failure
    if cleanup_kind in ("raised", "interrupted"):
        assert attached is cleanup_error
        assert original.setup_review_issue_cleanup is None
        assert failure.cleanup.issue is None
        assert failure.cleanup.diagnostics == ("issue_client_cleanup_unavailable",)
    else:
        assert str(attached) == "review_issue_cleanup_incomplete"
        assert original.setup_review_issue_cleanup is cleanup_returns[0]
        assert failure.cleanup.issue is cleanup_returns[0]
        assert failure.cleanup.diagnostics == ("issue_client_cleanup_incomplete",)
    assert not failure.cleanup.ledger_complete
    review_value_to_payload(failure.cleanup)
    assert len(releases) == 1
    with pytest.raises(v.SetupReviewError, match="review_client_released"):
        client.read_review(
            first.reference, expected_target=request.target, purpose="current_use"
        )
    cleanup = client.release_client()
    assert not cleanup.ledger_complete
    assert cleanup.issue is failure.cleanup.issue
    assert cleanup.diagnostics == failure.cleanup.diagnostics
    assert cleanup.directory.release == "confirmed"
    assert client.release_client() is cleanup
    assert len(releases) == 1
    assert not (repository / "aware.repo.toml").exists()


def test_concise_projection_requires_durable_full_capture():
    outcome = v.SetupCommandOutcome(
        "apply_completed",
        None,
        None,
        v.RetentionEvidence("incomplete", None, None, (), (), None, False, (), None),
        (),
        False,
    )
    with pytest.raises(ValueError, match="complete_retained_capture"):
        concise_result(outcome)


def _stale_review(context, drift):
    repository, evidence, client, request, _ = context
    review = client.preview_review(request)
    path = repository / (ISSUE if drift == "issue" else "aware.protocol.toml")
    path.write_bytes(path.read_bytes() + b"\n# independently changed\n")
    return repository, evidence, client, request, review


@pytest.mark.parametrize("drift", ["issue", "manifest"])
@pytest.mark.parametrize("operation", ["read", "decision", "apply"])
def test_stale_refusal_has_actual_record_and_independent_cleanup(
    context, monkeypatch, drift, operation
):
    from aware_workspace_sdk.architecture_setup_review_codec import (
        review_value_from_json,
    )

    repository, evidence, client, request, _ = context
    if operation == "apply":
        _, review, inputs = apply_ready(context)
        path = repository / (ISSUE if drift == "issue" else "aware.protocol.toml")
        path.write_bytes(path.read_bytes() + b"\n# independently changed\n")
    else:
        _, _, _, _, review = _stale_review(context, drift)
    before = {
        str(p): (p.read_bytes(), p.stat().st_mode)
        for p in repository.rglob("*")
        if p.is_file()
    }
    original_files = set(evidence.iterdir())
    calls = []

    def unexpected_driver(*args, **kwargs):
        calls.append("driver")
        raise AssertionError("stale current inputs must precede product dispatch")

    monkeypatch.setattr(client._runtime, "_run_driver", unexpected_driver)
    with pytest.raises(v.SetupReviewError) as caught:
        if operation == "read":
            client.read_review(
                review.reference, expected_target=request.target, purpose="current_use"
            )
        elif operation == "decision":
            client.record_review_decision(
                review.reference,
                decision=v.SetupScopeDecision(
                    review.reference,
                    "accept_reviewed_effect_scope",
                    EXECUTION,
                    "intent:stale",
                ),
            )
        else:
            client.apply_reviewed(inputs, client_intent_id="intent:apply")
    error = caught.value
    failure = error.failure
    assert failure.code == (
        "review_issue_changed"
        if drift == "issue"
        else "review_authority_sources_changed"
    )
    assert failure.retention.status == "published"
    assert failure.retention.ledger_complete
    assert failure.retention.physical_refusal is None
    assert error.retention_error is None
    assert not failure.interruption
    assert calls == []
    assert (
        len(failure.retention.sequence_observations)
        == len(failure.retention.sequence_cleanup)
        == 1
    )
    assert failure.retention.sequence_cleanup[0].sequence.release == "confirmed"
    reference = failure.reference
    assert reference.record_contract == v.REVIEW_SCHEMA_IDS[v.SetupRefusalRecord]
    assert set(evidence.iterdir()) - original_files == {evidence / reference.locator}
    read = client.read_evidence(reference, expected_target=request.target)
    refusal = review_value_from_json(v.SetupRefusalRecord, read.raw_bytes.decode())
    # The original Issue wire omits raw Markdown by design; compare its exact
    # owner encoding, not the decoder's intentionally absent raw-source cache.
    assert review_value_to_payload(refusal) == review_value_to_payload(failure.refusal)
    assert refusal.review_ref == review.reference
    assert refusal.request == review.record.request
    assert refusal.phase == failure.phase and refusal.code == failure.code
    assert refusal.reads == failure.reads
    assert refusal.reads and all(
        row.original.cleanup.outcome == "closed" for row in refusal.reads
    )
    assert refusal.product_dispatch == "not_invoked" and not refusal.authorizes_retry
    if operation == "read":
        assert (
            refusal.scope_decision
            is refusal.apply_decision
            is refusal.inputs_ref
            is None
        )
    elif operation == "decision":
        assert refusal.scope_decision.client_intent_id == "intent:stale"
        assert refusal.apply_decision is refusal.inputs_ref is None
    else:
        assert refusal.apply_decision == inputs.record.decision
        assert refusal.inputs_ref == inputs.reference and refusal.scope_decision is None
    assert (refusal.observed_sources is None) is (drift == "issue")
    if drift == "manifest":
        assert refusal.observed_sources.ledger_complete
        assert refusal.issue_cleanup.outcome == "confirmed"
    assert before == {
        str(p): (p.read_bytes(), p.stat().st_mode)
        for p in repository.rglob("*")
        if p.is_file()
    }
    with pytest.raises(v.SetupReviewError, match="original_review_record_required"):
        client.read_review(
            reference, expected_target=request.target, purpose="current_use"
        )
    cleanup = client.release_client()
    assert cleanup.ledger_complete and cleanup.directory.release == "confirmed"
    assert client.release_client() is cleanup


@pytest.mark.parametrize("drift", ["issue", "manifest"])
@pytest.mark.parametrize("fault", ["write", "lost_return", "cleanup", "cancel"])
def test_refusal_capture_failure_preserves_original_denial_and_unknowns(
    context, monkeypatch, drift, fault
):
    _, evidence, client, request, review = _stale_review(context, drift)
    from aware_file_system import private_directory as private

    class Cancel(BaseException):
        pass

    secondary = (
        Cancel("capture interrupted")
        if fault == "cancel"
        else OSError("capture unavailable")
    )
    write = client._runtime.store.write_metadata
    release = private.release_private_file_sequence
    calls = []

    def failed_write(*args, **kwargs):
        calls.append("write")
        if fault == "lost_return":
            write(*args, **kwargs)
        raise secondary

    def incomplete_release(child):
        calls.append("release")
        actual = release(child)
        return dataclasses.replace(
            actual,
            sequence=dataclasses.replace(
                actual.sequence, release="unknown", ledger_complete=False
            ),
        )

    if fault == "cleanup":
        monkeypatch.setattr(
            private, "release_private_file_sequence", incomplete_release
        )
    else:
        monkeypatch.setattr(client._runtime.store, "write_metadata", failed_write)
    with pytest.raises(Cancel if fault == "cancel" else v.SetupReviewError) as caught:
        client.read_review(
            review.reference, expected_target=request.target, purpose="current_use"
        )
    error = caught.value
    failure = (
        error.failure if isinstance(error, Exception) else error.setup_review_failure
    )
    assert failure.code == (
        "review_issue_changed"
        if drift == "issue"
        else "review_authority_sources_changed"
    )
    assert not failure.retention.ledger_complete
    assert failure.retention.status == "incomplete"
    assert failure.refusal is not None and failure.refusal.code == failure.code
    assert (
        failure.reference == review.reference
    )  # no invented completed refusal reference
    if fault == "cancel":
        assert error is secondary and failure.interruption
        assert error.setup_review_retention_error is secondary
    else:
        assert error.retention_error is not None
        if fault != "cleanup":
            assert error.retention_error is secondary
    assert len(calls) == 1
    with pytest.raises(v.SetupReviewError, match="review_client_released"):
        client.read_review(
            review.reference, expected_target=request.target, purpose="current_use"
        )
    if fault == "lost_return":
        assert (evidence / f"a1-{review.reference.attempt_ref}-refusal.json").is_file()
    client.release_client()
    client.release_client()
    assert len(calls) == 1


def test_second_stale_denial_cannot_overwrite_or_reuse_first_refusal(context):
    _, evidence, client, request, review = _stale_review(context, "issue")
    with pytest.raises(v.SetupReviewError) as first:
        client.read_review(
            review.reference, expected_target=request.target, purpose="current_use"
        )
    reference = first.value.failure.reference
    path = evidence / reference.locator
    before = path.read_bytes()
    with pytest.raises(v.SetupReviewError) as second:
        client.read_review(
            review.reference, expected_target=request.target, purpose="current_use"
        )
    assert second.value.failure.code == "review_issue_changed"
    assert second.value.retention_error is not None
    assert not second.value.failure.retention.ledger_complete
    assert second.value.failure.retention.physical_refusal is not None
    assert path.read_bytes() == before


def test_spent_physical_sequence_remains_incomplete(context):
    _, _, client, _, _ = context
    _, _, inputs = apply_ready(context)
    result = client.apply_reviewed(inputs, client_intent_id="intent:apply")
    assert result.product_status == "apply_completed"
    with pytest.raises(v.SetupReviewError) as caught:
        client.apply_reviewed(inputs, client_intent_id="intent:apply")
    assert caught.value.failure.code == "original_unconsumed_apply_inputs_required"
    assert not caught.value.failure.retention.ledger_complete


def test_new_client_spent_apply_keeps_original_physical_refusal(context):
    repository, evidence, client, _, _ = context
    _, review, inputs = apply_ready(context)
    assert (
        client.apply_reviewed(inputs, client_intent_id="intent:apply").product_status
        == "apply_completed"
    )
    before = (repository / "aware.repo.toml").read_bytes()
    with WorkspaceSetupReviewClient.filesystem(
        repository_root=repository,
        evidence_root=evidence,
        execution_id=EXECUTION,
        authority_manifest_locator="aware.protocol.toml",
    ) as other:
        with pytest.raises(v.SetupReviewError) as caught:
            other.record_review_decision(
                review.reference,
                decision=v.SetupApplyDecision(
                    review.reference,
                    "accept_reviewed_final_files",
                    EXECUTION,
                    "intent:apply",
                ),
            )
        failure = caught.value.failure
        assert failure.code == "sequence_request_baseline_changed"
        assert failure.retention.physical_refusal is not None
        assert not failure.retention.ledger_complete
        assert (
            failure.reference is None
            or failure.reference.record_contract
            != v.REVIEW_SCHEMA_IDS[v.SetupRefusalRecord]
        )
        assert not list(evidence.glob("*-refusal.json"))
    assert (repository / "aware.repo.toml").read_bytes() == before


def test_uncertain_read_cleanup_is_exposed_and_cannot_become_semantic_refusal(
    context, monkeypatch
):
    from aware_file_system import private_directory as private

    _, evidence, client, request, review = _stale_review(context, "issue")
    original = private.observe_private_directory_file
    returned = []

    def uncertain(*args, **kwargs):
        actual = original(*args, **kwargs)
        result = dataclasses.replace(
            actual,
            directory_after=dataclasses.replace(
                actual.directory_after, ledger_complete=False
            ),
        )
        returned.append(result)
        return result

    monkeypatch.setattr(private, "observe_private_directory_file", uncertain)
    with pytest.raises(v.SetupReviewError) as caught:
        client.read_review(
            review.reference, expected_target=request.target, purpose="current_use"
        )
    assert caught.value.failure.code == "review_read_cleanup_incomplete", repr(
        caught.value.__cause__
    )
    assert not caught.value.failure.retention.ledger_complete
    assert caught.value.failure.reads == tuple(returned)
    assert not caught.value.failure.reads[0].directory_after.ledger_complete
    assert caught.value.failure.reads[0].original.cleanup.outcome == "closed"
    assert not list(evidence.glob("*-refusal.json"))


@pytest.mark.parametrize("cleanup", ["unknown", "raised", "cancel"])
def test_semantic_denial_cannot_promote_independent_issue_cleanup(
    context, monkeypatch, cleanup
):
    from aware_issue_sdk.workspace_setup_admission import (
        IssueWorkspaceSetupAdmissionClient,
    )

    _, _, client, request, review = _stale_review(context, "manifest")
    release = IssueWorkspaceSetupAdmissionClient.release_client
    calls = []

    class Cancel(BaseException):
        pass

    cancellation = Cancel()

    def uncertain(owner):
        actual = release(owner)
        calls.append(actual)
        if cleanup == "cancel":
            raise cancellation
        if cleanup == "raised":
            raise OSError("Issue release return lost")
        return dataclasses.replace(actual, outcome="unknown", ledger_complete=False)

    monkeypatch.setattr(IssueWorkspaceSetupAdmissionClient, "release_client", uncertain)
    with pytest.raises(Cancel if cleanup == "cancel" else v.SetupReviewError) as caught:
        client.read_review(
            review.reference, expected_target=request.target, purpose="current_use"
        )
    failure = (
        caught.value.setup_review_failure
        if cleanup == "cancel"
        else caught.value.failure
    )
    assert failure.code == "review_authority_sources_changed"
    assert not failure.cleanup.ledger_complete
    if cleanup == "cancel":
        assert caught.value is cancellation and failure.interruption
        assert not failure.retention.ledger_complete
    else:
        assert (
            failure.retention.ledger_complete
        )  # refusal capture and Issue cleanup are independent
    cleanup_receipt = client.release_client()
    assert not cleanup_receipt.ledger_complete
    assert client.release_client() is cleanup_receipt
    assert len(calls) == 1
