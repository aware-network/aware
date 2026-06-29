from __future__ import annotations

from uuid import UUID

from aware_meta.graph.instance.commit.fs_store import (
    FSCommitStore,
    LaneHeadCommitReceipt,
)
from aware_meta.receipts.lane_commit_receipt_bus import LaneCommitReceiptBus
from aware_meta.receipts.notifications import (
    InvokeFunctionCallTarget,
    LaneCommitReceiptNotification,
)


class LaneHeadReceiptRelay:
    """Relay commit-store lane-head receipts onto the Meta lane commit bus."""

    def __init__(self) -> None:
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        FSCommitStore.register_lane_head_watcher(self._on_lane_head_receipt)
        self._started = True

    def stop(self) -> None:
        if not self._started:
            return
        FSCommitStore.unregister_lane_head_watcher(self._on_lane_head_receipt)
        self._started = False

    def _on_lane_head_receipt(self, receipt: LaneHeadCommitReceipt) -> None:
        call_target: InvokeFunctionCallTarget | None = None
        operation_label: str | None = None
        function_id: UUID | None = None
        object_id: UUID | None = None
        class_instance_identity_id: UUID | None = None
        if receipt.commit_action is not None:
            operation_label = receipt.commit_action.operation_label
            function_id = receipt.commit_action.function_id
            object_id = receipt.commit_action.object_id
            class_instance_identity_id = (
                receipt.commit_action.class_instance_identity_id
            )
            raw_call_target = (receipt.commit_action.call_target or "").strip()
            if raw_call_target:
                try:
                    call_target = InvokeFunctionCallTarget(raw_call_target)
                except Exception:
                    call_target = None

        payload = LaneCommitReceiptNotification(
            actor_id=receipt.author_id,
            branch_id=receipt.branch_id,
            projection_hash=receipt.projection_hash,
            commit_id=receipt.commit_id,
            object_instance_graph_commit_id=receipt.object_instance_graph_commit_id,
            object_projection_graph_id=receipt.object_projection_graph_id,
            object_projection_graph_identity_id=receipt.object_projection_graph_identity_id,
            object_instance_graph_id=receipt.object_instance_graph_id,
            object_instance_graph_identity_id=receipt.object_instance_graph_identity_id,
            object_instance_graph_branch_id=receipt.object_instance_graph_branch_id,
            created_at_unix_ms=receipt.created_at_unix_ms,
            operation_label=operation_label,
            call_target=call_target,
            function_id=function_id,
            object_id=object_id,
            class_instance_identity_id=(
                class_instance_identity_id or receipt.class_instance_identity_id
            ),
            graph_hash_post=receipt.graph_hash_post,
            root_object_id=receipt.root_object_id,
            head_version=receipt.head_version,
        )
        LaneCommitReceiptBus.instance().dispatch(payload)


__all__ = [
    "LaneHeadReceiptRelay",
]
