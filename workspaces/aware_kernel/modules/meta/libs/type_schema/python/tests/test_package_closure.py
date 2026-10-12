from __future__ import annotations

import gc
import tracemalloc
from dataclasses import dataclass
from types import FunctionType
from typing import cast

import pytest
from aware_meta_type_schema.composition import (
    ComposedPackageEvidence,
    TypeSchemaCompositionError,
    _package_closure,
)


@dataclass(frozen=True, slots=True)
class _PackageStub:
    dependency_package_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _EvidenceStub:
    package: _PackageStub


class _ObservedPackages:
    def __init__(self, values: dict[str, _EvidenceStub]) -> None:
        self._values = values
        self.lookups: list[str] = []

    def get(self, key: str) -> _EvidenceStub | None:
        self.lookups.append(key)
        return self._values.get(key)


def _packages(
    dependencies: dict[str, tuple[str, ...]],
) -> dict[str, ComposedPackageEvidence]:
    values = {
        package_ref: _EvidenceStub(_PackageStub(dependency_refs))
        for package_ref, dependency_refs in dependencies.items()
    }
    return cast(dict[str, ComposedPackageEvidence], values)


def _recursive_oracle(
    packages: dict[str, ComposedPackageEvidence], target_package_ref: str
) -> set[str]:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(package_ref: str) -> None:
        if package_ref in visiting:
            raise TypeSchemaCompositionError("slice package dependency cycle")
        if package_ref in visited:
            return
        evidence = packages.get(package_ref)
        if evidence is None:
            raise TypeSchemaCompositionError(
                f"slice package dependency is missing: {package_ref!r}"
            )
        visiting.add(package_ref)
        for dependency_ref in evidence.package.dependency_package_refs:
            visit(dependency_ref)
        visiting.remove(package_ref)
        visited.add(package_ref)

    visit(target_package_ref)
    return visited


def test_iterative_package_closure_matches_recursive_depth_first_semantics() -> None:
    graph = {
        "package:app": ("package:alpha", "package:beta"),
        "package:alpha": ("package:shared",),
        "package:beta": ("package:leaf", "package:shared"),
        "package:shared": ("package:leaf",),
        "package:leaf": (),
    }
    oracle_values = _packages(graph)
    iterative_values = _ObservedPackages(
        cast(dict[str, _EvidenceStub], _packages(graph))
    )
    oracle_observed = _ObservedPackages(
        cast(dict[str, _EvidenceStub], oracle_values)
    )

    expected = _recursive_oracle(
        cast(dict[str, ComposedPackageEvidence], oracle_observed), "package:app"
    )
    actual = _package_closure(
        cast(dict[str, ComposedPackageEvidence], iterative_values), "package:app"
    )

    assert actual == expected == set(graph)
    assert iterative_values.lookups == oracle_observed.lookups


@pytest.mark.parametrize(
    ("graph", "expected_message"),
    (
        (
            {
                "package:app": ("package:first", "package:second"),
                "package:first": ("package:missing-first",),
                "package:second": ("package:missing-second",),
            },
            "slice package dependency is missing: 'package:missing-first'",
        ),
        (
            {
                "package:app": ("package:first", "package:second"),
                "package:first": ("package:app",),
                "package:second": (),
            },
            "slice package dependency cycle",
        ),
    ),
)
def test_iterative_package_closure_preserves_recursive_error_precedence(
    graph: dict[str, tuple[str, ...]], expected_message: str
) -> None:
    values = _packages(graph)

    with pytest.raises(TypeSchemaCompositionError) as oracle_error:
        _recursive_oracle(values, "package:app")
    with pytest.raises(TypeSchemaCompositionError) as iterative_error:
        _package_closure(values, "package:app")

    assert str(iterative_error.value) == str(oracle_error.value) == expected_message


def test_iterative_package_closure_handles_deep_and_wide_graphs_with_bounded_memory() -> None:
    depth = 4096
    width = 4096
    deep = {
        f"package:deep-{index}": (
            (f"package:deep-{index + 1}",) if index + 1 < depth else ()
        )
        for index in range(depth)
    }
    wide = {
        "package:wide-root": tuple(f"package:wide-{index}" for index in range(width)),
        **{f"package:wide-{index}": () for index in range(width)},
    }

    tracemalloc.start()
    try:
        deep_result = _package_closure(_packages(deep), "package:deep-0")
        _, deep_peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.reset_peak()
        wide_result = _package_closure(_packages(wide), "package:wide-root")
        _, wide_peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert len(deep_result) == depth
    assert len(wide_result) == width + 1
    assert deep_peak_bytes < 4_000_000
    assert wide_peak_bytes < 4_000_000
    print(
        "package_closure_allocation "
        f"deep_nodes={depth} deep_peak_bytes={deep_peak_bytes} "
        f"wide_nodes={width + 1} wide_peak_bytes={wide_peak_bytes}"
    )


def test_iterative_package_closure_retains_no_recursive_function_cycles() -> None:
    values = _packages(
        {
            "package:app": ("package:dependency",),
            "package:dependency": (),
        }
    )
    gc.collect()
    was_enabled = gc.isenabled()
    gc.disable()
    try:
        before = _recursive_visit_function_count()
        for _ in range(256):
            assert _package_closure(values, "package:app") == {
                "package:app",
                "package:dependency",
            }
        after = _recursive_visit_function_count()
    finally:
        if was_enabled:
            gc.enable()

    assert after == before
    print(
        "package_closure_gc "
        f"iterations=256 retained_recursive_functions_before={before} "
        f"retained_recursive_functions_after={after}"
    )


def _recursive_visit_function_count() -> int:
    return sum(
        1
        for value in gc.get_objects()
        if isinstance(value, FunctionType)
        and value.__qualname__.endswith("_package_closure.<locals>.visit")
    )
