from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, Protocol, TypeVar

from aware_experience.environment_profile.api_models import (
    ApplyExperienceEnvironmentProfileProgramsRequest,
    ApplyExperienceEnvironmentProfileProgramsResponse,
    ExperienceEnvironmentProfileProcessSpec,
    ExperienceEnvironmentProfileSpec,
    ExperienceEnvironmentProfileThreadSpec,
    ExperienceEnvironmentProfileTopologySeedSpec,
    ProvisionExperienceEnvironmentProfileRequest,
    ProvisionExperienceEnvironmentProfileResponse,
    UpsertExperienceEnvironmentProfileRequest,
    UpsertExperienceEnvironmentProfileResponse,
)
from aware_experience.environment_profile.reactivity_policy import (
    build_environment_profile_reactivity_policy_summary,
    has_profile_reactivity_events,
)

_T = TypeVar("_T")

_RUNTIME_CUTOVER_ERROR = (
    "Experience environment profile runtime materialization is not enabled for this "
    "service handler. Provide an Experience-owned environment profile runtime backend "
    "or use validate_only=true for contract resolution."
)


class ExperienceEnvironmentProfileRuntimeBackend(Protocol):
    async def upsert_environment_profile(
        self,
        *,
        request: UpsertExperienceEnvironmentProfileRequest,
        host_context: Any | None = None,
    ) -> UpsertExperienceEnvironmentProfileResponse:
        """Commit an Experience-owned profile through the runtime backend."""

    async def provision_environment_profile(
        self,
        *,
        request: ProvisionExperienceEnvironmentProfileRequest,
        host_context: Any | None = None,
    ) -> ProvisionExperienceEnvironmentProfileResponse:
        """Provision runtime topology for a previously committed profile."""

    async def apply_environment_profile_programs(
        self,
        *,
        request: ApplyExperienceEnvironmentProfileProgramsRequest,
        host_context: Any | None = None,
    ) -> ApplyExperienceEnvironmentProfileProgramsResponse:
        """Apply profile-declared programs through the runtime backend."""


class ExperienceEnvironmentProfileReactivityPolicyBackend(Protocol):
    async def ensure_environment_profile_policy_bundle(
        self,
        *,
        request: UpsertExperienceEnvironmentProfileRequest,
        profile_key: str,
        validate_only: bool = False,
        host_context: Any | None = None,
    ) -> dict[str, object]:
        """Ensure Reactivity policy setup for an Experience profile."""


def _required_token(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def _optional_token(value: object, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string or null")
    normalized = value.strip()
    return normalized or None


def _ensure_unique(
    items: Iterable[_T],
    *,
    key_fn: Callable[[_T], str],
    field_name: str,
) -> dict[str, _T]:
    by_key: dict[str, _T] = {}
    for item in items:
        key = key_fn(item)
        if key in by_key:
            raise ValueError(f"{field_name} requires unique key: {key!r}")
        by_key[key] = item
    return by_key


def _profile_evidence(
    *,
    profile: ExperienceEnvironmentProfileSpec,
    topology_seeds: list[ExperienceEnvironmentProfileTopologySeedSpec],
    runtime_mutation: bool,
) -> dict[str, object]:
    has_events = has_profile_reactivity_events(profile=profile)
    return {
        "owner": "experience",
        "runtime_mutation": runtime_mutation,
        "profile_event_count": len(profile.events or []),
        "profile_program_count": len(profile.programs or []),
        "profile_program_apply_count": len(profile.program_applies or []),
        "process_config_count": len(profile.process_configs or []),
        "topology_seed_keys": [seed.key for seed in topology_seeds],
        "reactivity_policy_setup": "planned" if has_events else "not_declared",
        **build_environment_profile_reactivity_policy_summary(profile=profile),
    }


def _with_evidence(
    response: UpsertExperienceEnvironmentProfileResponse,
    values: dict[str, object],
) -> UpsertExperienceEnvironmentProfileResponse:
    evidence = dict(response.evidence or {})
    evidence.update(values)
    return response.model_copy(update={"evidence": evidence})


def _with_apply_evidence(
    response: ApplyExperienceEnvironmentProfileProgramsResponse,
    values: dict[str, object],
) -> ApplyExperienceEnvironmentProfileProgramsResponse:
    evidence = dict(response.evidence or {})
    evidence.update(values)
    return response.model_copy(update={"evidence": evidence})


def _program_run_boundary_evidence(
    *,
    phase: str,
    runtime_mutation: bool,
) -> dict[str, object]:
    return {
        "owner": "experience",
        "topology_owner": "environment",
        "runtime_owner": "experience",
        "program_run_owner": "experience",
        "program_run_boundary": "experience.program_turn_thread_program",
        "environment_program_run_allowed": False,
        "deprecated_runtime_rail": False,
        "runtime_mutation": runtime_mutation,
        "phase": phase,
    }


def _validate_thread_config(
    *,
    thread: ExperienceEnvironmentProfileThreadSpec,
    field_name: str,
) -> None:
    _required_token(thread.key, field_name=f"{field_name}.key")
    _ensure_unique(
        thread.projection_identities or [],
        key_fn=lambda item: _required_token(
            item.projection_identity_key,
            field_name=f"{field_name}.projection_identities[].projection_identity_key",
        ),
        field_name=f"{field_name}.projection_identities[]",
    )
    layout_keys = [
        _required_token(
            item.layout_key,
            field_name=f"{field_name}.layout_configs[].layout_key",
        )
        for item in (thread.layout_configs or [])
    ]
    if len(layout_keys) != len(set(layout_keys)):
        raise ValueError(f"{field_name}.layout_configs[] requires unique layout_key")


def _validate_process_config(
    *,
    process: ExperienceEnvironmentProfileProcessSpec,
    field_name: str,
) -> dict[str, ExperienceEnvironmentProfileThreadSpec]:
    _required_token(process.key, field_name=f"{field_name}.key")
    _required_token(process.type, field_name=f"{field_name}.type")
    threads_by_key = _ensure_unique(
        process.thread_configs or [],
        key_fn=lambda item: _required_token(
            item.key,
            field_name=f"{field_name}.thread_configs[].key",
        ),
        field_name=f"{field_name}.thread_configs[]",
    )
    for thread_index, thread in enumerate(process.thread_configs or []):
        _validate_thread_config(
            thread=thread,
            field_name=f"{field_name}.thread_configs[{thread_index}]",
        )
    return threads_by_key


def _validate_profile(
    *,
    profile: ExperienceEnvironmentProfileSpec,
) -> tuple[str, dict[str, ExperienceEnvironmentProfileProcessSpec]]:
    profile_key = _required_token(profile.key, field_name="profile.key")
    roles_by_name = _ensure_unique(
        profile.roles or [],
        key_fn=lambda item: _required_token(
            item.name,
            field_name="profile.roles[].name",
        ),
        field_name="profile.roles[]",
    )
    _ensure_unique(
        profile.actors or [],
        key_fn=lambda item: _required_token(
            item.key,
            field_name="profile.actors[].key",
        ),
        field_name="profile.actors[]",
    )
    for actor_index, actor in enumerate(profile.actors or []):
        for role_index, role_name_raw in enumerate(actor.role_names or []):
            role_name = _required_token(
                role_name_raw,
                field_name=f"profile.actors[{actor_index}].role_names[{role_index}]",
            )
            if role_name not in roles_by_name:
                raise ValueError(
                    "profile.actors[].role_names[] must reference profile.roles[].name: "
                    f"{role_name!r}"
                )

    programs_by_ref = _ensure_unique(
        profile.programs or [],
        key_fn=lambda item: _required_token(
            item.program_ref,
            field_name="profile.programs[].program_ref",
        ),
        field_name="profile.programs[]",
    )
    _ensure_unique(
        profile.program_applies or [],
        key_fn=lambda item: _required_token(
            item.key,
            field_name="profile.program_applies[].key",
        ),
        field_name="profile.program_applies[]",
    )
    for apply_index, apply_spec in enumerate(profile.program_applies or []):
        program_ref = _required_token(
            apply_spec.program_ref,
            field_name=f"profile.program_applies[{apply_index}].program_ref",
        )
        if program_ref not in programs_by_ref:
            raise ValueError(
                "profile.program_applies[].program_ref must reference "
                f"profile.programs[].program_ref: {program_ref!r}"
            )

    _ensure_unique(
        profile.events or [],
        key_fn=lambda item: _required_token(
            item.event_config_ref,
            field_name="profile.events[].event_config_ref",
        ),
        field_name="profile.events[]",
    )
    for event_index, event in enumerate(profile.events or []):
        for action_index, action in enumerate(event.actions or []):
            action_ref = _optional_token(
                action.action_experience_ref,
                field_name=(
                    f"profile.events[{event_index}].actions[{action_index}]."
                    "action_experience_ref"
                ),
            )
            action_config_ref = _optional_token(
                action.action_config_ref,
                field_name=(
                    f"profile.events[{event_index}].actions[{action_index}]."
                    "action_config_ref"
                ),
            )
            program_ref = _optional_token(
                action.program_ref,
                field_name=(
                    f"profile.events[{event_index}].actions[{action_index}]."
                    "program_ref"
                ),
            )
            if action_ref is None and action_config_ref is None and program_ref is None:
                raise ValueError(
                    "profile.events[].actions[] requires action_experience_ref, "
                    "action_config_ref, or program_ref"
                )
            if program_ref is not None and program_ref not in programs_by_ref:
                raise ValueError(
                    "profile.events[].actions[].program_ref must reference "
                    f"profile.programs[].program_ref: {program_ref!r}"
                )

    process_by_key = _ensure_unique(
        profile.process_configs or [],
        key_fn=lambda item: _required_token(
            item.key,
            field_name="profile.process_configs[].key",
        ),
        field_name="profile.process_configs[]",
    )
    for process_index, process in enumerate(profile.process_configs or []):
        _validate_process_config(
            process=process,
            field_name=f"profile.process_configs[{process_index}]",
        )
    return profile_key, process_by_key


def _validate_topology_seeds(
    *,
    profile: ExperienceEnvironmentProfileSpec,
    process_by_key: dict[str, ExperienceEnvironmentProfileProcessSpec],
    topology_seeds: list[ExperienceEnvironmentProfileTopologySeedSpec],
) -> None:
    _ = profile
    _ensure_unique(
        topology_seeds,
        key_fn=lambda item: _required_token(
            item.key,
            field_name="topology_seeds[].key",
        ),
        field_name="topology_seeds[]",
    )
    thread_configs_by_process_key: dict[
        str, dict[str, ExperienceEnvironmentProfileThreadSpec]
    ] = {}
    for process_key, process in process_by_key.items():
        thread_configs_by_process_key[process_key] = _ensure_unique(
            process.thread_configs or [],
            key_fn=lambda item: _required_token(
                item.key,
                field_name=f"profile.process_configs[{process_key}].thread_configs[].key",
            ),
            field_name=f"profile.process_configs[{process_key}].thread_configs[]",
        )

    for seed_index, seed in enumerate(topology_seeds):
        for process_seed_index, process_seed in enumerate(seed.process_seeds or []):
            process_config_key = _required_token(
                process_seed.process_config_key,
                field_name=(
                    f"topology_seeds[{seed_index}].process_seeds"
                    f"[{process_seed_index}].process_config_key"
                ),
            )
            process = process_by_key.get(process_config_key)
            if process is None:
                raise ValueError(
                    "topology_seeds[].process_seeds[].process_config_key must "
                    f"reference profile.process_configs[].key: {process_config_key!r}"
                )
            _required_token(
                process_seed.process_key,
                field_name=(
                    f"topology_seeds[{seed_index}].process_seeds"
                    f"[{process_seed_index}].process_key"
                ),
            )
            threads_by_key = thread_configs_by_process_key[process_config_key]
            for thread_seed_index, thread_seed in enumerate(
                process_seed.thread_seeds or []
            ):
                thread_config_key = _required_token(
                    thread_seed.thread_config_key,
                    field_name=(
                        f"topology_seeds[{seed_index}].process_seeds"
                        f"[{process_seed_index}].thread_seeds"
                        f"[{thread_seed_index}].thread_config_key"
                    ),
                )
                thread = threads_by_key.get(thread_config_key)
                if thread is None:
                    raise ValueError(
                        "topology_seeds[].process_seeds[].thread_seeds[]."
                        "thread_config_key must reference the selected "
                        f"process thread config: {thread_config_key!r}"
                    )
                _required_token(
                    thread_seed.thread_key,
                    field_name=(
                        f"topology_seeds[{seed_index}].process_seeds"
                        f"[{process_seed_index}].thread_seeds"
                        f"[{thread_seed_index}].thread_key"
                    ),
                )
                layout_keys = {
                    _required_token(
                        layout.layout_key,
                        field_name=(
                            f"profile.process_configs[{process.key}]."
                            f"thread_configs[{thread.key}].layout_configs[].layout_key"
                        ),
                    )
                    for layout in (thread.layout_configs or [])
                }
                for layout_seed_index, layout_seed in enumerate(
                    thread_seed.layout_seeds or []
                ):
                    layout_key = _required_token(
                        layout_seed.layout_key,
                        field_name=(
                            f"topology_seeds[{seed_index}].process_seeds"
                            f"[{process_seed_index}].thread_seeds"
                            f"[{thread_seed_index}].layout_seeds"
                            f"[{layout_seed_index}].layout_key"
                        ),
                    )
                    if layout_key not in layout_keys:
                        raise ValueError(
                            "topology_seeds[].process_seeds[].thread_seeds[]."
                            "layout_seeds[].layout_key must reference the selected "
                            f"thread layout config: {layout_key!r}"
                        )


async def upsert_experience_environment_profile(
    *,
    request: UpsertExperienceEnvironmentProfileRequest,
    host_context: Any | None = None,
    runtime_backend: ExperienceEnvironmentProfileRuntimeBackend | None = None,
    reactivity_policy_backend: ExperienceEnvironmentProfileReactivityPolicyBackend
    | None = None,
) -> UpsertExperienceEnvironmentProfileResponse:
    profile_key, process_by_key = _validate_profile(profile=request.profile)
    _validate_topology_seeds(
        profile=request.profile,
        process_by_key=process_by_key,
        topology_seeds=request.topology_seeds or [],
    )
    if not request.validate_only:
        if runtime_backend is not None:
            reactivity_evidence: dict[str, object] | None = None
            if has_profile_reactivity_events(profile=request.profile):
                if reactivity_policy_backend is None:
                    return UpsertExperienceEnvironmentProfileResponse(
                        request_id=request.request_id,
                        success=False,
                        status="reactivity_not_configured",
                        error=(
                            "Experience environment profile declares events, but "
                            "no Reactivity policy backend is configured."
                        ),
                        environment_id=request.environment_id,
                        process_id=request.process_id,
                        thread_id=request.thread_id,
                        branch_id=request.branch_id,
                        projection_hash=request.projection_hash,
                        experience_name=request.experience_name,
                        profile_key=profile_key,
                        evidence={
                            **_profile_evidence(
                                profile=request.profile,
                                topology_seeds=request.topology_seeds or [],
                                runtime_mutation=False,
                            ),
                            "reactivity_policy_setup": "missing_backend",
                        },
                    )
                try:
                    reactivity_evidence = (
                        await reactivity_policy_backend.ensure_environment_profile_policy_bundle(
                            request=request,
                            profile_key=profile_key,
                            validate_only=False,
                            host_context=host_context,
                        )
                    )
                except Exception as exc:
                    return UpsertExperienceEnvironmentProfileResponse(
                        request_id=request.request_id,
                        success=False,
                        status="reactivity_failed",
                        error=f"Experience Reactivity policy provisioning failed: {exc}",
                        environment_id=request.environment_id,
                        process_id=request.process_id,
                        thread_id=request.thread_id,
                        branch_id=request.branch_id,
                        projection_hash=request.projection_hash,
                        experience_name=request.experience_name,
                        profile_key=profile_key,
                        evidence={
                            **_profile_evidence(
                                profile=request.profile,
                                topology_seeds=request.topology_seeds or [],
                                runtime_mutation=False,
                            ),
                            "reactivity_policy_setup": "failed",
                        },
                    )
            response = await runtime_backend.upsert_environment_profile(
                request=request,
                host_context=host_context,
            )
            profile_evidence = _profile_evidence(
                profile=request.profile,
                topology_seeds=request.topology_seeds or [],
                runtime_mutation=True,
            )
            if reactivity_evidence is not None:
                return _with_evidence(
                    response,
                    {
                        **profile_evidence,
                        "reactivity_policy_setup": "ensured",
                        "reactivity_policy": reactivity_evidence,
                    },
                )
            return _with_evidence(
                response,
                {
                    **profile_evidence,
                    "reactivity_policy_setup": "not_declared",
                },
            )
        return UpsertExperienceEnvironmentProfileResponse(
            request_id=request.request_id,
            success=False,
            status="not_enabled",
            error=_RUNTIME_CUTOVER_ERROR,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            experience_name=request.experience_name,
            profile_key=profile_key,
            evidence=_profile_evidence(
                profile=request.profile,
                topology_seeds=request.topology_seeds or [],
                runtime_mutation=False,
            ),
        )
    return UpsertExperienceEnvironmentProfileResponse(
        request_id=request.request_id,
        success=True,
        status="planned",
        info="Experience environment profile contract resolved without mutation.",
        environment_id=request.environment_id,
        process_id=request.process_id,
        thread_id=request.thread_id,
        branch_id=request.branch_id,
        projection_hash=request.projection_hash,
        experience_name=request.experience_name,
        profile_key=profile_key,
        evidence=_profile_evidence(
            profile=request.profile,
            topology_seeds=request.topology_seeds or [],
            runtime_mutation=False,
        ),
    )


async def provision_experience_environment_profile(
    *,
    request: ProvisionExperienceEnvironmentProfileRequest,
    host_context: Any | None = None,
    runtime_backend: ExperienceEnvironmentProfileRuntimeBackend | None = None,
) -> ProvisionExperienceEnvironmentProfileResponse:
    topology_seed_key = _required_token(
        request.topology_seed_key,
        field_name="topology_seed_key",
    )
    profile_key = _optional_token(request.profile_key, field_name="profile_key")
    if not request.validate_only:
        if runtime_backend is not None:
            return await runtime_backend.provision_environment_profile(
                request=request,
                host_context=host_context,
            )
        return ProvisionExperienceEnvironmentProfileResponse(
            request_id=request.request_id,
            success=False,
            status="not_enabled",
            error=_RUNTIME_CUTOVER_ERROR,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            experience_name=request.experience_name,
            environment_experience_profile_id=request.environment_experience_profile_id,
            profile_key=profile_key,
            evidence={
                "owner": "experience",
                "runtime_mutation": False,
                "topology_seed_key": topology_seed_key,
            },
        )
    return ProvisionExperienceEnvironmentProfileResponse(
        request_id=request.request_id,
        success=True,
        status="planned",
        info="Experience environment profile provisioning resolved without mutation.",
        environment_id=request.environment_id,
        process_id=request.process_id,
        thread_id=request.thread_id,
        branch_id=request.branch_id,
        projection_hash=request.projection_hash,
        experience_name=request.experience_name,
        environment_experience_profile_id=request.environment_experience_profile_id,
        profile_key=profile_key,
        evidence={
            "owner": "experience",
            "runtime_mutation": False,
            "topology_seed_key": topology_seed_key,
        },
    )


async def apply_experience_environment_profile_programs(
    *,
    request: ApplyExperienceEnvironmentProfileProgramsRequest,
    host_context: Any | None = None,
    runtime_backend: ExperienceEnvironmentProfileRuntimeBackend | None = None,
) -> ApplyExperienceEnvironmentProfileProgramsResponse:
    phase = _required_token(request.phase, field_name="phase")
    profile_key = _optional_token(request.profile_key, field_name="profile_key")
    if not request.validate_only:
        if runtime_backend is not None:
            response = await runtime_backend.apply_environment_profile_programs(
                request=request,
                host_context=host_context,
            )
            return _with_apply_evidence(
                response,
                _program_run_boundary_evidence(
                    phase=phase,
                    runtime_mutation=True,
                ),
            )
        return ApplyExperienceEnvironmentProfileProgramsResponse(
            request_id=request.request_id,
            success=False,
            status="not_enabled",
            error=_RUNTIME_CUTOVER_ERROR,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            experience_name=request.experience_name,
            environment_experience_profile_id=request.environment_experience_profile_id,
            profile_key=profile_key,
            phase=phase,
            target_actor_id=request.target_actor_id,
            evidence=_program_run_boundary_evidence(
                phase=phase,
                runtime_mutation=False,
            ),
        )
    return ApplyExperienceEnvironmentProfileProgramsResponse(
        request_id=request.request_id,
        success=True,
        status="planned",
        info=(
            "Experience-owned Program/Turn run boundary resolved without "
            "mutation."
        ),
        environment_id=request.environment_id,
        process_id=request.process_id,
        thread_id=request.thread_id,
        branch_id=request.branch_id,
        projection_hash=request.projection_hash,
        experience_name=request.experience_name,
        environment_experience_profile_id=request.environment_experience_profile_id,
        profile_key=profile_key,
        phase=phase,
        target_actor_id=request.target_actor_id,
        evidence=_program_run_boundary_evidence(
            phase=phase,
            runtime_mutation=False,
        ),
    )


__all__ = [
    "ExperienceEnvironmentProfileReactivityPolicyBackend",
    "ExperienceEnvironmentProfileRuntimeBackend",
    "apply_experience_environment_profile_programs",
    "provision_experience_environment_profile",
    "upsert_experience_environment_profile",
]
