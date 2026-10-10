"""Workspace planning issuer mechanism, bound by original fixed application assembly.

The private assembly/binding methods are privileged mechanisms, not authentication
of their callers. Assembly must obtain Code's original host-bound validator through
its owning entrance. A matching Protocol or successful callback is insufficient.
"""

from __future__ import annotations

import copy
import inspect
import os
from contextlib import contextmanager
from typing import Any

from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticPackageCoordinate,
)
from aware_code_semantic_contract_runtime.dependency_admission_interfaces import (
    RetainedDependencyResolutionExpectation,
)
from aware_code_semantic_contract_runtime.retained_admission_interfaces import (
    RetainedSemanticAdmissionExpectation,
)
from aware_code_semantic_contract_runtime.target_context_interfaces import (
    RetainedTargetExpectation,
)

from .observed_semantic_issuers import (
    WorkspaceDeclarationInventoryAdmission,
    WorkspacePackageContextAdmission,
    _Record,
    _snapshot,
    _unavailable,
    _WorkspaceSemanticIssuerCore,
)


class WorkspaceSourcePlanningSemanticIssuerRuntime(_WorkspaceSemanticIssuerCore):
    """Separate non-fixture issuer; original Code validation on issuance and use."""

    _validator: Any
    _validator_method: Any
    _validator_descriptor: object
    _authority_validator_binding: Any
    _contexts: dict[object, object]
    _dependency_fulfillment: Any
    _dependency_resolution: Any
    _dependency_validator: Any
    _dependency_validator_method: Any
    _dependency_validator_descriptor: object

    @classmethod
    def _assemble(cls, *, observation_runtime, membership_runtime, observation):
        issuer = cls._initialize(
            observation_runtime=observation_runtime,
            membership_runtime=membership_runtime,
            observation=observation,
        )
        issuer._authority_validator_binding = None
        issuer._validator = None
        issuer._validator_method = None
        issuer._validator_descriptor = None
        issuer._contexts = {}
        issuer._dependency_validator = None
        issuer._dependency_validator_method = None
        issuer._dependency_validator_descriptor = None
        issuer._dependency_resolution = None
        issuer._dependency_fulfillment = None
        return issuer

    def _bind_original_code_validator(self, validator) -> None:
        """One-time original assembly handoff, after Code host creation.

        The issuer instance exists before complete Code resource binding. This
        installs no replacement resource and permits no issuance before binding.
        It does not discover or establish the validator's bootstrap provenance.
        """
        with self._lock:
            if self._closed or self._pid != os.getpid() or self._validator is not None:
                _unavailable("planning_validator_binding_unavailable")
            name = "validate_retained_semantic_operation_context"
            descriptor = inspect.getattr_static(validator, name)
            method = getattr(validator, name)
            if (
                not inspect.ismethod(method)
                or method.__self__ is not validator
                or method.__func__ is not descriptor
            ):
                _unavailable("original_code_validator_required")
            self._validator = validator
            self._validator_method = method
            self._validator_descriptor = descriptor

    def _bind_original_authority_validator(self, validator) -> None:
        """Privileged fixed-assembly handoff; never authenticates the caller.

        Retain Code's original authority_context_validator(host) separately from
        the planning validator. Structural method checks do not grant provenance.
        """
        with self._lock:
            if (
                self._closed
                or self._pid != os.getpid()
                or self._validator is None
                or self._authority_validator_binding is not None
            ):
                _unavailable("authority_validator_binding_unavailable")
            name = "validate_retained_semantic_operation_context"
            descriptor = inspect.getattr_static(validator, name)
            method = getattr(validator, name)
            if (
                validator is self._validator
                or not inspect.ismethod(method)
                or method.__self__ is not validator
                or method.__func__ is not descriptor
            ):
                _unavailable("original_authority_validator_required")
            self._authority_validator_binding = (validator, method, descriptor)

    def _validate_code(self, context, expected):
        if self._closed or self._pid != os.getpid() or self._validator is None:
            _unavailable("planning_validator_unavailable")
        if type(expected) is not RetainedSemanticAdmissionExpectation:
            _unavailable("semantic_context_required")
        if expected.stage == "source_planning":
            validator, method, descriptor = (
                self._validator,
                self._validator_method,
                self._validator_descriptor,
            )
        elif expected.stage == "authority_derivation":
            if self._authority_validator_binding is None:
                _unavailable("authority_validator_unavailable")
            validator, method, descriptor = self._authority_validator_binding
        else:
            _unavailable("semantic_stage_unavailable")
        name = "validate_retained_semantic_operation_context"
        if inspect.getattr_static(validator, name) is not descriptor:
            _unavailable("planning_validator_substituted")
        result = method(context, expected=expected)
        if result is not None:
            _unavailable("planning_validator_result_invalid")
        if self._closed or self._pid != os.getpid():
            _unavailable("planning_validator_unavailable")
        if inspect.getattr_static(validator, name) is not descriptor:
            _unavailable("planning_validator_substituted")

    @contextmanager
    def _source_validation_window(self):
        """Coalesce one synchronous owner entrance into one currentness pair.

        A fresh complete validation brackets every outer entrance. Nested
        issuer mechanics perform nominal identity checks only; the window never
        crosses an await or escapes as a reusable admission.
        """

        if self._source_validation_depth:
            self._source_validation_depth += 1
            try:
                yield
            finally:
                self._source_validation_depth -= 1
            return
        closure = self._qualified_closure()
        if closure is None:
            self._observation_runtime.revalidate(self._observation)
        self._source_validation_depth = 1
        try:
            yield
        finally:
            self._source_validation_depth = 0
            closure = self._qualified_closure()
            if closure is None:
                self._observation_runtime.revalidate(self._observation)

    def issue_source_planning_pair(self, membership, *, context, expected):
        """Consume nominal Code context; an expectation alone cannot issue handles."""
        if (
            type(expected) is not RetainedSemanticAdmissionExpectation
            or expected.stage != "source_planning"
        ):
            _unavailable("source_planning_context_required")
        return self._issue_stage_pair(membership, context=context, expected=expected)

    def inspect_workspace_ref(self, membership) -> str:
        """Return the authenticated qualified handle for catalog identity.

        V2 local scope has no separate portable handle and retains its admitted
        manifest path. V3 qualified scope uses the original declared handle.
        """
        with self._lock, self._source_validation_window():
            self._check(membership)
            evidence = self._evidence(membership)
            closure = self._qualified_closure()
            if closure is None:
                return evidence.workspace_manifest_path
            matches = tuple(
                scope.workspace_handle
                for scope in closure.scopes
                if scope.scope_key == evidence.workspace_manifest_path
            )
            if len(matches) != 1:
                _unavailable("qualified_workspace_identity_unavailable")
            self._qualified_member(membership, closure)
            return matches[0]

    def issue_authority_pair(self, membership, *, context, expected):
        """Fresh handles validated by the separately retained original validator."""
        if (
            type(expected) is not RetainedSemanticAdmissionExpectation
            or expected.stage != "authority_derivation"
        ):
            _unavailable("authority_context_required")
        return self._issue_stage_pair(membership, context=context, expected=expected)

    def _issue_stage_pair(self, membership, *, context, expected):
        with self._lock, self._source_validation_window():
            self._validate_code(context, expected)
            if len(self._records) >= 128:
                _unavailable("issuer_admission_capacity")
            original = _snapshot(expected)
            if any(
                operation is original.operation_identity and stage == original.stage
                for operation, stage in self._issued
            ):
                _unavailable("planning_issuance_replay")
            source, inventory, targets = self._derive(membership)
            self._match_inputs(source, inventory, original)
            self._check(membership)
            self._validate_code(context, original)
            record = _Record(source, inventory, targets, original)
            package = object.__new__(WorkspacePackageContextAdmission)
            declarations = object.__new__(WorkspaceDeclarationInventoryAdmission)
            self._records[package] = self._records[declarations] = record
            self._contexts[package] = self._contexts[declarations] = context
            self._issued.append((original.operation_identity, original.stage))
            return package, declarations

    def _validate(self, admission, expected, kind):
        if admission not in self._contexts:
            _unavailable("foreign_or_reconstructed_admission")
        context = self._contexts[admission]
        try:
            with self._source_validation_window():
                self._validate_code(context, expected)
                record = super()._validate(admission, expected, kind)
                self._validate_code(context, expected)
                return record
        except BaseException:
            # Retire both handles sharing the failed original Code operation.
            for handle, original in tuple(self._contexts.items()):
                if original is context:
                    self._contexts.pop(handle, None)
                    self._records.pop(handle, None)
            raise

    def inspect_inputs(self, membership):
        with self._lock, self._source_validation_window():
            return super().inspect_inputs(membership)

    def _bind_original_dependency_validator(self, validator) -> None:
        """Privileged fixed-assembly handoff; never authenticates its own caller."""
        with self._lock:
            if (
                self._closed
                or self._pid != os.getpid()
                or self._dependency_validator is not None
                or self._validator is None
            ):
                _unavailable("dependency_validator_binding_unavailable")
            name = "validate_retained_dependency_operation"
            descriptor = inspect.getattr_static(validator, name)
            method = getattr(validator, name)
            if (
                not inspect.ismethod(method)
                or method.__self__ is not validator
                or method.__func__ is not descriptor
            ):
                _unavailable("original_dependency_validator_required")
            self._dependency_validator = validator
            self._dependency_validator_method = method
            self._dependency_validator_descriptor = descriptor

    def _validate_dependency_inventory(
        self, operation, inventory_admission, *, expected
    ):
        """Check original demand and inventory; does not admit target resolution."""
        with self._lock:
            if (
                self._closed
                or self._pid != os.getpid()
                or self._dependency_validator is None
            ):
                _unavailable("dependency_validator_unavailable")
            if type(expected) is not RetainedDependencyResolutionExpectation:
                _unavailable("exact_dependency_expectation_required")
            if expected.demand_operation_identity is not operation:
                _unavailable("dependency_operation_identity_differs")
            name = "validate_retained_dependency_operation"

            def validate_original():
                if (
                    inspect.getattr_static(self._dependency_validator, name)
                    is not self._dependency_validator_descriptor
                ):
                    _unavailable("dependency_validator_substituted")
                result = self._dependency_validator_method(operation, expected=expected)
                if result is not None:
                    _unavailable("dependency_validator_result_invalid")
                if (
                    inspect.getattr_static(self._dependency_validator, name)
                    is not self._dependency_validator_descriptor
                ):
                    _unavailable("dependency_validator_substituted")
                if self._closed or self._pid != os.getpid():
                    _unavailable("dependency_validator_unavailable")

            validate_original()
            record = self._validate(
                inventory_admission,
                expected.source_planning,
                WorkspaceDeclarationInventoryAdmission,
            )
            validate_original()
            # Validation itself may run owner code. Require the original live
            # inventory still present after the last external entrance returns.
            if (
                self._validate(
                    inventory_admission,
                    expected.source_planning,
                    WorkspaceDeclarationInventoryAdmission,
                )
                is not record
            ):
                _unavailable("original_inventory_changed")
            return record

    def _target_record(self, inventory_admission, expected):
        if type(expected) is not RetainedTargetExpectation:
            _unavailable("exact_target_expectation_required")
        if (
            type(expected.target_package) is not SemanticPackageCoordinate
            or type(expected.target_source_identity_digest) is not ContentDigest
        ):
            _unavailable("exact_target_coordinates_required")
        frozen = RetainedTargetExpectation(
            _snapshot(expected.source_planning),
            copy.deepcopy(expected.target_source_identity_digest),
            copy.deepcopy(expected.target_package),
        )
        frozen.target_package.__post_init__()
        frozen.target_source_identity_digest.to_wire()
        record = self._validate(
            inventory_admission,
            frozen.source_planning,
            WorkspaceDeclarationInventoryAdmission,
        )
        targets = {
            id(target.membership): target
            for target in record.targets
            if target.context.package == frozen.target_package
            and target.context.source_identity_digest
            == frozen.target_source_identity_digest
        }
        if len(targets) != 1:
            _unavailable("target_not_in_original_inventory")
        target = next(iter(targets.values()))
        current = self._source(target.membership)
        if current != target:
            _unavailable("original_target_source_changed")
        if (
            self._validate(
                inventory_admission,
                frozen.source_planning,
                WorkspaceDeclarationInventoryAdmission,
            )
            is not record
        ):
            _unavailable("original_inventory_changed")
        self._check(target.membership)
        return target

    def select_dependency_target_admission(self, *, inventory_admission, expected):
        """Return an already retained target membership; do not issue new authority."""
        with self._lock:
            return self._target_record(inventory_admission, expected).membership

    def validate_dependency_target_admission(
        self, admission, *, inventory_admission, expected: RetainedTargetExpectation
    ) -> None:
        with self._lock:
            target = self._target_record(inventory_admission, expected)
            if admission is not target.membership:
                _unavailable("foreign_dependency_target_admission")

    def _bind_original_resolution_resources(self, *, target_origin, catalog):
        """Fixed assembly supplies the original Code host resources; no caller trust."""
        from .dependency_fulfillment import _WorkspaceEmptyDependencyFulfillmentRuntime
        from .dependency_resolution import _WorkspaceDependencyResolutionRuntime

        with self._lock:
            if (
                self._closed
                or self._pid != os.getpid()
                or self._dependency_validator is None
                or self._dependency_resolution is not None
            ):
                _unavailable("dependency_resolution_binding_unavailable")
            self._dependency_resolution = _WorkspaceDependencyResolutionRuntime(
                self, target_origin, catalog
            )
            self._dependency_fulfillment = _WorkspaceEmptyDependencyFulfillmentRuntime(
                self._dependency_resolution
            )

    def issue_dependency_resolution(self, operation, *, inventory_admission, expected):
        with self._lock:
            if (
                self._dependency_resolution is None
                or self._closed
                or self._pid != os.getpid()
            ):
                _unavailable("dependency_resolution_unavailable")
            return self._dependency_resolution.issue(
                operation, inventory_admission, expected
            )

    def validate_dependency_resolution_admission(self, admission, *, expected):
        with self._lock:
            if (
                self._dependency_resolution is None
                or self._closed
                or self._pid != os.getpid()
            ):
                _unavailable("dependency_resolution_unavailable")
            self._dependency_resolution.validate(admission, expected)

    def issue_empty_dependency_fulfillment(self, resolution_admission, *, expected):
        with self._lock:
            if (
                self._dependency_fulfillment is None
                or self._closed
                or self._pid != os.getpid()
            ):
                _unavailable("dependency_fulfillment_unavailable")
            return self._dependency_fulfillment.issue(resolution_admission, expected)

    def read_dependency_products(self, admission, *, resolution_admission, expected):
        with self._lock:
            if (
                self._dependency_fulfillment is None
                or self._closed
                or self._pid != os.getpid()
            ):
                _unavailable("dependency_fulfillment_unavailable")
            return self._dependency_fulfillment.read(
                admission, resolution_admission, expected
            )

    def issue_empty_dependency_products(
        self, operation, *, inventory_admission, expected
    ):
        """Resolve and read empty products in Code's original demand session.

        This is the fixed synchronous Workspace caller. Code derives the host,
        source context and validators from ``operation``; Workspace retains its
        original issuer lock and owns every resolution/fulfillment admission.
        No session token or validation result escapes this call.
        """

        from aware_code_retained_registry_policy_runtime.retained_demand_operation import (
            dependency_resolution_validation_session,
        )

        with self._lock, dependency_resolution_validation_session(operation):
            resolution = self.issue_dependency_resolution(
                operation,
                inventory_admission=inventory_admission,
                expected=expected,
            )
            fulfillment = self.issue_empty_dependency_fulfillment(
                resolution, expected=expected
            )
            body = self.read_dependency_products(
                fulfillment,
                resolution_admission=resolution,
                expected=expected,
            )
            return resolution, fulfillment, body

    def validate_dependency_fulfillment_admission(
        self, admission, *, resolution_admission, expected
    ):
        with self._lock:
            if (
                self._dependency_fulfillment is None
                or self._closed
                or self._pid != os.getpid()
            ):
                _unavailable("dependency_fulfillment_unavailable")
            self._dependency_fulfillment.validate(
                admission, resolution_admission, expected
            )

    def close(self) -> None:
        with self._lock:
            if self._dependency_fulfillment is not None:
                self._dependency_fulfillment.close()
            if self._dependency_resolution is not None:
                self._dependency_resolution.close()
            self._contexts.clear()
            super().close()
