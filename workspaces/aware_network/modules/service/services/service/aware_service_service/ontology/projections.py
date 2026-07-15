from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any, cast

from aware_experience.materialization.projection_resolution import (
    build_projection_runtime_resolver,
)
from aware_orm.projection.runtime import ProjectionRuntime
from aware_service_service.ontology.errors import (
    service_activation_requires_materialization as _service_activation_requires_materialization,
)
from aware_service_service_dto.host import ServiceHostProjectionRuntimeRequirement


def projection_names_from_runtime_requirements(
    requirements: tuple[ServiceHostProjectionRuntimeRequirement, ...],
) -> tuple[str, ...]:
    return dedupe_texts(
        tuple(
            name
            for requirement in requirements
            for name in (
                requirement.projection_name,
                *tuple(requirement.projection_names),
            )
            if name is not None
        )
    )


def dedupe_projection_runtime_requirements(
    requirements: tuple[ServiceHostProjectionRuntimeRequirement, ...],
) -> tuple[ServiceHostProjectionRuntimeRequirement, ...]:
    deduped: list[ServiceHostProjectionRuntimeRequirement] = []
    seen: set[tuple[object, ...]] = set()
    for requirement in requirements:
        key = (
            requirement.kind.value,
            requirement.provider_key,
            requirement.package_name,
            tuple(requirement.package_names),
            requirement.projection_name,
            tuple(requirement.projection_names),
            requirement.role,
            requirement.required,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(requirement)
    return tuple(deduped)


def service_host_required_projection_names(
    *,
    baseline_projection_names: tuple[str, ...],
    projection_runtime_requirements: tuple[
        ServiceHostProjectionRuntimeRequirement, ...
    ],
) -> tuple[str, ...]:
    return dedupe_texts(
        (
            *baseline_projection_names,
            *projection_names_from_runtime_requirements(
                projection_runtime_requirements
            ),
        )
    )


def ensure_service_host_projection_runtime_requirements_available(
    *,
    index: Any,
    requirements: tuple[ServiceHostProjectionRuntimeRequirement, ...],
) -> dict[str, object]:
    required_requirements = tuple(
        requirement
        for requirement in requirements
        if requirement.required
        and str(requirement.requirement_mode or "required").strip() != "optional"
    )
    if not required_requirements:
        return {
            "status": "skipped",
            "required_requirement_count": 0,
            "resolved_projection_count": 0,
        }
    resolver = build_projection_runtime_resolver(index=index)
    missing: list[dict[str, object]] = []
    resolved_projection_names: list[str] = []
    for requirement in required_requirements:
        metadata = dict(requirement.metadata or {})
        node_refs = tuple(
            str(node_ref or "").strip()
            for node_ref in cast(list[object], metadata.get("node_refs", []))
            if str(node_ref or "").strip()
        )
        experience_name = str(
            metadata.get("experience_name")
            or requirement.package_name
            or requirement.provider_key
            or "service_host"
        )
        for projection_name in dedupe_texts(
            tuple(
                name
                for name in (
                    requirement.projection_name,
                    *tuple(requirement.projection_names),
                )
                if name is not None
            )
        ):
            try:
                _ = resolver.resolve(
                    projection_key=projection_name,
                    node_refs=node_refs,
                    experience_name=experience_name,
                    context="ServiceHost projection runtime requirement",
                )
            except RuntimeError as exc:
                missing.append(
                    {
                        "projection_name": projection_name,
                        "provider_key": requirement.provider_key,
                        "package_name": requirement.package_name,
                        "kind": requirement.kind.value,
                        "error": str(exc),
                    }
                )
                continue
            if projection_name not in resolved_projection_names:
                resolved_projection_names.append(projection_name)
    if missing:
        missing_labels = ", ".join(
            f"{item['projection_name']} ({item['kind']})" for item in missing
        )
        raise _service_activation_requires_materialization(
            "ServiceHost projection runtime requirements missing required OPGs "
            "before Experience materialization: " + missing_labels
        )
    return {
        "status": "satisfied",
        "required_requirement_count": len(required_requirements),
        "resolved_projection_count": len(resolved_projection_names),
        "resolved_projection_names": resolved_projection_names,
    }


def verify_service_host_projection_runtime_from_ontology_artifacts(
    *,
    read_model: object,
    required_projection_names: tuple[str, ...],
) -> dict[str, object]:
    backend = (os.environ.get("AWARE_PERSISTENCE_BACKEND") or "").strip().lower()
    if backend != "db":
        return {
            "status": "skipped",
            "reason": f"backend:{backend or 'default'}",
            "dialect": "postgres",
            "source": "ontology_runtime_artifact_projection_plans",
            "projection_plan_count": 0,
        }

    index = getattr(read_model, "index", None)
    if index is None:
        return {
            "status": "skipped",
            "reason": "no_runtime_index",
            "dialect": "postgres",
            "source": "ontology_runtime_artifact_projection_plans",
            "projection_plan_count": 0,
        }

    projection_hashes: list[str] = []
    missing: list[dict[str, str]] = []
    for projection_name in dedupe_texts(required_projection_names):
        try:
            projection_hash = resolve_service_host_physical_projection_hash(
                index=index,
                projection=projection_name,
            )
            ProjectionRuntime.require_plan(
                dialect="postgres",
                projection_hash=projection_hash,
            )
        except Exception as exc:
            missing.append(
                {
                    "projection_name": projection_name,
                    "error": str(exc),
                }
            )
            continue
        if projection_hash not in projection_hashes:
            projection_hashes.append(projection_hash)

    if missing:
        missing_labels = ", ".join(
            f"{item['projection_name']} ({item['error']})" for item in missing
        )
        raise _service_activation_requires_materialization(
            "ServiceHost projection runtime requires ontology runtime artifact "
            "projection plans before implementation activation: " + missing_labels
        )

    return {
        "status": "satisfied",
        "dialect": "postgres",
        "source": "ontology_runtime_artifact_projection_plans",
        "projection_plan_count": len(projection_hashes),
        "projection_hashes": sorted(projection_hashes),
    }


def resolve_service_host_physical_projection_hash(
    *,
    index: Any,
    projection: str,
) -> str:
    resolved_projection = resolve_canonical_service_host_projection(
        index=index,
        projection=projection,
    )
    return resolve_runtime_lane_projection_hash(
        index=index,
        projection=resolved_projection,
    )


def resolve_canonical_service_host_projection(index: Any, *, projection: str) -> str:
    projection_token = str(projection or "").strip()
    if projection_token == "ServiceConfig":
        return resolve_projection_hash_by_required_class_names(
            index=index,
            projection_name=projection_token,
            required_class_names=frozenset(
                {
                    "ServiceConfig",
                    "ServiceConfigApi",
                    "ServiceConfigApiProjection",
                    "ServiceOperationConfigApiEndpoint",
                    "ServiceOperationConfigApiEndpointFunction",
                }
            ),
        )
    if projection_token == "Service":
        return resolve_projection_hash_by_required_class_names(
            index=index,
            projection_name=projection_token,
            required_class_names=frozenset(
                {
                    "Service",
                    "ServiceBranch",
                    "ServiceOperation",
                    "ServicePlan",
                }
            ),
        )
    return projection_token


def resolve_runtime_lane_projection_hash(index: Any, *, projection: str) -> str:
    projection_token = str(projection or "").strip()
    if not projection_token:
        raise ValueError("Service host lane projection cannot be empty.")

    opg_by_hash = getattr(index, "opg_by_hash", None)
    if not isinstance(opg_by_hash, Mapping):
        raise ValueError("Service host graph catalog must expose opg_by_hash.")
    if projection_token in opg_by_hash:
        return projection_token

    matches = tuple(
        projection_hash
        for projection_hash, opg in opg_by_hash.items()
        if str(getattr(opg, "name", "") or "").strip() == projection_token
    )
    if len(matches) != 1:
        raise ValueError(
            "Service host could not resolve one projection hash for lane binding: "
            + f"projection={projection_token!r} matches={matches!r}"
        )
    return str(matches[0])


def resolve_projection_hash_by_required_class_names(
    *,
    index: Any,
    projection_name: str,
    required_class_names: frozenset[str],
) -> str:
    candidate_hashes = tuple(
        projection_hash
        for projection_hash, opg in index.opg_by_hash.items()
        if (opg.name or "").strip() == projection_name
    )
    if not candidate_hashes:
        raise ValueError(
            f"Unknown projection {projection_name!r} while resolving canonical service-host lanes."
        )

    matches: list[str] = []
    candidate_descriptors: list[str] = []
    for projection_hash in candidate_hashes:
        opg = index.opg_by_hash[projection_hash]
        class_names = frozenset(
            index.class_configs_by_id[node.class_config_id].name
            for node in (opg.object_projection_graph_nodes or ())
        )
        candidate_descriptors.append(f"{projection_hash}:{sorted(class_names)!r}")
        if required_class_names.issubset(class_names):
            matches.append(projection_hash)

    if len(matches) != 1:
        raise ValueError(
            "Service host could not resolve one canonical projection hash for an implementation lane: "
            f"projection={projection_name!r} "
            f"required_class_names={sorted(required_class_names)!r} "
            f"matches={matches!r} "
            f"candidates={candidate_descriptors!r}"
        )
    return matches[0]


def dedupe_texts(values: tuple[str, ...]) -> tuple[str, ...]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return tuple(deduped)


__all__ = [
    "dedupe_projection_runtime_requirements",
    "dedupe_texts",
    "ensure_service_host_projection_runtime_requirements_available",
    "projection_names_from_runtime_requirements",
    "resolve_canonical_service_host_projection",
    "resolve_projection_hash_by_required_class_names",
    "resolve_runtime_lane_projection_hash",
    "service_host_required_projection_names",
    "verify_service_host_projection_runtime_from_ontology_artifacts",
]
