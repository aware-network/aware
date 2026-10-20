"""Declared constructor successor data/lifetime tests; no backend execution."""

import asyncio
import time
from dataclasses import replace

import pytest
from aware_meta_type_schema import TypeDefinition, TypeKind, TypeSchemaBundle
from aware_ontology_object_facade_client import owner_values as v
from aware_ontology_object_facade_client.actions import ObjectActionError
from aware_ontology_object_facade_client.constructor import (
    ObjectCreationReceipt,
    ObjectCreationResult,
)
from aware_ontology_object_facade_client.factories import (
    ObjectFactoryContext,
    ObjectFactoryResult,
    OntologyObjectFactory,
    require_factory_arguments,
)

D = "sha256:" + "a" * 64
T = "workflow.Issue"
A = T + ".ensure_issue"


def fixture():
    enum = TypeDefinition(
        "workflow.Priority",
        "Priority",
        TypeKind.ENUM,
        enum_values=("low", "medium", "high"),
    )
    schema = TypeSchemaBundle.create(
        namespace="workflow", semantic_version="1", types=(enum,)
    )
    specs = (
        ("title", v.ValueShape.scalar(v.ScalarKind.STRING), True, False),
        ("priority", v.ValueShape.named(enum.type_ref), False, False),
        ("content", v.ValueShape.scalar(v.ScalarKind.UUID), False, True),
    )
    params = tuple(
        v.OntologyObjectActionParameterBinding(
            A + "." + name, i, shape, required, nullable, v.ActionValueMode.VALUE
        )
        for i, (name, shape, required, nullable) in enumerate(specs)
    )
    binding = v.OntologyObjectClassBinding.create(
        type_ref=T,
        class_name="Issue",
        fields=(),
        relationships=(),
        actions=(
            v.OntologyObjectActionBinding(
                A, "ensure_issue", params, v.OntologyObjectActionRole.CONSTRUCTOR
            ),
        ),
    )
    definition = v.SchemaActionDefinition(
        A,
        T,
        tuple(
            v.SchemaActionParameterDefinition(
                p.parameter_ref,
                p.position,
                p.shape,
                p.required,
                p.nullable,
                p.value_mode,
            )
            for p in params
        ),
        v.ValueShape.named(T),
        v.ActionValueMode.INSTANCE_REF,
    )

    class Port:
        def __init__(self):
            self.calls = []
            self.change = None

        async def invoke_constructor(self, request):
            self.calls.append(request)
            creation = ObjectCreationResult(
                T,
                A,
                request.invocation_key,
                binding.binding_digest,
                D,
                v.OntologyRuntimeActionInstanceRefTarget(
                    T, "provider", "generation", "issue:1"
                ),
                ObjectCreationReceipt(
                    "call",
                    "attempt",
                    D,
                    "committed",
                    "provider",
                    "generation",
                    "R1",
                    "commit:1",
                ),
                True,
                True,
                True,
            )
            result = ObjectFactoryResult(request, creation, b"original-history")
            return self.change(result) if self.change else result

    port = Port()
    context = ObjectFactoryContext(
        binding,
        schema,
        definition,
        D,
        "provider",
        "generation",
        "branch",
        "projection",
        b"configuration",
        port,
    )

    class IssueFactory(OntologyObjectFactory):
        __ontology_type_ref__ = T
        __ontology_binding_digest__ = binding.binding_digest
        __ontology_dependency_closure_digest__ = D
        __ontology_schema_digest__ = schema.schema_digest
        __ontology_constructor_ref__ = A

    return context, port, IssueFactory


def operation(context, cls):
    return context.bind(
        cls,
        invocation_key="business:1",
        expected_revision_ref="R0",
        deadline=time.monotonic() + 30.0,
    )


def test_late_success_error_retains_original_attempt_coordinates(monkeypatch):
    context, port, cls = fixture()
    now = [100.0]
    monkeypatch.setattr(
        "aware_ontology_object_facade_client.factories.time.monotonic", lambda: now[0]
    )
    factory = operation(context, cls)

    def late(result):
        now[0] = 1000.0
        return result

    port.change = late
    with pytest.raises(TimeoutError) as caught:
        asyncio.run(factory._invoke_constructor(A, **{A + ".title": "Issue"}))
    assert caught.value.attempt_ref == "attempt"
    assert caught.value.recovery_ref == "attempt"
    assert factory.invocation_state == "failed"
    assert factory.invocation_result.creation.receipt.attempt_ref == "attempt"


def test_omission_and_null_remain_distinct_without_synthesized_defaults():
    c, port, cls = fixture()
    first = operation(c, cls)
    created = asyncio.run(first._invoke_constructor(A, **{A + ".title": "Issue"}))
    assert port.calls[0].arguments == ((A + ".title", "Issue"),)
    assert created.object_reference.instance_ref == "issue:1"
    second = operation(c, cls)
    asyncio.run(
        second._invoke_constructor(A, **{A + ".title": "Issue", A + ".content": None})
    )
    assert port.calls[1].arguments[-1] == (A + ".content", None)
    with pytest.raises(ObjectActionError, match="operation_consumed"):
        asyncio.run(first._invoke_constructor(A, **{A + ".title": "Issue"}))
    assert len(port.calls) == 2


@pytest.mark.parametrize(
    "values",
    [
        {},
        {A + ".title": True},
        {A + ".title": "x", A + ".priority": None},
        {A + ".title": "x", A + ".priority": "unknown"},
        {A + ".title": "x", A + ".content": "not-a-uuid"},
    ],
)
def test_invalid_values_consume_before_dispatch(values):
    c, port, cls = fixture()
    op = operation(c, cls)
    with pytest.raises(ObjectActionError, match="invalid_arguments"):
        asyncio.run(op._invoke_constructor(A, **values))
    assert not port.calls and op.invocation_state == "failed"


def test_required_omission_does_not_hide_unsupported_profile():
    c, _, _ = fixture()
    p = replace(c.definition.parameters[0], value_mode=v.ActionValueMode.INSTANCE_REF)
    definition = replace(c.definition, parameters=(p, *c.definition.parameters[1:]))
    original = c.binding.actions[0]
    binding = v.OntologyObjectClassBinding.create(
        type_ref=T,
        class_name="Issue",
        fields=(),
        relationships=(),
        actions=(
            replace(
                original,
                parameters=(
                    replace(
                        original.parameters[0],
                        value_mode=v.ActionValueMode.INSTANCE_REF,
                    ),
                    *original.parameters[1:],
                ),
            ),
        ),
    )
    with pytest.raises(ObjectActionError, match="unsupported_profile"):
        require_factory_arguments(binding, c.schema, definition, ())


def test_closed_context_after_valid_outcome_preserves_original_result():
    c, port, cls = fixture()
    op = operation(c, cls)

    def change(result):
        c.close()
        return result

    port.change = change
    with pytest.raises(ObjectActionError, match="context_closed"):
        asyncio.run(op._invoke_constructor(A, **{A + ".title": "Issue"}))
    assert op.invocation_result.creation.receipt.attempt_ref == "attempt"
    assert op._context is None


def test_foreign_factory_type_cannot_be_dispatched_by_context():
    c, _, _ = fixture()
    with pytest.raises(ObjectActionError, match="invalid_binding"):
        operation(c, dict)
