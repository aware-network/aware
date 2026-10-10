from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aware_file_system.benchmark_receipt_contract import (
    BenchmarkEnvironment,
    BenchmarkReceiptContractError,
    BenchmarkSample,
    BenchmarkStats,
    WORKSPACE_FS_BENCHMARK_VERSION,
)


WORKSPACE_FS_WORKLOAD_VERSION = "aware.file_system.workspace_fs_workload.v1"
PRODUCTION_TAIL_MIN_SAMPLES = 30
WORKLOAD_SUMMARY_KEYS = (
    "duration_s",
    "scanner_scan_time_s",
    "process_cpu_duration_s",
    "peak_rss_bytes",
    "current_rss_bytes",
    "io_read_bytes_delta",
    "io_write_bytes_delta",
    "voluntary_context_switches_delta",
    "involuntary_context_switches_delta",
)


class WorkloadScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1)
    workload_class: Literal[
        "cold",
        "warm_session",
        "warm_restart",
        "contention",
        "cpu_pressure",
        "diagnostic_comparison",
        "mutation",
        "recovery",
    ]
    source_mutation: bool
    cache_state: Literal["empty", "warm", "corrupt", "varied"]
    concurrency: int = Field(default=1, ge=1)
    setup: dict[str, Any]
    sample_count: int = Field(ge=1)
    success_count: int = Field(ge=0)
    failure_count: int = Field(ge=0)
    failures: list[str]
    inventory_digests: list[str]
    exact_inventory_stable: bool
    tail_claim_min_samples: int = Field(default=PRODUCTION_TAIL_MIN_SAMPLES, ge=2)
    tail_claim_eligible: bool = False
    summary: dict[str, BenchmarkStats]
    samples: list[BenchmarkSample]

    @model_validator(mode="after")
    def _validate_scenario(self) -> WorkloadScenario:
        if self.success_count + self.failure_count != self.sample_count:
            raise ValueError("success_count + failure_count must equal sample_count")
        if len(self.samples) != self.success_count:
            raise ValueError("samples length must equal success_count")
        if len(self.failures) != self.failure_count:
            raise ValueError("failures length must equal failure_count")
        if [sample.iteration_index for sample in self.samples] != list(
            range(self.success_count)
        ):
            raise ValueError("successful samples require contiguous iteration indexes")
        if {sample.label for sample in self.samples} not in (set(), {self.label}):
            raise ValueError("successful samples must use the scenario label")
        missing_summary = [
            key for key in WORKLOAD_SUMMARY_KEYS if key not in self.summary
        ]
        if missing_summary:
            raise ValueError(
                "scenario summary is missing required metrics: "
                + ", ".join(missing_summary)
            )
        actual_digests = sorted({sample.inventory_digest for sample in self.samples})
        if self.inventory_digests != actual_digests:
            raise ValueError(
                "inventory_digests must equal sorted successful sample digests"
            )
        expected_stability = bool(actual_digests) and len(actual_digests) == 1
        if self.exact_inventory_stable != expected_stability:
            raise ValueError("exact_inventory_stable disagrees with inventory digests")
        expected_tail_eligibility = (
            self.success_count >= self.tail_claim_min_samples
            and self.failure_count == 0
            and self.exact_inventory_stable
        )
        if self.tail_claim_eligible != expected_tail_eligibility:
            raise ValueError("tail_claim_eligible disagrees with scenario evidence")
        return self


class WorkspaceFsWorkloadReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workload_version: Literal["aware.file_system.workspace_fs_workload.v1"]
    baseline_contract_version: Literal[
        "aware.file_system.workspace_fs_benchmark.v1"
    ] = WORKSPACE_FS_BENCHMARK_VERSION
    backend_kind: Literal["python", "rust"]
    mode: Literal["real_workspace_readonly", "synthetic_mutating"]
    workspace_root: str = Field(min_length=1)
    cache_dir: str = Field(min_length=1)
    created_at: datetime
    environment: BenchmarkEnvironment
    canonical_filter_profile: str = Field(min_length=1)
    scenario_count: int = Field(ge=1)
    scenarios: list[WorkloadScenario]
    production_invariants: list[str]
    source_mutation: bool
    receipt_path: str | None = None

    @model_validator(mode="after")
    def _validate_receipt(self) -> WorkspaceFsWorkloadReceipt:
        if len(self.scenarios) != self.scenario_count:
            raise ValueError("scenarios length must equal scenario_count")
        labels = [scenario.label for scenario in self.scenarios]
        if len(labels) != len(set(labels)):
            raise ValueError("scenario labels must be unique")
        if self.mode == "real_workspace_readonly" and self.source_mutation:
            raise ValueError("real_workspace_readonly cannot mutate source")
        if self.mode == "real_workspace_readonly" and any(
            scenario.source_mutation for scenario in self.scenarios
        ):
            raise ValueError("real workspace scenarios cannot mutate source")
        if not self.production_invariants:
            raise ValueError("production_invariants must not be empty")
        return self


def validate_workspace_fs_workload_receipt(
    receipt: Mapping[str, Any],
) -> WorkspaceFsWorkloadReceipt:
    try:
        return WorkspaceFsWorkloadReceipt.model_validate(dict(receipt))
    except Exception as exc:
        raise BenchmarkReceiptContractError(str(exc)) from exc


def workspace_fs_workload_receipt_json_schema() -> dict[str, Any]:
    return WorkspaceFsWorkloadReceipt.model_json_schema()
