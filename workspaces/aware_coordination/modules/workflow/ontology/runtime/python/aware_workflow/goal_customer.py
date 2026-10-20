"""Source-only first Goal/attachment composition over the original owners.

No public registrar, new issuer/store, source refresh, evaluator or writer.
The Project embedded in the original Goal source freezes the attachment target.
Every restart selects historical original requests; it restores no live grant.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date as calendar_date
from typing import Any
from weakref import WeakKeyDictionary

from aware_goal_operational_runtime.planning_creation_request import (
    make_planning_goal_creation_request,
)
from aware_protocol_fs_adapter.native_goal_resolver import (
    require_planning_goal_resolver,
)
from aware_workspace_sdk.initial_authoring.goal_publication import (
    InitialGoalPublicationRequest,
)
from aware_workspace_sdk.repository_publication.codec import (
    repository_publication_value_to_payload,
)

from .goal_planning_initial_intent import authorize_initial_planning_goal_intent
from .goal_planning_initial_plan import prepare_initial_planning_goal_postimage
from .goal_planning_initial_read import show_initial_planning_goal
from .goal_planning_initial_source import prepare_initial_planning_goal_source
from .project_create_contract import canonical
from .project_customer import InitialProjectCustomerClient, _client, _wire_observation
from .project_initial_membership import prepare_initial_project_membership
from .project_membership_contract import (
    ProjectGoalMembershipRequestV1,
    plan_project_goal_membership,
)
from .project_membership_read import show_initial_project_membership
from .project_source_codec import decode_project_context_toml

_CLIENTS = WeakKeyDictionary()
_CLIENT_PINS = WeakKeyDictionary()
_PLANS = WeakKeyDictionary()
_PLAN_PINS = WeakKeyDictionary()


def _owner(client):
    state = _CLIENTS.get(client) if type(client) is InitialGoalCustomerClient else None
    if state is None or state != _CLIENT_PINS.get(client) or state[0] != os.getpid():
        raise ValueError("original_goal_customer_client_required")
    _client(state[1])
    return state[1], *_client(state[1])


def _target(capability, name, date):
    if type(date) is not str or calendar_date.fromisoformat(date).isoformat() != date:
        raise ValueError("goal_customer_explicit_date_required")
    if type(name) is not str or not name or "/" in name or "\\" in name:
        raise ValueError("goal_customer_name_invalid")
    goal = require_planning_goal_resolver(capability.goal_capability)
    year, month, day = date.split("-")
    tail = (
        goal.goal_template.replace("YYYY", year)
        .replace("MM", month)
        .replace("DD", day)
        .replace("<slug>", name)
    )
    path = goal.goal_root + "/" + tail
    if goal.match_goal_path(path) != (date, name):
        raise ValueError("goal_customer_name_invalid")
    goal.resolve_goal_path(path)
    return path


def _membership(goal_request):
    # Fixed semantics, not a caller inclusion list or a refreshed Project.
    project = goal_request.source["project_request"]["source"]["project_plan"][
        "request"
    ]["record"]
    before = decode_project_context_toml(
        goal_request.source["project_request"]["source"]["project_plan"][
            "content_utf8"
        ].encode()
    )
    tag = goal_request.source["goal_plan"]["request"]["goal_tag"]
    request = ProjectGoalMembershipRequestV1.author(before.project.project_key, tag)
    # Validate the original authored record as well; no new identity source.
    if project != before.to_wire():
        raise ValueError("goal_customer_project_intent_changed")
    return request, plan_project_goal_membership(request, before)


@dataclass
class _PlanState:
    pid: int
    client: InitialGoalCustomerClient
    kind: str
    original: object
    preview: bytes
    frozen: bytes
    phase: str = "prepared"

    def pins(self):
        return (
            self.pid,
            self.client,
            self.kind,
            self.original,
            self.preview,
            self.frozen,
        )


def _plan(handle):
    state = _PLANS.get(handle) if type(handle) is GoalCustomerPlan else None
    if (
        state is None
        or state.pins() != _PLAN_PINS.get(handle)
        or state.pid != os.getpid()
    ):
        raise ValueError("original_goal_customer_plan_required")
    _owner(state.client)
    original = (
        state.original.to_wire()
        if state.kind == "create"
        else state.original.request.to_wire()
    )
    if canonical(original) != state.frozen:
        raise ValueError("goal_customer_plan_mutated")
    return state


def _issue(client, kind, original, preview):
    handle = object.__new__(GoalCustomerPlan)
    wire = original.to_wire() if kind == "create" else original.request.to_wire()
    state = _PlanState(
        os.getpid(), client, kind, original, canonical(preview), canonical(wire)
    )
    _PLANS[handle], _PLAN_PINS[handle] = state, state.pins()
    return handle


class GoalCustomerPlan:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):
        raise TypeError("use prepare_create or prepare_attachment")

    def __copy__(self):
        raise TypeError("goal_customer_plan_not_copyable")

    def __deepcopy__(self, memo):
        raise TypeError("goal_customer_plan_not_copyable")

    def __reduce_ex__(self, protocol):
        raise TypeError("goal_customer_plan_not_serializable")

    def to_wire(self):
        state = _plan(self)
        if state.phase != "prepared":
            raise ValueError("goal_customer_plan_spent")
        return json.loads(state.preview)


class InitialGoalCustomerClient:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __init__(self, *, project_client):
        if type(self) is not InitialGoalCustomerClient:
            raise ValueError("original_goal_customer_client_required")
        _client(project_client)
        state = (os.getpid(), project_client)
        _CLIENTS[self] = _CLIENT_PINS[self] = state

    @classmethod
    def filesystem(cls, *, repository_root, manifest_path="aware.protocol.toml"):
        if cls is not InitialGoalCustomerClient:
            raise ValueError("original_goal_customer_client_required")
        return cls(
            project_client=InitialProjectCustomerClient.filesystem(
                repository_root=repository_root, manifest_path=manifest_path
            )
        )

    def prepare_create(self, name, *, project, date, title, intent, priority="medium"):
        customer, workspace, capability = _owner(self)
        target = _target(capability, name, date)
        if workspace.observe_initial_authoring_request("goal")["state"] != "absent":
            raise ValueError("goal_customer_attempt_retained_use_observe")
        _, _, project_request, _ = customer._selected(project)
        tag = "goal/" + date + "/" + name
        request = make_planning_goal_creation_request(
            {
                "idempotency_key": "goal-create-" + name,
                "goal_tag": tag,
                "title": title,
                "intent": intent,
                "priority": priority,
                "owner_ref": workspace._provider._execution,
                "definition_of_done_ref": None,
                "locks_ref": None,
                "lanes": [],
                "definitions": [],
                "dependencies": [],
                "unresolved_dependencies": [],
            }
        )
        source = prepare_initial_planning_goal_source(
            workspace=workspace,
            resolver_capability=capability,
            project_publication_request=project_request,
            target_path=target,
            request=request,
        )
        before = decode_project_context_toml(
            project_request.source["project_plan"]["content_utf8"].encode()
        )
        membership = plan_project_goal_membership(
            ProjectGoalMembershipRequestV1.author(before.project.project_key, tag),
            before,
        )
        return _issue(
            self,
            "create",
            source,
            {
                "operation": "goal_create_and_attach",
                "disposition": "planned",
                "name": name,
                "date": date,
                "project_name": project,
                "target_path": target,
                "request": request.to_wire(),
                "project_path": project_request.source["target_path"],
                "membership_plan": membership.to_wire(),
                "source_revision": source.to_wire()["source_context"][
                    "source_revision"
                ],
                "planned_effects": [
                    "publish_proposed_goal",
                    "project_goal_file",
                    "publish_project_membership",
                    "replace_project_file",
                    "qualified_h2_read",
                ],
                "publication_admission": "not_issued",
                "planning_status": "not_yet_decomposed",
                "dispatch_effect": "none",
            },
        )

    def _selected(self, name, date):
        _, workspace, capability = _owner(self)
        selected = workspace.observe_initial_authoring_request("goal")
        if selected["state"] != "retained":
            raise ValueError("goal_customer_no_retained_publication_attempt")
        request = selected["request"]
        if type(request) is not InitialGoalPublicationRequest:
            raise ValueError("goal_customer_original_request_required")
        location = require_planning_goal_resolver(capability.goal_capability)
        matched = location.match_goal_path(request.source["target_path"])
        if (
            matched is None
            or matched[1] != name
            or (date is not None and date != matched[0])
        ):
            raise ValueError("goal_customer_selection_mismatch")
        # Address from the exact original retained request, not clock/recency.
        target = _target(capability, name, matched[0])
        if (
            type(request) is not InitialGoalPublicationRequest
            or request.source["target_path"] != target
        ):
            raise ValueError("goal_customer_selection_mismatch")
        member = workspace.observe_initial_authoring_request("membership")
        if member["state"] == "retained" and canonical(
            member["request"].source["preparation"]["source"]["goal_creation_request"]
        ) != canonical(request.to_wire()):
            raise ValueError("goal_customer_foreign_membership")
        return workspace, capability, selected, member

    def observe(self, name, *, date=None):
        _, _, goal, member = self._selected(name, date)
        return {
            "operation": "goal_observe",
            "goal_request": goal["request"].to_wire(),
            "goal_recovery": _wire_observation(goal["recovery"]),
            "membership_request": member["request"].to_wire()
            if member["state"] == "retained"
            else None,
            "membership_recovery": _wire_observation(member["recovery"])
            if member["state"] == "retained"
            else None,
            "authorizes_redispatch": False,
        }

    def show(self, name, *, date=None) -> dict[str, Any]:
        workspace, capability, goal, member = self._selected(name, date)
        if goal["recovery"]["disposition"] != "recorded":
            raise ValueError("goal_customer_publication_unavailable")
        if member["state"] == "retained":
            if member["recovery"]["disposition"] != "recorded":
                raise ValueError("goal_customer_attachment_uncertain")
            reading = show_initial_project_membership(
                workspace=workspace,
                resolver_capability=capability,
                publication_request=member["request"],
            ).to_wire()
            return {
                "operation": "goal_show",
                "disposition": "created_and_linked",
                "reading": reading,
            }
        reading = show_initial_planning_goal(
            workspace=workspace,
            resolver_capability=capability,
            publication_request=goal["request"],
        ).to_wire()
        return {
            "operation": "goal_show",
            "disposition": "created_unlinked",
            "reading": reading,
            "goal_creation_publication": goal["recovery"]["publication"],
        }

    def show_project(self, project):
        customer, workspace, capability = _owner(self)
        # Name qualification is historical; never use the stale H0 reader at H2.
        _, _, project_request, _ = customer._selected(project)
        selected = workspace.observe_initial_authoring_request("membership")
        if (
            selected["state"] != "retained"
            or selected["recovery"]["disposition"] != "recorded"
        ):
            raise ValueError("goal_customer_project_successor_reading_unavailable")
        request = selected["request"]
        if canonical(
            request.source["preparation"]["source"]["project_creation_request"]
        ) != canonical(project_request.to_wire()):
            raise ValueError("goal_customer_selection_mismatch")
        reading = show_initial_project_membership(
            workspace=workspace,
            resolver_capability=capability,
            publication_request=request,
        ).to_wire()
        return {
            "operation": "project_show_at_membership",
            "disposition": "created_and_linked",
            "reading": reading,
        }

    def show_current_project(self, project):
        """Select original H0/H2 reading, never fall back from a stale successor."""
        customer, workspace, _ = _owner(self)
        membership = workspace.observe_initial_authoring_request("membership")
        if membership["state"] == "absent":
            return customer.show(project)
        # Malformed, pending or stale membership cannot become an empty Project.
        return self.show_project(project)

    def project_goal(self, name, *, date=None):
        workspace, _, goal, member = self._selected(name, date)
        if member["state"] != "absent":
            raise ValueError("goal_customer_use_membership_projection")
        return _wire_observation(workspace.project_initial_goal(goal["request"]))

    def project_attachment(self, name, *, date=None):
        workspace, _, _, member = self._selected(name, date)
        if member["state"] != "retained":
            raise ValueError("goal_customer_no_retained_attachment")
        return _wire_observation(
            workspace.project_initial_membership(member["request"])
        )

    def prepare_attachment(self, name, *, date=None):
        workspace, capability, goal, member = self._selected(name, date)
        if member["state"] != "absent":
            raise ValueError("goal_customer_attachment_retained_use_observe")
        intent, expected = _membership(goal["request"])
        source = prepare_initial_project_membership(
            workspace=workspace,
            resolver_capability=capability,
            goal_publication_request=goal["request"],
            request=intent,
        )
        original = workspace.plan_initial_membership(
            source, idempotency_key="goal-attach-" + name
        )
        if canonical(source.to_wire()["plan"]) != canonical(expected.to_wire()):
            raise ValueError("goal_customer_attachment_intent_changed")
        return _issue(
            self,
            "attach",
            original,
            {
                "operation": "goal_attach",
                "disposition": "planned",
                "name": name,
                "date": date,
                "request": original.request.to_wire(),
                "membership_plan": expected.to_wire(),
                "publication_admission": "not_issued",
                "dispatch_effect": "none",
            },
        )

    def apply_attachment(self, plan):
        state = _plan(plan)
        if (
            state.client is not self
            or state.kind != "attach"
            or state.phase != "prepared"
        ):
            raise ValueError("goal_customer_plan_foreign_kind_or_spent")
        _, workspace, _ = _owner(self)
        preview = json.loads(state.preview)
        output: dict[str, Any] = {
            "operation": "goal_attach",
            "disposition": "uncertain",
            "authorizes_redispatch": False,
        }
        frozen_h2: bytes | None = None
        state.phase = "applying"
        try:
            admission = workspace.admit_initial_membership(state.original)
            result = workspace.publish_initial_membership(admission)
            output["original_result"] = repository_publication_value_to_payload(result)
            recovered = workspace.recover_initial_membership(state.original.request)
            output["membership_recovery"] = _wire_observation(recovered)
            if (
                recovered["disposition"] != "recorded"
                or result != recovered["original_result"]
                or not result.ledger_complete
            ):
                return output
            projection = workspace.project_initial_membership(state.original.request)
            output["membership_projection"] = _wire_observation(projection)
            if projection.get("projection_state") == "installed":
                output["reading"] = self.show(preview["name"], date=preview["date"])
                frozen_h2 = canonical(output["reading"])
                output["disposition"] = "created_and_linked"
        except (OSError, ValueError, TypeError, RuntimeError) as error:
            output["diagnostics"] = [str(error)]
        finally:
            state.phase = "spent"
            try:
                output["retained"] = self.observe(preview["name"], date=preview["date"])
            except (OSError, ValueError, TypeError, RuntimeError) as error:
                output["recovery_diagnostics"] = [str(error)]
        return self._finish_linked_output(output, frozen_h2, preview)

    def apply_create(self, plan):
        state = _plan(plan)
        if (
            state.client is not self
            or state.kind != "create"
            or state.phase != "prepared"
        ):
            raise ValueError("goal_customer_plan_foreign_kind_or_spent")
        _, workspace, _ = _owner(self)
        preview = json.loads(state.preview)
        output: dict[str, Any] = {
            "operation": "goal_create_and_attach",
            "disposition": "uncertain",
            "authorizes_redispatch": False,
        }
        frozen_h2: bytes | None = None
        state.phase = "applying"
        try:
            # The owning source is requalified, not recaptured or refreshed.
            state.original.require_current()
            permission = authorize_initial_planning_goal_intent(state.original)
            postimage = prepare_initial_planning_goal_postimage(
                state.original, permission
            )
            original = workspace.plan_initial_goal(postimage)
            _, membership = _membership(original.request)
            if canonical(membership.to_wire()) != canonical(preview["membership_plan"]):
                raise ValueError("goal_customer_attachment_intent_changed")
            result = workspace.publish_initial_goal(
                workspace.admit_initial_goal(original)
            )
            output["original_result"] = repository_publication_value_to_payload(result)
            recovered = workspace.recover_initial_goal(original.request)
            output["goal_recovery"] = _wire_observation(recovered)
            if (
                recovered["disposition"] != "recorded"
                or result != recovered["original_result"]
                or not result.ledger_complete
            ):
                return output
            projection = workspace.project_initial_goal(original.request)
            output["goal_projection"] = _wire_observation(projection)
            if projection.get("projection_state") != "installed":
                return output
            output["goal_reading"] = self.show(preview["name"], date=preview["date"])
            output["disposition"] = "created_unlinked"
            attachment = self.prepare_attachment(preview["name"], date=preview["date"])
            if canonical(attachment.to_wire()["membership_plan"]) != canonical(
                preview["membership_plan"]
            ):
                raise ValueError("goal_customer_attachment_intent_changed")
            attached = self.apply_attachment(attachment)
            output["attachment"] = attached
            # Uncertain membership can have published; never call that unlinked.
            output["disposition"] = attached["disposition"]
            if attached["disposition"] == "created_and_linked":
                frozen_h2 = canonical(attached["reading"])
        except (OSError, ValueError, TypeError, RuntimeError) as error:
            output["diagnostics"] = [str(error)]
        finally:
            state.phase = "spent"
            try:
                output["retained"] = self.observe(preview["name"], date=preview["date"])
                if (
                    output["retained"]["membership_request"] is not None
                    and output["disposition"] != "created_and_linked"
                ):
                    output["disposition"] = "uncertain"
            except (OSError, ValueError, TypeError, RuntimeError) as error:
                output["recovery_diagnostics"] = [str(error)]
        return self._finish_linked_output(output, frozen_h2, preview)

    def _finish_linked_output(
        self,
        output: dict[str, Any],
        frozen_h2: bytes | None,
        preview: dict[str, Any],
    ) -> dict[str, Any]:
        """Finish ALL historical recovery before qualifying the frozen H2.

        The original reader must prove the same epoch, not refresh it. Nothing
        after this call may resolve another provider/source/retention input.
        Earlier qualified readings remain historical evidence on uncertainty.
        """
        if output["disposition"] == "created_and_linked":
            try:
                if frozen_h2 is None:
                    raise ValueError("goal_customer_frozen_h2_required")
                current = self.show(preview["name"], date=preview["date"])
                if canonical(current) != frozen_h2:
                    raise ValueError("goal_customer_frozen_h2_changed")
            except (OSError, ValueError, TypeError, RuntimeError) as error:
                output["disposition"] = "uncertain"
                output["qualification_diagnostics"] = [str(error)]
        return output


def summarize_goal_customer(result):
    """Descriptive only: an undecomposed Goal never implies eligibility."""
    if result["disposition"] == "planned":
        if result["operation"] == "goal_attach":
            return "Attach the existing Proposed Goal to its frozen Project?\nNo Goal recreation. No publication permission issued. No work started."
        request = result["request"]
        return f"Create Goal {request['title']} in Project {result['project_name']}?\nStatus: Proposed · not yet decomposed. Priority: {request['priority']}.\nGoal target: {result['target_path']}\nThen separately attach to: {result['project_path']}\nNo publication permission issued. No work started."
    if result["disposition"] == "created_and_linked":
        return "Goal created and attached to Project.\nStatus: Proposed · not yet decomposed. No work started.\nSuggested next step: create an Issue for your first task."
    if result["disposition"] == "created_unlinked":
        return "Goal created. Project attachment is pending.\nThe original Goal receipt is retained. No work started."
    return "Goal creation or attachment is uncertain.\nInspect original retained receipts before continuing; do not repeat creation."


def summarize_customer_read(result: dict[str, Any]) -> str:
    """Describe the qualified original reading; no source lookup or decision."""
    reading = result["reading"]
    if result["operation"] == "project_show":
        project = reading["content"]["project"]
        return f"Project {project['title']}.\nStatus: {project['status']} · no Goals yet.\nNo work started."
    if result["operation"] == "project_show_at_membership":
        record = reading["project"]
        return f"Project {record['title']}.\nStatus: {record['status']}. Goals: {', '.join(record['goal_tags'])}.\nNo work started."
    if result["operation"] != "goal_show":
        raise ValueError("customer_read_operation_invalid")
    document = (
        reading["goal"]
        if result["disposition"] == "created_and_linked"
        else reading["document"]
    )
    membership = (
        "Attached to Project."
        if result["disposition"] == "created_and_linked"
        else "Project attachment is pending."
    )
    return f"Goal {document['title']}.\nStatus: Proposed · not yet decomposed. {membership}\nNo work started. Suggested next step: create an Issue for your first task."
