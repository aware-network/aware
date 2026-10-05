"""Standalone, read-only native Goal eligibility through fresh Protocol admission."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from aware_goal_sdk.phase_operation import (
    GoalPhaseObserveEligibilityRequestV1,
    GoalPhaseOperationClient,
    decode_goal_phase_observe_eligibility_request,
)
from aware_goal_sdk.phase_direction import (
    GoalPhaseDirectionClient,
    GoalPhaseDirectionCurrentnessRequestV1,
    GoalPhaseDirectionObserveRequestV1,
)
from aware_protocol_fs_adapter import admit_native_goal_resolver

from aware_goal_native_fs_adapter.phase_operation import NativeGitGoalPhaseOperationProvider
from aware_goal_native_fs_adapter.phase_direction import NativeGitGoalPhaseDirectionProvider


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_phase_direction_json_key")
        result[key] = value
    return result


def _direction_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aware-goal-native",
        description="Read-only whole-document Goal Phase direction and currentness.",
    )
    operations = parser.add_subparsers(dest="operation", required=True)
    for name in ("observe_phase_direction", "verify_phase_direction_currentness"):
        operation = operations.add_parser(name)
        _ = operation.add_argument("--repository-root", type=Path, required=True)
        _ = operation.add_argument("--manifest-path", type=Path, required=True)
        _ = operation.add_argument("--goal-path", required=True)
        if name == "observe_phase_direction":
            _ = operation.add_argument("--goal-tag", required=True)
            _ = operation.add_argument("--lane-key", required=True)
            _ = operation.add_argument("--phase-key", required=True)
        else:
            _ = operation.add_argument("--receipt-file", type=Path, required=True)
    return parser


def _direction_main(argv: Sequence[str]) -> int:
    args = _direction_parser().parse_args(argv)
    try:
        admission = admit_native_goal_resolver(
            repository_root=args.repository_root, manifest_path=args.manifest_path
        )
        if admission.capability is None:
            raise ValueError("native_goal_admission_unavailable")
        client = GoalPhaseDirectionClient(
            NativeGitGoalPhaseDirectionProvider(admission.capability)
        )
        if args.operation == "observe_phase_direction":
            result = client.observe_phase_direction(
                GoalPhaseDirectionObserveRequestV1(
                    goal_path=args.goal_path,
                    goal_tag=args.goal_tag,
                    lane_key=args.lane_key,
                    phase_key=args.phase_key,
                )
            )
        else:
            payload: object = json.loads(
                args.receipt_file.read_text(encoding="utf-8"),
                object_pairs_hook=_unique_json_object,
            )
            if type(payload) is not dict:
                raise ValueError("phase_direction_receipt_must_be_object")
            result = client.verify_phase_direction_currentness(
                GoalPhaseDirectionCurrentnessRequestV1(
                    goal_path=args.goal_path, expected_receipt=cast(dict[str, object], payload)
                )
            )
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0 if result.get("status", "current") == "current" else 2
    except (OSError, TypeError, ValueError) as error:
        print(json.dumps({"status": "error", "error": str(error)}, sort_keys=True), file=sys.stderr)
        return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aware-goal-native",
        description="Observe native Goal Phase eligibility; no Goal or dispatch effect.",
    )
    _ = parser.add_argument("--repository-root", type=Path, required=True)
    _ = parser.add_argument("--manifest-path", type=Path, required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    _ = selection.add_argument("--request-file", type=Path)
    _ = selection.add_argument("--discover-goal-path")
    _ = parser.add_argument("--lane-key")
    _ = parser.add_argument("--phase-key")
    _ = parser.add_argument(
        "--prerequisite-goal",
        action="append",
        default=[],
        metavar="GOAL_TAG=REPOSITORY_PATH",
        help="Explicit source hint for a cross-Goal prerequisite; verified by the provider.",
    )
    return parser


def _prerequisite_paths(values: list[str]) -> dict[str, str]:
    paths: dict[str, str] = {}
    for value in values:
        goal_tag, separator, path = value.partition("=")
        if not separator or not goal_tag or not path or goal_tag in paths:
            raise ValueError("invalid_or_duplicate_prerequisite_goal")
        paths[goal_tag] = path
    return paths


def main(argv: Sequence[str] | None = None) -> int:
    selected = list(sys.argv[1:] if argv is None else argv)
    if selected and selected[0] in {
        "observe_phase_direction", "verify_phase_direction_currentness"
    }:
        return _direction_main(selected)
    args = _parser().parse_args(argv)
    try:
        request_file = cast(Path | None, args.request_file)
        discovery_path = cast(str | None, args.discover_goal_path)
        lane_key = cast(str | None, args.lane_key)
        phase_key = cast(str | None, args.phase_key)
        hints = cast(list[str], args.prerequisite_goal)
        request: GoalPhaseObserveEligibilityRequestV1 | None = None
        if request_file is None:
            if discovery_path is None or lane_key is None or phase_key is None:
                raise ValueError("discovery_requires_lane_and_phase_keys")
            if hints:
                raise ValueError("discovery_does_not_use_prerequisite_hints")
            prerequisite_paths: dict[str, str] = {}
        else:
            if lane_key is not None or phase_key is not None:
                raise ValueError("observation_does_not_accept_discovery_keys")
            payload: object = json.loads(request_file.read_text(encoding="utf-8"))
            if type(payload) is not dict:
                raise ValueError("eligibility_request_must_be_object")
            raw_payload = cast(dict[object, object], payload)
            if any(type(key) is not str for key in raw_payload):
                raise ValueError("eligibility_request_must_be_object")
            request = decode_goal_phase_observe_eligibility_request(
                cast(dict[str, object], raw_payload)
            )
            prerequisite_paths = _prerequisite_paths(hints)
        admission = admit_native_goal_resolver(
            repository_root=cast(Path, args.repository_root),
            manifest_path=cast(Path, args.manifest_path),
        )
        if admission.capability is None:
            raise ValueError("native_goal_admission_unavailable")
        provider = NativeGitGoalPhaseOperationProvider(
            admission.capability, prerequisite_goal_paths=prerequisite_paths
        )
        if request_file is None:
            assert discovery_path is not None and lane_key is not None and phase_key is not None
            discovered = provider.discover_eligibility_request(
                goal_path=discovery_path, lane_key=lane_key, phase_key=phase_key
            )
            print(json.dumps(discovered.to_wire(), sort_keys=True, separators=(",", ":")))
            return 0
        if request is None:
            raise ValueError("eligibility_request_unavailable")
        result = GoalPhaseOperationClient(provider).observe_eligibility(request)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0 if result["status"] == "observed" else 2
    except (OSError, TypeError, ValueError) as error:
        print(
            json.dumps({"status": "error", "error": str(error)}, sort_keys=True),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
