from __future__ import annotations

import multiprocessing
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import pytest
from aware_file_system.local_json_state import (
    read_json_state_document,
    update_json_state_document,
)


def _add_row(current: dict[str, object], *, key: str) -> dict[str, object]:
    rows = dict(cast("Mapping[str, object]", current.get("rows", {})))
    rows[key] = key
    return {"rows": rows}


def _publish_unique_rows(state_path: str, worker: int, count: int) -> None:
    path = Path(state_path)
    for index in range(count):
        key = f"{worker}:{index}"

        _ = update_json_state_document(
            state_path=path,
            update=lambda current, key=key: _add_row(current, key=key),
            default={"rows": {}},
        )


def test_json_state_update_serializes_processes_without_lost_rows(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    context = multiprocessing.get_context("spawn")
    workers = [
        context.Process(target=_publish_unique_rows, args=(str(state_path), index, 12))
        for index in range(6)
    ]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=20)
        assert worker.exitcode == 0

    document = read_json_state_document(state_path=state_path)
    rows = cast("dict[str, object]", document["rows"])
    assert len(rows) == 72
    assert rows["0:0"] == "0:0"
    assert rows["5:11"] == "5:11"


def test_json_state_invalid_bytes_fail_closed_without_replacement(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    malformed = b'{"valid": true} trailing'
    _ = state_path.write_bytes(malformed)

    with pytest.raises(ValueError, match="Invalid JSON state"):
        _ = update_json_state_document(
            state_path=state_path,
            update=lambda current: current,
        )

    assert state_path.read_bytes() == malformed
