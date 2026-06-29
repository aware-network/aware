from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, model_validator


WORKSPACE_FS_BENCHMARK_VERSION = "aware.file_system.workspace_fs_benchmark.v1"
SUPPORTED_BACKEND_KINDS = ("python", "rust")
SYNTHETIC_FIXTURE_MODE = "synthetic_fixture"
REAL_WORKSPACE_READONLY_MODE = "real_workspace_readonly"
SYNTHETIC_RUN_LABELS = (
    "cold_force_refresh",
    "warm_noop_session_cache",
    "one_file_edit_metadata_hash",
)
REAL_WORKSPACE_RUN_LABELS = (
    "cold_force_refresh",
    "warm_noop_session_cache",
)
SUMMARY_METRIC_KEYS = (
    "duration_s",
    "scanner_scan_time_s",
    "hash_duration_s",
    "cache_hit_ratio",
)
RUN_SEMANTIC_FIELDS = (
    "total_changes",
    "current_file_count",
    "added_count",
    "modified_count",
    "deleted_count",
    "files_processed",
    "files_content_read",
    "hashed_path_count",
)


class BenchmarkReceiptContractError(ValueError):
    """Raised when a benchmark receipt does not satisfy the backend contract."""


class BenchmarkStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int = Field(ge=0)
    min: float | None
    median: float | None
    p95: float | None
    max: float | None


class BenchmarkDirectoryCacheStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_directories: int | None = Field(default=None, ge=0)
    total_files_tracked: int | None = Field(default=None, ge=0)
    changed_directories: int | None = Field(default=None, ge=0)


class BenchmarkPersistentCacheStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entry_count: int | None = Field(default=None, ge=0)
    file_size: int | None = Field(default=None, ge=0)


class BenchmarkSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    iteration_index: int = Field(ge=0)
    duration_s: float = Field(ge=0)
    scanner_scan_time_s: float = Field(ge=0)
    total_changes: int = Field(ge=0)
    current_file_count: int = Field(ge=0)
    added_count: int = Field(ge=0)
    modified_count: int = Field(ge=0)
    deleted_count: int = Field(ge=0)
    files_processed: int = Field(ge=0)
    files_content_read: int = Field(ge=0)
    cache_hit_ratio: float = Field(ge=0)
    directory_cache: BenchmarkDirectoryCacheStats
    persistent_cache: BenchmarkPersistentCacheStats
    hashed_path_count: int = Field(ge=0)
    hash_duration_s: float = Field(ge=0)
    hashes: dict[str, str]

    @model_validator(mode="after")
    def _validate_hashes(self) -> BenchmarkSample:
        if self.hashed_path_count != len(self.hashes):
            raise ValueError(
                "hashed_path_count must equal the number of recorded hashes"
            )
        invalid_paths = [
            path
            for path, digest in self.hashes.items()
            if not _is_sha256_hexdigest(digest)
        ]
        if invalid_paths:
            raise ValueError(
                "hashes must be SHA-256 hex digests for paths: "
                + ", ".join(sorted(invalid_paths))
            )
        return self


class BenchmarkRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    iteration_count: int = Field(ge=1)
    duration_s: float = Field(ge=0)
    scanner_scan_time_s: float = Field(ge=0)
    hash_duration_s: float = Field(ge=0)
    total_changes: int = Field(ge=0)
    current_file_count: int = Field(ge=0)
    added_count: int = Field(ge=0)
    modified_count: int = Field(ge=0)
    deleted_count: int = Field(ge=0)
    files_processed: int = Field(ge=0)
    files_content_read: int = Field(ge=0)
    cache_hit_ratio: float = Field(ge=0)
    hashed_path_count: int = Field(ge=0)
    hashes: dict[str, str]
    directory_cache: BenchmarkDirectoryCacheStats
    persistent_cache: BenchmarkPersistentCacheStats
    summary: dict[str, BenchmarkStats]
    samples: list[BenchmarkSample]

    @model_validator(mode="after")
    def _validate_samples_and_summary(self) -> BenchmarkRun:
        if len(self.samples) != self.iteration_count:
            raise ValueError("samples length must equal iteration_count")
        expected_indexes = list(range(self.iteration_count))
        actual_indexes = [sample.iteration_index for sample in self.samples]
        if actual_indexes != expected_indexes:
            raise ValueError(
                "samples must be ordered by contiguous iteration_index values"
            )
        labels = {sample.label for sample in self.samples}
        if labels != {self.label}:
            raise ValueError("all samples must use the run label")
        missing_summary = [
            key for key in SUMMARY_METRIC_KEYS if key not in self.summary
        ]
        if missing_summary:
            raise ValueError(
                "summary is missing required metrics: "
                + ", ".join(missing_summary)
            )
        wrong_counts = [
            key
            for key in SUMMARY_METRIC_KEYS
            if self.summary[key].count != self.iteration_count
        ]
        if wrong_counts:
            raise ValueError(
                "summary metric counts must equal iteration_count for: "
                + ", ".join(wrong_counts)
            )
        if self.hashed_path_count != len(self.hashes):
            raise ValueError(
                "run hashed_path_count must equal the number of recorded hashes"
            )
        invalid_paths = [
            path
            for path, digest in self.hashes.items()
            if not _is_sha256_hexdigest(digest)
        ]
        if invalid_paths:
            raise ValueError(
                "run hashes must be SHA-256 hex digests for paths: "
                + ", ".join(sorted(invalid_paths))
            )
        return self


class BenchmarkRecommendation(BaseModel):
    model_config = ConfigDict(extra="allow")

    rust_must_preserve: list[str]
    rust_should_improve: list[str]


class WorkspaceFsBenchmarkReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    benchmark_version: Literal["aware.file_system.workspace_fs_benchmark.v1"]
    backend_kind: Literal["python", "rust"]
    mode: Literal["synthetic_fixture", "real_workspace_readonly"]
    iteration_count: int = Field(ge=1)
    workspace_root: str = Field(min_length=1)
    cache_dir: str = Field(min_length=1)
    fixture: dict[str, Any]
    runs: list[BenchmarkRun]
    recommendation: BenchmarkRecommendation
    receipt_path: str | None = None

    @model_validator(mode="after")
    def _validate_receipt_contract(self) -> WorkspaceFsBenchmarkReceipt:
        expected_labels = expected_run_labels_for_mode(self.mode)
        labels = tuple(run.label for run in self.runs)
        if labels != expected_labels:
            raise ValueError(
                f"{self.mode} run labels must be {expected_labels}, got {labels}"
            )
        wrong_iterations = [
            run.label
            for run in self.runs
            if run.iteration_count != self.iteration_count
        ]
        if wrong_iterations:
            raise ValueError(
                "run iteration_count must equal receipt iteration_count for: "
                + ", ".join(wrong_iterations)
            )
        if self.mode == SYNTHETIC_FIXTURE_MODE:
            _require_fixture_keys(
                self.fixture,
                (
                    "packages",
                    "files_per_package",
                    "payload_bytes",
                    "expected_tracked_file_count",
                    "edit_target",
                ),
            )
        else:
            _require_fixture_keys(self.fixture, ("workspace_root", "source_mutation"))
            if self.fixture["source_mutation"] is not False:
                raise ValueError(
                    "real_workspace_readonly fixture must set source_mutation=false"
                )
        return self


@dataclass(frozen=True, slots=True)
class WorkspaceFsBenchmarkParityReport:
    passed: bool
    benchmark_version: str
    mode: str
    reference_backend_kind: str
    candidate_backend_kind: str
    checked_fields: tuple[str, ...]
    mismatches: tuple[str, ...]


def workspace_fs_benchmark_receipt_json_schema() -> dict[str, Any]:
    return WorkspaceFsBenchmarkReceipt.model_json_schema()


def expected_run_labels_for_mode(mode: str) -> tuple[str, ...]:
    if mode == SYNTHETIC_FIXTURE_MODE:
        return SYNTHETIC_RUN_LABELS
    if mode == REAL_WORKSPACE_READONLY_MODE:
        return REAL_WORKSPACE_RUN_LABELS
    raise BenchmarkReceiptContractError(f"Unsupported benchmark mode: {mode}")


def validate_workspace_fs_benchmark_receipt(
    receipt: Mapping[str, Any],
) -> WorkspaceFsBenchmarkReceipt:
    try:
        return WorkspaceFsBenchmarkReceipt.model_validate(dict(receipt))
    except Exception as exc:
        raise BenchmarkReceiptContractError(str(exc)) from exc


def compare_workspace_fs_benchmark_receipts(
    *,
    reference: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> WorkspaceFsBenchmarkParityReport:
    reference_receipt = validate_workspace_fs_benchmark_receipt(reference)
    candidate_receipt = validate_workspace_fs_benchmark_receipt(candidate)
    mismatches: list[str] = []

    _compare_value(
        mismatches,
        "benchmark_version",
        reference_receipt.benchmark_version,
        candidate_receipt.benchmark_version,
    )
    _compare_value(mismatches, "mode", reference_receipt.mode, candidate_receipt.mode)
    _compare_value(
        mismatches,
        "iteration_count",
        reference_receipt.iteration_count,
        candidate_receipt.iteration_count,
    )
    _compare_fixture(mismatches, reference_receipt, candidate_receipt)

    reference_runs = {run.label: run for run in reference_receipt.runs}
    candidate_runs = {run.label: run for run in candidate_receipt.runs}
    _compare_value(
        mismatches,
        "run_labels",
        tuple(reference_runs),
        tuple(candidate_runs),
    )
    for label, reference_run in reference_runs.items():
        candidate_run = candidate_runs.get(label)
        if candidate_run is None:
            continue
        for field_name in RUN_SEMANTIC_FIELDS:
            _compare_value(
                mismatches,
                f"runs.{label}.{field_name}",
                getattr(reference_run, field_name),
                getattr(candidate_run, field_name),
            )
        _compare_value(
            mismatches,
            f"runs.{label}.hashes",
            reference_run.hashes,
            candidate_run.hashes,
        )
        for index, reference_sample in enumerate(reference_run.samples):
            candidate_sample = candidate_run.samples[index]
            for field_name in RUN_SEMANTIC_FIELDS:
                _compare_value(
                    mismatches,
                    f"runs.{label}.samples.{index}.{field_name}",
                    getattr(reference_sample, field_name),
                    getattr(candidate_sample, field_name),
                )
            _compare_value(
                mismatches,
                f"runs.{label}.samples.{index}.hashes",
                reference_sample.hashes,
                candidate_sample.hashes,
            )

    checked_fields = (
        "benchmark_version",
        "mode",
        "iteration_count",
        "fixture",
        "run_labels",
        *tuple(f"runs.*.{field_name}" for field_name in RUN_SEMANTIC_FIELDS),
        "runs.*.hashes",
        *tuple(f"runs.*.samples.*.{field_name}" for field_name in RUN_SEMANTIC_FIELDS),
        "runs.*.samples.*.hashes",
    )
    return WorkspaceFsBenchmarkParityReport(
        passed=not mismatches,
        benchmark_version=reference_receipt.benchmark_version,
        mode=reference_receipt.mode,
        reference_backend_kind=reference_receipt.backend_kind,
        candidate_backend_kind=candidate_receipt.backend_kind,
        checked_fields=checked_fields,
        mismatches=tuple(mismatches),
    )


def assert_workspace_fs_benchmark_parity(
    *,
    reference: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> WorkspaceFsBenchmarkParityReport:
    report = compare_workspace_fs_benchmark_receipts(
        reference=reference,
        candidate=candidate,
    )
    if not report.passed:
        raise BenchmarkReceiptContractError(
            "Benchmark receipts are not semantically equivalent: "
            + "; ".join(report.mismatches)
        )
    return report


def _compare_fixture(
    mismatches: list[str],
    reference: WorkspaceFsBenchmarkReceipt,
    candidate: WorkspaceFsBenchmarkReceipt,
) -> None:
    if reference.mode != candidate.mode:
        return
    if reference.mode == SYNTHETIC_FIXTURE_MODE:
        for key in (
            "packages",
            "files_per_package",
            "payload_bytes",
            "expected_tracked_file_count",
            "edit_target",
        ):
            _compare_value(
                mismatches,
                f"fixture.{key}",
                reference.fixture.get(key),
                candidate.fixture.get(key),
            )
    else:
        _compare_value(
            mismatches,
            "fixture.source_mutation",
            reference.fixture.get("source_mutation"),
            candidate.fixture.get("source_mutation"),
        )


def _compare_value(
    mismatches: list[str],
    path: str,
    reference_value: object,
    candidate_value: object,
) -> None:
    if reference_value != candidate_value:
        mismatches.append(
            f"{path}: reference={reference_value!r} candidate={candidate_value!r}"
        )


def _require_fixture_keys(fixture: Mapping[str, Any], keys: tuple[str, ...]) -> None:
    missing = [key for key in keys if key not in fixture]
    if missing:
        raise ValueError("fixture is missing required keys: " + ", ".join(missing))


def _is_sha256_hexdigest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)
