from __future__ import annotations

from dataclasses import dataclass
from typing import override

from aware_meta.materialization.contracts import (
    MaterializationExecutionObserver,
    MaterializationPlan,
    MaterializationStep,
    MaterializationStepResult,
    MaterializationStepRunner,
    validate_materialization_plan,
)
from aware_meta.materialization.receipts import (
    MaterializationRunReceipt,
    MaterializationStepReceipt,
    utc_now_iso,
)


@dataclass(slots=True)
class MaterializationExecutionError(RuntimeError):
    step_id: str
    run_receipt: MaterializationRunReceipt

    @override
    def __str__(self) -> str:
        message = (
            "materialization step failed: "
            f"pipeline={self.run_receipt.pipeline_id!r} "
            f"step_id={self.step_id!r}"
        )
        failed_step = next(
            (
                step
                for step in reversed(self.run_receipt.steps)
                if step.step_id == self.step_id and step.error
            ),
            None,
        )
        if failed_step is not None:
            message += f" error={failed_step.error}"
        return message


class MaterializationExecutor:
    async def run(
        self,
        *,
        plan: MaterializationPlan,
        runner: MaterializationStepRunner,
        observer: MaterializationExecutionObserver | None = None,
    ) -> MaterializationRunReceipt:
        validate_materialization_plan(plan=plan)
        run_started_at = utc_now_iso()
        step_receipts: list[MaterializationStepReceipt] = []
        await self._notify_run_started(
            observer=observer,
            plan=plan,
            started_at_utc=run_started_at,
        )

        for step in plan.steps:
            receipt = await self._run_step(
                plan=plan,
                step=step,
                runner=runner,
                observer=observer,
            )
            step_receipts.append(receipt)
            if receipt.status == "failed":
                run_receipt = MaterializationRunReceipt(
                    module_id=plan.module_id,
                    pipeline_id=plan.pipeline_id,
                    lane=plan.lane,
                    status="failed",
                    started_at_utc=run_started_at,
                    finished_at_utc=utc_now_iso(),
                    steps=tuple(step_receipts),
                )
                await self._notify_run_finished(
                    observer=observer,
                    receipt=run_receipt,
                )
                raise MaterializationExecutionError(
                    step_id=step.step_id,
                    run_receipt=run_receipt,
                )

        run_receipt = MaterializationRunReceipt(
            module_id=plan.module_id,
            pipeline_id=plan.pipeline_id,
            lane=plan.lane,
            status="succeeded",
            started_at_utc=run_started_at,
            finished_at_utc=utc_now_iso(),
            steps=tuple(step_receipts),
        )
        await self._notify_run_finished(observer=observer, receipt=run_receipt)
        return run_receipt

    async def _run_step(
        self,
        *,
        plan: MaterializationPlan,
        step: MaterializationStep,
        runner: MaterializationStepRunner,
        observer: MaterializationExecutionObserver | None,
    ) -> MaterializationStepReceipt:
        step_started_at = utc_now_iso()
        await self._notify_step_started(
            observer=observer,
            plan=plan,
            step=step,
            started_at_utc=step_started_at,
        )
        try:
            result = await runner(plan=plan, step=step)
            self._validate_commit_evidence(step=step, result=result)
            receipt = MaterializationStepReceipt(
                step_id=step.step_id,
                step_kind=step.step_kind,
                status="succeeded",
                commit_requested=step.commit_requested,
                commit_id=result.commit_id,
                head_commit_id=result.head_commit_id,
                started_at_utc=step_started_at,
                finished_at_utc=utc_now_iso(),
                details=dict(result.details),
                error=None,
            )
            await self._notify_step_finished(
                observer=observer,
                plan=plan,
                receipt=receipt,
            )
            return receipt
        except Exception as exc:
            receipt = MaterializationStepReceipt(
                step_id=step.step_id,
                step_kind=step.step_kind,
                status="failed",
                commit_requested=step.commit_requested,
                commit_id=None,
                head_commit_id=None,
                started_at_utc=step_started_at,
                finished_at_utc=utc_now_iso(),
                details={},
                error=str(exc),
            )
            await self._notify_step_finished(
                observer=observer,
                plan=plan,
                receipt=receipt,
            )
            return receipt

    def _validate_commit_evidence(
        self,
        *,
        step: MaterializationStep,
        result: MaterializationStepResult,
    ) -> None:
        if not step.commit_requested:
            return
        if result.commit_id is not None or result.head_commit_id is not None:
            return
        raise ValueError(
            "materialization step missing commit/head evidence for "
            "commit-requested step: "
            + f"step_id={step.step_id!r}"
        )

    async def _notify_run_started(
        self,
        *,
        observer: MaterializationExecutionObserver | None,
        plan: MaterializationPlan,
        started_at_utc: str,
    ) -> None:
        if observer is None:
            return
        try:
            await observer.on_run_started(plan=plan, started_at_utc=started_at_utc)
        except Exception:
            return

    async def _notify_step_started(
        self,
        *,
        observer: MaterializationExecutionObserver | None,
        plan: MaterializationPlan,
        step: MaterializationStep,
        started_at_utc: str,
    ) -> None:
        if observer is None:
            return
        try:
            await observer.on_step_started(
                plan=plan,
                step=step,
                started_at_utc=started_at_utc,
            )
        except Exception:
            return

    async def _notify_step_finished(
        self,
        *,
        observer: MaterializationExecutionObserver | None,
        plan: MaterializationPlan,
        receipt: MaterializationStepReceipt,
    ) -> None:
        if observer is None:
            return
        try:
            await observer.on_step_finished(plan=plan, receipt=receipt)
        except Exception:
            return

    async def _notify_run_finished(
        self,
        *,
        observer: MaterializationExecutionObserver | None,
        receipt: MaterializationRunReceipt,
    ) -> None:
        if observer is None:
            return
        try:
            await observer.on_run_finished(receipt=receipt)
        except Exception:
            return


__all__ = [
    "MaterializationExecutionError",
    "MaterializationExecutor",
]
