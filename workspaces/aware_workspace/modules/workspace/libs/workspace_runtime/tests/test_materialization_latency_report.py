"""Diagnostic accounting must expose overlap, residuals and failed cleanup."""

import asyncio
import gc
import sys
import weakref

import pytest
from materialization_latency_report import (
    BoundaryTimings,
    LatencyReport,
    thread_cost_sample,
)


def clock(*values):
    return iter(values).__next__


def test_serial_phases_reconcile_exactly_with_residual():
    trace = LatencyReport(clock=clock(0, 10, 30, 40, 80, 100))
    first = trace.start("admission")
    trace.stop(first)
    second = trace.start("execution")
    trace.stop(second)
    report = trace.finish(succeeded=True)
    assert report["covered_ns"] == 60
    assert report["unattributed_ns"] == 40
    assert report["elapsed_ns"] == 100
    assert report["top_level_overlap_ns"] == 0
    assert report["complete"]


def test_nested_overlapping_children_use_union_for_exclusive_time():
    trace = LatencyReport(clock=clock(0, 10, 20, 30, 50, 70, 90, 100))
    parent = trace.start("execution")
    first = trace.start("validation", parent=parent)
    second = trace.start("owner", parent=parent)
    trace.stop(first)
    trace.stop(second)
    trace.stop(parent)
    report = trace.finish(succeeded=True)
    assert report["spans"][0]["elapsed_ns"] == 80
    assert report["spans"][0]["exclusive_ns"] == 30
    assert report["covered_ns"] == 80
    assert report["unattributed_ns"] == 20


def test_top_level_overlap_is_reported_not_hidden_by_clamping():
    trace = LatencyReport(clock=clock(0, 10, 20, 50, 70, 100))
    first = trace.start("first")
    second = trace.start("second")
    trace.stop(first)
    trace.stop(second)
    report = trace.finish(succeeded=True)
    assert report["covered_ns"] == 60
    assert report["top_level_overlap_ns"] == 30
    assert report["unattributed_ns"] == 40


def test_failure_never_reports_unfinished_cleanup_as_completed():
    trace = LatencyReport(clock=clock(0, 10, 20, 100))
    parent = trace.start("operation")
    trace.start("cleanup", parent=parent)
    report = trace.finish(succeeded=False)
    assert not report["complete"]
    assert not report["succeeded"]
    assert [s["status"] for s in report["spans"]] == ["incomplete", "incomplete"]


def test_metadata_is_detached_without_retaining_owner_objects():
    trace = LatencyReport(clock=clock(0, 10))
    data = {"counts": [1, 2]}
    trace.attach("workload", data)
    data["counts"].append(3)
    with pytest.raises(TypeError):
        trace.attach("owner", object())
    assert trace.finish(succeeded=True)["metadata"] == {"workload": {"counts": [1, 2]}}


def test_disabled_reporting_does_not_read_clock():
    def forbidden():
        pytest.fail("disabled diagnostic called clock")

    trace = LatencyReport(enabled=False, clock=forbidden)
    marker = trace.start("owner")
    trace.stop(marker)
    trace.attach("ignored", object())
    assert trace.finish(succeeded=True) is None


def test_duplicate_stop_and_live_child_refuse():
    trace = LatencyReport(clock=clock(0, 10, 20, 30, 40))
    parent = trace.start("parent")
    child = trace.start("child", parent=parent)
    with pytest.raises(ValueError, match="child remains open"):
        trace.stop(parent)
    trace.stop(child)
    trace.stop(parent)
    with pytest.raises(ValueError, match="already ended"):
        trace.stop(parent)


def test_backward_clock_is_not_clamped_to_zero():
    trace = LatencyReport(clock=clock(0, 50, 20, 100))
    marker = trace.start("phase")
    trace.stop(marker)
    with pytest.raises(ValueError, match="interval outside root"):
        trace.finish(succeeded=True)


def test_original_boundaries_nest_without_replacing_functions():
    def child():
        return 7

    def parent():
        return child() + 1

    trace = LatencyReport()
    root = trace.start("wall")
    original = parent
    with BoundaryTimings(trace, root, (("parent", parent), ("child", child)), enabled=True):
        assert parent is original
        assert parent() == 8
    trace.stop(root)
    result = trace.finish(succeeded=True)
    wall, outer, inner = result["spans"]
    assert inner["parent_id"] == outer["span_id"]
    assert outer["parent_id"] == wall["span_id"]
    assert outer["elapsed_ns"] == outer["exclusive_ns"] + inner["elapsed_ns"]
    assert result["metadata"]["boundary_observation"]["call_counts"] == {
        "parent": 1, "child": 1,
    }


def test_coroutine_suspension_is_not_counted_as_active_work():
    async def suspended():
        await asyncio.sleep(0)
        return 3

    trace = LatencyReport()
    root = trace.start("wall")
    with BoundaryTimings(trace, root, (("async", suspended),), enabled=True):
        assert asyncio.run(suspended()) == 3
    trace.stop(root)
    result = trace.finish(succeeded=True)
    assert [s["stage"] for s in result["spans"]] == ["wall", "async", "async"]
    assert result["metadata"]["boundary_observation"]["call_counts"] == {"async": 1}
    assert result["metadata"]["boundary_observation"]["errors"] == []


def test_unwind_removes_monitoring_and_does_not_retain_returned_resources():
    class Resource:
        pass

    def give():
        return Resource()

    def fail():
        raise ValueError("original error")

    trace = LatencyReport()
    root = trace.start("wall")
    observer = BoundaryTimings(trace, root, (("give", give), ("fail", fail)), enabled=True)
    with pytest.raises(ValueError, match="original error"), observer:
        slot = observer.tool
        resource = give()
        ref = weakref.ref(resource)
        del resource
        fail()
    gc.collect()
    assert ref() is None
    assert observer.tool is None
    assert sys.monitoring.get_tool(slot) is None
    trace.stop(root)
    result = trace.finish(succeeded=False)
    assert result["metadata"]["boundary_observation"]["errors"] == []


def test_disabled_boundaries_leave_monitoring_slots_unchanged():
    def original():
        return 1

    before = [sys.monitoring.get_tool(i) for i in range(6)]
    trace = LatencyReport(enabled=False)
    with BoundaryTimings(trace, None, (("original", original),), enabled=False):
        assert original() == 1
    assert [sys.monitoring.get_tool(i) for i in range(6)] == before


def test_coroutine_throw_and_unrelated_exception_preserve_original_failure():
    async def suspended():
        await asyncio.sleep(0)

    trace = LatencyReport()
    root = trace.start("wall")
    with BoundaryTimings(trace, root, (("async", suspended),), enabled=True):
        with pytest.raises(KeyError):
            {}["foreign"]
        coroutine = suspended()
        assert coroutine.send(None) is None
        with pytest.raises(RuntimeError, match="cancelled"):
            coroutine.throw(RuntimeError("cancelled"))
    trace.stop(root)
    result = trace.finish(succeeded=False)
    assert result["metadata"]["boundary_observation"]["errors"] == []
    assert result["metadata"]["boundary_observation"]["call_counts"] == {"async": 1}
    assert len(result["spans"]) == 3


def counters(*values):
    samples = iter(values)
    return lambda: {"thread_cpu_ns": next(samples)}


def test_serial_cpu_partition_and_unclassified_wall_residual():
    trace = LatencyReport(
        clock=clock(0, 10, 30, 40, 80, 100), counters=counters(0, 5, 15, 20, 35, 50),
    )
    first = trace.start("admission")
    trace.stop(first)
    second = trace.start("execution")
    trace.stop(second)
    report = trace.finish(succeeded=True)
    costs = report["counter_accounting"]
    assert costs["delta"]["thread_cpu_ns"] == 50
    assert costs["covered"]["thread_cpu_ns"] == 25
    assert costs["unattributed"]["thread_cpu_ns"] == 25
    assert costs["top_level_overlap"]["thread_cpu_ns"] == 0
    assert costs["wall_minus_thread_cpu_ns"] == 50
    assert costs["wait_qualification"].startswith("unclassified residual")
    assert report["spans"][0]["counters_exclusive"]["thread_cpu_ns"] == 10


def test_overlapping_cpu_children_are_unioned_without_double_counting():
    trace = LatencyReport(
        clock=clock(0, 10, 20, 30, 50, 70, 90, 100),
        counters=counters(0, 5, 10, 15, 25, 35, 45, 50),
    )
    parent = trace.start("parent")
    first = trace.start("first", parent=parent)
    second = trace.start("second", parent=parent)
    trace.stop(first)
    trace.stop(second)
    trace.stop(parent)
    report = trace.finish(succeeded=True)
    outer = report["spans"][0]
    assert outer["counters_delta"]["thread_cpu_ns"] == 40
    assert outer["counters_exclusive"]["thread_cpu_ns"] == 15
    assert report["counter_accounting"]["covered"]["thread_cpu_ns"] == 40


def test_overlapping_top_level_cpu_reports_overlap():
    trace = LatencyReport(
        clock=clock(0, 10, 20, 50, 70, 100), counters=counters(0, 5, 10, 25, 35, 50),
    )
    first = trace.start("first")
    second = trace.start("second")
    trace.stop(first)
    trace.stop(second)
    report = trace.finish(succeeded=True)
    costs = report["counter_accounting"]
    assert costs["covered"]["thread_cpu_ns"] == 30
    assert costs["top_level_overlap"]["thread_cpu_ns"] == 15
    assert costs["unattributed"]["thread_cpu_ns"] == 20


def test_counter_failure_closes_open_spans_as_incomplete():
    trace = LatencyReport(clock=clock(0, 10, 20, 100), counters=counters(0, 5, 10, 50))
    parent = trace.start("operation")
    trace.start("cleanup", parent=parent)
    report = trace.finish(succeeded=False)
    assert not report["complete"]
    assert all(s["counters_end"]["thread_cpu_ns"] == 50 for s in report["spans"])


def test_counter_samples_are_detached():
    sample = {"thread_cpu_ns": 0}
    trace = LatencyReport(clock=clock(0, 100), counters=lambda: sample)
    sample["thread_cpu_ns"] = 50
    report = trace.finish(succeeded=True)
    assert report["counter_accounting"]["start"] == {"thread_cpu_ns": 0}
    assert report["counter_accounting"]["delta"] == {"thread_cpu_ns": 50}


@pytest.mark.parametrize("sample", [{}, {"x": -1}, {"x": True}, {"x": 1.0}, {1: 1}])
def test_malformed_counters_refuse(sample):
    with pytest.raises(ValueError, match="nonnegative integer"):
        LatencyReport(counters=lambda: sample)


def test_counter_schema_change_refuses():
    samples = iter(({"a": 0}, {"b": 1}))
    trace = LatencyReport(clock=clock(0, 100), counters=samples.__next__)
    with pytest.raises(ValueError, match="schema changed"):
        trace.finish(succeeded=True)


def test_nested_counter_reversal_cannot_hide_in_root_total():
    trace = LatencyReport(clock=clock(0, 10, 20, 100), counters=counters(0, 20, 10, 50))
    marker = trace.start("phase")
    trace.stop(marker)
    with pytest.raises(ValueError, match="moved backwards"):
        trace.finish(succeeded=True)


def test_negative_wall_cpu_residual_is_exposed_without_clamping():
    trace = LatencyReport(clock=clock(0, 10), counters=counters(0, 11))
    assert trace.finish(succeeded=True)["counter_accounting"]["wall_minus_thread_cpu_ns"] == -1


def test_disabled_counters_are_not_observed():
    def forbidden():
        pytest.fail("disabled diagnostic sampled counters")

    trace = LatencyReport(enabled=False, clock=forbidden, counters=forbidden)
    trace.start("ignored")
    trace.stop(None)
    assert trace.finish(succeeded=True) is None


def test_default_report_has_no_counter_fields():
    trace = LatencyReport(clock=clock(0, 10))
    assert "counter_accounting" not in trace.finish(succeeded=True)


def test_original_thread_sample_has_monotonic_numeric_counters():
    first = thread_cost_sample()
    for _ in range(1000):
        pass
    second = thread_cost_sample()
    assert set(first) == set(second)
    assert all(type(v) is int and v >= 0 for v in first.values())
    assert all(second[name] >= first[name] for name in first)


@pytest.mark.parametrize("event", ["resume", "close"])
def test_counter_failure_does_not_retain_callback_values_in_held_error(event):
    class Resource:
        pass

    class FailingTrace:
        def start(self, *args, **kwargs):
            raise RuntimeError("counter unavailable")

        def stop(self, *args, **kwargs):
            raise RuntimeError("counter unavailable")

    def original():
        return None

    observer = BoundaryTimings(FailingTrace(), None, (("original", original),), enabled=True)
    value = Resource()
    ref = weakref.ref(value)
    held = None
    try:
        if event == "resume":
            observer._resume(original.__code__, 0, value)
        else:
            observer.active.append((original.__code__, 0))
            observer._close(original.__code__, 0, value)
    except RuntimeError as error:
        held = error
    del value
    gc.collect()
    assert held is not None
    assert ref() is None


def test_closing_and_finalizing_do_not_rescan_all_spans_per_span():
    class CountedSpans(list):
        visits = 0

        def __iter__(self):
            self.visits += len(self)
            return super().__iter__()

    now = iter(range(100_000)).__next__
    # Every sample advances both clocks while preserving endpoint ordering.
    trace = LatencyReport(clock=now, counters=lambda: {"thread_cpu_ns": now()})
    trace._spans = CountedSpans()
    root = trace.start("root")
    for _ in range(1000):
        marker = trace.start("child", parent=root)
        trace.stop(marker)
    trace.stop(root)
    assert trace._spans.visits == 0
    result = trace.finish(succeeded=True)
    assert trace._spans.visits <= len(trace._spans) * 2
    assert len(result["spans"]) == 1001
    assert result["complete"]
