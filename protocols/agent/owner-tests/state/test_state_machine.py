from __future__ import annotations

import pytest
from aware_issue_operational_runtime import (
    AmendIssueScopePathsIntent,
    AppendIssueUpdateIntent,
    BindIssueScopePathsIntent,
    BlockIssueIntent,
    CloseIssueIntent,
    EnsureIssueIntent,
    IssueOperationalState,
    IssueOwnershipScopePath,
    IssueStatus,
    ResumeIssueIntent,
    SetIssueOwnerIntent,
    StartIssueProgressIntent,
    TransitionOutcome,
    apply_issue_intent,
)
from conftest import context


def test_issue_lifecycle_scope_and_update_are_revision_bound(actor, state) -> None:
    ensured = apply_issue_intent(
        state,
        EnsureIssueIntent(
            context(actor, "ensure", issue_revision=None), "fb/demo", "Demo"
        ),
    )
    assert ensured.outcome is TransitionOutcome.APPLIED
    assert ensured.issue_revision == 0
    issue_ref = ensured.issue_ref
    assert issue_ref is not None

    scoped = apply_issue_intent(
        ensured.state,
        BindIssueScopePathsIntent(
            context(actor, "scope", issue_revision=0),
            issue_ref,
            (IssueOwnershipScopePath("docs/a.md"),),
        ),
    )
    started = apply_issue_intent(
        scoped.state,
        StartIssueProgressIntent(context(actor, "start", issue_revision=1), issue_ref),
    )
    blocked = apply_issue_intent(
        started.state,
        BlockIssueIntent(context(actor, "block", issue_revision=2), issue_ref),
    )
    resumed = apply_issue_intent(
        blocked.state,
        ResumeIssueIntent(context(actor, "resume", issue_revision=3), issue_ref),
    )
    updated = apply_issue_intent(
        resumed.state,
        AppendIssueUpdateIntent(
            context(actor, "update", issue_revision=4),
            issue_ref,
            message="Proof passed.",
        ),
    )
    closed = apply_issue_intent(
        updated.state,
        CloseIssueIntent(context(actor, "close", issue_revision=5), issue_ref),
    )
    issue = closed.state.issue_by_ref(issue_ref)
    assert issue is not None
    assert issue.status is IssueStatus.CLOSED
    assert issue.revision == 6
    assert issue.scope_paths[0].relative_path == "docs/a.md"
    assert issue.updates[0].actor_ref == actor.actor_ref


def test_stale_revision_cannot_mutate(actor, state) -> None:
    ensured = apply_issue_intent(
        state,
        EnsureIssueIntent(
            context(actor, "ensure", issue_revision=None), "fb/demo", "Demo"
        ),
    )
    assert ensured.issue_ref is not None
    stale = apply_issue_intent(
        ensured.state,
        StartIssueProgressIntent(
            context(actor, "stale", issue_revision=9),
            ensured.issue_ref,
        ),
    )
    assert stale.outcome is TransitionOutcome.STALE
    assert not stale.changed


def test_owner_handoff_requires_current_owner_and_preserves_lifecycle(
    actor, state
) -> None:
    ensured = apply_issue_intent(
        state,
        EnsureIssueIntent(
            context(actor, "ensure-handoff", issue_revision=None),
            "fb/handoff",
            "Handoff",
            owner_session_id=actor.actor_ref,
        ),
    )
    assert ensured.issue_ref is not None
    blocked = apply_issue_intent(
        ensured.state,
        BlockIssueIntent(
            context(actor, "block-handoff", issue_revision=0),
            ensured.issue_ref,
        ),
    )
    transferred = apply_issue_intent(
        blocked.state,
        SetIssueOwnerIntent(
            context(actor, "transfer-handoff", issue_revision=1),
            ensured.issue_ref,
            new_owner_session_id="codex-replacement",
        ),
    )
    issue = transferred.state.issue_by_ref(ensured.issue_ref)

    assert transferred.outcome is TransitionOutcome.APPLIED
    assert issue is not None
    assert issue.status is IssueStatus.BLOCKED
    assert issue.owner_session_id == "codex-replacement"
    assert issue.revision == 2


def test_owner_handoff_rejects_foreign_actor_and_closed_issue(actor, state) -> None:
    ensured = apply_issue_intent(
        state,
        EnsureIssueIntent(
            context(actor, "ensure-handoff-refusals", issue_revision=None),
            "fb/handoff-refusals",
            "Handoff refusals",
            owner_session_id=actor.actor_ref,
        ),
    )
    assert ensured.issue_ref is not None
    foreign_actor = type(actor)("codex-foreign", "evidence:foreign")
    foreign = apply_issue_intent(
        ensured.state,
        SetIssueOwnerIntent(
            context(foreign_actor, "foreign-transfer", issue_revision=0),
            ensured.issue_ref,
            new_owner_session_id="codex-replacement",
        ),
    )
    assert foreign.outcome is TransitionOutcome.UNAUTHORIZED
    assert foreign.blocker_code == "issue_owner_transfer_actor_mismatch"

    closed = apply_issue_intent(
        ensured.state,
        CloseIssueIntent(
            context(actor, "close-before-transfer", issue_revision=0),
            ensured.issue_ref,
        ),
    )
    refused = apply_issue_intent(
        closed.state,
        SetIssueOwnerIntent(
            context(actor, "closed-transfer", issue_revision=1),
            ensured.issue_ref,
            new_owner_session_id="codex-replacement",
        ),
    )
    assert refused.outcome is TransitionOutcome.INVALID
    assert refused.blocker_code == "issue_owner_transfer_closed"


def test_scope_amendment_is_additive_owned_and_revision_bound(actor, state) -> None:
    ensured = apply_issue_intent(
        state,
        EnsureIssueIntent(
            context(actor, "ensure", issue_revision=None),
            "fb/amend",
            "Amend",
            owner_session_id="codex-owner",
        ),
    )
    assert ensured.issue_ref is not None
    scoped = apply_issue_intent(
        ensured.state,
        BindIssueScopePathsIntent(
            context(actor, "scope", issue_revision=0),
            ensured.issue_ref,
            (IssueOwnershipScopePath("docs/a.md"),),
        ),
    )
    started = apply_issue_intent(
        scoped.state,
        StartIssueProgressIntent(
            context(actor, "start", issue_revision=1), ensured.issue_ref
        ),
    )

    amended = apply_issue_intent(
        started.state,
        AmendIssueScopePathsIntent(
            context(actor, "amend", issue_revision=2),
            ensured.issue_ref,
            owner_session_id="codex-owner",
            add_scope_paths=(IssueOwnershipScopePath("src/b.py"),),
        ),
    )
    issue = amended.state.issue_by_ref(ensured.issue_ref)
    assert amended.outcome is TransitionOutcome.APPLIED
    assert issue is not None
    assert issue.revision == 3
    assert tuple(item.relative_path for item in issue.scope_paths) == (
        "docs/a.md",
        "src/b.py",
    )

    already_present = apply_issue_intent(
        amended.state,
        AmendIssueScopePathsIntent(
            context(actor, "amend-again", issue_revision=3),
            ensured.issue_ref,
            owner_session_id="codex-owner",
            add_scope_paths=(IssueOwnershipScopePath("src/b.py"),),
        ),
    )
    assert already_present.outcome is TransitionOutcome.IDEMPOTENT
    assert already_present.issue_revision == 3


def test_scope_amendment_rejects_foreign_owner_and_wrong_lifecycle(
    actor, state
) -> None:
    ensured = apply_issue_intent(
        state,
        EnsureIssueIntent(
            context(actor, "ensure", issue_revision=None),
            "fb/amend",
            "Amend",
            owner_session_id="codex-owner",
        ),
    )
    assert ensured.issue_ref is not None
    wrong_lifecycle = apply_issue_intent(
        ensured.state,
        AmendIssueScopePathsIntent(
            context(actor, "open-amend", issue_revision=0),
            ensured.issue_ref,
            owner_session_id="codex-owner",
            add_scope_paths=(IssueOwnershipScopePath("src/b.py"),),
        ),
    )
    assert wrong_lifecycle.outcome is TransitionOutcome.INVALID
    assert wrong_lifecycle.blocker_code == "issue_scope_amendment_status_invalid"

    started = apply_issue_intent(
        ensured.state,
        StartIssueProgressIntent(
            context(actor, "start", issue_revision=0), ensured.issue_ref
        ),
    )
    foreign = apply_issue_intent(
        started.state,
        AmendIssueScopePathsIntent(
            context(actor, "foreign-amend", issue_revision=1),
            ensured.issue_ref,
            owner_session_id="codex-foreign",
            add_scope_paths=(IssueOwnershipScopePath("src/b.py"),),
        ),
    )
    assert foreign.outcome is TransitionOutcome.UNAUTHORIZED
    assert foreign.blocker_code == "issue_scope_amendment_owner_mismatch"


def test_scope_amendment_rejects_stale_invalid_and_over_capacity(actor, state) -> None:
    ensured = apply_issue_intent(
        state,
        EnsureIssueIntent(
            context(actor, "ensure", issue_revision=None),
            "fb/amend-capacity",
            "Amend capacity",
            owner_session_id="codex-owner",
        ),
    )
    assert ensured.issue_ref is not None
    scoped = apply_issue_intent(
        ensured.state,
        BindIssueScopePathsIntent(
            context(actor, "scope", issue_revision=0),
            ensured.issue_ref,
            tuple(
                IssueOwnershipScopePath(f"src/{index:03}.py") for index in range(128)
            ),
        ),
    )
    started = apply_issue_intent(
        scoped.state,
        StartIssueProgressIntent(
            context(actor, "start", issue_revision=1), ensured.issue_ref
        ),
    )

    stale = apply_issue_intent(
        started.state,
        AmendIssueScopePathsIntent(
            context(actor, "stale", issue_revision=1),
            ensured.issue_ref,
            owner_session_id="codex-owner",
            add_scope_paths=(IssueOwnershipScopePath("extra.py"),),
        ),
    )
    assert stale.outcome is TransitionOutcome.STALE
    assert stale.blocker_code == "issue_revision_mismatch"

    over_capacity = apply_issue_intent(
        started.state,
        AmendIssueScopePathsIntent(
            context(actor, "capacity", issue_revision=2),
            ensured.issue_ref,
            owner_session_id="codex-owner",
            add_scope_paths=(IssueOwnershipScopePath("extra.py"),),
        ),
    )
    assert over_capacity.outcome is TransitionOutcome.INVALID
    assert over_capacity.blocker_code == "issue_scope_capacity_exceeded"

    with pytest.raises(ValueError, match="normalized"):
        AmendIssueScopePathsIntent(
            context(actor, "invalid", issue_revision=2),
            ensured.issue_ref,
            owner_session_id="codex-owner",
            add_scope_paths=(IssueOwnershipScopePath("../outside.py"),),
        )


def test_idempotency_key_replay_and_reuse_are_distinct(actor, state) -> None:
    intent = EnsureIssueIntent(
        context(actor, "same", issue_revision=None), "fb/demo", "Demo"
    )
    first = apply_issue_intent(state, intent)
    replay = apply_issue_intent(first.state, intent)
    conflict = apply_issue_intent(
        first.state,
        EnsureIssueIntent(
            context(actor, "same", issue_revision=None), "fb/other", "Other"
        ),
    )
    assert replay.outcome is TransitionOutcome.IDEMPOTENT
    assert conflict.outcome is TransitionOutcome.CONFLICT
    assert conflict.blocker_code == "client_intent_id_reused"


def test_unaccepted_actor_is_rejected(actor, state: IssueOperationalState) -> None:
    denied = type(actor)(actor.actor_ref, actor.evidence_ref, accepted=False)
    result = apply_issue_intent(
        state,
        EnsureIssueIntent(context(denied, "denied", issue_revision=None), "fb/x", "X"),
    )
    assert result.outcome is TransitionOutcome.UNAUTHORIZED
