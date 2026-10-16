"""Run the existing disposable source-grade materialization fixture with timings.

Usage: .venv/bin/python -B <this file> --output-dir /tmp/new-report --runs 3
Add --profile for one separate cProfile run; profile times are not latency data.
This does not execute the public CLI or qualify installed factory intake.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pstats
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path

_ENTRY_NS = time.perf_counter_ns()


def _repo_root():
    return Path(
        subprocess.check_output(
            [
                "git",
                "-C",
                str(Path(__file__).resolve().parent),
                "rev-parse",
                "--show-toplevel",
            ],
            text=True,
        ).strip()
    )


def _pins(root):
    paths = [
        root / "workspaces/aware_workspace/modules/workspace/libs/workspace_runtime",
        root
        / "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public",
        root
        / "workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python",
        root
        / "workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime",
        root
        / "workspaces/aware_network/modules/attention/libs/attention_definition_contract_runtime_provider",
    ]
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for directory in paths
        for path in directory.rglob("*.py")
    }


def _verify(root, pins):
    for name, expected in pins.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"source pin changed: {name}")


def _child(root, destination, profile):
    # Pytest supplies the same original source/factory/lifetime fixture; no
    # reconstructed registration, authority completion or provider execution.
    import pytest

    test = (
        root
        / "workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_cli_product_publication.py"
    )
    os.environ["AWARE_MATERIALIZATION_BENCHMARK_REPORT"] = str(destination)
    args = [
        "--noconftest",
        "-c",
        "/dev/null",
        "-p",
        "no:cacheprovider",
        "-p",
        "pytest_asyncio.plugin",
        "-o",
        "asyncio_mode=auto",
        "-o",
        "asyncio_default_fixture_loop_scope=function",
        "-q",
        "--tb=short",
        str(test) + "::test_original_local_graph_executes_publishes_and_rereads",
    ]
    if profile:
        import cProfile

        profiler = cProfile.Profile()
        profiler.enable()
        result = pytest.main(args)
        profiler.disable()
        profiler.dump_stats(str(destination.with_suffix(".prof")))
    else:
        result = pytest.main(args)
    finished = time.perf_counter_ns()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    if result != 0 or not destination.exists():
        return result or 1
    report = json.loads(destination.read_text())
    report["runner"] = {
        "entry_ns": _ENTRY_NS,
        "end_ns": finished,
        "elapsed_ns": finished - _ENTRY_NS,
        "before_test_body_ns": report["start_ns"] - _ENTRY_NS,
        "after_test_body_ns": finished - report["end_ns"],
        "user_cpu_seconds": usage.ru_utime,
        "system_cpu_seconds": usage.ru_stime,
        "max_rss_kib": usage.ru_maxrss // 1024
        if sys.platform == "darwin"
        else usage.ru_maxrss,
        "profiled": profile,
    }
    destination.write_text(json.dumps(report, indent=2) + "\n")
    return 0


def _profile_summary(path):
    stats = vars(pstats.Stats(str(path)))
    names = {
        "validate_semantic_input_source",
        "validate_registered_semantic_input_result",
        "_validate_selected_input_read_record",
        "revalidate_selected_package",
        "revalidate_declarations",
        "resolve_body",
        "_closure",
        "_check_declaration_projection_result",
        "declaration_closure_payload_bytes",
    }
    counts = [
        {
            "file": file,
            "function": name,
            "calls": value[1],
            "self_seconds": value[2],
            "inclusive_seconds": value[3],
        }
        for (file, _, name), value in stats["stats"].items()
        if name in names
    ]
    top_self = [
        {"file": file, "function": name, "calls": value[1], "self_seconds": value[2]}
        for (file, _, name), value in sorted(
            stats["stats"].items(), key=lambda row: row[1][2], reverse=True
        )[:30]
    ]
    brackets = [
        value[1]
        for (_, _, name), stats_row in stats["stats"].items()
        if name == "revalidate_declarations"
        for (_, _, caller), value in stats_row[4].items()
        if caller == "revalidate_selected_package"
    ]
    return {
        "profile_overhead_not_latency": True,
        "total_calls": stats["total_calls"],
        "profile_seconds": stats["total_tt"],
        "counts": counts,
        "capture_brackets": sum(brackets),
        "top_self": top_self,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("--boundaries", action="store_true", help="observe selected original code boundaries")
    parser.add_argument("--paired-boundaries", action="store_true", help="alternate baseline and observed runs")
    parser.add_argument("--child-report", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.boundaries and args.paired_boundaries:
        parser.error("choose --boundaries or --paired-boundaries, not both")
    root = _repo_root()
    if args.child_report is not None:
        os.environ["AWARE_MATERIALIZATION_BENCHMARK_BOUNDARIES"] = "1" if args.boundaries else "0"
        return _child(root, args.child_report, args.profile)
    if args.output_dir is None or not 1 <= args.runs <= 20:
        parser.error("provide a new output directory and 1–20 runs")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    pins = _pins(root)
    (output / "source-pins.json").write_text(json.dumps(pins, indent=2) + "\n")
    tests = (
        root
        / "workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests"
    )
    helpers = [
        tests,
        root
        / "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests",
        root
        / "workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests",
        root
        / "workspaces/aware_network/modules/environment/libs/environment_semantic_contract_runtime_provider/tests",
    ]
    env = dict(
        os.environ,
        PYTHONPATH=os.pathsep.join(map(str, helpers)),
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        PYTHONDONTWRITEBYTECODE="1",
    )
    rows = []
    jobs = [(f"run-{index}", False) for index in range(1, args.runs + 1)]
    if args.paired_boundaries:
        jobs = [
            (f"{arm}-{index}", False)
            for index in range(1, args.runs + 1)
            for arm in (("baseline", "observed") if index % 2 else ("observed", "baseline"))
        ]
    if args.profile:
        jobs.append(("profile", True))
    for name, profiled in jobs:
        _verify(root, pins)
        destination = output / f"{name}.json"
        command = [
            str(root / ".venv/bin/python"),
            "-B",
            str(Path(__file__).resolve()),
            "--child-report",
            str(destination),
        ]
        if profiled:
            command.append("--profile")
        observed = args.boundaries or name.startswith("observed-")
        if observed:
            command.append("--boundaries")
        start = time.perf_counter_ns()
        with (output / f"{name}.log").open("w") as log:
            completed = subprocess.run(
                command,
                cwd=root,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
        end = time.perf_counter_ns()
        _verify(root, pins)
        if completed.returncode != 0:
            raise RuntimeError(f"{name} failed; see {output / (name + '.log')}")
        report = json.loads(destination.read_text())
        if not report["succeeded"] or not report["complete"]:
            raise RuntimeError(f"{name} diagnostic is incomplete")
        if report["metadata"]["boundary_observation"]["errors"]:
            raise RuntimeError(f"{name} boundary observation is incomplete")
        report["outer_process_wall_ns"] = end - start
        report["interpreter_launch_and_exit_ns"] = (
            end - start - report["runner"]["elapsed_ns"]
        )
        destination.write_text(json.dumps(report, indent=2) + "\n")
        rows.append(
            {
                "name": name,
                "profiled": profiled,
                "boundaries_observed": observed,
                "process_seconds": (end - start) / 1e9,
                "test_body_seconds": report["elapsed_ns"] / 1e9,
            }
        )
        print(
            name,
            f"process={(end - start) / 1e9:.3f}s body={report['elapsed_ns'] / 1e9:.3f}s",
            flush=True,
        )
        if profiled:
            (output / "profile-summary.json").write_text(
                json.dumps(_profile_summary(destination.with_suffix(".prof")), indent=2)
                + "\n"
            )
    measured = [row for row in rows if not row["profiled"]]
    summary = {
        "qualification": "source_fixture",
        "public_command": False,
        "runs": rows,
        "median_process_seconds": None if args.paired_boundaries else statistics.median(
            row["process_seconds"] for row in measured
        ),
        "median_test_body_seconds": None if args.paired_boundaries else statistics.median(
            row["test_body_seconds"] for row in measured
        ),
        "source_pins_checked": len(pins),
        "per_arm_medians": {
            arm: {
                "process_seconds": statistics.median(row["process_seconds"] for row in measured if row["boundaries_observed"] == observed),
                "test_body_seconds": statistics.median(row["test_body_seconds"] for row in measured if row["boundaries_observed"] == observed),
            }
            for arm, observed in (("baseline", False), ("observed", True))
            if any(row["boundaries_observed"] == observed for row in measured)
        },
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
