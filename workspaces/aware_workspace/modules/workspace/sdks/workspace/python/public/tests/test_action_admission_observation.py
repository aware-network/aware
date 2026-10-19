"""Actual original observer joins, custody, unknowns and failure boundaries."""

from __future__ import annotations

import asyncio
import dataclasses
import hashlib
import importlib.util
import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from aware_workspace_sdk import architecture_setup_review_values as v
from aware_workspace_sdk.architecture_setup_review import WorkspaceSetupReviewClient
from aware_workspace_sdk.architecture_setup_review_codec import (
    SetupReviewValueError,
    review_value_from_json,
    review_value_to_json,
    review_value_to_payload,
)

SPEC = importlib.util.spec_from_file_location(
    "original_action_observer_fixture",
    Path(__file__).with_name("test_architecture_setup_review.py"),
)
assert SPEC and SPEC.loader
ORIGINAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORIGINAL)
context = ORIGINAL.context


def ready(context):
    repository, evidence, client, _, _ = context
    first, second, inputs = ORIGINAL.apply_ready(context)
    result = client.apply_reviewed(inputs, client_intent_id="intent:apply")
    request = v.SetupActionAdmissionRequest(
        second.reference.target, "apply", second.reference, result.retention.intent_ref
    )
    return repository, evidence, first, second, inputs, result, request


def observer(repository, evidence, *, execution="codex-independent-observer"):
    return WorkspaceSetupReviewClient.filesystem(
        repository_root=repository,
        evidence_root=evidence,
        execution_id=execution,
        authority_manifest_locator="aware.protocol.toml",
    )


def inventory(root):
    return {
        str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mode)
        for p in root.rglob("*")
        if p.is_file()
    }


def assert_view(value, request):
    assert type(value) is v.SetupActionAdmissionObservation
    assert value.observation == "validated_retained_intent"
    assert value.product_dispatch_this_observation == "not_invoked"
    assert value.historical_driver_outcome == "not_established"
    assert value.authorizes_retry is False
    assert value.intent.review == value.review_ref == request.review_ref
    assert value.intent_ref == request.intent_ref
    assert value.intent.inputs_ref == value.inputs_ref
    assert value.inputs.decision.review == value.review_ref
    assert value.intent.execution_ref == value.review.request.execution_ref
    assert value.private_observation.ledger_complete
    assert value.reads and all(
        row.original.cleanup.outcome == "closed" for row in value.reads
    )


def forbid_writes(client, monkeypatch):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append("unexpected_dispatch")
        raise AssertionError(
            "Observer must not write, dispatch or revalidate Issue currentness"
        )

    for name in ("_run_driver", "_intent", "_reference_for", "_current_issue"):
        monkeypatch.setattr(client._runtime, name, forbidden)
    monkeypatch.setattr(client._runtime.store, "write_metadata", forbidden)
    monkeypatch.setattr(client._runtime.store, "write_capture", forbidden)
    return calls


@pytest.mark.parametrize("changed_issue", [False, True])
def test_actual_observer_is_historical_read_only_and_never_completion(
    context, monkeypatch, changed_issue
):
    repository, evidence, _, _, _, result, request = ready(context)
    if changed_issue:
        path = repository / ORIGINAL.ISSUE
        path.write_bytes(path.read_bytes() + b"\n# later explicit change\n")
    before = inventory(repository), inventory(evidence)
    with observer(repository, evidence) as client:
        calls = forbid_writes(client, monkeypatch)
        value = client.observe_action_admission(request)
        assert_view(value, request)
        assert value.intent.execution_ref != client._runtime.execution
        assert not calls
        cleanup = client.release_client()
        assert cleanup.ledger_complete and cleanup.directory.release == "confirmed"
        assert client.release_client() is cleanup
    assert before == (inventory(repository), inventory(evidence))
    assert result.original_evidence.workspace_result.release == "unknown"
    with pytest.raises(dataclasses.FrozenInstanceError):
        value.authorizes_retry = True
    with pytest.raises(SetupReviewValueError, match="serializable_original"):
        review_value_to_payload(value)


def test_actual_observer_runs_in_fresh_process(context):
    repository, evidence, _, _, _, _, request = ready(context)
    before = inventory(repository), inventory(evidence)
    script = """
import json,sys
from pathlib import Path
from aware_workspace_sdk import architecture_setup_review_values as v
from aware_workspace_sdk.architecture_setup_review import WorkspaceSetupReviewClient
from aware_workspace_sdk.architecture_setup_review_codec import review_value_from_json
p=json.load(sys.stdin)
request=review_value_from_json(v.SetupActionAdmissionRequest,p['request'])
with WorkspaceSetupReviewClient.filesystem(repository_root=Path(p['repository']),evidence_root=Path(p['evidence']),execution_id='codex-fresh-action-observer',authority_manifest_locator='aware.protocol.toml') as c:
    value=c.observe_action_admission(request)
    assert value.observation=='validated_retained_intent'
    assert value.product_dispatch_this_observation=='not_invoked'
    assert value.historical_driver_outcome=='not_established'
    assert value.authorizes_retry is False
    assert c.release_client().ledger_complete
print('original-observer-ok')
"""
    child = subprocess.run(
        [sys.executable, "-B", "-c", script],
        input=json.dumps(
            {
                "repository": str(repository),
                "evidence": str(evidence),
                "request": review_value_to_json(request),
            }
        ),
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert child.returncode == 0, child.stderr
    assert child.stdout == "original-observer-ok\n"
    assert before == (inventory(repository), inventory(evidence))


@pytest.mark.parametrize("lost_after_dispatch", [False, True])
def test_intent_without_outcome_is_not_completion(
    context, monkeypatch, lost_after_dispatch
):
    repository, evidence, client, _, _ = context
    _, second, inputs = ORIGINAL.apply_ready(context)
    original = client._runtime._run_driver

    def missing_return(*args, **kwargs):
        if lost_after_dispatch:
            original(*args, **kwargs)
        raise RuntimeError("controlled unavailable driver return")

    monkeypatch.setattr(client._runtime, "_run_driver", missing_return)
    with pytest.raises(v.SetupReviewError) as caught:
        client.apply_reviewed(inputs, client_intent_id="intent:apply")
    request = v.SetupActionAdmissionRequest(
        second.reference.target,
        "apply",
        second.reference,
        caught.value.failure.retention.intent_ref,
    )
    assert not (evidence / f"a1-{inputs.reference.attempt_ref}-outcome.json").exists()
    with observer(repository, evidence) as fresh:
        assert_view(fresh.observe_action_admission(request), request)
    assert (repository / "aware.repo.toml").exists() is lost_after_dispatch


def rewritten(reference, value):
    """Corrupt only a disposable exact record and supply its real changed digest."""
    raw = review_value_to_json(value).encode()
    (Path(reference.evidence_root) / reference.locator).write_bytes(raw)
    return dataclasses.replace(
        reference,
        record_bytes=len(raw),
        record_sha256="sha256:" + hashlib.sha256(raw).hexdigest(),
    )


@pytest.mark.parametrize(
    "fault",
    [
        "action",
        "review",
        "execution",
        "intent",
        "key",
        "attempt",
        "input_kind",
        "input_attempt",
        "input_target",
        "input_root",
    ],
)
def test_intent_joins_refuse_even_with_valid_record_hash(context, monkeypatch, fault):
    repository, evidence, first, _, _, _, request = ready(context)
    with observer(repository, evidence) as client:
        raw = client.read_evidence(request.intent_ref, expected_target=request.target)
        intent = review_value_from_json(v.SetupDispatchIntent, raw.raw_bytes.decode())
        if fault == "action":
            intent = dataclasses.replace(intent, action="scope")
        elif fault == "review":
            intent = dataclasses.replace(intent, review=first.reference)
        elif fault == "execution":
            intent = dataclasses.replace(intent, execution_ref="codex-substituted")
        elif fault == "intent":
            intent = dataclasses.replace(intent, client_intent_id="intent:substituted")
        elif fault == "key":
            intent = dataclasses.replace(intent, action_key="sha256:" + "0" * 64)
        elif fault == "input_kind":
            intent = dataclasses.replace(
                intent,
                inputs_ref=dataclasses.replace(
                    intent.inputs_ref,
                    record_contract=v.REVIEW_SCHEMA_IDS[v.SetupReviewRecord],
                ),
            )
        elif fault == "input_attempt":
            intent = dataclasses.replace(
                intent,
                inputs_ref=dataclasses.replace(intent.inputs_ref, attempt_ref="0" * 64),
            )
        elif fault == "input_target":
            intent = dataclasses.replace(
                intent,
                inputs_ref=dataclasses.replace(
                    intent.inputs_ref,
                    target=dataclasses.replace(request.target, issue_tag="fb/foreign"),
                ),
            )
        elif fault == "input_root":
            intent = dataclasses.replace(
                intent,
                inputs_ref=dataclasses.replace(
                    intent.inputs_ref, evidence_root=str(evidence.parent)
                ),
            )
        reference = rewritten(request.intent_ref, intent)
        if fault == "attempt":
            reference = dataclasses.replace(reference, attempt_ref="0" * 64)
        calls = forbid_writes(client, monkeypatch)
        with pytest.raises(v.SetupReviewError) as caught:
            client.observe_action_admission(
                dataclasses.replace(request, intent_ref=reference)
            )
        assert caught.value.failure.phase == "observe_action_admission"
        assert (
            caught.value.failure.outcome is None
            and caught.value.failure.refusal is None
        )
        assert not calls


@pytest.mark.parametrize(
    "fault",
    [
        "decision_review",
        "decision_execution",
        "decision_intent",
        "guards",
        "request",
        "final_files",
    ],
)
def test_original_input_correspondence_is_checked(context, monkeypatch, fault):
    repository, evidence, first, _, _, _, request = ready(context)
    with observer(repository, evidence) as client:
        intent = review_value_from_json(
            v.SetupDispatchIntent,
            client.read_evidence(
                request.intent_ref, expected_target=request.target
            ).raw_bytes.decode(),
        )
        inputs = review_value_from_json(
            v.SetupApplyInputRecord,
            client.read_evidence(
                intent.inputs_ref, expected_target=request.target
            ).raw_bytes.decode(),
        )
        if fault == "decision_review":
            inputs = dataclasses.replace(
                inputs,
                decision=dataclasses.replace(inputs.decision, review=first.reference),
            )
        elif fault == "decision_execution":
            inputs = dataclasses.replace(
                inputs,
                decision=dataclasses.replace(
                    inputs.decision, execution_ref="codex-foreign"
                ),
            )
        elif fault == "decision_intent":
            inputs = dataclasses.replace(
                inputs,
                decision=dataclasses.replace(
                    inputs.decision, client_intent_id="intent:foreign"
                ),
            )
        elif fault == "guards":
            inputs = dataclasses.replace(
                inputs,
                review_guards=dataclasses.replace(
                    inputs.review_guards, plan_sha256="sha256:" + "0" * 64
                ),
            )
        elif fault == "request":
            inputs = dataclasses.replace(
                inputs,
                request=dataclasses.replace(
                    inputs.request, client_intent_id="intent:foreign"
                ),
            )
        else:
            inputs = dataclasses.replace(inputs, final_files=("different.py",))
        input_ref = rewritten(intent.inputs_ref, inputs)
        intent_ref = rewritten(
            request.intent_ref, dataclasses.replace(intent, inputs_ref=input_ref)
        )
        calls = forbid_writes(client, monkeypatch)
        with pytest.raises(v.SetupReviewError):
            client.observe_action_admission(
                dataclasses.replace(request, intent_ref=intent_ref)
            )
        assert not calls


@pytest.mark.parametrize(
    "fault",
    [
        "scope",
        "wrong_target",
        "wrong_contract",
        "foreign_root",
        "foreign_identity",
        "foreign_object",
    ],
)
def test_request_and_reference_refusals(context, monkeypatch, fault):
    repository, evidence, _, _, _, _, request = ready(context)
    if fault == "scope":
        request = dataclasses.replace(request, action="scope")
    elif fault == "wrong_target":
        request = dataclasses.replace(
            request, target=dataclasses.replace(request.target, issue_tag="fb/foreign")
        )
    elif fault == "wrong_contract":
        request = dataclasses.replace(
            request,
            intent_ref=dataclasses.replace(
                request.intent_ref,
                record_contract=v.REVIEW_SCHEMA_IDS[v.SetupOutcomeRecord],
            ),
        )
    elif fault == "foreign_root":
        request = dataclasses.replace(
            request,
            intent_ref=dataclasses.replace(
                request.intent_ref, evidence_root=str(evidence.parent)
            ),
        )
    elif fault == "foreign_identity":
        request = dataclasses.replace(
            request,
            review_ref=dataclasses.replace(
                request.review_ref,
                root_identity=dataclasses.replace(
                    request.review_ref.root_identity, inode=0
                ),
            ),
        )
    else:
        request = {"target": request.target}
    with observer(repository, evidence) as client:
        calls = forbid_writes(client, monkeypatch)
        with pytest.raises(v.SetupReviewError):
            client.observe_action_admission(request)
        assert not calls


@pytest.mark.parametrize("record", ["review_ref", "intent_ref", "inputs_ref"])
@pytest.mark.parametrize("fault", ["missing", "changed", "cancel", "lost_return"])
def test_each_read_boundary_retains_failures_and_interruptions(
    context, monkeypatch, record, fault
):
    repository, evidence, _, _, inputs, _, request = ready(context)
    reference = inputs.reference if record == "inputs_ref" else getattr(request, record)
    path = evidence / reference.locator
    if fault == "missing":
        path.unlink()
    elif fault == "changed":
        path.write_bytes(b"changed during read qualification")
    with observer(repository, evidence) as client:
        calls = forbid_writes(client, monkeypatch)
        original = client._runtime.store.read
        interruption = asyncio.CancelledError("original observer interruption")
        reached = []

        def injected(name, **kwargs):
            if name == reference.locator and fault in ("cancel", "lost_return"):
                reached.append(name)
                if fault == "lost_return":
                    original(name, **kwargs)
                if fault == "cancel":
                    raise interruption
                raise RuntimeError("original read return unavailable")
            return original(name, **kwargs)

        monkeypatch.setattr(client._runtime.store, "read", injected)
        expected = asyncio.CancelledError if fault == "cancel" else v.SetupReviewError
        with pytest.raises(expected) as caught:
            client.observe_action_admission(request)
        if fault == "cancel":
            assert caught.value is interruption
            failure = caught.value.setup_review_failure
            assert failure.interruption
        else:
            failure = caught.value.failure
        assert failure.phase == "observe_action_admission"
        assert failure.outcome is None and failure.refusal is None
        assert failure.retention.status == "incomplete"
        if fault in ("cancel", "lost_return"):
            assert reached == [reference.locator]
        assert not calls


def test_reentrant_and_foreign_thread_refusal_do_not_borrow_active_observation(
    context, monkeypatch
):
    repository, evidence, _, _, _, _, request = ready(context)
    with observer(repository, evidence) as client:
        original = client._runtime.store.read
        refused = []

        def read(name, **kwargs):
            if not refused:
                with pytest.raises(v.SetupReviewError) as error:
                    client.observe_action_admission(request)
                assert error.value.failure.retention.status == "not_attempted"
                assert not error.value.failure.reads
                refused.append(error.value.code)
            return original(name, **kwargs)

        monkeypatch.setattr(client._runtime.store, "read", read)
        assert_view(client.observe_action_admission(request), request)
        assert refused == ["review_action_in_progress"]
        values = []

        def foreign():
            try:
                client.observe_action_admission(request)
            except v.SetupReviewError as error:
                values.append(error)

        thread = threading.Thread(target=foreign)
        thread.start()
        thread.join(timeout=10)
        assert not thread.is_alive() and len(values) == 1
        assert values[0].code == "original_review_execution_required"
        assert not values[0].failure.reads


def test_observation_cannot_become_live_inputs_or_reset_a_spent_action(context):
    repository, evidence, _, _, inputs, _, request = ready(context)
    with observer(repository, evidence) as client:
        value = client.observe_action_admission(request)
        with pytest.raises(
            v.SetupReviewError, match="original_unconsumed_apply_inputs_required"
        ):
            client.apply_reviewed(value, client_intent_id="intent:apply")
        with pytest.raises(
            v.SetupReviewError, match="original_unconsumed_apply_inputs_required"
        ):
            client.apply_reviewed(inputs, client_intent_id="intent:apply")


def test_input_change_between_original_reads_refuses(context, monkeypatch):
    repository, evidence, _, _, inputs, _, request = ready(context)
    with observer(repository, evidence) as client:
        original = client._runtime.store.read
        changed = threading.Event()
        failures = []

        def change():
            try:
                (evidence / inputs.reference.locator).write_bytes(
                    b"concurrent changed history"
                )
            except OSError as error:
                failures.append(error)
            finally:
                changed.set()

        def read(name, **kwargs):
            raw = original(name, **kwargs)
            if name == request.intent_ref.locator:
                thread = threading.Thread(target=change)
                thread.start()
                assert changed.wait(timeout=10)
                thread.join(timeout=10)
                assert not thread.is_alive() and not failures
            return raw

        monkeypatch.setattr(client._runtime.store, "read", read)
        with pytest.raises(v.SetupReviewError) as caught:
            client.observe_action_admission(request)
        assert caught.value.failure.phase == "observe_action_admission"
        assert caught.value.failure.outcome is None


def test_prior_observation_does_not_bypass_later_atomic_intent_collision(
    context, monkeypatch
):
    repository, evidence, _, _, _, _, request = ready(context)
    with observer(repository, evidence, execution=ORIGINAL.EXECUTION) as client:
        assert_view(client.observe_action_admission(request), request)
        calls = []

        def forbidden(*args, **kwargs):
            calls.append("driver")
            raise AssertionError("A prior observation cannot restore apply admission")

        monkeypatch.setattr(client._runtime, "_run_driver", forbidden)
        inputs = client.record_review_decision(
            request.review_ref,
            decision=v.SetupApplyDecision(
                request.review_ref,
                "accept_reviewed_final_files",
                ORIGINAL.EXECUTION,
                "intent:after-observation",
            ),
        )
        with pytest.raises(v.SetupReviewError) as caught:
            client.apply_reviewed(inputs, client_intent_id="intent:after-observation")
        assert caught.value.code == "sequence_request_baseline_changed"
        assert caught.value.failure.phase == "apply_reviewed"
        assert not caught.value.failure.retention.ledger_complete
        assert not calls


@pytest.mark.parametrize("fault", ["read_cleanup", "root_drift", "budget"])
def test_original_cleanup_root_and_budget_limits_remain_binding(
    context, monkeypatch, fault
):
    from aware_file_system import private_directory as private

    repository, evidence, _, _, _, _, request = ready(context)
    with observer(repository, evidence) as client:
        original = private.observe_private_directory_file
        calls = []

        def actual_read(*args, **kwargs):
            result = original(*args, **kwargs)
            calls.append(kwargs["path"])
            if fault == "read_cleanup":
                return dataclasses.replace(
                    result,
                    directory_after=dataclasses.replace(
                        result.directory_after, ledger_complete=False
                    ),
                )
            if fault == "root_drift" and kwargs["path"] == request.intent_ref.locator:
                evidence.chmod(0o755)
            if fault == "budget":
                client._runtime.store.logical = 64 * 1024 * 1024
            return result

        monkeypatch.setattr(private, "observe_private_directory_file", actual_read)
        try:
            with pytest.raises(v.SetupReviewError) as error:
                client.observe_action_admission(request)
            assert error.value.failure.outcome is None
            assert error.value.failure.retention.status == "incomplete"
            assert calls
        finally:
            evidence.chmod(0o700)


def test_request_codec_is_closed_and_view_is_nonwire(context):
    _, _, _, _, _, _, request = ready(context)
    assert (
        review_value_from_json(
            v.SetupActionAdmissionRequest, review_value_to_json(request)
        )
        == request
    )
    payload = review_value_to_payload(request)
    for name in tuple(payload["value"]):
        changed = {
            **payload,
            "value": {k: x for k, x in payload["value"].items() if k != name},
        }
        with pytest.raises(SetupReviewValueError):
            review_value_from_json(v.SetupActionAdmissionRequest, json.dumps(changed))
    for change in (
        {**payload, "contract": "wrong"},
        {**payload, "value": {**payload["value"], "retry": True}},
    ):
        with pytest.raises(SetupReviewValueError):
            review_value_from_json(v.SetupActionAdmissionRequest, json.dumps(change))
    with pytest.raises(SetupReviewValueError):
        review_value_from_json(v.SetupActionAdmissionObservation, "{}")
