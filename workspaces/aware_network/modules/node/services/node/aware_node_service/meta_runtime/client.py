from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence
from uuid import UUID

from aware_meta_sdk import MetaSdkClient


class NodeMetaRuntimeClient(Protocol):
    async def get_lane_head(
        self,
        *,
        domain_branch_id: UUID,
        domain_projection_hash: str,
        actor_id: UUID | None = None,
    ) -> Any:
        """Read the committed graph lane head through Meta service authority."""
        ...

    async def get_object_instance_graph_commit(
        self,
        *,
        domain_branch_id: UUID,
        domain_projection_hash: str,
        domain_commit_id: UUID,
        actor_id: UUID | None = None,
    ) -> Any:
        """Read one committed ObjectInstanceGraphCommit through Meta service authority."""
        ...

    async def invoke_function(
        self,
        *,
        actor_id: UUID,
        function_id: UUID,
        domain_branch_id: UUID | None = None,
        domain_projection_hash: str | None = None,
        call_target: object = "instance",
        target_object_id: UUID | None = None,
        object_projection_graph_id: UUID | None = None,
        args: Sequence[object] = (),
        kwargs: Mapping[str, object] | None = None,
        expected_graph_hash_pre: str | None = None,
        expected_head_commit_id: UUID | None = None,
        commit: bool = True,
        publish: bool = False,
    ) -> Any:
        """Invoke one graph function through Meta service authority."""
        ...

    async def resolve_projection(
        self,
        *,
        actor_id: UUID | None = None,
        projection_name: str | None = None,
        projection_hash: str | None = None,
        object_projection_graph_id: UUID | None = None,
        include_available: bool = False,
    ) -> Any:
        """Resolve graph projection coordinates through Meta service authority."""
        ...

    async def describe_workspace(
        self,
        *,
        actor_id: UUID | None = None,
        workspace_root: str | None = None,
        repo_root: str | None = None,
        aware_root: str | None = None,
        environment_config_id: UUID | None = None,
        required_projection_names: Sequence[str] = (),
        force_refresh: bool = False,
        include_timings: bool = True,
        include_package_timings: bool = True,
        include_workspace_commit_truth: bool = False,
    ) -> Any:
        """Read Meta-owned workspace runtime coordinates."""
        ...


@dataclass(frozen=True)
class NodeMetaSdkRuntimeClient:
    sdk: MetaSdkClient

    async def get_lane_head(
        self,
        *,
        domain_branch_id: UUID,
        domain_projection_hash: str,
        actor_id: UUID | None = None,
    ) -> Any:
        return await self.sdk.get_lane_head(
            actor_id=actor_id,
            domain_branch_id=domain_branch_id,
            domain_projection_hash=domain_projection_hash,
        )

    async def get_object_instance_graph_commit(
        self,
        *,
        domain_branch_id: UUID,
        domain_projection_hash: str,
        domain_commit_id: UUID,
        actor_id: UUID | None = None,
    ) -> Any:
        return await self.sdk.get_object_instance_graph_commit(
            actor_id=actor_id,
            domain_branch_id=domain_branch_id,
            domain_projection_hash=domain_projection_hash,
            domain_commit_id=domain_commit_id,
        )

    async def invoke_function(
        self,
        *,
        actor_id: UUID,
        function_id: UUID,
        domain_branch_id: UUID | None = None,
        domain_projection_hash: str | None = None,
        call_target: object = "instance",
        target_object_id: UUID | None = None,
        object_projection_graph_id: UUID | None = None,
        args: Sequence[object] = (),
        kwargs: Mapping[str, object] | None = None,
        expected_graph_hash_pre: str | None = None,
        expected_head_commit_id: UUID | None = None,
        commit: bool = True,
        publish: bool = False,
    ) -> Any:
        return await self.sdk.invoke_function(
            actor_id=actor_id,
            function_id=function_id,
            domain_branch_id=domain_branch_id,
            domain_projection_hash=domain_projection_hash,
            call_target=call_target,  # type: ignore[arg-type]
            target_object_id=target_object_id,
            object_projection_graph_id=object_projection_graph_id,
            args=args,  # type: ignore[arg-type]
            kwargs=kwargs,  # type: ignore[arg-type]
            expected_graph_hash_pre=expected_graph_hash_pre,
            expected_head_commit_id=expected_head_commit_id,
            commit=commit,
            publish=publish,
        )

    async def resolve_projection(
        self,
        *,
        actor_id: UUID | None = None,
        projection_name: str | None = None,
        projection_hash: str | None = None,
        object_projection_graph_id: UUID | None = None,
        include_available: bool = False,
    ) -> Any:
        return await self.sdk.resolve_projection(
            actor_id=actor_id,
            projection_name=projection_name,
            projection_hash=projection_hash,
            object_projection_graph_id=object_projection_graph_id,
            include_available=include_available,
        )

    async def describe_workspace(
        self,
        *,
        actor_id: UUID | None = None,
        workspace_root: str | None = None,
        repo_root: str | None = None,
        aware_root: str | None = None,
        environment_config_id: UUID | None = None,
        required_projection_names: Sequence[str] = (),
        force_refresh: bool = False,
        include_timings: bool = True,
        include_package_timings: bool = True,
        include_workspace_commit_truth: bool = False,
    ) -> Any:
        return await self.sdk.describe_workspace(
            actor_id=actor_id,
            workspace_root=workspace_root,
            repo_root=repo_root,
            aware_root=aware_root,
            environment_config_id=environment_config_id,
            required_projection_names=required_projection_names,
            force_refresh=force_refresh,
            include_timings=include_timings,
            include_package_timings=include_package_timings,
            include_workspace_commit_truth=include_workspace_commit_truth,
        )


def build_node_meta_runtime_client(
    sdk: MetaSdkClient,
) -> NodeMetaRuntimeClient:
    return NodeMetaSdkRuntimeClient(sdk=sdk)


__all__ = [
    "NodeMetaRuntimeClient",
    "NodeMetaSdkRuntimeClient",
    "build_node_meta_runtime_client",
]
