from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_orm.session.session import Session
from _skill_runtime_test_paths import prepend_skill_dependency_paths


def _prepend_skill_runtime_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    prepend_skill_dependency_paths(monkeypatch)


def _add_all(session: Session, *objects: Any) -> None:
    for obj in objects:
        session.imap_add(obj)


def _import_class(module_name: str, class_name: str) -> type[Any]:
    return cast(type[Any], getattr(import_module(module_name), class_name))


def _resolve_plan_func() -> Callable[..., Any]:
    execution_module = import_module("aware_skill.execution")
    return cast(
        Callable[..., Any],
        getattr(execution_module, "resolve_skill_execution_plan_from_session"),
    )


def _skill_graph(
    *,
    api_endpoint_id: UUID | None = None,
    target_skill_config_id: UUID | None = None,
    step_position: int = 1,
) -> dict[str, Any]:
    api_endpoint_class = _import_class(
        "aware_api_ontology.api.api_capability_endpoint",
        "ApiCapabilityEndpoint",
    )
    skill_config_class = _import_class(
        "aware_skill_ontology.skill.skill_config",
        "SkillConfig",
    )
    skill_endpoint_class = _import_class(
        "aware_skill_ontology.skill.skill_config_api_endpoint",
        "SkillConfigApiEndpoint",
    )
    skill_step_class = _import_class(
        "aware_skill_ontology.skill.skill_config_step",
        "SkillConfigStep",
    )
    skill_step_target_class = _import_class(
        "aware_skill_ontology.skill.skill_config_step_target",
        "SkillConfigStepTarget",
    )
    skill_experience_class = _import_class(
        "aware_skill_ontology.skill.skill_config_experience",
        "SkillConfigExperience",
    )
    skill_target_class = _import_class(
        "aware_skill_ontology.skill.skill_config_target",
        "SkillConfigTarget",
    )

    skill_config_id = uuid4()
    step_id = uuid4()
    skill_endpoint_id = uuid4()
    resolved_api_endpoint_id = api_endpoint_id or uuid4()
    skill_experience_id = uuid4()
    skill_target_id = uuid4()
    step_target_id = uuid4()
    projection_experience_id = uuid4()
    projection_experience_graph_identity_id = uuid4()

    api_endpoint = api_endpoint_class.model_construct(
        id=resolved_api_endpoint_id,
        api_capability_id=uuid4(),
        name="open",
        description="Open one door.",
    )
    skill_endpoint = skill_endpoint_class.model_construct(
        id=skill_endpoint_id,
        skill_config_api_id=uuid4(),
        api_endpoint_id=resolved_api_endpoint_id,
        capability_name="door",
        name="open",
        description="Skill endpoint requirement.",
    )
    skill_experience = skill_experience_class.model_construct(
        id=skill_experience_id,
        skill_config_id=target_skill_config_id or skill_config_id,
        projection_experience_id=projection_experience_id,
        description="Home projection experience namespace.",
    )
    skill_target = skill_target_class.model_construct(
        id=skill_target_id,
        skill_config_experience_id=skill_experience_id,
        skill_config_experience=skill_experience,
        projection_experience_graph_identity_id=projection_experience_graph_identity_id,
        name="front-door",
        description="Experience graph identity target.",
    )
    step_target = skill_step_target_class.model_construct(
        id=step_target_id,
        skill_config_step_id=step_id,
        skill_config_target_id=skill_target_id,
        skill_config_target=skill_target,
        description="Step target.",
    )
    step = skill_step_class.model_construct(
        id=step_id,
        skill_config_id=skill_config_id,
        position=step_position,
        instruction="Read the requested door state before acting.",
        skill_config_api_endpoint_id=skill_endpoint_id,
        skill_config_api_endpoint=skill_endpoint,
        targets=[step_target],
    )
    skill_config = skill_config_class.model_construct(
        id=skill_config_id,
        name="door-control",
        description="Reusable door control skill.",
        steps=[step],
    )
    return {
        "skill_config": skill_config,
        "step": step,
        "skill_endpoint": skill_endpoint,
        "api_endpoint": api_endpoint,
        "skill_experience": skill_experience,
        "skill_target": skill_target,
        "step_target": step_target,
        "skill_target_id": skill_target_id,
        "projection_experience_graph_identity_id": projection_experience_graph_identity_id,
    }


def test_resolve_skill_execution_plan_sorts_steps_and_targets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_skill_runtime_paths(monkeypatch)
    resolve_skill_execution_plan_from_session = _resolve_plan_func()

    graph_a = _skill_graph(step_position=2)
    graph_b = _skill_graph(
        api_endpoint_id=graph_a["skill_endpoint"].api_endpoint_id,
        step_position=1,
    )
    skill_config = graph_a["skill_config"].model_copy(
        update={
            "steps": [
                graph_a["step"],
                graph_b["step"].model_copy(
                    update={"skill_config_id": graph_a["skill_config"].id}
                ),
            ]
        }
    )
    graph_b["step"].skill_config_id = skill_config.id
    graph_b["skill_experience"].skill_config_id = skill_config.id
    session = Session(branch_id=uuid4(), skip_db=True)
    _add_all(
        session,
        skill_config,
        graph_a["step"],
        graph_b["step"],
        graph_a["skill_endpoint"],
        graph_b["skill_endpoint"],
        graph_a["skill_experience"],
        graph_b["skill_experience"],
        graph_a["skill_target"],
        graph_b["skill_target"],
        graph_a["step_target"],
        graph_b["step_target"],
    )

    plan = resolve_skill_execution_plan_from_session(
        session=session,
        skill_config_id=skill_config.id,
    )

    assert plan.skill_config_id == skill_config.id
    assert plan.skill_name == "door-control"
    assert [step.position for step in plan.steps] == [1, 2]
    assert plan.steps[0].endpoint_requirement_name == "open"
    assert plan.steps[0].targets[0].name == "front-door"
    assert plan.steps[0].targets[0].skill_config_target_id == graph_b["skill_target"].id
    assert (
        plan.steps[0].targets[0].projection_experience_graph_identity_id
        == graph_b["projection_experience_graph_identity_id"]
    )


def test_resolve_skill_execution_plan_rejects_duplicate_step_positions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_skill_runtime_paths(monkeypatch)
    resolve_skill_execution_plan_from_session = _resolve_plan_func()

    graph_a = _skill_graph(step_position=1)
    graph_b = _skill_graph(
        api_endpoint_id=graph_a["skill_endpoint"].api_endpoint_id,
        step_position=1,
    )
    skill_config = graph_a["skill_config"].model_copy(
        update={
            "steps": [
                graph_a["step"],
                graph_b["step"].model_copy(
                    update={"skill_config_id": graph_a["skill_config"].id}
                ),
            ]
        }
    )
    graph_b["step"].skill_config_id = skill_config.id
    session = Session(branch_id=uuid4(), skip_db=True)
    _add_all(session, skill_config, graph_a["step"], graph_b["step"])

    with pytest.raises(RuntimeError, match="position 1 is duplicated"):
        resolve_skill_execution_plan_from_session(
            session=session,
            skill_config_id=skill_config.id,
        )


def test_resolve_skill_execution_plan_rejects_target_outside_skill_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_skill_runtime_paths(monkeypatch)
    resolve_skill_execution_plan_from_session = _resolve_plan_func()

    graph = _skill_graph(target_skill_config_id=uuid4())
    session = Session(branch_id=uuid4(), skip_db=True)
    _add_all(
        session,
        graph["skill_config"],
        graph["step"],
        graph["skill_endpoint"],
        graph["skill_experience"],
        graph["skill_target"],
        graph["step_target"],
    )

    with pytest.raises(RuntimeError, match="does not belong"):
        resolve_skill_execution_plan_from_session(
            session=session,
            skill_config_id=graph["skill_config"].id,
        )
