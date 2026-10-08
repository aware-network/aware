from __future__ import annotations

import io
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from aware_file_system.index import index_storage as storage_module  # noqa: E402
from aware_file_system.index.file_metadata_cached import FileMetadataCached  # noqa: E402
from aware_file_system.index.index_storage import (  # noqa: E402
    IndexData,
    IndexEntry,
    IndexStorage,
)


def _entry(path: str = "a.py") -> dict[str, Any]:
    return {
        "metadata": {
            "path": path, "name": Path(path).name, "size": 7,
            "last_modified": "2026-10-03T12:00:00", "mtime_ns": 123456789,
            "file_type": "text", "mime_type": "text/plain", "depth": 0,
            "hash": None, "hash_computed": False,
        },
        "last_checked": "2026-10-03T12:00:00",
        "is_valid": True,
    }


def _body(entries: dict[str, Any]) -> str:
    return json.dumps({
        "version": "1.0", "timestamp": "2026-10-03T12:00:00",
        "entries": entries,
    }, ensure_ascii=False)


def _legacy_result(raw: str) -> dict[str, FileMetadataCached] | None:
    """The pre-repair whole-file decoding/validation law, as a test oracle."""
    try:
        data = json.loads(raw)
        header = IndexData(
            version=data.get("version", ""),
            timestamp=datetime.fromisoformat(
                data.get("timestamp", datetime.now().isoformat())
            ),
            entries={},
        )
        if header.version != "1.0":
            return None
        result = {}
        for path, entry in data.get("entries", {}).items():
            try:
                result[path] = IndexEntry(**entry).metadata
            except Exception:
                continue
        return result
    except Exception:
        return None


@pytest.mark.parametrize("chunk_size", [1, 2, 7, 64 * 1024])
def test_streamed_index_preserves_metadata_and_roundtrip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, chunk_size: int,
) -> None:
    monkeypatch.setattr(storage_module, "_INDEX_JSON_READ_SIZE", chunk_size)
    path = tmp_path / "index.json"
    entry = _entry('nested/café-"quoted".py')
    entry["metadata"]["size"] = 1.25e2
    entry["extra"] = [None, True, {"unknown": "\\escaped\n"}]
    raw = _body({entry["metadata"]["path"]: entry, "bad.py": {"metadata": {}}})
    path.write_text(raw, encoding="utf-8")
    storage = IndexStorage(str(path))
    observed = storage.load_index()
    assert observed == _legacy_result(raw)
    assert observed is not None and len(observed) == 1
    assert storage.save_index(observed)
    assert storage.load_index() == observed


@pytest.mark.parametrize("raw", [
    "", "[]", "null", "{}", '{"version":"wrong","entries":{}}',
    '{"version":"1.0","timestamp":null,"entries":{}}',
    '{"version":"1.0","entries":[]}',
    '{"version":"1.0","entries":null}',
    '{"version":"1.0","entries":{}} trailing',
    '{"version":"1.0","entries":{},}',
    '{"version":"1.0","entries":{"bad":',
    '{"version":"1.0"}',
    '{"entries":{},"version":"1.0","unknown":[1e+2,-2.5,null]}',
    '{"version":"1.0","unknown":1e+2,"entries":{}}',
    '{"version":"1.0","unknown":-1.25e-3,"entries":{}}',
    '{"version":"1.0","unknown":NaN,"entries":{}}',
    '{"version":"wrong","version":"1.0","entries":{}}',
])
@pytest.mark.parametrize("chunk_size", [1, 7, 64 * 1024])
def test_streamed_index_matches_legacy_corruption_and_header_rules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, raw: str, chunk_size: int,
) -> None:
    monkeypatch.setattr(storage_module, "_INDEX_JSON_READ_SIZE", chunk_size)
    path = tmp_path / "index.json"
    path.write_text(raw, encoding="utf-8")
    assert IndexStorage(str(path)).load_index() == _legacy_result(raw)


@pytest.mark.parametrize("chunk_size", [1, 7, 64 * 1024])
def test_duplicate_entry_and_entries_bodies_use_only_final_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, chunk_size: int,
) -> None:
    monkeypatch.setattr(storage_module, "_INDEX_JSON_READ_SIZE", chunk_size)
    good = json.dumps(_entry())
    for members in (
        f'"entries":{{"a.py":{good},"a.py":{{}}}}',
        f'"entries":{{"a.py":{{}},"a.py":{good}}}',
        f'"entries":{{"a.py":{good}}},"entries":{{}}',
        f'"entries":null,"entries":{{"a.py":{good}}}',
        f'"entries":[],"entries":{{"a.py":{good}}}',
        f'"entries":{{"a.py":{good}}},"entries":null',
        f'"entries":{{"a.py":{{}},"b.py":{good},"a.py":{good}}}',
        f'"entries":{{"a.py":{good},"b.py":{good},"a.py":{good}}}',
    ):
        raw = '{"version":"1.0",' + members + '}'
        path = tmp_path / "index.json"
        path.write_text(raw, encoding="utf-8")
        observed = IndexStorage(str(path)).load_index()
        expected = _legacy_result(raw)
        assert observed == expected
        if observed is not None:
            assert expected is not None
            assert list(observed) == list(expected)


def test_index_loader_never_requests_a_whole_file_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = _body({f"{number}.py": _entry(f"{number}.py") for number in range(300)})
    path = tmp_path / "index.json"
    path.write_text(raw, encoding="utf-8")
    reads: list[int] = []

    class BoundedRead(io.StringIO):
        def read(self, size: int | None = -1) -> str:
            assert size is not None and 0 < size <= 64 * 1024
            reads.append(size)
            return super().read(size)

    monkeypatch.setattr(storage_module, "open", lambda *a, **kw: BoundedRead(raw), raising=False)
    result = IndexStorage(str(path)).load_index()
    assert result is not None and len(result) == 300
    assert len(reads) >= 2


def test_failed_tail_does_not_publish_partially_decoded_members(tmp_path: Path) -> None:
    raw = _body({"a.py": _entry()})[:-1]
    path = tmp_path / "index.json"
    path.write_text(raw, encoding="utf-8")
    assert IndexStorage(str(path)).load_index() is None


def test_utf8_corruption_and_nested_entry_impostor_reject(tmp_path: Path) -> None:
    path = tmp_path / "index.json"
    path.write_bytes(b'{"version":"1.0","entries":{}}\xff')
    assert IndexStorage(str(path)).load_index() is None
    entry = _entry()
    entry["metadata"] = _entry("impostor.py")
    raw = _body({"a.py": entry})
    path.write_text(raw, encoding="utf-8")
    assert IndexStorage(str(path)).load_index() == _legacy_result(raw) == {}
