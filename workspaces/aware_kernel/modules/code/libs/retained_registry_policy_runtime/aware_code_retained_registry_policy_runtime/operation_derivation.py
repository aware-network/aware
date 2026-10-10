"""Shared retained-source derivation; comparison values never grant authority.

Only original host stage retention selects a runtime. Authority issuance still
requires original planning/product lineage and a separate nominal operation.
"""

from copy import deepcopy
from dataclasses import dataclass, fields

from aware_code_module_manifest_contract_runtime import (
    AwareModuleSpecV2,
    parse_module_manifest,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_v2 import (
    CodeRetainedDependencyScopeClosureV2,
)
from aware_code_semantic_contract_runtime.retained_admission_interfaces import (
    RetainedSemanticAdmissionExpectation,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    DeclarationTargetInventoryCodec,
    PackageContextInputCodec,
    RegistryPackageInputCodec,
)
from aware_code_semantic_contract_runtime.retained_scope_interfaces import (
    CodeRetainedScopeProjection,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeRetainedDependencyScopeClosureV3,
    CodeSelectedPackageSourceBinding,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_code_semantic_contract_runtime.selected_provider import (
    validate_selected_provider_registration,
)
from aware_code_semantic_contract_runtime.semantic_candidates import (
    CodeSemanticCandidateListing,
    SemanticCandidateListingCodec,
)

from . import direct_host
from .calculation import _execution_entry_correspondence, _plain
from .qualified_calculation import _qualified_occurrences, qualified_occurrence


def _stage_runtime(state, registration, stage):
    if stage not in ("source_planning", "authority_derivation"):
        raise ContractViolation("unsupported retained semantic stage")
    retained = state.stage_retention
    if retained is None:
        if stage != "source_planning":
            raise ContractViolation("original authority stage retention required")
        return state.expected.runtime
    retained.check_identities()
    matches = [
        (runtime, original)
        for name, runtime, original in retained.stages
        if name == stage and original is registration
    ]
    if len(matches) != 1:
        raise ContractViolation("original stage registration required")
    return matches[0][0]


@dataclass(frozen=True, slots=True)
class RetainedSourcePlanningRequest:
    """Exact proposed bodies; Workspace still admits membership and completeness."""

    manifest_source: SemanticBody
    candidate_listing: SemanticBody
    registry_package: SemanticBody
    package_context: SemanticBody
    declaration_inventory: SemanticBody


def _bodies(request):
    if type(request) is not RetainedSourcePlanningRequest:
        raise TypeError("exact retained planning request required")
    result = []
    for field in fields(request):
        body = getattr(request, field.name)
        if type(body) is not SemanticBody:
            raise TypeError("exact semantic body required")
        body.__post_init__()
        if body.coordinate.role != field.name:
            raise ContractViolation("planning input role differs")
        result.append(body)
    return tuple(result)


def _decode(body, codec):
    if body.coordinate.contract != codec.contract:
        raise ContractViolation("planning input contract differs")
    value = codec.decode(body.canonical_body)
    if codec.encode(value) != body.canonical_body:
        raise ContractViolation("planning input is not canonical")
    return value


def _derive_stage(host, policy, registration, request, operation, *, stage):
    """Both stages consume the host-selected source rail; no qualified fallback."""
    state = direct_host._state(host)
    if state.source_rail == "declaration_v3":
        from .declaration_host import _selected_policy_source, _selected_policy_view

        with _selected_policy_source(host, policy) as (
            state, scope, admitted, selected,
        ):
            return _derive_stage_body(
                state, scope, admitted, registration, request, operation,
                stage=stage, selected_source=selected,
                selected_view=_selected_policy_view(host, policy),
            )
    if state.qualified:
        from .qualified_host import policy_source

        with policy_source(host, policy, purpose=stage) as (state, scope, admitted):
            return _derive_stage_body(
                state, scope, admitted, registration, request, operation, stage=stage
            )
    admitted = direct_host.validate_admitted_registry_policy(host, policy)
    _, snapshot, digest, _ = direct_host._POLICIES[policy]
    scope = state.methods["read"].call(snapshot)
    if (
        type(scope) is not CodeRetainedScopeProjection
        or scope.projection_digest != digest
    ):
        raise ContractViolation("original planning scope differs")
    result = _derive_stage_body(
        state, scope, admitted, registration, request, operation, stage=stage
    )
    state.methods["scope"].call(snapshot, projection_digest=digest)
    state.check(read_catalog=False)
    if _stage_runtime(state, registration, stage) is not result.runtime:
        raise ContractViolation("original stage runtime changed during derivation")
    return result


def _derive_stage_body(
    state, scope, admitted_policy, registration, request, operation, *, stage,
    selected_source=None,
    selected_view=None,
):
    bodies = _bodies(request)
    candidates = _decode(request.candidate_listing, SemanticCandidateListingCodec())
    if type(candidates) is not CodeSemanticCandidateListing:
        raise ContractViolation("exact candidate listing required")
    registry = _decode(request.registry_package, RegistryPackageInputCodec())
    context = _decode(request.package_context, PackageContextInputCodec())
    inventory = _decode(
        request.declaration_inventory, DeclarationTargetInventoryCodec()
    )
    runtime = _stage_runtime(state, registration, stage)
    if type(scope) is CodeRetainedDependencyScopeClosureV3:
        if type(selected_source) is not CodeSelectedPackageSourceBinding:
            raise ContractViolation("original v3 selected source required")
        selected = selected_source.expectation
        if context.source_identity_digest != selected.source_identity_digest:
            raise ContractViolation("v3 planning source identity differs")
        from .selected_participant_calculation import selected_qualified_occurrence

        _, package, _, declaration = selected_qualified_occurrence(
            scope, selected_view,
            (selected.scope_key, selected.module_id, selected.package_id),
        )
        declared = _plain(declaration)
    elif type(scope) is CodeRetainedDependencyScopeClosureV2:
        package, _, declaration = qualified_occurrence(
            scope, context.source_identity_digest
        )
        declared = _plain(declaration)
    else:
        matches = [
            p
            for p in scope.packages
            if p.source_identity_digest == context.source_identity_digest
        ]
        if len(matches) != 1:
            raise ContractViolation("unique planning source occurrence required")
        package = matches[0]
        declarations = {}
        for module in scope.modules:
            model = parse_module_manifest(module.manifest.body)
            if type(model) is not AwareModuleSpecV2:
                raise ContractViolation("planning scope requires v2")
            for declaration in model.package_declarations:
                declarations[(module.module_id, declaration.package_id)] = declaration
        occurrence = declarations[(package.module_id, package.package_id)].occurrence
        address = _plain(occurrence.registration.value)
        owner = declarations[(address["module_id"], address["package_id"])]
        matches = [
            _plain(r)
            for r in owner.registrations
            if _plain(r)["key"] == address["registration_key"]
        ]
        if len(matches) != 1:
            raise ContractViolation("original registration declaration unavailable")
        declared = matches[0]
    if (
        request.manifest_source.canonical_body != package.manifest.body
        or context.package.manifest_digest != package.manifest.content_digest
        or context.manifest_relative_path != package.manifest_relative_path
        or context.package.package_kind != package.package_kind
        or candidates.source_identity_digest != context.source_identity_digest
        or inventory.source_identity_digest != context.source_identity_digest
        or inventory.package != context.package
    ):
        raise ContractViolation("planning package/source closure differs")
    manifests = [
        c
        for c in candidates.candidates
        if c.relative_path == package.manifest_relative_path
    ]
    if (
        len(manifests) != 1
        or manifests[0].content_digest != package.manifest.content_digest
    ):
        raise ContractViolation("candidate manifest correspondence differs")
    stages = [s for s in declared["profiles"] if s["stage"] == stage]
    if len(stages) != 1:
        raise ContractViolation("source-planning stage unavailable")
    declared_stage = stages[0]
    profile = runtime.profile
    if (profile.profile_ref, profile.version, profile.digest.to_wire()) != (
        declared_stage["profile_ref"],
        declared_stage["profile_version"],
        declared_stage["profile_digest"],
    ):
        raise ContractViolation("original runtime is not declared planning stage")
    state.check(read_catalog=False)
    entry = state.catalog_resolver.read_profile_binding(
        profile=profile, semantic_provider_key=registry.semantic_provider_key
    )
    _execution_entry_correspondence(declared, entry, package_kind=package.package_kind)
    providers = [
        p for p in profile.providers if p.provider_key == registry.semantic_provider_key
    ]
    bindings = [
        b
        for b in entry.provider_execution_bindings
        if b.provider_key == registry.semantic_provider_key
    ]
    if len(providers) != 1 or len(bindings) != 1:
        raise ContractViolation("planning provider unavailable")
    binding = bindings[0]
    grant_matches = [
        g
        for g in admitted_policy.grants
        if g.source_identity_digest == context.source_identity_digest
        and g.registration_declaration_digest
        == ContentDigest.of_bytes(canonical_json_bytes(declared))
    ]
    if len(grant_matches) != 1:
        raise ContractViolation("original occurrence policy unavailable")
    grant = grant_matches[0]
    # Compare every registry field to original retained declaration, catalog and policy.
    expected_registry = {
        "manifest_contract_kind": declared["manifest_contract_kind"],
        "manifest_filename": declared["manifest_filename"],
        "semantic_provider_key": declared["semantic_contract"]["provider_key"],
        "semantic_package_family": declared["semantic_package_family"],
        "semantic_package_kind": declared["semantic_package_kind"],
        "semantic_contract": declared["semantic_contract"],
        "supported_languages": declared["supported_languages"],
        "code_package_surface": declared["code_package_surface"].get("value"),
        "fqn_prefix": grant.namespace,
        "owned_semantic_root_refs": list(grant.owned_roots),
        "profile_ref": profile.profile_ref,
        "profile_version": profile.version,
        "profile_digest": profile.digest.to_wire(),
        "binding": binding.to_wire(),
    }
    wire = registry.to_wire()
    if {k: wire[k] for k in expected_registry} != expected_registry:
        raise ContractViolation(
            "registry request differs from retained planning declaration"
        )
    inputs = {i.role: i.contract for i in profile.inputs}
    if any(inputs.get(b.coordinate.role) != b.coordinate.contract for b in bodies):
        raise ContractViolation("retained request differs from planning profile inputs")
    validate_selected_provider_registration(
        runtime,
        registration,
        expected_profile=profile,
        expected_declaration=providers[0],
        expected_binding=binding,
    )
    state.check(read_catalog=False)
    if _stage_runtime(state, registration, stage) is not runtime:
        raise ContractViolation("original stage runtime changed during derivation")
    return RetainedSemanticAdmissionExpectation(
        runtime,
        state.expected.epoch_identity,
        operation,
        state.pid,
        registration,
        stage,
        deepcopy(profile),
        deepcopy(providers[0]),
        deepcopy(binding),
        deepcopy(context.package),
        deepcopy(context.source_identity_digest),
        *(deepcopy(b.coordinate) for b in bodies),
    )


def _derive(host, policy, registration, request, operation):
    return _derive_stage(
        host, policy, registration, request, operation, stage="source_planning"
    )
