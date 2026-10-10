"""Real nominal Code mechanics with isolated source/parent, no bootstrap claim."""

import copy
import os
from dataclasses import fields, replace

import pytest
from aware_code_retained_registry_policy_runtime import direct_host as host
from aware_code_retained_registry_policy_runtime import operation_context as op
from aware_code_retained_registry_policy_runtime.calculation import (
    calculate_registry_policy,
)
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import (
    ConsumedRoleDeclaration,
    ContentDigest,
    ContractViolation,
    ProviderExecutionBinding,
    SemanticConfigurationCoordinate,
    SemanticImplementationCoordinate,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    RESOURCE_ROLES,
    DirectCommandExpectedContext,
    DirectCommandResourceBinding,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticMaterializationProfileBinding,
    _issue_code_semantic_contract_catalog,
)
from aware_code_semantic_contract_runtime.portable_semantic_package_authority import (
    CodePortableSemanticContract,
)
from aware_code_semantic_contract_runtime.profile import (
    ProfileInputDeclaration,
    RoleBinding,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    DeclarationTargetInventoryCodec,
    PackageContextInputCodec,
    RegistryPackageInputCodec,
    retained_projection_body,
)
from aware_code_semantic_contract_runtime.retained_input_projections import (
    CodeSemanticDeclarationTargetInventory,
    CodeSemanticPackageContextInput,
    CodeSemanticRegistryPackageInput,
)
from aware_code_semantic_contract_runtime.runtime import (
    SemanticBody,
    SemanticContractRuntime,
)
from aware_code_semantic_contract_runtime.semantic_candidates import (
    CodeSemanticCandidate,
    CodeSemanticCandidateListing,
    SemanticCandidateListingCodec,
    semantic_candidate_listing_body,
)
from test_calculation import (
    _binding,
    _body,
    _catalog,
    _configuration,
    _implementation,
    fixture,
)
from test_contracts import SOURCE
from test_direct_host import Owner
from test_materialization_catalog import _execution_closure
from test_profile_runtime import JsonBodyCodec

_ARTIFACT = b'{"artifact":"planning-context-test-provider"}'
_CONFIGURATION = b'{"configuration":"planning-context-test"}'
_BINDING = ProviderExecutionBinding(
    "planning_test",
    SemanticImplementationCoordinate("test", ContentDigest.of_bytes(_ARTIFACT)),
    SemanticConfigurationCoordinate("test", ContentDigest.of_bytes(_CONFIGURATION)),
)


class _SelectedProvider:
    calls = 0
    last_input_value = None

    @property
    def declaration(self):
        return self._declaration

    async def derive(self, invocation):
        raise AssertionError("no semantic invocation")

    def execute(self, step, value):
        raise AssertionError("no execution")

    def input_closure(self, value):
        raise AssertionError("no closure invocation")


CONTRACTS = {
    "manifest_source": SOURCE,
    "candidate_listing": SemanticCandidateListingCodec.contract,
    "registry_package": RegistryPackageInputCodec.contract,
    "package_context": PackageContextInputCodec.contract,
    "declaration_inventory": DeclarationTargetInventoryCodec.contract,
}


def planning_profile():
    base = _binding(
        provider_key="planning_test", profile_ref="planning"
    ).profile_declaration
    provider = replace(
        base.providers[0],
        provider_key="planning_test",
        consumed_roles=tuple(
            ConsumedRoleDeclaration(role, (contract,))
            for role, contract in sorted(CONTRACTS.items())
        ),
    )
    return replace(
        base,
        profile_ref="planning",
        providers=(provider,),
        inputs=tuple(
            ProfileInputDeclaration(role, contract)
            for role, contract in sorted(CONTRACTS.items())
        ),
        steps=(
            replace(
                base.steps[0],
                provider_key="planning_test",
                bindings=tuple(RoleBinding(role, role) for role in sorted(CONTRACTS)),
            ),
        ),
    )


def construct():
    declaration = planning_profile()
    provider = _SelectedProvider()
    provider._declaration = declaration.providers[0]
    contracts = set(CONTRACTS.values()) | {
        provider.declaration.result_role.contract,
        provider.declaration.transition_contract,
        provider.declaration.effect_contract,
        *(r.contract for r in provider.declaration.output_roles),
    }
    runtime = SemanticContractRuntime(
        declaration,
        {"planning_test": provider},
        {c: JsonBodyCodec(c) for c in contracts},
    )
    return selected._SelectedProviderFactoryProduct(
        runtime,
        provider,
        _BINDING,
        provider.execute,
        provider.input_closure,
        _ARTIFACT,
        _CONFIGURATION,
    )


FACTORY = selected._admit_selected_provider_factory(
    factory_ref="aware.test.planning-context",
    provider_key="planning_test",
    selection_factory=construct,
)


def setup():
    root = selected._issue_selected_provider_selection_root(FACTORY)
    source = selected._selection_root_state(root)
    runtime, provider = source.runtime, source.provider
    registration = selected.register_selected_provider(runtime, root)
    authority = _binding(provider_key="planning_test", profile_ref="authority")
    base = _binding(provider_key="planning_test", profile_ref="planning")
    values = {
        f.name: getattr(base, f.name)
        for f in fields(base)
        if f.name != "binding_digest"
    }
    values.update(
        profile_declaration=runtime.profile, provider_execution_bindings=(_BINDING,)
    )
    planning = CodeSemanticMaterializationProfileBinding.create(**values)
    original, old_catalog = fixture()
    text = (
        original.modules[0]
        .manifest.body.decode()
        .replace('provider_key = "demo"', 'provider_key = "planning_test"')
    )
    for old, new in zip(old_catalog.entries, (authority, planning), strict=True):
        text = text.replace(
            old.profile_declaration.digest.to_wire(),
            new.profile_declaration.digest.to_wire(),
        )
    module = replace(
        original.modules[0], manifest=_body("demo/aware.module.toml", text.encode())
    )
    projection = replace(original, modules=(module,))
    owner = Owner(projection)
    catalog = _catalog(authority, planning)
    providers, planners = _execution_closure(catalog)
    admitted = _issue_code_semantic_contract_catalog(
        catalog=catalog,
        provider_executable_bindings=providers,
        dependency_planner_bindings=planners,
        host_liveness=lambda: owner.catalog_live,
    )
    resources = {role: object() for role in RESOURCE_ROLES}
    resources.update(
        catalog=admitted,
        code_runtime=runtime,
        composition_factory=owner,
        lifetime_runtime=owner,
        scope_adapter=owner,
        policy_producer=calculate_registry_policy,
    )
    owner.expected = DirectCommandExpectedContext(
        object(),
        object(),
        os.getpid(),
        runtime,
        admitted,
        _implementation("composition"),
        _configuration("composition"),
        _implementation("policy"),
        _configuration("policy"),
        tuple(
            DirectCommandResourceBinding(role, resources[role], "borrowed")
            for role in RESOURCE_ROLES
        ),
    )
    bootstrap = host._assemble_direct_command_bootstrap(
        lifetime=owner.lifetime, expected=owner.expected
    )
    direct = host.register_direct_workspace_origin(bootstrap, owner.lifetime)
    policy = host.produce_registry_policy(direct, owner.snapshot)
    package = projection.packages[0]
    coordinate = SemanticPackageCoordinate(
        "home-demo@1.0", "sdk", package.manifest.content_digest
    )
    context = CodeSemanticPackageContextInput(
        coordinate,
        package.source_identity_digest,
        package.manifest_relative_path,
        "home-code",
        "1.0",
        None,
        None,
        None,
    )
    registry = CodeSemanticRegistryPackageInput(
        "demo_toml",
        "aware.demo.toml",
        "planning_test",
        "public",
        "sdk",
        CodePortableSemanticContract("sdk", "demo", "planning_test", "contract:demo"),
        ("aware",),
        None,
        "home",
        ("home",),
        runtime.profile.profile_ref,
        runtime.profile.version,
        runtime.profile.digest,
        _BINDING,
    )
    manifest = SemanticBody(
        SemanticValueCoordinate(
            "manifest_source",
            SOURCE,
            "retained:manifest",
            package.manifest.content_digest,
            len(package.manifest.body),
        ),
        package.manifest.body,
    )
    candidates = CodeSemanticCandidateListing(
        package.source_identity_digest,
        (
            CodeSemanticCandidate(
                package.manifest_relative_path, package.manifest.content_digest
            ),
        ),
    )
    request = op.RetainedSourcePlanningRequest(
        manifest,
        semantic_candidate_listing_body(candidates),
        retained_projection_body(registry),
        retained_projection_body(context),
        retained_projection_body(
            CodeSemanticDeclarationTargetInventory(
                coordinate, package.source_identity_digest, ()
            )
        ),
    )
    return owner, direct, policy, provider, registration, request


def begin(values):
    _owner, direct, policy, _provider, registration, request = values
    return op.begin_source_planning_operation(direct, policy, registration, request)


def test_original_context_revalidates_without_provider_execution():
    values = setup()
    owner, direct, _, provider, registration, _ = values
    context = begin(values)
    expected = op.source_planning_expectation(direct, context)
    validator = op.source_planning_context_validator(direct)
    assert op.source_planning_context_validator(direct) is validator
    for _ in range(3):
        validator.validate_retained_semantic_operation_context(
            context, expected=expected
        )
    assert expected.runtime is owner.expected.runtime
    assert expected.generation_identity is owner.expected.epoch_identity
    assert expected.stage == "source_planning"
    assert provider.calls == 0 and provider.last_input_value is None
    assert selected._registration_state(registration).sequence == 0


@pytest.mark.parametrize(
    "change", ["lifetime", "catalog", "scope", "provider", "request", "closed"]
)
def test_changed_original_evidence_rejects(change):
    values = setup()
    owner, direct, _, _provider, registration, request = values
    context = begin(values)
    expected = op.source_planning_expectation(direct, context)
    if change == "lifetime":
        owner.live = False
    elif change == "catalog":
        owner.catalog_live = False
    elif change == "scope":
        owner.projection = replace(
            owner.projection, observation_digest=ContentDigest.of_bytes(b"changed")
        )
    elif change == "provider":
        selected.close_selected_provider_registration(
            owner.expected.runtime, registration
        )
    elif change == "request":
        object.__setattr__(request.manifest_source.coordinate, "value_ref", "replaced")
    elif change == "closed":
        host.close_direct_validation_host(direct)
    with pytest.raises(ContractViolation):
        op.source_planning_context_validator(
            direct
        ).validate_retained_semantic_operation_context(context, expected=expected)


@pytest.mark.parametrize(
    "field,value",
    [
        ("stage", "authority_derivation"),
        ("operation_identity", object()),
        ("generation_identity", object()),
        ("process_id", -1),
    ],
)
def test_transplanted_expectation_rejects(field, value):
    values = setup()
    context = begin(values)
    direct = values[1]
    expected = replace(
        op.source_planning_expectation(direct, context), **{field: value}
    )
    with pytest.raises(ContractViolation):
        op.source_planning_context_validator(
            direct
        ).validate_retained_semantic_operation_context(context, expected=expected)


def test_foreign_and_reconstructed_contexts_reject():
    first, second = setup(), setup()
    context = begin(first)
    expected = op.source_planning_expectation(first[1], context)
    with pytest.raises(ContractViolation):
        op.source_planning_context_validator(
            second[1]
        ).validate_retained_semantic_operation_context(context, expected=expected)
    with pytest.raises(ContractViolation):
        op.source_planning_expectation(
            first[1], object.__new__(op.SourcePlanningOperationContext)
        )
    with pytest.raises(TypeError):
        copy.copy(context)


@pytest.mark.parametrize("role", list(CONTRACTS))
def test_changed_body_coordinate_rejects_before_publication(role):
    values = setup()
    body = getattr(values[-1], role)
    object.__setattr__(body.coordinate, "digest", ContentDigest.of_bytes(b"foreign"))
    with pytest.raises(ContractViolation):
        begin(values)


def test_parent_closure_during_acquire_refuses_context():
    values = setup()
    values[0].close_on_acquire = True
    with pytest.raises(ContractViolation):
        begin(values)
    assert values[0].guard is None


def test_foreign_registration_rejects():
    first, second = setup(), setup()
    with pytest.raises(ContractViolation):
        op.begin_source_planning_operation(first[1], first[2], second[4], first[5])


def test_original_validator_substitution_refuses(monkeypatch):
    values = setup()
    context = begin(values)
    expected = op.source_planning_expectation(values[1], context)
    validator = op.source_planning_context_validator(values[1])
    original = validator.validate_retained_semantic_operation_context
    with monkeypatch.context() as patch:
        patch.setattr(
            validator,
            "validate_retained_semantic_operation_context",
            lambda *a, **k: None,
        )
        with pytest.raises(ContractViolation, match="substituted"):
            op.source_planning_context_validator(values[1])
        with pytest.raises(ContractViolation, match="substituted"):
            original(context, expected=expected)


def test_forked_process_refuses(monkeypatch):
    values = setup()
    context = begin(values)
    pid = os.getpid()
    with monkeypatch.context() as patch:
        patch.setattr(host.os, "getpid", lambda: pid + 1)
        with pytest.raises(ContractViolation):
            op.source_planning_expectation(values[1], context)


def test_foreign_policy_refuses():
    first, second = setup(), setup()
    with pytest.raises(ContractViolation):
        op.begin_source_planning_operation(first[1], second[2], first[4], first[5])


def test_registry_replacement_refuses():
    values = list(setup())
    registry = RegistryPackageInputCodec().decode(
        values[-1].registry_package.canonical_body
    )
    changed = replace(registry, fqn_prefix="foreign")
    values[-1] = replace(values[-1], registry_package=retained_projection_body(changed))
    with pytest.raises(ContractViolation, match="registry request"):
        begin(values)


def test_missing_manifest_candidate_refuses():
    values = list(setup())
    candidates = SemanticCandidateListingCodec().decode(
        values[-1].candidate_listing.canonical_body
    )
    values[-1] = replace(
        values[-1],
        candidate_listing=semantic_candidate_listing_body(
            replace(candidates, candidates=())
        ),
    )
    with pytest.raises(ContractViolation, match="manifest correspondence"):
        begin(values)


def test_source_rederivation_uses_exact_entry_without_catalog_export(monkeypatch):
    from aware_code_semantic_contract_runtime import materialization_catalog as catalogs

    values = setup()
    snapshots = []
    original = catalogs._detached_catalog_snapshot

    def counted(catalog):
        snapshots.append(catalog)
        return original(catalog)

    monkeypatch.setattr(catalogs, "_detached_catalog_snapshot", counted)
    try:
        context = begin(values)
        # Both derivations and later validations read only detached entries.
        assert snapshots == []
        for _ in range(2):
            op.source_planning_expectation(values[1], context)
            assert snapshots == []
        values[0].catalog_live = False
        with pytest.raises(ContractViolation):
            op.source_planning_expectation(values[1], context)
        assert snapshots == []
    finally:
        host.close_direct_validation_host(values[1])


def test_optional_performance_probe_records_without_affecting_context():
    events = []

    class Probe:
        def record(self, **event):
            events.append(event)

    token = op.set_performance_probe(Probe())
    try:
        op._performance_count("code.test_counter", amount=2)
        with op._performance_phase("code.test_phase"):
            pass
    finally:
        op.reset_performance_probe(token)

    assert {event["kind"] for event in events} == {"counter", "phase_start", "phase_end"}
    assert {event["name"] for event in events} == {
        "code.test_counter",
        "code.test_phase",
    }
    assert next(event for event in events if event["kind"] == "counter")["amount"] == 2
