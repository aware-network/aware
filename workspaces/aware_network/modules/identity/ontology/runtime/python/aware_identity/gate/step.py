from __future__ import annotations

from uuid import UUID

from aware_environment.gate import EnvironmentGateStepSnapshot


def build_identity_gate_step(
    *,
    expected_actor_id: UUID | None,
    auth_session_available: bool,
    auth_actor_id: UUID | None,
) -> EnvironmentGateStepSnapshot:
    if auth_session_available and auth_actor_id is not None:
        if expected_actor_id is None or auth_actor_id == expected_actor_id:
            return EnvironmentGateStepSnapshot(
                key="identity",
                title="You",
                crossed=True,
                description=f"Authenticated as actor {auth_actor_id}.",
            )
        return EnvironmentGateStepSnapshot(
            key="identity",
            title="You",
            crossed=False,
            description=(
                "Authenticated actor does not match the resolved interface actor. "
                "Refresh the session login before continuing."
            ),
        )

    if expected_actor_id is None:
        description = "Resolve an interface actor before crossing the Identity step."
    else:
        description = f"Authenticate actor {expected_actor_id} to cross the Identity step."

    return EnvironmentGateStepSnapshot(
        key="identity",
        title="You",
        crossed=False,
        description=description,
    )


__all__ = [
    "build_identity_gate_step",
]
