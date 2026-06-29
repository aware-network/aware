from __future__ import annotations

from aware_code.semantic_materialization import (
    SEMANTIC_PROVIDER_DELTA_EVENT_REPORT_CONTRACT_VERSION,
    SemanticProviderDeltaEventReport,
    semantic_provider_delta_events_from_payloads,
)


def test_semantic_provider_delta_event_report_normalizes_meta_report() -> None:
    report = SemanticProviderDeltaEventReport.from_payload(
        {
            "report_kind": "meta_ocg_provider_delta_semantic_dirty_event_report",
            "contract_version": (
                "aware.meta.ocg.provider-delta-semantic-dirty-event-report.v1"
            ),
            "status": "semantic_dirty_event_report_ready",
            "reason": "meta_ocg_provider_delta_semantic_dirty_events_translated",
            "source": "aware_meta.provider_delta.semantic_dirty_diff",
            "provider_key": "aware_meta",
            "semantic_dirty_diff_status": "semantic_dirty_diff_ready",
            "provider_delta_typed_operation_status": "typed_operation_plan_ready",
            "semantic_world_change_events": (
                {
                    "event_kind": (
                        "meta_ocg_provider_delta_semantic_world_change_event"
                    ),
                    "contract_version": (
                        "aware.meta.ocg.provider-delta-semantic-world-change-event.v1"
                    ),
                    "event_key": (
                        "aware_meta.provider_delta.world_change.attribute.update"
                    ),
                    "event_type": "semantic_world_change_preview",
                    "summary": "Update attribute `name` on `TvChannel`.",
                    "semantic_key": ("ocg:aware_home/node:TvChannel/attribute:name"),
                    "verb": "update",
                    "subject_type": "attribute",
                    "ontology_subject_kind": "attribute",
                    "subject_label": "name",
                    "source_refs": ("home/tv_channel.aware",),
                    "condition_keys": (
                        "meta.provider_delta.semantic_dirty_diff_ready",
                    ),
                },
            ),
            "readable_semantic_event_chain": {
                "chain_kind": "meta_ocg_provider_delta_readable_semantic_event_chain",
                "contract_version": (
                    "aware.meta.ocg.provider-delta-readable-semantic-event-chain.v1"
                ),
                "status": "readable_semantic_event_chain_ready",
                "event_count": 1,
                "lines": ("1. Update attribute `name` on `TvChannel`.",),
                "markdown": "1. Update attribute `name` on `TvChannel`.",
            },
        }
    )

    assert report.ready is True
    assert report.provider_key == "aware_meta"
    assert report.provider_report_contract_version == (
        "aware.meta.ocg.provider-delta-semantic-dirty-event-report.v1"
    )
    assert report.semantic_dirty_diff_status == "semantic_dirty_diff_ready"
    assert report.typed_operation_status == "typed_operation_plan_ready"
    assert report.event_count == 1
    assert report.events[0].provider_event_kind == (
        "meta_ocg_provider_delta_semantic_world_change_event"
    )
    assert report.events[0].operation == "update"
    assert report.events[0].ontology_subject_kind == "attribute"
    assert report.events[0].source_refs == ("home/tv_channel.aware",)
    assert report.readable_event_chain.markdown == (
        "1. Update attribute `name` on `TvChannel`."
    )
    assert report.evidence_payload()["contract_version"] == (
        SEMANTIC_PROVIDER_DELTA_EVENT_REPORT_CONTRACT_VERSION
    )


def test_semantic_provider_delta_event_report_normalizes_api_report() -> None:
    report = SemanticProviderDeltaEventReport.from_payload(
        {
            "report_kind": "api_provider_delta_materialization_event_report",
            "contract_version": (
                "aware.api.provider-delta-materialization-event-report.v1"
            ),
            "status": "api_materialization_event_report_ready",
            "reason": "api_provider_delta_materialization_events_ready",
            "source": "aware_api.provider_delta.typed_operations",
            "provider_key": "aware_api",
            "semantic_dirty_diff_status": "semantic_dirty_diff_ready",
            "current_delta_fingerprint": "sha256:api-current",
            "head_refs": {
                "semantic_branch_id": "semantic-branch-id",
            },
            "baseline_refs": {
                "semantic_object_instance_graph_commit_id": "baseline-oig",
            },
            "materialization_events": (
                {
                    "event_kind": "api_provider_delta_materialization_event",
                    "contract_version": (
                        "aware.api.provider-delta-materialization-event.v1"
                    ),
                    "event_key": ("aware_api.materialization.api_capability.update"),
                    "event_type": "api_materialization_event_preview",
                    "summary": (
                        "Update generated api-client artifacts for toggle_door."
                    ),
                    "semantic_key": "api:home_devices/capability:toggle_door",
                    "verb": "update",
                    "subject_type": "api_capability",
                    "ontology_subject_kind": "api_capability",
                    "subject_label": "toggle_door",
                    "source_refs": ("bindings/home_devices.apis.aware",),
                    "condition_keys": (
                        "api.provider_delta.runtime_artifact_delta_plan_ready",
                    ),
                    "generated_path_candidates": (
                        {
                            "path": "python/aware_home_devices_api/client.py",
                            "target": "api_client",
                        },
                    ),
                },
            ),
            "readable_materialization_event_chain": {
                "chain_kind": "api_provider_delta_materialization_event_chain",
                "status": "api_provider_delta_materialization_event_chain_ready",
                "event_count": 1,
                "lines": ("1. Update generated api-client artifacts for toggle_door.",),
            },
        }
    )

    assert report.ready is True
    assert report.provider_key == "aware_api"
    assert report.current_delta_fingerprint == "sha256:api-current"
    assert report.head_refs["semantic_branch_id"] == "semantic-branch-id"
    assert report.baseline_refs["semantic_object_instance_graph_commit_id"] == (
        "baseline-oig"
    )
    assert report.events[0].provider_event_kind == (
        "api_provider_delta_materialization_event"
    )
    assert report.events[0].operation == "update"
    assert report.events[0].provider_payload["generated_path_candidates"] == (
        {
            "path": "python/aware_home_devices_api/client.py",
            "target": "api_client",
        },
    )


def test_semantic_provider_delta_event_report_preserves_blockers() -> None:
    report = SemanticProviderDeltaEventReport.from_payload(
        {
            "status": "semantic_dirty_event_report_blocked",
            "reason": "meta_ocg_provider_delta_semantic_dirty_event_report_blocked",
            "provider_key": "aware_meta",
            "blocked": True,
            "blockers": ("semantic_dirty_diff_not_ready:semantic_dirty_diff_blocked",),
        }
    )

    assert report.ready is False
    assert report.blocked is True
    assert report.blockers == (
        "semantic_dirty_diff_not_ready:semantic_dirty_diff_blocked",
    )
    assert report.events == ()


def test_semantic_provider_delta_events_from_payloads_skips_invalid_entries() -> None:
    events = semantic_provider_delta_events_from_payloads(
        (
            {"semantic_key": "api:demo", "summary": "Update demo.", "verb": "update"},
            {"summary": "No key still counts."},
            "invalid",
            {},
        ),
        provider_key="aware_api",
    )

    assert len(events) == 2
    assert events[0].semantic_key == "api:demo"
    assert events[0].operation == "update"
    assert events[1].summary == "No key still counts."
