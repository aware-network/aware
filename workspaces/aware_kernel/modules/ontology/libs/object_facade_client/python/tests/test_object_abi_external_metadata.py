"""Explicit external metadata profile; no acquisition/navigation/evaluation."""

import pytest
from aware_ontology_object_facade_client import object_abi_codec as codec
from aware_ontology_object_facade_client import owner_values as owner


def example(residence, *, source="Example", target="Dependency"):
    role_payload = {
        "contract": owner.OBJECT_ACTION_ROLES_CONTRACT,
        "topology_digest": "t",
        "actions": [],
    }
    roles = owner.OntologyObjectActionRoleManifest(
        "t", (), owner.digest_payload(owner.OBJECT_ACTION_ROLES_CONTRACT, role_payload)
    )
    relationship = owner.OntologyObjectRelationshipBinding(
        "Example.other",
        "other",
        source,
        target,
        owner.OntologyObjectRelationshipDirection.OUTGOING,
        owner.Cardinality.OPTIONAL_ONE,
        owner.TraversalPolicy.SOURCE_TO_TARGET,
        residence,
    )
    binding = owner.OntologyObjectClassBinding.create(
        type_ref="Example",
        class_name="Example",
        fields=(),
        actions=(),
        relationships=(relationship,),
    )
    payload = {
        "contract": owner.OBJECT_ABI_CONTRACT,
        "topology_digest": "t",
        "schema_digest": "s",
        "schema_slice_digest": "x",
        "action_roles": roles.to_wire(),
        "classes": [binding.to_wire()],
    }
    return owner.OntologyObjectAbi(
        "t",
        "s",
        "x",
        roles,
        (binding,),
        owner.digest_payload(owner.OBJECT_ABI_CONTRACT, payload),
    )


def test_external_metadata_requires_explicit_profile_and_round_trips_unchanged():
    value = example(owner.RelationshipEndpointResidence.EXTERNAL_DEPENDENCY)
    body = codec.encode_object_abi(value)
    with pytest.raises(
        codec.OntologyObjectAbiDecodeError, match="escaped class closure"
    ):
        codec.decode_object_abi(body)
    decoded = codec.decode_object_abi(body, allow_external_dependency_bindings=True)
    assert codec.encode_object_abi(decoded) == body
    assert (
        decoded.classes[0].relationships[0].endpoint_residence
        is owner.RelationshipEndpointResidence.EXTERNAL_DEPENDENCY
    )


def test_explicit_profile_does_not_admit_a_missing_resident_peer():
    with pytest.raises(ValueError, match="escaped class closure"):
        value = example(owner.RelationshipEndpointResidence.RESIDENT_TARGET)
        codec.decode_object_abi(
            codec.encode_object_abi(value), allow_external_dependency_bindings=True
        )


def test_explicit_profile_does_not_admit_a_foreign_relationship_owner():
    with pytest.raises(ValueError, match="escaped class closure"):
        value = example(
            owner.RelationshipEndpointResidence.EXTERNAL_DEPENDENCY, source="Foreign"
        )
        codec.decode_object_abi(
            codec.encode_object_abi(value), allow_external_dependency_bindings=True
        )


@pytest.mark.parametrize("profile", [0, 1, None, "true"])
def test_profile_requires_exact_boolean(profile):
    with pytest.raises(TypeError, match="exact bool"):
        codec.decode_object_abi(b"{}", allow_external_dependency_bindings=profile)
