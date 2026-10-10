from __future__ import annotations

import gc
import statistics
import time

import pytest
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticContractRef,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
)
from aware_workspace_runtime.revision_preparation import (
    _merge_prepared_pin_overlay,
    _merge_workspace_revision_source_overlay,
)
from aware_workspace_runtime.revision_preparation_admission import (
    WorkspaceRevisionPreparationAdmissionError,
)
from aware_workspace_runtime.revision_preparation_codec import (
    _measure_revision_preparation_decoding,
    _measure_revision_preparation_encoding,
)
from aware_workspace_runtime.revision_preparation_contracts import (
    WorkspaceRevisionCandidate,
    WorkspaceRevisionCandidatePredecessor,
    WorkspaceRevisionPinSlot,
    WorkspaceRevisionPreparedPackagePin,
    WorkspaceRevisionSourceClosure,
    WorkspaceRevisionSourcePackageEntry,
    WorkspaceRevisionState,
)


def _digest(label: str) -> str:
    return ContentDigest.of_bytes(label.encode()).value


def _pin(index: int, *, generation: int = 1) -> WorkspaceRevisionPreparedPackagePin:
    lineage = f"workspace-package-lineage:00000000-0000-4000-8000-{index:012d}"
    contract = SemanticContractRef(
        key="aware.test.result",
        version="1",
        schema_digest=ContentDigest(_digest("contract")),
    )
    slot = WorkspaceRevisionPinSlot.create(
        package_lineage_ref=lineage,
        result_role="result",
        semantic_contract=contract,
    )
    return WorkspaceRevisionPreparedPackagePin.create(
        slot=slot,
        semantic_package=SemanticPackageCoordinate(
            package_ref=f"package:test-{index:04d}@1.0.0",
            package_kind="ontology",
            manifest_digest=ContentDigest(_digest(f"manifest:{index}")),
        ),
        source_package_identity_digest=_digest(f"source:{index}"),
        source_after_state_authority_digest=_digest(f"after:{index}"),
        code_intent_digest=_digest(f"intent:{index}"),
        code_match_digest=_digest(f"match:{index}"),
        execution_input_closure_digest=_digest(f"closure:{index}"),
        result_coordinate=SemanticValueCoordinate(
            role="result",
            contract=contract,
            value_ref=f"value:{index}",
            digest=ContentDigest(_digest(f"value:{index}:{generation}")),
            size_bytes=32,
        ),
        package_head_revision=generation,
        package_head_digest=_digest(f"head:{index}:{generation}"),
        package_head_body_sha256=_digest(f"head-body:{index}:{generation}"),
    )


def _candidate(count: int) -> WorkspaceRevisionCandidate:
    pins = tuple(_pin(index) for index in range(1, count + 1))
    state = WorkspaceRevisionState.create(
        workspace_ref="workspace:performance",
        source_closure_digest=_digest(f"source-closure:{count}"),
        ordered_package_pins=pins,
    )
    return WorkspaceRevisionCandidate.create(
        state=state,
        predecessor=WorkspaceRevisionCandidatePredecessor.genesis(
            _digest("revision-nonmembership")
        ),
    )


def _source_closure(count: int) -> WorkspaceRevisionSourceClosure:
    entries = tuple(_source_entry(index) for index in range(1, count + 1))
    return WorkspaceRevisionSourceClosure.create(
        workspace_ref="workspace:performance", ordered_packages=entries
    )


def _source_entry(
    index: int, *, generation: int = 1
) -> WorkspaceRevisionSourcePackageEntry:
    return WorkspaceRevisionSourcePackageEntry.create(
        package_lineage_ref=(
            f"workspace-package-lineage:00000000-0000-4000-8000-{index:012d}"
        ),
        source_package_identity_digest=_digest(f"source:{index}"),
        current_package_ref=f"package:test-{index:04d}@1.0.0",
        source_after_state_authority_digest=_digest(f"after:{index}:{generation}"),
        source_after_state_body_sha256=_digest(f"after-body:{index}:{generation}"),
    )


def test_candidate_and_source_codecs_have_exact_linear_work_counters() -> None:
    reports: dict[int, dict[str, int]] = {}
    for count in (1, 100, 500):
        candidate = _candidate(count)
        source_closure = _source_closure(count)
        for _ in range(5):
            warm_body = candidate.canonical_bytes()
            WorkspaceRevisionCandidate.from_canonical_bytes(warm_body)
            warm_source_body = source_closure.canonical_bytes()
            WorkspaceRevisionSourceClosure.from_canonical_bytes(warm_source_body)
        encode_samples: list[int] = []
        decode_samples: list[int] = []
        bytes_encoded = 0
        bytes_decoded = 0
        source_bytes_encoded = 0
        source_bytes_decoded = 0
        gc.collect()
        gc_was_enabled = gc.isenabled()
        gc.disable()
        try:
            for _ in range(15):
                started = time.perf_counter_ns()
                body, bytes_encoded = _measure_revision_preparation_encoding(
                    candidate.canonical_bytes
                )
                encode_samples.append(time.perf_counter_ns() - started)
                started = time.perf_counter_ns()
                decoded, bytes_decoded = _measure_revision_preparation_decoding(
                    body, WorkspaceRevisionCandidate.from_canonical_bytes
                )
                decode_samples.append(time.perf_counter_ns() - started)
                assert decoded.canonical_bytes() == body
        finally:
            if gc_was_enabled:
                gc.enable()
        source_body, source_bytes_encoded = _measure_revision_preparation_encoding(
            source_closure.canonical_bytes
        )
        decoded_source, source_bytes_decoded = (
            _measure_revision_preparation_decoding(
                source_body, WorkspaceRevisionSourceClosure.from_canonical_bytes
            )
        )
        assert decoded_source.canonical_bytes() == source_body
        _unchanged_pins, members_visited = _merge_prepared_pin_overlay(
            predecessor_pins=candidate.state.ordered_package_pins,
            replacements=(),
            selected_lineages=frozenset(),
            removed_lineages=frozenset(),
        )
        _unchanged_sources, source_members_visited = (
            _merge_workspace_revision_source_overlay(
                predecessor_entries=source_closure.ordered_packages,
                replacements=(),
                removed_lineages=frozenset(),
            )
        )
        reports[count] = {
            "pin_count": count,
            "warmup_count": 5,
            "sample_count": 15,
            "encode_median_ns": int(statistics.median(encode_samples)),
            "encode_p95_ns": int(
                statistics.quantiles(encode_samples, n=20, method="inclusive")[18]
            ),
            "decode_median_ns": int(statistics.median(decode_samples)),
            "decode_p95_ns": int(
                statistics.quantiles(decode_samples, n=20, method="inclusive")[18]
            ),
            "members_visited": members_visited,
            "bytes_encoded": bytes_encoded,
            "bytes_decoded": bytes_decoded,
            "source_members_visited": source_members_visited,
            "source_bytes_encoded": source_bytes_encoded,
            "source_bytes_decoded": source_bytes_decoded,
            "provider_execution_count": 0,
            "external_read_count": 0,
            "external_write_count": 0,
            "ontology_call_count": 0,
            "meta_oig_call_count": 0,
        }
    for count, report in reports.items():
        assert report["members_visited"] == count
        assert report["bytes_encoded"] == report["bytes_decoded"]
        assert report["source_members_visited"] == count
        assert report["source_bytes_encoded"] == report["source_bytes_decoded"]
        assert report["warmup_count"] == 5
        assert report["sample_count"] == 15
        assert (
            report["provider_execution_count"],
            report["external_read_count"],
            report["external_write_count"],
            report["ontology_call_count"],
            report["meta_oig_call_count"],
        ) == (0, 0, 0, 0, 0)
    baseline = reports[1]
    for metric in ("encode_p95_ns", "decode_p95_ns"):
        per_member_100 = max(reports[100][metric] - baseline[metric], 1) / 100
        per_member_500 = max(reports[500][metric] - baseline[metric], 1) / 500
        assert per_member_500 <= per_member_100 * 1.25


def _overlay_report(count: int) -> dict[str, int]:
    predecessor = tuple(_pin(index) for index in range(1, count + 1))
    replacement_count = max(count // 5, 1)
    replacements = tuple(
        [_pin(index, generation=2) for index in range(1, replacement_count + 1)]
        + [
            _pin(index)
            for index in range(count + 1, count + replacement_count + 1)
        ]
    )
    replacements = tuple(
        sorted(replacements, key=lambda item: item.slot.ordering_key())
    )
    selected = frozenset(item.slot.package_lineage_ref for item in replacements)
    removed = frozenset(
        _pin(index).slot.package_lineage_ref
        for index in range(replacement_count + 1, (2 * replacement_count) + 1)
    )
    pin_samples: list[int] = []
    source_samples: list[int] = []
    for _ in range(5):
        _merge_prepared_pin_overlay(
            predecessor_pins=predecessor,
            replacements=replacements,
            selected_lineages=selected,
            removed_lineages=removed,
        )
    gc.collect()
    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        for _ in range(15):
            started = time.perf_counter_ns()
            final, visited = _merge_prepared_pin_overlay(
                predecessor_pins=predecessor,
                replacements=replacements,
                selected_lineages=selected,
                removed_lineages=removed,
            )
            pin_samples.append(time.perf_counter_ns() - started)
    finally:
        if gc_was_enabled:
            gc.enable()
    final, visited = _merge_prepared_pin_overlay(
        predecessor_pins=predecessor,
        replacements=replacements,
        selected_lineages=selected,
        removed_lineages=removed,
    )
    assert visited == len(predecessor) + len(replacements)
    assert len({item.slot.slot_digest for item in final}) == len(final)
    assert tuple(item.slot.ordering_key() for item in final) == tuple(
        sorted(item.slot.ordering_key() for item in final)
    )

    predecessor_source = tuple(_source_entry(index) for index in range(1, count + 1))
    source_replacements = tuple(
        [
            _source_entry(index, generation=2)
            for index in range(1, replacement_count + 1)
        ]
        + [
            _source_entry(index)
            for index in range(count + 1, count + replacement_count + 1)
        ]
    )
    for _ in range(5):
        _merge_workspace_revision_source_overlay(
            predecessor_entries=predecessor_source,
            replacements=source_replacements,
            removed_lineages=removed,
        )
    gc.collect()
    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        for _ in range(15):
            started = time.perf_counter_ns()
            source_final, source_visited = (
                _merge_workspace_revision_source_overlay(
                    predecessor_entries=predecessor_source,
                    replacements=source_replacements,
                    removed_lineages=removed,
                )
            )
            source_samples.append(time.perf_counter_ns() - started)
    finally:
        if gc_was_enabled:
            gc.enable()
    source_final, source_visited = _merge_workspace_revision_source_overlay(
        predecessor_entries=predecessor_source,
        replacements=source_replacements,
        removed_lineages=removed,
    )
    assert source_visited == len(predecessor_source) + len(source_replacements)
    assert tuple(item.package_lineage_ref for item in source_final) == tuple(
        sorted(item.package_lineage_ref for item in source_final)
    )
    return {
        "pin_members_visited": visited,
        "source_members_visited": source_visited,
        "pin_p95_ns": int(
            statistics.quantiles(pin_samples, n=20, method="inclusive")[18]
        ),
        "source_p95_ns": int(
            statistics.quantiles(source_samples, n=20, method="inclusive")[18]
        ),
    }


def test_source_and_pin_overlays_have_measured_linear_high_fan_in_work() -> None:
    reports = {count: _overlay_report(count) for count in (1, 100, 500, 2000)}
    for count, report in reports.items():
        replacement_count = max(count // 5, 1)
        expected_visits = count + (2 * replacement_count)
        assert report["pin_members_visited"] == expected_visits
        assert report["source_members_visited"] == expected_visits
    for metric in ("pin_p95_ns", "source_p95_ns"):
        fixed_baseline = reports[1][metric]
        normalized_100 = max(reports[100][metric] - fixed_baseline, 1) / reports[
            100
        ]["pin_members_visited"]
        normalized_500_after_baseline = max(
            reports[500][metric] - fixed_baseline, 1
        ) / reports[500]["pin_members_visited"]
        assert normalized_500_after_baseline <= normalized_100 * 1.25
        normalized_500 = reports[500][metric] / reports[500]["pin_members_visited"]
        normalized_2000 = (
            reports[2000][metric] / reports[2000]["pin_members_visited"]
        )
        assert normalized_2000 <= normalized_500 * 2.0


def test_overlay_order_validation_rejects_reversal_without_sorting_input() -> None:
    pins = (_pin(1), _pin(2))
    sources = (_source_entry(1), _source_entry(2))
    with pytest.raises(
        WorkspaceRevisionPreparationAdmissionError,
        match="predecessor prepared pins must be uniquely ordered",
    ):
        _merge_prepared_pin_overlay(
            predecessor_pins=tuple(reversed(pins)),
            replacements=(),
            selected_lineages=frozenset(),
            removed_lineages=frozenset(),
        )
    with pytest.raises(
        WorkspaceRevisionPreparationAdmissionError,
        match="predecessor source entries must be uniquely ordered",
    ):
        _merge_workspace_revision_source_overlay(
            predecessor_entries=tuple(reversed(sources)),
            replacements=(),
            removed_lineages=frozenset(),
        )
