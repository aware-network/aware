from __future__ import annotations

from types import SimpleNamespace

from aware_meta.graph.config.lane import delta_commit


def test_explicit_delta_full_fallback_guard_blocks_broad_oig(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "AWARE_OCG_EXPLICIT_DELTA_FULL_FALLBACK_MAX_OIG_OBJECTS",
        "3",
    )

    reason = delta_commit._explicit_delta_full_fallback_guard_reason(  # noqa: SLF001
        before_oig=SimpleNamespace(
            class_instances=[object(), object()],
            class_instance_relationships=[object(), object()],
        ),
        after_oig=SimpleNamespace(
            class_instances=[object()],
            class_instance_relationships=[object()],
        ),
        delta_node_count=1,
        candidate_id_count=1,
        fallback_reason="validation_hash_mismatch",
    )

    assert reason is not None
    assert "explicit_delta_full_fallback_guard" in reason
    assert "limit=3" in reason
    assert "max_oig_objects=4" in reason


def test_explicit_delta_full_fallback_guard_can_be_disabled(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "AWARE_OCG_EXPLICIT_DELTA_FULL_FALLBACK_MAX_OIG_OBJECTS",
        "0",
    )

    reason = delta_commit._explicit_delta_full_fallback_guard_reason(  # noqa: SLF001
        before_oig=SimpleNamespace(
            class_instances=[object(), object(), object(), object()],
            class_instance_relationships=[object()],
        ),
        after_oig=SimpleNamespace(class_instances=[], class_instance_relationships=[]),
        delta_node_count=1,
        candidate_id_count=1,
        fallback_reason="validation_hash_mismatch",
    )

    assert reason is None
