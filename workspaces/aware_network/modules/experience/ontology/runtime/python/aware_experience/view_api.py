from __future__ import annotations

import re

from pathlib import Path

from aware_api_runtime.ir import (
    APICompilePlan,
    APICompilePlanArtifact,
    emit_api_compile_plan_artifact,
)
from aware_api_runtime.ontology_graph.ontology import build_api_ontology_plans
from aware_api_runtime.models import (
    APICapabilityEndpointOwnership,
    APICapabilityEndpointRequestConfigOwnership,
    APICapabilityEndpointResponseConfigOwnership,
    APICapabilityOwnership,
    APIOwnership,
    APIViewCapabilityEndpointOwnership,
    APIViewOwnership,
    APIViewStreamPolicyOwnership,
)
from aware_experience.compiler.models import (
    ExperienceCompilePlan,
    ExperienceProjectionExperienceOwnership,
    ExperienceViewApiOwnership,
    ExperienceViewApiViewOwnership,
    ExperienceViewStateModelContract,
)

_DEFAULT_VIEW_STREAM_MODE = "snapshot"
_VIEW_ACTION_CAPABILITY_NAME = "view_action"
_VIEW_ACTION_REQUEST_MODEL_REF = (
    "aware_experience.invocation.ExperienceViewInvocationActionRequest"
)
_VIEW_ACTION_RESPONSE_MODEL_REF = (
    "aware_experience.invocation.ExperienceViewInvocationActionResponse"
)


def build_experience_view_api_ownership(
    *,
    package_name: str,
    fqn_prefix: str,
    projection_experience_ownership: tuple[
        ExperienceProjectionExperienceOwnership, ...
    ],
    view_state_model_contracts: tuple[ExperienceViewStateModelContract, ...] = (),
) -> ExperienceViewApiOwnership | None:
    normalized_fqn_prefix = _identifier_token(fqn_prefix)
    if not normalized_fqn_prefix:
        raise ValueError("Experience view API lowering requires non-empty fqn_prefix.")
    _package_token(package_name or normalized_fqn_prefix)
    _ = view_state_model_contracts
    for experience in sorted(
        projection_experience_ownership,
        key=lambda item: (item.name.casefold(), item.source_path),
    ):
        for observable in sorted(
            experience.observables,
            key=lambda item: (item.key.casefold(), item.source_path),
        ):
            for view in sorted(
                observable.views,
                key=lambda item: (item.key.casefold(), item.source_path),
            ):
                if view.api_view_ref is not None:
                    continue
                raise ValueError(
                    "Experience-generated View API is retired; Experience views "
                    "must mount API-owned ApiView contracts "
                    + (
                        f"(experience={experience.name!r}, observable={observable.key!r}, "
                        f"view={view.key!r})"
                    )
                )

    return None


def build_experience_view_api_compile_plan(
    *,
    experience_plan: ExperienceCompilePlan,
) -> APICompilePlan | None:
    view_api = experience_plan.view_api_ownership
    if view_api is None:
        return None
    api_ownership = _api_ownership_from_view_api(view_api=view_api)
    return APICompilePlan(
        schema_version=10,
        package_name=view_api.package_name,
        fqn_prefix=view_api.fqn_prefix,
        source_files=_unique_source_files(view_api=view_api),
        api_ownership=api_ownership,
        api_ontology=build_api_ontology_plans(api_ownership=api_ownership),
        generated_dto_namespace_roots=(),
    )


def emit_experience_view_api_compile_plan_artifact(
    *,
    experience_plan: ExperienceCompilePlan,
    repo_root: Path,
) -> APICompilePlanArtifact | None:
    view_api_plan = build_experience_view_api_compile_plan(
        experience_plan=experience_plan,
    )
    if view_api_plan is None:
        return None
    resolved_repo_root = repo_root.resolve()
    runtime_package_dir = (
        resolved_repo_root / ".aware" / "api" / "runtime" / view_api_plan.package_name
    )
    return emit_api_compile_plan_artifact(
        plan=view_api_plan,
        runtime_package_dir=runtime_package_dir,
        repo_root=resolved_repo_root,
    )


def _api_ownership_from_view_api(
    *,
    view_api: ExperienceViewApiOwnership,
) -> tuple[APIOwnership, ...]:
    return (
        APIOwnership(
            name=view_api.api_name,
            source_path=view_api.source_path,
            capabilities=_api_view_action_capabilities_from_view_api(view_api=view_api),
            graphs=(),
            views=tuple(
                _api_view_from_experience_view(view=view)
                for view in sorted(
                    view_api.views,
                    key=lambda item: (
                        item.view_name.casefold(),
                        item.source_path,
                    ),
                )
            ),
        ),
    )


def _api_view_action_capabilities_from_view_api(
    *,
    view_api: ExperienceViewApiOwnership,
) -> tuple[APICapabilityOwnership, ...]:
    endpoint_by_name: dict[str, APICapabilityEndpointOwnership] = {}
    action_key_by_endpoint_name: dict[str, str] = {}
    for view in sorted(
        view_api.views,
        key=lambda item: (item.view_name.casefold(), item.source_path),
    ):
        for action in sorted(
            view.invocation_actions,
            key=lambda item: (item.key.casefold(), item.source_path),
        ):
            endpoint_name = _view_action_endpoint_name(action_key=action.key)
            existing_action_key = action_key_by_endpoint_name.get(endpoint_name)
            if (
                existing_action_key is not None
                and existing_action_key.casefold() != action.key.casefold()
            ):
                raise ValueError(
                    "Experience-generated view API action endpoint collision: "
                    + f"endpoint_name={endpoint_name!r}, "
                    + f"actions=({existing_action_key!r}, {action.key!r})"
                )
            action_key_by_endpoint_name[endpoint_name] = action.key
            endpoint_by_name.setdefault(
                endpoint_name,
                APICapabilityEndpointOwnership(
                    name=endpoint_name,
                    source_path=action.source_path,
                    request_config=APICapabilityEndpointRequestConfigOwnership(
                        class_ref=_VIEW_ACTION_REQUEST_MODEL_REF,
                        source_path=action.source_path,
                        response_config=APICapabilityEndpointResponseConfigOwnership(
                            class_ref=_VIEW_ACTION_RESPONSE_MODEL_REF,
                            source_path=action.source_path,
                            description=(
                                "Response for Experience view action "
                                + f"{action.key}."
                            ),
                        ),
                    ),
                    description=f"Invoke Experience view action {action.key}.",
                ),
            )
    if not endpoint_by_name:
        return ()
    return (
        APICapabilityOwnership(
            name=_VIEW_ACTION_CAPABILITY_NAME,
            source_path=view_api.source_path,
            endpoints=tuple(
                endpoint_by_name[name]
                for name in sorted(endpoint_by_name, key=str.casefold)
            ),
            description="Experience-generated API endpoints for view actions.",
        ),
    )


def _api_view_from_experience_view(
    *,
    view: ExperienceViewApiViewOwnership,
) -> APIViewOwnership:
    return APIViewOwnership(
        name=view.view_name,
        observable_ref=view.observable_ref,
        state_model_ref=view.state_model_ref,
        state_model_id=view.state_model_id,
        source_path=view.source_path,
        view_ref=view.view_ref,
        view_key=view.projection_view_key,
        stream_policy=APIViewStreamPolicyOwnership(
            stream_mode=_DEFAULT_VIEW_STREAM_MODE,
            source_path=view.source_path,
            description=(
                "Snapshot stream policy for Experience view " f"{view.view_ref}."
            ),
        ),
        capability_endpoints=tuple(
            APIViewCapabilityEndpointOwnership(
                action_key=action.key,
                endpoint_ref=(
                    f"{view.api_name}.{_VIEW_ACTION_CAPABILITY_NAME}."
                    f"{_view_action_endpoint_name(action_key=action.key)}"
                ),
                source_path=action.source_path,
                description=action.label,
            )
            for action in sorted(
                view.invocation_actions,
                key=lambda item: (item.key.casefold(), item.source_path),
            )
        ),
        description=f"Readable API view-state contract for {view.view_ref}.",
    )


def _unique_source_files(
    *,
    view_api: ExperienceViewApiOwnership,
) -> tuple[str, ...]:
    source_files = {view_api.source_path}
    source_files.update(view.source_path for view in view_api.views)
    source_files.update(
        action.source_path
        for view in view_api.views
        for action in view.invocation_actions
    )
    return tuple(sorted(source_files, key=lambda item: item.casefold()))


def _view_name(
    *,
    experience_name: str,
    observable_key: str,
    view_key: str,
) -> str:
    return "_".join(
        token
        for token in (
            _identifier_token(experience_name),
            _identifier_token(observable_key),
            _identifier_token(view_key),
        )
        if token
    )


def _identifier_token(value: str) -> str:
    token = re.sub(r"[^0-9A-Za-z_]+", "_", (value or "").strip())
    token = re.sub(r"_+", "_", token).strip("_").casefold()
    if token and token[0].isdigit():
        token = f"v_{token}"
    return token


def _view_action_endpoint_name(*, action_key: str) -> str:
    endpoint_name = _identifier_token(action_key)
    if not endpoint_name:
        raise ValueError(
            "Experience-generated view API action endpoint requires non-empty action key."
        )
    return endpoint_name


def _package_token(value: str) -> str:
    token = re.sub(r"[^0-9A-Za-z_-]+", "-", (value or "").strip())
    token = re.sub(r"-+", "-", token).strip("-").casefold()
    return token or "experience"


__all__ = [
    "build_experience_view_api_compile_plan",
    "build_experience_view_api_ownership",
    "emit_experience_view_api_compile_plan_artifact",
]
