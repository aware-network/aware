from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import time


@dataclass(frozen=True, slots=True)
class RuntimeDerivationStep:
    name: str
    duration_s: float


class RuntimeDerivationTimer:
    def __init__(self) -> None:
        self._steps: list[RuntimeDerivationStep] = []
        self._metrics: dict[str, object] = {}

    @contextmanager
    def step(self, name: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            self.add(name, time.perf_counter() - start)

    def add(self, name: str, duration_s: float) -> None:
        self._steps.append(
            RuntimeDerivationStep(name=name, duration_s=round(duration_s, 3))
        )

    def metric(self, key: str, value: object) -> None:
        if key:
            self._metrics[key] = value

    def steps(self) -> tuple[RuntimeDerivationStep, ...]:
        return tuple(self._steps)

    def metrics(self) -> dict[str, object]:
        return dict(self._metrics)


__all__ = ["RuntimeDerivationStep", "RuntimeDerivationTimer"]
