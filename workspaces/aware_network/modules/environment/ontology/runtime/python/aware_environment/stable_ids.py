from __future__ import annotations

"""Compatibility stable-id helpers for the Environment module (Python runtime).

Canonical stable-id formulas are compiler-owned and generated from:
- `workspaces/aware_network/modules/environment/ontology/structure/stable_ids.toml`

Generated module:
- `aware_environment_ontology.stable_ids`

Policy:
- Do not add new stable-id formulas here.
- Add/update the SSOT spec and recompile, then (optionally) re-export here for compatibility.
"""

from uuid import NAMESPACE_URL, UUID, uuid5

try:
    from aware_environment_ontology import stable_ids as _generated_stable_ids
except ModuleNotFoundError:
    _generated_stable_ids = None


def _generated(name: str):
    if _generated_stable_ids is None:
        return None
    return getattr(_generated_stable_ids, name, None)


def _require_generated(name: str):
    generated = _generated(name)
    if generated is None:
        raise RuntimeError(
            "Compiler-owned stable id function is unavailable; "
            f"recompile environment and refresh runtime artifacts: {name}"
        )
    return generated


NS_ENVIRONMENT_COMPAT = uuid5(NAMESPACE_URL, "aware://environment/v1")


def _norm(value: str | None) -> str:
    return (value or "").casefold().strip()


def stable_environment_profile_id(
    *,
    environment_id: UUID,
    profile_config_id: UUID | None = None,
    key: str | None = None,
) -> UUID:
    generated = _generated("stable_environment_profile_id")
    if generated is not None and profile_config_id is not None:
        return generated(
            environment_id=environment_id,
            profile_config_id=profile_config_id,
        )
    if key is not None:
        return uuid5(
            NS_ENVIRONMENT_COMPAT,
            f"aware:environment_profile:{environment_id}:{_norm(key)}",
        )
    raise TypeError("stable_environment_profile_id requires profile_config_id")


def stable_environment_profile_config_id(
    *,
    environment_config_id: UUID,
    key: str,
) -> UUID:
    generated = _generated("stable_environment_profile_config_id")
    if generated is not None:
        return generated(environment_config_id=environment_config_id, key=key)
    return uuid5(
        NS_ENVIRONMENT_COMPAT,
        f"aware:environment_profile_config:{environment_config_id}:{_norm(key)}",
    )


def stable_process_id(
    *,
    key: str,
    environment_profile_id: UUID | None = None,
    process_config_id: UUID | None = None,
    environment_id: UUID | None = None,
) -> UUID:
    generated = _require_generated("stable_process_id")
    if environment_profile_id is not None and process_config_id is not None:
        return generated(
            environment_profile_id=environment_profile_id,
            process_config_id=process_config_id,
            key=key,
        )
    _ = environment_id
    return uuid5(NS_ENVIRONMENT_COMPAT, f"aware:process:{_norm(key)}")


def stable_thread_id(
    *,
    key: str,
    thread_config_id: UUID | None = None,
    process_id: UUID | None = None,
    environment_id: UUID | None = None,
) -> UUID:
    generated = _require_generated("stable_thread_id")
    if thread_config_id is not None and process_id is not None:
        return generated(
            thread_config_id=thread_config_id, process_id=process_id, key=key
        )
    _ = environment_id
    return uuid5(NS_ENVIRONMENT_COMPAT, f"aware:thread:{_norm(key)}")


def stable_thread_oigb_assoc_id(*, thread_id: UUID, oigb_id: UUID) -> UUID:
    """Stable Thread→OIGB association-edge id (ThreadObjectInstanceGraphBranch)."""
    return uuid5(NAMESPACE_URL, f"aware:thread_oigb_assoc:{thread_id}:{oigb_id}")


def stable_process_config_id(
    *,
    environment_profile_config_id: UUID | None = None,
    environment_profile_id: UUID | None = None,
    key: str | None = None,
    process_id: UUID | None = None,
) -> UUID:
    """Stable EnvironmentProfileConfig→ProcessConfig identity."""
    generated = _generated("stable_process_config_id")
    if (
        generated is not None
        and environment_profile_config_id is not None
        and key is not None
    ):
        return generated(
            environment_profile_config_id=environment_profile_config_id,
            key=key,
        )
    if environment_profile_id is not None and key is not None:
        return uuid5(
            NS_ENVIRONMENT_COMPAT,
            f"aware:process_config:{environment_profile_id}:{_norm(key)}",
        )
    if process_id is not None:
        return uuid5(NAMESPACE_URL, f"aware:process_config:{process_id}")
    raise TypeError(
        "stable_process_config_id requires environment_profile_config_id+key"
    )


def stable_thread_config_id(
    *,
    process_config_id: UUID | None = None,
    key: str | None = None,
    thread_id: UUID | None = None,
) -> UUID:
    """Stable ProcessConfig→ThreadConfig identity."""
    generated = _generated("stable_thread_config_id")
    if generated is not None and process_config_id is not None and key is not None:
        return generated(process_config_id=process_config_id, key=key)
    if thread_id is not None:
        return uuid5(NAMESPACE_URL, f"aware:thread_config:{thread_id}")
    raise TypeError("stable_thread_config_id requires process_config_id+key")


def stable_thread_config_opgi_assoc_id(
    *, thread_config_id: UUID, object_projection_graph_identity_id: UUID
) -> UUID:
    """Stable ThreadConfig→ObjectProjectionGraphIdentity association-edge id."""
    return uuid5(
        NAMESPACE_URL,
        "aware:thread_config_opgi_assoc:"
        f"{thread_config_id}:{object_projection_graph_identity_id}",
    )


def stable_boot_process_id(*, environment_id: UUID) -> UUID:
    environment_profile_id = stable_environment_profile_id(
        environment_id=environment_id,
        key="bootstrap",
    )
    process_config_id = stable_process_config_id(
        environment_profile_id=environment_profile_id,
        key="environment",
    )
    return stable_process_id(
        environment_profile_id=environment_profile_id,
        process_config_id=process_config_id,
        key="environment",
    )


def stable_boot_thread_id(*, environment_id: UUID) -> UUID:
    process_id = stable_boot_process_id(environment_id=environment_id)
    environment_profile_id = stable_environment_profile_id(
        environment_id=environment_id,
        key="bootstrap",
    )
    process_config_id = stable_process_config_id(
        environment_profile_id=environment_profile_id,
        key="environment",
    )
    thread_config_id = stable_thread_config_id(
        process_config_id=process_config_id,
        key="bootstrap",
    )
    return stable_thread_id(
        thread_config_id=thread_config_id,
        process_id=process_id,
        key="bootstrap",
    )


__all__ = [
    "stable_process_id",
    "stable_thread_id",
    "stable_thread_oigb_assoc_id",
    "stable_environment_profile_id",
    "stable_environment_profile_config_id",
    "stable_process_config_id",
    "stable_thread_config_id",
    "stable_thread_config_opgi_assoc_id",
    "stable_boot_process_id",
    "stable_boot_thread_id",
]
