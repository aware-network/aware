from __future__ import annotations

from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_code.types.json import JsonArray, JsonObject
from aware_environment_service_dto.environment.environment import (
    InvokeFunctionCallTarget,
    InvokeFunctionRequest,
    InvokeFunctionResponse,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_environment.branching import stable_environment_thread_branch_id


class _OcgSupport:
    @staticmethod
    def find_projection_hash_by_name(
        *,
        index: MetaGraphRuntimeIndex,
        projection_name: str,
    ) -> str:
        target = (projection_name or "").strip()
        for opg in index.ocg.object_projection_graphs:
            name = (opg.name or "").strip()
            if name == target:
                return opg.projection_hash
        raise ValueError(
            f"Projection {projection_name!r} was not found in hosted environment OCG"
        )

    @staticmethod
    def resolve_public_function_id(
        *,
        index: MetaGraphRuntimeIndex,
        class_name_suffix: str,
        function_name: str,
    ) -> UUID:
        normalized_suffix = (class_name_suffix or "").strip()
        normalized_fn_name = (function_name or "").strip()
        if not normalized_suffix:
            raise ValueError("class_name_suffix is required")
        if not normalized_fn_name:
            raise ValueError("function_name is required")

        suffix_leaf = normalized_suffix.rsplit(".", 1)[-1]

        function_by_id: dict[UUID, object] = {}
        for node in index.ocg.object_config_graph_nodes:
            if (
                node.type == ObjectConfigGraphNodeType.function
                and node.function_config is not None
            ):
                function_by_id[node.function_config.id] = node.function_config

        matches: set[UUID] = set()
        for node in index.ocg.object_config_graph_nodes:
            if (
                node.type != ObjectConfigGraphNodeType.class_
                or node.class_config is None
            ):
                continue
            class_name = (node.class_config.name or "").strip()
            class_match = class_name.endswith(normalized_suffix)
            if not class_match and "." in normalized_suffix:
                class_match = class_name == suffix_leaf or class_name.endswith(
                    f".{suffix_leaf}"
                )
            if not class_match:
                continue
            for link in node.class_config.class_config_function_configs:
                if not link.is_public:
                    continue
                fn_cfg = link.function_config
                function_config_id = getattr(link, "function_config_id", None)
                if function_config_id is not None:
                    fn_cfg = function_by_id.get(function_config_id) or fn_cfg
                if fn_cfg is None:
                    continue
                if (fn_cfg.name or "").strip() == normalized_fn_name:
                    matches.add(fn_cfg.id)

        if not matches:
            raise ValueError(
                "Could not resolve function "
                f"{normalized_fn_name!r} for class suffix {normalized_suffix!r}"
            )
        if len(matches) > 1:
            raise ValueError(
                "Ambiguous function "
                f"{normalized_fn_name!r} for class suffix {normalized_suffix!r}"
            )
        return next(iter(matches))


class _InvokeSupport:
    @staticmethod
    def assert_invoke_succeeded(
        *,
        response: InvokeFunctionResponse,
        label: str,
    ) -> None:
        if response.status == "succeeded":
            return
        if response.error:
            raise RuntimeError(f"{label} failed: {response.error}")
        raise RuntimeError(f"{label} failed")

    @staticmethod
    async def invoke_instance_environment_function(
        *,
        runtime: Any,
        index: MetaGraphRuntimeIndex,
        actor_id: UUID | None,
        environment_id: UUID,
        process_id: UUID,
        thread_id: UUID,
        branch_id: UUID,
        projection_hash: str,
        object_id: UUID,
        function_id: UUID,
        args: list[Any],
        commit: bool,
    ) -> InvokeFunctionResponse:
        request = InvokeFunctionRequest(
            operation="invoke_function",
            actor_id=actor_id,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            call_target=InvokeFunctionCallTarget.instance,
            object_id=object_id,
            object_projection_graph_id=None,
            function_id=function_id,
            args=JsonArray(args),
            kwargs=JsonObject({}),
            expected_graph_hash_pre=None,
            expected_head_commit_id=None,
            commit=commit,
            publish=False,
        )
        return await runtime.invoker.invoke_function_with_index(
            index=index,
            request=request,
        )


class _StableIds:
    @staticmethod
    def stable_boot_process_id(*, environment_id: UUID) -> UUID:
        return uuid5(NAMESPACE_URL, f"aware:process:{environment_id}:environment")

    @staticmethod
    def stable_boot_thread_id(*, environment_id: UUID) -> UUID:
        return uuid5(NAMESPACE_URL, f"aware:thread:{environment_id}:bootstrap")

    @staticmethod
    def stable_branch_id(*, environment_id: UUID, thread_id: UUID) -> UUID:
        return stable_environment_thread_branch_id(
            environment_id=environment_id,
            thread_id=thread_id,
        )


invoke_support = _InvokeSupport()
ocg_support = _OcgSupport()
stable_ids = _StableIds()

__all__ = [
    "invoke_support",
    "ocg_support",
    "stable_ids",
]
