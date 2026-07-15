from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_attention_ontology.layout.layout_config import LayoutConfig
from aware_attention_ontology.layout.layout_config_section_config import (
    LayoutConfigSectionConfig,
)
from aware_experience.handlers.impl.projection import (
    projection_experience as projection_handler,
)
from aware_experience.handlers.impl.projection import (
    projection_experience_layout_graph_binding as layout_binding_handler,
)
from aware_experience.handlers.impl.projection import (
    projection_experience_layout_section_graph_binding as layout_section_handler,
)
from aware_experience.stable_ids import (
    stable_projection_experience_layout_graph_binding_id,
    stable_projection_experience_layout_section_graph_binding_id,
)
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_experience_ontology.projection.projection_experience_layout_graph_binding import (
    ProjectionExperienceLayoutGraphBinding,
)
from aware_experience_ontology.projection.projection_experience_section_graph_binding import (
    ProjectionExperienceSectionGraphBinding,
)


class _Session:
    def __init__(self) -> None:
        self._rows: dict[tuple[type, UUID], object] = {}

    def put(self, value: object) -> None:
        value_id = getattr(value, "id", None)
        if value_id is not None:
            self._rows[(type(value), UUID(str(value_id)))] = value

    def imap_get(self, cls: type, value_id: UUID):
        return self._rows.get((cls, UUID(str(value_id))))


def _ids() -> dict[str, UUID]:
    ns = uuid5(
        NAMESPACE_URL,
        "aware://tests/experience/layout-graph-binding/v1",
    )
    return {
        "projection_experience": uuid5(ns, "projection-experience"),
        "opgi": uuid5(ns, "opgi"),
        "layout_config": uuid5(ns, "layout-config"),
        "layout_section": uuid5(ns, "layout-section-primary"),
        "other_layout": uuid5(ns, "layout-config-other"),
        "other_layout_section": uuid5(ns, "layout-section-other"),
        "section_binding": uuid5(ns, "section-binding-primary"),
        "view": uuid5(ns, "view-overview"),
        "graph_identity": uuid5(ns, "graph-identity-home"),
    }


def _projection_experience(ids: dict[str, UUID]) -> ProjectionExperience:
    return ProjectionExperience.model_construct(
        id=ids["projection_experience"],
        object_projection_graph_identity_id=ids["opgi"],
        name="home_story",
        projection_experience_layout_graph_bindings=[],
    )


def _layout_config(ids: dict[str, UUID]) -> LayoutConfig:
    return LayoutConfig.model_construct(
        id=ids["layout_config"],
        key="configuration_map",
        title="Configuration Map",
        section_configs=[],
    )


def _layout_section(
    ids: dict[str, UUID],
    *,
    layout_config_id: UUID | None = None,
    layout_section_id: UUID | None = None,
) -> LayoutConfigSectionConfig:
    return LayoutConfigSectionConfig.model_construct(
        id=layout_section_id or ids["layout_section"],
        layout_config_id=layout_config_id or ids["layout_config"],
        section_key="primary",
        order=0,
        flex=1.0,
        is_visible=True,
    )


def _section_graph_binding(
    ids: dict[str, UUID]
) -> ProjectionExperienceSectionGraphBinding:
    return ProjectionExperienceSectionGraphBinding.model_construct(
        id=ids["section_binding"],
        projection_experience_id=ids["projection_experience"],
        layout_config_section_config_id=ids["layout_section"],
        projection_experience_view_id=ids["view"],
        projection_experience_graph_identity_id=ids["graph_identity"],
        binding_key="home.primary",
        section_key="primary",
    )


@pytest.mark.asyncio
async def test_projection_experience_creates_layout_graph_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ids = _ids()
    session = _Session()
    projection_experience = _projection_experience(ids)
    layout_config = _layout_config(ids)
    session.put(projection_experience)
    session.put(layout_config)
    monkeypatch.setattr(
        layout_binding_handler,
        "current_handler_session",
        lambda: session,
    )
    monkeypatch.setattr(
        projection_handler.ProjectionExperienceLayoutGraphBinding,
        "build_via_projection_experience",
        staticmethod(layout_binding_handler.build_via_projection_experience),
    )

    created = await projection_handler.create_layout_graph_binding(
        projection_experience,
        layout_config_id=ids["layout_config"],
        binding_key=" configuration_map ",
    )

    assert created.id == stable_projection_experience_layout_graph_binding_id(
        projection_experience_id=ids["projection_experience"],
        layout_config_id=ids["layout_config"],
        binding_key="configuration_map",
    )
    assert created.layout_config is layout_config
    assert created.binding_key == "configuration_map"
    assert projection_experience.projection_experience_layout_graph_bindings == [
        created
    ]

    session.put(created)
    created_again = await projection_handler.create_layout_graph_binding(
        projection_experience,
        layout_config_id=ids["layout_config"],
        binding_key="configuration_map",
    )

    assert created_again is created
    assert projection_experience.projection_experience_layout_graph_bindings == [
        created
    ]


@pytest.mark.asyncio
async def test_layout_graph_binding_groups_section_binding_for_same_layout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ids = _ids()
    session = _Session()
    layout_binding = ProjectionExperienceLayoutGraphBinding.model_construct(
        id=stable_projection_experience_layout_graph_binding_id(
            projection_experience_id=ids["projection_experience"],
            layout_config_id=ids["layout_config"],
            binding_key="configuration_map",
        ),
        projection_experience_id=ids["projection_experience"],
        layout_config_id=ids["layout_config"],
        binding_key="configuration_map",
        layout_section_graph_bindings=[],
    )
    section_binding = _section_graph_binding(ids)
    layout_section = _layout_section(ids)
    session.put(layout_binding)
    session.put(section_binding)
    session.put(layout_section)
    monkeypatch.setattr(
        layout_binding_handler,
        "current_handler_session",
        lambda: session,
    )
    monkeypatch.setattr(
        layout_section_handler,
        "current_handler_session",
        lambda: session,
    )
    monkeypatch.setattr(
        layout_binding_handler.ProjectionExperienceLayoutSectionGraphBinding,
        "build_via_projection_experience_layout_graph_binding",
        staticmethod(
            layout_section_handler.build_via_projection_experience_layout_graph_binding
        ),
    )

    created = await layout_binding_handler.add_section_graph_binding(
        layout_binding,
        section_graph_binding_id=ids["section_binding"],
    )

    assert created.id == stable_projection_experience_layout_section_graph_binding_id(
        projection_experience_layout_graph_binding_id=layout_binding.id,
        section_graph_binding_id=ids["section_binding"],
    )
    assert created.section_graph_binding is section_binding
    assert layout_binding.layout_section_graph_bindings == [created]

    session.put(created)
    created_again = await layout_binding_handler.add_section_graph_binding(
        layout_binding,
        section_graph_binding_id=ids["section_binding"],
    )

    assert created_again is created
    assert layout_binding.layout_section_graph_bindings == [created]


@pytest.mark.asyncio
async def test_layout_graph_binding_rejects_section_from_other_layout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ids = _ids()
    session = _Session()
    layout_binding = ProjectionExperienceLayoutGraphBinding.model_construct(
        id=stable_projection_experience_layout_graph_binding_id(
            projection_experience_id=ids["projection_experience"],
            layout_config_id=ids["layout_config"],
            binding_key="configuration_map",
        ),
        projection_experience_id=ids["projection_experience"],
        layout_config_id=ids["layout_config"],
        binding_key="configuration_map",
        layout_section_graph_bindings=[],
    )
    section_binding = _section_graph_binding(ids)
    wrong_layout_section = _layout_section(
        ids,
        layout_config_id=ids["other_layout"],
        layout_section_id=ids["layout_section"],
    )
    session.put(layout_binding)
    session.put(section_binding)
    session.put(wrong_layout_section)
    monkeypatch.setattr(
        layout_binding_handler,
        "current_handler_session",
        lambda: session,
    )

    with pytest.raises(RuntimeError, match="layout mismatch"):
        await layout_binding_handler.add_section_graph_binding(
            layout_binding,
            section_graph_binding_id=ids["section_binding"],
        )
