"""Consumer observation semantics; synthetic data does not qualify a backend."""

import asyncio
from dataclasses import replace

import pytest
from aware_ontology_object_facade_client import owner_values as v
from aware_ontology_object_facade_client.observation import (
    ObjectReadContext,
    ObjectReadError,
    ObjectReadResult,
    OntologyObjectState,
)

DIGEST = "sha256:" + "a" * 64


def fixture():
    binding = v.OntologyObjectClassBinding.create(
        type_ref="T",
        class_name="Thing",
        actions=(),
        relationships=(),
        fields=(
            v.OntologyObjectFieldBinding(
                "T.size", "size", v.ValueShape.scalar(v.ScalarKind.INTEGER), True, False
            ),
        ),
    )

    class ThingState(OntologyObjectState):
        __slots__ = ()
        __ontology_type_ref__ = "T"
        __ontology_binding_digest__ = binding.binding_digest
        __ontology_dependency_closure_digest__ = DIGEST

        @property
        def size(self):
            return self._read_field("T.size")

    class Reader:
        calls = 0
        revision = "R1"
        size = 42
        change = None

        async def acquire(self, request):
            self.calls += 1
            value = v.OntologyObjectValue.create(
                v.ObjectInstance(
                    "thing:1",
                    "T",
                    (
                        v.FieldValue(
                            "T.size", v.RuntimeValue.of(v.ValueKind.INTEGER, self.size)
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
                topology_digest=DIGEST,
                branch_ref="branch",
                revision_ref=self.revision,
                projection_ref="projection",
                view_digest=DIGEST,
            )
            result = ObjectReadResult(
                request.read_ref,
                v.OntologyObjectSnapshotData.create(value=value, authority=authority),
                request.configuration_binding,
                b"original-history",
                v.ProjectionCoverage(v.CoverageGrade.COMPLETE),
                ("T.size",),
            )
            return self.change(result) if self.change else result

    reader = Reader()
    context = ObjectReadContext(
        binding,
        DIGEST,
        "provider",
        "generation",
        "branch",
        "projection",
        b"fixed-configuration",
        reader,
    )
    target = v.OntologyRuntimeActionInstanceRefTarget(
        "T", "provider", "generation", "thing:1"
    )
    return context, reader, ThingState, target


def test_binding_is_pure_and_reacquisition_preserves_old_state():
    context, reader, state_type, target = fixture()
    selection = context.bind(state_type, target)
    assert reader.calls == 0
    first = asyncio.run(selection.acquire())
    reader.size, reader.revision = 43, "R2"
    second = asyncio.run(selection.acquire())
    assert (first.state.size, first.revision_ref) == (42, "R1")
    assert (second.state.size, second.revision_ref) == (43, "R2")
    with pytest.raises(AttributeError):
        first.state.size = 99
    assert not hasattr(first.state, "invoke")
    context.close()
    assert first.state.size == 42
    with pytest.raises(ObjectReadError, match="context_closed"):
        asyncio.run(selection.acquire())
    assert reader.calls == 2


def test_expected_revision_is_not_historical_fallback():
    context, reader, state_type, target = fixture()
    reader.revision = "R2"
    with pytest.raises(ObjectReadError, match="revision_conflict"):
        asyncio.run(state_type.get(target, using=context, expected_revision_ref="R1"))
    assert reader.calls == 1


@pytest.mark.parametrize(
    "change",
    [
        lambda r: replace(r, read_ref="foreign"),
        lambda r: replace(r, configuration_binding=b"other-configuration"),
        lambda r: replace(r, field_refs=()),
        lambda r: replace(
            r, coverage=v.ProjectionCoverage(v.CoverageGrade.PARTIAL, ("T.size",))
        ),
    ],
)
def test_correspondence_and_coverage_refuse_before_state_exposure(change):
    context, reader, state_type, target = fixture()
    reader.change = change
    with pytest.raises(ObjectReadError):
        asyncio.run(state_type.get(target, using=context))


def test_context_closed_during_io_suppresses_response():
    context, reader, state_type, target = fixture()

    def close(result):
        context.close()
        return result

    reader.change = close
    with pytest.raises(ObjectReadError, match="context_closed"):
        asyncio.run(state_type.get(target, using=context))


def test_wrong_provider_refuses_without_contact():
    context, reader, state_type, target = fixture()
    with pytest.raises(ObjectReadError, match="binding_mismatch"):
        asyncio.run(
            state_type.get(replace(target, provider_generation="other"), using=context)
        )
    assert reader.calls == 0


def test_get_is_lazy_until_awaited_and_reacquires_an_immutable_observation():
    context, reader, state_type, target = fixture()
    pending = state_type.get(target, using=context, expected_revision_ref="R1")
    assert reader.calls == 0
    first = asyncio.run(pending)
    assert first.history_correspondence == b"original-history"
    reader.revision, reader.size = "R2", 43
    second = asyncio.run(state_type.get(target, using=context))
    assert (first.state.size, first.revision_ref) == (42, "R1")
    assert (second.state.size, second.revision_ref) == (43, "R2")
    assert reader.calls == 2
    # Field access cannot dispatch another read; state has no retained reader.
    assert first.state.size == first.state.size == 42
    assert reader.calls == 2
    context.close()
    assert second.state.size == 43
    with pytest.raises(ObjectReadError, match="context_closed"):
        asyncio.run(state_type.get(target, using=context))
    assert reader.calls == 2


def test_get_requires_explicit_injected_context():
    _, reader, state_type, target = fixture()
    with pytest.raises(TypeError, match="using"):
        state_type.get(target)
    assert reader.calls == 0


def test_declared_get_field_and_subclass_helper_override_refuse_explicitly():
    context, reader, _, _ = fixture()
    binding = v.OntologyObjectClassBinding.create(
        type_ref="T",
        class_name="Thing",
        actions=(),
        relationships=(),
        fields=(
            v.OntologyObjectFieldBinding(
                "T.get", "get", v.ValueShape.scalar(v.ScalarKind.STRING), True, False
            ),
        ),
    )
    with pytest.raises(ObjectReadError, match="state_helper_collision:get"):
        replace(context, binding=binding)
    with pytest.raises(ObjectReadError, match="state_helper_collision:get"):

        class ShadowState(OntologyObjectState):
            @property
            def get(self):
                return self._read_field("T.get")

    assert reader.calls == 0
