from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, model_validator


OBSERVATION_PRODUCTION_WORKLOAD_SCHEMA = (
    "aware.file_system.observation_production_workload.v1"
)
PRODUCTION_FIXTURE_MIN_FILES = 33_000
# Nearest-rank p99 becomes distinct from max only at 100 or more samples.
PRODUCTION_SCENARIO_MIN_SAMPLES = 100


class ObservationWorkloadContractError(ValueError):
    pass


class DurationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int = Field(ge=1)
    p50: float = Field(ge=0)
    p95: float = Field(ge=0)
    p99: float = Field(ge=0)
    max: float = Field(ge=0)

    @model_validator(mode="after")
    def _ordered(self) -> DurationSummary:
        if not self.p50 <= self.p95 <= self.p99 <= self.max:
            raise ValueError("duration quantiles must be monotonically ordered")
        return self


class ObservationWorkloadSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index: int = Field(ge=0)
    wall_s: float = Field(ge=0)
    request_wall_s: float = Field(ge=0)
    engine_s: float = Field(ge=0)
    scan_s: float = Field(ge=0)
    merge_s: float = Field(ge=0)
    cpu_s_delta: float | None = Field(default=None, ge=0)
    rss_bytes: int | None = Field(default=None, ge=0)
    io_read_bytes_delta: int | None = Field(default=None, ge=0)
    io_write_bytes_delta: int | None = Field(default=None, ge=0)
    from_generation: int = Field(ge=0)
    to_generation: int = Field(ge=0)
    snapshot_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: str = Field(min_length=1)
    observation_mode: str = Field(min_length=1)
    reconciliation_cause: str = Field(min_length=1)
    delta_count: int = Field(ge=0)
    exact: bool


class ObservationWorkloadBudget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_samples: int = Field(ge=1)
    p99_wall_s: float = Field(gt=0)
    max_wall_s: float = Field(gt=0)
    p99_request_wall_s: float = Field(gt=0)
    max_request_wall_s: float = Field(gt=0)

    @model_validator(mode="after")
    def _ordered(self) -> ObservationWorkloadBudget:
        if self.p99_wall_s > self.max_wall_s:
            raise ValueError("p99 wall budget cannot exceed max wall budget")
        if self.p99_request_wall_s > self.max_request_wall_s:
            raise ValueError(
                "p99 request wall budget cannot exceed max request wall budget"
            )
        return self


class ObservationWorkloadScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    workload_class: Literal[
        "cold",
        "restart",
        "idle",
        "mutation",
        "burst",
        "audit",
        "pressure",
        "concurrency",
    ]
    budget: ObservationWorkloadBudget
    samples: list[ObservationWorkloadSample]
    failures: list[str]
    wall_s: DurationSummary
    request_wall_s: DurationSummary

    @model_validator(mode="after")
    def _evidence_is_self_consistent(self) -> ObservationWorkloadScenario:
        indexes = [sample.index for sample in self.samples]
        if indexes != list(range(len(self.samples))):
            raise ValueError("scenario sample indexes must be contiguous")
        if self.wall_s.count != len(self.samples):
            raise ValueError("wall summary count must equal sample count")
        if self.request_wall_s.count != len(self.samples):
            raise ValueError("request wall summary count must equal sample count")
        expected_wall = duration_summary([sample.wall_s for sample in self.samples])
        expected_request = duration_summary(
            [sample.request_wall_s for sample in self.samples]
        )
        if self.wall_s.model_dump() != expected_wall:
            raise ValueError("wall summary does not match samples")
        if self.request_wall_s.model_dump() != expected_request:
            raise ValueError("request wall summary does not match samples")
        return self


class ObservationPlatformIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system: str = Field(min_length=1)
    release: str = Field(min_length=1)
    machine: str = Field(min_length=1)
    python: str = Field(min_length=1)


class ObservationBinaryIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    bytes: int = Field(gt=0)


class ObservationFixtureIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    root: str = Field(min_length=1)
    file_count: int = Field(ge=1)
    canonical_filter_profile: str = Field(min_length=1)
    initial_inventory_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    burst_size: int = Field(ge=1)
    periodic_interval_ms: int = Field(ge=1)


class ObservationResourceEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    process_cpu_s: float = Field(ge=0)
    rss_peak_bytes: int = Field(gt=0)
    io_read_bytes: int = Field(ge=0)
    io_write_bytes: int = Field(ge=0)


class ObservationFinalIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    python_parity: bool
    digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    generation: int = Field(ge=0)
    orphan_process_ids: list[int]
    leaked_reader_threads: list[str]


class ObservationWorkloadReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    contract_version: Literal[
        "aware.file_system.observation_production_workload.v1"
    ] = Field(alias="schema")
    created_at: datetime
    platform: ObservationPlatformIdentity
    binary: ObservationBinaryIdentity
    protocol: Literal["aware.file_system.maintained_observation_service.v2"]
    fixture: ObservationFixtureIdentity
    scenarios: list[ObservationWorkloadScenario]
    recovery_checks: dict[str, bool]
    resources: ObservationResourceEvidence
    final: ObservationFinalIdentity
    locks: list[str]

    @model_validator(mode="after")
    def _top_level_shape(self) -> ObservationWorkloadReceipt:
        names = [scenario.name for scenario in self.scenarios]
        if len(names) != len(set(names)):
            raise ValueError("scenario names must be unique")
        if not self.locks:
            raise ValueError("runtime locks must not be empty")
        return self


REQUIRED_SCENARIOS: dict[
    str, tuple[str, ObservationWorkloadBudget]
] = {
    "cold_initialize": (
        "cold",
        ObservationWorkloadBudget(
            min_samples=PRODUCTION_SCENARIO_MIN_SAMPLES,
            p99_wall_s=1.0,
            max_wall_s=2.0,
            p99_request_wall_s=1.0,
            max_request_wall_s=2.0,
        ),
    ),
    "warm_restart": (
        "restart",
        ObservationWorkloadBudget(
            min_samples=PRODUCTION_SCENARIO_MIN_SAMPLES,
            p99_wall_s=0.75,
            max_wall_s=1.5,
            p99_request_wall_s=0.75,
            max_request_wall_s=1.5,
        ),
    ),
    "idle_poll": (
        "idle",
        ObservationWorkloadBudget(
            min_samples=PRODUCTION_SCENARIO_MIN_SAMPLES,
            p99_wall_s=0.025,
            max_wall_s=0.100,
            p99_request_wall_s=0.025,
            max_request_wall_s=0.100,
        ),
    ),
    "create": (
        "mutation",
        ObservationWorkloadBudget(
            min_samples=PRODUCTION_SCENARIO_MIN_SAMPLES,
            p99_wall_s=0.500,
            max_wall_s=1.0,
            p99_request_wall_s=0.500,
            max_request_wall_s=1.0,
        ),
    ),
    "update": (
        "mutation",
        ObservationWorkloadBudget(
            min_samples=PRODUCTION_SCENARIO_MIN_SAMPLES,
            p99_wall_s=0.500,
            max_wall_s=1.0,
            p99_request_wall_s=0.500,
            max_request_wall_s=1.0,
        ),
    ),
    "rename": (
        "mutation",
        ObservationWorkloadBudget(
            min_samples=PRODUCTION_SCENARIO_MIN_SAMPLES,
            p99_wall_s=0.500,
            max_wall_s=1.0,
            p99_request_wall_s=0.500,
            max_request_wall_s=1.0,
        ),
    ),
    "delete": (
        "mutation",
        ObservationWorkloadBudget(
            min_samples=PRODUCTION_SCENARIO_MIN_SAMPLES,
            p99_wall_s=0.500,
            max_wall_s=1.0,
            p99_request_wall_s=0.500,
            max_request_wall_s=1.0,
        ),
    ),
    "atomic_replace": (
        "mutation",
        ObservationWorkloadBudget(
            min_samples=PRODUCTION_SCENARIO_MIN_SAMPLES,
            p99_wall_s=0.500,
            max_wall_s=1.0,
            p99_request_wall_s=0.500,
            max_request_wall_s=1.0,
        ),
    ),
    "ignore_policy_change": (
        "mutation",
        ObservationWorkloadBudget(
            min_samples=PRODUCTION_SCENARIO_MIN_SAMPLES,
            p99_wall_s=1.0,
            max_wall_s=2.0,
            p99_request_wall_s=1.0,
            max_request_wall_s=2.0,
        ),
    ),
    "bounded_burst": (
        "burst",
        ObservationWorkloadBudget(
            min_samples=PRODUCTION_SCENARIO_MIN_SAMPLES,
            p99_wall_s=1.0,
            max_wall_s=2.0,
            p99_request_wall_s=1.0,
            max_request_wall_s=2.0,
        ),
    ),
    "periodic_audit_poll": (
        "audit",
        ObservationWorkloadBudget(
            min_samples=PRODUCTION_SCENARIO_MIN_SAMPLES,
            p99_wall_s=1.0,
            max_wall_s=1.5,
            p99_request_wall_s=0.100,
            max_request_wall_s=0.250,
        ),
    ),
    "pressure_full_reconcile": (
        "pressure",
        ObservationWorkloadBudget(
            min_samples=PRODUCTION_SCENARIO_MIN_SAMPLES,
            p99_wall_s=2.0,
            max_wall_s=4.0,
            p99_request_wall_s=2.0,
            max_request_wall_s=4.0,
        ),
    ),
    "io_pressure_full_reconcile": (
        "pressure",
        ObservationWorkloadBudget(
            min_samples=PRODUCTION_SCENARIO_MIN_SAMPLES,
            p99_wall_s=3.0,
            max_wall_s=5.0,
            p99_request_wall_s=3.0,
            max_request_wall_s=5.0,
        ),
    ),
    "concurrent_distinct_roots": (
        "concurrency",
        ObservationWorkloadBudget(
            min_samples=PRODUCTION_SCENARIO_MIN_SAMPLES,
            p99_wall_s=1.0,
            max_wall_s=2.0,
            p99_request_wall_s=1.0,
            max_request_wall_s=2.0,
        ),
    ),
}

REQUIRED_RECOVERY_CHECKS = {
    "forced_restart_exact",
    "truncated_cache_rebuilt",
    "torn_journal_tail_recovered",
    "reconciliation_only_exact",
    "no_orphan_process",
    "no_reader_thread_leak",
}


def validate_observation_workload_receipt(
    receipt: Mapping[str, Any],
) -> ObservationWorkloadReceipt:
    try:
        return ObservationWorkloadReceipt.model_validate(dict(receipt))
    except Exception as error:
        raise ObservationWorkloadContractError(str(error)) from error


def evaluate_observation_workload_receipt(
    receipt: Mapping[str, Any],
) -> dict[str, Any]:
    parsed = validate_observation_workload_receipt(receipt)
    failures: list[str] = []
    scenarios = {scenario.name: scenario for scenario in parsed.scenarios}
    missing = sorted(set(REQUIRED_SCENARIOS).difference(scenarios))
    extra = sorted(set(scenarios).difference(REQUIRED_SCENARIOS))
    if missing:
        failures.append("missing scenarios: " + ", ".join(missing))
    if extra:
        failures.append("unexpected scenarios: " + ", ".join(extra))

    scenario_results: dict[str, dict[str, Any]] = {}
    for name, (expected_class, expected_budget) in REQUIRED_SCENARIOS.items():
        scenario = scenarios.get(name)
        if scenario is None:
            continue
        reasons: list[str] = []
        if scenario.workload_class != expected_class:
            reasons.append("workload class mismatch")
        if scenario.budget != expected_budget:
            reasons.append("budget mismatch")
        if len(scenario.samples) < expected_budget.min_samples:
            reasons.append("insufficient successful samples")
        if scenario.failures:
            reasons.append("scenario failures are non-empty")
        if not all(sample.exact for sample in scenario.samples):
            reasons.append("one or more samples are not exact")
        if scenario.wall_s.p99 > expected_budget.p99_wall_s:
            reasons.append("p99 wall budget exceeded")
        if scenario.wall_s.max > expected_budget.max_wall_s:
            reasons.append("max wall budget exceeded")
        if scenario.request_wall_s.p99 > expected_budget.p99_request_wall_s:
            reasons.append("p99 request wall budget exceeded")
        if scenario.request_wall_s.max > expected_budget.max_request_wall_s:
            reasons.append("max request wall budget exceeded")
        passed = not reasons
        scenario_results[name] = {
            "passed": passed,
            "reasons": reasons,
            "sample_count": len(scenario.samples),
            "p99_wall_s": scenario.wall_s.p99,
            "max_wall_s": scenario.wall_s.max,
            "p99_request_wall_s": scenario.request_wall_s.p99,
            "max_request_wall_s": scenario.request_wall_s.max,
        }
        failures.extend(f"{name}: {reason}" for reason in reasons)

    file_count = parsed.fixture.file_count
    if file_count < PRODUCTION_FIXTURE_MIN_FILES:
        failures.append(
            f"fixture has {file_count} files; need {PRODUCTION_FIXTURE_MIN_FILES}"
        )
    missing_recovery = sorted(
        REQUIRED_RECOVERY_CHECKS.difference(parsed.recovery_checks)
    )
    if missing_recovery:
        failures.append("missing recovery checks: " + ", ".join(missing_recovery))
    failed_recovery = sorted(
        name
        for name in REQUIRED_RECOVERY_CHECKS
        if parsed.recovery_checks.get(name) is not True
    )
    if failed_recovery:
        failures.append("failed recovery checks: " + ", ".join(failed_recovery))
    if parsed.final.python_parity is not True:
        failures.append("final Python parity is not proven")
    if parsed.final.orphan_process_ids != []:
        failures.append("orphan native processes remain")
    if parsed.final.leaked_reader_threads != []:
        failures.append("native response reader threads leaked")

    return {
        "schema": OBSERVATION_PRODUCTION_WORKLOAD_SCHEMA,
        "admitted": not failures,
        "failures": failures,
        "scenario_results": scenario_results,
        "required_scenarios": sorted(REQUIRED_SCENARIOS),
        "required_recovery_checks": sorted(REQUIRED_RECOVERY_CHECKS),
    }


def duration_summary(values: list[float]) -> dict[str, float | int]:
    if not values:
        raise ValueError("duration summary requires at least one value")
    ordered = sorted(values)
    return {
        "count": len(ordered),
        "p50": _nearest_rank(ordered, 0.50),
        "p95": _nearest_rank(ordered, 0.95),
        "p99": _nearest_rank(ordered, 0.99),
        "max": ordered[-1],
    }


def _nearest_rank(values: list[float], quantile: float) -> float:
    return values[max(0, math.ceil(quantile * len(values)) - 1)]
