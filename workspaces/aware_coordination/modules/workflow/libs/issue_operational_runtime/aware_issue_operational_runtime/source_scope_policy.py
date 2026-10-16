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
    # Construct only after the original owner/status checks and only when an
    # effect is actually examined. Never retain scope or a policy verdict
    # between decisions. Owner-normalized exact strings need no ordered scan.
    scope_index: frozenset[str] | None = None
    index_checked = False
    for path in effect_paths:
        if not index_checked:
            index_checked = True
            if type(scope_paths) is tuple and all(
                type(scope) is str for scope in scope_paths
            ):
                scope_index = frozenset(scope_paths)
        if scope_index is None or type(path) is not str:
            # Keep the original behavior for values outside the normalized
            # exact-string contract, including their original short circuit.
            covered = issue_scope_covers_path(path=path, scope_paths=scope_paths)
        else:
            covered = path in scope_index
            separator = path.find("/")
            while not covered and separator >= 0:
                covered = path[:separator] in scope_index
                separator = path.find("/", separator + 1)
        if not covered:
            return IssueSourceScopeDecision(IssueSourceScopeRefusal.OUT_OF_SCOPE, path)
    return IssueSourceScopeDecision()
