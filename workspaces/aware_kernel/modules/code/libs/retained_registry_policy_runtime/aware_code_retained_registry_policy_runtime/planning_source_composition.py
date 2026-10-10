"""Fixed composition of original Code planning readers; no planning producer."""

import inspect
import os
from copy import deepcopy
from dataclasses import dataclass
from typing import Any
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime.contracts import (
    ContractViolation,
    SemanticPackageCoordinate,
)

from . import direct_epoch_tracking as hooks
from . import direct_host
from . import planning_dependency_source as sources
from . import planning_execution as execution


@dataclass(frozen=True)
class _Member:
    source: object
    retained: tuple
    reader: Any
    package: SemanticPackageCoordinate
    host: object
    binding: Any
    operation_identity: object

    def check(self, guard):
        if sources._SOURCES.get(self.source) is not self.retained:
            raise ContractViolation("original planning source record changed")
        origin, context, stage, body, pid = self.retained
        if stage.record.expected.operation_identity is not self.operation_identity:
            raise ContractViolation("planning source operation identity changed")
        self.reader.check()
        if pid != os.getpid():
            raise ContractViolation("planning source process changed")
        host, registration, stages = execution._origin(origin)
        if (
            execution.contexts._CONTEXTS.get(context) is not stage.record
            or host is not self.host
            or stages.get(context) is not stage
            or stage.record.registration is not registration
            or stage.result_body is not body
            or stage.status != "returned"
            or stage.record.reservation.binding is not self.binding
            or stage.record.expected.package != self.package
        ):
            raise ContractViolation("original planning source lineage changed")
        hooks._original(self.binding, self.host, guard)


@dataclass(frozen=True)
class _Composition:
    members: tuple[_Member, ...]
    pid: int

    def check(self):
        if self.pid != os.getpid():
            raise ContractViolation("planning source composition process changed")
        anchor = self.members[0].binding
        with hooks._guard(anchor) as guard:
            for member in self.members:
                member.check(guard)
                binding = member.binding
                if (
                    binding.tracker.parent is not anchor.tracker.parent
                    or binding.acquire.receiver is not anchor.acquire.receiver
                    or binding.epoch is not anchor.epoch
                    or binding.catalog is not anchor.catalog
                ):
                    raise ContractViolation(
                        "planning sources have different parent/epoch/catalog"
                    )
                binding.participant._register_epoch(
                    guard, binding.epoch, expected=binding.expected
                )


_COMPOSITIONS = WeakKeyDictionary()


class ComposedRetainedPlanningSource(direct_host._Opaque):
    def __init_subclass__(cls, **kwargs):
        raise TypeError("composed planning source is sealed")

    def read_dependencies(self, package):
        state = _state(self)
        if type(package) is not SemanticPackageCoordinate:
            raise TypeError("exact planning source package required")
        package.__post_init__()
        member = next(
            (m for m in state.members if m.package.package_ref == package.package_ref),
            None,
        )
        if member is None or package != member.package:
            raise ContractViolation("original planning source package unavailable")
        # The retained reader performs original owner/source/currentness validation.
        # No source callback runs under parent exclusion.
        result = member.reader.call(package)
        _state(self)
        return result


_READ = ComposedRetainedPlanningSource.read_dependencies


def _state(source):
    if type(source) is not ComposedRetainedPlanningSource:
        raise TypeError("exact composed planning source required")
    state = _COMPOSITIONS.get(source)
    if state is None:
        raise ContractViolation("foreign composed planning source")
    if inspect.getattr_static(source, "read_dependencies") is not _READ:
        raise ContractViolation("composed planning reader substituted")
    state.check()
    return state


def compose_retained_planning_sources(original_sources):
    """Fixed assembly accepts original readers only, never values or callbacks.

    The immutable set is not proof of graph reachability or membership completeness.
    Missing packages refuse; fixed composition must provide every needed owner source.
    """
    if type(original_sources) is not tuple or not 1 <= len(original_sources) <= 4096:
        raise ContractViolation("planning source tuple must contain 1..4096 originals")
    members = []
    refs = set()
    for source in original_sources:
        if type(source) is not sources.RetainedPlanningDependencySource:
            raise TypeError("original retained planning source required")
        retained = sources._SOURCES.get(source)
        if retained is None or retained[4] != os.getpid():
            raise ContractViolation("foreign retained planning source/process")
        origin, _context, stage, _body, _pid = retained
        host, _registration, _stages = execution._origin(origin)
        binding = stage.record.reservation.binding
        if members:
            anchor = members[0].binding
            if (
                binding.tracker.parent is not anchor.tracker.parent
                or binding.acquire.receiver is not anchor.acquire.receiver
                or binding.epoch is not anchor.epoch
                or binding.catalog is not anchor.catalog
            ):
                raise ContractViolation(
                    "planning sources have different parent/epoch/catalog"
                )
        package = deepcopy(stage.record.expected.package)
        if package.package_ref in refs:
            raise ContractViolation("duplicate planning package source")
        refs.add(package.package_ref)
        if inspect.getattr_static(source, "read_dependencies") is not sources._READ:
            raise ContractViolation("original planning reader substituted")
        members.append(
            _Member(
                source,
                retained,
                direct_host._capture(source, "read_dependencies"),
                package,
                host,
                stage.record.reservation.binding,
                stage.record.expected.operation_identity,
            )
        )
    state = _Composition(
        tuple(sorted(members, key=lambda m: m.package.package_ref)), os.getpid()
    )
    state.check()
    for member in state.members:
        member.reader.call(member.package)
    state.check()
    result = object.__new__(ComposedRetainedPlanningSource)
    _COMPOSITIONS[result] = state
    return result


def validate_composed_retained_planning_source(
    host,
    source,
    package_closure,
):
    """Check one sealed source against its original host and package closure.

    This entrance issues no token and returns no semantic meaning. The caller
    must already own the admitted package closure; Code only proves that the
    retained owner results behind ``source`` belong to this exact live host and
    cover that closure completely.
    """

    direct_host._state(host)
    state = _state(source)
    if type(package_closure) is not tuple or not 1 <= len(package_closure) <= 4096:
        raise ContractViolation(
            "planning package closure must contain 1..4096 packages"
        )
    for package in package_closure:
        if type(package) is not SemanticPackageCoordinate:
            raise TypeError("exact planning package closure required")
        package.__post_init__()
    package_refs = tuple(package.package_ref for package in package_closure)
    if package_refs != tuple(sorted(set(package_refs))):
        raise ContractViolation("planning package closure must be unique and ordered")
    if any(member.host is not host for member in state.members):
        raise ContractViolation("planning source belongs to another direct host")
    if tuple(member.package for member in state.members) != package_closure:
        raise ContractViolation("planning source package closure differs")
    # Close the validation window around all original stage and host checks.
    # Every later source read repeats the same underlying lineage validation.
    _state(source)
    direct_host._state(host)
