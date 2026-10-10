"""Mechanics only: fixture owner and factory establish no bootstrap authority."""

import copy
import os
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
    ProviderExecutionBinding,
    SemanticConfigurationCoordinate,
    SemanticContractRuntime,
    SemanticImplementationCoordinate,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.isolated_validation_host import (
    IsolatedWorkspaceOriginProduct,
    IsolatedWorkspaceValidationOrigin,
    bind_isolated_workspace_validation_origin,
    close_isolated_validation_host,
    install_isolated_validation_host,
    require_trusted_validation_origin,
    validate_isolated_workspace_admission,
)
from aware_code_semantic_contract_runtime.retained_admission_interfaces import (
    RetainedSemanticAdmissionExpectation,
)
from test_profile_runtime import DeltaProvider, body_codecs, profile


class Owner:
    def __init__(self):
        self.observation = object()
        self.membership = object()
        self.handle = object()
        self.closed = False
        self.calls = 0
        self.on_call = None

    def make(self):
        return IsolatedWorkspaceOriginProduct(self.observation, self.membership, self)

    def validate_package_context_admission(self, admission, *, expected):
        if self.closed or admission is not self.handle:
            raise ContractViolation("foreign or closed fixture handle")
        self.calls += 1
        if self.on_call:
            self.on_call(expected)

    def validate_declaration_inventory_admission(self, admission, *, expected):
        if self.closed or admission is not self.handle:
            raise ContractViolation("foreign or closed fixture handle")
        self.calls += 1

    def validate_occurrence_assignments(
        self, admission, *, expected, namespace, owned_roots
    ):
        self.validate_package_context_admission(admission, expected=expected)
        if namespace != "home" or owned_roots != ("home:a", "home:b"):
            raise ContractViolation("assignment substitution")


@pytest.fixture
def fixture():
    owner = Owner()
    declaration = profile()
    runtime = SemanticContractRuntime(
        declaration, {"sdk": DeltaProvider()}, body_codecs()
    )
    generation = object()
    host = install_isolated_validation_host(
        runtime=runtime,
        generation_identity=generation,
        observation_runtime=owner.observation,
        membership_runtime=owner.membership,
        factory_owner=owner,
        factory_method="make",
    )
    origin = bind_isolated_workspace_validation_origin(host)
    digest = ContentDigest.of_bytes(b"fixture")
    coordinate = SemanticValueCoordinate(
        "fixture", declaration.inputs[0].contract, "fixture", digest, 7
    )
    expected = RetainedSemanticAdmissionExpectation(
        runtime,
        generation,
        object(),
        os.getpid(),
        object(),
        "source_planning",
        declaration,
        declaration.providers[0],
        ProviderExecutionBinding(
            "sdk",
            SemanticImplementationCoordinate("fixture", digest),
            SemanticConfigurationCoordinate("fixture", digest),
        ),
        SemanticPackageCoordinate("fixture@1", "sdk", digest),
        digest,
        coordinate,
        coordinate,
        coordinate,
        coordinate,
        coordinate,
    )
    return owner, host, origin, expected


def test_repeated_validation_is_not_execution_and_cannot_be_trusted(fixture):
    owner, _, origin, expected = fixture
    for _ in range(2):
        validate_isolated_workspace_admission(
            origin, owner.handle, expected=expected, kind="package_context"
        )
    validate_isolated_workspace_admission(
        origin, owner.handle, expected=expected, kind="declaration_inventory"
    )
    validate_isolated_workspace_admission(
        origin,
        owner.handle,
        expected=expected,
        kind="occurrence_assignments",
        namespace="home",
        owned_roots=("home:a", "home:b"),
    )
    assert owner.calls == 4
    with pytest.raises(ContractViolation, match="trusted bootstrap unavailable"):
        require_trusted_validation_origin(origin)


@pytest.mark.parametrize(
    "change",
    [
        "foreign_handle",
        "generation",
        "runtime",
        "pid",
        "partial_roots",
        "closed_owner",
        "closed_host",
        "copied_origin",
        "factory",
        "method",
    ],
)
def test_rejects_substitution_and_lifetime_changes(fixture, change):
    owner, host, origin, expected = fixture
    handle = owner.handle
    kind = "package_context"
    kwargs = {}
    if change == "foreign_handle":
        handle = object()
    elif change == "generation":
        expected = replace(expected, generation_identity=object())
    elif change == "runtime":
        expected = replace(expected, runtime=object())
    elif change == "pid":
        expected = replace(expected, process_id=os.getpid() + 1)
    elif change == "partial_roots":
        kind = "occurrence_assignments"
        kwargs = {"namespace": "home", "owned_roots": ("home:a",)}
    elif change == "closed_owner":
        owner.closed = True
    elif change == "closed_host":
        close_isolated_validation_host(host)
    elif change == "copied_origin":
        origin = object.__new__(IsolatedWorkspaceValidationOrigin)
    elif change == "factory":
        owner.make = lambda: owner
    else:
        owner.validate_package_context_admission = lambda *a, **k: None
    with pytest.raises((ContractViolation, TypeError)):
        validate_isolated_workspace_admission(
            origin, handle, expected=expected, kind=kind, **kwargs
        )


def test_copy_and_rebinding_refuse(fixture):
    _, host, origin, _ = fixture
    with pytest.raises(TypeError):
        copy.copy(origin)
    with pytest.raises(TypeError):
        copy.deepcopy(host)
    with pytest.raises(ContractViolation):
        bind_isolated_workspace_validation_origin(host)


def test_post_call_context_and_host_change_refuse(fixture):
    owner, host, origin, expected = fixture
    owner.on_call = lambda _: close_isolated_validation_host(host)
    with pytest.raises(ContractViolation):
        validate_isolated_workspace_admission(
            origin, owner.handle, expected=expected, kind="package_context"
        )


def test_expected_mutation_refuses(fixture):
    owner, _, origin, expected = fixture
    owner.on_call = lambda value: object.__setattr__(
        value, "operation_identity", object()
    )
    with pytest.raises(ContractViolation, match="changed during"):
        validate_isolated_workspace_admission(
            origin, owner.handle, expected=expected, kind="package_context"
        )


def test_factory_cannot_substitute_original_context(fixture):
    owner, _, _, expected = fixture
    host = install_isolated_validation_host(
        runtime=expected.runtime,
        generation_identity=expected.generation_identity,
        observation_runtime=object(),
        membership_runtime=owner.membership,
        factory_owner=owner,
        factory_method="make",
    )
    with pytest.raises(ContractViolation, match="substituted"):
        bind_isolated_workspace_validation_origin(host)


@pytest.mark.skipif(not hasattr(os, "fork"), reason="requires process fork")
def test_inherited_host_refuses_in_child(fixture):
    owner, _, origin, expected = fixture
    pid = os.fork()
    if pid == 0:
        try:
            validate_isolated_workspace_admission(origin, owner.handle, expected=expected, kind="package_context")
        except ContractViolation:
            os._exit(0)
        except BaseException:  # noqa: BLE001 - child must exit without running parent tests
            os._exit(2)
        os._exit(1)
    _, status = os.waitpid(pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
