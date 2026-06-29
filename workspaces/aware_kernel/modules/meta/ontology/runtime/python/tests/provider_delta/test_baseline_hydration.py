from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_meta.materialization.deltas import baseline


@pytest.mark.asyncio
async def test_runtime_index_full_oig_hydration_prefers_request_baseline_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    semantic_key = (
        "ocg:aware_home/node:aware_home.default.home.RemoteControl"
        "/attribute:selected_channel_id"
    )
    request_baseline_index = {
        semantic_key: {
            "semantic_key": semantic_key,
            "object_id": "baseline-package-index-object-id",
            "object_kind": "attribute",
            "attribute_name": "selected_channel_id",
            "runtime_delta_fingerprint": "sha256:committed-index-fingerprint",
            "semantic_fingerprint": "sha256:committed-index-fingerprint",
            "source_refs": ("home/tv_channel.aware",),
            "attribute_signature": {
                "name": "selected_channel_id",
                "kind": "primitive",
                "primitive_base_type": "uuid",
            },
        }
    }
    request = SimpleNamespace(
        previous_materialization_evidence={
            "baseline_semantic_object_index": request_baseline_index,
        }
    )
    baseline_ref = {
        "semantic_projection_name": "ObjectConfigGraph",
        "semantic_branch_id": str(uuid4()),
        "semantic_object_instance_graph_commit_id": str(uuid4()),
    }
    runtime_index = SimpleNamespace(
        ocg=SimpleNamespace(object_projection_graphs=()),
        opg_by_hash={
            "projection-hash": SimpleNamespace(name="ObjectConfigGraph"),
        },
    )

    class FakeCachedLaneMaterializer:
        async def get(self, **kwargs: object) -> tuple[object, dict[str, object]]:
            timings = kwargs.get("timings")
            metric = getattr(timings, "metric", None)
            if callable(metric):
                metric("oig_materializer_total_ms", 42)
                metric("oig_materializer_snapshot_lookup_ms", 7)
                metric("oig_materializer_base_snapshot_hit", True)
                metric("oig_materializer_target_commit_id", "commit-id")
            return (
                SimpleNamespace(class_instances=(), class_instance_relationships=()),
                {"object_instance_graph_id": "baseline-oig-id"},
            )

        def snapshot_cache_metrics(self) -> dict[str, int]:
            return {
                "cache_hit_count": 1,
                "cache_miss_count": 0,
                "cache_entry_count": 1,
            }

    monkeypatch.setattr(
        baseline,
        "CachedLaneMaterializer",
        FakeCachedLaneMaterializer,
    )

    hydration = await baseline._hydrate_baseline_from_runtime_index(
        request=request,
        index=runtime_index,
        baseline_ref=baseline_ref,
    )

    hydrated_index = hydration["baseline_semantic_object_index"]
    assert isinstance(hydrated_index, dict)
    hydrated_entry = hydrated_index[semantic_key]
    assert isinstance(hydrated_entry, dict)
    assert hydration["status"] == "baseline_hydrated"
    assert hydration["baseline_semantic_object_index_count"] == 1
    assert hydrated_entry["runtime_delta_fingerprint"] == (
        "sha256:committed-index-fingerprint"
    )
    assert hydrated_entry["source"] == (
        "hydrator_payload.baseline_semantic_object_index"
    )
    details = hydration["details"]
    assert isinstance(details, dict)
    materializer_metadata = details["materializer_metadata"]
    assert isinstance(materializer_metadata, dict)
    assert hydration["source"] == "aware_meta.CachedLaneMaterializer"
    assert (
        materializer_metadata["baseline_semantic_object_index_source"]
        == "request.baseline_semantic_object_index"
    )
    assert materializer_metadata["materialization_cache_metrics"] == {
        "cache_hit_count": 1,
        "cache_miss_count": 0,
        "cache_entry_count": 1,
    }
    assert materializer_metadata["oig_materializer_phase_metric_count"] == 4
    assert materializer_metadata["oig_materializer_phase_metrics"] == {
        "oig_materializer_total_ms": 42,
        "oig_materializer_snapshot_lookup_ms": 7,
        "oig_materializer_base_snapshot_hit": True,
        "oig_materializer_target_commit_id": "commit-id",
    }
