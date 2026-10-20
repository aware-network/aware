"""Original enum schema membership with immutable reacquisition data."""

import asyncio
from dataclasses import replace

import pytest
from aware_meta_type_schema import TypeDefinition, TypeKind, TypeSchemaBundle
from aware_ontology_object_facade_client import owner_values as v
from aware_ontology_object_facade_client.observation import (
    ObjectReadContext,
    ObjectReadError,
    ObjectReadResult,
    OntologyObjectState,
)

D = "sha256:" + "a" * 64
T = "workflow.Issue"


def fixture():
    enum = TypeDefinition(
        "workflow.IssueStatus",
        "IssueStatus",
        TypeKind.ENUM,
        enum_values=("open", "in_progress", "blocked", "closed"),
    )
    schema = TypeSchemaBundle.create(
        namespace="workflow", semantic_version="1", types=(enum,)
    )
    binding = v.OntologyObjectClassBinding.create(
        type_ref=T,
        class_name="Issue",
        actions=(),
        relationships=(),
        fields=(
            v.OntologyObjectFieldBinding(
                T + ".status", "status", v.ValueShape.named(enum.type_ref), True, False
            ),
        ),
    )

    class IssueState(OntologyObjectState):
        __slots__ = ()
        __ontology_type_ref__ = T
        __ontology_binding_digest__ = binding.binding_digest
        __ontology_dependency_closure_digest__ = D
        __ontology_schema_digest__ = schema.schema_digest

        @property
        def status(self):
            return self._read_field(T + ".status")

    class Reader:
        revision, status, change = "R1", "open", None

        async def acquire(self, request):
            value = v.OntologyObjectValue.create(
                v.ObjectInstance(
                    "issue:1",
                    T,
                    (
                        v.FieldValue(
                            T + ".status",
                            v.RuntimeValue.of(v.ValueKind.JSON, self.status),
                        ),
                    ),
                )
            )
            authority = v.OntologyObjectSnapshotAuthorityData.create(
                value_digest=value.value_digest,
                provider_authority=v.OntologyObjectProviderAuthorityClaim(
                    "local_operational",
                    "provider",
                    "authority",
                    "generation",
                    None,
                    None,
                ),
                class_binding_digest=binding.binding_digest,
                topology_digest=D,
                branch_ref="branch",
                revision_ref=self.revision,
                projection_ref="projection",
                view_digest=D,
            )
            result = ObjectReadResult(
                request.read_ref,
                v.OntologyObjectSnapshotData.create(value=value, authority=authority),
                request.configuration_binding,
                b"original-history",
                v.ProjectionCoverage(v.CoverageGrade.COMPLETE),
                (T + ".status",),
            )
            return self.change(result) if self.change else result

    reader = Reader()
    context = ObjectReadContext(
        binding,
        D,
        "provider",
        "generation",
        "branch",
        "projection",
        b"configuration",
        reader,
        schema,
    )
    target = v.OntologyRuntimeActionInstanceRefTarget(
        T, "provider", "generation", "issue:1"
    )
    return context, reader, IssueState, target


def test_enum_reacquisition_keeps_r1_immutable_and_has_no_execution_port():
    c, reader, cls, target = fixture()
    bound = c.bind(cls, target)
    first = asyncio.run(bound.acquire())
    reader.revision, reader.status = "R2", "in_progress"
    second = asyncio.run(bound.acquire())
    assert (first.revision_ref, first.state.status) == ("R1", "open")
    assert (second.revision_ref, second.state.status) == ("R2", "in_progress")
    with pytest.raises(AttributeError):
        first.state.status = "closed"
    assert not hasattr(first.state, "start_progress")


@pytest.mark.parametrize("value", ["unknown", 1, True, None])
def test_enum_values_are_original_members_not_coerced(value):
    c, reader, cls, target = fixture()
    reader.status = value
    with pytest.raises(ObjectReadError, match="invalid_field"):
        asyncio.run(c.bind(cls, target).acquire())


def test_enum_without_schema_or_with_substituted_generated_schema_refuses():
    c, _, cls, target = fixture()
    with pytest.raises(ObjectReadError, match="unsupported_profile"):
        replace(c, schema=None)
    cls.__ontology_schema_digest__ = "sha256:" + "b" * 64
    with pytest.raises(ObjectReadError, match="binding_mismatch"):
        c.bind(cls, target)


def test_configuration_and_expected_revision_are_independent_read_joins():
    c, reader, cls, target = fixture()
    with pytest.raises(ObjectReadError, match="revision_conflict"):
        asyncio.run(c.bind(cls, target).acquire(expected_revision_ref="R0"))
    reader.change = lambda result: replace(
        result, configuration_binding=b"other-config"
    )
    with pytest.raises(ObjectReadError, match="invalid_result"):
        asyncio.run(c.bind(cls, target).acquire())
