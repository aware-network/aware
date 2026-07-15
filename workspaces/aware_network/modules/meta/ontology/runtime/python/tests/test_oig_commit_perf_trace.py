from __future__ import annotations

from aware_meta.graph.instance.commit.perf_trace import (
    CommitPerfTraceRecorder,
    active_commit_perf_trace,
    commit_perf_span,
    record_commit_perf_elapsed,
    summarize_commit_perf_events,
    summarize_commit_perf_profiles,
)


def test_commit_perf_span_is_noop_without_active_recorder() -> None:
    with commit_perf_span(phase="not_recorded"):
        pass
    record_commit_perf_elapsed(phase="not_recorded", started=1.0, ended=2.0)


def test_commit_perf_trace_records_json_events_with_metadata() -> None:
    recorder = CommitPerfTraceRecorder(default_category="code_package.snapshot")

    with active_commit_perf_trace(recorder):
        with commit_perf_span(
            phase="build_class_instances",
            category="code_package.direct_state",
            metadata={"object_count": 3},
        ):
            pass

    events = recorder.snapshot_json()

    assert len(events) == 1
    assert events[0]["category"] == "code_package.direct_state"
    assert events[0]["phase"] == "build_class_instances"
    assert events[0]["duration_ms"] >= 0
    assert events[0]["metadata"] == {"object_count": 3}


def test_commit_perf_trace_records_manual_elapsed_events() -> None:
    recorder = CommitPerfTraceRecorder(default_category="code_package.snapshot")

    with active_commit_perf_trace(recorder):
        record_commit_perf_elapsed(
            phase="wall.prepare",
            started=1.0,
            ended=1.25,
            category="code_package.snapshot.wall",
            metadata={"stage": "update"},
        )

    events = recorder.snapshot_json()

    assert events == (
        {
            "category": "code_package.snapshot.wall",
            "duration_ms": 250.0,
            "metadata": {"stage": "update"},
            "phase": "wall.prepare",
        },
    )


def test_commit_perf_summary_helpers_accept_events_and_profiles() -> None:
    recorder = CommitPerfTraceRecorder()
    recorder.record(phase="build", duration_ms=1.25)
    recorder.record(phase="build", duration_ms=2.75)

    event_summary = summarize_commit_perf_events(recorder.snapshot())
    profile_summary = summarize_commit_perf_profiles(
        (
            {"append_ms": 2, "ignored": "x"},
            {"append_ms": 4, "build_ms": 1.5},
        )
    )

    assert event_summary["build"] == {
        "count": 2,
        "total_ms": 4.0,
        "mean_ms": 2.0,
        "max_ms": 2.75,
    }
    assert profile_summary["append_ms"] == {
        "total": 6,
        "mean": 3.0,
        "max": 4,
    }
    assert profile_summary["build_ms"]["total"] == 1.5
