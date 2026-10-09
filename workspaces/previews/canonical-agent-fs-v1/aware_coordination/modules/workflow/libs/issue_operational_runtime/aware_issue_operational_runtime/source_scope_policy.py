"""Pure Issue-owned source-scope policy; a decision is never a write permit.

Parsing, canonical path validation, actor issuance and at-use revalidation stay
with their owners. This policy preserves the existing publication precedence.
"""

from dataclasses import dataclass
from enum import StrEnum


class IssueSourceScopeRefusal(StrEnum):
    OWNER_MISMATCH = "issue_owner_mismatch"
    STATUS_INVALID = "issue_status_invalid"
    OUT_OF_SCOPE = "issue_source_out_of_scope"


@dataclass(frozen=True, slots=True)
class IssueSourceScopeDecision:
    refusal: IssueSourceScopeRefusal | None = None
    offending_path: str | None = None

    @property
    def allowed(self) -> bool:
        return self.refusal is None


def issue_scope_covers_path(*, path: str, scope_paths: tuple[str, ...]) -> bool:
    """Exact or slash-delimited prefix containment over owner-normalized paths."""
    return any(path == scope or path.startswith(scope + "/") for scope in scope_paths)


def evaluate_issue_source_scope(
    *,
    issue_owner: str,
    issue_status: str,
    scope_paths: tuple[str, ...],
    actor_ref: str,
    effect_paths: tuple[str, ...],
) -> IssueSourceScopeDecision:
    """Evaluate authored policy only; do not discover or admit an execution."""
    if issue_owner != actor_ref:
        return IssueSourceScopeDecision(IssueSourceScopeRefusal.OWNER_MISMATCH)
    normalized_status = " ".join(
        issue_status.strip().lower().replace("_", " ").replace("-", " ").split()
    )
    if normalized_status != "in progress":
        return IssueSourceScopeDecision(IssueSourceScopeRefusal.STATUS_INVALID)
    for path in effect_paths:
        if not issue_scope_covers_path(path=path, scope_paths=scope_paths):
            return IssueSourceScopeDecision(IssueSourceScopeRefusal.OUT_OF_SCOPE, path)
    return IssueSourceScopeDecision()
