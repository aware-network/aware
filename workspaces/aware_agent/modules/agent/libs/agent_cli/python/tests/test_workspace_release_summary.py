"""Original release observations are independent of operation completeness."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest
from aware_agent_cli import workspace_review as agent
from aware_workspace_runtime.architecture_setup_review import (
    WorkspaceSetupReviewRuntime,
)
from aware_workspace_sdk.architecture_setup_review import WorkspaceSetupReviewClient

ROOT = Path(__file__).resolve().parents[8]
SPEC = importlib.util.spec_from_file_location(
    "original_release_summary_fixture",
    Path(__file__).with_name("test_workspace_review.py"),
)
assert SPEC and SPEC.loader
original = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(original)
repository = original.repository
DIRECTORY = (
    'Private evidence directory release: "confirmed"; family ledger complete: false'
)
SEQUENCE = (
    'Original failed-sequence release: "confirmed"; sequence ledger complete: true'
)


@pytest.fixture
def observed():
    # Hash-bound original source-characterization output, not fabricated SDK
    # evidence or private V2. Copies below test presentation only.
    report = json.loads(
        (
            ROOT / "docs/reports/agent-spent-human-characterization-20261019.json"
        ).read_bytes()
    )
    row = next(r for r in report["cases"] if r["case"] == "human-distinct-reuse")[
        "receipt"
    ]
    raw = Path(row["path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row["sha256"]
    return json.loads(raw)["full"]


def directory(value):
    return value["client_cleanup"]["value"]["directory"]["value"]


def physical_cleanup(value):
    return value["error"]["retention"]["value"]["physical_refusal"]["value"]["cleanup"][
        "value"
    ]


def test_original_returned_rows_do_not_upgrade_ledgers_or_mutate_json(observed):
    before = copy.deepcopy(observed)
    text = agent._summary(observed)
    assert DIRECTORY in text and SEQUENCE in text
    assert "Client cleanup complete: false" in text
    assert 'Evidence retention: "incomplete"; ledger complete: false' in text
    assert "Original Workspace release: unknown/not returned here." in text
    assert "does not establish complete retention" in text
    assert "does not prove spent-reuse causality" in text
    assert "Do not repeat scope/apply" in text
    assert 'Product dispatch for this refused action: "not_invoked"' not in text
    assert observed == before


@pytest.mark.parametrize(
    "missing",
    [
        "client",
        "directory",
        "directory_release",
        "directory_observation",
        "physical",
        "physical_cleanup",
        "sequence",
        "sequence_release",
    ],
)
def test_missing_rows_remain_unknown(observed, missing):
    if missing == "client":
        observed.pop("client_cleanup")
    elif missing == "directory":
        observed["client_cleanup"]["value"].pop("directory")
    elif missing == "directory_release":
        directory(observed).pop("release")
    elif missing == "directory_observation":
        directory(observed).pop("observation")
    elif missing == "physical":
        observed["error"]["retention"]["value"].pop("physical_refusal")
    elif missing == "physical_cleanup":
        observed["error"]["retention"]["value"]["physical_refusal"]["value"].pop(
            "cleanup"
        )
    elif missing == "sequence":
        physical_cleanup(observed).pop("sequence")
    else:
        physical_cleanup(observed)["sequence"]["value"].pop("release")
    before = copy.deepcopy(observed)
    lines = agent._resource_release_summary(observed)
    index = 0 if missing.startswith("directory") or missing == "client" else 1
    assert "unknown/not returned" in lines[index]
    assert observed == before


@pytest.mark.parametrize("field", ["family", "sequence"])
def test_missing_ledger_does_not_discard_returned_release_or_infer_complete(
    observed, field
):
    if field == "family":
        directory(observed)["observation"]["value"].pop("ledger_complete")
    else:
        physical_cleanup(observed)["sequence"]["value"].pop("ledger_complete")
    lines = agent._resource_release_summary(observed)
    text = lines[0 if field == "family" else 1]
    assert 'release: "confirmed"' in text
    assert "ledger complete: unknown/not returned" in text


@pytest.mark.parametrize("release", ["unknown", "not_attempted", "failed"])
def test_nonconfirmed_observation_is_not_upgraded(observed, release):
    directory(observed)["release"] = release
    text = agent._resource_release_summary(observed)[0]
    assert 'release: "' + release + '"' in text
    assert 'release: "confirmed"' not in text


def test_display_escapes_original_values_without_rewriting_them(observed):
    value = "observed\u202e\n\x1b[31m"
    directory(observed)["release"] = value
    text = agent._resource_release_summary(observed)[0]
    assert "\\u202e" in text and "\\n" in text and "\\u001b" in text
    assert "\u202e" not in text and "\x1b" not in text
    assert directory(observed)["release"] == value


@pytest.mark.parametrize("intent", ["apply", "distinct-reuse"])
@pytest.mark.parametrize("json_mode", [False, True], ids=["human", "json-control"])
def test_genuine_collision_preserves_full_payload_exit_and_once_only_behavior(
    repository,
    capsys,
    monkeypatch,
    tmp_path,
    intent,
    json_mode,
):
    root, evidence = repository
    _, review = original.scoped(repository, capsys)
    code, success = original.invoke(
        repository,
        capsys,
        "apply",
        "--reference",
        original.reference(review),
        "--client-intent-id",
        "apply",
        "--accept-reviewed-final-files",
    )
    assert code == 0
    release = success["outcome"]["original_evidence"]["workspace_result"]["value"][
        "release"
    ]
    assert release == "unknown"

    def inventory(base):
        return {
            p.relative_to(base).as_posix(): (p.read_bytes(), p.stat().st_mode & 0o777)
            for p in base.rglob("*")
            if p.is_file()
        }

    before, prior_evidence = inventory(root), inventory(evidence)
    calls = {"payload": 0, "release": 0, "product": 0}
    returned = []
    actual_payload, actual_release = (
        agent.review_payload,
        WorkspaceSetupReviewClient.release_client,
    )

    def observe(args):
        calls["payload"] += 1
        result = actual_payload(args)
        returned.append(result)
        return result

    def cleanup(client):
        calls["release"] += 1
        return actual_release(client)

    def no_product(*args, **kwargs):
        calls["product"] += 1
        raise AssertionError("Reused collision must not dispatch the repository driver")

    monkeypatch.setattr(agent, "review_payload", observe)
    monkeypatch.setattr(WorkspaceSetupReviewClient, "release_client", cleanup)
    monkeypatch.setattr(WorkspaceSetupReviewRuntime, "_run_driver", no_product)
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
            original.reference(review),
            "--client-intent-id",
            intent,
            "--accept-reviewed-final-files",
            *(["--json"] if json_mode else []),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert code == returned[0][1] == 3 and payload == returned[0][0]
    assert calls == {"payload": 1, "release": 1, "product": 0}
    assert payload["status"] == "incomplete"
    assert payload["error"]["code"] == "sequence_request_baseline_changed"
    summary = agent._summary(payload)
    assert DIRECTORY in summary and SEQUENCE in summary
    assert "Client cleanup complete: false" in summary
    assert "Original Workspace release: unknown/not returned here." in summary
    if json_mode:
        assert captured.err == ""
    else:
        assert (
            summary in captured.err
            and "Operation exit before reporting: 3" in captured.err
        )
    assert inventory(root) == before
    current_evidence = inventory(evidence)
    assert all(current_evidence[p] == row for p, row in prior_evidence.items())
    assert (
        success["outcome"]["original_evidence"]["workspace_result"]["value"]["release"]
        == release
    )
    observation = {
        "exit": code,
        "calls": calls,
        "summary": summary,
        "payload": payload,
        "repository_preserved": True,
        "prior_release": release,
        "evidence_added": sorted(current_evidence.keys() - prior_evidence.keys()),
    }
    (tmp_path / "observation.json").write_text(json.dumps(observation, indent=2) + "\n")
    if output := os.environ.get("AWARE_RELEASE_SUMMARY_OUTPUT"):
        (
            Path(output) / (("json-" if json_mode else "human-") + intent + ".json")
        ).write_text(json.dumps(observation, indent=2) + "\n")
