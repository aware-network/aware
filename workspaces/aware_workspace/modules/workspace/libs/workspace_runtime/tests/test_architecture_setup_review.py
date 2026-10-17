"""Original preview driver and pure data joins; no proposed private IO execution."""

from __future__ import annotations

import dataclasses
import hashlib

import pytest
from aware_issue_runtime.parser import parse_issue_projection
from aware_issue_sdk import operation as issue
from aware_workspace_command import (
    architecture_setup_a1_command_values as compatibility,
)
from aware_workspace_command.architecture_setup_a1_command import run_a1
from aware_workspace_runtime.architecture_setup_a1_driver import run_setup_a1
from aware_workspace_runtime.architecture_setup_review import (
    apply_input_record,
    review_action_key,
    review_attempt_key,
    review_correspondence,
    reviewed_path_sets,
    scope_input_record,
    validate_review_capture,
    validate_scope_result,
)
from aware_workspace_sdk import architecture_setup_command_values as command
from aware_workspace_sdk import architecture_setup_review_values as v
from aware_workspace_sdk.architecture_setup_review_codec import (
    SetupReviewValueError,
    review_value_digest,
    review_value_to_json,
)
from test_architecture_setup_a1_command import ISSUE, arguments
from test_architecture_setup_a1_command import root as _original_root_fixture

root = _original_root_fixture


def sha(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


@pytest.fixture
def reviewed(root):
    evidence, code = run_a1(
        arguments(
            root,
            "--actor-ref",
            "actor:declared",
            "--actor-evidence-ref",
            "evidence:declared",
        )
    )
    assert code == 0
    raw = command.command_value_to_json(evidence).encode()
    projection = parse_issue_projection(
        text=(root / ISSUE).read_text(), source_path=ISSUE
    )
    read = issue.IssueReadProjectionResolveResult(
        issue.IssueReadProjectionResolveOutcome.FOUND,
        projection.issue_ref,
        "provider:proof",
        "original-projection-fixture",
        "1.0",
        projection,
    )
    request = v.SetupReviewRequest(
        v.SetupTarget(str(root), projection.tag, ISSUE, "aware.protocol.toml"),
        evidence.request.architecture_request,
        evidence.request.execution_ref,
        evidence.request.client_intent_id,
        "actor:declared",
        "evidence:declared",
        True,
    )
    physical, final = reviewed_path_sets(evidence)
    record = v.SetupReviewRecord(
        request,
        v.SetupCaptureDescriptor(
            "command_v1",
            len(raw),
            sha(raw),
            (v.SetupChunkDescriptor(0, "capture.bin", len(raw), sha(raw)),),
        ),
        read,
        evidence.review_guards,
        projection.ownership_scope,
        physical,
        final,
        review_correspondence(evidence),
        None,
        True,
        (),
    )
    reference = ref(record, request.target)
    return evidence, record, reference


def ref(record, target):
    return v.SetupEvidenceRef(
        "/tmp/external-evidence",
        v.DirectoryIdentity(1, 2),
        "record.json",
        v.REVIEW_SCHEMA_IDS[type(record)],
        review_value_digest(record),
        len(review_value_to_json(record).encode()),
        "attempt:proof",
        target,
    )


def test_compatibility_module_reexports_the_same_classes_functions_and_private_tables():
    for name in (
        *[cls.__name__ for cls in command._TYPES],
        "command_value_to_json",
        "command_value_from_json",
        "_FIELD_TYPES",
        "_DEFS",
    ):
        assert getattr(compatibility, name) is getattr(command, name)


def test_typed_driver_uses_original_preview_and_unchanged_v1(root):
    old, code = run_a1(arguments(root))
    request = old.request
    new, new_code = run_setup_a1(
        dataclasses.replace(request, issue_request=None),
        mode="preview",
        review_guards=old.review_guards,
    )
    assert code == new_code == 0
    assert set(command.command_value_to_payload(new)) == set(
        command.command_value_to_payload(old)
    )
    assert len(command.command_value_to_payload(new)) == 19
    assert review_correspondence(new) == review_correspondence(old)
    assert new.review_guards == old.review_guards
    assert (
        new.client_cleanup.workspace.outcome
        == new.client_cleanup.issue.outcome
        == "confirmed"
    )
    assert not (root / "aware.repo.toml").exists()


def test_genuine_preview_and_parsed_issue_correlate_without_admitting_a_dispatch(
    reviewed,
):
    evidence, record, reference = reviewed
    validate_review_capture(record, evidence)
    decision = v.SetupScopeDecision(
        reference,
        "accept_reviewed_effect_scope",
        record.request.execution_ref,
        "intent:scope",
    )
    inputs = scope_input_record(record, reference, decision)
    assert set(inputs.scope_paths) >= set(record.existing_scope) | set(
        record.physical_scope
    )
    assert record.request.target.issue_path in inputs.scope_paths
    assert (
        inputs.request.expected_source_sha256
        == record.review_guards.issue_source_sha256
    )
    assert inputs.request.scope_paths == inputs.scope_paths
    assert not hasattr(inputs, "intent_ref")
    # It is request data only; this helper never invokes Issue or writes an intent.


@pytest.mark.parametrize(
    "mutation", ["scratch", "input_state", "step_mode", "ordered_effects"]
)
def test_correspondence_preserves_original_preconditions_not_only_hashes(
    reviewed, mutation
):
    evidence, _, _ = reviewed
    binding = evidence.workspace_observation.binding
    if mutation == "scratch":
        row = binding.file_transitions[0]
        changed = dataclasses.replace(
            binding,
            file_transitions=(
                dataclasses.replace(row, scratch_path="different.scratch"),
            ),
        )
    elif mutation == "input_state":
        row = binding.input_bindings[0]
        obs = dataclasses.replace(
            row.observation,
            exists=True,
            device=1,
            inode=2,
            mode=33188,
            size_bytes=1,
            mtime_ns=1,
            ctime_ns=1,
            content_sha256="sha256:" + "b" * 64,
        )
        changed = dataclasses.replace(
            binding,
            input_bindings=(
                dataclasses.replace(row, observation=obs),
                *binding.input_bindings[1:],
            ),
        )
    elif mutation == "step_mode":
        step = binding.ordered_effects[0]
        changed = dataclasses.replace(
            binding,
            ordered_effects=(
                dataclasses.replace(step, requested_mode=0o700),
                *binding.ordered_effects[1:],
            ),
        )
    else:
        effects = tuple(
            dataclasses.replace(x, ordinal=i)
            for i, x in enumerate(reversed(binding.ordered_effects))
        )
        changed = dataclasses.replace(binding, ordered_effects=effects)
    changed_evidence = dataclasses.replace(
        evidence,
        workspace_observation=dataclasses.replace(
            evidence.workspace_observation, binding=changed
        ),
    )
    assert review_correspondence(changed_evidence) != review_correspondence(evidence)


def test_only_enumerated_live_identities_are_excluded_from_correspondence(reviewed):
    evidence, _, _ = reviewed
    old = evidence.workspace_observation.binding
    changed = dataclasses.replace(
        old,
        provider_ref="different-provider",
        provider_generation="generation2",
        plan_ref="other-plan",
        attempt_ref="other-attempt",
        physical_provider_ref="native2",
        physical_provider_generation="native-generation2",
        physical_preparation_ref="native-plan2",
        process_id=old.process_id + 1,
        thread_id=old.thread_id + 1,
        ordered_effects=tuple(
            dataclasses.replace(
                s, resource_refs=("new-resource",), cleanup_refs=("new-cleanup",)
            )
            for s in old.ordered_effects
        ),
    )
    assert review_correspondence(
        dataclasses.replace(
            evidence,
            workspace_observation=dataclasses.replace(
                evidence.workspace_observation, binding=changed
            ),
        )
    ) == review_correspondence(evidence)


@pytest.mark.parametrize("field", ["scope", "final", "digest", "request", "issue"])
def test_review_capture_mismatch_refuses(reviewed, field):
    evidence, record, _ = reviewed
    if field == "scope":
        changed = dataclasses.replace(record, physical_scope=())
    elif field == "final":
        changed = dataclasses.replace(record, final_files=())
    elif field == "digest":
        changed = dataclasses.replace(
            record, correspondence_sha256="sha256:" + "f" * 64
        )
    elif field == "request":
        changed = dataclasses.replace(
            record,
            request=dataclasses.replace(
                record.request, client_intent_id="foreign-intent"
            ),
        )
    else:
        changed = dataclasses.replace(record, existing_scope=())
    with pytest.raises(SetupReviewValueError):
        validate_review_capture(changed, evidence)


def test_decisions_require_exact_reference_execution_stage_and_preserve_omitted_actors(
    reviewed,
):
    _, record, reference = reviewed
    scope = v.SetupScopeDecision(
        reference, "accept_reviewed_effect_scope", record.request.execution_ref, "scope"
    )
    apply = v.SetupApplyDecision(
        reference, "accept_reviewed_final_files", record.request.execution_ref, "apply"
    )
    with pytest.raises(SetupReviewValueError):
        apply_input_record(record, reference, apply)
    with pytest.raises(SetupReviewValueError):
        scope_input_record(
            record, reference, dataclasses.replace(scope, execution_ref="foreign")
        )
    with pytest.raises(SetupReviewValueError):
        scope_input_record(
            record, dataclasses.replace(reference, record_bytes=1), scope
        )
    missing = dataclasses.replace(
        record, request=dataclasses.replace(record.request, actor_ref=None)
    )
    missingref = ref(missing, record.request.target)
    with pytest.raises(SetupReviewValueError, match="actor_metadata"):
        scope_input_record(
            missing, missingref, dataclasses.replace(scope, review=missingref)
        )


def scope_result(record, inputs, *, idempotent=False):
    text = record.issue_read.projection.raw_markdown
    if not idempotent:
        text += "\n" + "".join(
            "- `" + p + "`\n"
            for p in inputs.scope_paths
            if p not in record.existing_scope
        )
    projection = parse_issue_projection(
        text=text, source_path=record.request.target.issue_path
    )
    return issue.IssueMutationResult(
        issue.ISSUE_BIND_SCOPE_OPERATION_REF,
        issue.IssueMutationOutcome.IDEMPOTENT
        if idempotent
        else issue.IssueMutationOutcome.APPLIED,
        record.request.target.issue_tag,
        record.issue_read.provider_ref,
        record.issue_read.provider_distribution,
        record.issue_read.provider_version,
        inputs.request.expected_source_sha256,
        projection.source_digest,
        projection=projection,
    )


def test_complete_original_result_postimage_join_and_second_apply_data(reviewed):
    _, record, reference = reviewed
    decision = v.SetupScopeDecision(
        reference, "accept_reviewed_effect_scope", record.request.execution_ref, "scope"
    )
    inputs = scope_input_record(record, reference, decision)
    result = scope_result(record, inputs)
    assert validate_scope_result(record, inputs, result) is result
    after = dataclasses.replace(
        record,
        scope_outcome_ref=reference,
        review_guards=dataclasses.replace(
            record.review_guards, issue_source_sha256=result.source_sha256_after
        ),
        issue_read=dataclasses.replace(record.issue_read, projection=result.projection),
        existing_scope=result.projection.ownership_scope,
    )
    afterref = ref(after, record.request.target)
    apply = v.SetupApplyDecision(
        afterref, "accept_reviewed_final_files", record.request.execution_ref, "apply"
    )
    apply_inputs = apply_input_record(after, afterref, apply)
    assert apply_inputs.final_files == record.final_files
    assert (
        apply_inputs.request.issue_request.expected_issue_source_sha256
        == result.source_sha256_after
    )
    assert apply_inputs.request.client_intent_id == "apply"


@pytest.mark.parametrize(
    "field", ["before", "provider", "operation", "outcome", "projection", "scope"]
)
def test_scope_result_must_be_complete_correlated_original_return(reviewed, field):
    _, record, reference = reviewed
    inputs = scope_input_record(
        record,
        reference,
        v.SetupScopeDecision(
            reference,
            "accept_reviewed_effect_scope",
            record.request.execution_ref,
            "scope",
        ),
    )
    result = scope_result(record, inputs)
    if field == "before":
        result = dataclasses.replace(result, source_sha256_before="sha256:" + "b" * 64)
    elif field == "provider":
        result = dataclasses.replace(result, provider_ref="different")
    elif field == "operation":
        result = dataclasses.replace(
            result, operation_ref=issue.ISSUE_BLOCK_OPERATION_REF
        )
    elif field == "outcome":
        result = dataclasses.replace(
            result, outcome=issue.IssueMutationOutcome.STALE, projection=None
        )
    elif field == "projection":
        object.__setattr__(result, "projection", None)
    else:
        result = dataclasses.replace(
            result,
            projection=dataclasses.replace(
                result.projection, ownership_scope=("narrower",)
            ),
        )
    with pytest.raises(SetupReviewValueError):
        validate_scope_result(record, inputs, result)


def test_attempt_and_action_names_are_domain_separated_and_deterministic():
    assert (
        review_attempt_key("e", "i")
        == hashlib.sha256(b"aware.setup-review.attempt.v1\0e\0i").hexdigest()
    )
    digest = "sha256:" + "a" * 64
    assert review_action_key("apply", digest) == sha(
        b"aware.setup-review.intent.v1\0apply\0" + digest.encode()
    )
    assert review_action_key("apply", digest) != review_action_key("scope", digest)
    for execution, intent in [("e\0", "i"), ("e", ""), ("e", "i" * 1025)]:
        with pytest.raises(SetupReviewValueError):
            review_attempt_key(execution, intent)
    for action, d in [("unknown", digest), ("apply", "sha256:" + "A" * 64)]:
        with pytest.raises(SetupReviewValueError):
            review_action_key(action, d)


def test_idempotent_scope_before_after_equality_is_accepted(reviewed):
    _, record, reference = reviewed
    decision = v.SetupScopeDecision(
        reference, "accept_reviewed_effect_scope", record.request.execution_ref, "scope"
    )
    inputs = scope_input_record(record, reference, decision)
    applied = scope_result(record, inputs)
    already = dataclasses.replace(
        record,
        issue_read=dataclasses.replace(
            record.issue_read, projection=applied.projection
        ),
        existing_scope=applied.projection.ownership_scope,
        review_guards=dataclasses.replace(
            record.review_guards, issue_source_sha256=applied.source_sha256_after
        ),
    )
    alreadyref = ref(already, record.request.target)
    inputs = scope_input_record(
        already, alreadyref, dataclasses.replace(decision, review=alreadyref)
    )
    result = scope_result(already, inputs, idempotent=True)
    assert result.source_sha256_before == result.source_sha256_after
    assert validate_scope_result(already, inputs, result) is result


def test_typed_driver_applies_once_through_genuine_original_suppliers(root):
    from test_architecture_setup_a1_command import scope

    first, code = run_a1(arguments(root))
    assert code == 0
    scope(root, first.workspace_observation.binding)
    second, code = run_a1(arguments(root))
    assert code == 0
    outcome, code = run_setup_a1(
        second.request,
        mode="apply",
        review_guards=second.review_guards,
        allowed_final_files=tuple(
            row.path for row in second.workspace_observation.binding.file_transitions
        ),
    )
    assert code == 0 and outcome.command_status == "apply_completed"
    assert (root / "aware.repo.toml").is_file()
    assert (
        outcome.client_cleanup.issue.outcome
        == outcome.client_cleanup.workspace.outcome
        == "confirmed"
    )
    repeated, repeated_code = run_setup_a1(
        second.request,
        mode="apply",
        review_guards=second.review_guards,
        allowed_final_files=tuple(
            row.path for row in second.workspace_observation.binding.file_transitions
        ),
    )
    assert repeated_code != 0 and not repeated.completion_verified


def test_driver_preserves_original_interruption_and_cleanup_prefix(root, monkeypatch):
    from aware_workspace_sdk.architecture_setup import WorkspaceSetupClient

    original, code = run_a1(arguments(root))
    assert code == 0
    cause = RuntimeError("original cause")
    interruption = KeyboardInterrupt("original interruption")

    def interrupt(*args, **kwargs):
        raise interruption from cause

    monkeypatch.setattr(WorkspaceSetupClient, "preview", interrupt)
    with pytest.raises(KeyboardInterrupt) as captured:
        run_setup_a1(
            dataclasses.replace(original.request, issue_request=None),
            mode="preview",
            review_guards=original.review_guards,
        )
    assert captured.value is interruption and interruption.__cause__ is cause
    prefix = interruption.setup_command_evidence
    assert prefix.primary_failure.interruption
    assert (
        prefix.client_cleanup.workspace.outcome
        == prefix.client_cleanup.issue.outcome
        == "confirmed"
    )
    assert not (root / "aware.repo.toml").exists()
    # The Namespace command can render the prefix without turning interruption into success.
    evidence, code = run_a1(arguments(root))
    assert code != 0 and evidence.primary_failure.interruption
