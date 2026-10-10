"""Existing Code dependency-source interface over an original selected return.

Portable planning is not membership or resolved-product authority. This source
never accepts a caller-supplied result or a reconstructed execution completion.
"""

import inspect
import os
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime.contracts import (
    ContractViolation,
    SemanticPackageCoordinate,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    DependencyPlanningInputCodec,
)

from . import direct_epoch_tracking as hooks
from . import direct_host
from . import planning_execution as execution
from .operation_context import SourcePlanningOperationContext

_SOURCES = WeakKeyDictionary()


class RetainedPlanningDependencySource(direct_host._Opaque):
    def __init_subclass__(cls, **kwargs):
        raise TypeError("retained dependency source is sealed")

    def read_dependencies(self, package):
        if type(package) is not SemanticPackageCoordinate:
            raise TypeError("exact dependency package required")
        if inspect.getattr_static(self, "read_dependencies") is not _READ:
            raise ContractViolation("original dependency source reader substituted")
        retained = _SOURCES.get(self)
        if retained is None or retained[4] != os.getpid():
            raise ContractViolation("foreign dependency source/process")
        origin, context, stage, original_body, _pid = retained
        host, registration, stages = execution._origin(origin)
        if stages.get(context) is not stage or stage.result_body is not original_body:
            raise ContractViolation("original planning result substituted")
        execution._check_stage(host, registration, stages, stage, status="returned")
        from .planning_completion import (
            _original_retention,
            _validate_retained_completion,
        )

        _validate_retained_completion(stage)
        body = execution._planning_body(stage.record, stage.result)
        if body != original_body:
            raise ContractViolation("retained planning result changed")
        value = DependencyPlanningInputCodec().decode(original_body.canonical_body)
        if package != value.package:
            raise ContractViolation("dependency source package differs")
        binding = stage.record.reservation.binding
        with hooks._guard(binding) as guard:
            hooks._original(binding, host, guard)
            retained = _original_retention(stage)
            if retained is not None and not stage.record.expected.runtime.owns_completion(retained[1]):
                raise ContractViolation("planning completion revoked during dependency read")
            if (
                stages.get(context) is not stage
                or stage.status != "returned"
                or stage.result_body is not original_body
                or stage.result != value
                or inspect.getattr_static(self, "read_dependencies") is not _READ
            ):
                raise ContractViolation("planning source changed during read")
        return value


_READ = RetainedPlanningDependencySource.read_dependencies


def retained_planning_dependency_source(origin, context):
    """Select only an original returned stage; no result/body argument exists."""
    if type(context) is not SourcePlanningOperationContext:
        raise TypeError("exact planning context required")
    host, registration, stages = execution._origin(origin)
    stage = stages.get(context)
    if stage is None or stage.result_body is None:
        raise ContractViolation("original returned planning result unavailable")
    execution._check_stage(host, registration, stages, stage, status="returned")
    source = object.__new__(RetainedPlanningDependencySource)
    _SOURCES[source] = (origin, context, stage, stage.result_body, os.getpid())
    try:
        source.read_dependencies(stage.record.expected.package)
    except BaseException:
        _SOURCES.pop(source, None)
        raise
    return source
