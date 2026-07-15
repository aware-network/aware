from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_meta.commit.store_sync import sync_oig_commit_store


def _write_commit(
    *,
    commits_dir: Path,
    commit_id: UUID,
    parent_commit_id: UUID | None,
) -> None:
    commits_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "commit": {
            "id": str(commit_id),
            "commit_parents": (
                [{"parent_commit_id": str(parent_commit_id)}]
                if parent_commit_id is not None
                else []
            ),
        }
    }
    (commits_dir / f"{commit_id}.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def _write_head(*, lane_dir: Path, commit_id: UUID) -> None:
    lane_dir.mkdir(parents=True, exist_ok=True)
    (lane_dir / "HEAD.json").write_text(
        json.dumps({"v": 1, "commit_id": str(commit_id)}),
        encoding="utf-8",
    )


def test_meta_commit_store_sync_is_meta_owned() -> None:
    assert sync_oig_commit_store.__module__ == "aware_meta.commit.store_sync"


def test_sync_oig_commit_store_copy_if_missing_copies_lane_tree(
    tmp_path: Path,
) -> None:
    src_oig_dir = tmp_path / "bundle" / ".aware" / "oig"
    dest_oig_dir = tmp_path / "pv" / ".aware" / "oig"

    branch_id = uuid4()
    projection_hash = "proj_hash"
    commit_id = uuid4()

    src_lane_dir = src_oig_dir / str(branch_id) / projection_hash
    _write_commit(
        commits_dir=src_lane_dir / "commits",
        commit_id=commit_id,
        parent_commit_id=None,
    )
    _write_head(lane_dir=src_lane_dir, commit_id=commit_id)

    res = sync_oig_commit_store(
        src_oig_dir=src_oig_dir,
        dest_oig_dir=dest_oig_dir,
        mode="copy_if_missing",
    )
    assert res.lanes_seen == 1
    assert res.lanes_copied == 1

    dest_lane_dir = dest_oig_dir / str(branch_id) / projection_hash
    assert (dest_lane_dir / "HEAD.json").exists()
    assert (dest_lane_dir / "commits" / f"{commit_id}.json").exists()

    res2 = sync_oig_commit_store(
        src_oig_dir=src_oig_dir,
        dest_oig_dir=dest_oig_dir,
        mode="copy_if_missing",
    )
    assert res2.lanes_seen == 1
    assert res2.lanes_copied == 0


def test_sync_oig_commit_store_fast_forward_updates_lane_head(
    tmp_path: Path,
) -> None:
    src_oig_dir = tmp_path / "bundle" / ".aware" / "oig"
    dest_oig_dir = tmp_path / "pv" / ".aware" / "oig"

    branch_id = uuid4()
    projection_hash = "proj_hash"
    commit_a = uuid4()
    commit_b = uuid4()

    src_lane_dir = src_oig_dir / str(branch_id) / projection_hash
    _write_commit(
        commits_dir=src_lane_dir / "commits",
        commit_id=commit_a,
        parent_commit_id=None,
    )
    _write_commit(
        commits_dir=src_lane_dir / "commits",
        commit_id=commit_b,
        parent_commit_id=commit_a,
    )
    _write_head(lane_dir=src_lane_dir, commit_id=commit_b)

    dest_lane_dir = dest_oig_dir / str(branch_id) / projection_hash
    _write_commit(
        commits_dir=dest_lane_dir / "commits",
        commit_id=commit_a,
        parent_commit_id=None,
    )
    _write_head(lane_dir=dest_lane_dir, commit_id=commit_a)

    res = sync_oig_commit_store(
        src_oig_dir=src_oig_dir,
        dest_oig_dir=dest_oig_dir,
        mode="fast_forward",
    )
    assert res.lane_heads_fast_forwarded == 1

    head = json.loads((dest_lane_dir / "HEAD.json").read_text(encoding="utf-8"))
    assert head["commit_id"] == str(commit_b)
    assert (dest_lane_dir / "commits" / f"{commit_b}.json").exists()


def test_sync_oig_commit_store_fast_forward_detects_divergence(
    tmp_path: Path,
) -> None:
    src_oig_dir = tmp_path / "bundle" / ".aware" / "oig"
    dest_oig_dir = tmp_path / "pv" / ".aware" / "oig"

    branch_id = uuid4()
    projection_hash = "proj_hash"
    commit_a = uuid4()
    commit_b = uuid4()
    commit_c = uuid4()

    src_lane_dir = src_oig_dir / str(branch_id) / projection_hash
    _write_commit(
        commits_dir=src_lane_dir / "commits",
        commit_id=commit_a,
        parent_commit_id=None,
    )
    _write_commit(
        commits_dir=src_lane_dir / "commits",
        commit_id=commit_b,
        parent_commit_id=commit_a,
    )
    _write_head(lane_dir=src_lane_dir, commit_id=commit_b)

    dest_lane_dir = dest_oig_dir / str(branch_id) / projection_hash
    _write_commit(
        commits_dir=dest_lane_dir / "commits",
        commit_id=commit_c,
        parent_commit_id=None,
    )
    _write_head(lane_dir=dest_lane_dir, commit_id=commit_c)

    with pytest.raises(RuntimeError, match="HEAD divergence"):
        sync_oig_commit_store(
            src_oig_dir=src_oig_dir,
            dest_oig_dir=dest_oig_dir,
            mode="fast_forward",
        )
