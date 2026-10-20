"""Transport consistency only: fixtures are claims, not issued authority."""

import hashlib
import json
import copy

import pytest

from aware_goal_operational_runtime.phase_issued_gate_contracts import (
    ABSENT_ROLE_V2,
    EVIDENCE_PUBLICATION_V2,
    PORTAL_OBLIGATIONS,
    PORTAL_REVIEW_V2,
    PORTAL_LINEAGE_V2,
    LINEAGE_COMPLETENESS_V2,
    PORTAL_STAGE_ISSUES,
    PortalSourceScopeClaimV2,
    IssuedGateArtifactV2,
    IssuedGateCodecError,
    check_portal_review_publication_v2,
    decode_absent_gate_evidence_role_v2,
    decode_issued_gate_artifact_v2,
    encode_issued_gate_artifact_v2,
    make_issued_gate_artifact_v2,
    make_portal_source_scope_claim_v2,
    decode_portal_source_scope_claim_v2,
    check_portal_lineage_claims_v2,
    PORTAL_RETAINED_OUTPUT_V2,
    PortalRetainedOutputInventoryClaimV2,
    decode_portal_retained_output_inventory_claim_v2,
    check_portal_output_publication_claims_v2,
)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _ref(domain, value):
    return domain + _sha(_json(value).encode())


def _review():
    return make_issued_gate_artifact_v2(PORTAL_REVIEW_V2, {
        "coordinate": {"goal_tag": "goal/2026-10-03/customer-goal", "lane_key": "portal", "phase_key": "presentation"},
        "definition_ref": _ref("goal-phase-definition:", "definition"),
        "gate_digest": _sha(b"gate"),
        "lineage_ref": _ref("goal-phase-accepted-lineage:", "lineage"),
        "proof_publication_ref": _ref("goal-evidence-publication-binding:", "proof"),
        "source_scope_ref": _ref("goal-phase-source-scope:", "source"),
        "reviewer_execution_id": "provider-reviewer-execution",
        "obligations": [{"key": key, "finding": "accepted", "proof_record_refs": [
            _ref("goal-portal-proof-record:", key)
        ]} for key in PORTAL_OBLIGATIONS],
        "limitation_dispositions": [],
        "verdict": "accepted",
    })


def _identity(value):
    return {"blob_ref": "object:immutable:" + hashlib.sha256(value).hexdigest(),
            "sha256": _sha(value), "byte_count": len(value)}


def _issue(revision):
    scope = ["customer/issues/review.md", "customer/evidence/review.json"]
    return {
        "issue_coordinate": scope[0], "issue_tag": "issue:customer:review",
        "content_identity": _identity(revision.encode()), "source_revision": revision,
        "owner_execution_id": "provider-reviewer-execution", "lifecycle": "in_progress",
        "scope": scope, "scope_digest": _sha(_json({"ownership_scope": scope}).encode()),
    }


def _publication(review, raw=None):
    raw = encode_issued_gate_artifact_v2(review).encode() if raw is None else raw
    return make_issued_gate_artifact_v2(EVIDENCE_PUBLICATION_V2, {
        "artifact_schema_id": PORTAL_REVIEW_V2, "artifact_ref": review.reference,
        "artifact_coordinate": "customer/evidence/review.json",
        "artifact_content_identity": _identity(raw),
        "publication_revision": "object:revision:published", "parent_revision": "object:revision:parent",
        "repository_publication_receipt": "repository-commit:object:revision:published",
        "governing_issue_authority": {"parent": _issue("object:revision:parent"),
                                      "publication": _issue("object:revision:published")},
    })


def _redigest(body):
    field, domain = {
        PORTAL_REVIEW_V2: ("review_ref", "goal-phase-portal-review:"),
        EVIDENCE_PUBLICATION_V2: ("binding_ref", "goal-evidence-publication-binding:"),
        PORTAL_LINEAGE_V2: ("lineage_ref", "goal-phase-accepted-lineage:"),
        LINEAGE_COMPLETENESS_V2: ("binding_ref", "goal-portal-lineage-completeness-binding:"),
    }[body["schema_id"]]
    body[field] = _ref(domain, {k: v for k, v in body.items() if k != field})
    return _json(body)


def _mutate(body, path, value):
    target = body
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


def test_claim_round_trip_and_pure_exact_bytes_join_are_provider_neutral():
    review = _review()
    # Retained bytes need not use our encoder's whitespace. Never substitute its
    # normalized bytes when verifying an external raw-content identity.
    raw = (json.dumps(review.to_wire(), indent=2) + "\n").encode()
    publication = _publication(review, raw)
    assert decode_issued_gate_artifact_v2(raw).to_wire() == review.to_wire()
    for artifact in (review, publication):
        assert decode_issued_gate_artifact_v2(encode_issued_gate_artifact_v2(artifact)) == artifact
    assert check_portal_review_publication_v2(review, publication, retained_review_bytes=raw) is None
    # No verifier registration, currentness, observation or acceptance is issued.
    assert not hasattr(review, "verifier_token")
    assert not hasattr(publication, "currentness")


@pytest.mark.parametrize("path,value", [
    (("coordinate", "extra"), "unknown"),
    (("coordinate", "lane_key"), "Invalid_Lane"),
    (("coordinate", "phase_key"), True),
    (("definition_ref",), True),
    (("definition_ref",), "goal-phase-definition:sha256:" + "f" * 63),
    (("gate_digest",), "sha256:" + "F" * 64),
    (("lineage_ref",), "untyped:lineage"),
    (("proof_publication_ref",), "goal-phase-portal-review:sha256:" + "a" * 64),
    (("source_scope_ref",), 7),
    (("reviewer_execution_id",), "provider foreign"),
    (("reviewer_execution_id",), "provider|foreign"),
    (("reviewer_execution_id",), "provider\ud800"),
    (("verdict",), "satisfied"),
    (("obligations", 0, "finding"), "passed"),
    (("obligations", 0, "finding"), "rejected"),
    (("obligations", 0, "key"), "unknown"),
    (("obligations", 0, "proof_record_refs"), []),
    (("obligations", 0, "proof_record_refs"), "one-ref"),
    (("obligations", 0, "proof_record_refs"), [False]),
    (("obligations", 0, "proof_record_refs"), ["verdict:passed"]),
    (("obligations", 0, "extra"), True),
    (("obligations",), {}),
    (("authority_verified",), True),
])
def test_redigested_review_substitutions_refuse(path, value):
    body = _review().to_wire()
    _mutate(body, path, value)
    with pytest.raises(IssuedGateCodecError):
        decode_issued_gate_artifact_v2(_redigest(body))


@pytest.mark.parametrize("mode", ["missing", "extra", "duplicate", "reorder"])
def test_exact_seven_obligation_inventory(mode):
    body = _review().to_wire()
    records = body["obligations"]
    if mode == "missing": records.pop()
    elif mode == "extra": records.append({"key": "foreign", "finding": "accepted", "proof_record_refs": []})
    elif mode == "duplicate": records[-1] = records[0]
    else: records.reverse()
    with pytest.raises(IssuedGateCodecError, match="obligation_inventory|array_order"):
        decode_issued_gate_artifact_v2(_redigest(body))


@pytest.mark.parametrize("mode", ["duplicate", "unsorted"])
def test_proof_references_are_unique_and_sorted(mode):
    body = _review().to_wire()
    a, b = sorted(_ref("goal-portal-proof-record:", x) for x in ("a", "b"))
    body["obligations"][0]["proof_record_refs"] = [a, a] if mode == "duplicate" else [b, a]
    with pytest.raises(IssuedGateCodecError, match="array_order"):
        decode_issued_gate_artifact_v2(_redigest(body))


@pytest.mark.parametrize("finding", ["rejected", "unavailable"])
def test_negative_and_honestly_absent_review_facts_survive_transport(finding):
    body = _review().to_wire()
    body["verdict"] = finding
    body["obligations"][0]["finding"] = finding
    if finding == "unavailable": body["obligations"][0]["proof_record_refs"] = []
    result = decode_issued_gate_artifact_v2(_redigest(body)).to_wire()
    assert result["verdict"] == finding
    assert result["obligations"][0]["finding"] == finding


@pytest.mark.parametrize("disposition", ["in_scope_blocker", "outside_gate", "unverified"])
def test_limitations_are_retained_without_evaluating_or_waiving_them(disposition):
    body = _review().to_wire()
    body["limitation_dispositions"] = [{"key": "known-limit", "evidence_refs": ["evidence:exact-record"],
                                        "disposition": disposition}]
    assert decode_issued_gate_artifact_v2(_redigest(body)).to_wire()["limitation_dispositions"] == body["limitation_dispositions"]


@pytest.mark.parametrize("record", [
    {"key": "limit", "evidence_refs": [], "disposition": "unverified"},
    {"key": "limit", "evidence_refs": [True], "disposition": "outside_gate"},
    {"key": "limit", "evidence_refs": ["evidence:1", "evidence:1"], "disposition": "outside_gate"},
    {"key": "limit", "evidence_refs": ["evidence:1"], "disposition": "waived"},
    {"key": "limit", "evidence_refs": ["evidence:1"], "disposition": "outside_gate", "extra": True},
])
def test_invalid_limitation_records_refuse(record):
    body = _review().to_wire()
    body["limitation_dispositions"] = [record]
    with pytest.raises(IssuedGateCodecError):
        decode_issued_gate_artifact_v2(_redigest(body))


@pytest.mark.parametrize("mode", ["duplicate", "unsorted"])
def test_limitation_records_are_unique_and_sorted(mode):
    body = _review().to_wire()
    a = {"key": "a", "evidence_refs": ["evidence:a"], "disposition": "outside_gate"}
    b = {"key": "b", "evidence_refs": ["evidence:b"], "disposition": "unverified"}
    body["limitation_dispositions"] = [a, a] if mode == "duplicate" else [b, a]
    with pytest.raises(IssuedGateCodecError, match="limitation_inventory"):
        decode_issued_gate_artifact_v2(_redigest(body))


@pytest.mark.parametrize("path,value", [
    (("artifact_schema_id",), "typed:any-authority"),
    (("artifact_ref",), "goal-phase-accepted-lineage:sha256:" + "a" * 64),
    (("artifact_coordinate",), "/customer/review.json"),
    (("artifact_coordinate",), "customer/../review.json"),
    (("artifact_coordinate",), "customer//review.json"),
    (("artifact_coordinate",), "customer\\review.json"),
    (("artifact_coordinate",), "customer/review\u0000.json"),
    (("artifact_content_identity", "byte_count"), True),
    (("artifact_content_identity", "byte_count"), 1.0),
    (("artifact_content_identity", "byte_count"), 0),
    (("artifact_content_identity", "blob_ref"), 42),
    (("artifact_content_identity", "sha256"), "sha256:" + "0" * 65),
    (("artifact_content_identity", "extra"), "unknown"),
    (("parent_revision",), "object:revision:published"),
    (("repository_publication_receipt",), "repository-commit:foreign"),
    (("governing_issue_authority", "parent", "source_revision"), "foreign"),
    (("governing_issue_authority", "publication", "source_revision"), "foreign"),
    (("governing_issue_authority", "parent", "lifecycle"), "closed"),
    (("governing_issue_authority", "publication", "lifecycle"), "open"),
    (("governing_issue_authority", "parent", "scope_digest"), _sha(b"wrong")),
    (("governing_issue_authority", "parent", "scope"), []),
    (("governing_issue_authority", "parent", "scope"), [True]),
    (("governing_issue_authority", "parent", "scope"), ["customer/issues/review.md", "customer/issues/review.md"]),
    (("governing_issue_authority", "publication", "owner_execution_id"), "foreign-execution"),
    (("governing_issue_authority", "publication", "issue_tag"), "issue:foreign"),
    (("governing_issue_authority", "publication", "issue_coordinate"), "customer/issues/foreign.md"),
    (("governing_issue_authority", "parent", "content_identity", "byte_count"), False),
    (("governing_issue_authority", "extra"), "unknown"),
    (("governing_issue_authority", "parent", "extra"), "unknown"),
])
def test_redigested_publication_and_nested_issue_substitutions_refuse(path, value):
    body = _publication(_review()).to_wire()
    _mutate(body, path, value)
    with pytest.raises(IssuedGateCodecError):
        decode_issued_gate_artifact_v2(_redigest(body))


@pytest.mark.parametrize("mode", ["foreign-artifact", "same-path", "no-issue-scope", "repaired-scope"])
def test_exact_parent_issue_scope_is_required_before_publication(mode):
    body = _publication(_review()).to_wire()
    if mode == "foreign-artifact": body["artifact_coordinate"] = "elsewhere/review.json"
    elif mode == "same-path": body["artifact_coordinate"] = "customer/issues/review.md"
    else:
        for epoch in ("parent", "publication"):
            if mode == "repaired-scope" and epoch == "publication": continue
            item = body["governing_issue_authority"][epoch]
            item["scope"] = ["customer/evidence/review.json"]
            item["scope_digest"] = _sha(_json({"ownership_scope": item["scope"]}).encode())
    with pytest.raises(IssuedGateCodecError):
        decode_issued_gate_artifact_v2(_redigest(body))


@pytest.mark.parametrize("mode", ["wrong-ref", "foreign-owner", "byte-count", "digest", "foreign-raw", "normalization"])
def test_pure_review_publication_join_refuses_substitution(mode):
    review = _review()
    raw = encode_issued_gate_artifact_v2(review).encode()
    body = _publication(review).to_wire()
    if mode == "wrong-ref": body["artifact_ref"] = _ref("goal-phase-portal-review:", "foreign")
    elif mode == "foreign-owner":
        for epoch in ("parent", "publication"):
            body["governing_issue_authority"][epoch]["owner_execution_id"] = "foreign-execution"
    elif mode == "byte-count": body["artifact_content_identity"]["byte_count"] += 1
    elif mode == "digest": body["artifact_content_identity"]["sha256"] = _sha(b"foreign")
    elif mode == "foreign-raw":
        changed = review.to_wire()
        changed["reviewer_execution_id"] = "foreign-execution"
        raw = _redigest(changed).encode()
    else: raw += b"\n"
    publication = decode_issued_gate_artifact_v2(_redigest(body))
    with pytest.raises(IssuedGateCodecError):
        check_portal_review_publication_v2(review, publication, retained_review_bytes=raw)


@pytest.mark.parametrize("role", ["proof", "review"])
def test_typed_absence_has_no_publication_or_result(role):
    assert decode_absent_gate_evidence_role_v2(_json({"schema_id": ABSENT_ROLE_V2, "role": role})) == role
    for extra in ({"publication_ref": "invented"}, {"result": "passed"}):
        with pytest.raises(IssuedGateCodecError):
            decode_absent_gate_evidence_role_v2(_json({"schema_id": ABSENT_ROLE_V2, "role": role, **extra}))


@pytest.mark.parametrize("value", [True, 42, "lineage", "evaluator", ""])
def test_unsupported_absent_roles_refuse(value):
    with pytest.raises(IssuedGateCodecError):
        decode_absent_gate_evidence_role_v2(_json({"schema_id": ABSENT_ROLE_V2, "role": value}))


@pytest.mark.parametrize("schema", [
    "aware.goal.phase-portal-proof.v2",
    "aware.goal.phase-portal-retained-output.v2", "aware.goal.issued-gate-evaluation.v2",
    "aware.goal.issued-gate-acceptance-request.v2", "aware.goal.phase-portal-review.v1",
])
def test_unimplemented_profiles_do_not_acquire_a_generic_escape(schema):
    with pytest.raises(IssuedGateCodecError, match="schema_unsupported"):
        make_issued_gate_artifact_v2(schema, {})
    with pytest.raises(IssuedGateCodecError, match="schema_unsupported"):
        decode_issued_gate_artifact_v2(_json({"schema_id": schema}))


def test_duplicate_fields_and_nonfinite_values_refuse_at_any_nesting():
    raw = encode_issued_gate_artifact_v2(_review())
    for bad in (raw.replace('"verdict":"accepted"', '"verdict":"accepted","verdict":"accepted"'),
                raw.replace('"finding":"accepted"', '"finding":"accepted","finding":"accepted"', 1),
                raw.replace('"gate_digest":', '"nonfinite":NaN,"gate_digest":'),
                raw.replace('"gate_digest":', '"nonfinite":Infinity,"gate_digest":'),
                raw.encode("utf-16"), b"\xff", "[]"):
        with pytest.raises(IssuedGateCodecError):
            decode_issued_gate_artifact_v2(bad)


@pytest.mark.parametrize("data", [None, True, 7, {}, bytearray(b"{}")])
def test_decoder_refuses_coerced_input_types(data):
    with pytest.raises(IssuedGateCodecError, match="json_type"):
        decode_issued_gate_artifact_v2(data)


def test_mutation_is_detected_on_consumption_without_repair():
    artifact = _review()
    body = artifact.to_wire()
    body["review_ref"] = _ref("goal-phase-portal-review:", "mutated")
    altered = _json(body)
    object.__setattr__(artifact, "canonical_body", altered)
    for consume in (artifact.to_wire, lambda: artifact.reference,
                    lambda: encode_issued_gate_artifact_v2(artifact)):
        with pytest.raises(IssuedGateCodecError, match="artifact_digest"):
            consume()
        assert artifact.canonical_body == altered


def test_returned_and_constructor_input_mappings_are_detached():
    original = _review()
    body = original.to_wire()
    fields = {k: v for k, v in body.items() if k not in ("schema_id", "review_ref")}
    artifact = make_issued_gate_artifact_v2(PORTAL_REVIEW_V2, fields)
    fields["obligations"][0]["finding"] = "rejected"
    wire = artifact.to_wire()
    wire["obligations"][0]["finding"] = "unavailable"
    assert artifact == original
    assert artifact.to_wire()["obligations"][0]["finding"] == "accepted"


def test_direct_constructor_does_not_silently_normalize_noncanonical_storage():
    with pytest.raises(IssuedGateCodecError, match="artifact_canonical"):
        IssuedGateArtifactV2(json.dumps(_review().to_wire(), indent=2))


def test_claim_digest_tamper_factory_reserved_fields_and_subclasses_refuse():
    body = _review().to_wire()
    body["reviewer_execution_id"] = "foreign-execution"
    with pytest.raises(IssuedGateCodecError, match="artifact_digest"):
        decode_issued_gate_artifact_v2(_json(body))
    for key in ("schema_id", "review_ref"):
        with pytest.raises(IssuedGateCodecError, match="fields"):
            make_issued_gate_artifact_v2(PORTAL_REVIEW_V2, {key: "invented"})
    class Forged(IssuedGateArtifactV2):
        pass
    with pytest.raises(IssuedGateCodecError, match="artifact_type"):
        Forged(_review().canonical_body)


def test_publication_snapshot_scope_order_is_not_silently_sorted():
    body = _publication(_review()).to_wire()
    for epoch in ("parent", "publication"):
        item = body["governing_issue_authority"][epoch]
        item["scope"].reverse()
        item["scope_digest"] = _sha(_json({"ownership_scope": item["scope"]}).encode())
    artifact = decode_issued_gate_artifact_v2(_redigest(body))
    assert artifact.to_wire()["governing_issue_authority"]["parent"]["scope"] == body["governing_issue_authority"]["parent"]["scope"]


def test_recomputed_consistent_claims_still_have_no_verification_authority():
    body = _review().to_wire()
    body["reviewer_execution_id"] = "claimed-foreign-owner"
    review = decode_issued_gate_artifact_v2(_redigest(body))
    publication = _publication(review).to_wire()
    for epoch in ("parent", "publication"):
        publication["governing_issue_authority"][epoch]["owner_execution_id"] = "claimed-foreign-owner"
    claim = decode_issued_gate_artifact_v2(_redigest(publication))
    assert check_portal_review_publication_v2(review, claim,
        retained_review_bytes=encode_issued_gate_artifact_v2(review).encode()) is None
    # This merely joins two self-consistent authored claims. No source provider
    # was involved, and no qualified snapshot or Gate-result API exists here.
    assert type(claim) is IssuedGateArtifactV2
    assert set(claim.to_wire()) == set(publication)


def _source(inventory=None):
    inventory = [{"coordinate": "customer/src/portal.py", "content_identity": _identity(b"current")}] if inventory is None else inventory
    return make_portal_source_scope_claim_v2(epoch_fields={
        "provider_binding_ref": "object:repository:customer", "source_revision": "object:revision:proof-source",
        "goal_coordinate": {"goal_path": "customer/goals/portal.md", "goal_tag": "goal/2026-10-03/customer-goal"},
        "goal_content_identity": _identity(b"committed goal"),
        "document_ref": _ref("goal-phase-document:", "document"),
    }, source_inventory=inventory)


def _lineage_fixture():
    records, authorities, inventory = [], [], []
    # A2-P is terminal; keyed Issue authority order remains independent of DAG order.
    for stage in (0, 1, 3, 2):
        tag = PORTAL_STAGE_ISSUES[stage]
        issue_path, source_path = f"customer/issues/stage-{stage}.md", f"customer/src/stage-{stage}.py"
        scope = [issue_path, source_path]
        parent = "object:revision:base" if not records else records[-1]["revision"]
        before = None
        for kind in ("issue_creation", "implementation", "issue_closeout"):
            revision = f"object:revision:record-{len(records)}"
            after = {
                "issue_coordinate": issue_path, "issue_tag": tag,
                "content_identity": _identity((tag + kind).encode()), "source_revision": revision,
                "owner_execution_id": f"provider-implementer-{stage}",
                "lifecycle": "closed" if kind == "issue_closeout" else "in_progress",
                "scope": scope, "scope_digest": _sha(_json({"ownership_scope": scope}).encode()),
            }
            changes = [{"coordinate": issue_path, "disposition": "administrative",
                        "before": None if before is None else before["content_identity"], "after": after["content_identity"]}]
            if kind == "implementation":
                identity = _identity(f"source {stage}".encode())
                changes.append({"coordinate": source_path, "disposition": "source", "before": None, "after": identity})
                inventory.append({"coordinate": source_path, "content_identity": identity})
            records.append({
                "revision": revision, "parent_revision": parent, "effect_kind": kind,
                "issue_authority": {"parent": before, "publication": after},
                "changed_paths": changes, "repository_publication_receipt": "repository-commit:" + revision,
            })
            # The parent Issue snapshot is resolved at each publication parent.
            before = copy.deepcopy(after)
            parent = revision
        authorities.append(after)
    source = _source(sorted(inventory, key=lambda item: item["coordinate"]))
    common = {name: value for name, value in _review().to_wire().items() if name in ("coordinate", "definition_ref", "gate_digest")}
    paths = sorted(item["coordinate"] for item in inventory)
    fields = {
        **common, "work_history_ref": _ref("goal-phase-work-history:", "ordered work"),
        "mandatory_issue_authorities": sorted(authorities, key=lambda item: item["issue_tag"]),
        "history_base_revision": records[1]["parent_revision"], "terminal_closeout_binding": records[-1],
        "proof_source_epoch": source.to_wire()["source_epoch"], "verification_epoch": source.to_wire()["source_epoch"],
        "record_count": len(records), "records_root": _sha(_json({"records": records}).encode()),
        "implementation_paths": paths, "implementation_paths_root": _sha(_json({"implementation_paths": paths}).encode()),
        "records": records,
    }
    completeness = make_issued_gate_artifact_v2(LINEAGE_COMPLETENESS_V2, fields)
    lineage = make_issued_gate_artifact_v2(PORTAL_LINEAGE_V2, {
        **common, "completeness_binding_ref": completeness.reference,
        "implementation_records": records[:-1], "closeout_record": records[-1], "limitations": [],
    })
    return source, completeness, lineage


def test_source_and_lineage_claim_round_trips_and_exact_consistency_join():
    source, completeness, lineage = _lineage_fixture()
    assert decode_portal_source_scope_claim_v2(source.canonical_body) == source
    for artifact in (completeness, lineage):
        assert decode_issued_gate_artifact_v2(encode_issued_gate_artifact_v2(artifact)) == artifact
        assert not hasattr(artifact, "verifier_token")
    assert check_portal_lineage_claims_v2(lineage, completeness, source) is None
    assert completeness.to_wire()["record_count"] == 12
    assert len(completeness.to_wire()["implementation_paths"]) == 4


@pytest.mark.parametrize("path,value", [
    (("source_epoch", "extra"), "current"),
    (("source_epoch", "provider_binding_ref"), True),
    (("source_epoch", "source_revision"), 7),
    (("source_epoch", "goal_coordinate", "extra"), True),
    (("source_epoch", "goal_coordinate", "goal_path"), "../goal.md"),
    (("source_epoch", "goal_coordinate", "goal_tag"), "wrong-goal"),
    (("source_epoch", "goal_content_identity", "byte_count"), True),
    (("source_epoch", "document_ref"), "goal-phase-document:sha256:" + "a" * 63),
    (("source_epoch", "source_scope_ref"), _ref("goal-phase-source-scope:", "foreign")),
    (("source_inventory", 0, "coordinate"), "/src/portal.py"),
    (("source_inventory", 0, "content_identity", "byte_count"), False),
    (("source_inventory", 0, "content_identity", "extra"), True),
    (("source_inventory", 0, "extra"), True),
    (("currentness",), "current"),
])
def test_source_claim_substitutions_refuse(path, value):
    body = _source().to_wire()
    _mutate(body, path, value)
    with pytest.raises(IssuedGateCodecError):
        decode_portal_source_scope_claim_v2(_json(body))


@pytest.mark.parametrize("inventory", [
    [], [{"coordinate": "customer/a.py", "content_identity": None}] * 2,
    [{"coordinate": "customer/z.py", "content_identity": None}, {"coordinate": "customer/a.py", "content_identity": None}],
])
def test_source_inventory_missing_duplicate_and_unsorted_refuse(inventory):
    with pytest.raises(IssuedGateCodecError, match="source_inventory"):
        _source(inventory)


def test_deleted_and_empty_source_paths_remain_in_the_protected_inventory():
    source = _source([
        {"coordinate": "customer/src/deleted.py", "content_identity": None},
        {"coordinate": "customer/src/empty.py", "content_identity": _identity(b"")},
    ])
    assert source.to_wire()["source_inventory"][0]["content_identity"] is None
    assert source.to_wire()["source_inventory"][1]["content_identity"]["byte_count"] == 0
    with pytest.raises(IssuedGateCodecError, match="empty_content_identity"):
        _source([{"coordinate": "customer/empty.py", "content_identity": {
            "blob_ref": "object:empty", "sha256": _sha(b"foreign"), "byte_count": 0}}])


def test_source_goal_identity_must_agree_if_also_in_inventory():
    with pytest.raises(IssuedGateCodecError, match="source_goal_content"):
        _source([{"coordinate": "customer/goals/portal.md", "content_identity": None}])


@pytest.mark.parametrize("path,value", [
    (("record_count",), True), (("record_count",), 11),
    (("records_root",), _sha(b"smaller")),
    (("implementation_paths_root",), _sha(b"smaller")),
    (("implementation_paths",), []),
    (("records", 1, "extra"), True),
    (("records", 1, "revision"), True),
    (("records", 1, "effect_kind"), "passed"),
    (("records", 1, "repository_publication_receipt"), "repository-commit:foreign"),
    (("records", 1, "issue_authority", "parent", "source_revision"), "foreign"),
    (("records", 1, "issue_authority", "publication", "owner_execution_id"), "foreign-owner"),
    (("records", 1, "issue_authority", "parent", "lifecycle"), "closed"),
    (("records", 1, "changed_paths", 1, "disposition"), "test-count"),
    (("records", 1, "changed_paths", 1, "extra"), True),
    (("records", 1, "changed_paths", 1, "before"), True),
    (("records", 1, "changed_paths", 1, "after", "byte_count"), True),
    (("records", 0, "issue_authority", "parent"), {}),
    (("records", 2, "issue_authority", "publication", "lifecycle"), "in_progress"),
    (("history_base_revision",), "foreign-base"),
    (("work_history_ref",), "untyped:work"),
    (("proof_source_epoch", "goal_coordinate", "goal_tag"), "goal/2026-10-03/foreign-goal"),
    (("verification_epoch", "provider_binding_ref"), "object:repository:foreign"),
    (("verification_epoch", "currentness"), "current"),
])
def test_redigested_completeness_nested_claim_substitutions_refuse(path, value):
    _, completeness, _ = _lineage_fixture()
    body = completeness.to_wire()
    _mutate(body, path, value)
    with pytest.raises(IssuedGateCodecError):
        decode_issued_gate_artifact_v2(_redigest(body))


@pytest.mark.parametrize("mode", ["missing-stage", "duplicate-stage", "foreign-stage", "aliased-path", "record-foreign-owner"])
def test_mandatory_issue_identity_closure_and_record_pairing_refuse(mode):
    _, completeness, _ = _lineage_fixture()
    body = completeness.to_wire()
    if mode == "missing-stage": body["mandatory_issue_authorities"].pop()
    elif mode == "duplicate-stage": body["mandatory_issue_authorities"][-1] = body["mandatory_issue_authorities"][0]
    elif mode == "foreign-stage": body["mandatory_issue_authorities"][0]["issue_tag"] = "fb/2026-10-03/foreign"
    elif mode == "aliased-path": body["mandatory_issue_authorities"][-1]["issue_coordinate"] = body["mandatory_issue_authorities"][0]["issue_coordinate"]
    else: body["mandatory_issue_authorities"][0]["owner_execution_id"] = "foreign-owner"
    with pytest.raises(IssuedGateCodecError):
        decode_issued_gate_artifact_v2(_redigest(body))


@pytest.mark.parametrize("mode", ["duplicate-record", "child-before-parent", "drop-path", "add-path", "reorder-paths", "wrong-terminal"])
def test_lineage_roots_and_declared_record_order_refuse(mode):
    _, completeness, _ = _lineage_fixture()
    body = completeness.to_wire()
    if mode == "duplicate-record": body["records"][1] = body["records"][0]
    elif mode == "child-before-parent": body["records"][0], body["records"][1] = body["records"][1], body["records"][0]
    elif mode == "drop-path": body["implementation_paths"].pop()
    elif mode == "add-path": body["implementation_paths"].append("customer/src/z.py")
    elif mode == "reorder-paths": body["implementation_paths"].reverse()
    else: body["terminal_closeout_binding"] = body["records"][2]
    body["records_root"] = _sha(_json({"records": body["records"]}).encode())
    body["implementation_paths_root"] = _sha(_json({"implementation_paths": body["implementation_paths"]}).encode())
    with pytest.raises(IssuedGateCodecError):
        decode_issued_gate_artifact_v2(_redigest(body))


@pytest.mark.parametrize("mode", ["wrong-completeness", "coordinate", "definition", "gate", "drop-record", "foreign-epoch", "omitted-source-path"])
def test_cross_claim_joins_refuse_with_recomputed_claim_references(mode):
    source, completeness, lineage = _lineage_fixture()
    body = lineage.to_wire()
    if mode == "wrong-completeness": body["completeness_binding_ref"] = _ref("goal-portal-lineage-completeness-binding:", "foreign")
    elif mode == "coordinate": body["coordinate"]["phase_key"] = "foreign-phase"
    elif mode == "definition": body["definition_ref"] = _ref("goal-phase-definition:", "foreign")
    elif mode == "gate": body["gate_digest"] = _sha(b"foreign")
    elif mode == "drop-record": body["implementation_records"].pop(1)
    elif mode == "foreign-epoch":
        changed = source.to_wire()
        changed["source_epoch"]["source_revision"] = "object:revision:foreign"
        source = decode_portal_source_scope_claim_v2(_json(changed))
    else: source = _source(source.to_wire()["source_inventory"][:-1])
    lineage = decode_issued_gate_artifact_v2(_redigest(body))
    with pytest.raises(IssuedGateCodecError):
        check_portal_lineage_claims_v2(lineage, completeness, source)


def test_consistent_smaller_history_is_still_only_a_claim_not_completeness_authority():
    source, completeness, lineage = _lineage_fixture()
    body = completeness.to_wire()
    # Drop an entire claimed implementation publication AND its only source path,
    # recomputing every reference. A codec cannot know the missing Git history.
    body["records"].pop(4)
    body["record_count"] -= 1
    body["records_root"] = _sha(_json({"records": body["records"]}).encode())
    body["implementation_paths"].remove("customer/src/stage-1.py")
    body["implementation_paths_root"] = _sha(_json({"implementation_paths": body["implementation_paths"]}).encode())
    inventory = [item for item in source.to_wire()["source_inventory"] if item["coordinate"] != "customer/src/stage-1.py"]
    source = _source(inventory)
    body["proof_source_epoch"] = source.to_wire()["source_epoch"]
    body["verification_epoch"] = source.to_wire()["source_epoch"]
    smaller = decode_issued_gate_artifact_v2(_redigest(body))
    artifact = lineage.to_wire()
    artifact["completeness_binding_ref"] = smaller.reference
    artifact["implementation_records"] = [item for item in body["records"] if item != artifact["closeout_record"]]
    claimed_lineage = decode_issued_gate_artifact_v2(_redigest(artifact))
    assert check_portal_lineage_claims_v2(claimed_lineage, smaller, source) is None
    assert not hasattr(smaller, "verifier_token")
    # The upcoming concrete provider must derive the twelve actual records and
    # reject this eleven-record subset. No API here issues verification authority.


def test_lineage_limits_preserve_semantic_text_without_minting_a_verdict():
    _, _, lineage = _lineage_fixture()
    body = lineage.to_wire()
    description = "Disclosed failure.\n<!-- aware.goal.lane-phase.document.v1:start -->"
    body["limitations"] = [{"key": "foreign-issuer-failure", "description": description,
                            "evidence_refs": ["evidence:retained-fixture-failure"]}]
    claim = decode_issued_gate_artifact_v2(_redigest(body))
    assert claim.to_wire()["limitations"][0]["description"] == description
    assert "verdict" not in claim.to_wire()


def test_source_and_lineage_postconstruction_mutations_refuse_without_repair():
    source, completeness, lineage = _lineage_fixture()
    body = source.to_wire()
    body["source_inventory"][0]["content_identity"]["sha256"] = _sha(b"mutated")
    changed = _json(body)
    object.__setattr__(source, "canonical_body", changed)
    with pytest.raises(IssuedGateCodecError, match="source_scope_root"):
        check_portal_lineage_claims_v2(lineage, completeness, source)
    assert source.canonical_body == changed
    source = _lineage_fixture()[0]
    body = completeness.to_wire()
    body["record_count"] = True
    object.__setattr__(completeness, "canonical_body", _redigest(body))
    with pytest.raises(IssuedGateCodecError, match="records_root"):
        check_portal_lineage_claims_v2(lineage, completeness, source)


def test_source_inventory_detachment_and_direct_constructor_strictness():
    source = _source()
    wire = source.to_wire()
    wire["source_inventory"][0]["content_identity"] = None
    assert source.to_wire()["source_inventory"][0]["content_identity"] is not None
    with pytest.raises(IssuedGateCodecError, match="artifact_canonical"):
        PortalSourceScopeClaimV2(json.dumps(source.to_wire(), indent=2))


def test_advanced_verification_epoch_does_not_relabel_historical_evidence():
    source, completeness, _ = _lineage_fixture()
    body = completeness.to_wire()
    body["verification_epoch"]["source_revision"] = "object:revision:advanced"
    advanced = decode_issued_gate_artifact_v2(_redigest(body))
    assert advanced.to_wire()["proof_source_epoch"] == source.to_wire()["source_epoch"]
    assert advanced.to_wire()["verification_epoch"]["source_revision"] != source.to_wire()["source_epoch"]["source_revision"]
    assert "currentness" not in advanced.to_wire()


def test_lineage_publication_variant_is_structural_not_an_issued_completeness_binding():
    _, completeness, lineage = _lineage_fixture()
    body = _publication(_review()).to_wire()
    body["artifact_schema_id"], body["artifact_ref"] = PORTAL_LINEAGE_V2, lineage.reference
    body["artifact_content_identity"] = _identity(encode_issued_gate_artifact_v2(lineage).encode())
    publication = decode_issued_gate_artifact_v2(_redigest(body))
    assert publication.to_wire()["artifact_ref"] == lineage.reference
    body["artifact_schema_id"], body["artifact_ref"] = LINEAGE_COMPLETENESS_V2, completeness.reference
    with pytest.raises(IssuedGateCodecError, match="artifact_schema_unsupported"):
        decode_issued_gate_artifact_v2(_redigest(body))


def _output_inventory():
    return [{"artifact_coordinate": f"customer/outputs/{key}.json", "output_schema_id": PORTAL_RETAINED_OUTPUT_V2,
             "output_ref": _ref("goal-phase-portal-retained-output:", key), "sha256": _sha(key.encode()),
             "byte_count": len(key)} for key in ("negative", "pair", "stability", "witness")]


def _output_publication_claims():
    records = _output_inventory()
    scope = ["customer/issues/proof.md"] + [record["artifact_coordinate"] for record in records]
    issue = {epoch: dict(_issue(revision), issue_coordinate=scope[0], issue_tag="issue:customer:proof",
                        scope=scope, scope_digest=_ref("", {"ownership_scope": scope}))
             for epoch, revision in (("parent", "object:revision:parent"), ("publication", "object:revision:published"))}
    bindings = tuple(make_issued_gate_artifact_v2(EVIDENCE_PUBLICATION_V2, {
        "artifact_schema_id": PORTAL_RETAINED_OUTPUT_V2, "artifact_ref": record["output_ref"],
        "artifact_coordinate": record["artifact_coordinate"],
        "artifact_content_identity": _identity(key.encode()),
        "publication_revision": "object:revision:published", "parent_revision": "object:revision:parent",
        "repository_publication_receipt": "repository-commit:object:revision:published",
        "governing_issue_authority": issue,
    }) for record, key in zip(records, ("negative", "pair", "stability", "witness"), strict=True))
    raw = tuple((record["artifact_coordinate"], key.encode())
                for record, key in zip(records, ("negative", "pair", "stability", "witness"), strict=True))
    return decode_portal_retained_output_inventory_claim_v2(_json(records)), bindings, raw


def test_output_publication_byte_join_is_only_consistency():
    inventory, bindings, raw = _output_publication_claims()
    assert check_portal_output_publication_claims_v2(inventory, bindings, raw) is None
    # These are intentionally not valid owner outputs: no issuer is fabricated.
    assert raw[0][1] == b"negative"
    with pytest.raises(IssuedGateCodecError):
        decode_issued_gate_artifact_v2(raw[0][1])
    assert check_portal_output_publication_claims_v2(
        decode_portal_retained_output_inventory_claim_v2("[]"), (), (),
    ) is None


@pytest.mark.parametrize("mode", ["missing-binding", "extra-binding", "reordered-binding", "missing-bytes",
                                    "duplicate-bytes", "foreign-bytes", "text-bytes", "ref", "sha", "count", "epoch", "issue", "mutation"])
def test_output_publication_claim_substitutions_refuse(mode):
    inventory, bindings, raw = _output_publication_claims()
    if mode == "missing-binding": bindings = bindings[:-1]
    elif mode == "extra-binding": bindings += (bindings[0],)
    elif mode == "reordered-binding": bindings = tuple(reversed(bindings))
    elif mode == "missing-bytes": raw = raw[:-1]
    elif mode == "duplicate-bytes": raw = (raw[1],) + raw[1:]
    elif mode == "foreign-bytes": raw = ((raw[0][0], b"foreign"),) + raw[1:]
    elif mode == "text-bytes": raw = ((raw[0][0], "negative"),) + raw[1:]
    else:
        body = bindings[0].to_wire()
        if mode == "ref": body["artifact_ref"] = _ref("goal-phase-portal-retained-output:", "foreign")
        elif mode == "sha": body["artifact_content_identity"]["sha256"] = _sha(b"foreign")
        elif mode == "count": body["artifact_content_identity"]["byte_count"] += 1
        elif mode == "epoch":
            body["publication_revision"] = "object:revision:other"
            body["repository_publication_receipt"] = "repository-commit:object:revision:other"
            body["governing_issue_authority"]["publication"]["source_revision"] = "object:revision:other"
        elif mode == "issue":
            for snapshot in body["governing_issue_authority"].values(): snapshot["owner_execution_id"] = "foreign-owner"
        if mode == "mutation":
            object.__setattr__(bindings[0], "canonical_body", _json(body | {"passed": True}))
        else: bindings = (decode_issued_gate_artifact_v2(_redigest(body)),) + bindings[1:]
    with pytest.raises(IssuedGateCodecError):
        check_portal_output_publication_claims_v2(inventory, bindings, raw)


def test_prepublication_output_inventory_claim_round_trip_and_absence():
    inventory = _output_inventory()
    artifact = decode_portal_retained_output_inventory_claim_v2(_json(inventory))
    assert artifact.to_wire() == inventory
    wire = artifact.to_wire()
    wire[0]["byte_count"] = True
    assert artifact.to_wire() == inventory
    assert decode_portal_retained_output_inventory_claim_v2("[]").to_wire() == []
    assert not hasattr(artifact, "verifier_token")
    # No output record/owner schema or producer was decoded or authenticated.
    assert not hasattr(artifact, "result")


@pytest.mark.parametrize("path,value", [
    ((0, "artifact_coordinate"), "../foreign/output.json"),
    ((0, "output_schema_id"), "typed:arbitrary-authority"),
    ((0, "output_ref"), "output:passed"),
    ((0, "output_ref"), True),
    ((0, "sha256"), "sha256:" + "F" * 64),
    ((0, "byte_count"), True), ((0, "byte_count"), 0), ((0, "byte_count"), 1.0),
    ((0, "publication_revision"), "invented-future-revision"),
    ((0, "blob_ref"), "invented-future-blob"),
    ((0, "passed"), True),
])
def test_output_inventory_unknown_profiles_and_future_authority_claims_refuse(path, value):
    inventory = _output_inventory()
    _mutate(inventory, path, value)
    with pytest.raises(IssuedGateCodecError):
        decode_portal_retained_output_inventory_claim_v2(_json(inventory))


@pytest.mark.parametrize("mode", ["duplicate-path", "duplicate-ref", "unsorted"])
def test_output_inventory_coordinates_and_refs_are_unique_and_sorted(mode):
    inventory = _output_inventory()
    if mode == "duplicate-path": inventory[1]["artifact_coordinate"] = inventory[0]["artifact_coordinate"]
    elif mode == "duplicate-ref": inventory[1]["output_ref"] = inventory[0]["output_ref"]
    else: inventory.reverse()
    with pytest.raises(IssuedGateCodecError, match="output_inventory"):
        decode_portal_retained_output_inventory_claim_v2(_json(inventory))


def test_output_inventory_mutation_and_noncanonical_constructor_refuse():
    inventory = decode_portal_retained_output_inventory_claim_v2(_json(_output_inventory()))
    body = inventory.to_wire()
    body[0]["byte_count"] = True
    changed = _json(body)
    object.__setattr__(inventory, "canonical_body", changed)
    with pytest.raises(IssuedGateCodecError, match="byte_count"):
        inventory.to_wire()
    assert inventory.canonical_body == changed
    with pytest.raises(IssuedGateCodecError, match="artifact_canonical"):
        PortalRetainedOutputInventoryClaimV2(json.dumps(_output_inventory(), indent=2))


@pytest.mark.parametrize("mode", ["no-path-change", "wrong-issue-effect", "foreign-scope", "same-blob-new-sha", "path-duplicate", "unknown-limitation"])
def test_lineage_effect_and_limitations_internal_consistency_refuse(mode):
    _, _, lineage = _lineage_fixture()
    body = lineage.to_wire()
    record = body["implementation_records"][1]
    if mode == "no-path-change": record["changed_paths"][1]["before"] = copy.deepcopy(record["changed_paths"][1]["after"])
    elif mode == "wrong-issue-effect": record["changed_paths"][0]["after"] = _identity(b"foreign issue")
    elif mode == "foreign-scope": record["changed_paths"][1]["coordinate"] = "elsewhere/foreign.py"
    elif mode == "same-blob-new-sha":
        record["changed_paths"][1]["before"] = copy.deepcopy(record["changed_paths"][1]["after"])
        record["changed_paths"][1]["before"]["sha256"] = _sha(b"foreign")
    elif mode == "path-duplicate": record["changed_paths"].append(copy.deepcopy(record["changed_paths"][1]))
    else: body["limitations"] = [{"key": "limit", "description": "Disclosed", "evidence_refs": ["evidence:1"], "waived": True}]
    with pytest.raises(IssuedGateCodecError):
        decode_issued_gate_artifact_v2(_redigest(body))


def test_source_evolution_and_identical_restore_remain_two_explicit_records():
    source, completeness, _ = _lineage_fixture()
    body = completeness.to_wire()
    original_root = body["records_root"]
    current = source.to_wire()["source_inventory"][0]["content_identity"]
    original_identity = copy.deepcopy(current)
    for index, after in enumerate((_identity(b"changed source"), original_identity)):
        revision, parent = f"object:revision:evolution-{index}", body["records"][-1]["revision"]
        before_issue = _issue(parent)
        before_issue["issue_coordinate"], before_issue["issue_tag"] = "customer/issues/evolution.md", "issue:customer:evolution"
        before_issue["scope"] = ["customer/issues/evolution.md", "customer/src/stage-0.py"]
        before_issue["scope_digest"] = _sha(_json({"ownership_scope": before_issue["scope"]}).encode())
        after_issue = copy.deepcopy(before_issue)
        after_issue["source_revision"] = revision
        body["records"].append({"revision": revision, "parent_revision": parent, "effect_kind": "source_evolution",
            "issue_authority": {"parent": before_issue, "publication": after_issue},
            "changed_paths": [{"coordinate": "customer/src/stage-0.py", "disposition": "source", "before": current, "after": after}],
            "repository_publication_receipt": "repository-commit:" + revision})
        current = after
    body["record_count"] = len(body["records"])
    body["records_root"] = _sha(_json({"records": body["records"]}).encode())
    claim = decode_issued_gate_artifact_v2(_redigest(body))
    assert claim.to_wire()["records_root"] != original_root
    assert claim.to_wire()["record_count"] == 14
    assert claim.to_wire()["records"][-1]["changed_paths"][0]["after"] == original_identity
    assert "currentness" not in claim.to_wire()


def test_missing_and_removed_paths_cannot_disappear_from_a_given_lineage_root():
    _, completeness, _ = _lineage_fixture()
    body = completeness.to_wire()
    # A deletion is an explicit event; the historical path union remains protected.
    parent = body["records"][-1]["revision"]
    before_issue = _issue(parent)
    before_issue["scope"].append("customer/src/stage-0.py")
    before_issue["scope_digest"] = _sha(_json({"ownership_scope": before_issue["scope"]}).encode())
    after_issue = copy.deepcopy(before_issue)
    after_issue["source_revision"] = "object:revision:delete"
    identity = body["records"][1]["changed_paths"][1]["after"]
    body["records"].append({"revision": "object:revision:delete", "parent_revision": parent,
        "effect_kind": "source_evolution", "issue_authority": {"parent": before_issue, "publication": after_issue},
        "changed_paths": [{"coordinate": "customer/src/stage-0.py", "disposition": "source", "before": identity, "after": None}],
        "repository_publication_receipt": "repository-commit:object:revision:delete"})
    body["record_count"] = len(body["records"])
    body["records_root"] = _sha(_json({"records": body["records"]}).encode())
    assert "customer/src/stage-0.py" in decode_issued_gate_artifact_v2(_redigest(body)).to_wire()["implementation_paths"]
    body["implementation_paths"].remove("customer/src/stage-0.py")
    body["implementation_paths_root"] = _sha(_json({"implementation_paths": body["implementation_paths"]}).encode())
    with pytest.raises(IssuedGateCodecError, match="paths_root"):
        decode_issued_gate_artifact_v2(_redigest(body))
