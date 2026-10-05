"""Committed compatibility authority for Phase-native scope advancement."""
# pyright: reportUnusedCallResult=false

from __future__ import annotations

import hashlib
import posixpath
import re
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

from aware_goal_operational_runtime import (
    GoalGlobalDirectionAuthorityV1,
    GoalLaneDirectionAuthorityV1,
    GoalPhaseNativeCompatibilityRelation,
    GoalPhaseNativeDocumentV2,
    GoalPhaseNativeDocumentV3,
    GoalPhaseNativeScopeSourceEpochV1,
    GoalPhaseSourceBindingV1,
    verify_goal_phase_native_scope_source_epoch,
)
from aware_goal_operational_runtime.identity import fingerprint, required_token
from aware_goal_sdk.markdown_source import (
    GoalMarkdownImportPlan,
    GoalMarkdownLaneSeed,
    parse_goal_markdown_import_plan,
)
from aware_goal_sdk.native_phase_markdown import extract_goal_phase_native_document

PROJECTOR_REF = "goal-compatibility-direction-projector:v1"
_OWNER = re.compile(r"(?m)^- Owner:\s+`?(?P<value>[^`\n]+)`?\s*$")
_ISSUE_STATUS = re.compile(r"(?m)^- Status:\s+`?(?P<value>[^`\n]+)`?\s*$")
_ISSUE_TAG = re.compile(r"(?m)^- Tag:\s+`?(?P<value>[^`\n]+)`?\s*$")
_SCOPE_ITEM = re.compile(r"(?m)^- `(?P<path>[^`]+)`\s*$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_ALLOWLISTED_NOTE = re.compile(
    r"^- (?P<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) \| "
    + r"kind=`narrative-note` \| (?P<text>[^|\n]+) \| recorder=`(?P<recorder>[^`]+)`$"
)
_LANE_MAP_HEADER = (
    "| Lane | Role | Owner | Status | Current Issue | Since | Last Receipt | Scope |"
)
_FORWARD_PLAN_HEADER = "| Lane | Next Issue | Gate |"
_LANE_SEQUENCE_HEADER = (
    "| Step | Key | Time | Tick | Issue | Gate | Status | Owner | Receipt |"
)
_APPEND_ONLY_HISTORY_SECTION = "## Integrated Updates (append-only)"
_CANONICAL_GOAL_STATUS_LINE = re.compile(r"^- Status: (?:`[^`]+`|[^`\n]+)$")
_CANONICAL_GOAL_OWNER_LINE = re.compile(r"^- Owner: (?:`[^`]+`|[^`\n]+)$")


class GoalNativeScopeSourceError(RuntimeError):
    code: str

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class GoalAdmittedIssueLocation(Protocol):
    """Location only; committed Issue semantics remain Goal's responsibility."""

    @property
    def issue_root(self) -> str: ...

    def resolve_issue_path(self, relative_path: str) -> None: ...

    def match_issue_path(self, relative_path: str) -> bool: ...

    def issue_tag_for_path(self, relative_path: str) -> str: ...


@dataclass(frozen=True, slots=True)
class GoalCompatibilityIssueAuthorityV1:
    issue_ref: str
    status: str
    owner_ref: str
    authority_ref: str

    def __post_init__(self) -> None:
        for name in ("issue_ref", "owner_ref", "authority_ref"):
            required_token(cast(str, getattr(self, name)), name)
        if self.status not in {"open", "in_progress", "blocked", "closed"}:
            raise GoalNativeScopeSourceError(
                "issue_authority_invalid", "unsupported Issue status"
            )


@dataclass(frozen=True, slots=True)
class GoalCompatibilityDirectionProjectionV1:
    source_revision_ref: str
    goal_path: str
    compatibility_sha256: str
    compatibility_guard_ref: str
    allowlisted_note_records: tuple[str, ...]
    source_binding: GoalPhaseSourceBindingV1
    global_authority: GoalGlobalDirectionAuthorityV1
    lane_authorities: tuple[GoalLaneDirectionAuthorityV1, ...]
    projection_receipt_ref: str


class GitCommittedGoalCompatibilityDirectionProjector:
    def __init__(
        self,
        repository_root: Path,
        *,
        admitted_issue_location: GoalAdmittedIssueLocation | None = None,
    ) -> None:
        root = repository_root.resolve(strict=True)
        if not (root / ".git").exists():
            raise ValueError("repository_root must be a Git worktree")
        self.repository_root: Path = root
        self._admitted_issue_location: GoalAdmittedIssueLocation | None = (
            admitted_issue_location
        )

    def project(
        self,
        *,
        revision_ref: str,
        goal_path: str,
        expected_goal_sha256: str,
        expected_goal_blob_oid: str,
        expected_document: GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3,
        governance_authority_refs: tuple[str, ...],
        goal_hold_authority_refs: tuple[str, ...],
        issue_authority_by_ref: Mapping[str, GoalCompatibilityIssueAuthorityV1],
    ) -> GoalCompatibilityDirectionProjectionV1:
        revision = self._commit(revision_ref)
        path = _repository_path(goal_path)
        candidate = self._git("show", f"{revision}:{path}")
        digest = "sha256:" + hashlib.sha256(candidate).hexdigest()
        if digest != expected_goal_sha256:
            raise GoalNativeScopeSourceError(
                "goal_digest_mismatch", "committed Goal digest differs"
            )
        blob = self._git("rev-parse", f"{revision}:{path}").decode().strip()
        if blob != expected_goal_blob_oid.removeprefix("git-blob:"):
            raise GoalNativeScopeSourceError(
                "goal_blob_mismatch", "committed Goal blob differs"
            )
        return project_goal_compatibility_direction(
            candidate=candidate,
            source_revision_ref=revision,
            goal_path=path,
            expected_document=expected_document,
            governance_authority_refs=governance_authority_refs,
            goal_hold_authority_refs=goal_hold_authority_refs,
            issue_authority_by_ref=issue_authority_by_ref,
        )

    def project_committed(
        self,
        *,
        revision_ref: str,
        goal_path: str,
        expected_goal_sha256: str,
        expected_goal_blob_oid: str,
    ) -> tuple[GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3, GoalCompatibilityDirectionProjectionV1]:
        """Resolve every compatibility authority input from one committed tree."""

        revision = self._commit(revision_ref)
        path = _repository_path(goal_path)
        candidate = self._git("show", f"{revision}:{path}")
        compatibility, document = extract_goal_phase_native_document(candidate)
        if not isinstance(document, (GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3)):
            raise GoalNativeScopeSourceError(
                "document_profile_unsupported", "scope advancement requires V2 or V3"
            )
        text = compatibility.decode("utf-8")
        plan = parse_goal_markdown_import_plan(text, source_path=path)
        issues = {
            issue_ref: self._issue_authority(
                revision=revision, goal_path=path, issue_ref=issue_ref
            )
            for issue_ref in {
                lane.current_issue_tag
                for lane in plan.lanes
                if lane.current_issue_tag is not None
                and not lane.current_issue_tag.startswith("TBD:")
            }
        }
        owner_matches = tuple(
            match.group("value").strip() for match in _OWNER.finditer(text)
        )
        if len(owner_matches) != 1:
            raise GoalNativeScopeSourceError(
                "goal_owner_ambiguous", "Goal Owner must occur exactly once"
            )
        governance_ref = "goal-committed-owner-authority:" + fingerprint(
            {
                "schema_id": "aware.goal.committed-owner-authority.v1",
                "goal_path": path,
                "goal_tag": document.goal_tag,
                "owner_ref": owner_matches[0],
            }
        )
        if _goal_status(plan.status_snapshot) in {"parked", "held"}:
            raise GoalNativeScopeSourceError(
                "goal_hold_authority_unresolved",
                "held Goal requires a typed committed hold-authority resolver",
            )
        return document, self.project(
            revision_ref=revision,
            goal_path=path,
            expected_goal_sha256=expected_goal_sha256,
            expected_goal_blob_oid=expected_goal_blob_oid,
            expected_document=document,
            governance_authority_refs=(governance_ref,),
            goal_hold_authority_refs=(),
            issue_authority_by_ref=issues,
        )

    def _issue_authority(
        self, *, revision: str, goal_path: str, issue_ref: str
    ) -> GoalCompatibilityIssueAuthorityV1:
        path = self._resolve_issue_path(
            revision=revision, goal_path=goal_path, issue_ref=issue_ref
        )
        if self._admitted_issue_location is not None:
            self._admitted_issue_location.resolve_issue_path(path)
            entries = self._git("ls-tree", "-z", revision, "--", path).split(b"\0")
            if len(entries) != 2 or entries[1] != b"":
                raise GoalNativeScopeSourceError(
                    "issue_authority_invalid", "Issue is not a committed regular file"
                )
            try:
                metadata, listed = entries[0].split(b"\t", 1)
                mode, kind, _ = metadata.decode("ascii").split(" ")
                listed_path = listed.decode("utf-8")
            except (UnicodeDecodeError, ValueError) as error:
                raise GoalNativeScopeSourceError(
                    "issue_authority_invalid", "Issue tree entry is malformed"
                ) from error
            if (
                listed_path != path
                or mode not in {"100644", "100755"}
                or kind != "blob"
            ):
                raise GoalNativeScopeSourceError(
                    "issue_authority_invalid", "Issue is not a committed regular file"
                )
        payload = self._git("show", f"{revision}:{path}")
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise GoalNativeScopeSourceError(
                "issue_authority_invalid", f"Issue {path} is not UTF-8"
            ) from error
        owner = tuple(match.group("value").strip() for match in _OWNER.finditer(text))
        status = tuple(
            match.group("value").strip().lower().replace(" ", "_")
            for match in _ISSUE_STATUS.finditer(text)
        )
        tags = tuple(match.group("value").strip() for match in _ISSUE_TAG.finditer(text))
        if (
            len(owner) != 1
            or len(status) != 1
            or (self._admitted_issue_location is not None and len(tags) != 1)
        ):
            raise GoalNativeScopeSourceError(
                "issue_authority_invalid", f"Issue {path} metadata is ambiguous"
            )
        if self._admitted_issue_location is not None:
            expected_tag = self._admitted_issue_location.issue_tag_for_path(path)
            if tags != (expected_tag,) or (
                issue_ref.startswith("fb/") and issue_ref != expected_tag
            ):
                raise GoalNativeScopeSourceError(
                    "issue_authority_invalid", f"Issue {path} tag does not match"
                )
        scopes = tuple(match.group("path") for match in _SCOPE_ITEM.finditer(text))
        blob = self._git("rev-parse", f"{revision}:{path}").decode().strip()
        authority_ref = "goal-committed-issue-authority:" + fingerprint(
            {
                "issue_ref": path,
                "declared_issue_ref": issue_ref,
                "status": status[0],
                "owner_ref": owner[0],
                "ownership_scope": sorted(scopes),
                "blob_oid": blob,
            }
        )
        return GoalCompatibilityIssueAuthorityV1(
            issue_ref=issue_ref,
            status=status[0],
            owner_ref=owner[0],
            authority_ref=authority_ref,
        )

    def _resolve_issue_path(
        self, *, revision: str, goal_path: str, issue_ref: str
    ) -> str:
        admitted = self._admitted_issue_location
        source_path = issue_ref
        if admitted is not None and issue_ref.startswith(("./", "../")):
            source_path = posixpath.normpath(
                posixpath.join(posixpath.dirname(goal_path), issue_ref)
            )
            if source_path.startswith("../") or source_path in {"..", "."}:
                raise GoalNativeScopeSourceError(
                    "issue_outside_admitted_binding", "Issue link escapes repository"
                )
        if admitted is not None and admitted.match_issue_path(source_path):
            admitted.resolve_issue_path(source_path)
            return _repository_path(source_path)
        if admitted is None and issue_ref.startswith("docs/issues/"):
            return _repository_path(issue_ref)
        root = admitted.issue_root if admitted is not None else "docs/issues"
        try:
            completed = subprocess.run(
                (
                    "git",
                    "grep",
                    "-l",
                    "-F",
                    "-e",
                    issue_ref,
                    revision,
                    "--",
                    root,
                ),
                cwd=self.repository_root,
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except subprocess.TimeoutExpired as error:
            raise GoalNativeScopeSourceError(
                "issue_authority_unavailable", "Issue tag resolution timed out"
            ) from error
        candidates = tuple(
            line.split(":", 1)[1]
            for line in completed.stdout.splitlines()
            if ":" in line
        )
        matches_list: list[str] = []
        for path in candidates:
            if admitted is not None and not admitted.match_issue_path(path):
                continue
            try:
                candidate_text = self._git("show", f"{revision}:{path}").decode("utf-8")
            except UnicodeDecodeError as error:
                raise GoalNativeScopeSourceError(
                    "issue_authority_invalid", "Issue candidate is not UTF-8"
                ) from error
            tags = tuple(
                match.group("value").strip()
                for match in _ISSUE_TAG.finditer(candidate_text)
            )
            if tags == (issue_ref,):
                matches_list.append(path)
        matches = tuple(matches_list)
        if completed.returncode not in {0, 1} or len(matches) != 1:
            raise GoalNativeScopeSourceError(
                "issue_authority_ambiguous",
                f"Issue tag {issue_ref} does not resolve exactly once",
            )
        return _repository_path(matches[0])

    def _commit(self, value: str) -> str:
        result = (
            self._git("rev-parse", "--verify", f"{value}^{{commit}}").decode().strip()
        )
        if not _COMMIT.fullmatch(result):
            raise GoalNativeScopeSourceError(
                "revision_invalid", "Git returned invalid commit"
            )
        return result

    def _git(self, *args: str) -> bytes:
        try:
            return subprocess.run(
                ("git", *args),
                cwd=self.repository_root,
                check=True,
                capture_output=True,
                timeout=10,
            ).stdout
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            raise GoalNativeScopeSourceError(
                "git_unavailable", "committed Goal source is unavailable"
            ) from error

    def source_epoch(
        self,
        *,
        previous: GoalCompatibilityDirectionProjectionV1,
        candidate: GoalCompatibilityDirectionProjectionV1,
    ) -> GoalPhaseNativeScopeSourceEpochV1:
        if previous.goal_path != candidate.goal_path:
            raise GoalNativeScopeSourceError(
                "goal_path_mismatch", "source epoch paths differ"
            )
        def resolve_epoch(
            goal_path: str, previous_revision: str, candidate_revision: str
        ) -> Mapping[str, object]:
            if (
                goal_path != previous.goal_path
                or previous_revision != previous.source_revision_ref
                or candidate_revision != candidate.source_revision_ref
            ):
                raise GoalNativeScopeSourceError(
                    "source_epoch_request_mismatch",
                    "source epoch resolver coordinates differ",
                )
            # Re-read both tree entries and HEAD inside the verifier callback.
            observed_head = self._commit("HEAD")
            previous_bytes = self._git("show", f"{previous_revision}:{goal_path}")
            candidate_bytes = self._git("show", f"{candidate_revision}:{goal_path}")
            previous_blob = self._git(
                "rev-parse", f"{previous_revision}:{goal_path}"
            ).decode().strip()
            candidate_blob = self._git(
                "rev-parse", f"{candidate_revision}:{goal_path}"
            ).decode().strip()
            resolved_previous = GoalPhaseSourceBindingV1(
                repository_revision_ref=previous_revision,
                goal_sha256="sha256:" + hashlib.sha256(previous_bytes).hexdigest(),
                goal_blob_oid=previous_blob,
            )
            resolved_candidate = GoalPhaseSourceBindingV1(
                repository_revision_ref=candidate_revision,
                goal_sha256="sha256:" + hashlib.sha256(candidate_bytes).hexdigest(),
                goal_blob_oid=candidate_blob,
            )
            _, verified_previous = self.project_committed(
                revision_ref=previous_revision,
                goal_path=goal_path,
                expected_goal_sha256=resolved_previous.goal_sha256,
                expected_goal_blob_oid=resolved_previous.goal_blob_oid,
            )
            _, verified_candidate = self.project_committed(
                revision_ref=candidate_revision,
                goal_path=goal_path,
                expected_goal_sha256=resolved_candidate.goal_sha256,
                expected_goal_blob_oid=resolved_candidate.goal_blob_oid,
            )
            if (
                verified_previous.source_binding != previous.source_binding
                or verified_candidate.source_binding != candidate.source_binding
            ):
                raise GoalNativeScopeSourceError(
                    "source_binding_mismatch",
                    "supplied source bindings differ from committed source",
                )
            if verified_previous != previous or verified_candidate != candidate:
                raise GoalNativeScopeSourceError(
                    "compatibility_projection_mismatch",
                    "supplied direction projection differs from committed source",
                )
            relation = "equal"
            if previous_revision != candidate_revision:
                ancestor = subprocess.run(
                    (
                        "git",
                        "merge-base",
                        "--is-ancestor",
                        previous_revision,
                        candidate_revision,
                    ),
                    cwd=self.repository_root,
                    check=False,
                    capture_output=True,
                    timeout=10,
                )
                relation = "descendant" if ancestor.returncode == 0 else "unproven"
            compatibility_relation = _compatibility_relation(
                verified_previous, verified_candidate
            )
            return {
                "observed_head_ref": observed_head,
                "lineage": relation,
                "previous_source": resolved_previous.to_wire(),
                "candidate_source": resolved_candidate.to_wire(),
                "compatibility_relation": compatibility_relation.value,
            }

        return verify_goal_phase_native_scope_source_epoch(
            goal_path=previous.goal_path,
            previous_source=previous.source_binding,
            candidate_source=candidate.source_binding,
            repository_resolver=resolve_epoch,
        )


def _compatibility_relation(
    previous: GoalCompatibilityDirectionProjectionV1,
    candidate: GoalCompatibilityDirectionProjectionV1,
) -> GoalPhaseNativeCompatibilityRelation:
    notes_append = previous.allowlisted_note_records == (
        candidate.allowlisted_note_records[: len(previous.allowlisted_note_records)]
    )
    if previous.compatibility_sha256 == candidate.compatibility_sha256:
        return GoalPhaseNativeCompatibilityRelation.EXACT
    if (
        previous.compatibility_guard_ref != candidate.compatibility_guard_ref
        or not notes_append
    ):
        return GoalPhaseNativeCompatibilityRelation.UNKNOWN
    if previous.allowlisted_note_records != candidate.allowlisted_note_records:
        return GoalPhaseNativeCompatibilityRelation.ALLOWLISTED_APPEND
    return GoalPhaseNativeCompatibilityRelation.DECODED_AUTHORITY_CHANGE


def project_goal_compatibility_direction(
    *,
    candidate: bytes,
    source_revision_ref: str,
    goal_path: str,
    expected_document: GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3,
    governance_authority_refs: tuple[str, ...],
    goal_hold_authority_refs: tuple[str, ...],
    issue_authority_by_ref: Mapping[str, GoalCompatibilityIssueAuthorityV1],
) -> GoalCompatibilityDirectionProjectionV1:
    """Strictly project Goal and lane direction from one canonical V2/V3 carrier."""

    if not _COMMIT.fullmatch(source_revision_ref):
        raise GoalNativeScopeSourceError(
            "revision_invalid", "source revision must be a commit"
        )
    compatibility, document = extract_goal_phase_native_document(candidate)
    if not isinstance(document, (GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3)) or document != expected_document:
        raise GoalNativeScopeSourceError(
            "document_mismatch", "committed native document differs"
        )
    try:
        text = compatibility.decode("utf-8")
    except UnicodeDecodeError as error:
        raise GoalNativeScopeSourceError(
            "compatibility_not_utf8", "compatibility prefix is not UTF-8"
        ) from error
    plan = parse_goal_markdown_import_plan(text, source_path=goal_path)
    if plan.goal_tag != document.goal_tag:
        raise GoalNativeScopeSourceError(
            "goal_identity_mismatch", "compatibility Goal identity differs"
        )
    owner_matches = tuple(
        match.group("value").strip() for match in _OWNER.finditer(text)
    )
    if len(owner_matches) != 1:
        raise GoalNativeScopeSourceError(
            "goal_owner_ambiguous", "Goal Owner must occur exactly once"
        )
    governance = _tokens(governance_authority_refs, "governance_authority_refs")
    holds = _tokens(goal_hold_authority_refs, "goal_hold_authority_refs")
    lifecycle = _goal_status(plan.status_snapshot)
    hold_state = "held" if lifecycle in {"parked", "held"} else "clear"
    if (hold_state == "held") != bool(holds):
        raise GoalNativeScopeSourceError(
            "goal_hold_authority_mismatch", "Goal hold state and authority differ"
        )
    compatibility_sha = "sha256:" + hashlib.sha256(compatibility).hexdigest()
    guard_lines, notes, lane_guard_refs = _compatibility_guard(text, plan=plan)
    compatibility_guard_ref = "goal-compatibility-guard:" + fingerprint(
        {"guarded_lines": list(guard_lines)}
    )
    global_receipt = "goal-compatibility-direction-projection:" + fingerprint(
        {
            "projector_ref": PROJECTOR_REF,
            "source_revision_ref": source_revision_ref,
            "goal_path": goal_path,
            "compatibility_sha256": compatibility_sha,
            "goal_tag": plan.goal_tag,
            "lifecycle_status": lifecycle,
            "owner_ref": owner_matches[0],
            "governance_authority_refs": list(governance),
            "goal_hold_authority_refs": list(holds),
            "execution_authority_ref": document.execution_authority.authority_ref,
            "compatibility_guard_ref": compatibility_guard_ref,
        }
    )
    global_authority = GoalGlobalDirectionAuthorityV1(
        goal_tag=plan.goal_tag,
        lifecycle_status=lifecycle,
        owner_ref=owner_matches[0],
        governance_authority_refs=governance,
        hold_state=hold_state,
        hold_authority_refs=holds,
        execution_authority_ref=document.execution_authority.authority_ref,
        compatibility_guard_ref=compatibility_guard_ref,
        source_revision_ref=source_revision_ref,
        projector_ref=PROJECTOR_REF,
        projection_receipt_ref=global_receipt,
    )
    lanes = tuple(
        _lane_authority(
            plan=plan,
            lane=lane,
            source_revision_ref=source_revision_ref,
            compatibility_sha=compatibility_sha,
            issue_authority_by_ref=issue_authority_by_ref,
            compatibility_guard_ref=lane_guard_refs[lane.lane_key],
        )
        for lane in plan.lanes
    )
    required_lanes = {item.coordinate.lane_key for item in document.definitions}
    if {item.lane_key for item in lanes} != required_lanes:
        raise GoalNativeScopeSourceError(
            "lane_set_mismatch", "Lane Map does not exactly cover native definitions"
        )
    receipt = "goal-compatibility-direction-set:" + fingerprint(
        {
            "global_authority_ref": global_authority.authority_ref,
            "lane_authority_refs": [item.authority_ref for item in lanes],
            "source_revision_ref": source_revision_ref,
            "compatibility_sha256": compatibility_sha,
        }
    )
    return GoalCompatibilityDirectionProjectionV1(
        source_revision_ref=source_revision_ref,
        goal_path=goal_path,
        compatibility_sha256=compatibility_sha,
        compatibility_guard_ref=compatibility_guard_ref,
        allowlisted_note_records=notes,
        source_binding=GoalPhaseSourceBindingV1(
            repository_revision_ref=source_revision_ref,
            goal_sha256="sha256:" + hashlib.sha256(candidate).hexdigest(),
            goal_blob_oid=_git_blob_oid(candidate),
        ),
        global_authority=global_authority,
        lane_authorities=lanes,
        projection_receipt_ref=receipt,
    )


def _lane_authority(
    *,
    plan: GoalMarkdownImportPlan,
    lane: GoalMarkdownLaneSeed,
    source_revision_ref: str,
    compatibility_sha: str,
    issue_authority_by_ref: Mapping[str, GoalCompatibilityIssueAuthorityV1],
    compatibility_guard_ref: str,
) -> GoalLaneDirectionAuthorityV1:
    if lane.role_label is None or lane.owner_execution_id is None:
        raise GoalNativeScopeSourceError(
            "lane_authority_incomplete", f"Lane {lane.lane_key} lacks role or owner"
        )
    state, detail = _lane_state(lane.status_token)
    ambiguity_reasons: list[str] = []
    issue_ref = lane.current_issue_tag
    issue_authority_ref: str | None = None
    matching_rows = tuple(
        item
        for item in plan.lane_issues
        if item.lane_key == lane.lane_key and item.planned_issue_tag == issue_ref
    )
    if issue_ref is not None:
        if len(matching_rows) != 1:
            raise GoalNativeScopeSourceError(
                "lane_sequence_disagreement",
                f"Lane {lane.lane_key} current Issue differs from sequence",
            )
        if issue_ref.startswith("TBD:"):
            issue_authority_ref = "goal-planned-work:" + fingerprint(
                {
                    "goal_tag": plan.goal_tag,
                    "lane_key": lane.lane_key,
                    "issue_ref": issue_ref,
                    "row_key": matching_rows[0].row_key,
                }
            )
        else:
            authority = issue_authority_by_ref.get(issue_ref)
            if authority is None or authority.issue_ref != issue_ref:
                raise GoalNativeScopeSourceError(
                    "issue_authority_missing",
                    f"Lane {lane.lane_key} current Issue authority is missing",
                )
            if matching_rows[0].owner_execution_id not in {None, authority.owner_ref}:
                ambiguity_reasons.append("lane-sequence-issue-owner-disagreement")
            allowed_status = {
                "active": {"in_progress", "blocked"},
                "held": {"in_progress", "blocked"},
                "blocked": {"in_progress", "blocked"},
                "complete": {"closed"},
                "ready": {"closed"},
                "planned": {"open"},
                "withdrawn": {"closed"},
            }[state]
            if authority.status not in allowed_status:
                ambiguity_reasons.append("lane-current-issue-status-disagreement")
            issue_authority_ref = authority.authority_ref
    blocker_refs: tuple[str, ...] = ()
    if state in {"held", "blocked"}:
        if lane.last_receipt_ref in {None, "Pending"}:
            raise GoalNativeScopeSourceError(
                "lane_blocker_authority_missing",
                f"Lane {lane.lane_key} blocker authority is missing",
            )
        assert lane.last_receipt_ref is not None
        blocker_refs = (lane.last_receipt_ref,)
    receipt = "goal-lane-compatibility-direction-projection:" + fingerprint(
        {
            "projector_ref": PROJECTOR_REF,
            "source_revision_ref": source_revision_ref,
            "compatibility_sha256": compatibility_sha,
            "goal_tag": plan.goal_tag,
            "lane_key": lane.lane_key,
            "role": lane.role_label,
            "owner_ref": lane.owner_execution_id,
            "operational_state": state,
            "state_detail": detail,
            "blocker_authority_refs": list(blocker_refs),
            "current_issue_ref": issue_ref,
            "current_issue_authority_ref": issue_authority_ref,
            "compatibility_guard_ref": compatibility_guard_ref,
            "qualification": "ambiguous" if ambiguity_reasons else "qualified",
            "ambiguity_reasons": sorted(ambiguity_reasons),
        }
    )
    return GoalLaneDirectionAuthorityV1(
        goal_tag=plan.goal_tag,
        lane_key=lane.lane_key,
        role=lane.role_label,
        owner_ref=lane.owner_execution_id,
        operational_state=state,
        state_detail=detail,
        blocker_authority_refs=blocker_refs,
        current_issue_ref=issue_ref,
        current_issue_authority_ref=issue_authority_ref,
        compatibility_guard_ref=compatibility_guard_ref,
        qualification="ambiguous" if ambiguity_reasons else "qualified",
        ambiguity_reasons=tuple(sorted(ambiguity_reasons)),
        source_revision_ref=source_revision_ref,
        projector_ref=PROJECTOR_REF,
        projection_receipt_ref=receipt,
    )


def _goal_status(value: str) -> str:
    normalized = value.strip().lower()
    aliases = {"complete": "completed", "blocked": "held"}
    normalized = aliases.get(normalized, normalized)
    if normalized not in {
        "proposed",
        "active",
        "parked",
        "held",
        "completed",
        "withdrawn",
    }:
        raise GoalNativeScopeSourceError(
            "goal_status_unsupported", "Goal status is unsupported"
        )
    return normalized


def _lane_state(value: str) -> tuple[str, str | None]:
    pieces = value.split(" — ", 1)
    state = pieces[0].strip().lower()
    aliases = {"completed": "complete", "closed": "complete"}
    state = aliases.get(state, state)
    if state not in {
        "planned",
        "active",
        "held",
        "blocked",
        "ready",
        "complete",
        "withdrawn",
    }:
        raise GoalNativeScopeSourceError(
            "lane_state_unsupported", f"unsupported lane state: {value}"
        )
    detail = pieces[1].strip() if len(pieces) == 2 else None
    if len(pieces) == 2 and not detail:
        raise GoalNativeScopeSourceError(
            "lane_state_detail_empty", "compound lane state has empty detail"
        )
    return state, detail


def _tokens(values: tuple[str, ...], name: str) -> tuple[str, ...]:
    normalized = tuple(required_token(item, name) for item in values)
    if normalized != tuple(sorted(set(normalized))):
        raise GoalNativeScopeSourceError(
            "authority_refs_noncanonical", f"{name} must be sorted and unique"
        )
    return normalized


def _repository_path(value: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not value.strip():
        raise GoalNativeScopeSourceError(
            "goal_path_invalid", "Goal path must be repository-relative"
        )
    return path.as_posix()


def _compatibility_guard(
    text: str, *, plan: GoalMarkdownImportPlan
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, str]]:
    """Split global compatibility and exact per-lane compatibility authority."""

    guarded: list[str] = []
    notes: list[str] = []
    lane_lines: dict[str, list[str]] = {item.lane_key: [] for item in plan.lanes}
    lines = text.splitlines()
    index = 0
    section: str | None = None
    lane_section: str | None = None
    while index < len(lines):
        line = lines[index]
        if line.startswith("## "):
            section = line
            lane_section = None
        elif section == "## Lane Sequences" and line.startswith("### `"):
            match = re.fullmatch(r"### `([^`]+)`", line)
            lane_section = None if match is None else match.group(1)
        note = _ALLOWLISTED_NOTE.fullmatch(line)
        if note is not None and section == _APPEND_ONLY_HISTORY_SECTION:
            notes.append(line)
            index += 1
            continue
        if _CANONICAL_GOAL_STATUS_LINE.fullmatch(line):
            guarded.append("<decoded-goal-status>")
            index += 1
            continue
        if _CANONICAL_GOAL_OWNER_LINE.fullmatch(line):
            guarded.append("<decoded-goal-owner>")
            index += 1
            continue
        table_lane_keys: tuple[str, ...] = ()
        if (
            section == "## Lane Map" and line == _LANE_MAP_HEADER
        ) or (
            section == "## Forward Plan By Lane"
            and line == _FORWARD_PLAN_HEADER
        ):
            table_lane_keys = tuple(lane_lines)
        elif (
            section == "## Lane Sequences"
            and line == _LANE_SEQUENCE_HEADER
            and lane_section in lane_lines
        ):
            assert lane_section is not None
            table_lane_keys = (lane_section,)
        if table_lane_keys:
            if index + 1 >= len(lines) or not lines[index + 1].startswith("| ---"):
                raise GoalNativeScopeSourceError(
                    "compatibility_table_noncanonical", "authority table is malformed"
                )
            header = line
            rows: list[str] = []
            index += 2
            while index < len(lines) and lines[index].startswith("|"):
                if not (lines[index].startswith("| ") and lines[index].endswith(" |")):
                    raise GoalNativeScopeSourceError(
                        "compatibility_table_noncanonical",
                        "authority table row formatting is noncanonical",
                    )
                rows.append(lines[index])
                index += 1
            if header in {_LANE_MAP_HEADER, _FORWARD_PLAN_HEADER}:
                for row in rows:
                    cells = tuple(cell.strip() for cell in row.strip("|").split("|"))
                    if len(cells) < 1:
                        raise GoalNativeScopeSourceError(
                            "compatibility_table_noncanonical",
                            "authority table row is empty",
                        )
                    key = cells[0].strip("`")
                    if key not in lane_lines:
                        raise GoalNativeScopeSourceError(
                            "compatibility_table_lane_unknown",
                            "authority table contains unknown lane",
                        )
                    lane_lines[key].append(header)
                    lane_lines[key].append(row)
            else:
                assert lane_section is not None
                lane_lines[lane_section].append(header)
                lane_lines[lane_section].extend(rows)
            guarded.append(f"<decoded-lane-authority-table:{header}>")
            continue
        guarded.append(line)
        index += 1
    lane_guards = {
        lane_key: "goal-lane-compatibility-guard:"
        + fingerprint({"lane_key": lane_key, "lines": values})
        for lane_key, values in lane_lines.items()
    }
    return tuple(guarded), tuple(notes), lane_guards


def _git_blob_oid(value: bytes) -> str:
    body = b"blob " + str(len(value)).encode("ascii") + b"\0" + value
    return hashlib.sha1(body, usedforsecurity=False).hexdigest()
