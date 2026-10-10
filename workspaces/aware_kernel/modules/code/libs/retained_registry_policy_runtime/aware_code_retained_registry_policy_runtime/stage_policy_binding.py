"""Original Code host/policy occurrence validation; no caller source evidence.

Requires paired original assembly. This draft does not publish authority contexts,
provider execution, registry admissions or completion. Owner I/O stays outside
publication exclusion; the existing host retains lifetime/resource authority.
"""

from aware_code_module_manifest_contract_runtime import (
    AwareModuleSpecV2,
    parse_module_manifest,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.retained_scope_interfaces import (
    CodeRetainedScopeProjection,
)

from . import direct_host as hosts
from .calculation import _plain, calculate_registry_policy
from .direct_epoch_tracking import _tracked_policy


def validate_stage_policy_occurrence(host, policy, source_identity_digest):
    if hosts._state(host).source_rail == "declaration_v3":
        return _validate_v3_stage_policy_occurrence(
            host, policy, source_identity_digest
        )
    if hosts._qualified_mode(host):
        return _validate_qualified_stage_policy_occurrence(
            host, policy, source_identity_digest
        )
    return _validate_local_stage_policy_occurrence(host, policy, source_identity_digest)


def _validate_v3_stage_policy_occurrence(host, policy, source_identity_digest):
    from .declaration_host import _selected_policy_source, _selected_policy_view
    from .selected_participant_calculation import selected_qualified_occurrence

    if type(source_identity_digest) is not ContentDigest:
        raise TypeError("exact occurrence source digest required")
    source_identity_digest.__post_init__()
    with _selected_policy_source(host, policy) as (state, closure, admitted, binding):
        selected = binding.expectation
        if selected.source_identity_digest != source_identity_digest:
            raise ContractViolation("v3 stage source identity differs")
        if len(admitted.grants) != 1:
            raise ContractViolation("v3 stage occurrence unavailable")
        _, _, _, declaration = selected_qualified_occurrence(
            closure, _selected_policy_view(host, policy),
            (selected.scope_key, selected.module_id, selected.package_id),
        )
        wire = canonical_json_bytes(_plain(declaration))
        if (
            admitted.grants[0].source_identity_digest != source_identity_digest
            or admitted.grants[0].registration_declaration_digest
            != ContentDigest.of_bytes(wire)
        ):
            raise ContractViolation("v3 stage declaration differs")
        stages = state.stage_retention
        if stages is None:
            raise ContractViolation("original host has no retained authority stage")
        if stages.validate_declared_profiles(declaration) != wire:
            raise ContractViolation("original v3 stage profile differs")
        stages.validate()


def _validate_qualified_stage_policy_occurrence(host, policy, source_identity_digest):
    from .qualified_calculation import (
        calculate_qualified_registry_policy,
        qualified_occurrence,
    )
    from .qualified_host import policy_source

    if type(source_identity_digest) is not ContentDigest:
        raise TypeError("exact occurrence source digest required")
    source_identity_digest.__post_init__()
    source_key = source_identity_digest.value
    with policy_source(host, policy, purpose="authority_derivation") as (
        state,
        closure,
        admitted,
    ):
        stages = state.stage_retention
        if stages is None:
            raise ContractViolation("original host has no retained authority stage")
        derived = calculate_qualified_registry_policy(closure, state.check())
        if derived != admitted:
            raise ContractViolation("original qualified policy derivation changed")
        package, _, declaration = qualified_occurrence(closure, source_identity_digest)
        wire = canonical_json_bytes(_plain(declaration))
        grants = [
            g
            for g in derived.grants
            if g.source_identity_digest == package.source_identity_digest
        ]
        if len(grants) != 1 or grants[
            0
        ].registration_declaration_digest != ContentDigest.of_bytes(wire):
            raise ContractViolation("original qualified stage grant differs")
        if stages.validate_declared_profiles(declaration) != wire:
            raise ContractViolation("original qualified stage declaration changed")
        stages.validate()
        if (
            source_identity_digest.value != source_key
            or state.stage_retention is not stages
        ):
            raise ContractViolation("original qualified stage lineage changed")


@_tracked_policy
def _validate_local_stage_policy_occurrence(host, policy, source_identity_digest):
    """Validate one exact occurrence through original host-retained evidence."""
    if type(source_identity_digest) is not ContentDigest:
        raise TypeError("exact occurrence source digest required")
    source_identity_digest.__post_init__()
    source_key = source_identity_digest.value
    state = hosts._state(host)
    stages = state.stage_retention
    if stages is None:
        raise ContractViolation("original host has no retained authority stage")
    admitted = hosts.validate_admitted_registry_policy(host, policy)
    original_policy = hosts._POLICIES.get(policy)
    if original_policy is None or original_policy[0] is not host:
        raise ContractViolation("original stage policy unavailable")
    _, snapshot, digest, _ = original_policy
    methods = state.methods
    methods["scope"].call(snapshot, projection_digest=digest)
    scope = methods["read"].call(snapshot)
    if (
        type(scope) is not CodeRetainedScopeProjection
        or scope.projection_digest != digest
    ):
        raise ContractViolation("original stage policy scope changed")
    # Reuse the sole fixed producer; no independent membership or policy rule.
    derived = calculate_registry_policy(scope, state.check())
    if derived != admitted:
        raise ContractViolation("original stage policy derivation changed")
    grants = [g for g in derived.grants if g.source_identity_digest.value == source_key]
    if len(grants) != 1:
        raise ContractViolation("unique admitted stage occurrence required")
    grant = grants[0]
    wanted = grant.registration_declaration_digest
    declaration_body = None
    for module in scope.modules:
        model = parse_module_manifest(module.manifest.body)
        if type(model) is not AwareModuleSpecV2:
            raise ContractViolation("original stage scope requires v2 declaration")
        for package in model.package_declarations:
            for declaration in package.registrations:
                wire = canonical_json_bytes(_plain(declaration))
                if ContentDigest.of_bytes(wire) == wanted:
                    checked = stages.validate_declared_profiles(declaration)
                    if checked != wire:
                        raise ContractViolation("retained stage declaration changed")
                    if declaration_body is not None and declaration_body != wire:
                        raise ContractViolation("ambiguous retained stage declaration")
                    declaration_body = wire
    if declaration_body is None:
        raise ContractViolation("policy-bound stage declaration unavailable")
    stages.validate()
    methods["scope"].call(snapshot, projection_digest=digest)
    # The reread closes substitution of the consumed projection, not an atomic
    # filesystem-snapshot claim. Workspace retains the actual observation law.
    reread = methods["read"].call(snapshot)
    if (
        type(reread) is not CodeRetainedScopeProjection
        or reread.projection_digest != digest
    ):
        raise ContractViolation("stage scope changed after declaration validation")
    methods["scope"].call(snapshot, projection_digest=digest)
    state.check(read_catalog=False)
    guard = methods["acquire"].call(state.lifetime, expected=state.expected)
    try:
        methods["guard"].call(guard, lifetime=state.lifetime, expected=state.expected)
        # Original reference/liveness checks, no source reader or parser here.
        if (
            hosts._HOSTS.get(host) is not state
            or state.closed
            or hosts._POLICIES.get(policy) is not original_policy
            or state.stage_retention is not stages
            or source_identity_digest.value != source_key
        ):
            raise ContractViolation("original stage-policy lineage changed")
        stages.check_identities()
        if (
            methods["lifetime"].call(state.lifetime, expected=state.expected)
            is not None
        ):
            raise ContractViolation("original lifetime validator returned non-None")
        stages.check_identities()
        if state.closed:
            raise ContractViolation("stage host closed during final validation")
    finally:
        methods["release"].method(guard)
        methods["release"].check()
