from __future__ import annotations

import contextvars
from contextlib import asynccontextmanager
from dataclasses import replace

import pytest
import pytest_asyncio
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_code_semantic_contract_runtime.selected_input_verification import (
    SelectedInputSourceResult,
    SelectedInputVerificationAssembly,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputContextContract,
    SemanticInputProducerHost,
    SemanticInputProductionExpectation,
    execute_registered_semantic_input,
    original_result_verification_work_scope,
    register_semantic_input_producer,
    validate_registered_semantic_input_result,
)
from test_semantic_input_producer import (
    _DECLARATION,
    _body,
    _expectation,
    _SourceValidator,
)


class _NestedSourceValidator(_SourceValidator):
    nested = None
    context_calls = 0

    def validate_semantic_input_source(self, source_admission, *, expected):
        super().validate_semantic_input_source(source_admission, expected=expected)
        if self.nested is not None:
            check(self.nested)

    def validate_semantic_input_context(self, source_admission, *, expected):
        self.context_calls += 1
        self.validate_semantic_input_source(source_admission, expected=expected)


@asynccontextmanager
async def production(*, with_context=False):
    host = SemanticInputProducerHost()
    source, operation = object(), object()
    validator = _NestedSourceValidator(source, operation)
    expected = _expectation(operation, source)
    result = _body()
    declaration = _DECLARATION
    if with_context:
        body = SemanticBody(
            replace(result.coordinate, role="context"), result.canonical_body
        )
        declaration = replace(
            declaration,
            context_contracts=(
                SemanticInputContextContract("context", body.coordinate.contract),
            ),
        )
        expected = SemanticInputProductionExpectation.create(
            use_ref=expected.use_ref,
            operation_ref=expected.operation_ref,
            stage=expected.stage,
            package_identity=expected.package_identity,
            operation_identity=operation,
            source_identity=source,
            source_coordinates=expected.source_coordinates,
            context_bodies=(body,),
        )
    producer_calls = []

    async def produce(value):
        producer_calls.append(value)
        return result

    registration = register_semantic_input_producer(
        host,
        declaration=declaration,
        producer=produce,
        validator=validator,
        validator_entrance=validator.validate_semantic_input_source,
        reader=validator,
        reader_entrance=validator.read_semantic_input_sources,
        context_validator_entrance=(
            validator.validate_semantic_input_context if with_context else None
        ),
        retain_result=True,
    )
    returned = await execute_registered_semantic_input(
        host,
        registration,
        source_admission=source,
        expected=expected,
    )
    binding = SelectedInputSourceResult(host, registration, source, expected, returned)
    try:
        yield binding, validator, producer_calls
    finally:
        host.close()


@pytest_asyncio.fixture
async def original():
    async with production() as value:
        yield value


def check(binding):
    validate_registered_semantic_input_result(
        binding.host,
        binding.registration,
        source_admission=binding.source_admission,
        expected=binding.expected,
        result=binding.result,
    )


def assembly(binding, **changes):
    options = {
        "semantic_input": object(),
        "input_bodies": (binding.result,),
        "source_results": (binding,),
        "source_input_roles": (("owner_input", 0),),
    }
    options.update(changes)
    return SelectedInputVerificationAssembly(**options)


@pytest.mark.asyncio
async def test_original_correspondence_is_data_without_execution(original):
    binding, validator, calls = original
    count = validator.calls
    value = assembly(binding)
    assert value.source_results[0] is binding
    assert value.input_bodies[0] is binding.result
    assert validator.calls == count and len(calls) == 1


@pytest.mark.asyncio
async def test_closed_original_is_not_admitted_by_construction(original):
    binding, validator, _ = original
    validator.live = False
    value = assembly(binding)
    assert value.source_results[0] is binding
    with pytest.raises(ContractViolation, match="unavailable"):
        check(binding)


@pytest.mark.asyncio
async def test_equal_detached_body_cannot_substitute(original):
    binding, _, _ = original
    with pytest.raises(ContractViolation, match="not original"):
        assembly(binding, input_bodies=(replace(binding.result),))


@pytest.mark.parametrize(
    "changes",
    (
        {"source_input_roles": ()},
        {"source_input_roles": (("owner_input", 0), ("owner_input", 0))},
        {"source_input_roles": (("other", 0),)},
        {"source_input_roles": (("owner_input", True),)},
        {"source_input_roles": (("owner_input", -1),)},
        {"source_input_roles": (("owner_input", 1),)},
        {"source_results": ()},
        {"dependency_input_role": "products"},
    ),
)
@pytest.mark.asyncio
async def test_complete_original_role_partition_required(original, changes):
    binding, _, _ = original
    with pytest.raises(ContractViolation):
        assembly(binding, **changes)


@pytest.mark.asyncio
async def test_source_result_cannot_appear_twice(original):
    binding, _, _ = original
    with pytest.raises(ContractViolation, match="duplicate"):
        assembly(binding, source_results=(binding, binding))


@pytest.mark.asyncio
async def test_foreign_source_handle_is_never_inspected(original):
    binding, _, _ = original

    class Foreign:
        def __getattribute__(self, name):
            raise AssertionError("foreign source attribute")

        def __hash__(self):
            raise AssertionError("foreign source hash")

        def __eq__(self, other):
            raise AssertionError("foreign source equality")

    with pytest.raises(ContractViolation, match="admission differs"):
        replace(binding, source_admission=Foreign())


@pytest.mark.asyncio
async def test_product_reference_is_not_read_or_authenticated(original):
    binding, _, _ = original

    class Products:
        def __getattribute__(self, name):
            raise AssertionError("product access during data construction")

    products = Products()
    body = SemanticBody(
        replace(binding.result.coordinate, role="products"),
        binding.result.canonical_body,
    )
    value = assembly(
        binding,
        input_bodies=(binding.result, body),
        dependency_products=products,
        dependency_input_role="products",
    )
    assert value.dependency_products is products


@pytest.mark.asyncio
async def test_exact_input_and_occurrence_limits(original, monkeypatch):
    from aware_code_semantic_contract_runtime import (
        selected_input_verification as values,
    )

    binding, _, _ = original
    monkeypatch.setattr(
        values, "MAX_SELECTED_INPUT_BYTES", len(binding.result.canonical_body) - 1
    )
    with pytest.raises(ContractViolation, match="byte bound exceeded"):
        assembly(binding)


@pytest.mark.asyncio
async def test_product_only_shape_has_no_provider_specific_source_requirement(original):
    binding, _, _ = original
    body = SemanticBody(
        replace(binding.result.coordinate, role="products"),
        binding.result.canonical_body,
    )
    value = assembly(
        binding,
        input_bodies=(body,),
        source_results=(),
        source_input_roles=(),
        dependency_products=object(),
        dependency_input_role="products",
    )
    assert value.source_results == ()


@pytest.mark.asyncio
async def test_complete_input_quota_precedes_body_hashing(original, monkeypatch):
    from aware_code_semantic_contract_runtime import (
        selected_input_verification as values,
    )

    binding, _, _ = original
    body = SemanticBody(
        replace(binding.result.coordinate, role="products"),
        binding.result.canonical_body,
    )
    monkeypatch.setattr(values, "MAX_SELECTED_INPUT_BYTES", len(body.canonical_body))

    def forbidden_body_validation(_):
        pytest.fail("body hashing before complete byte admission")

    monkeypatch.setattr(values, "_body", forbidden_body_validation)
    with pytest.raises(ContractViolation, match="complete selected input byte"):
        assembly(
            binding,
            input_bodies=(binding.result, body),
            dependency_products=object(),
            dependency_input_role="products",
        )


@pytest.mark.asyncio
async def test_retained_occurrences_are_charged_again(original, monkeypatch):
    from aware_code_semantic_contract_runtime import (
        selected_input_verification as values,
    )

    binding, _, _ = original
    # The same result is retained as the source return and the final input.
    size = sum(row.coordinate.size_bytes for row in binding.expected.source_coordinates)
    size += 2 * len(binding.result.canonical_body)
    monkeypatch.setattr(values, "MAX_SELECTED_INPUT_RETAINED_BODY_BYTES", size - 1)
    with pytest.raises(ContractViolation, match="retained selected input"):
        assembly(binding)


@pytest.mark.asyncio
async def test_scoped_validation_preserves_both_original_checks(original):
    binding, validator, calls = original
    count = validator.calls
    with original_result_verification_work_scope(
        result_visits=2, source_calls=2, context_calls=0
    ):
        check(binding)
    assert validator.calls - count == 2
    assert len(calls) == 1
    assert not binding.host._closed
    check(binding)  # Ordinary unscoped behavior is preserved.


@pytest.mark.parametrize(
    "limits,expected_calls",
    (
        ({"result_visits": 0}, 0),
        ({"source_calls": 0}, 0),
        ({"result_visits": 1}, 1),
        ({"source_calls": 1}, 1),
    ),
)
@pytest.mark.asyncio
async def test_exhaustion_precedes_callback_and_retires_result(
    original, limits, expected_calls
):
    binding, validator, calls = original
    count = validator.calls
    with (
        pytest.raises(ContractViolation, match="work exhausted"),
        original_result_verification_work_scope(**limits),
    ):
        check(binding)
    assert validator.calls - count == expected_calls
    assert len(calls) == 1
    with pytest.raises(ContractViolation, match="original returned"):
        check(binding)
    assert not binding.host._closed


@pytest.mark.asyncio
async def test_nested_scope_cannot_refresh_or_resume_outer_budget(original):
    binding, validator, _ = original
    count = validator.calls
    with (
        pytest.raises(ContractViolation, match="work is terminal"),
        original_result_verification_work_scope(),
    ):
        with (
            pytest.raises(ContractViolation, match="nested"),
            original_result_verification_work_scope(),
        ):
            pass
        with pytest.raises(ContractViolation, match="work exhausted"):
            check(binding)
    assert validator.calls == count


@pytest.mark.asyncio
async def test_inherited_context_cannot_extend_exited_scope(original):
    binding, validator, _ = original
    count = validator.calls
    with original_result_verification_work_scope():
        inherited = contextvars.copy_context()
    with pytest.raises(ContractViolation, match="work exhausted"):
        inherited.run(check, binding)
    assert validator.calls == count


@pytest.mark.parametrize("value", (True, -1, 2049, "2", 2.0))
def test_quota_limits_are_exact_bounded_integers(value):
    with (
        pytest.raises(ContractViolation, match="limits differ"),
        original_result_verification_work_scope(result_visits=value),
    ):
        pass


def test_scope_exception_does_not_leak_quota():
    with (
        pytest.raises(RuntimeError, match="cancelled"),
        original_result_verification_work_scope(result_visits=0),
    ):
        raise RuntimeError("cancelled")
    with original_result_verification_work_scope():
        pass


@pytest.mark.asyncio
async def test_indirect_owner_checks_share_the_original_work_budget():
    async with (
        production() as (root, owner, root_calls),
        production() as (child, child_owner, child_calls),
    ):
        owner.nested = child
        before = owner.calls, child_owner.calls
        with (
            pytest.raises(ContractViolation, match="work exhausted"),
            original_result_verification_work_scope(result_visits=2),
        ):
            check(root)
        assert (owner.calls - before[0], child_owner.calls - before[1]) == (1, 1)
        assert len(root_calls) == len(child_calls) == 1
        assert not root.host._closed and not child.host._closed


@pytest.mark.asyncio
async def test_original_context_body_partition_and_both_context_checks():
    async with production(with_context=True) as (binding, owner, calls):
        context = binding.expected.context_bodies[0]
        value = assembly(
            binding,
            input_bodies=(binding.result, context),
            context_input_roles=(("context", 0, 0),),
        )
        assert value.input_bodies[1] is context
        count = owner.context_calls
        with original_result_verification_work_scope(context_calls=2):
            check(binding)
        assert owner.context_calls - count == 2 and len(calls) == 1


@pytest.mark.asyncio
async def test_context_quota_refuses_before_context_callback():
    async with production(with_context=True) as (binding, owner, _):
        count = owner.context_calls
        with (
            pytest.raises(ContractViolation, match="work exhausted"),
            original_result_verification_work_scope(context_calls=0),
        ):
            check(binding)
        assert owner.context_calls == count
