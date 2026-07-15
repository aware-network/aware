from __future__ import annotations

from aware_environment.gate import (
    EnvironmentGateStepSnapshot,
    compose_environment_gate_flow,
)


def test_compose_gate_flow_stops_at_network_until_network_crosses() -> None:
    state = compose_environment_gate_flow(
        network_step=EnvironmentGateStepSnapshot(
            key="network",
            title="Network",
            crossed=False,
            description="Authenticate against the selected node.",
        ),
        identity_step=EnvironmentGateStepSnapshot(
            key="identity",
            title="You",
            crossed=False,
            description="Authenticate the resolved actor.",
        ),
        boot_crossed=False,
        boot_locked_description="Boot is not ready.",
    )

    assert state.destination_key == "networkGate"
    assert state.active_step_key == "network"
    assert state.blocked is True
    assert tuple(step.status for step in state.steps) == ("active", "locked", "locked")


def test_compose_gate_flow_keeps_identity_active_until_boot_crosses() -> None:
    state = compose_environment_gate_flow(
        network_step=EnvironmentGateStepSnapshot(
            key="network",
            title="Network",
            crossed=True,
            description="Remote transport is authenticated.",
        ),
        identity_step=EnvironmentGateStepSnapshot(
            key="identity",
            title="You",
            crossed=True,
            description="Actor authentication is ready.",
        ),
        boot_crossed=False,
        boot_locked_description="Boot interface graph is not ready yet.",
    )

    assert state.destination_key == "identityGate"
    assert state.active_step_key == "identity"
    assert state.blocked is True
    assert state.reason == "Boot interface graph is not ready yet."
    assert tuple(step.status for step in state.steps) == ("crossed", "active", "locked")


def test_compose_gate_flow_enters_studio_when_all_steps_are_crossed() -> None:
    state = compose_environment_gate_flow(
        network_step=EnvironmentGateStepSnapshot(
            key="network",
            title="Network",
            crossed=True,
            description="Remote transport is authenticated.",
        ),
        identity_step=EnvironmentGateStepSnapshot(
            key="identity",
            title="You",
            crossed=True,
            description="Actor authentication is ready.",
        ),
        boot_crossed=True,
        boot_crossed_description="Boot is ready.",
    )

    assert state.destination_key == "studio"
    assert state.can_enter_studio is True
    assert state.blocked is False
    assert tuple(step.status for step in state.steps) == (
        "crossed",
        "crossed",
        "crossed",
    )
