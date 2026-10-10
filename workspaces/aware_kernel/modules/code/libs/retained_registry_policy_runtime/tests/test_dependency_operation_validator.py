"""Real Code demand/validator mechanics, fixture owner; no Workspace admission claim."""

import copy
from dataclasses import replace
from types import MethodType

import pytest
import test_planning_execution as planning_fixture
from aware_code_retained_registry_policy_runtime import (
    dependency_admission_origin as consumer,
)
from aware_code_retained_registry_policy_runtime import (
    dependency_operation_validator as validation,
)
from aware_code_retained_registry_policy_runtime import direct_host as hosts
from aware_code_retained_registry_policy_runtime import operation_context as contexts
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    dependency_product_input_body,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticDependencyProductInput,
)
from test_retained_demand_operation import execute, fixture


class OwnerFixture(planning_fixture.FixtureIssuer):
    """Fixture-issued handles behind an original host resource, not real resolution."""

    def issue_dependency_case(self, code_validator, operation, expected, body):
        code_validator.validate_retained_dependency_operation(
            operation, expected=expected
        )
        self.dep_expected = expected
        self.dep_body = body
        self.dep_resolution = object()
        self.dep_fulfillment = object()
        self.calls = []
        self.hook = None
        self.result = None

    def validate_dependency_resolution_admission(self, admission, *, expected):
        self.calls.append("resolution")
        if admission is not self.dep_resolution:
            raise ContractViolation("foreign owner resolution")
        validation._compare(expected, self.dep_expected)
        if self.hook:
            self.hook("resolution", expected)
        return self.result

    def validate_dependency_fulfillment_admission(
        self, admission, *, resolution_admission, expected
    ):
        self.calls.append("fulfillment")
        if (
            admission is not self.dep_fulfillment
            or resolution_admission is not self.dep_resolution
        ):
            raise ContractViolation("foreign owner fulfillment/resolution")
        validation._compare(expected.resolution, self.dep_expected)
        if expected.dependency_products_coordinate != self.dep_body.coordinate:
            raise ContractViolation("foreign owner product body")
        if dependency_product_input_body(expected.dependency_products) != self.dep_body:
            raise ContractViolation("foreign owner products")
        if self.hook:
            self.hook("fulfillment", expected)
        return self.result


@pytest.fixture(scope="module")
def case():
    patch = pytest.MonkeyPatch()
    patch.setattr(planning_fixture, "FixtureIssuer", OwnerFixture)
    values, _, source, context, planner, _ = fixture(patch)
    operation = execute(source, context)
    validator = validation.retained_dependency_operation_validator(values[1])
    expected = validator.expectation(operation)
    products = SemanticDependencyProductInput(
        expected.planning_input.package,
        expected.planning_input.source_identity_digest,
        tuple(
            (d.dependency_kind, d.dependency_ref)
            for d in expected.planning_input.dependencies
        ),
        expected.demand_set,
        (),
        expected.planning_context.code_intent,
    )
    body = dependency_product_input_body(products)
    owner = next(
        r.resource for r in values[0].expected.resources if r.role == "semantic_issuer"
    )
    owner.issue_dependency_case(validator, operation, expected, body)
    origin = consumer.assemble_dependency_admission_consumer(values[1])
    try:
        yield (
            values,
            operation,
            validator,
            expected,
            products,
            body,
            owner,
            origin,
            planner,
        )
    finally:
        hosts.close_direct_validation_host(values[1])
        patch.undo()


def test_original_expectation_and_repeat_validation(case):
    values, operation, validator, expected, _, _, _, _, planner = case
    assert validation.retained_dependency_operation_validator(values[1]) is validator
    detached = validator.expectation(operation)
    assert detached is not expected
    assert detached.planning_input is not expected.planning_input
    assert detached.demand_operation_identity is operation
    assert detached.source_planning.runtime is expected.source_planning.runtime
    validator.validate_retained_dependency_operation(operation, expected=detached)
    assert planner.calls == 1
    with pytest.raises(TypeError):
        copy.copy(validator)
    with pytest.raises(ContractViolation):
        object.__new__(type(validator)).validate_retained_dependency_operation(
            operation, expected=expected
        )


@pytest.mark.parametrize(
    "field",
    [
        "parent_identity",
        "epoch_identity",
        "demand_operation_identity",
        "source_planning",
        "planning_input",
        "profile",
    ],
)
def test_copied_or_changed_expectation_cannot_grant_authority(case, field):
    _, operation, validator, expected, _, _, _, _, planner = case
    value = object()
    if field == "source_planning":
        value = replace(expected.source_planning, stage="authority_derivation")
    elif field == "profile":

        class ForeignProfile:
            def __eq__(self, other):
                raise AssertionError("caller equality must not execute")

        field = "source_planning"
        value = replace(expected.source_planning, profile=ForeignProfile())
    elif field == "planning_input":
        value = replace(
            expected.planning_input,
            source_identity_digest=ContentDigest.of_bytes(b"foreign"),
        )
    with pytest.raises((ContractViolation, TypeError)):
        validator.validate_retained_dependency_operation(
            operation, expected=replace(expected, **{field: value})
        )
    assert planner.calls == 1


def test_empty_products_require_complete_original_owner_fulfillment(case):
    values, op, _, _, _, body, owner, origin, _ = case
    assert consumer.assemble_dependency_admission_consumer(values[1]) is origin
    owner.calls.clear()
    assert (
        origin.validate_dependency_products(
            op, owner.dep_resolution, owner.dep_fulfillment, body=body
        )
        is None
    )
    assert owner.calls == ["fulfillment"]


def test_product_validation_coalesces_synchronous_code_callbacks(case):
    _, op, _, _, _, body, owner, origin, _ = case

    class Probe:
        def __init__(self):
            self.counts = {}

        def record(self, *, kind, name, amount=1, **_fields):
            if kind == "counter":
                self.counts[name] = self.counts.get(name, 0) + amount

    probe = Probe()
    token = contexts.set_performance_probe(probe)
    try:
        origin.validate_dependency_products(
            op, owner.dep_resolution, owner.dep_fulfillment, body=body
        )
    finally:
        contexts.reset_performance_probe(token)
    assert probe.counts["code.demand_validation_complete"] == 2
    assert probe.counts["code.demand_validation_nominal"] == 2
    assert probe.counts["code.source_context_validation_complete"] == 2
    assert probe.counts["code.source_context_validation_nominal"] == 4


def test_changed_declaration_keys_refuse_before_owner_contact(case):
    _, op, _, _, products, _, owner, origin, _ = case
    body = dependency_product_input_body(
        replace(products, declared_dependencies=(("module", "invented"),))
    )
    owner.calls.clear()
    with pytest.raises(ContractViolation, match="original Code demand"):
        origin.validate_dependency_products(
            op, owner.dep_resolution, owner.dep_fulfillment, body=body
        )
    assert owner.calls == []


def test_original_owner_method_substitution_rejects_before_contact(case, monkeypatch):
    _, op, _, _, _, body, owner, origin, _ = case
    calls = []

    def fake(self, admission, *, expected):
        calls.append(admission)

    with monkeypatch.context() as patch:
        patch.setattr(
            owner, "validate_dependency_resolution_admission", MethodType(fake, owner)
        )
        with pytest.raises(ContractViolation, match="substituted"):
            origin.validate_dependency_products(
                op, owner.dep_resolution, owner.dep_fulfillment, body=body
            )
    # MonkeyPatch restores a bound method on the instance. Remove that shadow
    # so subsequent cases see the exact original inherited descriptor.
    del owner.__dict__["validate_dependency_resolution_admission"]
    assert calls == []


@pytest.mark.parametrize("kind", ["fulfillment"])
def test_foreign_owner_handle_is_not_portable_agreement(case, kind):
    _, op, _, _, _, body, owner, origin, _ = case
    owner.calls.clear()
    resolution = object() if kind == "resolution" else owner.dep_resolution
    fulfillment = object() if kind == "fulfillment" else owner.dep_fulfillment
    with pytest.raises(ContractViolation, match="foreign owner"):
        origin.validate_dependency_products(op, resolution, fulfillment, body=body)
    assert owner.calls == ["fulfillment"]


def test_non_none_owner_validation_refuses(case):
    _, op, _, _, _, body, owner, origin, _ = case
    owner.calls.clear()
    owner.result = False
    try:
        with pytest.raises(ContractViolation, match="non-None"):
            origin.validate_dependency_products(
                op, owner.dep_resolution, owner.dep_fulfillment, body=body
            )
        assert owner.calls == ["fulfillment"]
    finally:
        owner.result = None


def test_owner_cannot_change_expected_source_during_validation(case):
    _, op, _, _, _, body, owner, origin, _ = case

    def mutate(stage, expected):
        if stage == "fulfillment":
            object.__setattr__(
                expected.resolution.source_planning, "stage", "authority_derivation"
            )

    owner.calls.clear()
    owner.hook = mutate
    try:
        with pytest.raises(ContractViolation, match="source-planning"):
            origin.validate_dependency_products(
                op, owner.dep_resolution, owner.dep_fulfillment, body=body
            )
        assert owner.calls == ["fulfillment"]
    finally:
        owner.hook = None


def test_changed_product_coordinate_after_owner_validation_rejects(case):
    _, op, _, _, _, body, owner, origin, _ = case

    def mutate(stage, expected):
        if stage == "fulfillment":
            object.__setattr__(
                expected,
                "dependency_products_coordinate",
                replace(expected.dependency_products_coordinate, value_ref="foreign"),
            )

    owner.hook = mutate
    try:
        with pytest.raises(ContractViolation, match="closure changed"):
            origin.validate_dependency_products(
                op, owner.dep_resolution, owner.dep_fulfillment, body=body
            )
    finally:
        owner.hook = None


def test_fork_refuses_before_original_owner_contact(case, monkeypatch):
    import os

    _, op, validator, expected, _, body, owner, origin, _ = case
    owner.calls.clear()
    pid = os.getpid()
    with monkeypatch.context() as patch:
        patch.setattr(os, "getpid", lambda: pid + 1)
        with pytest.raises(ContractViolation, match="process"):
            validator.validate_retained_dependency_operation(op, expected=expected)
        with pytest.raises(ContractViolation, match="process"):
            origin.validate_dependency_products(
                op, owner.dep_resolution, owner.dep_fulfillment, body=body
            )
    assert owner.calls == []


def test_admitted_products_revalidate_and_detach(case):
    _, op, _, _, _, body, owner, origin, planner = case
    admitted = origin.admit_dependency_products(
        op, owner.dep_resolution, owner.dep_fulfillment, body=body
    )
    assert type(admitted) is consumer.AdmittedDependencyProducts
    owner.calls.clear()
    first = admitted.read_products()
    assert first == body and first is not body
    assert owner.calls == ["fulfillment"]
    object.__setattr__(first.coordinate, "value_ref", "changed-detached-copy")
    assert admitted.read_products() == body
    assert planner.calls == 1
    with pytest.raises(TypeError):
        copy.copy(admitted)
    with pytest.raises(ContractViolation, match="foreign admitted"):
        object.__new__(consumer.AdmittedDependencyProducts).read_products()


def test_retention_does_not_preserve_expired_owner_evidence(case):
    _, op, _, _, _, body, owner, origin, _ = case
    admitted = origin.admit_dependency_products(
        op, owner.dep_resolution, owner.dep_fulfillment, body=body
    )
    original = owner.dep_fulfillment
    owner.dep_fulfillment = object()
    try:
        with pytest.raises(ContractViolation, match="foreign owner"):
            admitted.read_products()
    finally:
        owner.dep_fulfillment = original


def test_failed_postvalidation_retains_no_products(case):
    _, op, _, _, _, body, owner, origin, _ = case
    count = len(consumer._PRODUCTS)

    def mutate(stage, expected):
        if stage == "fulfillment":
            object.__setattr__(
                expected.dependency_products_coordinate, "value_ref", "changed"
            )

    owner.hook = mutate
    try:
        with pytest.raises(ContractViolation, match="closure changed"):
            origin.admit_dependency_products(
                op, owner.dep_resolution, owner.dep_fulfillment, body=body
            )
        assert len(consumer._PRODUCTS) == count
    finally:
        owner.hook = None


def test_product_reader_substitution_and_fork_reject(case, monkeypatch):
    import os

    _, op, _, _, _, body, owner, origin, _ = case
    admitted = origin.admit_dependency_products(
        op, owner.dep_resolution, owner.dep_fulfillment, body=body
    )
    owner.calls.clear()
    original = consumer.AdmittedDependencyProducts.read_products
    with monkeypatch.context() as patch:
        patch.setattr(
            consumer.AdmittedDependencyProducts, "read_products", lambda s: body
        )
        with pytest.raises(ContractViolation, match="reader substituted"):
            original(admitted)
    pid = os.getpid()
    with monkeypatch.context() as patch:
        patch.setattr(os, "getpid", lambda: pid + 1)
        with pytest.raises(ContractViolation, match="process"):
            admitted.read_products()
    assert owner.calls == []


def test_close_prevents_further_owner_contact(case):
    values, op, validator, expected, _, body, owner, origin, _ = case
    admitted = origin.admit_dependency_products(
        op, owner.dep_resolution, owner.dep_fulfillment, body=body
    )
    count = len(consumer._PRODUCTS)

    def close_during_fulfillment(stage, expected):
        if stage == "fulfillment":
            hosts.close_direct_validation_host(values[1])

    owner.hook = close_during_fulfillment
    try:
        with pytest.raises(ContractViolation):
            origin.admit_dependency_products(
                op, owner.dep_resolution, owner.dep_fulfillment, body=body
            )
        assert len(consumer._PRODUCTS) == count
    finally:
        owner.hook = None
    owner.calls.clear()
    with pytest.raises(ContractViolation):
        admitted.read_products()
    with pytest.raises(ContractViolation):
        validator.validate_retained_dependency_operation(op, expected=expected)
    with pytest.raises(ContractViolation):
        origin.validate_dependency_products(
            op, owner.dep_resolution, owner.dep_fulfillment, body=body
        )
    assert owner.calls == []
