from __future__ import annotations

from pathlib import Path
from typing import cast
from uuid import uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
import aware_meta.materialization.schemas as materialization_schemas
from aware_meta.materialization.contracts import (
    MaterializationLaneContext,
    MaterializationPlan,
    MaterializationStep,
    MaterializationStepResult,
    validate_materialization_plan,
)
from aware_meta.materialization.executor import (
    MaterializationExecutionError,
    MaterializationExecutor,
)
from aware_meta.materialization.receipts import (
    MaterializationRunReceipt,
    MaterializationStepReceipt,
)
from aware_meta.materialization.schemas import (
    LocalMaterializationExecutionResult,
    MaterializationOutcome,
    MaterializationSource,
)


def _lane() -> MaterializationLaneContext:
    return MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="projection-action-experience",
    )


def test_meta_materialization_protocol_is_meta_owned() -> None:
    assert MaterializationLaneContext.__module__ == (
        "aware_meta.materialization.contracts"
    )
    assert MaterializationExecutionError.__module__ == (
        "aware_meta.materialization.executor"
    )


def test_materialization_outcome_is_split_from_local_execution_fields() -> None:
    assert not hasattr(materialization_schemas, "MaterializationResult")
    assert "MaterializationResult" not in materialization_schemas.__all__

    typed_fields = set(MaterializationOutcome.model_fields)
    local_fields = set(LocalMaterializationExecutionResult.model_fields)
    assert local_fields - typed_fields == {"files", "packages", "post_step_receipts"}

    result = LocalMaterializationExecutionResult(
        materialization_name="demo",
        source_kind=MaterializationSource.ontology,
        target_language=CodeLanguage.python,
        aware_root=Path("/repo"),
        output_root=Path("/repo/out"),
        files=[Path("/repo/out/demo.py")],
        packages=[],
        post_step_receipts=[{"tool": "pytest", "status": "passed"}],
    )

    payload = result.model_dump()
    assert "files" not in payload
    assert "packages" not in payload
    assert "post_step_receipts" not in payload


def test_validate_materialization_plan_rejects_duplicate_step_id() -> None:
    plan = MaterializationPlan(
        module_id="experience",
        pipeline_id="experience.compile_plan.action",
        lane=_lane(),
        steps=(
            MaterializationStep(
                step_id="action:open_door",
                step_kind="experience.action",
                payload={},
            ),
            MaterializationStep(
                step_id="action:open_door",
                step_kind="experience.action",
                payload={},
            ),
        ),
    )

    with pytest.raises(ValueError, match="step_id must be unique"):
        validate_materialization_plan(plan=plan)


@pytest.mark.asyncio
async def test_materialization_executor_returns_receipt_on_success() -> None:
    plan = MaterializationPlan(
        module_id="experience",
        pipeline_id="experience.compile_plan.action",
        lane=_lane(),
        steps=(
            MaterializationStep(
                step_id="action:open_door",
                step_kind="experience.action",
                payload={"action_name": "open_door"},
            ),
        ),
    )

    async def _runner(
        *,
        plan: MaterializationPlan,
        step: MaterializationStep,
    ) -> MaterializationStepResult:
        _ = (plan, step)
        return MaterializationStepResult(details={"ok": True}, commit_id=uuid4())

    receipt = await MaterializationExecutor().run(plan=plan, runner=_runner)

    assert receipt.status == "succeeded"
    assert receipt.module_id == "experience"
    assert receipt.pipeline_id == "experience.compile_plan.action"
    assert len(receipt.steps) == 1
    assert receipt.steps[0].status == "succeeded"
    assert receipt.steps[0].commit_id is not None


@pytest.mark.asyncio
async def test_materialization_executor_notifies_observer_for_step_lifecycle() -> None:
    plan = MaterializationPlan(
        module_id="experience",
        pipeline_id="experience.compile_plan.action",
        lane=_lane(),
        steps=(
            MaterializationStep(
                step_id="action:open_door",
                step_kind="experience.action",
                payload={"action_name": "open_door"},
            ),
        ),
    )
    events: list[tuple[str, str]] = []

    class _Observer:
        async def on_run_started(
            self,
            *,
            plan: MaterializationPlan,
            started_at_utc: str,
        ) -> None:
            _ = started_at_utc
            events.append(("run_started", plan.pipeline_id))

        async def on_step_started(
            self,
            *,
            plan: MaterializationPlan,
            step: MaterializationStep,
            started_at_utc: str,
        ) -> None:
            _ = (plan, started_at_utc)
            events.append(("step_started", step.step_id))

        async def on_step_finished(
            self,
            *,
            plan: MaterializationPlan,
            receipt: object,
        ) -> None:
            _ = plan
            typed_receipt = cast(MaterializationStepReceipt, receipt)
            events.append(("step_finished", typed_receipt.step_id))

        async def on_run_finished(self, *, receipt: object) -> None:
            typed_receipt = cast(MaterializationRunReceipt, receipt)
            events.append(("run_finished", typed_receipt.status))

    async def _runner(
        *,
        plan: MaterializationPlan,
        step: MaterializationStep,
    ) -> MaterializationStepResult:
        _ = (plan, step)
        return MaterializationStepResult(details={"ok": True}, commit_id=uuid4())

    receipt = await MaterializationExecutor().run(
        plan=plan,
        runner=_runner,
        observer=_Observer(),
    )

    assert receipt.status == "succeeded"
    assert events == [
        ("run_started", "experience.compile_plan.action"),
        ("step_started", "action:open_door"),
        ("step_finished", "action:open_door"),
        ("run_finished", "succeeded"),
    ]


@pytest.mark.asyncio
async def test_materialization_executor_fails_without_commit_evidence() -> None:
    plan = MaterializationPlan(
        module_id="experience",
        pipeline_id="experience.compile_plan.action",
        lane=_lane(),
        steps=(
            MaterializationStep(
                step_id="action:open_door",
                step_kind="experience.action",
                payload={"action_name": "open_door"},
                commit_requested=True,
            ),
        ),
    )

    async def _runner(
        *,
        plan: MaterializationPlan,
        step: MaterializationStep,
    ) -> MaterializationStepResult:
        _ = (plan, step)
        return MaterializationStepResult(details={"ok": True})

    with pytest.raises(MaterializationExecutionError) as exc_info:
        _ = await MaterializationExecutor().run(plan=plan, runner=_runner)

    assert exc_info.value.step_id == "action:open_door"
    assert exc_info.value.run_receipt.status == "failed"
    assert exc_info.value.run_receipt.steps[-1].status == "failed"
    assert "missing commit/head evidence" in (
        exc_info.value.run_receipt.steps[-1].error or ""
    )
    assert "missing commit/head evidence" in str(exc_info.value)


def test_validate_materialization_plan_requires_projection_hash() -> None:
    plan = MaterializationPlan(
        module_id="experience",
        pipeline_id="experience.compile_plan.action",
        lane=MaterializationLaneContext(
            branch_id=uuid4(),
            projection_hash="",
        ),
        steps=(),
    )
    with pytest.raises(ValueError, match="projection_hash is required"):
        validate_materialization_plan(plan=plan)
