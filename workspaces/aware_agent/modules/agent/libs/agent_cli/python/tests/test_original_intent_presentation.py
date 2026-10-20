"""Original owner values and genuine source flows; no installed/customer claim."""

from __future__ import annotations

import argparse
import ast
import copy
import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from aware_agent_cli import workspace_review as agent
from aware_workspace_sdk import architecture_setup_review_values as v
from aware_workspace_sdk.architecture_setup_review import (
    WorkspaceSetupReviewClient,
    concise_result,
)
from aware_workspace_sdk.architecture_setup_review_codec import (
    review_value_from_json,
    review_value_to_payload,
)

SPEC = importlib.util.spec_from_file_location(
    "original_intent_fixture", Path(__file__).with_name("test_workspace_review.py")
)
assert SPEC and SPEC.loader
original = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(original)
repository = original.repository
AVAILABLE = "Original retained intent reference candidate (exact SDK JSON; pairing/action not validated by this display):"
UNAVAILABLE = "Original retained intent reference: unavailable in this result."
AMBIGUOUS = "Original retained intent references disagree"


def values():
    target = v.SetupTarget(
        "/diagnostic-target",
        "fb/2026-10-20/diagnostic",
        "docs/issues/diagnostic.md",
        "aware.protocol.toml",
    )

    def ref(locator, kind):
        return v.SetupEvidenceRef(
            "/diagnostic-evidence",
            v.DirectoryIdentity(1, 2),
            locator,
            v.REVIEW_SCHEMA_IDS[kind],
            "sha256:" + "a" * 64,
            12,
            "b" * 64,
            target,
        )

    intent = ref("original-intent.json", v.SetupDispatchIntent)
    outcome_ref = ref("original-outcome.json", v.SetupOutcomeRecord)
    retention = v.RetentionEvidence(
        "published", intent, None, (), (), None, True, (), None
    )
    outcome = v.SetupCommandOutcome(
        "apply_completed", None, outcome_ref, retention, (), False
    )
    return target, intent, retention, outcome


def payload(source="outcome"):
    target, intent, retention, outcome = values()
    result = {
        "action": "apply",
        "status": "completed",
        "stage": "apply",
        "authorizes_retry": False,
        "reference": review_value_to_payload(outcome.reference),
    }
    if source == "outcome":
        result["outcome"] = agent._outcome_payload(outcome)
        result["result"] = review_value_to_payload(concise_result(outcome))
    else:
        failure = v.SetupReviewFailure(
            "original_failure",
            "apply",
            target,
            outcome if source == "error.outcome" else None,
            None,
            replace(
                retention,
                status="incomplete",
                ledger_complete=False,
                intent_ref=None if source == "error.outcome" else intent,
            ),
            None,
            False,
        )
        result["status"] = "incomplete"
        result["error"] = agent._error_payload(
            v.SetupReviewError("original_failure", failure=failure)
        )
    return result


def line_reference(text):
    return text.split(AVAILABLE + "\n", 1)[1].splitlines()[0]


@pytest.mark.parametrize("source", ["outcome", "error", "error.outcome"])
def test_declared_original_candidate_is_exact_not_validated(source):
    result = payload(source)
    before = copy.deepcopy(result)
    text = agent._summary(result)
    assert (
        review_value_from_json(v.SetupEvidenceRef, line_reference(text)) == values()[1]
    )
    assert source + ".retention.value.intent_ref" in text
    assert "pairing/action not validated" in text
    assert "saved original second-review" in text
    assert "never the saved apply result" in text
    assert "no completion, current admission or retry authority" in text
    assert result == before


@pytest.mark.parametrize(
    "missing", ["absent", "null", "unrelated", "top_level", "concise"]
)
def test_unavailable_is_not_negative_admission_or_reference_discovery(missing):
    result = payload()
    retention = result["outcome"]["retention"]["value"]
    if missing == "absent":
        retention.pop("intent_ref")
    else:
        retention["intent_ref"] = None
    if missing == "unrelated":
        result["arbitrary"] = {
            "retention": {"value": {"intent_ref": review_value_to_payload(values()[1])}}
        }
    elif missing == "top_level":
        result["reference"] = review_value_to_payload(values()[1])
    elif missing == "concise":
        result["unused_concise_reference"] = review_value_to_payload(values()[1])
    lines, error = agent._intent_reference_lines(result)
    text = "\n".join(lines)
    assert error is None and UNAVAILABLE in text and AVAILABLE not in text
    assert "not proof of non-admission, non-dispatch or safe retry" in text
    assert "never repeat apply" in text


def test_equal_candidates_collapse_but_keep_all_origins():
    result = payload()
    error = payload("error.outcome")["error"]
    error["retention"]["value"]["intent_ref"] = review_value_to_payload(values()[1])
    result["error"] = error
    text = agent._summary(result)
    assert text.count(AVAILABLE) == 1
    origins = text.split("Original source fields: ", 1)[1].splitlines()[0]
    assert set(origins.split(", ")) == {
        "outcome.retention.value.intent_ref",
        "error.retention.value.intent_ref",
        "error.outcome.retention.value.intent_ref",
    }


def test_conflicting_candidates_preserve_both_without_selecting_pair():
    result = payload()
    result["error"] = payload("error")["error"]
    other = replace(values()[1], locator="different-original.json")
    result["error"]["retention"]["value"]["intent_ref"] = review_value_to_payload(other)
    before = copy.deepcopy(result)
    text = agent._summary(result)
    assert AMBIGUOUS in text and AVAILABLE not in text
    assert "original-intent.json" in text and "different-original.json" in text
    assert "An explicit observe-admission" not in text
    assert "No pair is selected" in text and result == before


@pytest.mark.parametrize("bad", [{}, "reference-not-object", 7])
def test_malformed_candidate_is_not_null_or_fallback_selection(bad):
    result = payload()
    result["error"] = payload("error")["error"]
    result["error"]["retention"]["value"]["intent_ref"] = bad
    before = copy.deepcopy(result)
    with pytest.raises(agent._IntentPresentationError) as caught:
        agent._summary(result)
    assert caught.value.__cause__ is caught.value.original
    assert "presentation: incomplete" in caught.value.summary
    assert (
        UNAVAILABLE not in caught.value.summary
        and AVAILABLE not in caught.value.summary
    )
    assert "Original product outcome returned: apply_completed" in caught.value.summary
    assert result == before


def test_terminal_escaped_json_preserves_unicode_original_values():
    result = payload()
    intent = replace(values()[1], locator="intent-\u202e-\U0001f680.json")
    result["outcome"]["retention"]["value"]["intent_ref"] = review_value_to_payload(
        intent
    )
    text = agent._summary(result)
    assert "\u202e" not in text and "\\u202e" in text
    assert review_value_from_json(v.SetupEvidenceRef, line_reference(text)) == intent


def test_reference_kind_does_not_become_apply_or_pair_validation():
    result = payload()
    candidate = replace(
        values()[1], record_contract=v.REVIEW_SCHEMA_IDS[v.SetupReviewRecord]
    )
    result["outcome"]["retention"]["value"]["intent_ref"] = review_value_to_payload(
        candidate
    )
    text = agent._summary(result)
    assert review_value_from_json(v.SetupEvidenceRef, line_reference(text)) == candidate
    assert "pairing/action not validated" in text
    assert "the original owner validates all joins" in text


@pytest.mark.parametrize("source", ["outcome", "error", "error.outcome"])
@pytest.mark.parametrize("code", [0, 3, 130])
def test_json_bypasses_human_logic_and_keeps_original_payload_and_exit(
    monkeypatch, capsys, source, code
):
    result = payload(source)
    before = copy.deepcopy(result)
    calls = []

    def operation(args):
        calls.append("original_payload")
        return result, code, None

    monkeypatch.setattr(agent, "review_payload", operation)
    monkeypatch.setattr(
        agent,
        "_intent_reference_lines",
        lambda p: pytest.fail("JSON invoked human presentation"),
    )
    actual = agent._handle(
        SimpleNamespace(args=argparse.Namespace(json=True, focus=None))
    )
    output = capsys.readouterr()
    assert actual == code and calls == ["original_payload"]
    assert output.err == "" and json.loads(output.out) == before == result


@pytest.mark.parametrize("interruption", [False, True])
@pytest.mark.parametrize("primary", [0, 2, 3, 130])
def test_presentation_failure_keeps_full_primary_and_normal_exit_boundaries(
    monkeypatch, capsys, interruption, primary
):
    import aware_workspace_sdk.architecture_setup_review_codec as codec

    result = payload()
    before = copy.deepcopy(result)
    original_error = (
        KeyboardInterrupt("presentation interrupted")
        if interruption
        else ValueError("codec unavailable")
    )
    calls = []

    def failed(*args, **kwargs):
        calls.append("codec")
        raise original_error

    monkeypatch.setattr(codec, "review_value_from_payload", failed)
    monkeypatch.setattr(agent, "review_payload", lambda args: (result, primary, None))
    actual = agent._handle(
        SimpleNamespace(args=argparse.Namespace(json=False, focus=None))
    )
    output = capsys.readouterr()
    assert actual == (130 if interruption or primary == 130 else 3)
    assert calls == ["codec"]
    assert json.loads(output.out) == result == before
    assert f"Original operation exit: {primary}" in output.err
    assert "presentation: incomplete" in output.err


def test_candidate_display_does_not_acquire_provider_or_observe(monkeypatch):
    monkeypatch.setattr(
        WorkspaceSetupReviewClient,
        "filesystem",
        lambda **kwargs: pytest.fail("Provider acquired by presentation"),
    )
    monkeypatch.setattr(
        WorkspaceSetupReviewClient,
        "observe_action_admission",
        lambda *args: pytest.fail("Automatic observation"),
    )
    assert AVAILABLE in agent._summary(payload())


@pytest.mark.parametrize("code", [0, 2, 3, 130])
def test_missing_candidate_preserves_original_human_exit(monkeypatch, capsys, code):
    result = payload()
    result["outcome"]["retention"]["value"]["intent_ref"] = None
    before = copy.deepcopy(result)
    monkeypatch.setattr(agent, "review_payload", lambda args: (result, code, None))
    assert (
        agent._handle(SimpleNamespace(args=argparse.Namespace(json=False, focus=None)))
        == code
    )
    output = capsys.readouterr()
    assert UNAVAILABLE in output.out and result == before


def test_only_human_summary_and_reporting_functions_change():
    path = "workspaces/aware_agent/modules/agent/libs/agent_cli/python/aware_agent_cli/workspace_review.py"
    before = ast.parse(
        subprocess.check_output(
            ["git", "show", "3b2c3811abef431045ac41e4f17f357a1a4a3e43:" + path],
            cwd=original.ROOT,
        )
    )
    after = ast.parse(Path(agent.__file__).read_bytes())
    old = {
        n.name: ast.dump(n, include_attributes=False)
        for n in before.body
        if isinstance(n, (ast.FunctionDef, ast.ClassDef))
    }
    new = {
        n.name: ast.dump(n, include_attributes=False)
        for n in after.body
        if isinstance(n, (ast.FunctionDef, ast.ClassDef))
    }
    assert {name for name in old if old[name] != new[name]} == {"_summary", "_handle"}
    assert set(new) - set(old) == {
        "_intent_reference_lines",
        "_IntentPresentationError",
    }


def test_genuine_apply_candidate_pairs_only_with_original_second_review(
    repository, capsys, monkeypatch
):
    _, second = original.scoped(repository, capsys)
    returned = []
    actual = agent.review_payload

    def retained(args):
        result = actual(args)
        returned.append(result)
        return result

    monkeypatch.setattr(agent, "review_payload", retained)
    root, evidence = repository
    code = original.client.main(
        [
            "workspace",
            "review",
            "apply",
            "--repository-root",
            str(root),
            "--evidence-root",
            str(evidence),
            "--reference",
            original.reference(second),
            "--client-intent-id",
            "genuine-original-intent",
            "--accept-reviewed-final-files",
        ]
    )
    output = capsys.readouterr()
    assert code == 0 and output.err == ""
    assert len(returned) == 1 and (root / "aware.repo.toml").is_file()
    frame = returned[0][0]
    candidate = line_reference(output.out)
    assert json.loads(candidate) == frame["outcome"]["retention"]["value"]["intent_ref"]
    assert 'Original Workspace release: "unknown"' in output.out
    assert "Client cleanup complete: true" in output.out
    argv = [
        "workspace",
        "review",
        "observe-admission",
        "--repository-root",
        str(root),
        "--evidence-root",
        str(evidence),
        "--intent-reference",
        candidate,
        "--json",
    ]
    # This additional explicit test invocation is not performed by presentation.
    assert original.client.main([*argv, "--reference", original.reference(second)]) == 0
    observed = json.loads(capsys.readouterr().out)
    assert (
        observed["action_observation"]["historical_driver_outcome"] == "not_established"
    )
    assert observed["action_observation"]["authorizes_retry"] is False
    assert original.client.main([*argv, "--reference", original.reference(frame)]) != 0
    refused = json.loads(capsys.readouterr().out)
    assert "action_observation" not in refused


@pytest.mark.parametrize("interruption", [False, True])
def test_genuine_capture_failure_keeps_effects_intent_and_original_cleanup(
    repository, capsys, monkeypatch, interruption
):
    from aware_workspace_fs_adapter.architecture_setup_review import (
        FilesystemSetupReview,
    )

    _, second = original.scoped(repository, capsys)
    write = FilesystemSetupReview.write_capture
    calls = []

    def fail(owner, raw, **kwargs):
        if kwargs.get("kind") == "command_v1":
            calls.append("capture")
            if interruption:
                raise KeyboardInterrupt("after genuine effects")
            raise OSError("after genuine effects")
        return write(owner, raw, **kwargs)

    monkeypatch.setattr(FilesystemSetupReview, "write_capture", fail)
    root, evidence = repository
    code = original.client.main(
        [
            "workspace",
            "review",
            "apply",
            "--repository-root",
            str(root),
            "--evidence-root",
            str(evidence),
            "--reference",
            original.reference(second),
            "--client-intent-id",
            "capture-original-intent",
            "--accept-reviewed-final-files",
        ]
    )
    output = capsys.readouterr()
    frame = json.loads(output.out)
    assert code == (130 if interruption else 3)
    assert calls == ["capture"] and (root / "aware.repo.toml").is_file()
    assert frame["error"]["outcome"]["original_evidence"]["completion_verified"]
    assert "Original product outcome returned: apply_completed" in output.err
    assert AVAILABLE in output.err
    assert frame["client_cleanup"]["value"]["ledger_complete"]


@pytest.mark.parametrize("channel", ["stdout", "stderr"])
@pytest.mark.parametrize("code", [3, 130])
def test_real_closed_pipe_keeps_failure_exit_and_surviving_evidence(channel, code):
    script = r"""
import argparse,importlib.util,os,sys
from types import SimpleNamespace
from aware_agent_cli import workspace_review as agent
spec=importlib.util.spec_from_file_location('intent_values_fixture',sys.argv[1])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
value=module.payload()
if int(sys.argv[3])==130:
    import aware_workspace_sdk.architecture_setup_review_codec as codec
    def interrupted(*args,**kwargs):raise KeyboardInterrupt('presentation interrupted')
    codec.review_value_from_payload=interrupted
else:
    value['outcome']['retention']['value']['intent_ref']={}
agent.review_payload=lambda args:(value,0,None)
read_fd,write_fd=os.pipe();os.close(read_fd)
setattr(sys,sys.argv[2],os.fdopen(write_fd,'w'))
raise SystemExit(agent._handle(SimpleNamespace(args=argparse.Namespace(json=False,focus=None))))
"""
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            script,
            str(Path(__file__).resolve()),
            channel,
            str(code),
        ],
        text=True,
        capture_output=True,
        env=os.environ.copy(),
        timeout=30,
        check=False,
    )
    assert result.returncode == code, result
    remaining = result.stderr if channel == "stdout" else result.stdout
    assert "apply_completed" in remaining
