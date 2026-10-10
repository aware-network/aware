from __future__ import annotations

import copy
import os
from dataclasses import replace
from threading import Thread

import pytest

from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.dependency_admission_interfaces import (
    RetainedDependencyFulfillmentExpectation,
    RetainedDependencyResolutionExpectation,
)
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    dependency_product_input_body,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputJoinedProducerDeclaration,
    SemanticInputJoinedProductionInput,
    SemanticInputPredecessorBody,
    SemanticDependencyInputProducerDeclaration,
    SemanticDependencyInputProductionExpectation,
    SemanticDependencyInputProductionInput,
    SemanticInputDependencyContract,
    SemanticInputProducerDeclaration,
    SemanticInputProducerHost,
    SemanticInputPackageIdentity,
    SemanticInputProductionInput,
    SemanticInputProductionExpectation,
    SemanticInputRoleJoinPredecessor,
    SemanticInputSourceBody,
    SemanticInputSourceContract,
    SemanticInputSourceCoordinate,
    close_dependency_semantic_input_producer_registration,
    close_semantic_input_role_join,
    close_semantic_input_producer_registration,
    execute_registered_dependency_semantic_input,
    execute_registered_joined_semantic_input,
    execute_registered_semantic_input,
    open_semantic_input_role_join,
    register_dependency_semantic_input_producer,
    register_joined_semantic_input_producer,
    register_semantic_input_producer,
)
from test_dependency_inputs import product_input


def _digest(label: str) -> ContentDigest:
    return ContentDigest.of_bytes(label.encode())


_CONTRACT = SemanticContractRef("example.input.v1", "1", _digest("schema"))
_SOURCE_CONTRACT = SemanticContractRef("example.source.v1", "1", _digest("s"))
_PACKAGE_IDENTITY = SemanticInputPackageIdentity(
    SemanticPackageCoordinate("package:example@1", "api", _digest("manifest")),
    "example",
)
_DECLARATION = SemanticInputProducerDeclaration(
    "example.owner.input",
    "example.owner.profile.v1",
    SemanticImplementationCoordinate("example-owner@1/input", _digest("impl")),
    SemanticConfigurationCoordinate("example.owner.config.v1", _digest("config")),
    (SemanticInputSourceContract("source", _SOURCE_CONTRACT),),
    "owner_input",
    _CONTRACT,
)


class _SourceValidator:
    def __init__(self, source: object, operation: object) -> None:
        self.source = source
        self.operation = operation
        self.live = True
        self.calls = 0

    def validate_semantic_input_source(
        self,
        source_admission: object,
        *,
        expected: SemanticInputProductionExpectation,
    ) -> None:
        self.calls += 1
        if (
            not self.live
            or source_admission is not self.source
            or expected.source_identity is not self.source
            or expected.operation_identity is not self.operation
        ):
            raise ContractViolation("source unavailable")

    def read_semantic_input_sources(
        self,
        source_admission: object,
        *,
        expected: SemanticInputProductionExpectation,
    ) -> tuple[SemanticInputSourceBody, ...]:
        self.validate_semantic_input_source(source_admission, expected=expected)
        return tuple(
            SemanticInputSourceBody(
                SemanticInputSourceCoordinate(
                    source.relative_path, replace(source.coordinate)
                ),
                b"source-body",
            )
            for source in expected.source_coordinates
        )


def _expectation(
    operation: object, source: object, *, use_ref: str = "use-1"
) -> SemanticInputProductionExpectation:
    coordinate = SemanticValueCoordinate(
        "source", _SOURCE_CONTRACT,
        "cas://source", _digest("source-body"), len(b"source-body")
    )
    return SemanticInputProductionExpectation.create(
        use_ref=use_ref,
        operation_ref="operation-1",
        stage="definition_request",
        package_identity=_PACKAGE_IDENTITY,
        operation_identity=operation,
        source_identity=source,
        source_coordinates=(
            SemanticInputSourceCoordinate("bindings/source.aware", coordinate),
        ),
    )


def _body(payload: bytes = b"result") -> SemanticBody:
    return SemanticBody(
        SemanticValueCoordinate(
            "owner_input",
            _CONTRACT,
            "cas://result",
            ContentDigest.of_bytes(payload),
            len(payload),
        ),
        payload,
    )


@pytest.mark.asyncio
async def test_original_validator_wraps_awaited_owner_call_and_use_is_single_shot():
    host = SemanticInputProducerHost()
    source, operation = object(), object()
    validator = _SourceValidator(source, operation)
    calls: list[object] = []

    async def produce(production_input):
        assert type(production_input) is SemanticInputProductionInput
        assert production_input.package_identity == _PACKAGE_IDENTITY
        calls.extend(
            (production_input.sources[0].canonical_body, production_input.stage)
        )
        return _body()

    registration = register_semantic_input_producer(
        host,
        declaration=_DECLARATION,
        producer=produce,
        validator=validator,
        validator_entrance=validator.validate_semantic_input_source,
        reader=validator,
        reader_entrance=validator.read_semantic_input_sources,
    )
    expected = _expectation(operation, source)
    result = await execute_registered_semantic_input(
        host, registration, source_admission=source, expected=expected
    )
    assert result == _body()
    assert calls == [b"source-body", "definition_request"]
    assert validator.calls == 3
    with pytest.raises(ContractViolation, match="already consumed"):
        await execute_registered_semantic_input(
            host, registration, source_admission=source, expected=expected
        )


@pytest.mark.asyncio
async def test_post_validation_rejects_source_revocation():
    host = SemanticInputProducerHost()
    source, operation = object(), object()
    validator = _SourceValidator(source, operation)

    def produce(_production_input):
        validator.live = False
        return _body()

    registration = register_semantic_input_producer(
        host,
        declaration=_DECLARATION,
        producer=produce,
        validator=validator,
        validator_entrance=validator.validate_semantic_input_source,
        reader=validator,
        reader_entrance=validator.read_semantic_input_sources,
    )
    with pytest.raises(ContractViolation, match="source unavailable"):
        await execute_registered_semantic_input(
            host,
            registration,
            source_admission=source,
            expected=_expectation(operation, source),
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["role", "contract", "body", "return"])
async def test_result_must_match_exact_declaration_and_canonical_body(mode):
    host = SemanticInputProducerHost()
    source, operation = object(), object()
    validator = _SourceValidator(source, operation)

    def produce(_production_input):
        if mode == "return":
            return object()
        result = _body()
        coordinate = result.coordinate
        if mode == "role":
            coordinate = replace(coordinate, role="foreign")
        elif mode == "contract":
            coordinate = replace(
                coordinate,
                contract=SemanticContractRef("foreign.v1", "1", _digest("f")),
            )
        elif mode == "body":
            return SemanticBody(coordinate, b"foreign")
        return SemanticBody(coordinate, result.canonical_body)

    registration = register_semantic_input_producer(
        host,
        declaration=_DECLARATION,
        producer=produce,
        validator=validator,
        validator_entrance=validator.validate_semantic_input_source,
        reader=validator,
        reader_entrance=validator.read_semantic_input_sources,
    )
    with pytest.raises((ContractViolation, TypeError)):
        await execute_registered_semantic_input(
            host,
            registration,
            source_admission=source,
            expected=_expectation(operation, source),
        )


def test_registration_requires_original_bound_validator_and_unique_ref():
    host = SemanticInputProducerHost()
    source, operation = object(), object()
    validator = _SourceValidator(source, operation)
    producer = lambda *_: _body()
    with pytest.raises(ContractViolation, match="original registered"):
        register_semantic_input_producer(
            host,
            declaration=_DECLARATION,
            producer=producer,
            validator=validator,
            validator_entrance=lambda *_args, **_kwargs: None,
            reader=validator,
            reader_entrance=validator.read_semantic_input_sources,
        )
    registration = register_semantic_input_producer(
        host,
        declaration=_DECLARATION,
        producer=producer,
        validator=validator,
        validator_entrance=validator.validate_semantic_input_source,
        reader=validator,
        reader_entrance=validator.read_semantic_input_sources,
    )
    with pytest.raises(ContractViolation, match="already registered"):
        register_semantic_input_producer(
            host,
            declaration=_DECLARATION,
            producer=producer,
            validator=validator,
            validator_entrance=validator.validate_semantic_input_source,
            reader=validator,
            reader_entrance=validator.read_semantic_input_sources,
        )
    with pytest.raises(TypeError):
        copy.copy(registration)


@pytest.mark.asyncio
async def test_failure_consumes_use_and_close_revokes_registration(monkeypatch):
    host = SemanticInputProducerHost()
    source, operation = object(), object()
    validator = _SourceValidator(source, operation)

    def fail(*_args):
        raise RuntimeError("owner failed")

    registration = register_semantic_input_producer(
        host,
        declaration=_DECLARATION,
        producer=fail,
        validator=validator,
        validator_entrance=validator.validate_semantic_input_source,
        reader=validator,
        reader_entrance=validator.read_semantic_input_sources,
    )
    expected = _expectation(operation, source)
    with pytest.raises(RuntimeError, match="owner failed"):
        await execute_registered_semantic_input(
            host, registration, source_admission=source, expected=expected
        )
    with pytest.raises(ContractViolation, match="already consumed"):
        await execute_registered_semantic_input(
            host, registration, source_admission=source, expected=expected
        )
    close_semantic_input_producer_registration(host, registration)
    with pytest.raises(ContractViolation, match="unavailable"):
        await execute_registered_semantic_input(
            host,
            registration,
            source_admission=source,
            expected=_expectation(operation, source, use_ref="use-2"),
        )
    monkeypatch.setattr(os, "getpid", lambda: -1)
    with pytest.raises(ContractViolation, match="another process"):
        host.close()


def test_expectation_rejects_digest_restamp_and_identity_substitution():
    source, operation = object(), object()
    expected = _expectation(operation, source)
    with pytest.raises(ContractViolation, match="digest mismatched"):
        replace(expected, input_digest=_digest("foreign"))
    foreign_package = SemanticInputPackageIdentity(
        SemanticPackageCoordinate("package:foreign@1", "api", _digest("foreign")),
        "foreign",
    )
    with pytest.raises(ContractViolation, match="digest mismatched"):
        replace(expected, package_identity=foreign_package)


def test_registration_rejects_reconstructed_reader_entrance():
    host = SemanticInputProducerHost()
    source, operation = object(), object()
    validator = _SourceValidator(source, operation)
    with pytest.raises(ContractViolation, match="original registered reader"):
        register_semantic_input_producer(
            host,
            declaration=_DECLARATION,
            producer=lambda _input: _body(),
            validator=validator,
            validator_entrance=validator.validate_semantic_input_source,
            reader=validator,
            reader_entrance=lambda *_args, **_kwargs: (),
        )


@pytest.mark.asyncio
async def test_reader_must_return_exact_expected_path_closure():
    host = SemanticInputProducerHost()
    source, operation = object(), object()
    validator = _SourceValidator(source, operation)
    expected = _expectation(operation, source)

    class ForeignClosureReader:
        def read_semantic_input_sources(self, source_admission, *, expected):
            bodies = validator.read_semantic_input_sources(
                source_admission, expected=expected
            )
            return (
                replace(
                    bodies[0],
                    source=replace(
                        bodies[0].source, relative_path="foreign/source.aware"
                    ),
                ),
            )

    reader = ForeignClosureReader()
    registration = register_semantic_input_producer(
        host,
        declaration=_DECLARATION,
        producer=lambda _input: _body(),
        validator=validator,
        validator_entrance=validator.validate_semantic_input_source,
        reader=reader,
        reader_entrance=reader.read_semantic_input_sources,
    )
    with pytest.raises(ContractViolation, match="source closure differs"):
        await execute_registered_semantic_input(
            host, registration, source_admission=source, expected=expected
        )


@pytest.mark.asyncio
async def test_distinct_paths_with_deduplicated_bytes_remain_distinct():
    host = SemanticInputProducerHost()
    source, operation = object(), object()
    validator = _SourceValidator(source, operation)
    coordinate = SemanticValueCoordinate(
        "source",
        _SOURCE_CONTRACT,
        "cas://shared-body",
        _digest("source-body"),
        len(b"source-body"),
    )
    expected = SemanticInputProductionExpectation.create(
        use_ref="use-deduplicated",
        operation_ref="operation-1",
        stage="parsed_documents",
        package_identity=_PACKAGE_IDENTITY,
        operation_identity=operation,
        source_identity=source,
        source_coordinates=(
            SemanticInputSourceCoordinate("bindings/a.aware", coordinate),
            SemanticInputSourceCoordinate("bindings/b.aware", coordinate),
        ),
    )
    seen: list[str] = []

    def produce(production_input):
        seen.extend(item.source.relative_path for item in production_input.sources)
        return _body()

    registration = register_semantic_input_producer(
        host,
        declaration=_DECLARATION,
        producer=produce,
        validator=validator,
        validator_entrance=validator.validate_semantic_input_source,
        reader=validator,
        reader_entrance=validator.read_semantic_input_sources,
    )
    await execute_registered_semantic_input(
        host, registration, source_admission=source, expected=expected
    )
    assert seen == ["bindings/a.aware", "bindings/b.aware"]


@pytest.mark.asyncio
async def test_source_role_and_contract_must_match_registered_declaration():
    host = SemanticInputProducerHost()
    source, operation = object(), object()
    validator = _SourceValidator(source, operation)
    foreign_contract = SemanticContractRef("foreign.source.v1", "1", _digest("f"))
    coordinate = SemanticValueCoordinate(
        "source",
        foreign_contract,
        "cas://source",
        _digest("source-body"),
        len(b"source-body"),
    )
    expected = SemanticInputProductionExpectation.create(
        use_ref="use-foreign-contract",
        operation_ref="operation-1",
        stage="definition_request",
        package_identity=_PACKAGE_IDENTITY,
        operation_identity=operation,
        source_identity=source,
        source_coordinates=(
            SemanticInputSourceCoordinate("bindings/source.aware", coordinate),
        ),
    )
    registration = register_semantic_input_producer(
        host,
        declaration=_DECLARATION,
        producer=lambda _input: _body(),
        validator=validator,
        validator_entrance=validator.validate_semantic_input_source,
        reader=validator,
        reader_entrance=validator.read_semantic_input_sources,
    )
    with pytest.raises(ContractViolation, match="source contracts differ"):
        await execute_registered_semantic_input(
            host, registration, source_admission=source, expected=expected
        )


class _DependencyValidators:
    def __init__(self, resolution: object, fulfillment: object) -> None:
        self.resolution = resolution
        self.fulfillment = fulfillment
        self.live = True
        self.calls: list[str] = []

    def validate_dependency_resolution_admission(self, admission, *, expected):
        self.calls.append("resolution")
        if not self.live or admission is not self.resolution:
            raise ContractViolation("dependency resolution unavailable")

    def validate_dependency_fulfillment_admission(
        self, admission, *, resolution_admission, expected
    ):
        self.calls.append("fulfillment")
        if (
            not self.live
            or admission is not self.fulfillment
            or resolution_admission is not self.resolution
        ):
            raise ContractViolation("dependency fulfillment unavailable")


def _dependency_expectation(operation: object, *, use_ref: str = "dependency-use-1"):
    products = product_input()
    resolution = RetainedDependencyResolutionExpectation(
        object(),
        object(),
        object(),
        object(),
        object(),
        object(),
        object(),
        object(),
        object(),
        products.demand_set,
    )
    body = dependency_product_input_body(products)
    fulfillment = RetainedDependencyFulfillmentExpectation(
        resolution, body.coordinate, products
    )
    return SemanticDependencyInputProductionExpectation.create(
        use_ref=use_ref,
        operation_ref="operation-1",
        stage="type_schema_slices",
        operation_identity=operation,
        resolution=resolution,
        fulfillment=fulfillment,
    )


def _dependency_declaration(expected):
    product = expected.fulfillment.dependency_products.products[0]
    return SemanticDependencyInputProducerDeclaration(
        "example.meta.input",
        "example.meta.profile.v1",
        SemanticImplementationCoordinate("example-meta@1/input", _digest("meta")),
        SemanticConfigurationCoordinate("example.meta.config.v1", _digest("cfg")),
        (
            SemanticInputDependencyContract(
                product.body.coordinate.role, product.body.coordinate.contract
            ),
        ),
        "owner_input",
        _CONTRACT,
    )


@pytest.mark.asyncio
async def test_dependency_admissions_wrap_detached_owner_execution_and_single_use():
    host = SemanticInputProducerHost()
    operation = object()
    expected = _dependency_expectation(operation)
    resolution_admission, fulfillment_admission = object(), object()
    validators = _DependencyValidators(resolution_admission, fulfillment_admission)
    original_products = expected.fulfillment.dependency_products
    seen: list[object] = []

    async def produce(production_input):
        assert type(production_input) is SemanticDependencyInputProductionInput
        assert production_input.dependency_products == original_products
        assert production_input.dependency_products is not original_products
        seen.append(production_input.stage)
        return _body()

    registration = register_dependency_semantic_input_producer(
        host,
        declaration=_dependency_declaration(expected),
        producer=produce,
        resolution_validator=validators,
        resolution_validator_entrance=(
            validators.validate_dependency_resolution_admission
        ),
        fulfillment_validator=validators,
        fulfillment_validator_entrance=(
            validators.validate_dependency_fulfillment_admission
        ),
    )
    result = await execute_registered_dependency_semantic_input(
        host,
        registration,
        resolution_admission=resolution_admission,
        fulfillment_admission=fulfillment_admission,
        expected=expected,
    )
    assert result == _body()
    assert seen == ["type_schema_slices"]
    assert validators.calls == [
        "resolution",
        "fulfillment",
        "resolution",
        "fulfillment",
    ]
    with pytest.raises(ContractViolation, match="already consumed"):
        await execute_registered_dependency_semantic_input(
            host,
            registration,
            resolution_admission=resolution_admission,
            fulfillment_admission=fulfillment_admission,
            expected=expected,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("substitution", ["resolution", "fulfillment", "revoke"])
async def test_dependency_execution_rejects_substitution_and_revocation(substitution):
    host = SemanticInputProducerHost()
    expected = _dependency_expectation(object(), use_ref=f"use-{substitution}")
    resolution_admission, fulfillment_admission = object(), object()
    validators = _DependencyValidators(resolution_admission, fulfillment_admission)

    def produce(_production_input):
        if substitution == "revoke":
            validators.live = False
        return _body()

    registration = register_dependency_semantic_input_producer(
        host,
        declaration=_dependency_declaration(expected),
        producer=produce,
        resolution_validator=validators,
        resolution_validator_entrance=(
            validators.validate_dependency_resolution_admission
        ),
        fulfillment_validator=validators,
        fulfillment_validator_entrance=(
            validators.validate_dependency_fulfillment_admission
        ),
    )
    with pytest.raises(ContractViolation, match="unavailable"):
        await execute_registered_dependency_semantic_input(
            host,
            registration,
            resolution_admission=(
                object() if substitution == "resolution" else resolution_admission
            ),
            fulfillment_admission=(
                object() if substitution == "fulfillment" else fulfillment_admission
            ),
            expected=expected,
        )


def test_dependency_registration_requires_original_validator_entrances_and_closes():
    host = SemanticInputProducerHost()
    expected = _dependency_expectation(object())
    resolution_admission, fulfillment_admission = object(), object()
    validators = _DependencyValidators(resolution_admission, fulfillment_admission)
    kwargs = dict(
        declaration=_dependency_declaration(expected),
        producer=lambda _input: _body(),
        resolution_validator=validators,
        resolution_validator_entrance=(
            validators.validate_dependency_resolution_admission
        ),
        fulfillment_validator=validators,
        fulfillment_validator_entrance=(
            validators.validate_dependency_fulfillment_admission
        ),
    )
    with pytest.raises(ContractViolation, match="original dependency resolution"):
        register_dependency_semantic_input_producer(
            host, **(kwargs | {"resolution_validator_entrance": lambda *_a, **_k: None})
        )
    registration = register_dependency_semantic_input_producer(host, **kwargs)
    with pytest.raises(TypeError):
        copy.copy(registration)
    close_dependency_semantic_input_producer_registration(host, registration)

_REQUEST_CONTRACT = SemanticContractRef(
    "example.definition-request.v1", "1", _digest("request-schema")
)
_PARSED_CONTRACT = SemanticContractRef(
    "example.parsed-documents.v1", "1", _digest("parsed-schema")
)


class _JoinSourceValidator:
    def __init__(self, admission, operation, source_identity):
        self.admission = admission
        self.operation = operation
        self.source_identity = source_identity
        self.live = True
        self.calls = 0

    def validate_semantic_input_source(self, admission, *, expected):
        self.calls += 1
        if (
            not self.live
            or admission is not self.admission
            or expected.operation_identity is not self.operation
            or expected.source_identity is not self.source_identity
        ):
            raise ContractViolation("joined source unavailable")

    def read_semantic_input_sources(self, admission, *, expected):
        self.validate_semantic_input_source(admission, expected=expected)
        return tuple(
            SemanticInputSourceBody(
                SemanticInputSourceCoordinate(
                    value.relative_path, replace(value.coordinate)
                ),
                b"source-body",
            )
            for value in expected.source_coordinates
        )


def _role_expectation(
    operation,
    source_identity,
    *,
    use_ref: str,
    stage: str,
):
    coordinate = SemanticValueCoordinate(
        "source",
        _SOURCE_CONTRACT,
        f"cas://{use_ref}",
        _digest("source-body"),
        len(b"source-body"),
    )
    return SemanticInputProductionExpectation.create(
        use_ref=use_ref,
        operation_ref="operation-join-1",
        stage=stage,
        package_identity=_PACKAGE_IDENTITY,
        operation_identity=operation,
        source_identity=source_identity,
        source_coordinates=(
            SemanticInputSourceCoordinate(f"bindings/{use_ref}.aware", coordinate),
        ),
    )


def _role_declaration(producer_ref, role, contract):
    return SemanticInputProducerDeclaration(
        producer_ref,
        f"{producer_ref}.profile.v1",
        SemanticImplementationCoordinate(
            f"{producer_ref}@1/input", _digest(producer_ref)
        ),
        SemanticConfigurationCoordinate(f"{producer_ref}.config.v1", _digest(role)),
        (SemanticInputSourceContract("source", _SOURCE_CONTRACT),),
        role,
        contract,
    )


def _role_body(role, contract, payload):
    return SemanticBody(
        SemanticValueCoordinate(
            role,
            contract,
            f"cas://{role}",
            ContentDigest.of_bytes(payload),
            len(payload),
        ),
        payload,
    )


def _register_source_role(host, declaration, producer, validator):
    return register_semantic_input_producer(
        host,
        declaration=declaration,
        producer=producer,
        validator=validator,
        validator_entrance=validator.validate_semantic_input_source,
        reader=validator,
        reader_entrance=validator.read_semantic_input_sources,
    )


def _register_joined_role(host, producer, validator):
    declaration = SemanticInputJoinedProducerDeclaration(
        _role_declaration(
            "example.source-question",
            "source_question_bindings",
            _CONTRACT,
        ),
        (
            SemanticInputSourceContract("definition_request", _REQUEST_CONTRACT),
            SemanticInputSourceContract("parsed_documents", _PARSED_CONTRACT),
        ),
    )
    return register_joined_semantic_input_producer(
        host,
        declaration=declaration,
        producer=producer,
        validator=validator,
        validator_entrance=validator.validate_semantic_input_source,
        reader=validator,
        reader_entrance=validator.read_semantic_input_sources,
    )


def _open_join_fixture(joined_producer):
    host = SemanticInputProducerHost()
    admission, operation = object(), object()
    request_source, parsed_source, joined_source = object(), object(), object()
    request_expected = _role_expectation(
        operation,
        request_source,
        use_ref="request-use",
        stage="definition_request",
    )
    parsed_expected = _role_expectation(
        operation,
        parsed_source,
        use_ref="parsed-use",
        stage="parsed_documents",
    )
    joined_expected = _role_expectation(
        operation,
        joined_source,
        use_ref="joined-use",
        stage="source_question_bindings",
    )
    request_validator = _JoinSourceValidator(admission, operation, request_source)
    parsed_validator = _JoinSourceValidator(admission, operation, parsed_source)
    joined_validator = _JoinSourceValidator(admission, operation, joined_source)
    ordinary_inputs = []

    def request_producer(value):
        ordinary_inputs.append(type(value))
        return _role_body("definition_request", _REQUEST_CONTRACT, b"request")

    def parsed_producer(value):
        ordinary_inputs.append(type(value))
        return _role_body("parsed_documents", _PARSED_CONTRACT, b"parsed")

    request_registration = _register_source_role(
        host,
        _role_declaration(
            "example.request", "definition_request", _REQUEST_CONTRACT
        ),
        request_producer,
        request_validator,
    )
    parsed_registration = _register_source_role(
        host,
        _role_declaration("example.parsed", "parsed_documents", _PARSED_CONTRACT),
        parsed_producer,
        parsed_validator,
    )
    joined_registration = _register_joined_role(
        host, joined_producer, joined_validator
    )
    role_join = open_semantic_input_role_join(
        host,
        joined_registration=joined_registration,
        joined_expected=joined_expected,
        source_admission=admission,
        predecessors=(
            SemanticInputRoleJoinPredecessor(
                request_registration, request_expected
            ),
            SemanticInputRoleJoinPredecessor(parsed_registration, parsed_expected),
        ),
    )
    return {
        "host": host,
        "admission": admission,
        "operation": operation,
        "request_registration": request_registration,
        "request_expected": request_expected,
        "parsed_registration": parsed_registration,
        "parsed_expected": parsed_expected,
        "joined_registration": joined_registration,
        "joined_expected": joined_expected,
        "role_join": role_join,
        "ordinary_inputs": ordinary_inputs,
        "validators": (request_validator, parsed_validator, joined_validator),
    }


@pytest.mark.asyncio
async def test_role_join_supplies_ordered_detached_predecessors_and_is_single_use():
    seen = []

    def joined_producer(value):
        assert type(value) is SemanticInputJoinedProductionInput
        assert type(value.ordinary) is SemanticInputProductionInput
        assert all(
            type(item) is SemanticInputPredecessorBody
            for item in value.predecessors
        )
        assert tuple(item.role for item in value.predecessors) == (
            "definition_request",
            "parsed_documents",
        )
        assert tuple(item.canonical_body for item in value.predecessors) == (
            b"request",
            b"parsed",
        )
        seen.append(value.predecessor_closure_digest)
        return _role_body("source_question_bindings", _CONTRACT, b"joined")

    fixture = _open_join_fixture(joined_producer)
    request_result = await execute_registered_semantic_input(
        fixture["host"],
        fixture["request_registration"],
        source_admission=fixture["admission"],
        expected=fixture["request_expected"],
    )
    parsed_result = await execute_registered_semantic_input(
        fixture["host"],
        fixture["parsed_registration"],
        source_admission=fixture["admission"],
        expected=fixture["parsed_expected"],
    )
    object.__setattr__(request_result, "canonical_body", b"mutated")
    object.__setattr__(parsed_result, "canonical_body", b"mutate")
    result = await execute_registered_joined_semantic_input(
        fixture["host"],
        fixture["joined_registration"],
        role_join=fixture["role_join"],
        source_admission=fixture["admission"],
        expected=fixture["joined_expected"],
    )
    assert result == _role_body("source_question_bindings", _CONTRACT, b"joined")
    assert fixture["ordinary_inputs"] == [
        SemanticInputProductionInput,
        SemanticInputProductionInput,
    ]
    assert len(seen) == 1
    with pytest.raises(ContractViolation, match="unavailable"):
        close_semantic_input_role_join(fixture["host"], fixture["role_join"])
    with pytest.raises(TypeError):
        copy.copy(fixture["role_join"])


@pytest.mark.asyncio
async def test_role_join_closure_digest_uses_the_frozen_binary_preimage():
    observed = []

    def joined_producer(value):
        observed.append(value.predecessor_closure_digest)
        return _role_body("source_question_bindings", _CONTRACT, b"joined")

    fixture = _open_join_fixture(joined_producer)
    for registration_key, expected_key in (
        ("request_registration", "request_expected"),
        ("parsed_registration", "parsed_expected"),
    ):
        await execute_registered_semantic_input(
            fixture["host"],
            fixture[registration_key],
            source_admission=fixture["admission"],
            expected=fixture[expected_key],
        )
    await execute_registered_joined_semantic_input(
        fixture["host"],
        fixture["joined_registration"],
        role_join=fixture["role_join"],
        source_admission=fixture["admission"],
        expected=fixture["joined_expected"],
    )

    def field(value: bytes) -> bytes:
        return len(value).to_bytes(8, "big") + value

    payload = bytearray(b"aware.code.semantic-input-predecessor-closure.v1\0")
    payload.extend(field(b"operation-join-1"))
    payload.extend(field(canonical_json_bytes(_PACKAGE_IDENTITY.to_wire())))
    for role, expected_key, body in (
        ("definition_request", "request_expected", b"request"),
        ("parsed_documents", "parsed_expected", b"parsed"),
    ):
        expected = fixture[expected_key]
        result = _role_body(
            role,
            _REQUEST_CONTRACT if role == "definition_request" else _PARSED_CONTRACT,
            body,
        )
        payload.extend(field(role.encode()))
        payload.extend(field(expected.use_ref.encode()))
        payload.extend(
            field(
                canonical_json_bytes(
                    [value.to_wire() for value in expected.source_coordinates]
                )
            )
        )
        payload.extend(field(canonical_json_bytes(result.coordinate.to_wire())))
        payload.extend(field(body))
    assert observed == [ContentDigest.of_bytes(bytes(payload))]


@pytest.mark.asyncio
async def test_role_join_rejects_reordered_predecessor_and_terminally_revokes():
    called = []
    fixture = _open_join_fixture(
        lambda value: called.append(value)
        or _role_body("source_question_bindings", _CONTRACT, b"joined")
    )
    with pytest.raises(ContractViolation, match="slot differs"):
        await execute_registered_semantic_input(
            fixture["host"],
            fixture["parsed_registration"],
            source_admission=fixture["admission"],
            expected=fixture["parsed_expected"],
        )
    assert called == []
    with pytest.raises(ContractViolation, match="unavailable"):
        await execute_registered_joined_semantic_input(
            fixture["host"],
            fixture["joined_registration"],
            role_join=fixture["role_join"],
            source_admission=fixture["admission"],
            expected=fixture["joined_expected"],
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode",
    ["expected", "admission", "operation", "source", "package", "closed"],
)
async def test_role_join_poison_matrix_for_substitution_and_closure(mode):
    fixture = _open_join_fixture(
        lambda _value: _role_body(
            "source_question_bindings", _CONTRACT, b"joined"
        )
    )
    expected = fixture["request_expected"]
    if mode == "expected":
        expected = replace(expected)
    elif mode in {"operation", "source"}:
        expected = _role_expectation(
            object() if mode == "operation" else fixture["operation"],
            object() if mode == "source" else expected.source_identity,
            use_ref=expected.use_ref,
            stage=expected.stage,
        )
    elif mode == "package":
        expected = SemanticInputProductionExpectation.create(
            use_ref=expected.use_ref,
            operation_ref=expected.operation_ref,
            stage=expected.stage,
            package_identity=SemanticInputPackageIdentity(
                SemanticPackageCoordinate(
                    "package:other@1", "api", _digest("other-manifest")
                ),
                "other",
            ),
            operation_identity=expected.operation_identity,
            source_identity=expected.source_identity,
            source_coordinates=expected.source_coordinates,
        )
    admission = object() if mode == "admission" else fixture["admission"]
    if mode == "closed":
        close_semantic_input_producer_registration(
            fixture["host"], fixture["request_registration"]
        )
        with pytest.raises(ContractViolation, match="unavailable"):
            close_semantic_input_role_join(fixture["host"], fixture["role_join"])
        return
    with pytest.raises(ContractViolation, match="slot differs"):
        await execute_registered_semantic_input(
            fixture["host"],
            fixture["request_registration"],
            source_admission=admission,
            expected=expected,
        )
    with pytest.raises(ContractViolation, match="unavailable"):
        close_semantic_input_role_join(fixture["host"], fixture["role_join"])


@pytest.mark.asyncio
async def test_joined_execution_with_missing_predecessor_consumes_join():
    fixture = _open_join_fixture(
        lambda _value: _role_body(
            "source_question_bindings", _CONTRACT, b"joined"
        )
    )
    await execute_registered_semantic_input(
        fixture["host"],
        fixture["request_registration"],
        source_admission=fixture["admission"],
        expected=fixture["request_expected"],
    )
    with pytest.raises(ContractViolation, match="incomplete or differs"):
        await execute_registered_joined_semantic_input(
            fixture["host"],
            fixture["joined_registration"],
            role_join=fixture["role_join"],
            source_admission=fixture["admission"],
            expected=fixture["joined_expected"],
        )
    with pytest.raises(ContractViolation, match="unavailable"):
        close_semantic_input_role_join(fixture["host"], fixture["role_join"])


@pytest.mark.asyncio
async def test_joined_producer_failure_terminally_consumes_join():
    def fail(_value):
        raise RuntimeError("owner failed")

    fixture = _open_join_fixture(fail)
    for registration_key, expected_key in (
        ("request_registration", "request_expected"),
        ("parsed_registration", "parsed_expected"),
    ):
        await execute_registered_semantic_input(
            fixture["host"],
            fixture[registration_key],
            source_admission=fixture["admission"],
            expected=fixture[expected_key],
        )
    with pytest.raises(RuntimeError, match="owner failed"):
        await execute_registered_joined_semantic_input(
            fixture["host"],
            fixture["joined_registration"],
            role_join=fixture["role_join"],
            source_admission=fixture["admission"],
            expected=fixture["joined_expected"],
        )
    with pytest.raises(ContractViolation, match="unavailable"):
        close_semantic_input_role_join(fixture["host"], fixture["role_join"])


def test_role_join_rejects_foreign_thread_without_transferring_ownership():
    fixture = _open_join_fixture(
        lambda _value: _role_body(
            "source_question_bindings", _CONTRACT, b"joined"
        )
    )
    failures = []

    def close_from_foreign_thread():
        try:
            close_semantic_input_role_join(fixture["host"], fixture["role_join"])
        except Exception as error:  # noqa: BLE001 - captures exact boundary result
            failures.append(error)

    thread = Thread(target=close_from_foreign_thread)
    thread.start()
    thread.join()
    assert len(failures) == 1
    assert type(failures[0]) is ContractViolation
    assert "another thread" in str(failures[0])
    close_semantic_input_role_join(fixture["host"], fixture["role_join"])


def test_role_join_open_requires_original_complete_contract_and_same_operation():
    host = SemanticInputProducerHost()
    admission, operation = object(), object()
    source = object()
    validator = _JoinSourceValidator(admission, operation, source)
    expected = _role_expectation(
        operation, source, use_ref="request-use", stage="definition_request"
    )
    registration = _register_source_role(
        host,
        _role_declaration(
            "example.request", "definition_request", _REQUEST_CONTRACT
        ),
        lambda _value: _role_body(
            "definition_request", _REQUEST_CONTRACT, b"request"
        ),
        validator,
    )
    joined_validator = _JoinSourceValidator(admission, operation, object())
    joined_expected = _role_expectation(
        operation,
        joined_validator.source_identity,
        use_ref="joined-use",
        stage="source_question_bindings",
    )
    joined_registration = _register_joined_role(
        host,
        lambda _value: _role_body(
            "source_question_bindings", _CONTRACT, b"joined"
        ),
        joined_validator,
    )
    with pytest.raises(ContractViolation, match="predecessor count differs"):
        open_semantic_input_role_join(
            host,
            joined_registration=joined_registration,
            joined_expected=joined_expected,
            source_admission=admission,
            predecessors=(SemanticInputRoleJoinPredecessor(registration, expected),),
        )
