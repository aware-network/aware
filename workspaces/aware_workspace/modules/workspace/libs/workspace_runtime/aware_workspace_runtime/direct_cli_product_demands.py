"""Keep Code's first product-demand invocations on the original command.

This is local reference custody, not a demand producer or admission issuer.
Only Code's original operations can supply the demand evidence used below.
"""

from __future__ import annotations

import os
from threading import get_ident

from aware_code_retained_registry_policy_runtime import (
    retained_demand_operation as owner,
)
from aware_code_retained_registry_policy_runtime.product_planning_source import (
    RetainedProductPlanningDependencySource,
)
from aware_code_semantic_contract_runtime import (
    CodeSemanticPackagePlanningContext,
    ContractViolation,
    SemanticPackageCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticDependencyPlanningInput,
)
from aware_code_semantic_contract_runtime.materialization_catalog_codec import (
    encode_code_semantic_package_planning_context,
)

_EXECUTE = owner.execute_retained_dependency_demand
_EXECUTE_CODE = _EXECUTE.__code__
_READ = owner.RetainedDependencyDemandOperation.read_demand
_READ_CODE = _READ.__code__


def _check_entrances():
    if (owner.execute_retained_dependency_demand is not _EXECUTE
        or _EXECUTE.__code__ is not _EXECUTE_CODE
        or owner.RetainedDependencyDemandOperation.read_demand is not _READ
        or _READ.__code__ is not _READ_CODE):
        raise ContractViolation("original graph demand entrance changed")


class DirectCLIProductDemands:
    """Bounded retained originals; no portable value can replace an operation."""

    def __init__(self, sources):
        if type(sources) is not tuple or not 1 <= len(sources) <= 256:
            raise TypeError("original product source rows required")
        if any(type(row) is not tuple or len(row) != 2 or type(row[0]) is not SemanticPackageCoordinate
            or type(row[1]) is not RetainedProductPlanningDependencySource for row in sources):
            raise TypeError("exact original product source rows required")
        self._sources = sources
        self._rows = {}
        self._pid, self._thread = os.getpid(), get_ident()
        self._terminal = False

    def __init_subclass__(cls, **kwargs):
        raise TypeError("original graph demand custody is sealed")

    def check(self):
        _check_entrances()
        if self._terminal or self._pid != os.getpid() or self._thread != get_ident():
            raise ContractViolation("original graph demands are terminal or foreign")

    async def plan(self, context, planning_input):
        self.check()
        if type(context) is not CodeSemanticPackagePlanningContext or type(planning_input) is not SemanticDependencyPlanningInput:
            raise TypeError("exact original planning context and input required")
        key = context.package.package_ref
        try:
            if key in self._rows:
                raise ContractViolation("original graph demand context already dispatched")
            matches = tuple(source for package, source in self._sources if package == context.package)
            if len(matches) != 1:
                raise ContractViolation("original graph planning source unavailable")
            source, = matches
            if planning_input.package != context.package:
                raise ContractViolation("original graph planning input differs")
            context_wire = encode_code_semantic_package_planning_context(context)
            operation = await _EXECUTE(source, context=context)
            self.check()
            demand = _READ(operation)
            self.check()
            if encode_code_semantic_package_planning_context(context) != context_wire:
                raise ContractViolation("original graph demand context changed")
            self._rows[key] = (operation, context_wire, canonical_json_bytes(demand.to_wire()))
            return demand
        except BaseException:
            self.close()
            raise

    def operation(self, binding):
        self.check()
        try:
            row = self._rows.get(binding.package.package_ref)
            if row is None:
                raise ContractViolation("original graph demand operation unavailable")
            operation, context_wire, demand_wire = row
            if (encode_code_semantic_package_planning_context(binding.planning_context) != context_wire
                or canonical_json_bytes(binding.dependency_demand_set.to_wire()) != demand_wire):
                raise ContractViolation("original graph binding differs from demand invocation")
            value = _READ(operation)
            self.check()
            if canonical_json_bytes(value.to_wire()) != demand_wire:
                raise ContractViolation("original graph demand changed")
            return operation
        except BaseException:
            self.close()
            raise

    def close(self):
        self._terminal = True
        self._sources = ()
        self._rows.clear()
