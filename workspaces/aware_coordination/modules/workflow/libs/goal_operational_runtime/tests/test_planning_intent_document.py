"""Planning carrier structure does not qualify creator, origin or publication."""

import copy
import json

import pytest
from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.phase_document import (
    decode_goal_phase_native_document,
    extract_goal_phase_native_carrier,
)
from aware_goal_operational_runtime.phase_document_v5 import (
    decode_goal_phase_native_document_v5,
)
from aware_goal_operational_runtime.planning_creation_request import (
    make_planning_goal_creation_request,
)
from aware_goal_operational_runtime.planning_intent_document import (
    DOCUMENT_DOMAIN,
    GoalPlanningIntentDocumentV1,
    decode_goal_planning_intent_document,
    encode_goal_planning_intent_document,
    extract_goal_planning_markdown,
    make_goal_planning_intent_document,
    render_goal_planning_markdown,
    validate_goal_planning_intent_join,
)


def request(**overrides):
    fields = {
        "idempotency_key": "customer-first-goal",
        "goal_tag": "goal/2026-10-17/our-direction",
        "title": "Our direction",
        "intent": "Agree intent before defining meaningful milestones.",
        "owner_ref": "codex-customer-example",
        "definition_of_done_ref": None,
        "priority": "high",
        "locks_ref": None,
        "lanes": [],
        "definitions": [],
        "dependencies": [],
        "unresolved_dependencies": [],
    }
    return make_planning_goal_creation_request({**fields, **overrides})


def creator():
    return {
        "kind": "provider_execution_correlation",
        "execution_id": "codex-customer-example",
        "evidence_ref": "workspace-initial-enrollment:sha256:" + "a" * 64,
    }


def origin():
    return "goal-planning-creation-intent:sha256:" + "b" * 64


def document():
    return make_goal_planning_intent_document(
        request(), creator_binding=creator(), origin_intent_ref=origin()
    )


def redigest(body):
    body = copy.deepcopy(body)
    body["document_ref"] = (
        DOCUMENT_DOMAIN
        + ":"
        + fingerprint(
            {key: value for key, value in body.items() if key != "document_ref"}
        )
    )
    return json.dumps(body).encode()


def test_complete_minimal_planning_document_and_markdown_round_trip():
    source = document()
    body = source.to_wire()
    assert (
        decode_goal_planning_intent_document(
            encode_goal_planning_intent_document(source)
        )
        == source
    )
    assert (
        extract_goal_planning_markdown(render_goal_planning_markdown(source)) == source
    )
    assert source.planning_status == "not_yet_decomposed"
    assert body["lifecycle_status"] == "proposed"
    assert body["origin_profile"] == "repository_initial_authoring_v1"
    assert all(
        body[key] == []
        for key in ("lanes", "definitions", "dependencies", "unresolved_dependencies")
    )
    validate_goal_planning_intent_join(
        source, request(), creator_binding=creator(), origin_intent_ref=origin()
    )
    for field in (
        "execution_authority",
        "operational_bundle",
        "verified",
        "currentness",
        "eligibility",
        "publish",
    ):
        assert field not in body
        assert not hasattr(source, field)


@pytest.mark.parametrize(
    "field,value",
    [
        ("lifecycle_status", "active"),
        ("lifecycle_status", "accepted"),
        ("lifecycle_status", True),
        ("origin_profile", "goal-native-genesis-repository-issue-v1"),
        ("schema_id", "aware.goal.lane-phase.document.v2"),
        ("owner_ref", "codex-foreign"),
        ("goal_tag", "issue/customer"),
        ("priority", False),
        ("title", ""),
        ("intent", None),
        ("definition_of_done_ref", {}),
        ("locks_ref", []),
        ("lanes", [{"placeholder": "lane"}]),
        ("definitions", [{"placeholder": "phase"}]),
        ("dependencies", [{}]),
        ("unresolved_dependencies", [{}]),
        ("origin_intent_ref", "goal-planning-creation-intent:sha256:" + "B" * 64),
        ("origin_intent_ref", "goal-native-creation-intent:sha256:" + "b" * 64),
        ("origin_intent_ref", None),
        ("creator_binding", {}),
        ("operational_bundle", {}),
        ("execution_authority", {}),
        ("work", []),
        ("acceptance", {}),
        ("gate_observations", []),
        ("phase_operation_journal", []),
    ],
)
def test_redigested_semantic_and_authority_substitutions_refuse(field, value):
    body = document().to_wire()
    body[field] = value
    with pytest.raises(ValueError):
        decode_goal_planning_intent_document(redigest(body))


@pytest.mark.parametrize(
    "field,value",
    [
        ("kind", "authenticated_actor"),
        ("execution_id", "codex-foreign"),
        ("execution_id", True),
        ("evidence_ref", "workspace-initial-enrollment:sha256:" + "A" * 64),
        ("evidence_ref", "caller-token"),
        ("verified", True),
        ("actor_ref", "actor:owner"),
    ],
)
def test_redigested_creator_claims_do_not_broaden_local_assurance(field, value):
    body = document().to_wire()
    body["creator_binding"][field] = value
    with pytest.raises(ValueError):
        decode_goal_planning_intent_document(redigest(body))


@pytest.mark.parametrize(
    "field",
    ["goal_tag", "title", "intent", "priority", "definition_of_done_ref", "locks_ref"],
)
def test_recomputed_document_cannot_substitute_for_original_request_join(field):
    body = document().to_wire()
    body[field] = (
        "goal/2026-10-17/foreign"
        if field == "goal_tag"
        else "reference:foreign"
        if field.endswith("_ref")
        else "foreign"
    )
    altered = decode_goal_planning_intent_document(redigest(body))
    with pytest.raises(ValueError, match="source_mismatch"):
        validate_goal_planning_intent_join(
            altered, request(), creator_binding=creator(), origin_intent_ref=origin()
        )


def test_external_creator_and_origin_claim_join_is_exact_but_not_authentication():
    # These are fabricated claims on purpose. Structural acceptance does not
    # yield a verifier token or authorize any effect.
    source = document()
    for binding, ref in (
        (
            {
                **creator(),
                "evidence_ref": "workspace-initial-enrollment:sha256:" + "c" * 64,
            },
            origin(),
        ),
        (creator(), "goal-planning-creation-intent:sha256:" + "c" * 64),
    ):
        with pytest.raises(ValueError, match="source_mismatch"):
            validate_goal_planning_intent_join(
                source, request(), creator_binding=binding, origin_intent_ref=ref
            )
    assert set(source.to_wire()) == {
        "schema_id",
        "goal_tag",
        "title",
        "intent",
        "priority",
        "definition_of_done_ref",
        "locks_ref",
        "owner_ref",
        "creator_binding",
        "lifecycle_status",
        "origin_profile",
        "origin_intent_ref",
        "lanes",
        "definitions",
        "dependencies",
        "unresolved_dependencies",
        "document_ref",
    }


def test_semantic_text_can_contain_all_frame_markers_and_multiline_unicode():
    text = (
        "Direction 雨\n<!-- aware.goal.intent.document.v1:start -->\n```json\n"
        "<!-- aware.goal.intent.document.v1:end -->\n```\n"
        "<!-- aware.goal.lane-phase.document.v1:start -->\n"
        "<!-- aware.goal.lane-phase.document.v1:end -->"
    )
    source = make_goal_planning_intent_document(
        request(title=text, intent=text),
        creator_binding=creator(),
        origin_intent_ref=origin(),
    )
    assert (
        extract_goal_planning_markdown(render_goal_planning_markdown(source)) == source
    )


@pytest.mark.parametrize(
    "kind",
    [
        "duplicate",
        "prefix",
        "suffix",
        "title",
        "owner",
        "status",
        "json_whitespace",
        "crlf",
    ],
)
def test_conflicting_display_duplicate_blocks_and_noncanonical_framing_refuse(kind):
    source = document()
    rendered = render_goal_planning_markdown(source)
    if kind == "duplicate":
        candidate = rendered + rendered
    elif kind == "prefix":
        candidate = b"# Another Goal\n" + rendered
    elif kind == "suffix":
        candidate = rendered + b"\nextra"
    elif kind == "title":
        candidate = rendered.replace(b'- Title: "Our direction"', b'- Title: "Foreign"')
    elif kind == "owner":
        candidate = rendered.replace(
            b'- Owner correlation: "codex-customer-example"',
            b'- Owner correlation: "codex-foreign"',
        )
    elif kind == "status":
        candidate = rendered.replace(b"- Status: Proposed", b"- Status: Active")
    elif kind == "json_whitespace":
        candidate = rendered.replace(
            encode_goal_planning_intent_document(source),
            json.dumps(source.to_wire(), indent=2).encode(),
        )
    else:
        candidate = rendered.replace(b"\n", b"\r\n")
    with pytest.raises(ValueError):
        extract_goal_planning_markdown(candidate)


def test_old_native_readers_refuse_planning_document_and_markdown():
    source = document()
    for decode in (
        decode_goal_phase_native_document,
        decode_goal_phase_native_document_v5,
    ):
        with pytest.raises(ValueError):
            decode(encode_goal_planning_intent_document(source))
    with pytest.raises(ValueError):
        extract_goal_phase_native_carrier(render_goal_planning_markdown(source))


def test_consume_revalidates_without_repair_or_reconstruction():
    source = document()
    body = source.to_wire()
    body["document_ref"] = "foreign"
    altered = json.dumps(body)
    object.__setattr__(source, "canonical_body", altered)
    for consume in (
        encode_goal_planning_intent_document,
        render_goal_planning_markdown,
    ):
        with pytest.raises(ValueError):
            consume(source)
    assert source.canonical_body == altered
    assert isinstance(source, GoalPlanningIntentDocumentV1)


@pytest.mark.parametrize(
    "payload", [b"null", b"[]", b"{", b'{"x":1,"x":2}', b"\xff", "{}", True]
)
def test_invalid_payload_types_duplicates_and_encoding_refuse(payload):
    with pytest.raises(ValueError):
        decode_goal_planning_intent_document(payload)
