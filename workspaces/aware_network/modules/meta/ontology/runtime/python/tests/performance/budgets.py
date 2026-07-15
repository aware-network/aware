from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from time import perf_counter
from typing import Protocol


class TimedStep(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def duration_s(self) -> float: ...


@dataclass(frozen=True, slots=True)
class BudgetTimer:
    label: str
    max_duration_s: float
    started_at: float

    @classmethod
    def start(cls, *, label: str, max_duration_s: float) -> BudgetTimer:
        return cls(
            label=label,
            max_duration_s=max_duration_s,
            started_at=perf_counter(),
        )

    def assert_within_budget(self) -> float:
        elapsed_s = round(perf_counter() - self.started_at, 6)
        assert elapsed_s <= self.max_duration_s, (
            f"{self.label} exceeded budget: "
            f"actual={elapsed_s:.6f}s max={self.max_duration_s:.6f}s"
        )
        return elapsed_s


def assert_metric_lte(
    *,
    label: str,
    actual: int | float,
    maximum: int | float,
) -> None:
    assert actual <= maximum, f"{label} exceeded budget: actual={actual} max={maximum}"


def assert_metric_gte(
    *,
    label: str,
    actual: int | float,
    minimum: int | float,
) -> None:
    assert actual >= minimum, f"{label} below budget: actual={actual} min={minimum}"


def metric_int(payload: Mapping[str, object], key: str) -> int:
    value = payload.get(key)
    assert isinstance(value, int), f"Expected integer metric {key!r}, got {value!r}"
    return value


def count_steps_with_name(
    steps: Iterable[TimedStep],
    name_fragment: str,
) -> int:
    return sum(1 for step in steps if name_fragment in step.name)


def sum_steps_with_name(
    steps: Iterable[TimedStep],
    name_fragment: str,
) -> float:
    return round(
        sum(step.duration_s for step in steps if name_fragment in step.name),
        6,
    )


__all__ = [
    "BudgetTimer",
    "assert_metric_gte",
    "assert_metric_lte",
    "count_steps_with_name",
    "metric_int",
    "sum_steps_with_name",
]
