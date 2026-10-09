from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any, Callable

import pytest

from aware_file_system.observation_workload_receipt_contract import (
    OBSERVATION_PRODUCTION_WORKLOAD_SCHEMA,
    REQUIRED_RECOVERY_CHECKS,
    REQUIRED_SCENARIOS,
    ObservationWorkloadContractError,
    duration_summary,
    evaluate_observation_workload_receipt,
    validate_observation_workload_receipt,
)


def _sample(index: int, *, wall_s: float = 0.001) -> dict[str, object]:
    return {
        "index": index,
        "wall_s": wall_s,
        "request_wall_s": wall_s / 2,
        "engine_s": wall_s / 3,
        "scan_s": 0.0,
        "merge_s": 0.0,
        "cpu_s_delta": 0.0,
        "rss_bytes": 1024,
        "io_read_bytes_delta": 0,
        "io_write_bytes_delta": 0,
        "from_generation": index,
        "to_generation": index,
        "snapshot_digest": "a" * 64,
        "status": "exact",
        "observation_mode": "idle",
        "reconciliation_cause": "none",
        "delta_count": 0,
        "exact": True,
    }


def _valid_receipt() -> dict[str, object]:
    scenarios: list[dict[str, object]] = []
    for name, (workload_class, budget) in REQUIRED_SCENARIOS.items():
        samples = [_sample(index) for index in range(budget.min_samples)]
        scenarios.append(
            {
                "name": name,
                "workload_class": workload_class,
                "budget": budget.model_dump(),
                "samples": samples,
                "failures": [],
                "wall_s": duration_summary(
                    [float(sample["wall_s"]) for sample in samples]
                ),
                "request_wall_s": duration_summary(
                    [float(sample["request_wall_s"]) for sample in samples]
                ),
            }
        )
    return {
        "schema": OBSERVATION_PRODUCTION_WORKLOAD_SCHEMA,
        "created_at": datetime.now(UTC).isoformat(),
        "platform": {
            "system": "Linux",
            "release": "test",
            "machine": "x86_64",
            "python": "3.12",
        },
        "binary": {"path": "/tmp/native", "sha256": "b" * 64, "bytes": 1},
        "protocol": "aware.file_system.maintained_observation_service.v2",
        "fixture": {
            "root": "/tmp/root",
            "file_count": 34_000,
            "canonical_filter_profile": "canonical_source_v1",
            "initial_inventory_digest": "a" * 64,
            "burst_size": 16,
            "periodic_interval_ms": 750,
        },
        "scenarios": scenarios,
        "recovery_checks": {name: True for name in REQUIRED_RECOVERY_CHECKS},
        "resources": {
            "process_cpu_s": 1.0,
            "rss_peak_bytes": 4096,
            "io_read_bytes": 0,
            "io_write_bytes": 0,
        },
        "final": {
            "python_parity": True,
            "digest": "a" * 64,
            "generation": 1,
            "orphan_process_ids": [],
            "leaked_reader_threads": [],
        },
        "locks": ["one observer", "no materialization"],
    }


def test_valid_complete_receipt_is_admitted() -> None:
    receipt = _valid_receipt()
    parsed = validate_observation_workload_receipt(receipt)
    decision = evaluate_observation_workload_receipt(receipt)

    assert parsed.contract_version == OBSERVATION_PRODUCTION_WORKLOAD_SCHEMA
    assert decision["admitted"] is True
    assert decision["failures"] == []


@pytest.mark.parametrize(
    ("mutation", "failure_fragment"),
    [
        (lambda value: value["scenarios"].pop(), "missing scenarios"),
        (
            lambda value: value["scenarios"][0]["samples"].pop(),
            "insufficient successful samples",
        ),
        (
            lambda value: value["scenarios"][0]["failures"].append("boom"),
            "scenario failures",
        ),
        (
            lambda value: value["scenarios"][0]["samples"][0].__setitem__(
                "exact", False
            ),
            "not exact",
        ),
        (
            lambda value: value["recovery_checks"].__setitem__(
                "forced_restart_exact", False
            ),
            "failed recovery checks",
        ),
        (
            lambda value: value["fixture"].__setitem__("file_count", 32_999),
            "fixture has",
        ),
    ],
)
def test_admission_fails_closed_on_incomplete_evidence(
    mutation: Callable[[dict[str, Any]], object],
    failure_fragment: str,
) -> None:
    receipt = deepcopy(_valid_receipt())
    mutation(receipt)
    for scenario in receipt["scenarios"]:  # type: ignore[index]
        samples = scenario["samples"]
        scenario["wall_s"] = duration_summary(
            [float(sample["wall_s"]) for sample in samples]
        )
        scenario["request_wall_s"] = duration_summary(
            [float(sample["request_wall_s"]) for sample in samples]
        )

    decision = evaluate_observation_workload_receipt(receipt)

    assert decision["admitted"] is False
    assert any(failure_fragment in item for item in decision["failures"])


def test_contract_rejects_forged_summary_and_duplicate_scenario() -> None:
    forged = deepcopy(_valid_receipt())
    forged["scenarios"][0]["wall_s"]["p99"] = 0.0  # type: ignore[index]
    with pytest.raises(
        ObservationWorkloadContractError,
        match="duration quantiles|wall summary",
    ):
        validate_observation_workload_receipt(forged)

    duplicate = deepcopy(_valid_receipt())
    duplicate["scenarios"].append(deepcopy(duplicate["scenarios"][0]))  # type: ignore[index]
    with pytest.raises(ObservationWorkloadContractError, match="unique"):
        validate_observation_workload_receipt(duplicate)


def test_contract_rejects_self_authorization_field() -> None:
    receipt = _valid_receipt()
    receipt["production_gate_passed"] = True

    with pytest.raises(ObservationWorkloadContractError, match="extra_forbidden"):
        validate_observation_workload_receipt(receipt)


def test_periodic_convergence_and_request_budgets_are_independent() -> None:
    receipt = _valid_receipt()
    periodic = next(
        scenario
        for scenario in receipt["scenarios"]
        if scenario["name"] == "periodic_audit_poll"
    )
    for sample in periodic["samples"]:
        sample["wall_s"] = 0.6
        sample["request_wall_s"] = 0.05
    periodic["wall_s"] = duration_summary([0.6] * len(periodic["samples"]))
    periodic["request_wall_s"] = duration_summary(
        [0.05] * len(periodic["samples"])
    )
    assert evaluate_observation_workload_receipt(receipt)["admitted"] is True

    for sample in periodic["samples"]:
        sample["request_wall_s"] = 0.2
    periodic["request_wall_s"] = duration_summary(
        [0.2] * len(periodic["samples"])
    )
    decision = evaluate_observation_workload_receipt(receipt)
    assert decision["admitted"] is False
    assert any(
        "periodic_audit_poll: p99 request wall budget exceeded" in failure
        for failure in decision["failures"]
    )


@pytest.mark.parametrize(
    "path",
    ["platform.release", "binary.sha256", "fixture.initial_inventory_digest"],
)
def test_contract_rejects_incomplete_or_malformed_identity(path: str) -> None:
    receipt = _valid_receipt()
    section, key = path.split(".")
    if key.endswith("digest") or key == "sha256":
        receipt[section][key] = "not-a-digest"
    else:
        del receipt[section][key]

    with pytest.raises(ObservationWorkloadContractError):
        validate_observation_workload_receipt(receipt)
