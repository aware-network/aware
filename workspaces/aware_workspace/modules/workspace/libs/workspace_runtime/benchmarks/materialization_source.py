"""Repeatable source-admission measurements; never materialize or publish.

The full declaration inventory is copied from the supplied repository into a
disposable checkout. All changes, retained bodies and observations live there.
Actual Workspace readers and lifetime checks run; no provider or installed
authority is fabricated. Reported stages must not be labelled command E2E.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import os
import platform
import resource
import statistics
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, cast

from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    DirectInvocationExpectation,
)
from aware_workspace_runtime import (
    FileSystemIndexObservationProvider,
    WorkspaceRepositoryBinding,
    WorkspaceRepositoryObservationSession,
    WorkspaceSourceObservationRuntime,
)
from aware_workspace_runtime.command_lifetime import WorkspaceCommandLifetimeRuntime
from aware_workspace_runtime.composition import (
    LocalCheckoutWorkspaceCompositionProvider,
)
from aware_workspace_runtime.source_exclusion import WorkspaceSourceExclusion
from aware_workspace_runtime.source_observation_io import (
    SourceObservationLimits,
    capture_exact_paths,
)
from aware_workspace_sdk.repository_delta_retention import (
    WorkspaceRepositoryDeltaRetentionFactory,
)

E2E_TARGET_SECONDS = 5.0


def summarize(samples: list[float]) -> dict[str, float | int]:
    if not samples or any(not math.isfinite(value) or value < 0 for value in samples):
        raise ValueError("nonempty finite nonnegative timings required")
    ordered = sorted(samples)
    return {
        "count": len(ordered),
        "median_seconds": statistics.median(ordered),
        "p95_seconds": ordered[math.ceil(0.95 * len(ordered)) - 1],
        "maximum_seconds": ordered[-1],
    }


def capture_inventory(repo_root: Path) -> tuple[dict[str, Any], tuple[tuple[str, bytes], ...]]:
    provider = LocalCheckoutWorkspaceCompositionProvider()
    description = provider.describe(repo_root)
    paths = provider.declaration_body_paths(description)
    fd = os.open(repo_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        rows = capture_exact_paths(fd, paths, SourceObservationLimits())
    finally:
        os.close(fd)
    # Diagnostic copying does not create an admission. The original Workspace
    # observer rediscovers/adopts the complete set in the disposable checkout.
    return cast(dict[str, Any], description), rows


def inventory_digest(rows: tuple[tuple[str, bytes], ...]) -> str:
    payload = [[path, hashlib.sha256(body).hexdigest(), len(body)] for path, body in rows]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


async def benchmark(
    repo_root: Path, *, samples: int = 5, workspace: str = "aware_kernel",
) -> dict[str, Any]:
    if type(samples) is not int or not 1 <= samples <= 30:
        raise ValueError("sample count must be between 1 and 30")
    capture_started = time.perf_counter()
    description, rows = capture_inventory(repo_root)
    capture_seconds = time.perf_counter() - capture_started
    workspaces = description["repository"]["workspaces"]
    matches = [item for item in workspaces if item["workspace_handle"] == workspace]
    if len(matches) != 1:
        raise ValueError("one declared benchmark Workspace required")
    selected_workspace = matches[0]
    # Choose distinct declared package roots, without interpreting package
    # features or semantic dependencies. This is source observation only.
    packages: list[tuple[str, dict[str, Any]]] = []
    seen: set[str] = set()
    for module in selected_workspace["modules"]:
        for package in module["packages"]:
            if package["package_root"] not in seen:
                packages.append((module["module_id"], package))
                seen.add(package["package_root"])
    if not packages:
        raise ValueError("at least one declared package required")
    metrics: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="aware-materialize-source-benchmark-") as scratch:
        scratch_root = Path(scratch)
        checkout = scratch_root / "repository"
        checkout.mkdir()
        for path, body in rows:
            target = checkout / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
        binding = WorkspaceRepositoryBinding(checkout)
        session = WorkspaceRepositoryObservationSession(
            binding=binding, provider=FileSystemIndexObservationProvider(binding=binding),
        )
        command = WorkspaceCommandLifetimeRuntime()
        parent = command._retain_direct_invocation_parent()
        expectation = DirectInvocationExpectation(
            command.invocation_identity, command.epoch_identity, os.getpid(),
        )
        exclusion = WorkspaceSourceExclusion(runtime=command, parent=parent, expected=expectation)
        binding_ref = binding.binding_key
        if binding_ref is None:
            raise RuntimeError("repository binding identity unavailable")
        store = WorkspaceRepositoryDeltaRetentionFactory.filesystem(
            state_root=scratch_root / "state",
        ).allocate_delta_retention()
        store.initialize_delta_retention(
            repository_binding_ref=binding_ref,
            body_capacity=4096,
        )
        observer = None
        started = time.perf_counter()
        await session.start(background=False)
        session_seconds = time.perf_counter() - started
        try:
            observer = WorkspaceSourceObservationRuntime(session=session, store=store, exclusion=exclusion)
            started = time.perf_counter()
            declaration = observer.observe_declarations()
            admission_seconds = time.perf_counter() - started
            evidence = observer.declaration_evidence(declaration)
            if tuple(item.relative_path for item in evidence.bodies) != tuple(path for path, _ in rows):
                raise RuntimeError("copied declaration coverage differs")
            latencies = []
            before = store.snapshot().metrics
            for _ in range(samples):
                started = time.perf_counter()
                observer.revalidate_declarations(declaration)
                latencies.append(time.perf_counter() - started)
            after = store.snapshot().metrics
            metrics.append({
                "stage": "complete_declaration_currentness", "samples_seconds": latencies,
                **summarize(latencies),
                "retained_body_reads": after.body_read_count - before.body_read_count,
                "retained_body_bytes": after.body_read_bytes - before.body_read_bytes,
            })
            for touched in dict.fromkeys((1, min(3, len(packages)))):
                chosen = packages[:touched]
                latencies = []
                before = store.snapshot().metrics
                for sample in range(samples):
                    # Explicitly synthetic source edits, confined to scratch.
                    # These bytes are not Meta meaning or a published DELTA.
                    for _, package in chosen:
                        (checkout / package["package_root"] / "benchmark-source.bin").write_bytes(
                            f"sample {sample} / touched {touched}".encode() + b"x" * 1024,
                        )
                    started = time.perf_counter()
                    handles = []
                    try:
                        for module_id, package in chosen:
                            handle = observer.observe_selected_package(
                                declaration=declaration,
                                workspace_manifest_path=selected_workspace["manifest_path"],
                                module_id=module_id, package_id=package["package_id"],
                            )
                            handles.append(handle)
                            observer.revalidate_selected_package(handle)
                    finally:
                        for handle in reversed(handles):
                            observer.release_selected_package(handle)
                    latencies.append(time.perf_counter() - started)
                after = store.snapshot().metrics
                metrics.append({
                    "stage": "selected_source_admission_and_currentness",
                    "touched_packages": touched,
                    "addresses": [
                        [workspace, module_id, package["package_id"]]
                        for module_id, package in chosen
                    ],
                    "samples_seconds": latencies, **summarize(latencies),
                    "retained_body_reads": after.body_read_count - before.body_read_count,
                    "retained_body_bytes": after.body_read_bytes - before.body_read_bytes,
                })
            observer.release_declarations(declaration)
        finally:
            if observer is not None:
                observer.close()
            command.close()
            await session.stop()
    runtime_root = Path(__file__).parents[1] / "aware_workspace_runtime"
    return {
        "schema": "aware.workspace.materialization-source-benchmark.v1",
        "grade": "original_workspace_component_in_disposable_declaration_copy",
        "command_e2e_qualified": False,
        "sampling": {
            "command_count": 1, "declarations_observed_once": True,
            "selected_handles_reissued_per_sample": True,
            "source_bodies": "synthetic_1kib_in_disposable_checkout",
            "timed_work": "source_admission_currentness_and_handle_release",
            "setup_included_in_metric_samples": False,
        },
        "runtime": {
            "python_version": sys.version, "python_executable": sys.executable,
            "platform": platform.platform(), "machine": platform.machine(),
            "cpu_count": os.cpu_count(),
            "cpu_affinity_count": len(os.sched_getaffinity(0)),
            "source_sha256": {
                name: hashlib.sha256((runtime_root / name).read_bytes()).hexdigest()
                for name in ("source_observation.py", "source_observation_io.py")
            },
        },
        "target_command_e2e_seconds": E2E_TARGET_SECONDS,
        "unmeasured_command_stages": [
            "installed_launch", "code_selected_planning", "dependency_fulfillment",
            "meta_delta", "ontology_lowering", "publication_and_positive_reread",
            "installed_terminal_settlement",
        ],
        "inventory": {
            "declaration_count": len(rows), "declaration_bytes": sum(len(body) for _, body in rows),
            "digest": inventory_digest(rows), "workspace_count": len(workspaces),
            "selected_workspace": workspace, "module_count": len(selected_workspace["modules"]),
            "package_count": sum(len(module["packages"]) for module in selected_workspace["modules"]),
        },
        "setup_seconds": {
            "original_inventory_capture": capture_seconds, "session_start": session_seconds,
            "initial_declaration_admission": admission_seconds,
        },
        "metrics": metrics,
        "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--workspace", default="aware_kernel")
    parser.add_argument("--samples", type=int, default=5)
    arguments = parser.parse_args()
    value = asyncio.run(benchmark(arguments.repo_root, samples=arguments.samples, workspace=arguments.workspace))
    print(json.dumps(value, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
