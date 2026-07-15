from __future__ import annotations

from aware_interface import (
    InterfaceHostCapabilityAction,
    InterfaceHostCapabilityConsumer,
    InterfaceHostCapabilityOperation,
    InterfaceHostCapabilityScreen,
    InterfaceHostCapabilitySnapshot,
    InterfaceHostCapabilityTarget,
    InterfaceHostCapabilityTraceEntry,
)


class _FakeCapabilityConsumer:
    def __init__(self, snapshot: InterfaceHostCapabilitySnapshot) -> None:
        self._snapshot = snapshot

    def build_snapshot(self) -> InterfaceHostCapabilitySnapshot:
        return self._snapshot


def test_interface_host_capability_snapshot_exports_capability_contract() -> None:
    snapshot = InterfaceHostCapabilitySnapshot(
        capability_id="workspace",
        kind="workspace",
        screen=InterfaceHostCapabilityScreen(
            screen_key="workspace_start_gate",
            source_kind="workspace",
            title="Start Workspace",
            message="Workspace runtime is available to start.",
        ),
        actions=(
            InterfaceHostCapabilityAction(
                action_key="ensure_selected_workspace_running",
                label="Start Workspace",
            ),
        ),
        operation=InterfaceHostCapabilityOperation(
            capability_id="workspace",
            title="Workspace Lifecycle",
            status="available",
            current_target_id="workspace_session",
            current_target_title="Workspace Session",
            targets=(
                InterfaceHostCapabilityTarget(
                    target_id="workspace_session",
                    display_name="Workspace Session",
                    status="available",
                    is_active=False,
                    is_healthy=False,
                    trace_preview=(
                        InterfaceHostCapabilityTraceEntry(
                            source_key="workspace",
                            source_label="Workspace",
                            message="Workspace runtime is available to start.",
                        ),
                    ),
                ),
            ),
        ),
    )

    consumer: InterfaceHostCapabilityConsumer = _FakeCapabilityConsumer(snapshot)

    resolved = consumer.build_snapshot()
    assert resolved.capability_id == "workspace"
    assert resolved.screen is not None
    assert resolved.screen.screen_key == "workspace_start_gate"
    assert resolved.actions[0].action_key == "ensure_selected_workspace_running"
    assert resolved.operation is not None
    assert resolved.operation.targets[0].trace_preview[0].message == (
        "Workspace runtime is available to start."
    )
