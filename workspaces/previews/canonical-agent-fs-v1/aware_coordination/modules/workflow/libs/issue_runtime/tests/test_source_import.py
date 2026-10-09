from __future__ import annotations

import pytest
from aware_issue_operational_runtime import (
    ActorEvidence,
    AuthorityKind,
    InMemoryIssueStateStore,
    IssueAuthorityEvidence,
    IssueOperationalRuntimeHost,
    IssueOperationalState,
    IssueStatus,
    ReconciliationState,
    ReconciliationStatus,
)
from aware_issue_runtime import (
    admit_issue_source_import,
    parse_issue_projection,
    propose_issue_source_import,
)

_SOURCE = """# Issue: Imported work

- Slug: `imported-work`
- Tag: `fb/2026-08-22/imported-work`
- Status: In Progress
- Owner: `codex-source`
- Priority: P0

## Ownership Scope
- `docs/example.md`

## Updates (append-only)
- 2026-08-22T10:00:00Z — Source update. (recorder: `codex-source`)

## Evidence
- `receipt-1`
"""


def test_digest_bound_source_proposal_lowers_to_operational_intents() -> None:
    projection = parse_issue_projection(
        text=_SOURCE,
        source_path="docs/issues/2026/08/22/imported.md",
    )
    authority_ref = "issue-authority:repo"
    proposal = propose_issue_source_import(
        projection,
        target_authority_ref=authority_ref,
    )
    actor = ActorEvidence("human:local", "human-admission:1")
    admission = admit_issue_source_import(
        proposal,
        projection,
        actor_evidence=actor,
        expected_authority_generation=0,
    )
    host = IssueOperationalRuntimeHost(InMemoryIssueStateStore())
    state = IssueOperationalState(
        IssueAuthorityEvidence(
            AuthorityKind.LOCAL_OPERATIONAL,
            "test",
            authority_ref,
            0,
            reconciliation=ReconciliationState(ReconciliationStatus.UNMAPPED),
        )
    )
    assert host.admit_authority(authority_ref, state, epoch="test-epoch")
    for intent in admission.intents:
        result = host.submit(authority_ref, intent)
        assert result.receipt is not None
    record = host.read(authority_ref)
    assert record is not None
    issue = record.state.issue_by_ref(admission.target_issue_ref)
    assert issue is not None
    assert issue.status is IssueStatus.IN_PROGRESS
    assert issue.scope_paths[0].relative_path == "docs/example.md"
    assert issue.updates[0].actor_ref == "codex-source"
    assert issue.evidence_refs[0].path == "receipt-1"


def test_changed_source_cannot_be_admitted() -> None:
    before = parse_issue_projection(text=_SOURCE, source_path="docs/issues/a.md")
    after = parse_issue_projection(text=_SOURCE + "\n", source_path="docs/issues/a.md")
    proposal = propose_issue_source_import(before, target_authority_ref="authority:1")
    with pytest.raises(ValueError, match="source_digest_changed"):
        admit_issue_source_import(
            proposal,
            after,
            actor_evidence=ActorEvidence("human:local", "admission:1"),
            expected_authority_generation=0,
        )
