"""Internal Code mechanics with isolated original-owner fixtures, not application trust."""

import copy
import os
from dataclasses import replace
from threading import RLock

import pytest
from aware_code_retained_registry_policy_runtime import direct_host as host
from aware_code_retained_registry_policy_runtime.calculation import (
    calculate_registry_policy,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticImplementationCoordinate,
)
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    RESOURCE_ROLES,
    DirectCommandExpectedContext,
    DirectCommandResourceBinding,
    DirectWorkspaceOriginProduct,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticContractCatalog,
    CodeSemanticMaterializationProfileBinding,
    _issue_code_semantic_contract_catalog,
)
from aware_code_semantic_contract_runtime.profile import (
    SemanticContractProfileDeclaration,
)
from aware_code_semantic_contract_runtime.runtime import SemanticContractRuntime
from test_calculation import fixture as source_fixture
from test_materialization_catalog import _execution_closure
from test_profile_runtime import DeltaProvider, body_codecs, profile


class Owner:
    def __init__(self, projection):
        self.projection = projection
        self.snapshot = object()
        self.lifetime = object()
        self.expected = None
        self.live = True
        self.catalog_live = True
        self.lock = RLock()
        self.guard = None
        self.close_on_acquire = False

    def validate_command_lifetime(self, lifetime, *, expected):
        if (
            not self.live
            or lifetime is not self.lifetime
            or expected is not self.expected
        ):
            raise ContractViolation("owner lifetime unavailable")

    def create_direct_semantic_origin(self, lifetime):
        return DirectWorkspaceOriginProduct(lifetime, self.expected)

    def validate_complete_scope_projection(self, snapshot, *, projection_digest=None):
        if snapshot is not self.snapshot:
            raise ContractViolation("foreign snapshot")
        if (
            projection_digest is not None
            and projection_digest != self.projection.projection_digest
        ):
            raise ContractViolation("scope moved")

    def read_complete_scope_projection(self, snapshot):
        self.validate_complete_scope_projection(snapshot)
        return self.projection

    def acquire_command_publication_guard(self, lifetime, *, expected):
        if self.close_on_acquire:
            self.live = False
        self.validate_command_lifetime(lifetime, expected=expected)
        self.lock.acquire()
        self.guard = object()
        return self.guard

    def validate_command_publication_guard(self, guard, *, lifetime, expected):
        self.validate_command_lifetime(lifetime, expected=expected)
        assert guard is self.guard

    def release_command_publication_guard(self, guard):
        assert guard is self.guard
        self.guard = None
        self.lock.release()


def assembly():
    projection, catalog = source_fixture()
    owner = Owner(projection)
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
    resources = {key: object() for key in RESOURCE_ROLES}
    resources.update(
        catalog=admission,
        code_runtime=runtime,
        composition_factory=owner,
        lifetime_runtime=owner,
        scope_adapter=owner,
        policy_producer=calculate_registry_policy,
    )
    digest = ContentDigest.of_bytes(b"isolated-source-coordinate")
    owner.expected = DirectCommandExpectedContext(
        object(),
        object(),
        os.getpid(),
        runtime,
        admission,
        SemanticImplementationCoordinate("composition", digest),
        SemanticConfigurationCoordinate("composition", digest),
        SemanticImplementationCoordinate("policy", digest),
        SemanticConfigurationCoordinate("policy", digest),
        tuple(
            DirectCommandResourceBinding(key, resources[key], "borrowed")
            for key in RESOURCE_ROLES
        ),
    )
    bootstrap = host._assemble_direct_command_bootstrap(
        lifetime=owner.lifetime, expected=owner.expected
    )
    return owner, bootstrap


def registered():
    owner, bootstrap = assembly()
    return owner, host.register_direct_workspace_origin(bootstrap, owner.lifetime)


def test_policy_retained_and_parent_close_refuses():
    owner, direct = registered()
    policy = host.produce_registry_policy(direct, owner.snapshot)
    value = host.validate_admitted_registry_policy(direct, policy)
    assert len(value.grants) == 1
    assert owner.guard is None
    owner.live = False
    with pytest.raises(ContractViolation):
        host.validate_admitted_registry_policy(direct, policy)
    host.close_direct_validation_host(direct)


def test_registration_and_bootstrap_replay_reject():
    owner, bootstrap = assembly()
    direct = host.register_direct_workspace_origin(bootstrap, owner.lifetime)
    with pytest.raises(ContractViolation):
        host.register_direct_workspace_origin(bootstrap, owner.lifetime)
    with pytest.raises(ContractViolation):
        host._assemble_direct_command_bootstrap(
            lifetime=owner.lifetime, expected=owner.expected
        )
    host.close_direct_validation_host(direct)


def test_failed_registration_consumes_slot():
    owner, bootstrap = assembly()
    with pytest.raises(ContractViolation):
        host.register_direct_workspace_origin(bootstrap, object())
    with pytest.raises(ContractViolation):
        host.register_direct_workspace_origin(bootstrap, owner.lifetime)


@pytest.mark.parametrize(
    "method",
    [
        "create_direct_semantic_origin",
        "validate_command_lifetime",
        "read_complete_scope_projection",
        "validate_complete_scope_projection",
    ],
)
def test_original_method_substitution_rejects(method):
    owner, bootstrap = assembly()
    setattr(owner, method, lambda *a, **kw: None)
    with pytest.raises(ContractViolation, match="substituted"):
        host.register_direct_workspace_origin(bootstrap, owner.lifetime)


def test_close_wins_publication():
    owner, direct = registered()
    owner.close_on_acquire = True
    with pytest.raises(ContractViolation):
        host.produce_registry_policy(direct, owner.snapshot)
    assert owner.guard is None
    host.close_direct_validation_host(direct)


def test_scope_change_invalidates_policy():
    owner, direct = registered()
    policy = host.produce_registry_policy(direct, owner.snapshot)
    owner.projection = replace(owner.projection, repository_binding_ref="substituted")
    with pytest.raises(ContractViolation, match="scope moved"):
        host.validate_admitted_registry_policy(direct, policy)
    host.close_direct_validation_host(direct)


def test_catalog_revocation_invalidates_policy():
    owner, direct = registered()
    policy = host.produce_registry_policy(direct, owner.snapshot)
    owner.catalog_live = False
    with pytest.raises(ContractViolation):
        host.validate_admitted_registry_policy(direct, policy)
    host.close_direct_validation_host(direct)


def test_context_coordinate_substitution_rejects():
    owner, direct = registered()
    object.__setattr__(
        owner.expected,
        "policy_configuration",
        SemanticConfigurationCoordinate("other", ContentDigest.of_bytes(b"other")),
    )
    with pytest.raises(ContractViolation, match="configuration"):
        host.produce_registry_policy(direct, owner.snapshot)
    host.close_direct_validation_host(direct)


def test_foreign_and_copied_handles_reject():
    owner, direct = registered()
    policy = host.produce_registry_policy(direct, owner.snapshot)
    for value in (direct, policy):
        with pytest.raises(TypeError):
            copy.copy(value)
    with pytest.raises(ContractViolation):
        host.validate_admitted_registry_policy(
            direct, object.__new__(host.AdmittedRegistryPolicy)
        )
    host.close_direct_validation_host(direct)


def test_guard_failure_releases(monkeypatch):
    owner, direct = registered()
    state = host._HOSTS[direct]
    original = state.check
    calls = 0

    def failure_after_guard(*, read_catalog=True):
        nonlocal calls
        calls += 1
        if owner.guard is not None:
            raise RuntimeError("final validation failed")
        return original(read_catalog=read_catalog)

    monkeypatch.setattr(state, "check", failure_after_guard)
    with pytest.raises(RuntimeError, match="final validation"):
        host.produce_registry_policy(direct, owner.snapshot)
    assert owner.guard is None
    host.close_direct_validation_host(direct)


def test_cross_host_policy_and_explicit_close_reject():
    owner, first = registered()
    _, second = registered()
    policy = host.produce_registry_policy(first, owner.snapshot)
    with pytest.raises(ContractViolation, match="foreign"):
        host.validate_admitted_registry_policy(second, policy)
    host.close_direct_validation_host(first)
    with pytest.raises(ContractViolation):
        host.validate_admitted_registry_policy(first, policy)
    host.close_direct_validation_host(second)


def test_fork_pid_change_refuses_without_closing_parent(monkeypatch):
    owner, direct = registered()
    pid = os.getpid()
    with monkeypatch.context() as patch:
        patch.setattr(host.os, "getpid", lambda: pid + 1)
        with pytest.raises(ContractViolation):
            host.produce_registry_policy(direct, owner.snapshot)
    policy = host.produce_registry_policy(direct, owner.snapshot)
    assert host.validate_admitted_registry_policy(direct, policy).grants
    host.close_direct_validation_host(direct)


def test_foreign_two_stage_expectation_cannot_enter_bootstrap():
    from test_direct_origin_interfaces import two_stage_context

    with pytest.raises(ContractViolation, match="foreign stage context process"):
        host._assemble_direct_command_bootstrap(
            lifetime=object(), expected=two_stage_context()
        )


def test_source_only_state_cannot_ignore_added_stage_bindings():
    import os

    from test_direct_origin_interfaces import two_stage_context

    # No nominal host is minted. Exercise the early refusal before the old
    # state implementation can ignore fields or contact any owner method.
    state = object.__new__(host._State)
    state.pid = os.getpid()
    state.closed = False
    state.expected = two_stage_context()
    with pytest.raises(ContractViolation, match="original stage retention unavailable"):
        state.check()


def test_checks_reuse_original_resolver_but_detach_each_catalog(monkeypatch):
    owner, direct = registered()
    state = host._state(direct)
    original = state.catalog_resolver
    constructions = []
    constructor = host.CodeSemanticContractCatalogResolver.__init__

    def counted(self, admission):
        constructions.append(admission)
        constructor(self, admission)

    monkeypatch.setattr(host.CodeSemanticContractCatalogResolver, "__init__", counted)
    try:
        first = state.check()
        object.__setattr__(first.entries[0].profile_declaration, "version", "foreign")
        second = state.check()
        assert second.entries[0].profile_declaration.version != "foreign"
        assert first is not second and state.catalog_resolver is original
        assert constructions == []
        owner.catalog_live = False
        with pytest.raises(ContractViolation):
            state.check()
    finally:
        host.close_direct_validation_host(direct)


def test_reused_resolver_rejects_foreign_admission():
    _, direct = registered()
    _, foreign = registered()
    state = host._state(direct)
    state.catalog_resolver = host._state(foreign).catalog_resolver
    try:
        with pytest.raises(ContractViolation, match="resolver substituted"):
            state.check()
    finally:
        host.close_direct_validation_host(direct)
        host.close_direct_validation_host(foreign)


def test_validation_only_check_constructs_no_snapshot(monkeypatch):
    from aware_code_semantic_contract_runtime import materialization_catalog as catalogs

    owner, direct = registered()
    state = host._state(direct)

    def forbidden(*args, **kwargs):
        raise AssertionError("validation must not export a snapshot")

    monkeypatch.setattr(catalogs, "_detached_catalog_snapshot", forbidden)
    try:
        assert host._state(direct) is state
        assert state.check(read_catalog=False) is None
        owner.catalog_live = False
        with pytest.raises(ContractViolation):
            state.check(read_catalog=False)
    finally:
        host.close_direct_validation_host(direct)


def test_validation_only_check_does_not_reconstruct_catalog_payload(monkeypatch):
    owner, direct = registered()
    state = host._state(direct)

    def forbidden(*args, **kwargs):
        raise AssertionError("retained coordinate check must not rebuild catalog")

    monkeypatch.setattr(CodeSemanticContractCatalog, "__post_init__", forbidden)
    monkeypatch.setattr(
        CodeSemanticMaterializationProfileBinding, "__post_init__", forbidden
    )
    try:
        assert state.check(read_catalog=False) is None
        owner.catalog_live = False
        with pytest.raises(ContractViolation):
            state.check(read_catalog=False)
    finally:
        host.close_direct_validation_host(direct)


def test_validation_only_check_still_rejects_catalog_content_mutation():
    _, direct = registered()
    state = host._state(direct)
    object.__setattr__(
        state.catalog_resolver._catalog.entries[0].profile_declaration,
        "version",
        "changed",
    )
    try:
        with pytest.raises(ContractViolation):
            state.check(read_catalog=False)
    finally:
        host.close_direct_validation_host(direct)


def test_validation_only_check_rejects_equal_copied_nested_tuple():
    from aware_code_semantic_contract_runtime import materialization_catalog as catalogs

    def retains_identity(coordinate, target):
        if type(coordinate) is catalogs._RetainedScalarCoordinate:
            return coordinate.value is target
        if type(coordinate) is catalogs._RetainedTupleCoordinate:
            return coordinate.value is target or any(
                retains_identity(item, target) for item in coordinate.items
            )
        if type(coordinate) is catalogs._RetainedObjectCoordinate:
            return coordinate.value is target or any(
                retains_identity(item, target) for item in coordinate.fields
            )
        raise AssertionError("unexpected retained coordinate node")

    _, direct = registered()
    state = host._state(direct)
    provider = state.catalog_resolver._catalog.entries[0].profile_declaration.providers[
        0
    ]
    original = provider.package_kinds
    copied = (*original,)
    assert copied == original and copied is not original
    assert retains_identity(
        state.catalog_resolver._retained_catalog_coordinate, original
    )
    object.__setattr__(provider, "package_kinds", copied)
    del original
    try:
        with pytest.raises(ContractViolation, match="tuple identity changed"):
            state.check(read_catalog=False)
    finally:
        host.close_direct_validation_host(direct)


def test_validation_only_check_rejects_hostile_nested_class_without_behavior():
    calls = []

    class HostileMeta(type):
        def __instancecheck__(cls, instance):
            calls.append("instancecheck")
            raise AssertionError("hostile instance check invoked")

    class Hostile(metaclass=HostileMeta):
        def __getattribute__(self, name):
            calls.append(f"get:{name}")
            raise AssertionError("hostile attribute invoked")

        def __eq__(self, other):
            calls.append("equal")
            raise AssertionError("hostile equality invoked")

    _, direct = registered()
    state = host._state(direct)
    binding = state.catalog_resolver._catalog.entries[0]
    original = binding.profile_declaration
    object.__setattr__(binding, "profile_declaration", Hostile())
    try:
        with pytest.raises(TypeError, match="exact SemanticContractProfile"):
            state.check(read_catalog=False)
        assert calls == []
    finally:
        object.__setattr__(binding, "profile_declaration", original)
        host.close_direct_validation_host(direct)


def test_validation_only_check_rejects_hostile_descriptor_without_invocation(
    monkeypatch,
):
    calls = []

    class HostileDescriptor:
        def __get__(self, instance, owner=None):
            calls.append("get")
            raise AssertionError("hostile descriptor invoked")

        def __set__(self, instance, value):
            calls.append("set")
            raise AssertionError("hostile descriptor invoked")

    _, direct = registered()
    state = host._state(direct)
    monkeypatch.setattr(
        SemanticContractProfileDeclaration, "version", HostileDescriptor()
    )
    try:
        with pytest.raises(ContractViolation, match="descriptor substituted"):
            state.check(read_catalog=False)
        assert calls == []
    finally:
        host.close_direct_validation_host(direct)
