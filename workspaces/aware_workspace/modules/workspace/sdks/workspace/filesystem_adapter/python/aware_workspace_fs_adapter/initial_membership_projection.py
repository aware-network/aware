"""Exact cooperative Project replacement through the original FileSystem owner.

Local private retention is the assurance, not authentic Identity, continuous
confinement or a general installer. A missing acknowledgement NEVER permits
adoption of matching bytes or another physical dispatch.
"""

from __future__ import annotations

import hashlib
import os
import stat

from aware_file_system.retained_mutation import retain_confined_manifest_replacement
from aware_workspace_sdk.initial_authoring.goal_publication import (
    InitialGoalPublicationRequest,
)
from aware_workspace_sdk.initial_authoring.values import (
    InitialConfigurationRequest,
    InitialProjectRequest,
    _canonical,
    initial_reference,
)

from .initial_authoring import (
    _private,
    _projection_effect,
    _projection_stat,
    _read_record,
    _root_and_metadata,
    _write_record,
    configuration_attempt,
    project_attempt,
)


def _digest(content):
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _original_project(attempt, project):
    """Verify the retained original creation at its historical physical epoch."""
    source = project.source
    content = source["project_plan"]["content_utf8"].encode()
    with project_attempt(attempt.port, project) as original:
        recovered = original.recover()
        if recovered["disposition"] != "recorded":
            raise ValueError("initial_membership_original_project_unavailable")
        record = _read_record(original.directory, "projection-result.json")
        intent = _read_record(original.directory, "projection-start.json")
        expected_intent = {
            "schema_id": "aware.workspace.initial-project-projection-intent.v1",
            "publication_ref": recovered["publication"]["publication_ref"],
            "request_ref": project.request_ref,
            "commit": recovered["original_result"].commit_hash,
            "target_path": source["target_path"],
            "preimage": "absent",
            "physical_profile": "descriptor_walk_v1",
            "directory_paths": [
                p["path"] for p in source["parent_preimages"] if p["state"] == "absent"
            ],
        }
        if (
            type(record) is not dict
            or set(record)
            != {"schema_id", "intent", "target", "effects", "projection_ref"}
            or _canonical(intent) != _canonical(expected_intent)
        ):
            raise ValueError("initial_membership_original_project_projection_invalid")
        target = record["target"]
        file = target["file"]
        if (
            set(target) != {"parents", "file"}
            or set(file) != {"stat", "sha256"}
            or type(file["stat"]) is not list
            or len(file["stat"]) != 7
            or any(type(v) is not int for v in file["stat"])
            or file["stat"][2:5] != [stat.S_IFREG | 0o644, 1, len(content)]
            or file["sha256"] != _digest(content)
        ):
            raise ValueError("initial_membership_original_project_file_invalid")
        # Every parent has exactly the original preimage or its creation effect.
        if len(target["parents"]) != len(source["parent_preimages"]):
            raise ValueError("initial_membership_original_parent_inventory_invalid")
        effects = []
        for parent, before in zip(
            target["parents"], source["parent_preimages"], strict=True
        ):
            if (
                set(parent) != {"path", "identity", "mode"}
                or parent["path"] != before["path"]
            ):
                raise ValueError("initial_membership_original_parent_invalid")
            if before["state"] == "directory":
                if (
                    parent["identity"] != before["identity"]
                    or parent["mode"] != before["mode"]
                ):
                    raise ValueError("initial_membership_original_parent_substituted")
            else:
                if parent["mode"] != 0o700:
                    raise ValueError("initial_membership_original_parent_mode_invalid")
                effects.append(
                    {
                        "path": parent["path"],
                        "kind": "directory",
                        "state": "applied",
                        "durability_confirmed": True,
                        "mode": 0o700,
                        "before_digest": None,
                        "after_digest": None,
                        "after_identity": parent["identity"],
                    }
                )
        effects.append(
            {
                "path": source["target_path"],
                "kind": "file",
                "state": "applied",
                "durability_confirmed": True,
                "mode": 0o644,
                "before_digest": None,
                "after_digest": _digest(content),
                "after_identity": file["stat"][:2],
            }
        )
        body = {k: v for k, v in record.items() if k != "projection_ref"}
        if (
            record["schema_id"] != "aware.workspace.initial-project-projection.v1"
            or _canonical(record["intent"]) != _canonical(intent)
            or _canonical(record["effects"]) != _canonical(effects)
            or record["projection_ref"]
            != initial_reference("workspace-initial-project-projection", body)
        ):
            raise ValueError("initial_membership_original_project_record_mismatch")
        return record


def _participants(attempt):
    """Original Goal and manifest effects remain exact at the successor epoch."""
    source = attempt.record["request"]["source"]
    facts = source["preparation"]["source"]
    goal = InitialGoalPublicationRequest.from_wire(facts["goal_creation_request"])
    project = InitialProjectRequest.from_wire(facts["project_creation_request"])
    old_project = _original_project(attempt, project)
    if (
        old_project["projection_ref"]
        != goal.source["context"]["project_projection_ref"]
        or source["before_content_utf8"]
        != project.source["project_plan"]["content_utf8"]
    ):
        raise ValueError("initial_membership_project_origin_mismatch")
    with attempt.port.initial_goal_attempt(goal) as original:
        recovered = original.recover()
        record = _read_record(original.directory, "projection-result.json")
        intent = _read_record(original.directory, "projection-start.json")
        if (
            recovered["disposition"] != "recorded"
            or _canonical(recovered["publication"])
            != _canonical(facts["goal_creation_publication"])
            or _canonical(record) != _canonical(facts["goal_creation_projection"])
        ):
            raise ValueError("initial_membership_goal_origin_mismatch")
        original._verify_project_projection(
            record, intent, goal.source["content_utf8"].encode()
        )
        goal_record, goal_intent = record, intent
    from aware_workspace_sdk.initial_authoring.configuration_successor import (
        project_configuration_request,
    )

    config = project_configuration_request(project.source)
    config_claim = config.to_wire()["configuration"]
    if type(config_claim) is not dict:
        raise ValueError("initial_membership_manifest_source_invalid")
    config_body = config_claim["content_utf8"].encode()
    manager = (
        configuration_attempt(attempt.port, config)
        if type(config) is InitialConfigurationRequest
        else attempt.port.initial_configuration_successor_attempt(config)
    )
    with manager as original:
        record = _read_record(original.directory, "projection-result.json")
        intent = _read_record(original.directory, "projection-start.json")
        original._verify_projection(record, intent, config_body)
        if record["projection_ref"] != project.source["configuration_projection_ref"]:
            raise ValueError("initial_membership_manifest_origin_mismatch")
    # The last manifest qualification must not hide a mutation of the Goal
    # already checked above. Project is reobserved after this original check.
    with attempt.port.initial_goal_attempt(goal) as original:
        original._verify_project_projection(
            goal_record, goal_intent, goal.source["content_utf8"].encode()
        )
    return old_project, {
        source["target_path"]: source["content_utf8"].encode(),
        goal.source["target_path"]: goal.source["content_utf8"].encode(),
        "aware.protocol.toml": config_body,
    }


def _barrier(attempt, result, entries):
    expected = []
    for path, body in sorted(entries.items()):
        oid = attempt.port._git("hash-object", "--stdin", input=body)
        if (
            attempt.port._git("ls-tree", "-z", result.commit_hash, "--", path)
            != f"100644 blob {oid}\t{path}\0"
        ):
            raise ValueError("initial_membership_projection_committed_source_mismatch")
        expected.append((path, oid))
    with _root_and_metadata(attempt.port) as (_, metadata_fd, _, _):
        before = os.stat("index", dir_fd=metadata_fd, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError("initial_membership_projection_regular_index_required")
        observed = attempt.port._git(
            "ls-files", "--stage", "-z", "--", *(p for p, _ in expected)
        )
        if observed != "".join(f"100644 {oid} 0\t{path}\0" for path, oid in expected):
            raise ValueError(
                "initial_membership_projection_participating_index_mismatch"
            )
        if attempt.port._head() != ("refs/heads/main", result.commit_hash):
            raise ValueError("initial_membership_projection_head_advanced")
        if _projection_stat(before) != _projection_stat(
            os.stat("index", dir_fd=metadata_fd, follow_symlinks=False)
        ):
            raise ValueError(
                "initial_membership_projection_participating_index_changed"
            )


def _current(attempt, recovered, *, target=None, before=False):
    # One stable participating-index horizon spans historical resolution,
    # physical qualification and the final barrier, not fresh per-entry views.
    with _root_and_metadata(attempt.port) as (_, metadata_fd, _, _):
        index_before = os.stat("index", dir_fd=metadata_fd, follow_symlinks=False)
        if not stat.S_ISREG(index_before.st_mode) or index_before.st_nlink != 1:
            raise ValueError("initial_membership_projection_regular_index_required")
        old = _current_unfenced(attempt, recovered, target=target, before=before)
        # A source lookup/HEAD read cannot hide a later target or unchanged
        # participant mutation. Reobserve originals without renewing effects.
        _participants(attempt)
        source = attempt.record["request"]["source"]
        if before or target is not None:
            expected = old["target"] if before else target
            observed = attempt._project_target(
                source["before_content_utf8" if before else "content_utf8"].encode()
            )
            if _canonical(observed) != _canonical(expected):
                raise ValueError(
                    "initial_membership_projection_terminal_target_changed"
                )
        if attempt.port._head() != (
            "refs/heads/main",
            recovered["original_result"].commit_hash,
        ):
            raise ValueError("initial_membership_projection_head_advanced")
        if _projection_stat(index_before) != _projection_stat(
            os.stat("index", dir_fd=metadata_fd, follow_symlinks=False)
        ):
            raise ValueError("initial_membership_projection_terminal_index_changed")
        return old


def _current_unfenced(attempt, recovered, *, target=None, before=False):
    result = recovered["original_result"]
    if (
        result.publication_state != "published"
        or not result.ledger_complete
        or result.admission_completion != "completed"
        or result.index_projection != "applied"
    ):
        raise ValueError("initial_membership_projection_publication_incomplete")
    old, entries = _participants(attempt)
    source = attempt.record["request"]["source"]
    observed = (
        attempt._project_target(
            source["before_content_utf8" if before else "content_utf8"].encode()
        )
        if (before or target is not None)
        else None
    )
    if before and _canonical(observed) != _canonical(old["target"]):
        raise ValueError("initial_membership_projection_preimage_substituted")
    if target is not None and _canonical(observed) != _canonical(target):
        raise ValueError("initial_membership_projection_target_changed")
    if observed is not None and _canonical(observed["parents"]) != _canonical(
        old["target"]["parents"]
    ):
        raise ValueError("initial_membership_projection_parent_substituted")
    _barrier(attempt, result, entries)
    return old


def _verify_record(attempt, record, intent):
    source = attempt.record["request"]["source"]
    observed = attempt._project_target(source["content_utf8"].encode())
    body = {k: v for k, v in record.items() if k != "projection_ref"}
    effect = {
        "path": source["target_path"],
        "kind": "manifest",
        "state": "applied",
        "durability_confirmed": True,
        "mode": 0o644,
        "before_digest": _digest(source["before_content_utf8"].encode()),
        "after_digest": _digest(source["content_utf8"].encode()),
        "after_identity": observed["file"]["stat"][:2],
    }
    if (
        type(record) is not dict
        or set(record) != {"schema_id", "intent", "target", "effect", "projection_ref"}
        or record["schema_id"] != "aware.workspace.initial-membership-projection.v1"
        or _canonical(record["intent"]) != _canonical(intent)
        or _canonical(record["target"]) != _canonical(observed)
        or _canonical(record["effect"]) != _canonical(effect)
        or record["projection_ref"]
        != initial_reference("workspace-initial-membership-projection", body)
        or observed["parents"] != intent["preimage"]["parents"]
        or observed["file"]["stat"][:2] == intent["preimage"]["file"]["stat"][:2]
    ):
        raise ValueError("initial_membership_projection_record_mismatch")


def _reread(attempt, intent, record):
    for name, expected in (
        ("projection-start.json", intent),
        ("projection-result.json", record),
    ):
        descriptor = os.open(
            name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=attempt.directory,
        )
        try:
            _private(os.fstat(descriptor), 0o600)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        if _canonical(_read_record(attempt.directory, name)) != _canonical(expected):
            raise ValueError("initial_membership_projection_retention_changed")
    os.fsync(attempt.directory)


def project_membership(attempt, *, read_only=False):
    # Damaged retained claims must remain a projection refusal with the original
    # CAS receipt, rather than leaking a nested container exception past it.
    try:
        return _project_membership(attempt, read_only=read_only)
    except (KeyError, TypeError, IndexError, AttributeError) as error:
        raise ValueError("initial_membership_projection_record_invalid") from error


def _project_membership(attempt, *, read_only=False):
    recovered = attempt.recover()
    if recovered["disposition"] != "recorded":
        raise ValueError("initial_membership_original_result_required")
    result = recovered["original_result"]
    old = _current(attempt, recovered)
    source = attempt.record["request"]["source"]
    intent = {
        "schema_id": "aware.workspace.initial-membership-projection-intent.v1",
        "publication_ref": recovered["publication"]["publication_ref"],
        "goal_creation_publication_ref": source["preparation"]["source"][
            "goal_creation_publication"
        ]["publication_ref"],
        "request_ref": attempt.record["request"]["request_ref"],
        "commit": result.commit_hash,
        "target_path": source["target_path"],
        "preimage": old["target"],
        "physical_profile": "descriptor_walk_v1",
    }
    names = set(os.listdir(attempt.directory))
    if "projection-start.json" in names:
        if _canonical(
            _read_record(attempt.directory, "projection-start.json")
        ) != _canonical(intent):
            raise ValueError("initial_membership_projection_intent_mismatch")
        if "projection-result.json" not in names:
            return {
                "projection_state": "uncertain",
                "projection": None,
                "diagnostics": (),
            }
        record = _read_record(attempt.directory, "projection-result.json")
        _verify_record(attempt, record, intent)
        _reread(attempt, intent, record)
        _current(attempt, recovered, target=record["target"])
        _verify_record(attempt, record, intent)
        _current(attempt, recovered, target=record["target"])
        return {
            "projection_state": "installed",
            "projection": record,
            "diagnostics": (),
        }
    if "projection-result.json" in names:
        raise ValueError("initial_membership_projection_result_without_intent")
    if read_only:
        _current(attempt, recovered, before=True)
        return {
            "projection_state": "not_started",
            "projection": None,
            "diagnostics": (),
        }
    _current(attempt, recovered, before=True)
    handle = retain_confined_manifest_replacement(
        root=attempt.port._root,
        target_path=source["target_path"],
        expected_content_digest=_digest(source["before_content_utf8"].encode()),
        content=source["content_utf8"].encode(),
    )
    try:
        _current(attempt, recovered, before=True)
        handle.validate_current()
        _write_record(attempt.directory, "projection-start.json", intent)
        handle.replace_manifest()
        effects = handle.finish()
        record_body = {
            "schema_id": "aware.workspace.initial-membership-projection.v1",
            "intent": intent,
            "target": attempt._project_target(source["content_utf8"].encode()),
            "effect": _projection_effect(effects[0]),
        }
        record = {
            **record_body,
            "projection_ref": initial_reference(
                "workspace-initial-membership-projection", record_body
            ),
        }
        handle.validate_consumed_current()
        _verify_record(attempt, record, intent)
        _current(attempt, recovered, target=record["target"])
        _write_record(attempt.directory, "projection-result.json", record)
        _reread(attempt, intent, record)
        handle.validate_consumed_current()
        _verify_record(attempt, record, intent)
        _current(attempt, recovered, target=record["target"])
        return {
            "projection_state": "installed",
            "projection": record,
            "diagnostics": (),
        }
    except (ValueError, OSError, RuntimeError) as error:
        return {
            "projection_state": "uncertain",
            "projection": None,
            "projection_effects": tuple(
                _projection_effect(effect) for effect in handle.effects
            ),
            "residual_scratch_paths": tuple(
                getattr(error, "residual_scratch_paths", ())
            ),
            "diagnostics": (str(error),),
        }
    finally:
        handle.release()
