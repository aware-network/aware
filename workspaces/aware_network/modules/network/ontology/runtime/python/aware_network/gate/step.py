from __future__ import annotations

from aware_environment.gate import EnvironmentGateStepSnapshot


def build_community_gate_step(
    *,
    endpoint: str | None,
    auth_session_available: bool,
    authority_snapshot_available: bool,
) -> EnvironmentGateStepSnapshot:
    endpoint_value = (endpoint or "").strip()
    endpoint_label = endpoint_value or "the selected node"

    if auth_session_available or authority_snapshot_available:
        return EnvironmentGateStepSnapshot(
            key="network",
            title="Network",
            crossed=True,
            description=f"Remote session proof is available for {endpoint_label}.",
        )

    if endpoint_value:
        description = f"Authenticate against {endpoint_label} to cross the Network step."
    else:
        description = "Select a node endpoint and authenticate to cross the Network step."

    return EnvironmentGateStepSnapshot(
        key="network",
        title="Network",
        crossed=False,
        description=description,
    )


__all__ = [
    "build_community_gate_step",
]
