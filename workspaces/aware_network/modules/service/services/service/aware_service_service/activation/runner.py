from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Protocol
from uuid import UUID

from aware_service_runtime.implementation_package import ProjectionSessionResolver
from aware_service_runtime.package_ref_resolution import (
    ResolvedServiceRuntimePackageRef,
)
from aware_utils.logging import logger

from aware_service_service.activation.registry import (
    ActivatedServiceImplementationPackage,
)
from aware_service_service.activation.package_refs import (
    committed_package_source_path,
)


class CommittedServicePackageActivator(Protocol):
    async def __call__(
        self,
        *,
        package_ref: ResolvedServiceRuntimePackageRef,
        runtime: Any,
        index: Any,
        actor_id: UUID | None,
        service_config_lane: Any,
        service_lane: Any,
        api_reference_branch_ids_by_api_name: Mapping[str, UUID],
        experience_reference_branch_ids_by_experience_name: Mapping[str, UUID],
        experience_reference_commit_store_root: Path | None,
        allow_materialization: bool,
        projection_session_resolver: ProjectionSessionResolver,
        activation_commit_store_root: Path | None,
    ) -> Any: ...


class TomlServicePackageActivator(Protocol):
    async def __call__(
        self,
        *,
        toml_path: Path,
        repo_root: Path | None,
        runtime: Any,
        index: Any,
        actor_id: UUID | None,
        service_config_lane: Any,
        service_lane: Any,
        api_reference_branch_ids_by_api_name: Mapping[str, UUID],
        experience_reference_branch_ids_by_experience_name: Mapping[str, UUID],
        experience_reference_commit_store_root: Path | None,
        allow_materialization: bool,
        projection_session_resolver: ProjectionSessionResolver,
        activation_commit_store_root: Path | None,
    ) -> Any: ...


@dataclass(frozen=True, slots=True)
class ImplementationPackageActivationResult:
    activated_packages: tuple[ActivatedServiceImplementationPackage, ...]
    service_ids_by_name: dict[str, UUID]
    timings: dict[str, object]


def duration_since(started: float) -> float:
    return perf_counter() - started


async def activate_implementation_package_bindings(
    *,
    toml_paths: tuple[Path, ...],
    committed_package_refs: tuple[ResolvedServiceRuntimePackageRef, ...],
    runtime: Any,
    index: Any,
    lanes: Any,
    api_reference_branch_ids_by_api_name: Mapping[str, UUID],
    experience_reference_branch_ids_by_experience_name: Mapping[str, UUID],
    experience_reference_commit_store_root: Path | None,
    allow_materialization: bool,
    activation_commit_store_root: Path | None = None,
    projection_session_resolver_factory: Callable[[], ProjectionSessionResolver],
    materialization_runtime_persistence_context: Callable[
        [], AbstractContextManager[object]
    ],
    toml_path_context: Callable[[Path], AbstractContextManager[object]],
    activate_committed_package_binding: CommittedServicePackageActivator,
    activate_toml_package_binding: TomlServicePackageActivator,
    service_package_id_for_committed_package_ref: Callable[..., UUID],
    service_package_id_for_activated_binding: Callable[[Any], UUID],
) -> ImplementationPackageActivationResult:
    activated_packages: list[ActivatedServiceImplementationPackage] = []
    service_ids_by_name: dict[str, UUID] = {}
    service_source_by_name: dict[str, str] = {}
    timings: dict[str, object] = {}

    committed_item_timings: list[dict[str, object]] = []
    committed_activation_started = perf_counter()
    for package_ref in committed_package_refs:
        item_started = perf_counter()
        projection_session_resolver = projection_session_resolver_factory()
        with materialization_runtime_persistence_context():
            binding = await activate_committed_package_binding(
                package_ref=package_ref,
                runtime=runtime,
                index=index,
                actor_id=None,
                service_config_lane=lanes.service_config,
                service_lane=lanes.service,
                api_reference_branch_ids_by_api_name=api_reference_branch_ids_by_api_name,
                experience_reference_branch_ids_by_experience_name=(
                    experience_reference_branch_ids_by_experience_name
                ),
                experience_reference_commit_store_root=(
                    experience_reference_commit_store_root
                ),
                allow_materialization=allow_materialization,
                projection_session_resolver=projection_session_resolver,
                activation_commit_store_root=activation_commit_store_root,
            )
        source = committed_package_source_path(package_ref=package_ref)
        activated_packages.append(
            ActivatedServiceImplementationPackage(
                source_path=source,
                service_package_id=service_package_id_for_committed_package_ref(
                    package_ref=package_ref,
                    binding=binding,
                ),
                binding=binding,
            )
        )
        source_label = (
            source.as_posix() if source is not None else package_ref.package_name
        )
        committed_item_timings.append(
            {
                "source": source_label,
                "duration_s": duration_since(item_started),
                "service_count": len(binding.service_ids_by_name),
            }
        )
        _remember_activated_services(
            service_ids_by_name=service_ids_by_name,
            service_source_by_name=service_source_by_name,
            binding=binding,
            source_label=source_label,
        )
    timings["activate_committed_packages_duration_s"] = duration_since(
        committed_activation_started
    )
    timings["activate_committed_package_items"] = committed_item_timings

    toml_item_timings: list[dict[str, object]] = []
    toml_activation_started = perf_counter()
    for toml_path in toml_paths:
        item_started = perf_counter()
        logger.info(
            "ServiceHost implementation activation package started: source=%s",
            toml_path,
        )
        if not toml_path.exists() or not toml_path.is_file():
            raise RuntimeError(
                "Service host implementation package TOML was not found: "
                f"{toml_path}"
            )
        with toml_path_context(toml_path):
            projection_session_resolver = projection_session_resolver_factory()
            with materialization_runtime_persistence_context():
                binding = await activate_toml_package_binding(
                    toml_path=toml_path,
                    repo_root=None,
                    runtime=runtime,
                    index=index,
                    actor_id=None,
                    service_config_lane=lanes.service_config,
                    service_lane=lanes.service,
                    api_reference_branch_ids_by_api_name=api_reference_branch_ids_by_api_name,
                    experience_reference_branch_ids_by_experience_name=(
                        experience_reference_branch_ids_by_experience_name
                    ),
                    experience_reference_commit_store_root=(
                        experience_reference_commit_store_root
                    ),
                    allow_materialization=allow_materialization,
                    projection_session_resolver=projection_session_resolver,
                    activation_commit_store_root=activation_commit_store_root,
                )
        activated_packages.append(
            ActivatedServiceImplementationPackage(
                source_path=toml_path,
                service_package_id=service_package_id_for_activated_binding(binding),
                binding=binding,
            )
        )
        toml_item_timings.append(
            {
                "source": toml_path.as_posix(),
                "duration_s": duration_since(item_started),
                "service_count": len(binding.service_ids_by_name),
            }
        )
        logger.info(
            "ServiceHost implementation activation package finished: source=%s duration_s=%.3f service_count=%d",
            toml_path,
            duration_since(item_started),
            len(binding.service_ids_by_name),
        )
        _remember_activated_services(
            service_ids_by_name=service_ids_by_name,
            service_source_by_name=service_source_by_name,
            binding=binding,
            source_label=toml_path.as_posix(),
        )
    timings["activate_toml_packages_duration_s"] = duration_since(
        toml_activation_started
    )
    timings["activate_toml_package_items"] = toml_item_timings

    return ImplementationPackageActivationResult(
        activated_packages=tuple(activated_packages),
        service_ids_by_name=service_ids_by_name,
        timings=timings,
    )


def _remember_activated_services(
    *,
    service_ids_by_name: dict[str, UUID],
    service_source_by_name: dict[str, str],
    binding: Any,
    source_label: str,
) -> None:
    for service_name, service_id in binding.service_ids_by_name.items():
        existing_source = service_source_by_name.get(service_name)
        if existing_source is not None:
            raise RuntimeError(
                "Multiple Service implementation packages activate the same service name: "
                f"service={service_name!r} first={existing_source} second={source_label}"
            )
        service_source_by_name[service_name] = source_label
        service_ids_by_name[service_name] = service_id


__all__ = [
    "CommittedServicePackageActivator",
    "ImplementationPackageActivationResult",
    "TomlServicePackageActivator",
    "activate_implementation_package_bindings",
    "duration_since",
]
