"""Validate evidence shape and byte accounting, never external claim truth."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys

from jsonschema import Draft202012Validator, FormatChecker

HERE = Path(__file__).resolve().parent


def pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise ValueError("duplicate_json_key:" + key)
        value[key] = item
    return value


def decode(text):
    return json.loads(text, object_pairs_hook=pairs)


def validate_schema(value, filename):
    schema = decode((HERE / filename).read_text())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = list(validator.iter_errors(value))
    if errors:
        raise ValueError("schema_invalid:" + filename + ":" + errors[0].message)


def validate(root: Path):
    if root.is_symlink():
        raise ValueError("evaluation_root_symlink_refused")
    root = root.resolve(strict=True)
    regular = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("evaluation_symlink_refused")
        if path.is_file():
            regular[path.relative_to(root).as_posix()] = path
        elif not path.is_dir():
            raise ValueError("evaluation_non_regular_entry")
    if not {"manifest.json", "evaluation.md", "findings.json", "interactions.jsonl"} <= regular.keys():
        raise ValueError("evaluation_required_files_missing")
    manifest = decode(regular["manifest.json"].read_text())
    findings = decode(regular["findings.json"].read_text())
    validate_schema(manifest, "manifest.schema.json")
    validate_schema(findings, "findings.schema.json")
    if findings["evaluation_id"] != manifest["evaluation_id"]:
        raise ValueError("evaluation_id_mismatch")
    declared = manifest["artifact_digests"]
    if set(declared) != set(regular) - {"manifest.json"}:
        raise ValueError("artifact_inventory_mismatch")
    for name, digest in declared.items():
        path = PurePosixPath(name)
        if path.is_absolute() or name != path.as_posix() or any(p in {".", ".."} for p in path.parts):
            raise ValueError("artifact_path_invalid")
        if "sha256:" + hashlib.sha256(regular[name].read_bytes()).hexdigest() != digest:
            raise ValueError("artifact_digest_mismatch:" + name)
    interactions = []
    for number, line in enumerate(regular["interactions.jsonl"].read_text().splitlines(), 1):
        item = decode(line)
        validate_schema(item, "interaction.schema.json")
        if item["sequence"] != number:
            raise ValueError("interaction_sequence_not_contiguous")
        interactions.append(item)
    if not interactions:
        raise ValueError("interactions_empty")
    executions = [e["ref"] for e in manifest["executions"]]
    if len(set(executions)) != len(executions):
        raise ValueError("execution_duplicate")
    passes = manifest["passes"]
    if [p["pass"] for p in passes] != ["I", "U", "V", "R"]:
        raise ValueError("pass_order_invalid")
    by_pass = {p["pass"]: p for p in passes}
    for p in passes:
        if not set(p["execution_refs"]) <= set(executions):
            raise ValueError("pass_execution_unknown")
        if p["result"] in {"not_run", "not_applicable"}:
            if p["started_at_utc"] is not None or p["ended_at_utc"] is not None or p["execution_refs"]:
                raise ValueError("unrun_pass_has_execution_or_timestamps")
        else:
            if not p["execution_refs"] or p["started_at_utc"] is None or p["ended_at_utc"] is None:
                raise ValueError("executed_pass_evidence_missing")
            if datetime.fromisoformat(p["started_at_utc"]) > datetime.fromisoformat(p["ended_at_utc"]):
                raise ValueError("pass_time_order_invalid")
    for item in interactions:
        if item["execution_ref"] not in by_pass[item["pass"]]["execution_refs"]:
            raise ValueError("interaction_execution_not_in_pass")
        if item["kind"] == "human_hint" and not by_pass[item["pass"]]["assistance"]:
            raise ValueError("human_hint_not_disclosed")
    if by_pass["R"]["result"] == "passed":
        if set(by_pass["R"]["execution_refs"]) & set(by_pass["U"]["execution_refs"] + by_pass["V"]["execution_refs"]):
            raise ValueError("recovery_requires_fresh_execution")
    target = manifest["inputs"]["target"]
    if target["starting_state"] in {"missing_directory", "empty_directory", "unborn_git", "not_selected"} and target["baseline_commit"] is not None:
        raise ValueError("unborn_or_absent_target_has_fake_baseline")
    if target["starting_state"] == "committed_git" and target["baseline_commit"] is None:
        raise ValueError("committed_target_baseline_missing")
    if manifest["subject"] == "goal_readonly" and target["goal"] is None:
        raise ValueError("goal_subject_requires_qualified_goal")
    refs = {"artifact:" + name for name in declared} | {"interaction:" + str(i["sequence"]) for i in interactions}
    ids = [f["id"] for f in findings["findings"]]
    if len(set(ids)) != len(ids):
        raise ValueError("finding_id_duplicate")
    for finding in findings["findings"]:
        if not set(finding["evidence_refs"]) <= refs:
            raise ValueError("finding_evidence_unknown")
        if finding["enforcement_result"] == "rejected" and (not finding.get("rejecting_component") or not finding.get("diagnostic")):
            raise ValueError("refusal_component_and_diagnostic_required")
    return {"outcome": "valid", "schema": manifest["schema"], "evaluation_id": manifest["evaluation_id"],
            "artifacts": len(declared), "interactions": len(interactions), "findings": len(ids),
            "authority": "external-client-evidence-only"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evaluation_directory", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.evaluation_directory), sort_keys=True))
        return 0
    except (ValueError, OSError, UnicodeError) as error:
        print(json.dumps({"outcome": "invalid", "diagnostics": [str(error)]}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
