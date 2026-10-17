"""Benchmark-only wall accounting; never admission or runtime authority."""

import json
import resource
import sys
import time
from itertools import pairwise
from pathlib import Path
from threading import get_ident


def thread_cost_sample():
    """Current-thread counters; only thread_cpu_ns supports fine attribution.

    Resource counters are sampled separately and may update in coarse quanta.
    Their nested differences are raw arithmetic, not precise leaf costs.
    """
    usage = resource.getrusage(resource.RUSAGE_THREAD)
    return {
        "thread_cpu_ns": time.thread_time_ns(),
        "user_cpu_ns": round(usage.ru_utime * 1_000_000_000),
        "system_cpu_ns": round(usage.ru_stime * 1_000_000_000),
        "voluntary_context_switches": usage.ru_nvcsw,
        "involuntary_context_switches": usage.ru_nivcsw,
        "minor_faults": usage.ru_minflt,
        "major_faults": usage.ru_majflt,
    }


def _counter_coverage(spans, names):
    """Union cumulative counters at the same interval endpoints as wall time."""
    result = dict.fromkeys(names, 0)
    first = last = None
    for span in sorted(spans, key=lambda s: s["start_ns"]):
        if last is None or span["start_ns"] > last["end_ns"]:
            if last is not None:
                for name in names:
                    result[name] += last["counters_end"][name] - first["counters_start"][name]
            first = last = span
        elif span["end_ns"] > last["end_ns"]:
            last = span
    if last is not None:
        for name in names:
            result[name] += last["counters_end"][name] - first["counters_start"][name]
    return result


def _covered(intervals):
    """Union duration, so nested or concurrent intervals are not summed twice."""
    total = 0
    end = None
    for start, stop in sorted(intervals):
        if stop < start:
            raise ValueError("negative diagnostic interval")
        if end is None or start > end:
            total += stop - start
        elif stop > end:
            total += stop - end
        end = stop if end is None else max(end, stop)
    return total


class LatencyReport:
    def __init__(self, *, enabled=True, clock=time.perf_counter_ns, counters=None):
        self.enabled = enabled
        self._clock = clock
        self._started = clock() if enabled else None
        self._counters = counters
        self._counter_names = None
        self._counter_started = self._sample() if enabled else None
        self._ended = None
        self._spans = []
        self._open_children = []
        self._metadata = {}

    def _sample(self):
        if self._counters is None:
            return None
        sample = self._counters()
        if type(sample) is not dict or not sample or any(
            type(name) is not str or not name or type(value) is not int or value < 0
            for name, value in sample.items()
        ):
            raise ValueError("diagnostic counters must be nonnegative integer fields")
        names = tuple(sorted(sample))
        if self._counter_names is not None and names != self._counter_names:
            raise ValueError("diagnostic counter schema changed")
        self._counter_names = names
        return dict(sample)

    def start(self, stage, *, parent=None):
        if not self.enabled:
            return None
        if self._ended is not None or type(stage) is not str or not stage:
            raise ValueError("diagnostic stage unavailable")
        if parent is not None and (
            type(parent) is not int
            or not 0 <= parent < len(self._spans)
            or self._spans[parent]["end_ns"] is not None
        ):
            raise ValueError("diagnostic parent unavailable")
        marker = len(self._spans)
        self._spans.append(
            {
                "span_id": marker,
                "parent_id": parent,
                "stage": stage,
                "start_ns": self._clock(),
                "end_ns": None,
                "status": "open",
            }
        )
        self._open_children.append(0)
        if parent is not None:
            self._open_children[parent] += 1
        if self._counters is not None:
            self._spans[-1]["counters_start"] = self._sample()
            self._spans[-1]["counters_end"] = None
        return marker

    def stop(self, marker):
        if not self.enabled:
            return
        if type(marker) is not int or not 0 <= marker < len(self._spans):
            raise ValueError("diagnostic marker unavailable")
        span = self._spans[marker]
        if self._ended is not None or span["end_ns"] is not None:
            raise ValueError("diagnostic stage already ended")
        if self._open_children[marker]:
            raise ValueError("diagnostic child remains open")
        span["end_ns"] = self._clock()
        if self._counters is not None:
            span["counters_end"] = self._sample()
        span["status"] = "completed"
        if span["parent_id"] is not None:
            self._open_children[span["parent_id"]] -= 1

    def attach(self, name, value):
        if self.enabled:
            # Retain detached descriptive JSON only, never owner handles/results.
            self._metadata[name] = json.loads(json.dumps(value, allow_nan=False))

    def finish(self, *, succeeded):
        if not self.enabled:
            return None
        if self._ended is not None:
            raise ValueError("diagnostic root already ended")
        self._ended = self._clock()
        counter_end = self._sample()
        spans = []
        for original in self._spans:
            span = dict(original)
            if span["end_ns"] is None:
                span["end_ns"] = self._ended
                span["status"] = "incomplete"
                if self._counters is not None:
                    span["counters_end"] = counter_end
            spans.append(span)
        children_by_parent = {}
        for span in spans:
            children_by_parent.setdefault(span["parent_id"], []).append(span)
        for span in spans:
            if not self._started <= span["start_ns"] <= span["end_ns"] <= self._ended:
                raise ValueError("diagnostic interval outside root")
            children = children_by_parent.get(span["span_id"], ())
            if any(
                not span["start_ns"] <= s["start_ns"] <= s["end_ns"] <= span["end_ns"]
                for s in children
            ):
                raise ValueError("diagnostic child outside parent")
            span["elapsed_ns"] = span["end_ns"] - span["start_ns"]
            span["exclusive_ns"] = span["elapsed_ns"] - _covered(
                [(s["start_ns"], s["end_ns"]) for s in children]
            )
            if self._counters is not None:
                delta = {
                    name: span["counters_end"][name] - span["counters_start"][name]
                    for name in self._counter_names
                }
                covered_counters = _counter_coverage(children, self._counter_names)
                span["counters_delta"] = delta
                span["counters_exclusive"] = {
                    name: delta[name] - covered_counters[name]
                    for name in self._counter_names
                }
        top = children_by_parent.get(None, ())
        covered = _covered([(s["start_ns"], s["end_ns"]) for s in top])
        elapsed = self._ended - self._started
        report = {
            "format": "aware.workspace.materialization-latency-diagnostics.v1",
            "qualification": "source_fixture",
            "public_command": False,
            "succeeded": succeeded,
            "complete": all(s["status"] == "completed" for s in spans),
            "start_ns": self._started,
            "end_ns": self._ended,
            "elapsed_ns": elapsed,
            "covered_ns": covered,
            "unattributed_ns": elapsed - covered,
            "top_level_overlap_ns": sum(s["elapsed_ns"] for s in top) - covered,
            "spans": spans,
            "metadata": self._metadata,
        }
        if self._counters is not None:
            points = [(self._started, self._counter_started), (self._ended, counter_end)]
            for span in spans:
                points.extend(((span["start_ns"], span["counters_start"]),
                               (span["end_ns"], span["counters_end"])))
            points.sort(key=lambda pair: pair[0])
            if any(
                stop[name] < start[name]
                for (_, start), (_, stop) in pairwise(points)
                for name in self._counter_names
            ):
                raise ValueError("diagnostic cumulative counter moved backwards")
            delta = {name: counter_end[name] - self._counter_started[name]
                     for name in self._counter_names}
            covered_counters = _counter_coverage(top, self._counter_names)
            report["counter_accounting"] = {
                "scope": "single observed thread; endpoint samples are not simultaneous",
                "start": self._counter_started,
                "end": counter_end,
                "delta": delta,
                "covered": covered_counters,
                "unattributed": {name: delta[name] - covered_counters[name]
                                 for name in self._counter_names},
                "top_level_overlap": {
                    name: sum(s["counters_delta"][name] for s in top) - covered_counters[name]
                    for name in self._counter_names
                },
                "wall_minus_thread_cpu_ns": (
                    elapsed - delta["thread_cpu_ns"] if "thread_cpu_ns" in delta else None
                ),
                "wait_qualification": "unclassified residual; not measured scheduler or I/O wait",
                "resource_precision": (
                    "user/system/context counters are separate coarse samples; "
                    "nested differences are not qualified leaf attribution"
                ),
            }
        return report

    @staticmethod
    def write(report, destination):
        Path(destination).write_text(json.dumps(report, indent=2) + "\n")


class BoundaryTimings:
    """Observe selected code objects without retaining frames, arguments or results.

    Coroutine yield closes an active segment; resume opens another. Suspended
    time stays in the enclosing wall span, not falsely counted as owner work.
    """

    def __init__(self, trace, parent, targets, *, enabled):
        self.trace, self.parent = trace, parent
        self.targets = {function.__code__: name for name, function in targets}
        self.enabled = enabled
        self.tool = None
        self.active = []
        self.counts = dict.fromkeys(self.targets.values(), 0)
        self.errors = []
        self.thread = get_ident()

    def _start(self, code, offset):
        self._open(code, resumed=False)

    def _resume(self, code, offset, value=None):
        try:
            if code in self.targets:
                self._open(code, resumed=True)
        finally:
            del value

    def _open(self, code, *, resumed):
        if get_ident() != self.thread:
            self.errors.append("foreign-thread boundary")
            return
        parent = self.active[-1][1] if self.active else self.parent
        marker = self.trace.start(self.targets[code], parent=parent)
        self.active.append((code, marker))
        if not resumed:
            self.counts[self.targets[code]] += 1

    def _close(self, code, offset, value):
        # The event's value is deliberately never stored or inspected.
        try:
            if code not in self.targets:
                return
            if not self.active or self.active[-1][0] is not code:
                self.errors.append("unbalanced boundary")
                return
            _, marker = self.active.pop()
            self.trace.stop(marker)
        finally:
            del value

    def __enter__(self):
        if not self.enabled:
            return self
        monitor = sys.monitoring
        self.tool = next((i for i in range(6) if monitor.get_tool(i) is None), None)
        if self.tool is None:
            raise RuntimeError("no free benchmark monitoring slot")
        monitor.use_tool_id(self.tool, "workspace-latency-benchmark")
        try:
            events = monitor.events
            for event, callback in (
                (events.PY_START, self._start),
                (events.PY_RESUME, self._resume),
                (events.PY_THROW, self._resume),
                (events.PY_RETURN, self._close),
                (events.PY_YIELD, self._close),
                (events.PY_UNWIND, self._close),
            ):
                monitor.register_callback(self.tool, event, callback)
            mask = (
                events.PY_START | events.PY_RESUME | events.PY_RETURN | events.PY_YIELD
            )
            for code in self.targets:
                monitor.set_local_events(self.tool, code, mask)
            # Exception events are global-only in CPython 3.12; callbacks
            # discard every code object outside the exact target set.
            monitor.set_events(self.tool, events.PY_THROW | events.PY_UNWIND)
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self.tool is not None:
            monitor = sys.monitoring
            try:
                monitor.set_events(self.tool, 0)
                for code in self.targets:
                    monitor.set_local_events(self.tool, code, 0)
                for event in (
                    monitor.events.PY_START, monitor.events.PY_RESUME,
                    monitor.events.PY_THROW, monitor.events.PY_RETURN,
                    monitor.events.PY_YIELD, monitor.events.PY_UNWIND,
                ):
                    monitor.register_callback(self.tool, event, None)
            finally:
                monitor.free_tool_id(self.tool)
                self.tool = None
            if self.active:
                self.errors.append("unfinished active boundary")
            while self.active:
                _, marker = self.active.pop()
                self.trace.stop(marker)
        self.trace.attach("boundary_observation", {
            "enabled": self.enabled,
            "accounting": "active segments; suspend time belongs to enclosing wall",
            "call_counts": self.counts if self.enabled else {},
            "errors": self.errors,
        })
        if exc_type is None and self.errors:
            raise RuntimeError("benchmark boundary accounting failed")
