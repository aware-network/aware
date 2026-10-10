"""Selected v3 correspondence for the existing Code host lifecycle.

This portable calculation is not admission. The host must authenticate the
original Workspace declaration and selected-source handles before using its
result, and revalidate both after provider work and under parent exclusion.
"""

from __future__ import annotations

import os
from copy import deepcopy
from contextlib import contextmanager
from dataclasses import dataclass
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from aware_code_semantic_contract_runtime.registry_policy import RegistryPolicy
from aware_code_semantic_contract_runtime.registry_policy import RegistryPolicyGrant
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeRetainedDependencyScopeClosureV3,
    CodeDeclarationScopeExpectation,
    CodeSelectedPackageSourceBinding,
)
from aware_code_semantic_contract_runtime.selected_participant_scope import (
    CodeSelectedParticipantViewV1,
)

from .declaration_eligibility import (
    DeclarationEligibility,
    calculate_declaration_eligibility,
)
from .qualified_scope import validate_selected_scope_graph_v3


@dataclass(frozen=True, eq=False)
class _PreparedDeclarationSource:
    """Original host-bound read prepared outside the parent's exclusion."""

    host: object
    state: object
    handle: object
    expectation: CodeDeclarationScopeExpectation
    closure: CodeRetainedDependencyScopeClosureV3
    digest: ContentDigest
    pid: int


_PREPARED: WeakKeyDictionary[_PreparedDeclarationSource, ContentDigest] = WeakKeyDictionary()


def _prepare_declaration_source(host, handle, expectation):
    from . import direct_host as direct

    state = direct._state(host)
    if state.source_rail != "declaration_v3":
        raise ContractViolation("v3 declaration host required")
    if type(expectation) is not CodeDeclarationScopeExpectation:
        raise TypeError("exact declaration expectation required")
    expectation.__post_init__()
    if expectation.process_id != os.getpid():
        raise ContractViolation("declaration process differs")
    methods = state.methods
    methods["scope"].call(handle, expectation=expectation)
    closure = methods["read"].call(handle)
    if type(closure) is not CodeRetainedDependencyScopeClosureV3:
        raise ContractViolation("original v3 declaration closure required")
    if closure.repository_binding_ref != expectation.repository_binding_ref:
        raise ContractViolation("declaration repository differs")
    validate_selected_scope_graph_v3(closure)
    methods["scope"].call(
        handle, expectation=expectation, closure_digest=closure.closure_digest
    )
    state.check(read_catalog=False)
    prepared = _PreparedDeclarationSource(
        host, state, handle, expectation, closure, closure.closure_digest,
        os.getpid(),
    )
    _PREPARED[prepared] = prepared.digest
    return prepared


def _retain_declaration_source_locked(host, prepared, guard):
    from . import direct_host as direct

    if type(prepared) is not _PreparedDeclarationSource:
        raise TypeError("exact prepared declaration required")
    state = direct._HOSTS.get(host)
    retained = _PREPARED.get(prepared)
    if (
        retained is None
        or retained != prepared.digest
        or prepared.expectation.process_id != os.getpid()
        or state is None
        or state is not prepared.state
        or prepared.host is not host
        or prepared.pid != os.getpid()
        or state.closed
        or state.declaration_binding is not None
    ):
        raise ContractViolation("original declaration preparation unavailable")
    state.methods["scope_locked"].call(
        prepared.handle,
        expectation=prepared.expectation,
        closure_digest=prepared.digest,
        guard=guard,
    )
    state.declaration_binding = prepared


def _check_declaration_source_locked(host, guard):
    from . import direct_host as direct

    state = direct._HOSTS.get(host)
    prepared = None if state is None else state.declaration_binding
    if (
        prepared is None
        or prepared.host is not host
        or prepared.state is not state
        or prepared.pid != os.getpid()
        or state.closed
    ):
        raise ContractViolation("original declaration binding unavailable")
    state.methods["scope_locked"].call(
        prepared.handle,
        expectation=prepared.expectation,
        closure_digest=prepared.digest,
        guard=guard,
    )


def _validate_declaration_source(host, *, successor_transition=False):
    from . import direct_host as direct

    if successor_transition:
        state = direct._HOSTS.get(host)
        if state is None:
            raise ContractViolation("original declaration host unavailable")
        state.check(read_catalog=False, check_catalog=False)
    else:
        state = direct._state(host)
    prepared = state.declaration_binding
    if prepared is None or prepared.host is not host or prepared.state is not state:
        raise ContractViolation("original declaration binding unavailable")
    methods = state.methods
    methods["scope"].call(
        prepared.handle,
        expectation=prepared.expectation,
        closure_digest=prepared.digest,
    )
    closure = methods["read"].call(prepared.handle)
    if (
        type(closure) is not CodeRetainedDependencyScopeClosureV3
        or closure != prepared.closure
        or closure.closure_digest != prepared.digest
        or _PREPARED.get(prepared) != prepared.digest
    ):
        raise ContractViolation("original declaration closure changed")
    methods["scope"].call(
        prepared.handle,
        expectation=prepared.expectation,
        closure_digest=prepared.digest,
    )
    if successor_transition:
        state.check(read_catalog=False, check_catalog=False)
    else:
        state.check(read_catalog=False)
    return prepared


def _selected_binding(host, handle, prepared):
    state = prepared.state
    methods = state.methods
    binding = methods["selected_read"].call(handle)
    if type(binding) is not CodeSelectedPackageSourceBinding:
        raise ContractViolation("original selected binding required")
    binding.__post_init__()
    if (
        binding.expectation.declaration != prepared.expectation
        or binding.expectation.closure_digest != prepared.closure.closure_digest
    ):
        raise ContractViolation("selected source belongs to another declaration")
    methods["selected_validate"].call(
        handle,
        expectation=binding.expectation,
        binding_digest=binding.binding_digest,
    )
    return binding


def _produce_selected_registry_policy(host, handle):
    from . import direct_host as direct
    from .direct_epoch_tracking import _BINDINGS, _guard, _policy_epoch_use

    result = None
    state = direct._state(host)
    if state.source_rail != "declaration_v3":
        raise ContractViolation("v3 declaration host required")
    try:
        with _policy_epoch_use(host) as pair:
            if pair is None:
                raise ContractViolation("v3 selected source requires original epoch")
            epoch, _use = pair
            prepared = _validate_declaration_source(host)
            binding = _selected_binding(host, handle, prepared)
            view = state.methods["participant_read"].call(prepared.handle, handle)
            if type(view) is not CodeSelectedParticipantViewV1:
                raise ContractViolation("original selected participant view required")
            state.methods["participant_validate"].call(
                prepared.handle, handle, view=view
            )
            eligibility = calculate_declaration_eligibility(
                prepared.closure, selected_view=view
            )
            grant = selected_source_grant_candidate(
                prepared.closure, eligibility, binding
            )
            policy = RegistryPolicy(prepared.closure.closure_digest, (grant,))
            _validate_declaration_source(host)
            state.methods["selected_validate"].call(
                handle,
                expectation=binding.expectation,
                binding_digest=binding.binding_digest,
            )
            state.methods["participant_validate"].call(
                prepared.handle, handle, view=view
            )
            state.check(read_catalog=False)
            with _guard(epoch) as guard:
                _check_declaration_source_locked(host, guard)
                state.methods["selected_locked"].call(
                    handle,
                    expectation=binding.expectation,
                    binding_digest=binding.binding_digest,
                    guard=guard,
                )
                with direct._LOCK:
                    if (
                        direct._HOSTS.get(host) is not state
                        or state.closed
                        or state.declaration_binding is not prepared
                        or _BINDINGS.get(host) is not epoch
                    ):
                        raise ContractViolation("selected policy origin changed")
                    result = object.__new__(direct.AdmittedRegistryPolicy)
                    direct._POLICIES[result] = (
                        host, handle, binding.binding_digest, policy,
                        binding.expectation, prepared, epoch, view,
                    )
        return result
    except BaseException:
        if result is not None:
            direct._POLICIES.pop(result, None)
        state.closed = True
        raise


def _validate_selected_registry_policy(host, admission):
    with _selected_policy_source(host, admission) as (_state, _closure, policy, _source):
        return policy


def _selected_policy_view(host, admission):
    """Return the exact original view retained with a validated policy use."""
    from . import direct_host as direct

    record = direct._POLICIES.get(admission)
    if (
        type(admission) is not direct.AdmittedRegistryPolicy
        or record is None
        or len(record) != 8
        or record[0] is not host
        or type(record[7]) is not CodeSelectedParticipantViewV1
    ):
        raise ContractViolation("original selected participant view unavailable")
    return record[7]


@contextmanager
def _selected_policy_source(host, admission):
    """Keep one original v3 epoch use across a selected-stage derivation."""
    from . import direct_host as direct
    from .direct_epoch_tracking import _BINDINGS, _guard, _policy_epoch_use

    state = direct._state(host)
    record = direct._POLICIES.get(admission)
    if (
        type(admission) is not direct.AdmittedRegistryPolicy
        or record is None
        or len(record) != 8
        or record[0] is not host
        or record[6] is not _BINDINGS.get(host)
    ):
        raise ContractViolation("original v3 policy unavailable")
    _, handle, digest, policy, expectation, prepared, _epoch, view = record
    try:
        with _policy_epoch_use(host) as pair:
            if pair is None or _validate_declaration_source(host) is not prepared:
                raise ContractViolation("original v3 policy epoch unavailable")
            epoch, _use = pair
            binding = _selected_binding(host, handle, prepared)
            if binding.binding_digest != digest or binding.expectation != expectation:
                raise ContractViolation("selected policy source changed")
            state.methods["participant_validate"].call(
                prepared.handle, handle, view=view
            )
            eligibility = calculate_declaration_eligibility(
                prepared.closure, selected_view=view
            )
            grant = selected_source_grant_candidate(
                prepared.closure, eligibility, binding
            )
            if RegistryPolicy(prepared.closure.closure_digest, (grant,)) != policy:
                raise ContractViolation("selected policy meaning changed")
            yield state, prepared.closure, deepcopy(policy), binding
            if _validate_declaration_source(host) is not prepared:
                raise ContractViolation("original v3 declaration changed")
            state.methods["selected_validate"].call(
                handle, expectation=expectation, binding_digest=digest
            )
            state.methods["participant_validate"].call(
                prepared.handle, handle, view=view
            )
            state.check(read_catalog=False)
            with _guard(epoch) as guard:
                _check_declaration_source_locked(host, guard)
                state.methods["selected_locked"].call(
                    handle, expectation=expectation,
                    binding_digest=digest, guard=guard,
                )
                with direct._LOCK:
                    if (
                        direct._HOSTS.get(host) is not state
                        or state.closed
                        or state.declaration_binding is not prepared
                        or _BINDINGS.get(host) is not epoch
                        or direct._POLICIES.get(admission) is not record
                    ):
                        raise ContractViolation("selected stage origin changed")
    except BaseException:
        state.closed = True
        raise


def selected_source_grant_candidate(
    closure: CodeRetainedDependencyScopeClosureV3,
    eligibility: DeclarationEligibility,
    binding: CodeSelectedPackageSourceBinding,
) -> RegistryPolicyGrant:
    """Relate one observed occurrence to its complete declaration eligibility.

    A caller-built binding can produce the same portable value; only the
    authenticated host may later retain it after original owner validation.
    """
    if type(closure) is not CodeRetainedDependencyScopeClosureV3:
        raise TypeError("exact v3 declaration closure required")
    if type(eligibility) is not DeclarationEligibility:
        raise TypeError("exact declaration eligibility required")
    if type(binding) is not CodeSelectedPackageSourceBinding:
        raise TypeError("exact selected source binding required")
    closure.__post_init__()
    eligibility.__post_init__()
    binding.__post_init__()
    expected = binding.expectation
    if (
        closure.closure_digest != eligibility.closure_digest
        or expected.closure_digest != eligibility.closure_digest
        or expected.declaration.repository_binding_ref
        != closure.repository_binding_ref
    ):
        raise ContractViolation("selected declaration closure differs")
    matches = [
        (scope, package)
        for scope in closure.scopes
        if scope.scope_key == expected.scope_key
        for package in scope.projection.packages
        if (package.module_id, package.package_id)
        == (expected.module_id, expected.package_id)
    ]
    if len(matches) != 1:
        raise ContractViolation("selected declaration occurrence unavailable")
    _, package = matches[0]
    if (
        package.manifest_relative_path != expected.manifest_relative_path
        or package.manifest.content_digest != expected.manifest_content_digest
    ):
        raise ContractViolation("selected package manifest differs")
    rows = [
        row
        for row in eligibility.packages
        if row.occurrence_key
        == (expected.scope_key, expected.module_id, expected.package_id)
    ]
    if len(rows) != 1:
        raise ContractViolation("selected package lacks declaration eligibility")
    row = rows[0]
    if row.declared_package_kind != package.package_kind:
        raise ContractViolation("selected package kind differs")
    return RegistryPolicyGrant(
        expected.source_identity_digest,
        row.registration_declaration_digest,
        row.declared_package_kind,
        row.semantic_package_kind,
        row.namespace,
        row.owned_roots,
    )


__all__ = ["selected_source_grant_candidate"]
