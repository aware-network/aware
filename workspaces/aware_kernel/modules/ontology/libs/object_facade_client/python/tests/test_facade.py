"""Client consistency and one-use lifecycle proofs; no evaluator execution."""

import asyncio
from typing import Any

import pytest
from aware_ontology_object_facade_client import (
    ActionValueMode,
    LocalScalarClient,
    OntologyObjectActionBinding,
    OntologyObjectActionParameterBinding,
    OntologyObjectClassBinding,
    OntologyObjectFacade,
    ScalarArguments,
    ScalarInvocationError,
    ScalarKind,
    ScalarObjectContext,
    ScalarReceipt,
    ScalarResult,
    ValueShape,
)

DIGEST = "sha256:" + "d" * 64
RECEIPT = ScalarReceipt("invocation:1", "attempt:1", DIGEST, "no_op")


class Invoker:
    def __init__(self, failure: BaseException | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.failure = failure

    async def invoke_action(self, **values: Any) -> ScalarResult:
        self.calls.append(values)
        if self.failure:
            raise self.failure
        return ScalarResult(42, RECEIPT)


def binding(*, parameters=(), actions=None):
    return OntologyObjectClassBinding.create(
        type_ref="scalar.Counter", class_name="Counter", fields=(), relationships=(),
        actions=actions or (OntologyObjectActionBinding("scalar.read_scalar", "read_scalar", parameters),),
    )


def counter(context: ScalarObjectContext, key="business/1", **metadata):
    facade_type = type("Counter", (OntologyObjectFacade,), {
        "__ontology_type_ref__": context.binding.type_ref,
        "__ontology_binding_digest__": context.binding.binding_digest,
        "__ontology_dependency_closure_digest__": context.fragment_closure_digest,
        "__ontology_action_bindings__": tuple((a.action_ref, a.method_name) for a in context.binding.actions),
        **metadata,
    })
    return context.bind(facade_type, action_ref="scalar.read_scalar", invocation_key=key)


def parameter(ref="scalar.read_scalar.number", *, kind=ScalarKind.INTEGER, required=True, nullable=False, position=0):
    return OntologyObjectActionParameterBinding(
        ref, position, ValueShape.scalar(kind), required, nullable, ActionValueMode.VALUE,
    )


def test_completed_value_and_receipt_are_operation_scoped_context_is_reusable():
    invoker = Invoker()
    context = ScalarObjectContext("object:root", binding(), DIGEST, invoker)
    original = counter(context)
    assert asyncio.run(original._invoke_action("scalar.read_scalar")) == 42
    assert original.invocation_receipt is RECEIPT and original.invocation_state == "complete"
    with pytest.raises(ScalarInvocationError, match="operation_consumed"):
        asyncio.run(original._invoke_action("scalar.read_scalar"))
    fresh = counter(context, "business/2")
    assert fresh.invocation_receipt is None
    assert asyncio.run(fresh._invoke_action("scalar.read_scalar")) == 42
    assert [v["invocation_key"] for v in invoker.calls] == ["business/1", "business/2"]


@pytest.mark.parametrize("field,value", [
    ("__ontology_type_ref__", "other.Type"),
    ("__ontology_binding_digest__", "sha256:" + "a" * 64),
    ("__ontology_dependency_closure_digest__", "sha256:" + "a" * 64),
    ("__ontology_action_bindings__", (("scalar.other", "read_scalar"),)),
])
def test_exact_binding_mismatch_refuses_without_contact(field, value):
    invoker = Invoker()
    context = ScalarObjectContext("object:root", binding(), DIGEST, invoker)
    with pytest.raises(ScalarInvocationError, match="binding_mismatch"):
        counter(context, **{field: value})
    assert invoker.calls == []


def test_arguments_keep_abi_order_and_distinguish_omission_from_null():
    invoker = Invoker()
    first = parameter()
    second = parameter("scalar.read_scalar.label", kind=ScalarKind.STRING, required=False, nullable=True, position=1)
    context = ScalarObjectContext("object:root", binding(parameters=(second, first)), DIGEST, invoker)
    obj = counter(context)
    asyncio.run(obj._invoke_action("scalar.read_scalar", **{second.parameter_ref: None, first.parameter_ref: 7}))
    expected: ScalarArguments = ((first.parameter_ref, 7), (second.parameter_ref, None))
    assert invoker.calls[0]["arguments"] == expected
    asyncio.run(counter(context, "business/2")._invoke_action("scalar.read_scalar", **{first.parameter_ref: 7}))
    assert invoker.calls[1]["arguments"] == ((first.parameter_ref, 7),)


@pytest.mark.parametrize("arguments", [{}, {"unknown": 1}, {"scalar.read_scalar.number": True},
                                       {"scalar.read_scalar.number": None}, {"scalar.read_scalar.number": "7"}])
def test_argument_refusal_is_terminal_and_makes_no_contact(arguments):
    invoker = Invoker()
    obj = counter(ScalarObjectContext("object:root", binding(parameters=(parameter(),)), DIGEST, invoker))
    with pytest.raises(ScalarInvocationError, match="invalid_arguments"):
        asyncio.run(obj._invoke_action("scalar.read_scalar", **arguments))
    assert obj.invocation_state == "failed" and invoker.calls == []
    with pytest.raises(ScalarInvocationError, match="operation_consumed"):
        asyncio.run(obj._invoke_action("scalar.read_scalar", **{"scalar.read_scalar.number": 7}))


@pytest.mark.parametrize("failure", [ScalarInvocationError("scalar.timeout", "attempt:1"),
                                     asyncio.CancelledError(), RuntimeError("transport failed")])
def test_dispatch_failure_preserves_original_exception_and_never_retries(failure):
    invoker = Invoker(failure)
    obj = counter(ScalarObjectContext("object:root", binding(), DIGEST, invoker))
    with pytest.raises(type(failure)) as observed:
        asyncio.run(obj._invoke_action("scalar.read_scalar"))
    assert observed.value is failure and obj.invocation_state == "failed"
    assert obj.invocation_receipt is None and len(invoker.calls) == 1
    with pytest.raises(ScalarInvocationError, match="operation_consumed"):
        asyncio.run(obj._invoke_action("scalar.read_scalar"))
    assert len(invoker.calls) == 1


def test_concurrent_duplicate_cannot_dispatch_or_abort_original():
    async def run():
        entered, finish = asyncio.Event(), asyncio.Event()
        class SuspendedInvoker(Invoker):
            async def invoke_action(self, **values):
                self.calls.append(values)
                entered.set()
                await finish.wait()
                return ScalarResult(42, RECEIPT)
        invoker = SuspendedInvoker()
        obj = counter(ScalarObjectContext("object:root", binding(), DIGEST, invoker))
        original = asyncio.create_task(obj._invoke_action("scalar.read_scalar"))
        await entered.wait()
        with pytest.raises(ScalarInvocationError, match="operation_consumed"):
            await obj._invoke_action("scalar.read_scalar")
        assert obj.invocation_state == "pending" and len(invoker.calls) == 1
        finish.set()
        assert await original == 42
        assert obj.invocation_state == "complete"
    asyncio.run(run())


def test_close_prevents_contact_and_context_does_not_supply_snapshots():
    invoker = Invoker()
    obj = counter(ScalarObjectContext("object:root", binding(), DIGEST, invoker))
    obj.close()
    with pytest.raises(ScalarInvocationError, match="operation_consumed"):
        asyncio.run(obj._invoke_action("scalar.read_scalar"))
    assert not hasattr(obj, "_read_field") and invoker.calls == []


def test_bound_action_cannot_be_replaced_with_another_declared_method():
    invoker = Invoker()
    abi = binding(actions=(OntologyObjectActionBinding("scalar.read_scalar", "read_scalar", ()),
                           OntologyObjectActionBinding("scalar.other", "other", ())))
    obj = counter(ScalarObjectContext("object:root", abi, DIGEST, invoker))
    with pytest.raises(ScalarInvocationError, match="action_mismatch"):
        asyncio.run(obj._invoke_action("scalar.other"))
    assert invoker.calls == [] and obj.invocation_state == "failed"


def test_existing_local_scalar_adapter_refuses_arguments_without_wire_downgrade():
    class Transport:
        async def exchange(self, request: bytes) -> bytes:
            pytest.fail("unsupported arguments reached the no-argument wire")
    context = ScalarObjectContext.for_local_scalar(
        client=LocalScalarClient(Transport()), object_ref="object:root",
        binding=binding(parameters=(parameter(),)), fragment_closure_digest=DIGEST,
    )
    obj = counter(context)
    with pytest.raises(ScalarInvocationError, match="arguments_unavailable"):
        asyncio.run(obj._invoke_action("scalar.read_scalar", **{"scalar.read_scalar.number": 7}))
    assert obj.invocation_state == "failed"


def test_omitting_optional_arguments_does_not_downgrade_a_parameterized_action():
    class Transport:
        async def exchange(self, request: bytes) -> bytes:
            pytest.fail("argument-bearing ABI was downgraded to no-argument v1")
    context = ScalarObjectContext.for_local_scalar(
        client=LocalScalarClient(Transport()), object_ref="object:root",
        binding=binding(parameters=(parameter(required=False),)), fragment_closure_digest=DIGEST,
    )
    with pytest.raises(ScalarInvocationError, match="arguments_unavailable"):
        asyncio.run(counter(context)._invoke_action("scalar.read_scalar"))


def test_invalid_completion_receipt_cannot_publish_a_value_or_revive_operation():
    class InvalidInvoker(Invoker):
        async def invoke_action(self, **values):
            self.calls.append(values)
            return ScalarResult(42, ScalarReceipt("invocation:1", "attempt:1", DIGEST, "mutation"))
    invoker = InvalidInvoker()
    obj = counter(ScalarObjectContext("object:root", binding(), DIGEST, invoker))
    with pytest.raises(ScalarInvocationError, match="invalid_result"):
        asyncio.run(obj._invoke_action("scalar.read_scalar"))
    assert obj.invocation_state == "failed" and obj.invocation_receipt is None
    with pytest.raises(ScalarInvocationError, match="operation_consumed"):
        asyncio.run(obj._invoke_action("scalar.read_scalar"))
    assert len(invoker.calls) == 1
