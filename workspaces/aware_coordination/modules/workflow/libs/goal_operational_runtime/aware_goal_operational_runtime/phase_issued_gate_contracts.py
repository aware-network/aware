"""Non-authorizing V2 review, source and lineage contracts.

These are authored claims, NOT verifier outputs. Neither a content reference,
a claimed Issue owner, nor a successful byte/identity join proves issuance.
Concrete providers must independently resolve the complete source authority.
Other issued-Gate evidence variants are deliberately unsupported in this cut.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import cast

from .phase_contracts import GoalPhaseCoordinate, _goal_tag  # pyright: ignore[reportPrivateUsage]

PORTAL_REVIEW_V2 = "aware.goal.phase-portal-review.v2"
PORTAL_LINEAGE_V2 = "aware.goal.phase-accepted-lineage.v2"
LINEAGE_COMPLETENESS_V2 = "aware.goal.portal-lineage-completeness-binding.v2"
PORTAL_RETAINED_OUTPUT_V2 = "aware.goal.phase-portal-retained-output.v2"
EVIDENCE_PUBLICATION_V2 = "aware.goal.evidence-publication-binding.v2"
ABSENT_ROLE_V2 = "aware.goal.evidence-role-absent.v2"
PORTAL_OBLIGATIONS = tuple(sorted((
    "environment_portal", "attention_resolution", "owner_only_carriage",
    "human_agent_parity", "negative_coordinates", "r3c_stability", "f2_stability",
)))

_ARTIFACTS = {
    PORTAL_REVIEW_V2: ("review_ref", "goal-phase-portal-review:"),
    EVIDENCE_PUBLICATION_V2: ("binding_ref", "goal-evidence-publication-binding:"),
    PORTAL_LINEAGE_V2: ("lineage_ref", "goal-phase-accepted-lineage:"),
    LINEAGE_COMPLETENESS_V2: ("binding_ref", "goal-portal-lineage-completeness-binding:"),
}
PORTAL_STAGE_ISSUES = (
    "fb/2026-09-23/actorworld-r4a1-trusted-attention-topology-implementation-v0",
    "fb/2026-09-23/actorworld-r4a2e-experience-presentation-authority-implementation-v0",
    "fb/2026-09-24/actorworld-r4a2p-selected-attach-implementation-v0",
    "fb/2026-09-24/actorworld-r4a2w-environment-portal-witness-implementation-v0",
)
_LINEAGE_FIELDS = {
    "schema_id", "lineage_ref", "coordinate", "definition_ref", "gate_digest",
    "completeness_binding_ref", "implementation_records", "closeout_record", "limitations",
}
_COMPLETENESS_FIELDS = {
    "schema_id", "binding_ref", "coordinate", "definition_ref", "gate_digest",
    "work_history_ref", "mandatory_issue_authorities", "history_base_revision",
    "terminal_closeout_binding", "proof_source_epoch", "record_count", "records_root",
    "implementation_paths_root", "records", "implementation_paths", "verification_epoch",
}
_REVIEW_FIELDS = {
    "schema_id", "review_ref", "coordinate", "definition_ref", "gate_digest",
    "lineage_ref", "proof_publication_ref", "source_scope_ref",
    "reviewer_execution_id", "obligations", "limitation_dispositions", "verdict",
}
_PUBLICATION_FIELDS = {
    "schema_id", "binding_ref", "artifact_schema_id", "artifact_ref",
    "artifact_coordinate", "artifact_content_identity", "publication_revision",
    "parent_revision", "repository_publication_receipt", "governing_issue_authority",
}


class IssuedGateCodecError(ValueError):
    """Malformed or internally contradictory claim; not an authority verdict."""


def _json(value: object) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise IssuedGateCodecError("issued_gate_json_value") from exc


def _parse(data: str | bytes) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise IssuedGateCodecError("issued_gate_duplicate_field")
            result[key] = value
        return result

    def constant(_value: str) -> object:
        raise IssuedGateCodecError("issued_gate_nonfinite_json")

    if type(data) not in (str, bytes):
        raise IssuedGateCodecError("issued_gate_json_type")
    try:
        wire = data.decode("utf-8") if type(data) is bytes else data
        return cast(object, json.loads(wire, object_pairs_hook=pairs, parse_constant=constant))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise IssuedGateCodecError("issued_gate_json_encoding") from exc


def _object(value: object, fields: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(cast(dict[str, object], value)) != fields:
        raise IssuedGateCodecError("issued_gate_fields")
    return cast(dict[str, object], value)


def _token(value: object) -> str:
    if type(value) is not str or not value or "|" in value or any(
        c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value
    ):
        raise IssuedGateCodecError("issued_gate_text")
    try:
        _ = value.encode("utf-8")
    except UnicodeError as exc:
        raise IssuedGateCodecError("issued_gate_text") from exc
    return value


def _path(value: object) -> str:
    if type(value) is not str or not value or any(
        p in ("", ".", "..") for p in value.split("/")
    ) or any(c in value for c in ("\\", ":", "|")) or any(
        ord(c) < 32 or ord(c) == 127 for c in value
    ):
        raise IssuedGateCodecError("issued_gate_path")
    try:
        _ = value.encode("utf-8")
    except UnicodeError as exc:
        raise IssuedGateCodecError("issued_gate_path") from exc
    return value


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _sha(value: object) -> str:
    result = _token(value)
    if re.fullmatch(r"sha256:[0-9a-f]{64}", result) is None:
        raise IssuedGateCodecError("issued_gate_sha256")
    return result


def _ref(value: object, domain: str) -> str:
    result = _token(value)
    if not result.startswith(domain):
        raise IssuedGateCodecError("issued_gate_reference_domain")
    _ = _sha(result[len(domain):])
    return result


def _array(value: object) -> list[object]:
    if type(value) is not list:
        raise IssuedGateCodecError("issued_gate_array")
    return cast(list[object], value)


def _strings(value: object, *, domain: str | None = None, paths: bool = False,
             sorted_items: bool = True, nonempty: bool = True) -> list[str]:
    items = [(_path(v) if paths else _ref(v, domain) if domain else _token(v))
             for v in _array(value)]
    if (nonempty and not items) or len(set(items)) != len(items) or (
        sorted_items and items != sorted(items)
    ):
        raise IssuedGateCodecError("issued_gate_array_order")
    return items


def _coordinate(value: object) -> None:
    body = _object(value, {"goal_tag", "lane_key", "phase_key"})
    try:
        _ = GoalPhaseCoordinate(*(_token(body[k]) for k in ("goal_tag", "lane_key", "phase_key")))
    except (TypeError, ValueError) as exc:
        raise IssuedGateCodecError("issued_gate_coordinate") from exc


def _content_identity(value: object, *, allow_empty: bool = False) -> None:
    body = _object(value, {"blob_ref", "sha256", "byte_count"})
    # Blob/revision identities remain provider-neutral. Git sizes belong to Git.
    _ = _token(body["blob_ref"])
    _ = _sha(body["sha256"])
    count = body["byte_count"]
    if type(count) is not int or count < 0 or (not allow_empty and count == 0):
        raise IssuedGateCodecError("issued_gate_byte_count")
    if count == 0 and body["sha256"] != "sha256:" + hashlib.sha256(b"").hexdigest():
        raise IssuedGateCodecError("issued_gate_empty_content_identity")


def _issue_snapshot(value: object, *, lifecycles: tuple[str, ...] = ("in_progress",)) -> dict[str, object]:
    body = _object(value, {
        "issue_coordinate", "issue_tag", "content_identity", "source_revision",
        "owner_execution_id", "lifecycle", "scope", "scope_digest",
    })
    _ = _path(body["issue_coordinate"])
    for name in ("issue_tag", "source_revision", "owner_execution_id"):
        _ = _token(body[name])
    _content_identity(body["content_identity"])
    if body["lifecycle"] not in lifecycles:
        raise IssuedGateCodecError("issued_gate_publication_issue_lifecycle")
    # Scope is an authored ordered list, not a sorted set. Preserve its digest.
    scope = _strings(body["scope"], paths=True, sorted_items=False)
    if body["scope_digest"] != _digest({"ownership_scope": scope}):
        raise IssuedGateCodecError("issued_gate_issue_scope_digest")
    return body


def _publication(body: dict[str, object]) -> None:
    _ = _object(body, _PUBLICATION_FIELDS)
    # No generic typed-artifact escape: only the implemented variant is admitted.
    if body["artifact_schema_id"] not in (PORTAL_REVIEW_V2, PORTAL_LINEAGE_V2, PORTAL_RETAINED_OUTPUT_V2):
        raise IssuedGateCodecError("issued_gate_artifact_schema_unsupported")
    domain = ("goal-phase-portal-retained-output:" if body["artifact_schema_id"] == PORTAL_RETAINED_OUTPUT_V2
              else _ARTIFACTS[cast(str, body["artifact_schema_id"])][1])
    _ = _ref(body["artifact_ref"], domain)
    artifact_path = _path(body["artifact_coordinate"])
    _content_identity(body["artifact_content_identity"])
    revision, parent = _token(body["publication_revision"]), _token(body["parent_revision"])
    if revision == parent:
        raise IssuedGateCodecError("issued_gate_publication_parent")
    if body["repository_publication_receipt"] != "repository-commit:" + revision:
        raise IssuedGateCodecError("issued_gate_repository_receipt")
    issue = _object(body["governing_issue_authority"], {"parent", "publication"})
    before, after = _issue_snapshot(issue["parent"]), _issue_snapshot(issue["publication"])
    if before["source_revision"] != parent or after["source_revision"] != revision:
        raise IssuedGateCodecError("issued_gate_issue_epoch")
    for name in ("issue_coordinate", "issue_tag", "owner_execution_id", "lifecycle", "scope", "scope_digest"):
        if before[name] != after[name]:
            raise IssuedGateCodecError("issued_gate_issue_parent_disagreement")
    if artifact_path == before["issue_coordinate"] or any(
        p not in cast(list[object], before["scope"])
        for p in (artifact_path, before["issue_coordinate"])
    ):
        raise IssuedGateCodecError("issued_gate_artifact_issue_scope")


def _review(body: dict[str, object]) -> None:
    _ = _object(body, _REVIEW_FIELDS)
    _coordinate(body["coordinate"])
    _ = _ref(body["definition_ref"], "goal-phase-definition:")
    _ = _sha(body["gate_digest"])
    _ = _ref(body["lineage_ref"], "goal-phase-accepted-lineage:")
    _ = _ref(body["proof_publication_ref"], _ARTIFACTS[EVIDENCE_PUBLICATION_V2][1])
    _ = _ref(body["source_scope_ref"], "goal-phase-source-scope:")
    _ = _token(body["reviewer_execution_id"])
    if body["verdict"] not in ("accepted", "rejected", "unavailable"):
        raise IssuedGateCodecError("issued_gate_review_verdict")
    keys: list[str] = []
    findings: list[str] = []
    for item in _array(body["obligations"]):
        record = _object(item, {"key", "finding", "proof_record_refs"})
        keys.append(_token(record["key"]))
        finding = _token(record["finding"])
        if finding not in ("accepted", "rejected", "unavailable"):
            raise IssuedGateCodecError("issued_gate_review_finding")
        findings.append(finding)
        _ = _strings(record["proof_record_refs"], domain="goal-portal-proof-record:",
                     nonempty=finding != "unavailable")
    if tuple(keys) != PORTAL_OBLIGATIONS:
        raise IssuedGateCodecError("issued_gate_obligation_inventory")
    if body["verdict"] == "accepted" and any(f != "accepted" for f in findings):
        raise IssuedGateCodecError("issued_gate_review_contradiction")
    keys = []
    for item in _array(body["limitation_dispositions"]):
        record = _object(item, {"key", "evidence_refs", "disposition"})
        keys.append(_token(record["key"]))
        _ = _strings(record["evidence_refs"])
        if record["disposition"] not in ("in_scope_blocker", "outside_gate", "unverified"):
            raise IssuedGateCodecError("issued_gate_limitation_disposition")
    if keys != sorted(set(keys)):
        raise IssuedGateCodecError("issued_gate_limitation_inventory")


def _source_inventory(value: object) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for item in _array(value):
        record = _object(item, {"coordinate", "content_identity"})
        _ = _path(record["coordinate"])
        if record["content_identity"] is not None:
            _content_identity(record["content_identity"], allow_empty=True)
        records.append(record)
    keys = [cast(str, record["coordinate"]) for record in records]
    if not keys or keys != sorted(set(keys)):
        raise IssuedGateCodecError("issued_gate_source_inventory")
    return records


def _source_scope_ref(inventory: object) -> str:
    return "goal-phase-source-scope:" + _digest({"source_inventory": _source_inventory(inventory)})


def _source_epoch(value: object) -> dict[str, object]:
    body = _object(value, {
        "provider_binding_ref", "source_revision", "goal_coordinate",
        "goal_content_identity", "document_ref", "source_scope_ref",
    })
    _ = _token(body["provider_binding_ref"]), _token(body["source_revision"])
    goal = _object(body["goal_coordinate"], {"goal_path", "goal_tag"})
    _ = _path(goal["goal_path"])
    try:
        _ = _goal_tag(_token(goal["goal_tag"]))
    except (TypeError, ValueError) as exc:
        raise IssuedGateCodecError("issued_gate_source_goal_identity") from exc
    _content_identity(body["goal_content_identity"])
    _ = _ref(body["document_ref"], "goal-phase-document:")
    _ = _ref(body["source_scope_ref"], "goal-phase-source-scope:")
    return body


def _lineage_record(value: object) -> dict[str, object]:
    body = _object(value, {
        "revision", "parent_revision", "issue_authority", "effect_kind",
        "changed_paths", "repository_publication_receipt",
    })
    revision, parent = _token(body["revision"]), _token(body["parent_revision"])
    if revision == parent or body["repository_publication_receipt"] != "repository-commit:" + revision:
        raise IssuedGateCodecError("issued_gate_lineage_revision")
    kind = _token(body["effect_kind"])
    if kind not in ("issue_creation", "issue_update", "issue_closeout", "implementation", "source_evolution"):
        raise IssuedGateCodecError("issued_gate_lineage_effect")
    issue = _object(body["issue_authority"], {"parent", "publication"})
    after = _issue_snapshot(issue["publication"], lifecycles=("open", "in_progress", "blocked", "closed"))
    before: dict[str, object] | None = None
    if kind == "issue_creation":
        if issue["parent"] is not None or after["lifecycle"] not in ("open", "in_progress"):
            raise IssuedGateCodecError("issued_gate_lineage_issue_creation")
    else:
        before = _issue_snapshot(issue["parent"], lifecycles=("open", "in_progress", "blocked", "closed"))
        if before["source_revision"] != parent:
            raise IssuedGateCodecError("issued_gate_issue_epoch")
        for name in ("issue_coordinate", "issue_tag", "owner_execution_id"):
            if before[name] != after[name]:
                raise IssuedGateCodecError("issued_gate_lineage_issue_identity")
        if kind == "issue_closeout":
            if before["lifecycle"] not in ("in_progress", "blocked") or after["lifecycle"] != "closed":
                raise IssuedGateCodecError("issued_gate_lineage_issue_closeout")
        elif kind in ("implementation", "source_evolution"):
            if before["lifecycle"] != "in_progress" or after["lifecycle"] != "in_progress" or before["scope"] != after["scope"]:
                raise IssuedGateCodecError("issued_gate_lineage_source_issue")
        elif before["lifecycle"] == "closed" or after["lifecycle"] == "closed":
            raise IssuedGateCodecError("issued_gate_lineage_unsupported_lifecycle")
    if after["source_revision"] != revision:
        raise IssuedGateCodecError("issued_gate_issue_epoch")
    paths: list[str] = []
    nonadministrative: list[str] = []
    issue_changed = False
    for item in _array(body["changed_paths"]):
        change = _object(item, {"coordinate", "disposition", "before", "after"})
        path = _path(change["coordinate"])
        paths.append(path)
        if change["disposition"] not in ("administrative", "source", "generated", "proof"):
            raise IssuedGateCodecError("issued_gate_changed_path_disposition")
        for name in ("before", "after"):
            if change[name] is not None:
                _content_identity(change[name], allow_empty=True)
        if change["before"] is not None and change["after"] is not None:
            before_identity, after_identity = cast(dict[str, object], change["before"]), cast(dict[str, object], change["after"])
            if before_identity["blob_ref"] == after_identity["blob_ref"] and before_identity != after_identity:
                raise IssuedGateCodecError("issued_gate_immutable_identity_contradiction")
        if change["before"] == change["after"]:
            raise IssuedGateCodecError("issued_gate_unchanged_path_record")
        if path == after["issue_coordinate"]:
            issue_changed = True
            if (change["disposition"] != "administrative" or change["after"] != after["content_identity"] or
                change["before"] != (None if before is None else before["content_identity"])):
                raise IssuedGateCodecError("issued_gate_lineage_issue_effect")
        elif change["disposition"] != "administrative":
            nonadministrative.append(path)
    if not paths or paths != sorted(set(paths)):
        raise IssuedGateCodecError("issued_gate_lineage_changed_paths")
    if kind in ("issue_creation", "issue_update", "issue_closeout") and not issue_changed:
        raise IssuedGateCodecError("issued_gate_lineage_missing_issue_effect")
    if not issue_changed and before is not None and before["content_identity"] != after["content_identity"]:
        raise IssuedGateCodecError("issued_gate_lineage_hidden_issue_effect")
    if kind in ("implementation", "source_evolution") and (
        not nonadministrative or before is None or not set(paths).issubset(cast(list[str], before["scope"]))
    ):
        raise IssuedGateCodecError("issued_gate_lineage_source_scope")
    return body


def _lineage_records(value: object) -> list[dict[str, object]]:
    records = [_lineage_record(item) for item in _array(value)]
    revisions = [cast(str, record["revision"]) for record in records]
    if not records or len(set(revisions)) != len(revisions):
        raise IssuedGateCodecError("issued_gate_lineage_record_inventory")
    positions = {revision: index for index, revision in enumerate(revisions)}
    for index, record in enumerate(records):
        if positions.get(cast(str, record["parent_revision"]), -1) >= index:
            raise IssuedGateCodecError("issued_gate_lineage_parent_order")
    # This checks only declared edges. Full DAG ordering/completeness is derived
    # independently by the repository provider, never by sorting opaque ids.
    return records


def _lineage_paths(records: list[dict[str, object]]) -> list[str]:
    return sorted({cast(str, change["coordinate"]) for record in records
                   for change in cast(list[dict[str, object]], record["changed_paths"])
                   if change["disposition"] != "administrative"})


def _lineage(body: dict[str, object]) -> None:
    _ = _object(body, _LINEAGE_FIELDS)
    _coordinate(body["coordinate"])
    _ = _ref(body["definition_ref"], "goal-phase-definition:"), _sha(body["gate_digest"])
    _ = _ref(body["completeness_binding_ref"], _ARTIFACTS[LINEAGE_COMPLETENESS_V2][1])
    records = _lineage_records(body["implementation_records"])
    closeout = _lineage_record(body["closeout_record"])
    if closeout["effect_kind"] != "issue_closeout" or any(r["revision"] == closeout["revision"] for r in records):
        raise IssuedGateCodecError("issued_gate_lineage_terminal_closeout")
    _limitations(body["limitations"])


def _limitations(value: object) -> None:
    keys: list[str] = []
    for item in _array(value):
        record = _object(item, {"key", "description", "evidence_refs"})
        keys.append(_token(record["key"]))
        description = record["description"]
        if type(description) is not str or not description.strip():
            raise IssuedGateCodecError("issued_gate_limitation_description")
        try:
            _ = description.encode("utf-8")
        except UnicodeError as exc:
            raise IssuedGateCodecError("issued_gate_limitation_description") from exc
        _ = _strings(record["evidence_refs"])
    if keys != sorted(set(keys)):
        raise IssuedGateCodecError("issued_gate_limitation_inventory")


def _completeness(body: dict[str, object]) -> None:
    _ = _object(body, _COMPLETENESS_FIELDS)
    _coordinate(body["coordinate"])
    _ = _ref(body["definition_ref"], "goal-phase-definition:"), _sha(body["gate_digest"])
    _ = _ref(body["work_history_ref"], "goal-phase-work-history:")
    _ = _token(body["history_base_revision"])
    records = _lineage_records(body["records"])
    count = body["record_count"]
    if type(count) is not int or count != len(records) or body["records_root"] != _digest({"records": records}):
        raise IssuedGateCodecError("issued_gate_lineage_records_root")
    paths = _strings(body["implementation_paths"], paths=True)
    if paths != _lineage_paths(records) or body["implementation_paths_root"] != _digest({"implementation_paths": paths}):
        raise IssuedGateCodecError("issued_gate_lineage_paths_root")
    authorities = [_issue_snapshot(item, lifecycles=("open", "in_progress", "blocked", "closed"))
                   for item in _array(body["mandatory_issue_authorities"])]
    tags = [cast(str, authority["issue_tag"]) for authority in authorities]
    coordinates = [cast(str, authority["issue_coordinate"]) for authority in authorities]
    if (tags != sorted(set(tags)) or len(set(coordinates)) != len(coordinates) or
        not set(PORTAL_STAGE_ISSUES).issubset(tags)):
        raise IssuedGateCodecError("issued_gate_mandatory_issue_inventory")
    known = {cast(str, authority["issue_tag"]): authority for authority in authorities}
    for record in records:
        after = cast(dict[str, object], cast(dict[str, object], record["issue_authority"])["publication"])
        if record["effect_kind"] != "source_evolution":
            authority = known.get(cast(str, after["issue_tag"]))
            if authority is None or any(authority[k] != after[k] for k in ("issue_coordinate", "owner_execution_id")):
                raise IssuedGateCodecError("issued_gate_lineage_mandatory_issue_join")
    terminal = _lineage_record(body["terminal_closeout_binding"])
    terminal_issue = cast(dict[str, object], cast(dict[str, object], terminal["issue_authority"])["publication"])
    if terminal["effect_kind"] != "issue_closeout" or terminal not in records or terminal_issue["issue_tag"] != PORTAL_STAGE_ISSUES[2]:
        raise IssuedGateCodecError("issued_gate_lineage_terminal_closeout")
    implementations = [record for record in records if record["effect_kind"] == "implementation"]
    if not implementations or body["history_base_revision"] != implementations[0]["parent_revision"]:
        raise IssuedGateCodecError("issued_gate_lineage_history_base")
    proof_epoch, verified_epoch = _source_epoch(body["proof_source_epoch"]), _source_epoch(body["verification_epoch"])
    goal_tag = cast(dict[str, object], body["coordinate"])["goal_tag"]
    for epoch in (proof_epoch, verified_epoch):
        if cast(dict[str, object], epoch["goal_coordinate"])["goal_tag"] != goal_tag:
            raise IssuedGateCodecError("issued_gate_source_goal_join")
    if any(proof_epoch[k] != verified_epoch[k] for k in ("provider_binding_ref", "goal_coordinate")):
        raise IssuedGateCodecError("issued_gate_source_provider_join")


def _validate(value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise IssuedGateCodecError("issued_gate_fields")
    body = cast(dict[str, object], value)
    schema = _token(body.get("schema_id"))
    if schema not in _ARTIFACTS:
        raise IssuedGateCodecError("issued_gate_schema_unsupported")
    field, domain = _ARTIFACTS[schema]
    if schema == PORTAL_REVIEW_V2:
        _review(body)
    elif schema == EVIDENCE_PUBLICATION_V2:
        _publication(body)
    elif schema == PORTAL_LINEAGE_V2:
        _lineage(body)
    else:
        _completeness(body)
    if body[field] != domain + _digest({k: v for k, v in body.items() if k != field}):
        raise IssuedGateCodecError("issued_gate_artifact_digest")
    return body


@dataclass(frozen=True, slots=True)
class IssuedGateArtifactV2:
    """Immutable canonical CLAIM storage, with validation at every consumption."""

    canonical_body: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        if type(self) is not IssuedGateArtifactV2 or type(self.canonical_body) is not str:
            raise IssuedGateCodecError("issued_gate_artifact_type")
        body = _validate(_parse(self.canonical_body))
        if self.canonical_body != _json(body):
            raise IssuedGateCodecError("issued_gate_artifact_canonical")
        return body  # Fresh nested values; no caller-owned mutable storage.

    @property
    def reference(self) -> str:
        body = self.to_wire()
        field = _ARTIFACTS[cast(str, body["schema_id"])][0]
        return cast(str, body[field])


def decode_issued_gate_artifact_v2(data: str | bytes) -> IssuedGateArtifactV2:
    return IssuedGateArtifactV2(_json(_validate(_parse(data))))


def encode_issued_gate_artifact_v2(artifact: IssuedGateArtifactV2) -> str:
    if type(artifact) is not IssuedGateArtifactV2:
        raise IssuedGateCodecError("issued_gate_artifact_type")
    return _json(artifact.to_wire())


def make_issued_gate_artifact_v2(schema_id: str, fields: dict[str, object]) -> IssuedGateArtifactV2:
    """Derive a claim reference. This is NOT an issuer or verifier entrance."""
    if type(schema_id) is not str or schema_id not in _ARTIFACTS or type(fields) is not dict:
        raise IssuedGateCodecError("issued_gate_schema_unsupported")
    field, domain = _ARTIFACTS[schema_id]
    if "schema_id" in fields or field in fields:
        raise IssuedGateCodecError("issued_gate_fields")
    body = dict(fields, schema_id=schema_id)
    body[field] = domain + _digest(body)
    return decode_issued_gate_artifact_v2(_json(body))


def check_portal_review_publication_v2(
    review: IssuedGateArtifactV2, publication: IssuedGateArtifactV2,
    *, retained_review_bytes: bytes,
) -> None:
    """Check a declared pair and exact bytes only; resolve NO source authority."""
    if type(review) is not IssuedGateArtifactV2 or type(publication) is not IssuedGateArtifactV2:
        raise IssuedGateCodecError("issued_gate_artifact_type")
    value, binding = review.to_wire(), publication.to_wire()
    if (value["schema_id"] != PORTAL_REVIEW_V2 or binding["schema_id"] != EVIDENCE_PUBLICATION_V2 or
        binding["artifact_schema_id"] != PORTAL_REVIEW_V2):
        raise IssuedGateCodecError("issued_gate_pair_profile")
    if type(retained_review_bytes) is not bytes:
        raise IssuedGateCodecError("issued_gate_retained_bytes")
    if (binding["artifact_ref"] != review.reference or
        decode_issued_gate_artifact_v2(retained_review_bytes).to_wire() != value):
        raise IssuedGateCodecError("issued_gate_pair_artifact")
    identity = cast(dict[str, object], binding["artifact_content_identity"])
    if (identity["byte_count"] != len(retained_review_bytes) or
        identity["sha256"] != "sha256:" + hashlib.sha256(retained_review_bytes).hexdigest()):
        raise IssuedGateCodecError("issued_gate_pair_bytes")
    issue = cast(dict[str, object], binding["governing_issue_authority"])
    for epoch in ("parent", "publication"):
        snapshot = cast(dict[str, object], issue[epoch])
        if snapshot["owner_execution_id"] != value["reviewer_execution_id"]:
            raise IssuedGateCodecError("issued_gate_pair_reviewer")


@dataclass(frozen=True, slots=True)
class PortalSourceScopeClaimV2:
    """Canonical source-epoch/inventory CLAIM. Never source verification."""

    canonical_body: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> dict[str, object]:
        if type(self) is not PortalSourceScopeClaimV2 or type(self.canonical_body) is not str:
            raise IssuedGateCodecError("issued_gate_source_claim_type")
        body = _object(_parse(self.canonical_body), {"source_epoch", "source_inventory"})
        epoch = _source_epoch(body["source_epoch"])
        inventory = _source_inventory(body["source_inventory"])
        if epoch["source_scope_ref"] != _source_scope_ref(inventory):
            raise IssuedGateCodecError("issued_gate_source_scope_root")
        goal_path = cast(dict[str, object], epoch["goal_coordinate"])["goal_path"]
        for record in inventory:
            if record["coordinate"] == goal_path and record["content_identity"] != epoch["goal_content_identity"]:
                raise IssuedGateCodecError("issued_gate_source_goal_content")
        if self.canonical_body != _json(body):
            raise IssuedGateCodecError("issued_gate_artifact_canonical")
        return body


def decode_portal_source_scope_claim_v2(data: str | bytes) -> PortalSourceScopeClaimV2:
    return PortalSourceScopeClaimV2(_json(_parse(data)))


def make_portal_source_scope_claim_v2(
    *, epoch_fields: dict[str, object], source_inventory: list[dict[str, object]],
) -> PortalSourceScopeClaimV2:
    """Derive a submitted inventory root, NOT its completeness or currentness."""
    if type(epoch_fields) is not dict or "source_scope_ref" in epoch_fields:
        raise IssuedGateCodecError("issued_gate_source_claim_fields")
    epoch = dict(epoch_fields, source_scope_ref=_source_scope_ref(source_inventory))
    return decode_portal_source_scope_claim_v2(_json({"source_epoch": epoch, "source_inventory": source_inventory}))


def check_portal_lineage_claims_v2(
    lineage: IssuedGateArtifactV2, completeness: IssuedGateArtifactV2,
    source: PortalSourceScopeClaimV2,
) -> None:
    """Pure consistency join. An independently derived complete set is STILL required."""
    if type(lineage) is not IssuedGateArtifactV2 or type(completeness) is not IssuedGateArtifactV2 or type(source) is not PortalSourceScopeClaimV2:
        raise IssuedGateCodecError("issued_gate_lineage_claim_type")
    artifact, binding, scope = lineage.to_wire(), completeness.to_wire(), source.to_wire()
    if artifact["schema_id"] != PORTAL_LINEAGE_V2 or binding["schema_id"] != LINEAGE_COMPLETENESS_V2:
        raise IssuedGateCodecError("issued_gate_lineage_claim_profile")
    if artifact["completeness_binding_ref"] != completeness.reference or any(
        artifact[name] != binding[name] for name in ("coordinate", "definition_ref", "gate_digest")
    ):
        raise IssuedGateCodecError("issued_gate_lineage_claim_binding")
    terminal = binding["terminal_closeout_binding"]
    if artifact["closeout_record"] != terminal or artifact["implementation_records"] != [
        record for record in _array(binding["records"]) if record != terminal
    ]:
        raise IssuedGateCodecError("issued_gate_lineage_claim_records")
    if scope["source_epoch"] != binding["proof_source_epoch"]:
        raise IssuedGateCodecError("issued_gate_lineage_claim_epoch")
    supplied_paths = {record["coordinate"] for record in _source_inventory(scope["source_inventory"])}
    if not set(cast(list[str], binding["implementation_paths"])).issubset(supplied_paths):
        raise IssuedGateCodecError("issued_gate_lineage_claim_source_inventory")


@dataclass(frozen=True, slots=True)
class PortalRetainedOutputInventoryClaimV2:
    """Prepublication output locators/byte identities; no future blobs or issuers."""

    canonical_body: str

    def __post_init__(self) -> None:
        _ = self.to_wire()

    def to_wire(self) -> list[dict[str, object]]:
        if type(self) is not PortalRetainedOutputInventoryClaimV2 or type(self.canonical_body) is not str:
            raise IssuedGateCodecError("issued_gate_output_inventory_type")
        values: list[dict[str, object]] = []
        for item in _array(_parse(self.canonical_body)):
            record = _object(item, {"artifact_coordinate", "output_schema_id", "output_ref", "sha256", "byte_count"})
            _ = _path(record["artifact_coordinate"])
            if record["output_schema_id"] != PORTAL_RETAINED_OUTPUT_V2:
                raise IssuedGateCodecError("issued_gate_output_schema")
            _ = _ref(record["output_ref"], "goal-phase-portal-retained-output:")
            _ = _sha(record["sha256"])
            if type(record["byte_count"]) is not int or record["byte_count"] <= 0:
                raise IssuedGateCodecError("issued_gate_byte_count")
            values.append(record)
        keys = [cast(str, record["artifact_coordinate"]) for record in values]
        refs = [cast(str, record["output_ref"]) for record in values]
        if keys != sorted(set(keys)) or len(set(refs)) != len(refs):
            raise IssuedGateCodecError("issued_gate_output_inventory")
        if self.canonical_body != _json(values):
            raise IssuedGateCodecError("issued_gate_artifact_canonical")
        return values


def decode_portal_retained_output_inventory_claim_v2(data: str | bytes) -> PortalRetainedOutputInventoryClaimV2:
    return PortalRetainedOutputInventoryClaimV2(_json(_parse(data)))


def check_portal_output_publication_claims_v2(
    inventory: PortalRetainedOutputInventoryClaimV2,
    publications: tuple[IssuedGateArtifactV2, ...],
    retained_bytes: tuple[tuple[str, bytes], ...],
) -> None:
    """Join complete declared locators, bindings and bytes; authenticate NOTHING.

    Does not decode owner records, establish output issuance, prove a Git effect,
    or return a qualified output. Arbitrary bytes can pass this consistency join;
    concrete output decoding and provider verification remain mandatory.
    """
    if (type(inventory) is not PortalRetainedOutputInventoryClaimV2 or
        type(publications) is not tuple or type(retained_bytes) is not tuple):
        raise IssuedGateCodecError("issued_gate_output_claim_type")
    records = inventory.to_wire()
    bindings: list[dict[str, object]] = []
    for publication in publications:
        if type(publication) is not IssuedGateArtifactV2:
            raise IssuedGateCodecError("issued_gate_output_claim_type")
        binding = publication.to_wire()
        if (binding["schema_id"] != EVIDENCE_PUBLICATION_V2 or
            binding["artifact_schema_id"] != PORTAL_RETAINED_OUTPUT_V2):
            raise IssuedGateCodecError("issued_gate_output_claim_profile")
        bindings.append(binding)
    paths = [record["artifact_coordinate"] for record in records]
    if [binding["artifact_coordinate"] for binding in bindings] != paths:
        raise IssuedGateCodecError("issued_gate_output_claim_set")
    raw_values: list[bytes] = []
    raw_paths: list[str] = []
    for entry in retained_bytes:
        if type(entry) is not tuple or len(entry) != 2 or type(entry[1]) is not bytes:
            raise IssuedGateCodecError("issued_gate_retained_bytes")
        raw_paths.append(_path(entry[0]))
        raw_values.append(entry[1])
    if raw_paths != paths:
        raise IssuedGateCodecError("issued_gate_output_claim_set")
    common: dict[str, object] | None = None
    for record, binding, raw in zip(records, bindings, raw_values, strict=True):
        identity = cast(dict[str, object], binding["artifact_content_identity"])
        if (binding["artifact_ref"] != record["output_ref"] or
            identity["sha256"] != record["sha256"] or identity["byte_count"] != record["byte_count"] or
            identity["sha256"] != "sha256:" + hashlib.sha256(raw).hexdigest() or
            identity["byte_count"] != len(raw)):
            raise IssuedGateCodecError("issued_gate_output_claim_bytes")
        # First-profile outputs share one declared publication/Issue epoch.
        # This equality is not proof that that commit created any of the files.
        epoch = {key: binding[key] for key in (
            "publication_revision", "parent_revision", "repository_publication_receipt", "governing_issue_authority",
        )}
        if common is not None and epoch != common:
            raise IssuedGateCodecError("issued_gate_output_claim_publication")
        common = epoch


def decode_absent_gate_evidence_role_v2(data: str | bytes) -> str:
    """Return an honestly absent role; no invented publication or outcome."""
    body = _object(_parse(data), {"schema_id", "role"})
    if body["schema_id"] != ABSENT_ROLE_V2 or body["role"] not in ("proof", "review"):
        raise IssuedGateCodecError("issued_gate_absent_role")
    return cast(str, body["role"])
