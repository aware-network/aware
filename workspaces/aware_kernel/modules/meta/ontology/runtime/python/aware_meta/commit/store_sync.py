from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from uuid import UUID

OIGCommitStoreSyncMode = Literal["off", "copy_if_missing", "fast_forward"]


@dataclass(frozen=True, slots=True)
class OIGCommitStoreSyncResult:
    mode: OIGCommitStoreSyncMode
    lanes_seen: int = 0
    lanes_copied: int = 0
    lane_heads_copied: int = 0
    lane_heads_fast_forwarded: int = 0
    commits_copied: int = 0
    hint_files_copied: int = 0


def sync_oig_commit_store(
    *,
    src_oig_dir: Path,
    dest_oig_dir: Path,
    mode: OIGCommitStoreSyncMode = "copy_if_missing",
) -> OIGCommitStoreSyncResult:
    """Sync bundle commit-store lanes into the local Meta OIG store."""

    if mode not in {"off", "copy_if_missing", "fast_forward"}:
        raise ValueError(f"Unsupported OIG commit store sync mode: {mode!r}")

    result = OIGCommitStoreSyncResult(mode=mode)
    if mode == "off":
        return result

    if not src_oig_dir.exists() or not src_oig_dir.is_dir():
        return result

    dest_oig_dir.mkdir(parents=True, exist_ok=True)

    lanes_seen = lanes_copied = 0
    heads_copied = heads_fast_forwarded = 0
    commits_copied = hint_files_copied = 0

    for branch_dir in src_oig_dir.iterdir():
        if not branch_dir.is_dir():
            continue
        try:
            branch_id = UUID(branch_dir.name)
        except Exception:
            continue

        for proj_dir in branch_dir.iterdir():
            if not proj_dir.is_dir():
                continue
            projection_hash = proj_dir.name
            if not projection_hash:
                continue

            lanes_seen += 1
            dest_lane_dir = dest_oig_dir / str(branch_id) / projection_hash

            if mode == "copy_if_missing":
                if _copy_lane_tree_if_missing(
                    src_lane_dir=proj_dir,
                    dest_lane_dir=dest_lane_dir,
                ):
                    lanes_copied += 1
                continue

            if _copy_lane_tree_if_missing(
                src_lane_dir=proj_dir,
                dest_lane_dir=dest_lane_dir,
            ):
                lanes_copied += 1
                continue

            src_head_path = proj_dir / "HEAD.json"
            dest_head_path = dest_lane_dir / "HEAD.json"
            dest_commits_dir = dest_lane_dir / "commits"

            copied_commits, copied_hints = _copy_missing_lane_payloads(
                src_lane_dir=proj_dir,
                dest_lane_dir=dest_lane_dir,
            )
            commits_copied += copied_commits
            hint_files_copied += copied_hints

            src_head_commit_id = _read_head_commit_id(head_path=src_head_path)
            dest_head_commit_id = _read_head_commit_id(head_path=dest_head_path)

            if dest_head_commit_id is None and src_head_path.exists():
                _atomic_copy(src=src_head_path, dest=dest_head_path)
                heads_copied += 1
                continue

            if (
                src_head_commit_id is None
                or dest_head_commit_id is None
                or src_head_commit_id == dest_head_commit_id
            ):
                continue

            if _is_ancestor_commit_id(
                ancestor_commit_id=src_head_commit_id,
                descendant_commit_id=dest_head_commit_id,
                commits_dir=dest_commits_dir,
            ):
                continue

            if _is_ancestor_commit_id(
                ancestor_commit_id=dest_head_commit_id,
                descendant_commit_id=src_head_commit_id,
                commits_dir=dest_commits_dir,
            ):
                _atomic_copy(src=src_head_path, dest=dest_head_path)
                heads_fast_forwarded += 1
                continue

            raise RuntimeError(
                "OIG lane HEAD divergence detected (refusing to sync). "
                "lane=(%s, %s) runtime_head=%s bundle_head=%s"
                % (
                    branch_id,
                    projection_hash,
                    dest_head_commit_id,
                    src_head_commit_id,
                )
            )

    return OIGCommitStoreSyncResult(
        mode=mode,
        lanes_seen=lanes_seen,
        lanes_copied=lanes_copied,
        lane_heads_copied=heads_copied,
        lane_heads_fast_forwarded=heads_fast_forwarded,
        commits_copied=commits_copied,
        hint_files_copied=hint_files_copied,
    )


def _copy_missing_lane_payloads(
    *,
    src_lane_dir: Path,
    dest_lane_dir: Path,
) -> tuple[int, int]:
    commits_copied = 0
    hint_files_copied = 0

    src_commits_dir = src_lane_dir / "commits"
    dest_commits_dir = dest_lane_dir / "commits"
    if src_commits_dir.exists() and src_commits_dir.is_dir():
        for entry in src_commits_dir.iterdir():
            if not entry.is_file():
                continue
            if not (entry.name.endswith(".json") or entry.name.endswith(".meta.json")):
                continue
            dest_entry = dest_commits_dir / entry.name
            if dest_entry.exists():
                continue
            _atomic_copy(src=entry, dest=dest_entry)
            commits_copied += 1

    src_hints_dir = src_lane_dir / "hints"
    if src_hints_dir.exists() and src_hints_dir.is_dir():
        for entry in src_hints_dir.rglob("*"):
            if not entry.is_file():
                continue
            if "locks" in entry.parts:
                continue
            rel = entry.relative_to(src_lane_dir)
            dest_entry = dest_lane_dir / rel
            if dest_entry.exists():
                continue
            _atomic_copy(src=entry, dest=dest_entry)
            hint_files_copied += 1

    return commits_copied, hint_files_copied


def _atomic_copy(*, src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    with open(src, "rb") as reader, open(tmp, "wb") as writer:
        shutil.copyfileobj(reader, writer)
        writer.flush()
        os.fsync(writer.fileno())
    tmp.replace(dest)


def _read_head_commit_id(*, head_path: Path) -> UUID | None:
    if not head_path.exists():
        return None
    try:
        raw = json.loads(head_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Unreadable lane HEAD.json: {head_path}") from exc
    if not isinstance(raw, dict):
        raise RuntimeError(
            f"Invalid lane HEAD.json payload (expected object): {head_path}"
        )
    cid = raw.get("commit_id")
    if not cid:
        return None
    return UUID(str(cid))


def _read_parent_commit_id(*, commit_path: Path) -> UUID | None:
    try:
        raw = json.loads(commit_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Unreadable commit file: {commit_path}") from exc

    if not isinstance(raw, dict):
        raise RuntimeError(f"Invalid commit payload (expected object): {commit_path}")
    commit_obj = raw.get("commit") or {}
    if not isinstance(commit_obj, dict):
        raise RuntimeError(
            f"Invalid commit.commit payload (expected object): {commit_path}"
        )

    parents = commit_obj.get("commit_parents") or []
    if parents is None:
        parents = []
    if not isinstance(parents, list):
        raise RuntimeError(
            f"Invalid commit.commit_parents payload (expected list): {commit_path}"
        )
    if len(parents) > 1:
        raise RuntimeError(f"Non-linear commit has {len(parents)} parents: {commit_path}")
    if not parents:
        return None

    entry = parents[0]
    if not isinstance(entry, dict):
        raise RuntimeError(
            f"Invalid commit parent payload (expected object): {commit_path}"
        )
    parent_id = entry.get("parent_commit_id")
    if not parent_id:
        return None
    return UUID(str(parent_id))


def _is_ancestor_commit_id(
    *,
    ancestor_commit_id: UUID,
    descendant_commit_id: UUID,
    commits_dir: Path,
) -> bool:
    cur: UUID | None = descendant_commit_id
    seen: set[UUID] = set()
    while cur is not None and cur not in seen:
        if cur == ancestor_commit_id:
            return True
        seen.add(cur)
        commit_path = commits_dir / f"{cur}.json"
        if not commit_path.exists():
            return False
        cur = _read_parent_commit_id(commit_path=commit_path)
    return False


def _copy_lane_tree_if_missing(*, src_lane_dir: Path, dest_lane_dir: Path) -> bool:
    if dest_lane_dir.exists():
        return False
    dest_lane_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        src_lane_dir,
        dest_lane_dir,
        ignore=_ignored_lane_tree_entries,
        dirs_exist_ok=False,
    )
    return True


def _ignored_lane_tree_entries(_dir: str, entries: list[str]) -> set[str]:
    ignored = {".DS_Store", "__pycache__", "locks"}
    return ignored.intersection(entries)


__all__ = [
    "OIGCommitStoreSyncMode",
    "OIGCommitStoreSyncResult",
    "sync_oig_commit_store",
]
