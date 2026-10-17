"""Pure optional bytes codec; original journal replay remains authoritative."""

from __future__ import annotations

import importlib.util
import json
import os
import random
import subprocess
import sys
from pathlib import Path

import pytest
from aware_workspace_fs_adapter.repository_index_journal import _apply_delta

SDK = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def bytes_native(tmp_path_factory):
    root = tmp_path_factory.mktemp("workspace-index-bytes-native")
    result = subprocess.run(
        [sys.executable, str(SDK / "hatch_build.py"), "--output-directory", str(root)],
        capture_output=True,
        text=True,
        check=True,
        timeout=130,
    )
    (root / "build-evidence.json").write_text(result.stdout)
    evidence = json.loads(result.stdout)
    if evidence["status"] != "compiled":
        pytest.skip(evidence["reason"])
    spec = importlib.util.spec_from_file_location("_tree_native", evidence["artifact"])
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.INDEX_BYTES_DELTA_ABI == 1
    return module


@pytest.mark.parametrize("seed", range(24))
def test_exact_byte_roundtrip_for_insert_delete_replace_reorder(bytes_native, seed):
    rng = random.Random(seed)
    previous = rng.randbytes(18000) if seed % 2 else (b"original-record," * 1500)
    cases = [b"", previous, previous + b"new-row", b"prefix" + previous]
    for _ in range(12):
        start, stop = sorted(rng.sample(range(len(previous) + 1), 2))
        cases.extend(
            (
                previous[:start] + rng.randbytes(100) + previous[stop:],
                previous[stop:] + previous[:start] + previous[start:stop],
            )
        )
    for current in cases:
        delta = bytes_native.index_bytes_delta(previous, current)
        assert delta is None or _apply_delta(previous, delta, len(current)) == current
        assert previous == bytes(previous) and current == bytes(current)


def test_canonical_index_append_is_compact_and_old_field_changes_are_exact(
    bytes_native,
):
    previous = json.dumps(
        {"records": [{"path": str(i), "body": "old"} for i in range(1000)]},
        sort_keys=True,
    ).encode()
    payload = json.loads(previous)
    payload["records"].append({"path": "next", "body": "new"})
    current = json.dumps(payload, sort_keys=True).encode()
    delta = bytes_native.index_bytes_delta(previous, current)
    assert delta is not None and len(delta) < len(current) // 20
    assert _apply_delta(previous, delta, len(current)) == current
    payload["records"][0]["body"] = "changed-old-field"
    changed = json.dumps(payload, sort_keys=True).encode()
    delta = bytes_native.index_bytes_delta(current, changed)
    assert delta is not None and _apply_delta(current, delta, len(changed)) == changed


@pytest.mark.parametrize(
    "previous,current",
    [(b"", b""), (b"", b"a"), (b"x", b""), (bytes(range(256)), b"NaN -0.0 \\ud800")],
)
def test_empty_short_and_binary_inputs(bytes_native, previous, current):
    delta = bytes_native.index_bytes_delta(previous, current)
    assert delta is not None and _apply_delta(previous, delta, len(current)) == current


def test_exact_limit_and_full_fallback_preserve_input_quota(bytes_native):
    previous = b"a" * (32 * 1024 * 1024)
    delta = bytes_native.index_bytes_delta(previous, previous)
    assert (
        delta is not None and _apply_delta(previous, delta, len(previous)) == previous
    )
    assert bytes_native.index_bytes_delta(previous + b"x", b"short") is None
    assert bytes_native.index_bytes_delta(b"short", previous + b"x") is None


@pytest.mark.parametrize("value", [None, "bytes", bytearray(b"x"), memoryview(b"x"), 1])
def test_foreign_shapes_refuse_without_coercion(bytes_native, value):
    with pytest.raises(TypeError, match="exact previous/current"):
        bytes_native.index_bytes_delta(value, b"exact")
    with pytest.raises(TypeError, match="exact previous/current"):
        bytes_native.index_bytes_delta(b"exact", value)


def test_bytes_subclass_never_dispatches_foreign_behavior(bytes_native):
    calls = []

    class Foreign(bytes):
        def __bytes__(self):
            calls.append(True)
            raise AssertionError("foreign")

    with pytest.raises(TypeError):
        bytes_native.index_bytes_delta(Foreign(b"x"), b"x")
    assert calls == []


def test_random_literal_fallback_never_emits_invalid_program(bytes_native):
    for size in (0, 1, 15, 16, 31, 32, 63, 64, 512, 100000):
        old, new = os.urandom(size), os.urandom(size)
        delta = bytes_native.index_bytes_delta(old, new)
        assert delta is None or _apply_delta(old, delta, len(new)) == new


def test_program_never_exceeds_full_literal_bound(bytes_native):
    previous = b"a" * 16
    current = b"b" * 16 + previous + b"c" * 16
    delta = bytes_native.index_bytes_delta(previous, current)
    assert delta is None or len(delta) <= len(current) + 25


def test_binding_rejects_same_module_wrong_builtin_and_wrong_abi(
    bytes_native, monkeypatch
):
    import aware_workspace_sdk
    from aware_workspace_sdk._tree_native_binding import prepare_index_delta

    monkeypatch.setattr(
        aware_workspace_sdk, "_tree_native", bytes_native, raising=False
    )
    original = bytes_native.index_bytes_delta
    assert prepare_index_delta() is original
    monkeypatch.setattr(bytes_native, "index_bytes_delta", bytes_native.verify)
    assert prepare_index_delta() is None
    monkeypatch.setattr(bytes_native, "index_bytes_delta", original)
    for abi in (True, 0, "1"):
        monkeypatch.setattr(bytes_native, "INDEX_BYTES_DELTA_ABI", abi)
        assert prepare_index_delta() is None
