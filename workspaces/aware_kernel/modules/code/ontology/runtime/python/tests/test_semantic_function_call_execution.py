from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import pytest

from aware_code.semantic_function_call_execution import (
    SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY,
    SemanticFunctionCallExecutionConfig,
    SemanticFunctionCallExecutionResolution,
    SemanticFunctionCallExecutionStep,
    execute_semantic_function_call_resolutions,
)


@dataclass(frozen=True, slots=True)
class FakeResolution:
    status: str
    function_ref: str
    result_semantic_key: str | None = None
    result_object_id: str | None = None
    receiver_object_id: str | None = None
    reason: str | None = None

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": self.status,
            "function_ref": self.function_ref,
        }
        if self.result_semantic_key is not None:
            payload["result_semantic_key"] = self.result_semantic_key
        if self.result_object_id is not None:
            payload["result_object_id"] = self.result_object_id
        if self.receiver_object_id is not None:
            payload["receiver_object_id"] = self.receiver_object_id
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


class FakeAdapter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def execute_create_root(
        self,
        resolution: SemanticFunctionCallExecutionResolution,
    ) -> SemanticFunctionCallExecutionStep:
        self.calls.append(("create_root", resolution.result_semantic_key or ""))
        return SemanticFunctionCallExecutionStep(
            status="invoked",
            resolution_status=resolution.status,
            function_ref=cast(str, resolution.evidence_payload()["function_ref"]),
            semantic_key=resolution.result_semantic_key,
            result_object_id="created-root-id",
            evidence={"adapter": "root"},
        )

    async def execute_create_child(
        self,
        resolution: SemanticFunctionCallExecutionResolution,
    ) -> SemanticFunctionCallExecutionStep:
        self.calls.append(("create_child", resolution.result_semantic_key or ""))
        return SemanticFunctionCallExecutionStep(
            status="invoked",
            resolution_status=resolution.status,
            function_ref=cast(str, resolution.evidence_payload()["function_ref"]),
            semantic_key=resolution.result_semantic_key,
            receiver_object_id=resolution.receiver_object_id,
            result_object_id="created-child-id",
            evidence={"adapter": "child"},
        )


class FailingAdapter(FakeAdapter):
    async def execute_create_root(
        self,
        resolution: SemanticFunctionCallExecutionResolution,
    ) -> SemanticFunctionCallExecutionStep:
        _ = resolution
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_execution_kernel_invokes_safe_create_resolutions() -> None:
    adapter = FakeAdapter()

    result = await execute_semantic_function_call_resolutions(
        resolutions=(
            FakeResolution(
                status="create_root",
                function_ref="demo.Root.create",
                result_semantic_key="root",
            ),
            FakeResolution(
                status="create_child",
                function_ref="demo.Root.create_child",
                result_semantic_key="root/child",
                receiver_object_id="root-id",
            ),
        ),
        adapter=adapter,
    )

    assert adapter.calls == [
        ("create_root", "root"),
        ("create_child", "root/child"),
    ]
    assert result.status_counts == {"invoked": 2}
    assert result.invoked_count == 2
    assert result.evidence_payload()["step_count"] == 2


def test_execution_config_parses_materialization_context() -> None:
    config = SemanticFunctionCallExecutionConfig.from_materialization_context(
        {
            SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY: {
                "enabled": "true",
                "continue_on_failure": True,
            },
        }
    )

    assert config.enabled is True
    assert config.continue_on_failure is True
    assert config.evidence_payload() == {
        "enabled": True,
        "continue_on_failure": True,
    }


@pytest.mark.asyncio
async def test_execution_kernel_skips_noop_without_adapter_call() -> None:
    adapter = FakeAdapter()

    result = await execute_semantic_function_call_resolutions(
        resolutions=(
            FakeResolution(
                status="noop_existing",
                function_ref="demo.Root.create",
                result_semantic_key="root",
                result_object_id="existing-root-id",
            ),
        ),
        adapter=adapter,
    )

    assert adapter.calls == []
    assert result.status_counts == {"skipped_noop": 1}
    assert result.steps[0].result_object_id == "existing-root-id"


@pytest.mark.asyncio
async def test_execution_kernel_blocks_unsafe_resolutions_without_adapter_call() -> (
    None
):
    adapter = FakeAdapter()

    result = await execute_semantic_function_call_resolutions(
        resolutions=(
            FakeResolution(
                status="needs_ref_resolution",
                function_ref="demo.Root.create_child",
                result_semantic_key="root/child",
                reason="missing class ref",
            ),
            FakeResolution(
                status="unsupported_function",
                function_ref="demo.Unsupported.call",
                result_semantic_key="unsupported",
            ),
        ),
        adapter=adapter,
    )

    assert adapter.calls == []
    assert result.status_counts == {"blocked": 2}
    assert result.blocked_count == 2
    assert result.steps[0].reason == "missing class ref"


@pytest.mark.asyncio
async def test_execution_kernel_records_failure_and_stops_by_default() -> None:
    adapter = FailingAdapter()

    result = await execute_semantic_function_call_resolutions(
        resolutions=(
            FakeResolution(
                status="create_root",
                function_ref="demo.Root.create",
                result_semantic_key="root",
            ),
            FakeResolution(
                status="create_child",
                function_ref="demo.Root.create_child",
                result_semantic_key="root/child",
            ),
        ),
        adapter=adapter,
    )

    assert result.status_counts == {"failed": 1}
    assert result.failed_count == 1
    assert result.steps[0].error == "RuntimeError: boom"


@pytest.mark.asyncio
async def test_execution_kernel_can_continue_after_failure() -> None:
    adapter = FailingAdapter()

    result = await execute_semantic_function_call_resolutions(
        resolutions=(
            FakeResolution(
                status="create_root",
                function_ref="demo.Root.create",
                result_semantic_key="root",
            ),
            FakeResolution(
                status="needs_ref_resolution",
                function_ref="demo.Root.create_child",
                result_semantic_key="root/child",
            ),
        ),
        adapter=adapter,
        continue_on_failure=True,
    )

    assert result.status_counts == {"blocked": 1, "failed": 1}
