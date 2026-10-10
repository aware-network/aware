"""Original validation boundaries survive retained closed-graph reuse."""

from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import ContractViolation, SemanticContractRef
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from test_contextual_semantic_input_producer import OriginalSource, context
from test_semantic_input_producer import _DECLARATION, _body, _expectation


def setup(owner_type=OriginalSource, *, source_count=2, distinct_contracts=False):
    host = inputs.SemanticInputProducerHost()
    source, operation = object(), object()
    bodies = (context(),)
    owner = owner_type(source, operation, bodies)
    base = _expectation(operation, source)
    original = base.source_coordinates[0]
    contract = replace(original.coordinate.contract,
                       schema_digest=replace(original.coordinate.contract.schema_digest))
    coordinate = replace(original.coordinate, contract=contract)
    # Distinct paths legitimately reuse the same original contract object.
    coordinates = tuple(replace(original, relative_path=f"bindings/{i:04d}.aware",
        coordinate=replace(coordinate, contract=replace(contract,
            schema_digest=replace(contract.schema_digest)) if distinct_contracts else contract))
        for i in range(source_count))
    expected = inputs.SemanticInputProductionExpectation.create(
        use_ref=base.use_ref, operation_ref=base.operation_ref, stage=base.stage,
        package_identity=base.package_identity, operation_identity=operation,
        source_identity=source, source_coordinates=coordinates, context_bodies=bodies,
    )
    declaration = replace(_DECLARATION, context_contracts=(
        inputs.SemanticInputContextContract("context", bodies[0].coordinate.contract),
    ))
    seen = []
    registered = inputs.register_semantic_input_producer(
        host, declaration=declaration, producer=lambda value: seen.append(value) or _body(),
        validator=owner, validator_entrance=owner.validate_semantic_input_source,
        reader=owner, reader_entrance=owner.read_semantic_input_sources,
        context_validator_entrance=owner.validate_semantic_input_context,
        retain_result=True,
    )
    return host, registered, source, expected, owner, seen


async def execute(fixture):
    host, registered, source, expected, _, _ = fixture
    return await inputs.execute_registered_semantic_input(
        host, registered, source_admission=source, expected=expected,
    )


def validate(fixture, result):
    host, registered, source, expected, _, _ = fixture
    inputs.validate_registered_semantic_input_result(
        host, registered, source_admission=source, expected=expected, result=result,
    )


@pytest.mark.asyncio
async def test_context_owner_checks_remain_fresh_through_public_result_validation():
    fixture = setup()
    host, _registered, _source, _expected, owner, seen = fixture
    try:
        result = await execute(fixture)
        assert owner.context_calls == 3 and len(seen) == 1
        validate(fixture, result)
        assert owner.context_calls == 5
        owner.live = False
        with pytest.raises(ContractViolation, match="source unavailable"):
            validate(fixture, result)
        assert not host._results
        with pytest.raises(ContractViolation):
            await execute(fixture)
    finally:
        host.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["copied_contract", "changed_digest"])
async def test_large_distinct_contract_inventory_preserves_last_row_integrity(change):
    fixture = setup(source_count=100, distinct_contracts=True)
    host, _, _, expected, _, _ = fixture
    try:
        result = await execute(fixture)
        last = expected.source_coordinates[-1].coordinate
        if change == "copied_contract":
            object.__setattr__(last, "contract", replace(last.contract))
        else:
            object.__setattr__(last.contract.schema_digest, "value", "sha256:" + "0" * 64)
        with pytest.raises(ContractViolation):
            validate(fixture, result)
        assert not host._results
    finally:
        host.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("boundary", range(1, 6))
@pytest.mark.parametrize("change", ["tuple", "contract_copy", "shared_digest", "opaque", "descriptor"])
async def test_each_context_boundary_rejects_original_graph_changes(boundary, change, monkeypatch):
    invoked = []

    def foreign(instance):
        invoked.append(instance)
        raise AssertionError("foreign descriptor invoked")

    class MutatingOwner(OriginalSource):
        def validate_semantic_input_context(self, source_admission, *, expected):
            super().validate_semantic_input_context(source_admission, expected=expected)
            if self.context_calls != boundary:
                return
            coordinate = expected.source_coordinates[1].coordinate
            if change == "tuple":
                object.__setattr__(expected, "source_coordinates", (*expected.source_coordinates,))
            elif change == "contract_copy":
                object.__setattr__(coordinate, "contract", replace(coordinate.contract))
            elif change == "shared_digest":
                object.__setattr__(coordinate.contract.schema_digest, "value", "sha256:" + "0" * 64)
            elif change == "opaque":
                object.__setattr__(expected, "operation_identity", object())
            else:
                monkeypatch.setattr(SemanticContractRef, "schema_digest", property(foreign))

    fixture = setup(MutatingOwner)
    host, _, _, _, owner, seen = fixture
    try:
        with pytest.raises(ContractViolation):
            result = await execute(fixture)
            validate(fixture, result)
        assert owner.context_calls == boundary
        assert len(seen) == int(boundary >= 3)
        assert not invoked and not host._results
    finally:
        host.close()
