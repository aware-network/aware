"""Benchmark-only wall accounting; never admission or runtime authority."""

import json
import sys
import time
from pathlib import Path
from threading import get_ident


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
    def __init__(self, *, enabled=True, clock=time.perf_counter_ns):
        self.enabled = enabled
        self._clock = clock
        self._started = clock() if enabled else None
        self._ended = None
        self._spans = []
        self._metadata = {}

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
        return marker

    def stop(self, marker):
        if not self.enabled:
            return
        if type(marker) is not int or not 0 <= marker < len(self._spans):
            raise ValueError("diagnostic marker unavailable")
        span = self._spans[marker]
        if self._ended is not None or span["end_ns"] is not None:
            raise ValueError("diagnostic stage already ended")
        if any(s["parent_id"] == marker and s["end_ns"] is None for s in self._spans):
            raise ValueError("diagnostic child remains open")
        span["end_ns"] = self._clock()
        span["status"] = "completed"

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
        spans = []
        for original in self._spans:
            span = dict(original)
            if span["end_ns"] is None:
                span["end_ns"] = self._ended
                span["status"] = "incomplete"
            spans.append(span)
        for span in spans:
            if not self._started <= span["start_ns"] <= span["end_ns"] <= self._ended:
                raise ValueError("diagnostic interval outside root")
            children = [s for s in spans if s["parent_id"] == span["span_id"]]
            if any(
                not span["start_ns"] <= s["start_ns"] <= s["end_ns"] <= span["end_ns"]
                for s in children
            ):
                raise ValueError("diagnostic child outside parent")
            span["elapsed_ns"] = span["end_ns"] - span["start_ns"]
            span["exclusive_ns"] = span["elapsed_ns"] - _covered(
                [(s["start_ns"], s["end_ns"]) for s in children]
            )
        top = [s for s in spans if s["parent_id"] is None]
        covered = _covered([(s["start_ns"], s["end_ns"]) for s in top])
        elapsed = self._ended - self._started
        return {
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
        if code in self.targets:
            self._open(code, resumed=True)

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
        if code not in self.targets:
            return
        if not self.active or self.active[-1][0] is not code:
            self.errors.append("unbalanced boundary")
            return
        _, marker = self.active.pop()
        self.trace.stop(marker)

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
