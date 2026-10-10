"""V3 methods are retained by the original host, without policy authority."""

import os
from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime import direct_host
from aware_code_retained_registry_policy_runtime import epoch_participation as epochs
from aware_code_retained_registry_policy_runtime.direct_epoch_tracking import (
    _bind_direct_policy_epoch,
)
from aware_code_retained_registry_policy_runtime.declaration_eligibility import (
    calculate_declaration_eligibility,
)
from aware_code_retained_registry_policy_runtime.declaration_host import (
    _check_declaration_source_locked,
    _prepare_declaration_source,
    _retain_declaration_source_locked,
    _selected_policy_source,
    _validate_declaration_source,
    selected_source_grant_candidate,
)
from aware_code_retained_registry_policy_runtime.operation_derivation import (
    _derive_stage,
)
from aware_code_retained_registry_policy_runtime.retained_input_admission import (
    assemble_retained_input_admission_origin,
)
from aware_code_retained_registry_policy_runtime import operation_derivation
from aware_code_retained_registry_policy_runtime.stage_policy_binding import (
    validate_stage_policy_occurrence,
)
from aware_code_retained_registry_policy_runtime.selected_participant_calculation import (
    derive_selected_participant_view,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticImplementationCoordinate,
)
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    CatalogPairEpochExpectation,
    DirectInvocationExpectation,
)
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    DECLARATION_V3_RESOURCE_ROLES,
    DirectCommandExpectedContext,
    DirectCommandResourceBinding,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    _issue_code_semantic_contract_catalog,
)
from aware_code_semantic_contract_runtime.runtime import SemanticContractRuntime
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeDeclarationScopeExpectation,
    CodeSelectedPackageSourceBinding,
    CodeSelectedPackageSourceExpectation,
)
from aware_code_semantic_contract_runtime.semantic_candidates import (
    CodeSemanticCandidate,
    CodeSemanticCandidateListing,
)

from test_calculation import fixture as local_fixture
from test_declaration_eligibility import fixture as declaration_fixture
from test_direct_host import Owner
from test_direct_epoch_tracking import Owner as EpochOwner
from test_materialization_catalog import _execution_closure
from test_profile_runtime import DeltaProvider, body_codecs, profile
from test_selected_participant_calculation import _mixed_closure


class DeclarationOwner(Owner):
    def read_declaration_scope(self, handle):
        if handle is not self.snapshot:
            raise ContractViolation("foreign declaration handle")
        return self.projection

    def validate_declaration_scope(self, handle, *, expectation, closure_digest=None):
        self.read_declaration_scope(handle)
        if closure_digest is not None and closure_digest != self.projection.closure_digest:
            raise ContractViolation("declaration changed")

    def check_declaration_scope_locked(
        self, handle, *, expectation, closure_digest, guard
    ):
        self.validate_declaration_scope(
            handle, expectation=expectation, closure_digest=closure_digest
        )

    def read_selected_package_source(self, handle):
        raise ContractViolation("selected source not yet admitted")

    def validate_selected_package_source(
        self, handle, *, expectation, binding_digest=None
    ):
        raise ContractViolation("selected source not yet admitted")

    def check_selected_package_source_locked(
        self, handle, *, expectation, binding_digest, guard
    ):
        raise ContractViolation("selected source not yet admitted")

    def read_selected_participant_view(self, declaration, selected):
        closure = self.read_declaration_scope(declaration)
        binding = self.read_selected_package_source(selected)
        expected = binding.expectation
        return derive_selected_participant_view(
            closure, scope_key=expected.scope_key,
            module_id=expected.module_id, package_id=expected.package_id,
        )

    def validate_selected_participant_view(self, declaration, selected, *, view):
        if self.read_selected_participant_view(declaration, selected) != view:
            raise ContractViolation("original selected participant view changed")


def registered(owner_type=DeclarationOwner, projection=None):
    _, catalog = local_fixture()
    owner = owner_type(declaration_fixture() if projection is None else projection)
    providers, planners = _execution_closure(catalog)
    admission = _issue_code_semantic_contract_catalog(
        catalog=catalog,
        provider_executable_bindings=providers,
        dependency_planner_bindings=planners,
        host_liveness=lambda: owner.catalog_live,
    )
    runtime = SemanticContractRuntime(
        profile(), {"sdk": DeltaProvider()}, body_codecs()
    )
    resources = {role: object() for role in DECLARATION_V3_RESOURCE_ROLES}
    resources.update(
        catalog=admission,
        code_runtime=runtime,
        composition_factory=owner,
        lifetime_runtime=owner,
        declaration_scope_runtime=owner,
        policy_producer=calculate_declaration_eligibility,
    )
    digest = ContentDigest.of_bytes(b"isolated-v3-host")
    owner.expected = DirectCommandExpectedContext(
        object(), object(), os.getpid(), runtime, admission,
        SemanticImplementationCoordinate("composition", digest),
        SemanticConfigurationCoordinate("composition", digest),
        SemanticImplementationCoordinate("policy", digest),
        SemanticConfigurationCoordinate("policy", digest),
        tuple(
            DirectCommandResourceBinding(role, resources[role], "borrowed")
            for role in DECLARATION_V3_RESOURCE_ROLES
        ),
        source_rail="declaration_v3",
    )
    bootstrap = direct_host._assemble_direct_command_bootstrap(
        lifetime=owner.lifetime, expected=owner.expected
    )
    host = direct_host.register_direct_workspace_origin(
        bootstrap, owner.lifetime
    )
    return owner, host


def test_declaration_host_requires_no_legacy_whole_root_resources():
    owner, host = registered()
    try:
        assert tuple(binding.role for binding in owner.expected.resources) == (
            "catalog",
            "code_runtime",
            "composition_factory",
            "declaration_scope_runtime",
            "lifetime_runtime",
            "policy_producer",
        )
        with pytest.raises(
            ContractViolation, match="original semantic issuer entrance unavailable"
        ):
            assemble_retained_input_admission_origin(host)
    finally:
        direct_host.close_direct_validation_host(host)


class OriginalEpochDeclarationOwner(DeclarationOwner, EpochOwner):
    def __init__(self, projection):
        super().__init__(projection)
        self.selected = object()
        self.selected_live = True
        self.selected_value = selected_binding(projection)

    def read_declaration_scope(self, handle):
        assert not self.guards, "source read under parent exclusion"
        return super().read_declaration_scope(handle)

    def check_declaration_scope_locked(
        self, handle, *, expectation, closure_digest, guard
    ):
        assert guard in self.guards
        if (
            handle is not self.snapshot
            or expectation != self.declaration_expectation
            or closure_digest != self.projection.closure_digest
            or not self.live
        ):
            raise ContractViolation("original guarded declaration changed")

    def read_selected_package_source(self, handle):
        assert not self.guards, "selected source read under parent exclusion"
        if handle is not self.selected or not self.selected_live:
            raise ContractViolation("original selected source unavailable")
        return self.selected_value

    def validate_selected_package_source(
        self, handle, *, expectation, binding_digest=None
    ):
        binding = self.read_selected_package_source(handle)
        if (
            binding.expectation != expectation
            or binding_digest is not None
            and binding.binding_digest != binding_digest
        ):
            raise ContractViolation("original selected source changed")

    def check_selected_package_source_locked(
        self, handle, *, expectation, binding_digest, guard
    ):
        assert guard in self.guards
        if (
            handle is not self.selected
            or not self.selected_live
            or expectation != self.selected_value.expectation
            or binding_digest != self.selected_value.binding_digest
        ):
            raise ContractViolation("original guarded selected source changed")


def registered_epoch(projection=None):
    owner, host = registered(
        OriginalEpochDeclarationOwner,
        _mixed_closure(direct_target=False) if projection is None else projection,
    )
    closure = owner.projection
    expectation = CodeDeclarationScopeExpectation(
        closure.repository_binding_ref, "parent", os.getpid(), "operation", "epoch"
    )
    owner.declaration_expectation = expectation
    prepared = _prepare_declaration_source(host, owner.snapshot, expectation)
    invocation = DirectInvocationExpectation(
        owner.expected.invocation_identity, owner.expected.epoch_identity, os.getpid()
    )
    digest = ContentDigest.of_bytes(b"v3-membership")
    owner.epoch = CatalogPairEpochExpectation(
        invocation, object(), direct_host._HOSTS[host].catalog_digest, digest, digest
    )
    guard = owner.acquire_catalog_epoch_exclusion(owner.parent, expected=invocation)
    try:
        participant = epochs._assemble_code_epoch_participation(
            owner=owner, parent=owner.parent, invocation=invocation,
            epoch_owner=owner, guard=guard,
        )
        _bind_direct_policy_epoch(
            host, participant, owner.current, expected=owner.epoch,
            guard=guard, declaration_source=prepared,
        )
    finally:
        owner.release_catalog_epoch_exclusion(guard)
    return owner, host


def test_v3_original_epoch_admits_selected_policy_and_refuses_changed_source():
    owner, host = registered_epoch()
    admission = direct_host.produce_registry_policy(host, owner.selected)
    policy = direct_host.validate_admitted_registry_policy(host, admission)
    assert len(policy.grants) == 1
    owner.selected_live = False
    with pytest.raises(ContractViolation, match="original selected source unavailable"):
        direct_host.validate_admitted_registry_policy(host, admission)
    direct_host.close_direct_validation_host(host)


def test_v3_selected_policy_accepts_unrelated_observed_v1_module():
    owner, host = registered_epoch(_mixed_closure())
    try:
        policy = direct_host.produce_registry_policy(host, owner.selected)
        admitted = direct_host.validate_admitted_registry_policy(host, policy)
        assert len(admitted.grants) == 1
        assert admitted.declaration_scope_digest == owner.projection.closure_digest
    finally:
        direct_host.close_direct_validation_host(host)


def test_v3_selected_stage_revalidates_after_owner_work():
    owner, host = registered_epoch()
    admission = direct_host.produce_registry_policy(host, owner.selected)
    with _selected_policy_source(host, admission) as (state, closure, policy, binding):
        assert state is direct_host._HOSTS[host]
        assert closure.closure_digest == policy.declaration_scope_digest
        assert binding.expectation.source_identity_digest == policy.grants[0].source_identity_digest
    with pytest.raises(ContractViolation, match="original selected source unavailable"):
        with _selected_policy_source(host, admission):
            owner.selected_live = False
    direct_host.close_direct_validation_host(host)


@pytest.mark.parametrize("stage", ("source_planning", "authority_derivation"))
def test_both_v3_stage_derivations_enter_original_selected_source(stage):
    owner, host = registered_epoch()
    admission = direct_host.produce_registry_policy(host, owner.selected)
    with pytest.raises(TypeError, match="exact retained planning request"):
        _derive_stage(host, admission, object(), object(), object(), stage=stage)
    direct_host.close_direct_validation_host(host)


@pytest.mark.parametrize("stage", ("source_planning", "authority_derivation"))
def test_both_v3_stage_derivations_refuse_revoked_selected_source(stage):
    owner, host = registered_epoch()
    admission = direct_host.produce_registry_policy(host, owner.selected)
    owner.selected_live = False
    with pytest.raises(ContractViolation, match="original selected source unavailable"):
        _derive_stage(host, admission, object(), object(), object(), stage=stage)
    direct_host.close_direct_validation_host(host)


@pytest.mark.parametrize("stage", ("source_planning", "authority_derivation"))
def test_both_v3_stage_calls_keep_source_valid_through_owner_work(
    monkeypatch, stage
):
    owner, host = registered_epoch()
    admission = direct_host.produce_registry_policy(host, owner.selected)
    marker = object()

    def owner_work(state, scope, policy, registration, request, operation, **kwargs):
        assert state is direct_host._HOSTS[host]
        assert scope.closure_digest == policy.declaration_scope_digest
        assert kwargs["stage"] == stage
        return marker

    monkeypatch.setattr(operation_derivation, "_derive_stage_body", owner_work)
    assert _derive_stage(
        host, admission, object(), object(), object(), stage=stage
    ) is marker
    direct_host.close_direct_validation_host(host)

    owner, host = registered_epoch()
    admission = direct_host.produce_registry_policy(host, owner.selected)

    def change_during_owner_work(*args, **kwargs):
        owner.selected_live = False
        return marker

    monkeypatch.setattr(
        operation_derivation, "_derive_stage_body", change_during_owner_work
    )
    with pytest.raises(ContractViolation, match="original selected source unavailable"):
        _derive_stage(host, admission, object(), object(), object(), stage=stage)
    direct_host.close_direct_validation_host(host)


def test_v3_stage_policy_requires_original_selected_source_and_stage_pair():
    owner, host = registered_epoch()
    admission = direct_host.produce_registry_policy(host, owner.selected)
    source = owner.selected_value.expectation.source_identity_digest
    with pytest.raises(ContractViolation, match="retained authority stage"):
        validate_stage_policy_occurrence(host, admission, source)
    direct_host.close_direct_validation_host(host)

    owner, host = registered_epoch()
    admission = direct_host.produce_registry_policy(host, owner.selected)
    source = owner.selected_value.expectation.source_identity_digest
    owner.selected_live = False
    with pytest.raises(ContractViolation, match="original selected source unavailable"):
        validate_stage_policy_occurrence(host, admission, source)
    direct_host.close_direct_validation_host(host)


def test_v3_host_retains_original_reader_entrances_but_has_no_grant():
    owner, host = registered()
    state = direct_host._state(host)
    assert state.source_rail == "declaration_v3"
    assert state.methods["read"].receiver is owner
    assert state.methods["scope"].receiver is owner
    assert state.methods["scope_locked"].receiver is owner
    assert state.methods["selected_read"].receiver is owner
    assert state.methods["selected_validate"].receiver is owner
    assert state.methods["participant_read"].receiver is owner
    assert state.methods["participant_validate"].receiver is owner
    assert state.methods["selected_locked"].receiver is owner
    with pytest.raises(ContractViolation, match="original epoch"):
        direct_host.produce_registry_policy(host, owner.snapshot)
    direct_host.close_direct_validation_host(host)


@pytest.mark.parametrize(
    "name", ("validate_selected_package_source", "validate_selected_participant_view")
)
def test_v3_host_rejects_replaced_original_selected_validator(name):
    owner, host = registered()
    setattr(owner, name, lambda *args, **kwargs: None)
    with pytest.raises(ContractViolation, match="substituted"):
        direct_host._state(host)
    direct_host.close_direct_validation_host(host)


@pytest.mark.parametrize(
    "name", ("check_declaration_scope_locked", "check_selected_package_source_locked")
)
def test_v3_host_rejects_replaced_guarded_entrance(name):
    owner, host = registered()
    setattr(owner, name, lambda *args, **kwargs: None)
    with pytest.raises(ContractViolation, match="substituted"):
        direct_host._state(host)
    direct_host.close_direct_validation_host(host)


def test_v3_context_rejects_old_resources_and_source_mode_substitution():
    owner, host = registered()
    original = owner.expected
    object.__setattr__(original, "source_rail", "existing")
    with pytest.raises(ContractViolation):
        direct_host._state(host)
    direct_host.close_direct_validation_host(host)


def test_v3_declaration_preparation_and_original_guarded_retention():
    owner, host = registered()
    closure = owner.projection
    expectation = CodeDeclarationScopeExpectation(
        closure.repository_binding_ref, "parent", os.getpid(), "operation", "epoch"
    )
    prepared = _prepare_declaration_source(host, owner.snapshot, expectation)
    assert prepared.digest == closure.closure_digest
    guard = owner.acquire_command_publication_guard(
        owner.lifetime, expected=owner.expected
    )
    try:
        _retain_declaration_source_locked(host, prepared, guard)
        _check_declaration_source_locked(host, guard)
        with pytest.raises(ContractViolation, match="preparation unavailable"):
            _retain_declaration_source_locked(host, prepared, guard)
    finally:
        owner.release_command_publication_guard(guard)
    assert _validate_declaration_source(host) is prepared
    direct_host.close_direct_validation_host(host)


def test_v3_declaration_preparation_refuses_foreign_host():
    owner, host = registered()
    other, foreign = registered()
    closure = owner.projection
    expectation = CodeDeclarationScopeExpectation(
        closure.repository_binding_ref, "parent", os.getpid(), "operation", "epoch"
    )
    prepared = _prepare_declaration_source(host, owner.snapshot, expectation)
    guard = other.acquire_command_publication_guard(
        other.lifetime, expected=other.expected
    )
    try:
        with pytest.raises(ContractViolation, match="preparation unavailable"):
            _retain_declaration_source_locked(foreign, prepared, guard)
    finally:
        other.release_command_publication_guard(guard)
    direct_host.close_direct_validation_host(host)
    direct_host.close_direct_validation_host(foreign)


def test_v3_declaration_preparation_cannot_be_copied_or_restamped():
    owner, host = registered()
    closure = owner.projection
    expectation = CodeDeclarationScopeExpectation(
        closure.repository_binding_ref, "parent", os.getpid(), "operation", "epoch"
    )
    prepared = _prepare_declaration_source(host, owner.snapshot, expectation)
    guard = owner.acquire_command_publication_guard(
        owner.lifetime, expected=owner.expected
    )
    try:
        with pytest.raises(ContractViolation, match="preparation unavailable"):
            _retain_declaration_source_locked(host, replace(prepared), guard)
        _retain_declaration_source_locked(host, prepared, guard)
    finally:
        owner.release_command_publication_guard(guard)
    object.__setattr__(prepared, "digest", ContentDigest.of_bytes(b"foreign"))
    with pytest.raises(ContractViolation, match="declaration changed"):
        _validate_declaration_source(host)
    direct_host.close_direct_validation_host(host)


def selected_binding(closure):
    scope = closure.scopes[0]
    package = scope.projection.packages[0]
    source = ContentDigest.of_bytes(b"observed selected package")
    expected = CodeSelectedPackageSourceExpectation(
        CodeDeclarationScopeExpectation(
            closure.repository_binding_ref, "parent", os.getpid(), "operation", "epoch"
        ),
        closure.closure_digest,
        scope.scope_key,
        package.module_id,
        package.package_id,
        package.manifest_relative_path,
        package.manifest.content_digest,
        source,
    )
    return CodeSelectedPackageSourceBinding(
        expected,
        CodeSemanticCandidateListing(
            source,
            (
                CodeSemanticCandidate(
                    package.manifest_relative_path,
                    package.manifest.content_digest,
                ),
            ),
        ),
    )


def test_selected_candidate_joins_only_one_eligible_occurrence():
    closure = declaration_fixture()
    eligibility = calculate_declaration_eligibility(closure)
    binding = selected_binding(closure)
    grant = selected_source_grant_candidate(closure, eligibility, binding)
    row = next(
        row for row in eligibility.packages
        if row.occurrence_key == (
            binding.expectation.scope_key,
            binding.expectation.module_id,
            binding.expectation.package_id,
        )
    )
    assert grant.source_identity_digest == binding.expectation.source_identity_digest
    assert grant.registration_declaration_digest == row.registration_declaration_digest


def test_selected_candidate_refuses_foreign_or_changed_declaration():
    closure = declaration_fixture()
    eligibility = calculate_declaration_eligibility(closure)
    binding = selected_binding(closure)
    for changed in (
        replace(binding.expectation, package_id="foreign"),
        replace(binding.expectation, closure_digest=ContentDigest.of_bytes(b"old")),
    ):
        with pytest.raises(ContractViolation):
            selected_source_grant_candidate(
                closure, eligibility, replace(binding, expectation=changed)
            )
