"""Local issue-state JSON helpers owned by the Issue SDK."""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_file_system.local_json_state import (
    read_json_state_document,
    update_json_state_document,
    write_json_state_document,
)
from pydantic import BaseModel, ConfigDict, Field

_HEADER_FIELD_PATTERN = re.compile(r"^\s*-\s*([^:]+):\s*(.*)$")
_OWNERSHIP_HEADER = "Ownership Scope"
_WORKFLOW_NAMESPACE = uuid5(NAMESPACE_URL, "aware://workflow/v1")
_CANONICAL_OWNER_PREFIX_PATTERN = re.compile(r"^[a-z][a-z0-9_]*-.+$")
_PROVIDER_KEY_SANITIZER = re.compile(r"[^a-z0-9]+")
_PREFERRED_PROVIDER_KEYS = frozenset({"codex", "claude_code"})


class WorkflowIssueScopePath(BaseModel):
    relative_path: str


class WorkflowIssueUpdateEntry(BaseModel):
    sequence: int
    message: str
    actor_session_id: str | None = None
    outcome: str = "info"
    command: str | None = None
    command_exit_code: int | None = None
    timestamp_utc: datetime | None = None


class WorkflowIssueEvidenceRef(BaseModel):
    sequence: int
    path: str
    description: str | None = None


class WorkflowIssueStateEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    issue_id: UUID
    tag: str
    title: str
    status: str = "open"
    priority_level: str = "medium"
    owner_actor_id: UUID | None = None
    owner_session_id: str | None = None
    overview_content_id: UUID | None = None
    scope_paths: list[WorkflowIssueScopePath] = Field(default_factory=list)
    updates: list[WorkflowIssueUpdateEntry] = Field(default_factory=list)
    evidence_refs: list[WorkflowIssueEvidenceRef] = Field(default_factory=list)
    lane_head_commit_id: UUID | None = None
    function_call_id: UUID | None = None


class WorkflowIssueStateStore(BaseModel):
    model_config = ConfigDict(extra="allow")

    issues_by_id: dict[str, WorkflowIssueStateEntry] = Field(default_factory=dict)
    issue_id_by_tag: dict[str, str] = Field(default_factory=dict)


class IssueDocSnapshot(BaseModel):
    title: str
    tag: str
    status_token: str
    owner_session_id: str | None = None
    ownership_scope: tuple[str, ...] = ()


class WorkflowIssueBootstrapResult(BaseModel):
    issue_id: UUID
    issue_tag: str
    issue_doc_path: str
    state_path: str
    existed_before: bool
    status_token: str
    owner_session_id: str | None = None
    ownership_scope: list[str] = Field(default_factory=list)


def stable_issue_id(*, tag: str) -> UUID:
    canonical_tag = tag.casefold().strip()
    return uuid5(_WORKFLOW_NAMESPACE, f"issue:{canonical_tag}")


def resolve_workflow_issue_state_path(
    *, repo_root: Path, raw_state_path: str | None
) -> Path:
    value = (raw_state_path or "").strip()
    if not value:
        return (repo_root / ".aware" / "workflow_issue" / "state.json").resolve()
    candidate = Path(value).expanduser()
    return (
        candidate.resolve()
        if candidate.is_absolute()
        else (repo_root / candidate).resolve()
    )


def resolve_repo_relative_path(*, repo_root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path.strip()).expanduser()
    resolved = (
        candidate.resolve()
        if candidate.is_absolute()
        else (repo_root / candidate).resolve()
    )
    try:
        resolved.relative_to(repo_root)
    except Exception as exc:
        raise ValueError(f"Path escapes repo root: {resolved}") from exc
    return resolved


def load_workflow_issue_state_store(*, state_path: Path) -> WorkflowIssueStateStore:
    try:
        payload = read_json_state_document(
            state_path=state_path,
            default={"issues_by_id": {}, "issue_id_by_tag": {}},
        )
    except Exception as exc:
        raise ValueError(f"Invalid issue-state JSON at {state_path}: {exc}") from exc
    try:
        return WorkflowIssueStateStore.model_validate(payload)
    except Exception as exc:
        raise ValueError(f"Invalid issue-state schema at {state_path}: {exc}") from exc


def save_workflow_issue_state_store(
    *,
    state_path: Path,
    store: WorkflowIssueStateStore,
) -> None:
    write_json_state_document(
        state_path=state_path,
        document=store.model_dump(mode="json"),
    )


def find_issue_entry_by_tag(
    *,
    store: WorkflowIssueStateStore,
    issue_tag: str,
) -> WorkflowIssueStateEntry | None:
    canonical_tag = issue_tag.casefold().strip()
    issue_id = store.issue_id_by_tag.get(canonical_tag)
    if issue_id:
        entry = store.issues_by_id.get(issue_id)
        if entry is not None:
            return entry
    for candidate in store.issues_by_id.values():
        if candidate.tag.casefold().strip() == canonical_tag:
            return candidate
    return None


def parse_issue_doc_snapshot(*, issue_doc_path: Path) -> IssueDocSnapshot:
    text = issue_doc_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    title = _extract_issue_title(lines=lines)
    tag = ""
    status_value = ""
    owner_value = ""
    inline_scope: tuple[str, ...] = ()

    for line in lines:
        match = _HEADER_FIELD_PATTERN.match(line)
        if not match:
            continue
        key = match.group(1).strip().lower()
        raw_value = match.group(2).strip()
        value = _normalize_header_value(raw_value)
        if key == "tag":
            tag = value
        elif key == "status":
            status_value = value
        elif key == "owner":
            owner_value = value
        elif key == _OWNERSHIP_HEADER.lower():
            inline_scope = _parse_scope_tokens(raw_value)

    section_scope = _parse_scope_section(lines=tuple(lines))
    ownership_scope = _normalize_scope_tokens(tokens=(*inline_scope, *section_scope))
    status_token = _normalize_status_token(status_value)
    owner_session_id = _normalize_owner_session_id(owner_value)

    return IssueDocSnapshot(
        title=title,
        tag=tag.casefold().strip(),
        status_token=status_token,
        owner_session_id=owner_session_id,
        ownership_scope=ownership_scope,
    )


def bootstrap_issue_state_from_doc(
    *,
    repo_root: Path,
    issue_doc_path: Path,
    state_path: Path,
    tag: str | None = None,
    title: str | None = None,
    status_token: str | None = None,
    owner_session_id: str | None = None,
    ownership_scope: tuple[str, ...] = (),
) -> WorkflowIssueBootstrapResult:
    snapshot = parse_issue_doc_snapshot(issue_doc_path=issue_doc_path)
    issue_tag = (tag or snapshot.tag).casefold().strip()
    issue_title = (title or snapshot.title).strip()
    issue_status_token = _normalize_status_token(status_token or snapshot.status_token)
    issue_owner_session = (
        _normalize_owner_session_id(owner_session_id) or snapshot.owner_session_id
    )
    issue_scope = (
        _normalize_scope_tokens(tokens=ownership_scope)
        if ownership_scope
        else snapshot.ownership_scope
    )

    if not issue_tag:
        raise ValueError(
            "Issue tag is required (set `- Tag:` in issue doc or pass --tag)."
        )
    if not issue_title:
        raise ValueError(
            "Issue title is required (set '# Issue: ...' or pass --title)."
        )
    if not issue_status_token:
        raise ValueError(
            "Issue status is required (set `- Status:` or pass --status-token)."
        )
    entry: WorkflowIssueStateEntry | None = None
    existed_before = False

    def update(payload: dict[str, object]) -> dict[str, object]:
        nonlocal entry, existed_before
        store = WorkflowIssueStateStore.model_validate(payload)
        existing = find_issue_entry_by_tag(store=store, issue_tag=issue_tag)
        existed_before = existing is not None
        issue_id = (
            existing.issue_id
            if existing is not None
            else stable_issue_id(tag=issue_tag)
        )
        entry = (
            existing.model_copy(
                update={
                    "tag": issue_tag,
                    "title": issue_title,
                    "status": issue_status_token,
                    "owner_session_id": issue_owner_session,
                    "scope_paths": [
                        WorkflowIssueScopePath(relative_path=value)
                        for value in issue_scope
                    ],
                }
            )
            if existing is not None
            else WorkflowIssueStateEntry(
                issue_id=issue_id,
                tag=issue_tag,
                title=issue_title,
                status=issue_status_token,
                owner_session_id=issue_owner_session,
                scope_paths=[
                    WorkflowIssueScopePath(relative_path=value) for value in issue_scope
                ],
            )
        )
        issue_id_key = str(entry.issue_id)
        store.issues_by_id[issue_id_key] = entry
        store.issue_id_by_tag[issue_tag] = issue_id_key
        return store.model_dump(mode="json")

    try:
        update_json_state_document(
            state_path=state_path,
            update=update,
            default={"issues_by_id": {}, "issue_id_by_tag": {}},
        )
    except Exception as exc:
        raise ValueError(f"Invalid issue-state JSON at {state_path}: {exc}") from exc
    assert entry is not None

    return WorkflowIssueBootstrapResult(
        issue_id=entry.issue_id,
        issue_tag=entry.tag,
        issue_doc_path=issue_doc_path.relative_to(repo_root).as_posix(),
        state_path=state_path.relative_to(repo_root).as_posix(),
        existed_before=existed_before,
        status_token=entry.status,
        owner_session_id=issue_owner_session,
        ownership_scope=[path.relative_path for path in entry.scope_paths],
    )


def sync_issue_state_from_doc(
    *,
    repo_root: Path,
    issue_doc_path: Path,
    state_path: Path,
    issue_tag: str | None = None,
) -> WorkflowIssueBootstrapResult:
    return bootstrap_issue_state_from_doc(
        repo_root=repo_root,
        issue_doc_path=issue_doc_path,
        state_path=state_path,
        tag=issue_tag,
    )


def _extract_issue_title(*, lines: list[str]) -> str:
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("# issue:"):
            return stripped.split(":", 1)[1].strip()
    return ""


def _parse_scope_tokens(value: str) -> tuple[str, ...]:
    if not value:
        return ()
    tokens = [segment.strip() for segment in value.split(",")]
    normalized = [_normalize_header_value(token) for token in tokens if token]
    return tuple(token for token in normalized if token)


def _parse_scope_section(*, lines: tuple[str, ...]) -> tuple[str, ...]:
    in_scope_section = False
    collected: list[str] = []
    for raw_line in lines:
        stripped = raw_line.strip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip().lower()
            in_scope_section = heading == _OWNERSHIP_HEADER.lower()
            continue
        if not in_scope_section or not stripped:
            continue
        if stripped.startswith("- "):
            candidate = _normalize_header_value(stripped[2:])
            if candidate:
                collected.append(candidate)
    return tuple(collected)


def _normalize_scope_tokens(*, tokens: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for token in tokens:
        value = _normalize_header_value(token)
        if not value:
            continue
        if value.startswith("/"):
            raise ValueError(f"Ownership scope must be repo-relative: {value}")
        if "*" in value or "?" in value:
            raise ValueError(f"Ownership scope must not use wildcards: {value}")
        candidate = Path(value)
        if any(part in {"..", "."} for part in candidate.parts):
            raise ValueError(f"Ownership scope must not contain '.' or '..': {value}")
        cleaned = candidate.as_posix().strip("/")
        if cleaned:
            normalized.append(cleaned)
    return tuple(dict.fromkeys(normalized))


def _normalize_header_value(value: str) -> str:
    candidate = str(value).strip()
    if len(candidate) >= 2 and candidate[0] == "`" and candidate[-1] == "`":
        candidate = candidate[1:-1].strip()
    if len(candidate) >= 2 and candidate[0] == '"' and candidate[-1] == '"':
        candidate = candidate[1:-1].strip()
    return candidate


def _normalize_status_token(raw_value: str | None) -> str:
    candidate = _normalize_header_value(raw_value or "")
    if not candidate:
        return ""
    spaced = candidate.lower().replace("-", " ").replace("_", " ")
    return "_".join(spaced.split())


def _normalize_provider_key(raw_value: str | None) -> str | None:
    candidate = _PROVIDER_KEY_SANITIZER.sub(
        "_",
        str(raw_value or "").strip().lower(),
    ).strip("_")
    return candidate or None


def _resolve_default_provider_key() -> str | None:
    provider = _normalize_provider_key(os.environ.get("AWARE_INTERFACE_PROVIDER"))
    if provider:
        return provider
    if (os.environ.get("CODEX_THREAD_ID") or "").strip():
        return "codex"
    return None


def default_owner_execution_id() -> str | None:
    provider = _resolve_default_provider_key()
    if provider is None:
        return None
    provider_session_id = (
        os.environ.get("AWARE_INTERFACE_PROVIDER_SESSION_ID") or ""
    ).strip()
    if not provider_session_id and provider == "codex":
        provider_session_id = (os.environ.get("CODEX_THREAD_ID") or "").strip()
    if not provider_session_id:
        return None
    return f"{provider}-{provider_session_id}"


def normalize_owner_session_id(raw_value: str | None) -> str | None:
    candidate = _normalize_header_value(raw_value or "")
    if not candidate:
        return None
    if candidate.casefold() == "unassigned":
        return None
    if _CANONICAL_OWNER_PREFIX_PATTERN.match(candidate):
        return candidate
    provider = _resolve_default_provider_key() or "codex"
    return f"{provider}-{candidate}"


def normalize_owner_session_token(raw_value: str | None) -> str | None:
    candidate = _normalize_header_value(raw_value or "")
    if not candidate:
        return None
    if candidate.casefold() == "unassigned":
        return None
    provider = _resolve_default_provider_key()
    if provider is None:
        return normalize_owner_session_id(candidate)
    if candidate.startswith(f"{provider}-"):
        return candidate
    if any(
        candidate.startswith(f"{known_provider}-")
        for known_provider in _PREFERRED_PROVIDER_KEYS
    ):
        return candidate
    return f"{provider}-{candidate}"


def _normalize_owner_session_id(raw_value: str | None) -> str | None:
    return normalize_owner_session_id(raw_value)


__all__ = [
    "IssueDocSnapshot",
    "WorkflowIssueBootstrapResult",
    "WorkflowIssueEvidenceRef",
    "WorkflowIssueScopePath",
    "WorkflowIssueStateEntry",
    "WorkflowIssueStateStore",
    "WorkflowIssueUpdateEntry",
    "bootstrap_issue_state_from_doc",
    "default_owner_execution_id",
    "find_issue_entry_by_tag",
    "load_workflow_issue_state_store",
    "normalize_owner_session_id",
    "normalize_owner_session_token",
    "parse_issue_doc_snapshot",
    "resolve_repo_relative_path",
    "resolve_workflow_issue_state_path",
    "save_workflow_issue_state_store",
    "stable_issue_id",
    "sync_issue_state_from_doc",
]
