from __future__ import annotations

from aware_meta.materialization.deltas.dirty_diff import (
    _semantic_dirty_entry_with_baseline_match,
    _semantic_dirty_entries_with_relationship_support_normalization,
)


def test_meta_provider_delta_function_impl_signature_match_is_noop() -> None:
    semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.TvChannel.rename"
        "/function_impl:default"
    )
    signature = {
        "function_name": "rename",
        "function_owner_key": "aware_demo.default.home.TvChannel",
        "instruction_count": 0,
        "instruction_summaries": [],
        "instructions": [],
        "key": "default",
        "kind": "instruction_body",
    }

    dirty_entry = _semantic_dirty_entry_with_baseline_match(
        entry={
            "semantic_key": semantic_key,
            "ontology_subject_kind": "function_impl",
            "dirty_operation": "function_impl_upsert",
            "semantic_fingerprint": "sha256:current-source-ref-fingerprint",
            "function_impl_signature": signature,
            "payload": {
                "function_impl_signature": signature,
                "source_refs": ("structure/ontology/aware/home/tv_channel.aware",),
            },
        },
        semantic_key=semantic_key,
        baseline_entry={
            "object_id": "baseline-function-impl-id",
            "object_kind": "function_impl",
            "semantic_fingerprint": "sha256:baseline-source-ref-fingerprint",
            "function_impl_signature": signature,
            "payload": {
                "function_impl_signature": signature,
                "source_refs": ("home/tv_channel.aware",),
            },
        },
        baseline_commit_id="baseline-oig-commit",
    )

    assert dirty_entry["baseline_compare_operation"] == "noop"
    assert dirty_entry["baseline_compare_status"] == "baseline_object_unchanged"
    assert dirty_entry["dirty_operation"] == "function_impl_noop"


def test_meta_provider_delta_relationship_support_attribute_updates_defer_to_relationship() -> (
    None
):
    relationship_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.RemoteControl:"
        "selected_channel:many_to_one:aware_demo.default.home.TvChannel"
    )
    attribute_semantic_key = (
        "ocg:aware_demo/node:aware_demo.default.home.RemoteControl"
        "/attribute:selected_channel_id"
    )
    relationship_entry = {
        "semantic_key": relationship_semantic_key,
        "ontology_subject_kind": "relationship",
        "dirty_operation": "relationship_update",
        "baseline_compare_operation": "update",
        "relationship_key": "selected_channel",
        "payload": {
            "relationship_signature": {
                "relationship_key": "selected_channel",
                "forward_loading_strategy": "eager",
            },
        },
    }
    attribute_entry = {
        "semantic_key": attribute_semantic_key,
        "ontology_subject_kind": "attribute",
        "dirty_operation": "attribute_update",
        "baseline_compare_operation": "update",
        "baseline_compare_status": "baseline_object_matched",
        "attribute_signature": {
            "kind": "primitive",
            "name": "selected_channel_id",
            "primitive_base_type": "uuid",
            "is_required": False,
        },
        "baseline_object": {
            "attribute_signature": {
                "kind": "primitive",
                "name": "selected_channel_id",
                "primitive_base_type": "uuid",
                "is_required": True,
            },
        },
        "payload": {
            "attribute_signature": {
                "kind": "primitive",
                "name": "selected_channel_id",
                "primitive_base_type": "uuid",
                "is_required": False,
            },
        },
    }

    normalized = _semantic_dirty_entries_with_relationship_support_normalization(
        dirty_entries=(attribute_entry, relationship_entry),
    )

    attribute = normalized[0]
    assert attribute["dirty_operation"] == "attribute_noop"
    assert attribute["baseline_compare_operation"] == "noop"
    assert attribute["baseline_compare_status"] == (
        "relationship_support_attribute_deferred_to_relationship_update"
    )
    assert attribute["relationship_support_attribute_deferred_to"] == (
        relationship_semantic_key
    )
    assert normalized[1]["dirty_operation"] == "relationship_update"
