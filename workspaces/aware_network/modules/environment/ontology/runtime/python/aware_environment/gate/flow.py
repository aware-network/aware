from __future__ import annotations

from dataclasses import dataclass


_STATUS_ACTIVE = "active"
_STATUS_CROSSED = "crossed"
_STATUS_LOCKED = "locked"
_DESTINATION_IDENTITY = "identityGate"
_DESTINATION_NETWORK = "networkGate"
_DESTINATION_STUDIO = "studio"
_STEP_BOOT = "space"


@dataclass(frozen=True, slots=True)
class EnvironmentGateStepSnapshot:
    key: str
    title: str
    crossed: bool
    description: str | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentGateStep:
    key: str
    status: str
    title: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentGateFlowState:
    destination_key: str
    active_step_key: str | None
    blocked: bool
    steps: tuple[EnvironmentGateStep, ...]
    reason: str | None = None

    @property
    def can_enter_studio(self) -> bool:
        return self.destination_key == _DESTINATION_STUDIO


def compose_environment_gate_flow(
    *,
    network_step: EnvironmentGateStepSnapshot,
    identity_step: EnvironmentGateStepSnapshot,
    boot_crossed: bool,
    boot_title: str = "Boot",
    boot_locked_description: str | None = None,
    boot_crossed_description: str | None = None,
) -> EnvironmentGateFlowState:
    """Compose the canonical v0 gate flow over module-owned step snapshots.

    v0 keeps a guided ladder:
    - network -> identity -> studio
    - boot remains environment-owned readiness and does not become its own destination
    """

    if not network_step.crossed:
        return EnvironmentGateFlowState(
            destination_key=_DESTINATION_NETWORK,
            active_step_key=network_step.key,
            blocked=True,
            reason=network_step.description,
            steps=(
                EnvironmentGateStep(
                    key=network_step.key,
                    status=_STATUS_ACTIVE,
                    title=network_step.title,
                    description=network_step.description,
                ),
                EnvironmentGateStep(
                    key=identity_step.key,
                    status=_STATUS_LOCKED,
                    title=identity_step.title,
                    description=identity_step.description,
                ),
                EnvironmentGateStep(
                    key=_STEP_BOOT,
                    status=_STATUS_LOCKED,
                    title=boot_title,
                    description=boot_locked_description,
                ),
            ),
        )

    if not identity_step.crossed or not boot_crossed:
        return EnvironmentGateFlowState(
            destination_key=_DESTINATION_IDENTITY,
            active_step_key=identity_step.key,
            blocked=True,
            reason=(
                identity_step.description
                if not identity_step.crossed
                else boot_locked_description
            ),
            steps=(
                EnvironmentGateStep(
                    key=network_step.key,
                    status=_STATUS_CROSSED,
                    title=network_step.title,
                    description=network_step.description,
                ),
                EnvironmentGateStep(
                    key=identity_step.key,
                    status=_STATUS_ACTIVE,
                    title=identity_step.title,
                    description=identity_step.description,
                ),
                EnvironmentGateStep(
                    key=_STEP_BOOT,
                    status=_STATUS_LOCKED,
                    title=boot_title,
                    description=boot_locked_description,
                ),
            ),
        )

    return EnvironmentGateFlowState(
        destination_key=_DESTINATION_STUDIO,
        active_step_key=None,
        blocked=False,
        steps=(
            EnvironmentGateStep(
                key=network_step.key,
                status=_STATUS_CROSSED,
                title=network_step.title,
                description=network_step.description,
            ),
            EnvironmentGateStep(
                key=identity_step.key,
                status=_STATUS_CROSSED,
                title=identity_step.title,
                description=identity_step.description,
            ),
            EnvironmentGateStep(
                key=_STEP_BOOT,
                status=_STATUS_CROSSED,
                title=boot_title,
                description=boot_crossed_description,
            ),
        ),
        reason=boot_crossed_description,
    )


__all__ = [
    "EnvironmentGateFlowState",
    "EnvironmentGateStep",
    "EnvironmentGateStepSnapshot",
    "compose_environment_gate_flow",
]
