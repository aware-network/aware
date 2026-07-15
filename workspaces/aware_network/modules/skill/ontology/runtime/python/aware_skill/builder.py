from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from .compiler import load_skill_ownership_from_sources
from .models import (
    SkillApiOwnership,
    SkillConfigApiEndpointPlan,
    SkillConfigApiPlan,
    SkillConfigPlan,
    SkillConfigStepPlan,
    SkillOwnership,
)
from .workspace import SkillWorkspaceSnapshot


@dataclass(frozen=True, slots=True)
class SkillCompilePlan:
    schema_version: int
    package_name: str
    fqn_prefix: str
    source_files: tuple[str, ...]
    skill_ownership: tuple[SkillOwnership, ...]
    skill_configs: tuple[SkillConfigPlan, ...]


@dataclass(frozen=True, slots=True)
class SkillCompilePlanArtifact:
    path: Path
    relpath: str
    hash_sha256: str


def build_skill_compile_plan(*, snapshot: SkillWorkspaceSnapshot) -> SkillCompilePlan:
    source_files = tuple(path.as_posix() for path in snapshot.source_files)
    skill_ownership = load_skill_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
    )
    skill_configs = tuple(_build_skill_config_plan(skill=skill) for skill in skill_ownership)
    return SkillCompilePlan(
        schema_version=1,
        package_name=(snapshot.spec.skill.package_name or "").strip(),
        fqn_prefix=(snapshot.spec.skill.fqn_prefix or "").strip(),
        source_files=source_files,
        skill_ownership=skill_ownership,
        skill_configs=skill_configs,
    )


def emit_skill_compile_plan_artifact(
    *,
    plan: SkillCompilePlan,
    runtime_package_dir: Path,
    repo_root: Path,
) -> SkillCompilePlanArtifact:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)

    payload = encode_skill_compile_plan(plan=plan)
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = sha256(canonical).hexdigest()

    artifact_path = (runtime_package_dir / "skill.compile_plan.json").resolve()
    _ = artifact_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    relpath = artifact_path.relative_to(repo_root).as_posix()
    return SkillCompilePlanArtifact(
        path=artifact_path,
        relpath=relpath,
        hash_sha256=digest,
    )


def _build_skill_config_plan(*, skill: SkillOwnership) -> SkillConfigPlan:
    api_plans = tuple(
        SkillConfigApiPlan(
            api_ref=api.api_ref,
            source_path=api.source_path,
        )
        for api in skill.apis
    )
    endpoint_plans: list[SkillConfigApiEndpointPlan] = []
    for endpoint in skill.endpoints:
        api_ref = _resolve_api_ref_for_endpoint(endpoint_ref=endpoint.endpoint_ref, apis=skill.apis)
        endpoint_plans.append(
            SkillConfigApiEndpointPlan(
                name=endpoint.name,
                endpoint_ref=endpoint.endpoint_ref,
                api_ref=api_ref,
                capability_name=_resolve_capability_name(endpoint_ref=endpoint.endpoint_ref, api_ref=api_ref),
                source_path=endpoint.source_path,
                description=endpoint.description,
            )
        )
    endpoint_plans_by_name = {endpoint.name.casefold(): endpoint for endpoint in endpoint_plans}
    step_plans: list[SkillConfigStepPlan] = []
    for step in skill.steps:
        endpoint_plan = endpoint_plans_by_name.get(step.endpoint_name.casefold())
        if endpoint_plan is None:
            raise ValueError(
                f"Skill compile plan cannot resolve endpoint {step.endpoint_name!r} for step {step.position}"
            )
        step_plans.append(
            SkillConfigStepPlan(
                position=step.position,
                endpoint_name=step.endpoint_name,
                endpoint_ref=endpoint_plan.endpoint_ref,
                api_ref=endpoint_plan.api_ref,
                instruction=step.instruction,
                source_path=step.source_path,
            )
        )
    return SkillConfigPlan(
        name=skill.name,
        source_path=skill.source_path,
        apis=api_plans,
        api_endpoints=tuple(endpoint_plans),
        steps=tuple(sorted(step_plans, key=lambda item: (item.position, item.source_path))),
        description=skill.description,
    )


def _resolve_api_ref_for_endpoint(*, endpoint_ref: str, apis: tuple[SkillApiOwnership, ...]) -> str:
    matches = [
        api.api_ref
        for api in apis
        if endpoint_ref == api.api_ref or endpoint_ref.startswith(api.api_ref + ".")
    ]
    if not matches:
        raise ValueError(f"Skill compile plan cannot resolve api_ref for endpoint {endpoint_ref!r}")
    return max(matches, key=len)


def _resolve_capability_name(*, endpoint_ref: str, api_ref: str) -> str:
    suffix = endpoint_ref.removeprefix(api_ref + ".")
    parts = [part.strip() for part in suffix.split(".")]
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Skill compile plan cannot resolve capability name for endpoint {endpoint_ref!r}")
    return parts[0]


def encode_skill_compile_plan(*, plan: SkillCompilePlan) -> dict[str, object]:
    return {
        "schema_version": plan.schema_version,
        "package_name": plan.package_name,
        "fqn_prefix": plan.fqn_prefix,
        "source_files": list(plan.source_files),
        "skill_ownership": [
            {
                "name": skill.name,
                "source_path": skill.source_path,
                "description": skill.description,
                "apis": [
                    {
                        "api_ref": api.api_ref,
                        "source_path": api.source_path,
                    }
                    for api in skill.apis
                ],
                "endpoints": [
                    {
                        "name": endpoint.name,
                        "endpoint_ref": endpoint.endpoint_ref,
                        "source_path": endpoint.source_path,
                        "description": endpoint.description,
                    }
                    for endpoint in skill.endpoints
                ],
                "steps": [
                    {
                        "position": step.position,
                        "endpoint_name": step.endpoint_name,
                        "instruction": step.instruction,
                        "source_path": step.source_path,
                    }
                    for step in skill.steps
                ],
            }
            for skill in plan.skill_ownership
        ],
        "skill_configs": [_encode_skill_config_plan(row) for row in plan.skill_configs],
    }


def _encode_skill_config_plan(plan: SkillConfigPlan) -> dict[str, object]:
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
        "api_endpoints": [
            {
                "name": endpoint.name,
                "endpoint_ref": endpoint.endpoint_ref,
                "api_ref": endpoint.api_ref,
                "capability_name": endpoint.capability_name,
                "source_path": endpoint.source_path,
                "description": endpoint.description,
            }
            for endpoint in plan.api_endpoints
        ],
        "steps": [
            {
                "position": step.position,
                "endpoint_name": step.endpoint_name,
                "endpoint_ref": step.endpoint_ref,
                "api_ref": step.api_ref,
                "instruction": step.instruction,
                "source_path": step.source_path,
            }
            for step in plan.steps
        ],
    }


__all__ = [
    "SkillCompilePlan",
    "SkillCompilePlanArtifact",
    "build_skill_compile_plan",
    "emit_skill_compile_plan_artifact",
    "encode_skill_compile_plan",
]
