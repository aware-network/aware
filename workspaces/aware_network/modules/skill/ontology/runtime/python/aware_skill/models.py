from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SkillApiOwnership:
    api_ref: str
    source_path: str


@dataclass(frozen=True, slots=True)
class SkillEndpointOwnership:
    name: str
    endpoint_ref: str
    source_path: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SkillStepOwnership:
    position: int
    endpoint_name: str
    instruction: str
    source_path: str


@dataclass(frozen=True, slots=True)
class SkillOwnership:
    name: str
    source_path: str
    apis: tuple[SkillApiOwnership, ...]
    endpoints: tuple[SkillEndpointOwnership, ...]
    steps: tuple[SkillStepOwnership, ...]
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SkillConfigApiPlan:
    api_ref: str
    source_path: str


@dataclass(frozen=True, slots=True)
class SkillConfigApiEndpointPlan:
    name: str
    endpoint_ref: str
    api_ref: str
    capability_name: str
    source_path: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SkillConfigStepPlan:
    position: int
    endpoint_name: str
    endpoint_ref: str
    api_ref: str
    instruction: str
    source_path: str


@dataclass(frozen=True, slots=True)
class SkillConfigPlan:
    name: str
    source_path: str
    apis: tuple[SkillConfigApiPlan, ...]
    api_endpoints: tuple[SkillConfigApiEndpointPlan, ...]
    steps: tuple[SkillConfigStepPlan, ...]
    description: str | None = None


__all__ = [
    "SkillApiOwnership",
    "SkillConfigApiEndpointPlan",
    "SkillConfigApiPlan",
    "SkillConfigPlan",
    "SkillConfigStepPlan",
    "SkillEndpointOwnership",
    "SkillOwnership",
    "SkillStepOwnership",
]
