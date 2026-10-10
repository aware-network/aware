"""Internal original-source consumer; fixed composition authenticates its capture.

No Workspace import or issuer lives here. Capturing methods is not bootstrap
qualification. Callers are fixed Code entrances with an explicit running use.
"""

from contextlib import contextmanager
from dataclasses import dataclass

from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.dependency_scope_closure_v2 import (
    CodeRetainedDependencyScopeClosureV2,
)
from aware_code_semantic_contract_runtime.dependency_scope_interfaces import (
    RetainedDependencyScopeExpectation,
)

from . import dependency_scope_operation as operations
from .direct_epoch_tracking import _guard
from .direct_host import _capture


@dataclass(frozen=True)
class _RetainedDependencySource:
    validator: operations.OriginalDependencyScopeOperationValidator
    validator_state: object
    source: object
    runtime: object
    entrances: tuple

    def check(self):
        state, _ = operations._state(self.validator)
        if state is not self.validator_state:
            raise ContractViolation("original source host changed")
        resources = {role: value for role, value, _ in state.host_state.resources}
        if resources["scope_runtime"] is not self.runtime:
            raise ContractViolation("original dependency runtime changed")
        for method in self.entrances:
            if method.method.__func__ is not method.descriptor:
                raise ContractViolation("original source method descriptor differs")
            method.check()
        return state


def _capture_dependency_source(validator, source):
    """Fixed assembly only, with its original source; never a public registration."""
    state, _ = operations._state(validator)
    if source is None:
        raise ContractViolation("original dependency source required")
    resources = {role: value for role, value, _ in state.host_state.resources}
    runtime = resources["scope_runtime"]
    methods = tuple(
        _capture(runtime, name)
        for name in (
            "prepare_dependency_scope_expectation",
            "bind_dependency_scope_operation",
            "release_dependency_scope_operation",
            "read_dependency_scope_closure",
            "validate_dependency_scope_closure",
            "check_dependency_scope_closure_locked",
        )
    )
    if state.host_state.qualified:
        methods = (*methods[:3], state.host_state.methods["read"], *methods[4:])
    result = _RetainedDependencySource(validator, state, source, runtime, methods)
    result.check()
    return result


@dataclass(frozen=True)
class _BoundDependencySource:
    retained: _RetainedDependencySource
    expected: RetainedDependencyScopeExpectation

    def check(self):
        self.retained.check()
        self.retained.validator.validate_dependency_scope_operation(
            self.expected.operation_identity, expected=self.expected
        )

    def validate(self, *, closure_digest=None):
        self.check()
        result = self.retained.entrances[4].call(
            self.retained.source, expected=self.expected, closure_digest=closure_digest
        )
        if result is not None:
            raise ContractViolation("source validator returned non-None")
        self.check()

    def read(self, *, closure_digest=None):
        self.validate(closure_digest=closure_digest)
        result = self.retained.entrances[3].call(
            self.retained.source, expected=self.expected
        )
        if type(result) is not CodeRetainedDependencyScopeClosureV2:
            raise ContractViolation("exact v2 dependency closure required")
        result.__post_init__()
        if closure_digest is not None and result.closure_digest != closure_digest:
            raise ContractViolation("original dependency closure digest changed")
        self.validate(closure_digest=result.closure_digest)
        return result

    def check_locked(self, *, closure_digest, guard):
        # Code checks original use separately; owner locked method must neither
        # call Code nor acquire exclusion again. No full reader runs here.
        self.retained.check()
        self.retained.validator.validate_dependency_scope_operation(
            self.expected.operation_identity, expected=self.expected
        )
        result = self.retained.entrances[5].call(
            self.retained.source,
            expected=self.expected,
            closure_digest=closure_digest,
            guard=guard,
        )
        if result is not None:
            raise ContractViolation("locked source validator returned non-None")
        self.retained.check()


@contextmanager
def _bind_dependency_source(retained, operation, *, purpose):
    """Prepare -> Code retain -> owner bind; release before caller finishes use.

    Purpose is fixed by the internal calling entrance, not an owner proposal.
    Failed retirement leaves the existing operation uncertain and blocks cutover.
    """
    if type(retained) is not _RetainedDependencySource:
        raise TypeError("exact retained source consumer required")
    state = retained.check()
    expected = retained.entrances[0].call(
        retained.source,
        parent_identity=state.binding.tracker.parent,
        epoch_identity=state.binding.epoch,
        operation_identity=operation,
        process_id=state.host_state.pid,
    )
    if (
        type(expected) is not RetainedDependencyScopeExpectation
        or expected.closure_runtime_identity is not retained.runtime
    ):
        raise ContractViolation("original prepared source context differs")
    retained.check()
    operations._retain_dependency_scope_operation(
        retained.validator, operation, expected=expected, purpose=purpose
    )
    failures = []
    attempted = False
    cleanup_failed = False
    try:
        # Retain before calling owner, because bind invokes Code's validator.
        retained.entrances[1].check()
        attempted = True
        if retained.entrances[1].call(retained.source, expected=expected) is not None:
            raise ContractViolation("source bind returned non-None")
        retained.check()
        yield _BoundDependencySource(retained, expected)
    except BaseException as error:  # noqa: BLE001 - re-raised after all cleanup
        failures.append(error)
    finally:
        if attempted:
            try:
                # Cleanup invokes the original callable even after substitution.
                release = retained.entrances[2]
                if release.method(retained.source, expected=expected) is not None:
                    raise ContractViolation("source release returned non-None")
                release.check()
            except BaseException as error:  # noqa: BLE001 - re-raised after all cleanup
                failures.append(error)
                cleanup_failed = True
        try:
            operations._release_dependency_scope_operation(
                retained.validator, operation
            )
        except BaseException as error:  # noqa: BLE001 - re-raised after all cleanup
            failures.append(error)
            cleanup_failed = True
        if cleanup_failed:
            try:
                with _guard(state.binding) as guard:
                    state.binding.participant._mark_epoch_use_uncertain(
                        guard, operation
                    )
            except BaseException as uncertainty_error:  # noqa: BLE001 - retained below
                failures.append(uncertainty_error)
    if len(failures) == 1:
        raise failures[0]
    if failures:
        raise BaseExceptionGroup("dependency source use and cleanup failed", failures)
