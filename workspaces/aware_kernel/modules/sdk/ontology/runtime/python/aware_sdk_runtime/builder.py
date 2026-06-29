from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from aware_sdk_runtime.manifest.spec import (
    AwareSdkDependencyKind,
    AwareSdkTomlDependencySpec,
)

from .compiler import load_sdk_ownership_from_sources
from .models import (
    SdkApiOwnership,
    SdkConfigApiPlan,
    SdkConfigPlan,
    SdkOperationDependencyPlan,
    SdkOperationEndpointPlan,
    SdkOperationOwnership,
    SdkOperationPlan,
    SdkSurfaceMethodPlan,
    SdkSurfaceOwnership,
    SdkSurfacePlan,
    SdkOwnership,
)
from .workspace import SdkWorkspaceSnapshot


@dataclass(frozen=True, slots=True)
class SdkCompilePlan:
    schema_version: int
    package_name: str
    fqn_prefix: str
    source_files: tuple[str, ...]
    sdk_ownership: tuple[SdkOwnership, ...]
    sdk_configs: tuple[SdkConfigPlan, ...]


@dataclass(frozen=True, slots=True)
class SdkCompilePlanArtifact:
    path: Path
    relpath: str
    hash_sha256: str


def build_sdk_compile_plan(*, snapshot: SdkWorkspaceSnapshot) -> SdkCompilePlan:
    source_files = tuple(path.as_posix() for path in snapshot.source_files)
    sdk_dependency_package_names_by_sdk_ref = _sdk_dependency_package_names_by_sdk_ref(
        snapshot.spec.dependencies
    )
    sdk_ownership = load_sdk_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
        sdk_dependency_package_names_by_sdk_ref=sdk_dependency_package_names_by_sdk_ref,
    )
    sdk_configs = tuple(
        _build_sdk_config_plan(
            sdk=sdk,
            sdk_dependency_package_names_by_sdk_ref=(
                sdk_dependency_package_names_by_sdk_ref
            ),
        )
        for sdk in sdk_ownership
    )
    return SdkCompilePlan(
        schema_version=1,
        package_name=(snapshot.spec.sdk.package_name or "").strip(),
        fqn_prefix=(snapshot.spec.sdk.fqn_prefix or "").strip(),
        source_files=source_files,
        sdk_ownership=sdk_ownership,
        sdk_configs=sdk_configs,
    )


def emit_sdk_compile_plan_artifact(
    *,
    plan: SdkCompilePlan,
    runtime_package_dir: Path,
    repo_root: Path,
) -> SdkCompilePlanArtifact:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)

    payload = encode_sdk_compile_plan(plan=plan)
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = sha256(canonical).hexdigest()

    artifact_path = (runtime_package_dir / "sdk.compile_plan.json").resolve()
    _ = artifact_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    relpath = artifact_path.relative_to(repo_root).as_posix()
    return SdkCompilePlanArtifact(
        path=artifact_path,
        relpath=relpath,
        hash_sha256=digest,
    )


def _build_sdk_config_plan(
    *,
    sdk: SdkOwnership,
    sdk_dependency_package_names_by_sdk_ref: dict[str, str],
) -> SdkConfigPlan:
    api_plans = tuple(
        SdkConfigApiPlan(
            api_ref=api.api_ref,
            source_path=api.source_path,
        )
        for api in sdk.apis
    )
    operation_plans = tuple(
        _build_sdk_operation_plan(
            sdk_name=sdk.name,
            operation=operation,
            apis=sdk.apis,
            sdk_dependency_package_names_by_sdk_ref=(
                sdk_dependency_package_names_by_sdk_ref
            ),
        )
        for operation in sdk.operations
    )
    surface_plans = tuple(
        _build_sdk_surface_plan(surface=surface) for surface in sdk.surfaces
    )
    return SdkConfigPlan(
        name=sdk.name,
        source_path=sdk.source_path,
        apis=api_plans,
        operations=operation_plans,
        surfaces=surface_plans,
        description=sdk.description,
    )


def _build_sdk_operation_plan(
    *,
    sdk_name: str,
    operation: SdkOperationOwnership,
    apis: tuple[SdkApiOwnership, ...],
    sdk_dependency_package_names_by_sdk_ref: dict[str, str],
) -> SdkOperationPlan:
    endpoint_plans: list[SdkOperationEndpointPlan] = []
    for order, endpoint in enumerate(operation.endpoints, start=1):
        endpoint_ref = endpoint.endpoint_ref
        api_ref = _resolve_api_ref_for_endpoint(endpoint_ref=endpoint_ref, apis=apis)
        endpoint_plans.append(
            SdkOperationEndpointPlan(
                name=_resolve_endpoint_name(endpoint_ref=endpoint_ref),
                endpoint_ref=endpoint_ref,
                api_ref=api_ref,
                capability_name=_resolve_capability_name(
                    endpoint_ref=endpoint_ref, api_ref=api_ref
                ),
                source_path=endpoint.source_path,
                order=order,
                description=endpoint.description,
            )
        )
    operation_dependency_plans: list[SdkOperationDependencyPlan] = []
    for order, dependency in enumerate(operation.operation_dependencies, start=1):
        target_sdk_key = dependency.target_sdk_name.casefold()
        target_package_name = (
            None
            if target_sdk_key == sdk_name.casefold()
            else sdk_dependency_package_names_by_sdk_ref[target_sdk_key]
        )
        operation_dependency_plans.append(
            SdkOperationDependencyPlan(
                target_operation_ref=dependency.target_operation_ref,
                target_sdk_name=dependency.target_sdk_name,
                target_operation_name=dependency.target_operation_name,
                target_package_name=target_package_name,
                source_path=dependency.source_path,
                order=order,
                description=dependency.description,
            )
        )
    return SdkOperationPlan(
        name=operation.name,
        source_path=operation.source_path,
        api_endpoints=tuple(endpoint_plans),
        sdk_operation_dependencies=tuple(operation_dependency_plans),
        description=operation.description,
    )


def _build_sdk_surface_plan(*, surface: SdkSurfaceOwnership) -> SdkSurfacePlan:
    return SdkSurfacePlan(
        name=surface.name,
        source_path=surface.source_path,
        methods=tuple(
            SdkSurfaceMethodPlan(
                name=method.name,
                surface_name=method.surface_name,
                source_path=method.source_path,
                operation_ref=method.operation_ref,
                operation_name=method.operation_name,
                method_family=method.method_family,
                effect=method.effect,
                mutation_scope=method.mutation_scope,
                confirmation_policy=method.confirmation_policy,
                execution_mode=method.execution_mode,
                runtime_binding_kind=method.runtime_binding_kind,
                description=method.description,
            )
            for method in surface.methods
        ),
        description=surface.description,
    )


def _sdk_dependency_package_names_by_sdk_ref(
    dependencies: list[AwareSdkTomlDependencySpec],
) -> dict[str, str]:
    package_names_by_sdk_ref: dict[str, str] = {}
    for dependency in dependencies:
        if dependency.kind != AwareSdkDependencyKind.sdk_package:
            continue
        package_name = (dependency.package_name or "").strip()
        sdk_ref = _sdk_ref_from_package_name(package_name)
        if not sdk_ref:
            continue
        sdk_ref_key = sdk_ref.casefold()
        if sdk_ref_key in package_names_by_sdk_ref:
            raise ValueError(
                "SDK dependency package names resolve to duplicate SDK refs: " + sdk_ref
            )
        package_names_by_sdk_ref[sdk_ref_key] = package_name
    return package_names_by_sdk_ref


def _sdk_ref_from_package_name(package_name: str) -> str:
    return "".join(
        char if char.isalnum() else "_" for char in (package_name or "").strip()
    ).strip("_")


def _resolve_api_ref_for_endpoint(
    *, endpoint_ref: str, apis: tuple[SdkApiOwnership, ...]
) -> str:
    matches = [
        api.api_ref
        for api in apis
        if endpoint_ref == api.api_ref or endpoint_ref.startswith(api.api_ref + ".")
    ]
    if not matches:
        raise ValueError(
            f"SDK compile plan cannot resolve api_ref for endpoint {endpoint_ref!r}"
        )
    return max(matches, key=len)


def _resolve_capability_name(*, endpoint_ref: str, api_ref: str) -> str:
    suffix = endpoint_ref.removeprefix(api_ref + ".")
    parts = [part.strip() for part in suffix.split(".")]
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"SDK compile plan cannot resolve capability name for endpoint {endpoint_ref!r}"
        )
    return parts[0]


def _resolve_endpoint_name(*, endpoint_ref: str) -> str:
    parts = [part.strip() for part in endpoint_ref.split(".") if part.strip()]
    if len(parts) < 3:
        raise ValueError(
            f"SDK compile plan cannot resolve endpoint name for endpoint {endpoint_ref!r}"
        )
    return parts[-1]


def encode_sdk_compile_plan(*, plan: SdkCompilePlan) -> dict[str, object]:
    return {
        "schema_version": plan.schema_version,
        "package_name": plan.package_name,
        "fqn_prefix": plan.fqn_prefix,
        "source_files": list(plan.source_files),
        "sdk_ownership": [
            {
                "name": sdk.name,
                "source_path": sdk.source_path,
                "description": sdk.description,
                "apis": [
                    {
                        "api_ref": api.api_ref,
                        "source_path": api.source_path,
                    }
                    for api in sdk.apis
                ],
                "operations": [
                    {
                        "name": operation.name,
                        "source_path": operation.source_path,
                        "description": operation.description,
                        "endpoints": [
                            {
                                "endpoint_ref": endpoint.endpoint_ref,
                                "source_path": endpoint.source_path,
                                "description": endpoint.description,
                            }
                            for endpoint in operation.endpoints
                        ],
                        "operation_dependencies": [
                            {
                                "target_operation_ref": (
                                    dependency.target_operation_ref
                                ),
                                "target_sdk_name": dependency.target_sdk_name,
                                "target_operation_name": (
                                    dependency.target_operation_name
                                ),
                                "source_path": dependency.source_path,
                                "description": dependency.description,
                            }
                            for dependency in operation.operation_dependencies
                        ],
                    }
                    for operation in sdk.operations
                ],
                "surfaces": [
                    {
                        "name": surface.name,
                        "source_path": surface.source_path,
                        "description": surface.description,
                        "methods": [
                            {
                                "name": method.name,
                                "surface_name": method.surface_name,
                                "source_path": method.source_path,
                                "description": method.description,
                                "operation_ref": method.operation_ref,
                                "operation_name": method.operation_name,
                                "method_family": method.method_family,
                                "effect": method.effect,
                                "mutation_scope": method.mutation_scope,
                                "confirmation_policy": method.confirmation_policy,
                                "execution_mode": method.execution_mode,
                                "runtime_binding_kind": method.runtime_binding_kind,
                            }
                            for method in surface.methods
                        ],
                    }
                    for surface in sdk.surfaces
                ],
            }
            for sdk in plan.sdk_ownership
        ],
        "sdk_configs": [_encode_sdk_config_plan(row) for row in plan.sdk_configs],
    }


def _encode_sdk_config_plan(plan: SdkConfigPlan) -> dict[str, object]:
    return {
        "name": plan.name,
        "source_path": plan.source_path,
        "description": plan.description,
        "apis": [
            {
                "api_ref": api.api_ref,
                "source_path": api.source_path,
            }
            for api in plan.apis
        ],
        "operations": [
            {
                "name": operation.name,
                "source_path": operation.source_path,
                "description": operation.description,
                "api_endpoints": [
                    {
                        "name": endpoint.name,
                        "endpoint_ref": endpoint.endpoint_ref,
                        "api_ref": endpoint.api_ref,
                        "capability_name": endpoint.capability_name,
                        "source_path": endpoint.source_path,
                        "order": endpoint.order,
                        "role": endpoint.role,
                        "required": endpoint.required,
                        "description": endpoint.description,
                    }
                    for endpoint in operation.api_endpoints
                ],
                "sdk_operation_dependencies": [
                    {
                        "target_operation_ref": (dependency.target_operation_ref),
                        "target_sdk_name": dependency.target_sdk_name,
                        "target_operation_name": (dependency.target_operation_name),
                        "target_package_name": dependency.target_package_name,
                        "source_path": dependency.source_path,
                        "order": dependency.order,
                        "role": dependency.role,
                        "required": dependency.required,
                        "description": dependency.description,
                    }
                    for dependency in operation.sdk_operation_dependencies
                ],
            }
            for operation in plan.operations
        ],
        "surfaces": [
            {
                "name": surface.name,
                "source_path": surface.source_path,
                "description": surface.description,
                "methods": [
                    {
                        "name": method.name,
                        "surface_name": method.surface_name,
                        "source_path": method.source_path,
                        "description": method.description,
                        "operation_ref": method.operation_ref,
                        "operation_name": method.operation_name,
                        "method_family": method.method_family,
                        "effect": method.effect,
                        "mutation_scope": method.mutation_scope,
                        "confirmation_policy": method.confirmation_policy,
                        "execution_mode": method.execution_mode,
                        "runtime_binding_kind": method.runtime_binding_kind,
                    }
                    for method in surface.methods
                ],
            }
            for surface in plan.surfaces
        ],
    }


__all__ = [
    "SdkCompilePlan",
    "SdkCompilePlanArtifact",
    "build_sdk_compile_plan",
    "emit_sdk_compile_plan_artifact",
    "encode_sdk_compile_plan",
]
