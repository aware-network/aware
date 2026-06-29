from __future__ import annotations

from aware_meta.materialization.deltas.contracts import (
    MetaProviderDeltaSemanticChangeReport as FacadeChangeReport,
    MetaProviderDeltaSemanticCommitEvidence as FacadeCommitEvidence,
)
from aware_meta.materialization.deltas.change_evidence_contracts import (
    MetaProviderDeltaReadableSemanticChangeChain,
    MetaProviderDeltaSemanticChangeReport,
    MetaProviderDeltaSemanticCommitEvidence,
    semantic_world_changes_from_payloads,
)


def test_change_evidence_contracts_are_reexported_by_contract_facade() -> None:
    assert FacadeChangeReport is MetaProviderDeltaSemanticChangeReport
    assert FacadeCommitEvidence is MetaProviderDeltaSemanticCommitEvidence


def test_change_evidence_contract_module_normalizes_report_payload() -> None:
    report = MetaProviderDeltaSemanticChangeReport.from_payload(
        {
            "status": "semantic_change_report_ready",
            "available": True,
            "blocked": False,
            "semantic_dirty_entry_count": 1,
            "typed_operation_count": 1,
            "semantic_world_change_count": 1,
            "semantic_world_changes": (
                {
                    "change_key": (
                        "aware_meta.provider_delta.world_change.attribute.update"
                    ),
                    "semantic_key": ("ocg:home/node:Device/attribute:display_name"),
                    "verb": "update",
                    "ontology_subject_kind": "attribute",
                    "source_refs": ("home/device.aware",),
                    "condition_keys": ("meta.provider_delta.ready",),
                },
            ),
            "readable_semantic_change_chain": {
                "status": "readable_semantic_change_chain_ready",
                "change_count": 1,
                "line_count": 1,
                "lines": ("1. Update display_name.",),
                "markdown": "1. Update display_name.",
            },
        }
    )

    assert report.ready is True
    assert report.semantic_world_change_count == 1
    assert report.semantic_world_changes[0].verb == "update"
    assert report.semantic_world_changes[0].source_refs == ("home/device.aware",)
    assert report.readable_semantic_change_chain.ready is True
    assert report.readable_markdown == "1. Update display_name."
    assert "events" not in report.evidence_payload()


def test_change_evidence_contract_module_normalizes_committed_payload() -> None:
    translation = MetaProviderDeltaSemanticCommitEvidence.from_payload(
        {
            "status": "semantic_commit_evidence_ready",
            "available": True,
            "blocked": False,
            "committed_semantic_change_count": 1,
            "committed_semantic_changes": (
                {
                    "change_key": "aware_meta.attribute.update.committed",
                    "semantic_key": ("ocg:home/node:Device/attribute:display_name"),
                    "verb": "update",
                    "ontology_subject_kind": "attribute",
                    "commit_ref": {"commit_id": "oig-commit-1"},
                },
            ),
        }
    )

    assert translation.ready is True
    assert translation.committed_semantic_change_count == 1
    assert translation.committed_semantic_changes[0].commit_ref["commit_id"] == (
        "oig-commit-1"
    )
    assert translation.changes_for_subject("attribute")
    assert translation.evidence_payload()["committed_semantic_changes"] == (
        translation.committed_semantic_changes[0].evidence_payload(),
    )


def test_change_evidence_contract_module_skips_invalid_world_change_payloads() -> None:
    changes = semantic_world_changes_from_payloads(
        (
            {"change_key": "aware_meta.attribute.update"},
            {"semantic_key": "ocg:home/node:Device"},
            {"summary": "missing required keys"},
        )
    )

    assert len(changes) == 2


def test_readable_chain_preserves_empty_payload() -> None:
    chain = MetaProviderDeltaReadableSemanticChangeChain.from_payload({})

    assert chain.ready is False
    assert chain.lines == ()
    assert chain.markdown == ""
