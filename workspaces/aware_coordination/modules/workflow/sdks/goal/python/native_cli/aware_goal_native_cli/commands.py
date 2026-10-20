"""Goal-owned public read commands; summaries describe, never authorize."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

from aware_command_runtime import AwareCommandInvocation, AwareCommandRegistry


def _common(parser: argparse.ArgumentParser) -> None:
    _ = parser.add_argument("--repository-root", type=Path, required=True)
    _ = parser.add_argument(
        "--protocol-manifest",
        type=Path,
        required=True,
        help="Existing committed native manifest; no setup or upgrade.",
    )
    _ = parser.add_argument(
        "--goal-path",
        required=True,
        help="Explicit repository-relative committed Goal.",
    )
    _ = parser.add_argument("--format", choices=("summary", "json"), default="summary")


def _eligibility_parser(parser: argparse.ArgumentParser) -> None:
    _common(parser)
    _ = parser.add_argument("--lane-key", required=True)
    _ = parser.add_argument("--phase-key", required=True)
    _ = parser.add_argument(
        "--prerequisite-goal",
        action="append",
        default=[],
        metavar="GOAL_TAG=REPOSITORY_PATH",
        help="Explicit cross-Goal source hint, independently verified.",
    )


def register_goal_commands(registry: AwareCommandRegistry) -> None:
    """Mount through the original command runtime, without invoking any read."""
    registry.register_command(
        name="show",
        help="Read an already qualified committed Goal and associated inputs.",
        configure_parser=_common,
        handle=_show,
        source="aware_goal_native_cli",
        operation_ref="goal_cli.qualified_show",
    )
    registry.register_command(
        name="eligibility",
        help="Describe one Phase's eligibility; never authorize RUN.",
        configure_parser=_eligibility_parser,
        handle=_eligibility,
        source="aware_goal_native_cli",
        operation_ref="workflow.goal.phase.eligibility.observe",
    )


def _client(args: argparse.Namespace):
    # Help/registration has no source I/O and imports no provider or Service.
    from aware_goal_native_fs_adapter.consumer_read import NativeGoalConsumerReadClient
    from aware_protocol_fs_adapter import admit_native_goal_resolver

    root = cast(Path, args.repository_root)
    manifest = cast(Path, args.protocol_manifest)
    if not manifest.is_absolute():
        manifest = root / manifest
    hints: dict[str, str] = {}
    for value in cast(list[str], getattr(args, "prerequisite_goal", [])):
        tag, separator, path = value.partition("=")
        if not separator or not tag or not path or tag in hints:
            raise ValueError("invalid_or_duplicate_prerequisite_goal")
        hints[tag] = path
    admission = admit_native_goal_resolver(repository_root=root, manifest_path=manifest)
    if admission.capability is None:
        raise ValueError("native_goal_admission_unavailable")
    return NativeGoalConsumerReadClient(
        admission.capability, prerequisite_goal_paths=hints
    )


def _show(invocation: AwareCommandInvocation) -> int:
    return _run(invocation, eligibility=False)


def _eligibility(invocation: AwareCommandInvocation) -> int:
    return _run(invocation, eligibility=True)


def _run(invocation: AwareCommandInvocation, *, eligibility: bool) -> int:
    args = invocation.args
    try:
        client = _client(args)
        if eligibility:
            result = client.eligibility(
                goal_path=cast(str, args.goal_path),
                lane_key=cast(str, args.lane_key),
                phase_key=cast(str, args.phase_key),
            )
        else:
            result = client.show(goal_path=cast(str, args.goal_path))
        print(
            json.dumps(result, sort_keys=True, separators=(",", ":"))
            if cast(str, args.format) == "json"
            else summarize_goal_read(result)
        )
        return (
            0
            if not eligibility
            or cast(dict[str, object], result["result"])["status"] == "observed"
            else 2
        )
    except (OSError, TypeError, ValueError) as error:
        # Reads cannot have a Goal publication effect; no setup/retry is offered.
        failure = {
            "status": "refused",
            "reason": str(error),
            "goal_effect": "none",
            "event_effect": "none",
            "dispatch_effect": "none",
        }
        print(json.dumps(failure, sort_keys=True), file=sys.stderr)
        return 2


def summarize_goal_read(value: dict[str, object]) -> str:
    """Present original owner facts without deriving eligibility or permission."""
    if value["operation"] == "eligibility":
        result = cast(dict[str, object], value["result"])
        coordinate = cast(dict[str, str], result["coordinate"])
        lines = [
            f"Phase: {coordinate['goal_tag']} / {coordinate['lane_key']} / {coordinate['phase_key']}",
            f"Eligibility: {result['eligibility']} ({result['status']})",
            f"Source epoch: {result['source_revision_ref']}",
            f"Observed reasons: {', '.join(cast(list[str], result['reasons'])) or 'none'}",
        ]
        gate = result.get("dependency_gate")
        if type(gate) is dict:
            lines.append(
                f"Prerequisites: {gate['state']}; coverage: {result['observation_coverage']}"
            )
            for state in (
                "satisfied",
                "pending",
                "rejected",
                "stale",
                "unresolved",
                "not_evaluated",
            ):
                keys = cast(list[str], gate[state])
                if keys:
                    lines.append(f"  {state}: {', '.join(keys)}")
        unresolved = cast(list[str], result.get("unresolved_dependency_keys", []))
        if unresolved:
            lines.append("Unresolved declarations: " + ", ".join(unresolved))
        lines.extend(
            [
                "Eligible is not authorized to RUN. No approval, Work admission or dispatch occurred.",
                "Suggested next step: review the original evidence and obtain separate work/execution authority.",
            ]
        )
        return "\n".join(lines)
    state = cast(dict[str, object], value["state"])
    goal, source = (
        cast(dict[str, object], state["goal"]),
        cast(dict[str, object], state["source"]),
    )
    lines = [
        f"Goal: {goal['title']} ({goal['goal_tag']})",
        f"Recorded status: {goal['lifecycle_status']}; hold: {goal['hold_state']}",
        f"Source epoch: {source['source_revision']} (verified at return)",
        f"Local Goal projection: {source['projection_health']}",
        f"Phases: {state['definition_count']} definitions; {state['operational_phase_count']} operational",
    ]
    for lane in cast(list[dict[str, object]], state["lanes"]):
        reading = cast(dict[str, object], lane["reading"])
        lines.append(
            f"Lane {reading['lane_key']}: {reading['operational_state'] or 'unavailable'}; authority {reading['authority_availability']}"
        )
        for phase in cast(list[dict[str, object]], lane["phases"]):
            definition = cast(dict[str, object], phase["definition"])
            coordinate = cast(dict[str, str], definition["coordinate"])
            operational = phase["operational"]
            recorded = (
                cast(dict[str, object], operational)["state"]
                if type(operational) is dict
                else "definition only"
            )
            lines.append(
                f"  {coordinate['phase_key']}: {definition['title']} — {recorded}"
            )
    for issue in cast(list[dict[str, object]], state["linked_issues"]):
        lines.append(
            f"Issue {issue['issue_ref']}: {issue['title'] or 'unavailable'} ({issue['status'] or 'unavailable'})"
        )
    lines.extend(
        [
            "Phase transition time, execution posture and action capabilities: unavailable in this reading.",
            "Suggested next step: select an explicit lane/Phase and observe eligibility; this reading authorizes no work.",
        ]
    )
    return "\n".join(lines)
