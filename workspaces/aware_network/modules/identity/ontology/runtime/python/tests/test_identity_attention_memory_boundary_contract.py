from __future__ import annotations

import importlib
import tomllib

from ._paths import (
    IDENTITY_AWARE_ROOT,
    IDENTITY_ONTOLOGY_ROOT,
    IDENTITY_RUNTIME_SOURCE_ROOT,
    IDENTITY_STRUCTURE_ROOT,
)


_MOVED_SOURCE_TOKENS = (
    "ActorFocus",
    "ActorFocusEvidence",
    "ActorFocusRequest",
    "ActorFocusScope",
    "ActorFocusScopeEvidence",
    "ActorFocusScopeRequest",
    "FocusScope",
    "MemoryWorking",
    "MemoryWorkingAttentionFrame",
    "MemoryWorkingItem",
)

_MOVED_RUNTIME_SYMBOLS = (
    "stable_actor_focus_id",
    "stable_actor_focus_scope_id",
    "stable_actor_focus_scope_request_id",
    "stable_memory_working_id",
    "stable_memory_working_item_id",
    "memory_working_lane_key",
    "stable_actor_focus_lane_id",
)


def _toml(path):
    return tomllib.loads(path.read_text(encoding="utf-8"))


def test_identity_manifests_do_not_depend_on_attention_or_memory() -> None:
    manifests = (
        IDENTITY_STRUCTURE_ROOT / "aware.toml",
        IDENTITY_ONTOLOGY_ROOT / "aware.ontology.toml",
    )
    for manifest in manifests:
        package_names = {
            dependency["package_name"]
            for dependency in _toml(manifest).get("dependencies", [])
        }
        assert "attention-ontology" not in package_names
        assert "memory-ontology" not in package_names


def test_identity_structure_no_longer_declares_attention_or_memory_objects() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in IDENTITY_AWARE_ROOT.rglob("*.aware")
        if path.is_file() and ".aware/" not in path.as_posix()
    )

    for token in _MOVED_SOURCE_TOKENS:
        assert token not in source_text
    assert "aware_attention." not in source_text
    assert "aware_memory." not in source_text


def test_identity_runtime_facades_do_not_export_moved_attention_or_memory() -> None:
    actor_facade = importlib.import_module("aware_identity.actor")
    stable_ids = importlib.import_module("aware_identity.stable_ids")

    for symbol in (
        "ActorFocusMaterializationContext",
        "ensure_actor_focus",
        "ensure_actor_focus_scope",
        "request_actor_focus",
        "resolve_actor_focuses",
        "resolve_actor_focus_scopes",
    ):
        assert not hasattr(actor_facade, symbol)

    for symbol in _MOVED_RUNTIME_SYMBOLS:
        assert not hasattr(stable_ids, symbol)

    assert not (IDENTITY_RUNTIME_SOURCE_ROOT / "actor" / "focus.py").exists()
    assert not (
        IDENTITY_RUNTIME_SOURCE_ROOT / "memory_working_item_frame_support.py"
    ).exists()
