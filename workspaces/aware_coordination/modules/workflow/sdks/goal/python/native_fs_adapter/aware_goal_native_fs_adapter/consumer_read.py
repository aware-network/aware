"""Read-only consumer composition over original Goal providers.

This module qualifies Git inputs, not Goal meaning. It never prepares a
manifest, retries discovery, repairs projections or grants execution authority.
"""

from __future__ import annotations

# Concrete adapter siblings share their original source primitives.
# pyright: reportPrivateUsage=false
import hashlib
from collections.abc import Mapping
from typing import cast, final

from aware_goal_operational_runtime.phase_native_view import project_goal_native_view_v2
from aware_goal_sdk.phase_operation import GoalPhaseOperationClient
from aware_protocol_fs_adapter.native_goal_resolver import require_native_goal_resolver

from .native_view_source import CommittedGoalViewSourceProvider
from .phase_operation import NativeGitGoalPhaseOperationProvider


@final
class NativeGoalConsumerReadClient:
    """A concrete Git composition, not a new provider-neutral Goal evaluator."""

    def __init__(
        self,
        resolver_capability: object,
        *,
        prerequisite_goal_paths: Mapping[str, str] | None = None,
    ) -> None:
        self._capability = require_native_goal_resolver(resolver_capability)
        self._source = CommittedGoalViewSourceProvider(
            resolver_capability=self._capability,
            provider_ref="provider:goal-protocol-committed-read.v1",
            provider_generation="generation:goal-protocol-committed-read.v1",
            source_scope_ref="scope:goal-protocol-committed-read.v1",
        )
        self._eligibility = NativeGitGoalPhaseOperationProvider(
            self._capability,
            prerequisite_goal_paths=prerequisite_goal_paths,
        )

    def _epoch(self) -> str:
        resolver = require_native_goal_resolver(self._capability)
        head = self._source._commit("HEAD")
        path = resolver.manifest_path.relative_to(resolver.repository_root).as_posix()
        manifest, _ = self._source._regular_file(head, path)
        if "sha256:" + hashlib.sha256(manifest).hexdigest() != resolver.manifest_sha256:
            raise ValueError("native_view_protocol_not_committed")
        self._finish(head)
        return head

    def _finish(self, revision: str, goal_path: str | None = None) -> None:
        resolver = require_native_goal_resolver(self._capability)
        if goal_path is not None:
            _ = resolver.resolve_goal_path(goal_path)
        resolver.revalidate()
        if self._source._commit("HEAD") != revision:
            raise ValueError("repository_head_advanced")

    def show(self, *, goal_path: str) -> dict[str, object]:
        """Return the original qualified source and its neutral reading.

        Associated Issue fields and schedules come from that same committed
        epoch. Unsupported facts stay unavailable in the original contract.
        """
        epoch = self._epoch()
        location = self._capability.resolve_goal_path(goal_path)
        tag = f"goal/{location.location_date}/{location.location_slug}"
        reading = self._source.observe(goal_tag=tag, expected_revision=epoch)
        self._source.require_current(reading)
        wire = reading.to_wire()
        state = project_goal_native_view_v2(
            wire, observation_ref=reading.observation_ref
        )
        self._source.require_current(reading)
        self._finish(epoch, goal_path)
        return {
            "operation": "show",
            "reading": wire,
            "observation_ref": reading.observation_ref,
            "state": state,
        }

    def eligibility(
        self, *, goal_path: str, lane_key: str, phase_key: str
    ) -> dict[str, object]:
        """Compose existing discovery and observation once, at one exact epoch.

        Whole-repository advancement, even unrelated to Goal bytes, refuses
        rather than silently discovering fresh evidence in this invocation.
        """
        epoch = self._epoch()
        request = self._eligibility.discover_eligibility_request(
            goal_path=goal_path,
            lane_key=lane_key,
            phase_key=phase_key,
        )
        self._finish(epoch, goal_path)
        result = GoalPhaseOperationClient(self._eligibility).observe_eligibility(
            request
        )
        if cast(str, result["source_revision_ref"]) != epoch:
            raise ValueError("repository_head_advanced")
        self._finish(epoch, goal_path)
        return {
            "operation": "eligibility",
            "discovered_revision": epoch,
            "request": request.to_wire(),
            "result": result,
        }
