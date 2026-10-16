"""Closed original descriptive values do not mint Issue authority."""

import copy

import pytest
from aware_issue_sdk.workspace_setup_admission import (
    IssueWorkspaceSetupRefusal,
    consume_workspace_setup_admission,
)
from aware_issue_sdk.workspace_setup_admission_codec import (
    IssueWorkspaceSetupValueError,
    issue_setup_value_from_payload,
    issue_setup_value_to_payload,
)
from aware_issue_sdk.workspace_setup_admission_values import IssueWorkspaceSetupRequest


def request():
    return IssueWorkspaceSetupRequest(
        "docs/issues/2026/10/14/fb-2026-10-14-a1.md",
        "sha256:" + "1" * 64,
        None,
        None,
        "intent:codec",
        "workspace_setup_a1_v1",
        "sha256:" + "2" * 64,
    )


def test_roundtrip_remains_data_only():
    original = request()
    decoded = issue_setup_value_from_payload(
        IssueWorkspaceSetupRequest, issue_setup_value_to_payload(original)
    )
    assert decoded == original and decoded is not original
    with pytest.raises(IssueWorkspaceSetupRefusal):
        consume_workspace_setup_admission(decoded, expected_binding=object())


@pytest.mark.parametrize(
    "field,value",
    [
        ("issue_ref", "../escape"),
        ("issue_ref", "/absolute"),
        ("expected_issue_source_sha256", "x"),
        ("actor_ref", "actor:unpaired"),
        ("intent", "other"),
        ("client_intent_id", True),
    ],
)
def test_scalar_and_pair_refusals(field, value):
    payload = copy.deepcopy(issue_setup_value_to_payload(request()))
    payload["value"][field] = value
    with pytest.raises((IssueWorkspaceSetupValueError, ValueError)):
        issue_setup_value_from_payload(IssueWorkspaceSetupRequest, payload)


def test_closed_wrappers_and_members():
    payload = issue_setup_value_to_payload(request())
    payload["value"]["approved"] = True
    with pytest.raises(IssueWorkspaceSetupValueError):
        issue_setup_value_from_payload(IssueWorkspaceSetupRequest, payload)


def test_decode_uses_original_slots_without_constructor_dispatch(monkeypatch):
    payload = issue_setup_value_to_payload(request())
    calls = []
    monkeypatch.setattr(
        IssueWorkspaceSetupRequest, "__init__", lambda *a, **k: calls.append(True)
    )
    decoded = issue_setup_value_from_payload(IssueWorkspaceSetupRequest, payload)
    assert not calls and decoded.client_intent_id == "intent:codec"
