"""Unmounted create-first registrars over original source/customer owners.

No launcher selects these functions yet. Interactive confirmation consumes the
same displayed live plan; it is local authoring consent, not Goal approval.
Noninteractive apply needs a separate original-owner durable review binding.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast

from aware_command_runtime import AwareCommandInvocation, AwareCommandRegistry

from .commands import _eligibility, _eligibility_parser, _show


def _location(parser: argparse.ArgumentParser) -> None:
    _ = parser.add_argument("--repository-root", type=Path, required=True)
    _ = parser.add_argument("--protocol-manifest", type=Path, required=True)
    _ = parser.add_argument("--format", choices=("summary", "json"), default="summary")


def _create(parser: argparse.ArgumentParser) -> None:
    _location(parser)
    _ = parser.add_argument("name")
    _ = parser.add_argument("--title", required=True)
    _ = parser.add_argument("--priority", default="medium")
    _ = parser.add_argument(
        "--apply",
        action="store_true",
        help="Preview, then confirm the same live plan interactively. No unattended apply.",
    )


def _goal_create(parser: argparse.ArgumentParser) -> None:
    _create(parser)
    _ = parser.add_argument("--project", required=True)
    _ = parser.add_argument("--intent", required=True)
    _ = parser.add_argument(
        "--date", required=True, help="Explicit addressing date, not lifecycle time."
    )


def _project_show_parser(parser: argparse.ArgumentParser) -> None:
    _location(parser)
    _ = parser.add_argument("name")


def _goal_show_parser(parser: argparse.ArgumentParser) -> None:
    _location(parser)
    selection = parser.add_mutually_exclusive_group(required=True)
    _ = selection.add_argument("name", nargs="?")
    _ = selection.add_argument("--goal-path")
    _ = parser.add_argument("--date", help="Optional exact planning selector only.")


def register_project_commands(registry: AwareCommandRegistry) -> None:
    """Qualification only: no Agent or standalone launcher mounting."""
    registry.register_command(
        name="create",
        help="Preview an empty Project; apply requires same-plan confirmation.",
        configure_parser=_create,
        handle=_project_create,
        source=__name__,
        operation_ref="project.customer.create",
    )
    registry.register_command(
        name="show",
        help="Qualified original Project reading, before or after Goal attachment.",
        configure_parser=_project_show_parser,
        handle=_project_show,
        source=__name__,
        operation_ref="project.customer.show",
    )


def register_create_first_goal_commands(registry: AwareCommandRegistry) -> None:
    """Alternative unmounted registrar; preserve existing Phase read operations."""
    registry.register_command(
        name="create",
        help="Preview Proposed Goal creation and separate Project attachment.",
        configure_parser=_goal_create,
        handle=_goal_create_command,
        source=__name__,
        operation_ref="goal.customer.create_and_attach",
    )
    registry.register_command(
        name="show",
        help="Qualified planning name or existing committed Phase Goal path.",
        configure_parser=_goal_show_parser,
        handle=_goal_show_command,
        source=__name__,
        operation_ref="goal.customer.show",
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
    # Registration/help perform no provider imports or filesystem operations.
    from aware_workflow.goal_customer import InitialGoalCustomerClient

    root = cast(Path, args.repository_root)
    if not root.is_absolute():
        raise ValueError("explicit_absolute_repository_root_required")
    return InitialGoalCustomerClient.filesystem(
        repository_root=root,
        manifest_path=str(cast(Path, args.protocol_manifest)),
    )


def _output(stage: str, result: dict[str, Any], summary: str, format: str) -> None:
    wire = json.dumps(
        {
            "schema_id": "aware.project-goal.customer-cli-output.v1",
            "stage": stage,
            "result": result,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    if format == "json":
        print(wire)
    else:
        print(summary)
        # Full original receipts from THIS invocation, not a repeated mutation.
        print(wire, file=sys.stderr)


def _failure(
    error: BaseException, *, attempted: bool, result: dict[str, Any] | None = None
) -> int:
    print(
        json.dumps(
            {
                "schema_id": "aware.project-goal.customer-cli-output.v1",
                "stage": "uncertain" if attempted else "refused",
                "reason": str(error) or type(error).__name__,
                "result": result,
                "effects": "inspect_original_outcome" if attempted else "not_started",
                "authorizes_redispatch": False,
            },
            sort_keys=True,
        ),
        file=sys.stderr,
    )
    return 3 if attempted else 2


def _run_create(invocation: AwareCommandInvocation, *, goal: bool) -> int:
    args = invocation.args
    attempted = False
    result = None
    try:
        apply = cast(bool, args.apply)
        if apply and not (sys.stdin.isatty() and sys.stdout.isatty()):
            raise ValueError(
                "noninteractive_apply_requires_original_durable_review_binding"
            )
        if not cast(Path, args.repository_root).is_absolute():
            raise ValueError("explicit_absolute_repository_root_required")
        from aware_workflow.goal_customer import summarize_goal_customer
        from aware_workflow.project_customer import (
            InitialProjectCustomerClient,
            summarize_project_customer,
        )

        summary = summarize_goal_customer if goal else summarize_project_customer
        selected = (
            _client(args)
            if goal
            else InitialProjectCustomerClient.filesystem(
                repository_root=cast(Path, args.repository_root),
                manifest_path=str(cast(Path, args.protocol_manifest)),
            )
        )
        authored = {"title": args.title, "priority": args.priority}
        if goal:
            authored.update(project=args.project, intent=args.intent, date=args.date)
        plan = selected.prepare_create(args.name, **authored)
        preview = plan.to_wire()
        heading = (
            f"Repository: {args.repository_root}\nManifest: {args.protocol_manifest}\n"
            f"Profile: owner-qualified initial-authoring fs_v4. Source: {preview['source_revision']}\n"
        )
        if goal:
            heading += f"Intent: {args.intent}\n"
        _output("preview", preview, heading + summary(preview), args.format)
        if not apply:
            return 0
        print(
            f"Local authoring only, not Goal approval or RUN. Type 'create {args.name}' to confirm this exact plan: ",
            file=sys.stderr,
            flush=True,
        )
        if sys.stdin.readline().rstrip("\r\n") != f"create {args.name}":
            raise ValueError("exact_plan_confirmation_not_given")
        attempted = True
        # Never reconstruct or refresh the plan after confirmation.
        result = selected.apply_create(plan)
        _output("result", result, summary(result), args.format)
        expected = "created_and_linked" if goal else "created"
        return 0 if result["disposition"] == expected else 3
    except (OSError, TypeError, ValueError, KeyboardInterrupt) as error:
        return _failure(error, attempted=attempted, result=result)


def _project_create(invocation: AwareCommandInvocation) -> int:
    return _run_create(invocation, goal=False)


def _goal_create_command(invocation: AwareCommandInvocation) -> int:
    return _run_create(invocation, goal=True)


def _read(invocation: AwareCommandInvocation, *, project: bool) -> int:
    args = invocation.args
    try:
        from aware_workflow.goal_customer import summarize_customer_read

        selected = _client(args)
        result = (
            selected.show_current_project(args.name)
            if project
            else selected.show(args.name, date=args.date)
        )
        _output("reading", result, summarize_customer_read(result), args.format)
        return 0
    except (OSError, TypeError, ValueError) as error:
        return _failure(error, attempted=False)


def _project_show(invocation: AwareCommandInvocation) -> int:
    return _read(invocation, project=True)


def _goal_show_command(invocation: AwareCommandInvocation) -> int:
    if invocation.args.goal_path is not None:
        if invocation.args.date is not None:
            return _failure(ValueError("date_is_planning_only"), attempted=False)
        return _show(invocation)
    return _read(invocation, project=False)
