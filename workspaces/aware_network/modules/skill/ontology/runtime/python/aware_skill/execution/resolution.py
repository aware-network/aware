from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import TypeVar, cast
from uuid import UUID

from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_orm.models.orm_model import ORMModel
from aware_orm.session.session import Session

from ._meta_hydration import hydrate_committed_lane_session, hydrate_oig_commit_session
from .models import (
    ResolvedSkillExecutionPlan,
    ResolvedSkillExecutionStep,
    ResolvedSkillStepTarget,
)


_TOrm = TypeVar("_TOrm", bound=ORMModel)


@dataclass(frozen=True, slots=True)
class _SkillOntologyClasses:
    skill_config: type[ORMModel]
    skill_config_api: type[ORMModel]
    skill_config_api_endpoint: type[ORMModel]
    skill_config_experience: type[ORMModel]
    skill_config_step: type[ORMModel]
    skill_config_step_target: type[ORMModel]
    skill_config_target: type[ORMModel]


async def resolve_committed_skill_execution_plan(
    *,
    index: MetaGraphRuntimeIndex,
    lane: MaterializationLaneContext,
    skill_config_id: UUID,
) -> ResolvedSkillExecutionPlan:
    session = await hydrate_committed_lane_session(
        index=index,
        lane=lane,
        error_context="Skill execution plan resolution",
    )
    return resolve_skill_execution_plan_from_session(
        session=session,
        skill_config_id=skill_config_id,
    )


async def resolve_skill_execution_plan_from_commit(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    skill_config_id: UUID,
) -> ResolvedSkillExecutionPlan:
    session = await hydrate_oig_commit_session(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        error_context="Skill execution plan commit resolution",
    )
    return resolve_skill_execution_plan_from_session(
        session=session,
        skill_config_id=skill_config_id,
    )


def resolve_skill_execution_plan_from_session(
    *,
    session: Session,
    skill_config_id: UUID,
) -> ResolvedSkillExecutionPlan:
    ontology = _skill_ontology_classes()
    skill_config = _required_imap(
        session=session,
        orm_class=ontology.skill_config,
        object_id=skill_config_id,
        context="Skill execution plan",
    )
    steps = _ordered_skill_config_steps(
        session=session, ontology=ontology, skill_config=skill_config
    )
    return ResolvedSkillExecutionPlan(
        skill_config_id=skill_config.id,
        skill_name=str(getattr(skill_config, "name")),
        steps=tuple(
            _resolve_step(session=session, ontology=ontology, step=step)
            for step in steps
        ),
    )


def _resolve_step(
    *, session: Session, ontology: _SkillOntologyClasses, step: ORMModel
) -> ResolvedSkillExecutionStep:
    step_id = _required_uuid(step.id, "SkillConfigStep.id")
    endpoint_id = _required_uuid(
        getattr(step, "skill_config_api_endpoint_id", None),
        f"SkillConfigStep {step_id} missing skill_config_api_endpoint_id",
    )
    skill_endpoint = _resolve_related(
        session=session,
        orm_class=ontology.skill_config_api_endpoint,
        object_id=endpoint_id,
        related=getattr(step, "skill_config_api_endpoint", None),
        context=f"SkillConfigStep {step_id} endpoint requirement",
    )
    skill_config_api_id = _required_uuid(
        getattr(skill_endpoint, "skill_config_api_id", None),
        f"SkillConfigApiEndpoint {skill_endpoint.id} missing skill_config_api_id",
    )
    skill_config_api = session.imap_get(ontology.skill_config_api, skill_config_api_id)
    api_id = (
        _required_uuid(
            getattr(skill_config_api, "api_id", None),
            f"SkillConfigApi {skill_config_api.id} missing api_id",
        )
        if skill_config_api is not None
        else None
    )
    api_endpoint_id = _required_uuid(
        getattr(skill_endpoint, "api_endpoint_id", None),
        f"SkillConfigApiEndpoint {skill_endpoint.id} missing api_endpoint_id",
    )
    return ResolvedSkillExecutionStep(
        skill_config_step_id=step_id,
        position=int(getattr(step, "position")),
        instruction=str(getattr(step, "instruction")),
        skill_config_api_endpoint_id=skill_endpoint.id,
        api_capability_endpoint_id=api_endpoint_id,
        endpoint_requirement_name=str(getattr(skill_endpoint, "name")),
        capability_name=str(getattr(skill_endpoint, "capability_name")),
        targets=tuple(
            _resolve_step_target(
                session=session,
                ontology=ontology,
                step=step,
                step_target=step_target,
            )
            for step_target in _ordered_step_targets(
                session=session, ontology=ontology, step=step
            )
        ),
        api_id=api_id,
    )


def _resolve_step_target(
    *,
    session: Session,
    ontology: _SkillOntologyClasses,
    step: ORMModel,
    step_target: ORMModel,
) -> ResolvedSkillStepTarget:
    step_target_id = _required_uuid(step_target.id, "SkillConfigStepTarget.id")
    step_id = _required_uuid(step.id, "SkillConfigStep.id")
    step_target_step_id = _required_uuid(
        getattr(step_target, "skill_config_step_id", None),
        "SkillConfigStepTarget.skill_config_step_id",
    )
    if step_target_step_id != step_id:
        raise RuntimeError(
            f"SkillConfigStepTarget {step_target_id} does not belong to SkillConfigStep {step_id}."
        )

    skill_config_target_id = _required_uuid(
        getattr(step_target, "skill_config_target_id", None),
        f"SkillConfigStepTarget {step_target_id} missing skill_config_target_id",
    )
    skill_config_target = _resolve_related(
        session=session,
        orm_class=ontology.skill_config_target,
        object_id=skill_config_target_id,
        related=getattr(step_target, "skill_config_target", None),
        context=f"SkillConfigStepTarget {step_target_id} Skill target",
    )
    skill_config_experience_id = _required_uuid(
        getattr(skill_config_target, "skill_config_experience_id", None),
        f"SkillConfigTarget {skill_config_target.id} missing skill_config_experience_id",
    )
    skill_config_experience = _resolve_related(
        session=session,
        orm_class=ontology.skill_config_experience,
        object_id=skill_config_experience_id,
        related=getattr(skill_config_target, "skill_config_experience", None),
        context=f"SkillConfigTarget {skill_config_target.id} Skill experience",
    )
    step_skill_config_id = _required_uuid(
        getattr(step, "skill_config_id", None),
        f"SkillConfigStep {step.id} missing skill_config_id",
    )
    target_skill_config_id = _required_uuid(
        getattr(skill_config_experience, "skill_config_id", None),
        f"SkillConfigExperience {skill_config_experience.id} missing skill_config_id",
    )
    if target_skill_config_id != step_skill_config_id:
        raise RuntimeError(
            f"SkillConfigTarget {skill_config_target.id} does not belong to "
            f"SkillConfigStep {step.id} SkillConfig {step_skill_config_id}."
        )
    graph_identity_id = _required_uuid(
        getattr(skill_config_target, "projection_experience_graph_identity_id", None),
        f"SkillConfigTarget {skill_config_target.id} missing projection_experience_graph_identity_id",
    )

    return ResolvedSkillStepTarget(
        skill_config_step_target_id=step_target_id,
        skill_config_target_id=skill_config_target_id,
        projection_experience_graph_identity_id=graph_identity_id,
        name=str(getattr(skill_config_target, "name")),
    )


def _ordered_skill_config_steps(
    *,
    session: Session,
    ontology: _SkillOntologyClasses,
    skill_config: ORMModel,
) -> tuple[ORMModel, ...]:
    related_steps = tuple(
        step
        for step in getattr(skill_config, "steps", [])
        if isinstance(step, ontology.skill_config_step)
    )
    if related_steps:
        steps = related_steps
    else:
        skill_config_id = _required_uuid(skill_config.id, "SkillConfig.id")
        steps = tuple(
            obj
            for obj in _session_objects(
                session=session, orm_class=ontology.skill_config_step
            )
            if _optional_uuid(getattr(obj, "skill_config_id", None)) == skill_config_id
        )
    return _sort_steps_fail_on_duplicate_positions(steps)


def _ordered_step_targets(
    *,
    session: Session,
    ontology: _SkillOntologyClasses,
    step: ORMModel,
) -> tuple[ORMModel, ...]:
    related_targets = tuple(
        target
        for target in getattr(step, "targets", [])
        if isinstance(target, ontology.skill_config_step_target)
    )
    if related_targets:
        targets = related_targets
    else:
        step_id = _required_uuid(step.id, "SkillConfigStep.id")
        targets = tuple(
            obj
            for obj in _session_objects(
                session=session, orm_class=ontology.skill_config_step_target
            )
            if _optional_uuid(getattr(obj, "skill_config_step_id", None)) == step_id
        )
    return tuple(sorted(targets, key=lambda target: str(target.id)))


def _sort_steps_fail_on_duplicate_positions(
    steps: tuple[ORMModel, ...]
) -> tuple[ORMModel, ...]:
    seen: dict[int, UUID] = {}
    for step in steps:
        position = int(getattr(step, "position"))
        existing = seen.get(position)
        if existing is not None:
            raise RuntimeError(
                f"SkillConfigStep position {position} is duplicated by steps {existing} and {step.id}."
            )
        seen[position] = step.id
    return tuple(
        sorted(steps, key=lambda step: (int(getattr(step, "position")), str(step.id)))
    )


def _resolve_related(
    *,
    session: Session,
    orm_class: type[_TOrm],
    object_id: UUID,
    related: object,
    context: str,
) -> _TOrm:
    if (
        isinstance(related, orm_class)
        and _optional_uuid(getattr(related, "id", None)) == object_id
    ):
        return related
    return _required_imap(
        session=session,
        orm_class=orm_class,
        object_id=object_id,
        context=context,
    )


def _required_imap(
    *,
    session: Session,
    orm_class: type[_TOrm],
    object_id: UUID,
    context: str,
) -> _TOrm:
    obj = session.imap_get(orm_class, object_id)
    if obj is None:
        raise RuntimeError(
            f"{context} could not resolve {orm_class.__name__} {object_id}."
        )
    return obj


def _session_objects(*, session: Session, orm_class: type[_TOrm]) -> tuple[_TOrm, ...]:
    return tuple(
        cast(_TOrm, obj)
        for obj in session.imap_all_objects()
        if isinstance(obj, orm_class)
    )


def _skill_ontology_classes() -> _SkillOntologyClasses:
    return _SkillOntologyClasses(
        skill_config=_import_orm_class(
            module_name="aware_skill_ontology.skill.skill_config",
            class_name="SkillConfig",
        ),
        skill_config_api=_import_orm_class(
            module_name="aware_skill_ontology.skill.skill_config_api",
            class_name="SkillConfigApi",
        ),
        skill_config_api_endpoint=_import_orm_class(
            module_name="aware_skill_ontology.skill.skill_config_api_endpoint",
            class_name="SkillConfigApiEndpoint",
        ),
        skill_config_experience=_import_orm_class(
            module_name="aware_skill_ontology.skill.skill_config_experience",
            class_name="SkillConfigExperience",
        ),
        skill_config_step=_import_orm_class(
            module_name="aware_skill_ontology.skill.skill_config_step",
            class_name="SkillConfigStep",
        ),
        skill_config_step_target=_import_orm_class(
            module_name="aware_skill_ontology.skill.skill_config_step_target",
            class_name="SkillConfigStepTarget",
        ),
        skill_config_target=_import_orm_class(
            module_name="aware_skill_ontology.skill.skill_config_target",
            class_name="SkillConfigTarget",
        ),
    )


def _import_orm_class(*, module_name: str, class_name: str) -> type[ORMModel]:
    imported = import_module(module_name)
    value = getattr(imported, class_name)
    if not isinstance(value, type) or not issubclass(value, ORMModel):
        raise RuntimeError(f"{module_name}.{class_name} is not an ORMModel class.")
    return value


def _required_uuid(value: object, context: str) -> UUID:
    resolved = _optional_uuid(value)
    if resolved is None:
        raise RuntimeError(f"{context} is required.")
    return resolved


def _optional_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))
