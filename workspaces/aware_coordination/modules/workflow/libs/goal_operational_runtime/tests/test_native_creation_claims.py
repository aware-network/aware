"""Creation declarations, never live ownership, history or fence authority."""

import json

import pytest

from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.native_creation_claims import (
    ABSENCE_SCHEMA, CONTEXT_SCHEMA, EXCLUSION_SCHEMA, GENESIS_SCHEMA, GIT_PROFILE,
    GRANT_SCHEMA, SOURCE_SCHEMA, NativeCreationClaimError, NativeCreationClaimV1,
    check_native_creation_context_claims, decode_native_creation_claim,
    encode_native_creation_claim, make_native_creation_claim,
)


def ref(domain, value):
    return domain + fingerprint({"fixture": value})


def fixture_claims():
    common = dict(namespace_ref="object:namespace:1", namespace_revision_ref="object:revision:1",
                  target_locator_ref="object:goal-location:1")
    request_ref = ref("goal-native-creation-request:", "request")
    creator = "object:creator:1"
    grant = make_native_creation_claim(GRANT_SCHEMA, dict(
        common, creator_ref=creator, initial_owner_ref=creator, request_ref=request_ref,
        permission="create_proposed_goal", authority_profile=GIT_PROFILE,
        authority_source_ref="object:unverified-issue-authority:1",
    ))
    source = make_native_creation_claim(SOURCE_SCHEMA, dict(
        common, provider_ref="object:provider:1", admission_profile="protocol-native-goal-fs-v1",
        admission_authority_ref="object:unverified-source:1",
    ))
    absence = make_native_creation_claim(ABSENCE_SCHEMA, dict(
        common, goal_tag="goal/2026-10-04/new-goal", target_disposition="absent",
        history_profile="goal-native-git-identity-census-v1", history_boundary_ref="object:history:1",
        history_inventory_ref="object:history-inventory:1", identity_inventory_ref="object:identities:1",
    ))
    exclusion = make_native_creation_claim(EXCLUSION_SCHEMA, dict(
        provider_ref="object:provider:1", namespace_ref=common["namespace_ref"],
        repository_binding_ref="object:repository:1", request_ref=request_ref, creator_ref=creator,
        enforcement_profile="goal-native-git-namespace-exclusion-v1",
        enforcement_authority_ref="object:unverified-enforcement:1",
        scope="complete_repository_ref_domain", fence_ref="object:unverified-fence:1",
        acquired_namespace_revision_ref=common["namespace_revision_ref"], acquired_at="2026-10-04T01:00:00Z",
    ))
    context = make_native_creation_claim(CONTEXT_SCHEMA, dict(
        common, provider_ref="object:provider:1", verifier_profile=GIT_PROFILE,
        request_ref=request_ref, creator_ref=creator, initial_owner_ref=creator,
        creation_grant_ref=grant.reference, source_admission_ref=source.reference,
        identity_absence_ref=absence.reference, namespace_exclusion_ref=exclusion.reference,
        verified_at="2026-10-04T01:00:01Z",
    ))
    genesis = make_native_creation_claim(GENESIS_SCHEMA, dict(
        origin_profile="native_genesis_v1", target_execution_authority_profile="phase_native_operational_v1",
        legacy_execution_disposition="not_applicable",
        creation_intent_ref=ref("goal-native-creation-intent:", "intent"),
    ))
    return context, grant, source, absence, exclusion, genesis


def author_changed(claim, **changes):
    body = claim.to_wire()
    schema = body.pop("schema_id")
    body = {key: value for key, value in body.items() if key != reference_field(claim)}
    return make_native_creation_claim(schema, dict(body, **changes))


def reference_field(claim):
    return next(key for key, value in claim.to_wire().items() if value == claim.reference)


def redigested_payload(claim, **changes):
    body = dict(claim.to_wire(), **changes)
    field = reference_field(claim)
    domain = claim.reference.split("sha256:")[0]
    body[field] = domain + fingerprint({key: value for key, value in body.items() if key != field})
    return json.dumps(body)


@pytest.mark.parametrize("index", range(6))
def test_round_trip_and_detached_body_grant_no_authority(index):
    claim = fixture_claims()[index]
    restored = decode_native_creation_claim(encode_native_creation_claim(claim))
    assert restored.to_wire() == claim.to_wire()
    detached = claim.to_wire()
    detached["schema_id"] = "foreign"
    assert claim.to_wire()["schema_id"] != "foreign"
    for attribute in ("verifier_token", "outcome", "live_handle", "publish", "require_verified"):
        assert not hasattr(restored, attribute)


@pytest.mark.parametrize("index", range(6))
@pytest.mark.parametrize("invalid", [True, 1, 1.2, None, [], {}, "", " spaced ", "bad\x00token", "\ud800"])
def test_exact_text_fields_not_coerced(index, invalid):
    claim = fixture_claims()[index]
    field = "creation_intent_ref" if index == 5 else "namespace_ref"
    with pytest.raises((NativeCreationClaimError, UnicodeError)):
        decode_native_creation_claim(redigested_payload(claim, **{field: invalid}))


@pytest.mark.parametrize("index", range(6))
def test_extra_fields_refuse_even_after_digest_recomputed(index):
    with pytest.raises(NativeCreationClaimError):
        decode_native_creation_claim(redigested_payload(fixture_claims()[index], caller_current=True))


@pytest.mark.parametrize("index", range(6))
def test_missing_field_and_stale_reference_refuse(index):
    claim = fixture_claims()[index]
    body = claim.to_wire()
    body.pop("schema_id")
    with pytest.raises(NativeCreationClaimError):
        decode_native_creation_claim(json.dumps(body))
    body = claim.to_wire()
    body[reference_field(claim)] = ref("foreign:", "digest")
    with pytest.raises(NativeCreationClaimError):
        decode_native_creation_claim(json.dumps(body))


@pytest.mark.parametrize("index", range(6))
def test_post_construction_mutation_refuses_on_consumption(index):
    claim = fixture_claims()[index]
    object.__setattr__(claim, "canonical_body", redigested_payload(claim, unknown="x"))
    with pytest.raises(NativeCreationClaimError):
        encode_native_creation_claim(claim)


@pytest.mark.parametrize("payload", ['[]', 'null', 'true', '1', '{', '{"schema_id":"x","schema_id":"x"}'])
def test_invalid_json_and_duplicate_keys_refuse(payload):
    with pytest.raises(NativeCreationClaimError):
        decode_native_creation_claim(payload)


@pytest.mark.parametrize("index,field,value", [
    (0, "verifier_profile", "caller"), (1, "permission", "approve_phase"),
    (2, "admission_profile", "raw_root"), (3, "history_profile", "current_tree_only"),
    (3, "target_disposition", "unknown"), (4, "scope", "selected_branch"),
    (4, "enforcement_profile", "advisory_lock"), (5, "origin_profile", "legacy"),
    (5, "legacy_execution_disposition", "retired"),
    (0, "verified_at", "2026-02-30T01:00:00Z"), (4, "acquired_at", "2026-10-04T01:00:00+00:00"),
    (0, "initial_owner_ref", "object:foreign-owner"),
    (0, "request_ref", ref("foreign:", "request")),
])
def test_closed_profiles_owner_times_and_reference_domains(index, field, value):
    with pytest.raises(NativeCreationClaimError):
        decode_native_creation_claim(redigested_payload(fixture_claims()[index], **{field: value}))


def test_join_is_consistency_only_and_does_not_seal_unverified_sources():
    assert check_native_creation_context_claims(*fixture_claims()[:5]) is None


@pytest.mark.parametrize("index,field,value", [
    (1, "namespace_ref", "object:foreign-namespace"),
    (2, "target_locator_ref", "object:foreign-location"),
    (3, "namespace_revision_ref", "object:foreign-revision"),
    (4, "provider_ref", "object:foreign-provider"),
    (4, "creator_ref", "object:foreign-creator"),
    (4, "request_ref", ref("goal-native-creation-request:", "foreign")),
    (4, "acquired_namespace_revision_ref", "object:foreign-revision"),
    (4, "acquired_at", "2026-10-04T02:00:00Z"),
])
def test_join_refuses_substitution_even_when_context_names_recomputed_claim(index, field, value):
    claims = list(fixture_claims()[:5])
    claims[index] = author_changed(claims[index], **{field: value})
    ref_field = ("creation_grant_ref", "source_admission_ref", "identity_absence_ref", "namespace_exclusion_ref")[index-1]
    claims[0] = author_changed(claims[0], **{ref_field: claims[index].reference})
    with pytest.raises(NativeCreationClaimError):
        check_native_creation_context_claims(*claims)


def test_join_revalidates_mutated_context_and_rejects_wrong_exact_type():
    claims = list(fixture_claims()[:5])
    object.__setattr__(claims[0], "canonical_body", redigested_payload(claims[0], request_ref="invalid"))
    with pytest.raises(NativeCreationClaimError):
        check_native_creation_context_claims(*claims)
    with pytest.raises(NativeCreationClaimError):
        encode_native_creation_claim(object())


def test_genesis_cannot_contain_fabricated_retirement_provenance():
    genesis = fixture_claims()[-1]
    with pytest.raises(NativeCreationClaimError):
        decode_native_creation_claim(redigested_payload(genesis, parity_ref="fake"))
    assert type(genesis) is NativeCreationClaimV1
