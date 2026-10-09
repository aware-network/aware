"""Synthetic STRUCTURAL fixtures, not authentic deployment or live authority."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import tomllib
from pathlib import Path
from typing import Any, cast

import pytest

from aware_file_system.guarded_replacement_contract import (
    BODY_SCHEMAS,
    PREFIX,
    GuardedReplacementContractError,
    canonical_json,
    decode_replacement_bytes,
    decode_record,
    derive_body_ref,
    encode_record,
    encode_replacement_bytes,
    signature_input,
    validate_result_links,
)

DIGEST = "sha256:" + "a" * 64
HEX = "a" * 64


def reference(name: str) -> str:
    return PREFIX + name + ":sha256:" + "a" * 64


def fixtures() -> dict[str, dict[str, Any]]:
    content = {"digest": DIGEST, "size": 0}
    file = dict(content=content, uid=1001, gid=1001, mode=384, device_major=8,
                device_minor=1, inode=1, link_count=1)
    storage = dict(storage_id="volume-1", filesystem="ext4", device_major=8,
                   device_minor=1, root_inode=1, anchor_digest=DIGEST,
                   provisioning_profile="fresh_exclusive_volume_v1",
                   exposure_policy="broker_write_admitted_readers_only_v1")
    process = dict(pid=1, start_ticks=1, boot_id=HEX, executable=DIGEST, uid=1001, gid=1001)
    coordinate = dict(kind="observation", repository_binding_ref="workspace:1",
                      state_digest=DIGEST, revision_ref=None, observation=dict(
                          repository_binding_ref="workspace:1", epoch="epoch:1", cursor=0,
                          snapshot_digest=DIGEST, visibility_policy_ref="policy:1", visibility_policy_version="1"))
    common = dict(deployment_ref=reference("deployment.v1"), operation_ref="operation:1",
                  idempotency_key="retry:1", activation_sequence=1)
    intent = dict(**common, live_ref=reference("live.v1"), grant_ref=reference("grant.v1"),
                  session_id="session:1", target_path="customer/sources/é.txt",
                  expected_coordinate=coordinate, before=file, replacement=content, exclusion_id="exclusion:1")
    records: dict[str, dict[str, Any]] = {
        "deployment.v1": dict(
            deployment_id="deployment:1", host_id="host:1", workspace_binding_ref="workspace:1",
            backend="linux_managed_volume_broker_v1", physical_profile="continuous_root_v1",
            operation_profile="guarded_replace_existing_v1", release_digest=DIGEST,
            configuration_digest=DIGEST, storage=storage, writer_uid=1001, writer_gid=1001,
            reader_gids=[1002], policy_digest=DIGEST, publication_ref=reference("deployment-effect.v1"),
            supervisor_issuer_id="supervisor:1", supervisor_key_id=DIGEST,
            broker_issuer_id="broker:1", broker_key_id=DIGEST, workspace_issuer_id="workspace:issuer:1",
            workspace_key_id=DIGEST, activation_sequence=1),
        "issuer-appointment.v1": dict(
            deployment_ref=reference("deployment.v1"), issuer_id="supervisor:1",
            key_id="sha256:" + hashlib.sha256(bytes.fromhex(HEX)).hexdigest(), public_key=HEX,
            role="supervisor", allowed_schemas=sorted(PREFIX + n for n in ("live.v1", "fence.v1", "recovery.v1")), appointment_sequence=1),
        "live.v1": dict(
            deployment_ref=reference("deployment.v1"), challenge=HEX, session_id="session:1",
            activation_sequence=1, policy_sequence=1, observed_boottime_ns=0, expires_boottime_ns=10,
            state="active", broker=process, mount_namespace_id=1, mount_id=1, root=storage,
            configuration_digest=DIGEST, release_digest=DIGEST, writer_policy_digest=DIGEST,
            fencing_record_ref=reference("fence.v1")),
        "grant.v1": dict(
            deployment_ref=reference("deployment.v1"), workspace_binding_ref="workspace:1", holder_id="holder:1",
            operation_ref="operation:1", idempotency_key="retry:1", target_path="custom/root/file",
            purpose="replace_existing", source_admission_ref=reference("workspace-source-admission.v1"),
            policy_sequence=1, issued_boottime_ns=0, expires_boottime_ns=10, boot_id=HEX),
        "admission.v1": dict(**intent, workspace_binding_ref="workspace:1", journal_intent_ref=reference("journal-intent.v1")),
        "result.v1": dict(**common, admission_ref=reference("admission.v1"), status="applied", after=file,
                          stage="complete", journal_result_ref=reference("journal-result.v1"), terminal_live_ref=reference("live.v1"), reason="none"),
        "refusal.v1": dict(request_fingerprint=DIGEST, status="denied", reason="verification_unavailable"),
        "recovery.v1": dict(original_admission_ref=reference("admission.v1"), original_result_ref=None,
                            recovered_result_ref=reference("result.v1"), recovery_live_ref=reference("live.v1"), fencing_record_ref=reference("fence.v1")),
        "deployment-effect.v1": dict(
            deployment_id="deployment:1", host_id="host:1", configuration_digest=DIGEST,
            release_digest=DIGEST, storage=storage, writer_uid=1001, writer_gid=1001,
            reader_gids=[], policy_digest=DIGEST, operator_admission_ref=DIGEST,
            effect_sequence=1, initialization="fresh_before_untrusted_exposure", completed_boottime_ns=1, boot_id=HEX),
        "workspace-source-admission.v1": dict(workspace_binding_ref="workspace:1", holder_id="holder:1",
            target_path="custom/file", purpose="replace_existing", policy_digest=DIGEST,
            policy_sequence=1, boot_id=HEX, issued_boottime_ns=0, expires_boottime_ns=10),
        "fence.v1": dict(deployment_ref=reference("deployment.v1"), activation_sequence=1,
            prior_processes=[], mode="fresh_start", policy_sequence=1, completed_boottime_ns=1, boot_id=HEX),
        "journal-intent.v1": dict(**intent, sequence=1),
        "journal-result.v1": dict(journal_intent_ref=reference("journal-intent.v1"), admission_ref=reference("admission.v1"),
            sequence=2, stage="complete", after=file, file_sync="complete", directory_sync="complete", replacement="complete"),
    }
    return copy.deepcopy({name: dict(schema=PREFIX + name, **body) for name, body in records.items()})


def signed(body: dict[str, Any]) -> dict[str, Any]:
    return dict(schema=PREFIX + "signed.v1", body=body, body_ref=derive_body_ref(body),
                issuer_id="UNTRUSTED:fixture", key_id=DIGEST, signature_profile="ed25519_v1", signature="0" * 128)


@pytest.mark.parametrize("name", [schema[len(PREFIX):] for schema in BODY_SCHEMAS])
def test_every_closed_body_round_trips_without_qualifying_authority(name: str) -> None:
    body = fixtures()[name]
    raw = encode_record(body)
    assert decode_record(raw) == body
    assert encode_record(decode_record(raw)) == raw
    expected = hashlib.sha256(body["schema"].encode() + b"\0" + raw).hexdigest()
    assert derive_body_ref(body) == body["schema"] + ":sha256:" + expected


@pytest.mark.parametrize("name", [schema[len(PREFIX):] for schema in BODY_SCHEMAS if not schema.endswith("refusal.v1")])
def test_envelopes_decode_as_unverified_even_with_fake_signature(name: str) -> None:
    envelope = signed(fixtures()[name])
    assert decode_record(encode_record(envelope)) == envelope
    fields = {key: envelope[key] for key in ("body_ref", "issuer_id", "key_id", "signature_profile")}
    assert signature_input(envelope) == b"aware.managed-replacement.signature.v1\0" + canonical_json(fields)


@pytest.mark.parametrize("name", [schema[len(PREFIX):] for schema in BODY_SCHEMAS])
def test_unknown_and_missing_body_fields_refuse_even_after_redigest(name: str) -> None:
    body = fixtures()[name]
    body["current"] = "true"
    with pytest.raises(GuardedReplacementContractError):
        decode_record(canonical_json(body))
    del body["current"]
    del body[next(key for key in body if key != "schema")]
    with pytest.raises(GuardedReplacementContractError):
        derive_body_ref(body)


@pytest.mark.parametrize("alteration", ["schema", "body_ref", "signature_profile", "signature", "extra"])
def test_envelope_substitution_refuses(alteration: str) -> None:
    envelope = signed(fixtures()["admission.v1"])
    envelope[alteration] = "foreign"
    with pytest.raises(GuardedReplacementContractError):
        decode_record(canonical_json(envelope))


def test_signature_cannot_be_attached_to_refusal() -> None:
    with pytest.raises(GuardedReplacementContractError):
        encode_record(signed(fixtures()["refusal.v1"]))


@pytest.mark.parametrize("raw", [b"{}\n", b" {}", b'{"schema": "foreign"}', b'{"schema":"foreign","schema":"foreign"}',
    b'{"number":NaN}', b'{"number":1.0}', b'{"number":true}', b'{"number":-1}', b'{"number":01}',
    b'{"number":9223372036854775808}', b'{"text":"\\ud800"}', b'{"text":"e\\u0301"}', b'{"text":"\\u00e9"}',
    b'{"text":"a\\/b"}', b'\xef\xbb\xbf{}', b'\xff', b'{"z":0,"a":0}', b'{"schema":"foreign"}'])
def test_noncanonical_invalid_json_and_aliases_refuse(raw: bytes) -> None:
    with pytest.raises(GuardedReplacementContractError):
        decode_record(raw)


def test_parser_rejects_depth_and_size_before_json_recursion() -> None:
    for raw in (b"[" * 25 + b"0" + b"]" * 25, b" " * ((1 << 20) + 1)):
        with pytest.raises(GuardedReplacementContractError):
            decode_record(raw)


@pytest.mark.parametrize("path", ["/file", "a/../b", "a/./b", "a//b", "a/", "", "a\\b", "a\x00b", "a\x7fb", "a\x85b", "e\u0301", "a" * 4097])
def test_target_path_domain_is_neutral_and_strict(path: str) -> None:
    body = fixtures()["grant.v1"]
    body["target_path"] = path
    with pytest.raises(GuardedReplacementContractError):
        encode_record(body)


@pytest.mark.parametrize("key,value", [("activation_sequence", True), ("activation_sequence", 0),
    ("target_path", 1), ("replacement", {"digest": DIGEST, "size": (16 << 20) + 1}),
    ("before", {}), ("deployment_ref", reference("live.v1")), ("operation_ref", "non ascii é")])
def test_nested_types_bounds_and_reference_domains_refuse(key: str, value: object) -> None:
    body = fixtures()["admission.v1"]
    body[key] = value
    with pytest.raises(GuardedReplacementContractError):
        decode_record(canonical_json(body))


@pytest.mark.parametrize("field,value", [("mode", 420), ("link_count", 2), ("uid", 0), ("gid", True),
    ("inode", 0), ("content", {"digest": "sha256:" + "a" * 63, "size": 0})])
def test_file_metadata_never_silently_normalizes(field: str, value: object) -> None:
    body = fixtures()["admission.v1"]
    body["before"][field] = value
    with pytest.raises(GuardedReplacementContractError):
        decode_record(canonical_json(body))


@pytest.mark.parametrize("field", ["repository_binding_ref", "state_digest"])
def test_coordinate_repeated_fields_must_match(field: str) -> None:
    body = fixtures()["admission.v1"]
    body["expected_coordinate"][field] = "other" if field == "repository_binding_ref" else "sha256:" + "b" * 64
    with pytest.raises(GuardedReplacementContractError):
        encode_record(body)


@pytest.mark.parametrize("groups", [[2, 1], [1, 1], [True], list(range(1, 18))])
def test_reader_set_is_sorted_unique_and_bounded(groups: list[object]) -> None:
    body = fixtures()["deployment.v1"]
    body["reader_gids"] = groups
    with pytest.raises(GuardedReplacementContractError):
        encode_record(body)


@pytest.mark.parametrize("mutation", ["wrong_key", "foreign_role", "extra_schema", "duplicate_schema", "wrong_order"])
def test_appointment_does_not_expand_role_or_key(mutation: str) -> None:
    body = fixtures()["issuer-appointment.v1"]
    if mutation == "wrong_key":
        body["key_id"] = DIGEST
    elif mutation == "foreign_role":
        body["role"] = "broker"
    elif mutation == "extra_schema":
        body["allowed_schemas"] = sorted(body["allowed_schemas"] + [PREFIX + "deployment.v1"])
    elif mutation == "duplicate_schema":
        body["allowed_schemas"].append(body["allowed_schemas"][-1])
    else:
        body["allowed_schemas"].reverse()
    with pytest.raises(GuardedReplacementContractError):
        encode_record(body)


@pytest.mark.parametrize("role,names", [
    ("broker", ("admission.v1", "result.v1", "journal-intent.v1", "journal-result.v1")),
    ("workspace", ("grant.v1", "workspace-source-admission.v1", "issuer-appointment.v1")),
])
def test_other_role_assignments_round_trip_without_enrollment(role: str, names: tuple[str, ...]) -> None:
    body = fixtures()["issuer-appointment.v1"]
    body.update(role=role, allowed_schemas=sorted(PREFIX + name for name in names))
    assert decode_record(encode_record(body)) == body


@pytest.mark.parametrize("expiry", [0, 10_000_000_001])
def test_live_window_is_not_repaired(expiry: int) -> None:
    body = fixtures()["live.v1"]
    body["expires_boottime_ns"] = expiry
    with pytest.raises(GuardedReplacementContractError):
        encode_record(body)


def test_fence_rejects_claimed_fresh_start_with_prior_processes() -> None:
    body = fixtures()["fence.v1"]
    body["prior_processes"] = [fixtures()["live.v1"]["broker"]]
    with pytest.raises(GuardedReplacementContractError):
        encode_record(body)
    body["mode"] = "terminated_previous_generation"
    assert decode_record(encode_record(body)) == body  # Claim only: no termination verified.
    body["prior_processes"] *= 2
    with pytest.raises(GuardedReplacementContractError):
        encode_record(body)


@pytest.mark.parametrize("change", [dict(file_sync="failed"), dict(directory_sync="not_started"),
    dict(replacement="unknown"), dict(stage="admitted"), dict(after=None)])
def test_journal_claims_cannot_hide_incomplete_durability(change: dict[str, object]) -> None:
    body = fixtures()["journal-result.v1"]
    body.update(change)
    with pytest.raises(GuardedReplacementContractError):
        decode_record(canonical_json(body))


def test_nested_duplicate_fields_and_unknown_coordinate_fields_refuse() -> None:
    body = fixtures()["admission.v1"]
    raw = encode_record(body)
    raw = raw.replace(b'"link_count":1', b'"link_count":1,"link_count":1')
    with pytest.raises(GuardedReplacementContractError):
        decode_record(raw)
    body["expected_coordinate"]["observation"]["current"] = "yes"
    with pytest.raises(GuardedReplacementContractError):
        decode_record(canonical_json(body))


@pytest.mark.parametrize("change", [dict(status="running"), dict(status="applied", after=None),
    dict(status="applied", terminal_live_ref=None), dict(status="unapplied"),
    dict(status="unapplied", after=None, stage="replaced", reason="authority_refused"),
    dict(status="uncertain", after=None, reason="none")])
def test_result_contradictions_refuse(change: dict[str, object]) -> None:
    body = fixtures()["result.v1"]
    body.update(change)
    with pytest.raises(GuardedReplacementContractError):
        decode_record(canonical_json(body))


@pytest.mark.parametrize("status,stage,reason", [("unapplied", "admitted", "authority_refused"),
    ("unapplied", "staged", "cancelled_before_replace"), ("uncertain", "replaced", "effect_uncertain"),
    ("uncertain", "admitted", "recovery_required"), ("uncertain", "durable", "sync_failed")])
def test_negative_outcomes_remain_explicit(status: str, stage: str, reason: str) -> None:
    body = fixtures()["result.v1"]
    body.update(status=status, stage=stage, reason=reason, after=None, terminal_live_ref=None)
    assert decode_record(encode_record(body))["status"] == status


def linked() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    bodies = fixtures()
    admission, result, journal, live = (bodies[name] for name in ("admission.v1", "result.v1", "journal-result.v1", "live.v1"))
    result["admission_ref"] = journal["admission_ref"] = derive_body_ref(admission)
    result["journal_result_ref"] = derive_body_ref(journal)
    result["terminal_live_ref"] = derive_body_ref(live)
    return result, admission, journal, live


def test_pure_result_join_is_consistency_only_and_requires_every_named_body() -> None:
    result, admission, journal, live = linked()
    validate_result_links(result=result, admission=admission, journal=journal, terminal_live=live)
    with pytest.raises(GuardedReplacementContractError):
        validate_result_links(result=result, admission=admission, journal=journal, terminal_live=None)


def test_admission_rejects_foreign_workspace_binding_in_bare_body() -> None:
    body = fixtures()["admission.v1"]
    body["workspace_binding_ref"] = "workspace:foreign"
    with pytest.raises(GuardedReplacementContractError, match="admission source binding disagreement"):
        encode_record(body)
    with pytest.raises(GuardedReplacementContractError, match="admission source binding disagreement"):
        decode_record(canonical_json(body))


def test_redigested_signed_admission_rejects_foreign_workspace_binding() -> None:
    envelope = signed(fixtures()["admission.v1"])
    body = envelope["body"]
    body["workspace_binding_ref"] = "workspace:foreign"
    # Deliberately bypass validation to reproduce an attacker's public digest.
    envelope["body_ref"] = body["schema"] + ":sha256:" + hashlib.sha256(
        body["schema"].encode("ascii") + b"\0" + canonical_json(body)
    ).hexdigest()
    with pytest.raises(GuardedReplacementContractError, match="admission source binding disagreement"):
        decode_record(canonical_json(envelope))


def test_redigested_result_join_rejects_foreign_admission_workspace_binding() -> None:
    result, admission, journal, live = linked()
    admission["workspace_binding_ref"] = "workspace:foreign"
    # Recompute every affected link without asking the admission validator.
    admission_ref = admission["schema"] + ":sha256:" + hashlib.sha256(
        admission["schema"].encode("ascii") + b"\0" + canonical_json(admission)
    ).hexdigest()
    result["admission_ref"] = journal["admission_ref"] = admission_ref
    result["journal_result_ref"] = derive_body_ref(journal)
    with pytest.raises(GuardedReplacementContractError, match="admission source binding disagreement"):
        validate_result_links(result=result, admission=admission, journal=journal, terminal_live=live)


@pytest.mark.parametrize("change", ["gate_target", "metadata", "replacement", "stage", "operation", "journal", "session"])
def test_redigested_result_link_substitution_still_refuses(change: str) -> None:
    result, admission, journal, live = linked()
    if change == "gate_target":
        result["admission_ref"] = reference("admission.v1")
    elif change in ("metadata", "replacement"):
        after = copy.deepcopy(result["after"])
        after["uid"] = 2000 if change == "metadata" else after["uid"]
        if change == "replacement":
            after["content"] = {"digest": "sha256:" + "b" * 64, "size": 0}
        result["after"] = journal["after"] = after
    elif change == "stage":
        journal["stage"] = "durable"
    elif change == "operation":
        result["operation_ref"] = "other"
    elif change == "journal":
        journal["journal_intent_ref"] = reference("admission.v1")
    else:
        live["session_id"] = "foreign"
    if change != "journal":
        result["journal_result_ref"] = derive_body_ref(journal)
        result["terminal_live_ref"] = derive_body_ref(live)
    with pytest.raises(GuardedReplacementContractError):
        validate_result_links(result=result, admission=admission, journal=journal, terminal_live=live)


def test_decode_returns_independent_unverified_data_and_never_repairs_it() -> None:
    envelope = signed(fixtures()["admission.v1"])
    raw = encode_record(envelope)
    decoded = decode_record(raw)
    cast(dict[str, object], decoded["body"])["target_path"] = "different/target"
    with pytest.raises(GuardedReplacementContractError):
        encode_record(decoded)
    assert decode_record(raw) == envelope
    decoded["body_ref"] = derive_body_ref(decoded["body"])
    assert decode_record(encode_record(decoded)) == decoded  # New claim, still unauthenticated.


@pytest.mark.parametrize("content", [b"", b"\x00\xff\xfe", b"small", b"\xff" * (16 << 20)])
def test_replacement_bytes_are_separate_bounded_canonical_transport(content: bytes) -> None:
    assert decode_replacement_bytes(encode_replacement_bytes(content)) == content


@pytest.mark.parametrize("encoded", ["Zg==", "Zh", "Z", "+w", "/w", "é", "a b", "a\n"])
def test_replacement_encoding_aliases_refuse(encoded: str) -> None:
    with pytest.raises(GuardedReplacementContractError):
        decode_replacement_bytes(encoded)


def test_replacement_limit_is_not_the_authority_wire_limit() -> None:
    with pytest.raises(GuardedReplacementContractError):
        encode_replacement_bytes(b"\x00" * ((16 << 20) + 1))
    with pytest.raises(GuardedReplacementContractError):
        decode_replacement_bytes("a" * ((16 << 20) * 4 // 3 + 2))


def test_canonical_specification_manifest_and_exact_member_projections() -> None:
    # Schema and projection evidence only: the installed FS adapter is a later
    # independent read gate, not silently substituted by this test.
    jsonschema = pytest.importorskip("jsonschema")
    root = next(parent for parent in Path(__file__).resolve().parents if (parent / ".git").exists())
    package = root / "workspaces/aware_kernel/modules/filesystem/docs/specs/filesystem-guarded-replacement"
    manifest = tomllib.loads((package / "aware.spec.toml").read_text())
    schema = json.loads((root / "docs/specs/schemas/aware-spec-v1.schema.json").read_bytes())
    jsonschema.Draft202012Validator(schema).validate(manifest)
    spec_key = manifest["specification"]["key"]
    assert spec_key == "filesystem.guarded-replacement"
    assert manifest["phase_dependencies"] == []
    assert len(manifest["invariants"]) == len(manifest["phases"]) == len(manifest["iterations"]) == 1
    invariant, phase, iteration = (manifest[key][0] for key in ("invariants", "phases", "iterations"))
    for kind, member, index in (("invariant", invariant, "invariants/README.md"), ("phase", phase, "PHASES.md")):
        expected = f'| `specification:{spec_key}/{kind}:{member["key"]}` | `{member["entrypoint"]}` |'
        rows = re.findall(r"^\| `specification:.*$", (package / index).read_text(), re.MULTILINE)
        assert rows == [expected]
    phase_doc = (package / phase["entrypoint"]).read_text()
    assert f'- `{iteration["entrypoint"]}`' in phase_doc
    advances = phase_doc.split("## Advances\n\n", 1)[1].split("\n\n##", 1)[0]
    assert advances == "\n".join(f"- `{ref}`" for ref in phase["invariant_refs"])
    assert iteration["phase_ref"] == f'specification:{spec_key}/phase:{phase["key"]}'
    for path in ("SPEC.md", "invariants/README.md", "PHASES.md", invariant["entrypoint"], phase["entrypoint"], iteration["entrypoint"]):
        raw = (package / path).read_bytes()
        assert raw.endswith(b"\n") and not raw.endswith(b"\n\n") and b"\r" not in raw
    assert not (package / "README.md").exists()
    assert not (package / "iterations/PROTOCOL.md").exists()
