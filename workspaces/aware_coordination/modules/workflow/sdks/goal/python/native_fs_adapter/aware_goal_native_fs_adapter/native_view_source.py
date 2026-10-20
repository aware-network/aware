"""Protocol-admitted, committed-source Goal reading; no Goal decision law.

This is a concrete source adapter, not a caller-authored source callback. It
reuses committed Goal/Issue verification and the owners' read projectors.
"""

from __future__ import annotations

# Shared adapter internals retain the accepted Protocol/source boundary.
# pyright: reportPrivateUsage=false
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import cast
from weakref import WeakKeyDictionary

from aware_goal_operational_runtime import (
    GoalPhaseNativeDocumentV2, decode_goal_phase_future_schedule, schedule_path,
    assess_goal_phase_future_schedule, encode_goal_phase_native_document,
)
from aware_goal_operational_runtime.phase_native_view import (
    SOURCE_SCHEMA, canonical_json, validate_goal_native_view_source, goal_native_issue_facets,
)
from aware_issue_runtime import build_issue_development_read_payload_v2
from aware_protocol_fs_adapter.manifest import resolve_repository_path_at_use
from aware_protocol_fs_adapter.native_goal_resolver import require_native_goal_resolver
from .native_lane_source import NativeGitLaneSource
from .phase_operation import _require_native_resolver

PROFILE = "aware.goal.committed-filesystem-view.v2"


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class CommittedGoalViewReading:
    payload_bytes: bytes
    observation_ref: str
    issue_readings_bytes: bytes

    def to_wire(self) -> dict[str, object]:
        return cast(dict[str, object], json.loads(self.payload_bytes))


class CommittedGoalViewSourceProvider(NativeGitLaneSource):
    """A retained provider binding, selected by Service rather than the client."""

    def __init__(self, *, resolver_capability: object, provider_ref: str,
                 provider_generation: str, source_scope_ref: str) -> None:
        super().__init__(resolver_capability=resolver_capability)
        for token in (provider_ref, provider_generation, source_scope_ref):
            if type(token) is not str or not token or any(c.isspace() for c in token):
                raise ValueError("native_view_provider_binding_invalid")
        self.provider_ref = provider_ref
        self.provider_generation = provider_generation
        self.source_scope_ref = source_scope_ref
        self._issued: WeakKeyDictionary[CommittedGoalViewReading, bytes] = WeakKeyDictionary()

    def require_issued(self, reading: CommittedGoalViewReading) -> None:
        if type(reading) is not CommittedGoalViewReading or self._issued.get(reading) != self._fingerprint(reading):
            raise ValueError("native_view_reading_not_issued_or_mutated")
        validate_goal_native_view_source(reading.to_wire())

    def require_current(self, reading: CommittedGoalViewReading) -> None:
        self.require_issued(reading)
        resolver = _require_native_resolver(self._capability)
        root = reading.to_wire()
        source = cast(dict[str, object], root["source"])
        for ref in cast(list[str], source["input_refs"]):
            if not ref.startswith("git-blob:"):
                continue
            path = ref.removeprefix("git-blob:").rsplit(":", 1)[0]
            if resolver.match_goal_path(path) is not None:
                resolver.resolve_goal_path(path)
            elif self._issues.match_issue_path(path):
                self._issues.resolve_issue_path(path)
            elif "/schedules/" in path:
                self._contain_schedule(path, resolver.goal_root)
        resolver.revalidate()
        if self._commit("HEAD") != source["source_revision"]:
            raise ValueError("repository_head_advanced")

    @staticmethod
    def _fingerprint(reading: CommittedGoalViewReading) -> bytes:
        return hashlib.sha256(canonical_json([
            reading.payload_bytes.hex(), reading.observation_ref, reading.issue_readings_bytes.hex(),
        ])).digest()

    def observe(self, *, goal_tag: str, expected_revision: str | None = None) -> CommittedGoalViewReading:
        resolver = require_native_goal_resolver(self._capability)
        head = self._commit("HEAD")
        if expected_revision is not None and expected_revision != head:
            raise ValueError("native_view_source_revision_mismatch")
        manifest_path = resolver.manifest_path.relative_to(self._root).as_posix()
        manifest, manifest_blob = self._regular_file(head, manifest_path)
        if "sha256:" + hashlib.sha256(manifest).hexdigest() != resolver.manifest_sha256:
            raise ValueError("native_view_protocol_not_committed")
        path = self._goal_path(head, goal_tag)
        document, projection, payload, blob = self._snapshot(head, path)
        compatibility_title = re.findall(rb"(?m)^# Goal: ([^\r\n]+)$", payload)
        if len(compatibility_title) != 1:
            raise ValueError("native_view_goal_title_ambiguous")
        global_authority = projection.global_authority
        by_lane = {a.lane_key: a for a in projection.lane_authorities}
        lanes = []
        input_refs = [f"git-blob:{manifest_path}:{manifest_blob}", f"git-blob:{path}:{blob}", projection.projection_receipt_ref]
        participating_issues: set[str] = set()
        participating_schedules: set[str] = set()
        # The compatibility projector consumes current lane Issues even when
        # no native Phase/Work exists. They are source authority, not extra
        # native Work or embedded Issue Views. Inventory them independently.
        for authority in projection.lane_authorities:
            ref = authority.current_issue_ref
            if ref is None or ref.startswith("TBD:"):
                continue
            issue_path = self._projector._resolve_issue_path(
                revision=head, goal_path=path, issue_ref=ref)
            _, issue_blob = self._regular_file(head, issue_path)
            participating_issues.add(issue_path)
            input_refs.append(f"git-blob:{issue_path}:{issue_blob}")
        for key in dict.fromkeys(d.coordinate.lane_key for d in document.definitions):
            authority = by_lane.get(key)
            lanes.append({
                "lane_key": key, "label": authority.role if authority else key,
                "authority_availability": ("ambiguous" if authority.qualification == "ambiguous" else "source_recorded") if authority else "unavailable",
                "reason": ";".join(authority.ambiguity_reasons) if authority and authority.ambiguity_reasons else (None if authority else "native_lane_authority_not_qualified"),
                "owner_ref": authority.owner_ref if authority else None,
                "operational_state": authority.operational_state if authority else None,
                "state_detail": authority.state_detail if authority else None,
                "current_issue_ref": authority.current_issue_ref if authority else None,
                "authority_ref": authority.authority_ref if authority else None,
                "source_revision": head,
            })
        issues = []
        retained_readings = {}
        observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        refs = dict.fromkeys(w.issue_ref for p in document.operational_bundle.phases for w in p.work_associations)
        for ref in refs:
            issue_path = self._projector._resolve_issue_path(revision=head, goal_path=path, issue_ref=ref)
            authority = self._issue(head, issue_path)
            issue_bytes, issue_blob = self._regular_file(head, issue_path)
            reading = build_issue_development_read_payload_v2(content_text=issue_bytes.decode(),
                source_path=issue_path, source_observed_at=observed_at)
            identity = cast(dict[str, object], reading["identity"])
            retained_readings[ref] = reading
            participating_issues.add(issue_path)
            input_refs.append(f"git-blob:{issue_path}:{issue_blob}")
            issues.append({
                "issue_ref": ref, "availability": "available", "reason": None,
                "tag": authority["tag"], "title": identity["title"], "status": authority["status"],
                "owner_execution_id": authority["owner"], "source_revision": head,
                "source_ref": f"git-blob:{issue_path}:{issue_blob}",
                **goal_native_issue_facets(reading),
            })
        schedules = []
        for lane in lanes:
            key = cast(str, lane["lane_key"])
            schedule_reading, schedule_inputs, schedule_issues = self._schedule(head, path, document, key)
            schedules.append(schedule_reading)
            input_refs.extend(schedule_inputs)
            participating_issues.update(schedule_issues)
            participating_schedules.add(schedule_path(goal_doc_path=path, lane_key=key))
        location = resolver.resolve_goal_path(path)
        try:
            local = location.resolved_path.read_bytes()
            health = "current" if local == payload else "stale"
        except FileNotFoundError:
            health = "absent"
        root = {
            "schema_id": SOURCE_SCHEMA, "document": json.loads(encode_goal_phase_native_document(document)),
            "source": {"profile": PROFILE, "provider_ref": self.provider_ref,
                "provider_generation": self.provider_generation, "source_scope_ref": self.source_scope_ref,
                "source_revision": head, "document_ref": document.document_ref,
                "projection_health": health, "input_refs": list(dict.fromkeys(input_refs))},
            "goal": {"goal_tag": document.goal_tag, "title": compatibility_title[0].decode(),
                "lifecycle_status": global_authority.lifecycle_status, "owner_ref": global_authority.owner_ref,
                "hold_state": global_authority.hold_state, "authority_ref": global_authority.authority_ref,
                "source_revision": head}, "lanes": lanes, "schedules": schedules, "linked_issues": issues,
        }
        validate_goal_native_view_source(root)
        # All target I/O precedes the terminal HEAD check. No local writes.
        _ = resolver.resolve_goal_path(path)
        for issue_path in sorted(participating_issues):
            self._issues.resolve_issue_path(issue_path)
        for schedule_target in sorted(participating_schedules):
            self._contain_schedule(schedule_target, resolver.goal_root)
        resolver.revalidate()
        if self._commit("HEAD") != head:
            raise ValueError("repository_head_advanced")
        body = canonical_json(root)
        reading = CommittedGoalViewReading(body,
            "goal-native-view-observation:sha256:" + hashlib.sha256(body).hexdigest(),
            canonical_json(retained_readings))
        self._issued[reading] = self._fingerprint(reading)
        return reading

    def _contain_schedule(self, path: str, goal_root: str) -> None:
        resolution = resolve_repository_path_at_use(repository_root=self._root,
            relative_path=path, field_name="goal.schedule")
        if resolution.path is None or not resolution.path.is_relative_to((self._root / goal_root).resolve()):
            raise ValueError("native_view_schedule_outside_binding")

    def _schedule(self, head, path, document, lane_key):
        target = schedule_path(goal_doc_path=path, lane_key=lane_key)
        resolver = _require_native_resolver(self._capability)
        self._contain_schedule(target, resolver.goal_root)
        entries = self._git("ls-tree", "-z", head, "--", target)
        if not entries:
            return {"lane_key": lane_key, "status": "absent", "reason": "schedule_absent",
                "schedule": None, "source_revision": head}, [], set()
        body, blob = self._regular_file(head, target)
        schedule = decode_goal_phase_future_schedule(body)
        if (schedule.goal_tag, schedule.goal_doc_path, schedule.lane_key) != (document.goal_tag, path, lane_key):
            raise ValueError("native_view_schedule_target_mismatch")
        commit = self._git("log", "-1", "--format=%H", "--full-history", head, "--", target).decode().strip()
        parents = self._parents(commit)
        if len(parents) != 1 or not self._ancestor(commit, head):
            raise ValueError("native_view_schedule_publication_unproven")
        changed = self._git("diff-tree", "--no-commit-id", "--name-only", "-r", commit).decode().splitlines()
        if changed != [target]:
            raise ValueError("native_view_schedule_publication_effect_mismatch")
        if commit not in self._git("rev-list", "--first-parent", head).decode().splitlines():
            raise ValueError("native_view_schedule_merge_provenance_unqualified")
        issue = self._issue(parents[0], schedule.decision_issue_path)
        post_issue = self._issue(commit, schedule.decision_issue_path)
        if issue != post_issue or issue["blob_oid"] != schedule.decision_issue_blob_oid or issue["status"] != "in_progress" or target not in cast(tuple[str, ...], issue["scope"]):
            raise ValueError("native_view_schedule_issue_not_authorized")
        self._issue_effect_issuance(commit, schedule.decision_issue_path, issue, (target,))
        if self._regular_file(commit, target)[0] != body:
            raise ValueError("native_view_schedule_publication_blob_mismatch")
        _, origin, _, _ = self._snapshot(commit, path)
        _, current, _, _ = self._snapshot(head, path)
        inputs = [f"git-blob:{target}:{blob}", f"repository-commit:{commit}",
            f"git-blob:{schedule.decision_issue_path}:{issue['blob_oid']}"]
        if origin.global_authority.semantic_wire() != current.global_authority.semantic_wire():
            status, reason = "stale", "goal_global_authority_changed"
        elif type(document) is not GoalPhaseNativeDocumentV2:
            status, reason = "unavailable", "schedule_carrier_profile_unsupported"
        else:
            status, reason = assess_goal_phase_future_schedule(schedule=schedule, document=document)
        return {"lane_key": lane_key, "status": status, "reason": reason,
            "schedule": schedule.to_wire(), "source_revision": head}, inputs, {schedule.decision_issue_path}
