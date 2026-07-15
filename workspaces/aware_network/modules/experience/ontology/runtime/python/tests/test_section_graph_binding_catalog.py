from __future__ import annotations

import sys
from types import SimpleNamespace
from uuid import uuid4

from ._experience_runtime_test_paths import REPO_ROOT

_REPO_ROOT = REPO_ROOT
for _path in (
    _REPO_ROOT / "modules" / "experience" / "runtime",
    _REPO_ROOT / "modules" / "experience" / "structure" / "ontology" / "python",
    _REPO_ROOT / "modules" / "experience" / "structure" / "api" / "python",
):
    _path_str = str(_path.resolve())
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from aware_experience.section_graph_binding.catalog import (  # noqa: E402
    resolve_section_graph_binding_catalog,
    resolve_section_observable_invocation_actions,
    resolve_section_observable_view_instance,
)
from aware_api_ontology.api.api_view import ApiView  # noqa: E402
from aware_api_ontology.api.api_view_capability_endpoint import (  # noqa: E402
    ApiViewCapabilityEndpoint,
)
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)  # noqa: E402
from aware_experience_ontology.projection.projection_experience_graph_identity import (  # noqa: E402
    ProjectionExperienceGraphIdentity,
)
from aware_experience_ontology.projection.projection_experience_section import (  # noqa: E402
    ProjectionExperienceSection,
)
from aware_experience_ontology.projection.projection_experience_section_graph_binding import (  # noqa: E402
    ProjectionExperienceSectionGraphBinding,
)
from aware_experience_ontology.projection.projection_experience_section_view import (  # noqa: E402
    ProjectionExperienceSectionView,
)
from aware_experience_ontology.projection.projection_experience_view import (
    ProjectionExperienceView,
)  # noqa: E402
from aware_experience_ontology.projection.projection_experience_view_instance import (  # noqa: E402
    ProjectionExperienceViewInstance,
)
from aware_experience_ontology.projection.projection_experience_view_invocation_action_config import (  # noqa: E402
    ProjectionExperienceViewInvocationActionConfig,
)
from aware_experience_ontology.invocation.experience_invocation_action_config import (  # noqa: E402
    ExperienceInvocationActionConfig,
)
from aware_experience_ontology.invocation.experience_invocation_action_target_kind import (  # noqa: E402
    ExperienceInvocationActionTargetKind,
)


def test_resolve_section_graph_binding_catalog_builds_descriptor_rows() -> None:
    experience_id = uuid4()
    view_id = uuid4()
    api_view_id = uuid4()
    projection_observable_id = uuid4()
    graph_identity_id = uuid4()
    object_projection_graph_identity_id = uuid4()
    binding_id = uuid4()

    experience = ProjectionExperience.model_construct(
        id=experience_id,
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        name="workspace_coordination",
    )
    api_view = ApiView.model_construct(
        id=api_view_id,
        object_projection_graph_observable_id=projection_observable_id,
    )
    view = ProjectionExperienceView.model_construct(
        id=view_id,
        projection_experience_id=experience_id,
        api_view_id=api_view_id,
        name="detail",
    )
    graph_identity = ProjectionExperienceGraphIdentity.model_construct(
        id=graph_identity_id,
        projection_experience_graph_id=uuid4(),
        projection_experience_node_identity_id=uuid4(),
        key="issue.graph",
        is_root=True,
    )
    binding = ProjectionExperienceSectionGraphBinding.model_construct(
        id=binding_id,
        projection_experience_id=experience_id,
        projection_experience_view_id=view_id,
        projection_experience_graph_identity_id=graph_identity_id,
        binding_key="issue.primary",
        section_key="coordination.primary",
    )

    fake_session = SimpleNamespace(
        imap_all_objects=lambda: [
            experience,
            api_view,
            view,
            graph_identity,
            binding,
        ]
    )

    catalog = resolve_section_graph_binding_catalog(
        session=fake_session,
        experience_name="workspace_coordination",
    )

    assert catalog.experience_name == "workspace_coordination"
    assert len(catalog.entries) == 1
    assert catalog.catalog_revision

    entry = catalog.entry_for_binding_key(binding_key="issue.primary")
    assert entry is not None
    assert entry.projection_observable_id == projection_observable_id
    assert entry.graph_identity_object_id == graph_identity_id
    assert entry.projection_experience_id == experience_id
    assert entry.projection_experience_view_id == view_id
    assert entry.section_graph_binding_id == binding_id
    assert entry.descriptor.binding_key == "issue.primary"
    assert entry.descriptor.section_key == "coordination.primary"
    assert entry.descriptor.projection_observable_id == projection_observable_id
    assert entry.descriptor.projection_experience_graph_identity_id == graph_identity_id
    assert (
        entry.descriptor.object_projection_graph_identity_id
        == object_projection_graph_identity_id
    )
    assert entry.descriptor.view_ref == "workspace_coordination.detail"
    assert entry.descriptor.graph_identity_ref == "issue.graph"


def test_resolve_section_graph_binding_catalog_rejects_duplicate_binding_keys() -> None:
    experience_id = uuid4()
    view_id = uuid4()
    api_view_id = uuid4()
    graph_identity_id = uuid4()

    experience = ProjectionExperience.model_construct(
        id=experience_id,
        object_projection_graph_identity_id=uuid4(),
        name="workspace_coordination",
    )
    api_view = ApiView.model_construct(
        id=api_view_id,
        object_projection_graph_observable_id=uuid4(),
    )
    view = ProjectionExperienceView.model_construct(
        id=view_id,
        projection_experience_id=experience_id,
        api_view_id=api_view_id,
        name="detail",
    )
    graph_identity = ProjectionExperienceGraphIdentity.model_construct(
        id=graph_identity_id,
        projection_experience_graph_id=uuid4(),
        projection_experience_node_identity_id=uuid4(),
        key="issue.graph",
        is_root=True,
    )
    binding_a = ProjectionExperienceSectionGraphBinding.model_construct(
        id=uuid4(),
        projection_experience_id=experience_id,
        projection_experience_view_id=view_id,
        projection_experience_graph_identity_id=graph_identity_id,
        binding_key="issue.primary",
        section_key="coordination.primary",
    )
    binding_b = ProjectionExperienceSectionGraphBinding.model_construct(
        id=uuid4(),
        projection_experience_id=experience_id,
        projection_experience_view_id=view_id,
        projection_experience_graph_identity_id=graph_identity_id,
        binding_key="issue.primary",
        section_key="coordination.secondary",
    )

    fake_session = SimpleNamespace(
        imap_all_objects=lambda: [
            experience,
            api_view,
            view,
            graph_identity,
            binding_a,
            binding_b,
        ]
    )

    try:
        resolve_section_graph_binding_catalog(
            session=fake_session,
            experience_name="workspace_coordination",
        )
    except ValueError as exc:
        assert "Duplicate ProjectionExperienceSectionGraphBinding.binding_key" in str(
            exc
        )
    else:
        raise AssertionError("expected duplicate binding key failure")


def test_resolve_section_observable_view_instance_uses_section_bridge() -> None:
    experience_id = uuid4()
    observable_id = uuid4()
    graph_identity_id = uuid4()
    binding_id = uuid4()
    section_a_id = uuid4()
    section_b_id = uuid4()
    api_view_a_id = uuid4()
    api_view_b_id = uuid4()
    view_a_id = uuid4()
    view_b_id = uuid4()
    view_instance_a_id = uuid4()
    view_instance_b_id = uuid4()
    section_a_bridge_id = uuid4()
    section_b_bridge_id = uuid4()
    section_view_a_id = uuid4()
    section_view_b_id = uuid4()
    view_action_config_a_id = uuid4()
    view_action_config_b_id = uuid4()
    experience_action_config_a_id = uuid4()
    experience_action_config_b_id = uuid4()
    api_capability_endpoint_a_id = uuid4()
    api_capability_endpoint_b_id = uuid4()
    api_view_capability_endpoint_a_id = uuid4()
    api_view_capability_endpoint_b_id = uuid4()

    experience = ProjectionExperience.model_construct(
        id=experience_id,
        object_projection_graph_identity_id=uuid4(),
        name="aware_live",
    )
    api_view_a = ApiView.model_construct(
        id=api_view_a_id,
        object_projection_graph_observable_id=observable_id,
    )
    api_view_b = ApiView.model_construct(
        id=api_view_b_id,
        object_projection_graph_observable_id=observable_id,
    )
    view_a = ProjectionExperienceView.model_construct(
        id=view_a_id,
        projection_experience_id=experience_id,
        api_view_id=api_view_a_id,
        name="identity.admission.a",
    )
    view_b = ProjectionExperienceView.model_construct(
        id=view_b_id,
        projection_experience_id=experience_id,
        api_view_id=api_view_b_id,
        name="identity.admission.b",
    )
    binding = ProjectionExperienceSectionGraphBinding.model_construct(
        id=binding_id,
        projection_experience_id=experience_id,
        projection_experience_view_id=view_a_id,
        projection_experience_graph_identity_id=graph_identity_id,
        binding_key="identity.admission",
        section_key="identity_admission",
    )
    view_instance_a = ProjectionExperienceViewInstance.model_construct(
        id=view_instance_a_id,
        projection_experience_view_id=view_a_id,
        section_graph_binding_id=binding_id,
        view_instance_key="section-a.identity.admission",
        status="active",
    )
    view_instance_b = ProjectionExperienceViewInstance.model_construct(
        id=view_instance_b_id,
        projection_experience_view_id=view_b_id,
        section_graph_binding_id=binding_id,
        view_instance_key="section-b.identity.admission",
        status="active",
    )
    section_a = ProjectionExperienceSection.model_construct(
        id=section_a_bridge_id,
        projection_experience_id=experience_id,
        section_id=section_a_id,
        section_key="identity_admission",
    )
    section_b = ProjectionExperienceSection.model_construct(
        id=section_b_bridge_id,
        projection_experience_id=experience_id,
        section_id=section_b_id,
        section_key="identity_admission",
    )
    section_view_a = ProjectionExperienceSectionView.model_construct(
        id=section_view_a_id,
        projection_experience_section_id=section_a_bridge_id,
        projection_experience_view_instance_id=view_instance_a_id,
        status="active",
    )
    section_view_b = ProjectionExperienceSectionView.model_construct(
        id=section_view_b_id,
        projection_experience_section_id=section_b_bridge_id,
        projection_experience_view_instance_id=view_instance_b_id,
        status="active",
    )
    experience_action_config_a = ExperienceInvocationActionConfig.model_construct(
        id=experience_action_config_a_id,
        projection_experience_id=experience_id,
        target_kind=ExperienceInvocationActionTargetKind.api,
        api_capability_endpoint_id=api_capability_endpoint_a_id,
    )
    experience_action_config_b = ExperienceInvocationActionConfig.model_construct(
        id=experience_action_config_b_id,
        projection_experience_id=experience_id,
        target_kind=ExperienceInvocationActionTargetKind.api,
        api_capability_endpoint_id=api_capability_endpoint_b_id,
    )
    api_view_capability_endpoint_a = ApiViewCapabilityEndpoint.model_construct(
        id=api_view_capability_endpoint_a_id,
        api_view_id=api_view_a_id,
        api_capability_endpoint_id=api_capability_endpoint_a_id,
        action_key="admit_from_a",
        endpoint_ref="identity.admission.admit_from_a",
    )
    api_view_capability_endpoint_b = ApiViewCapabilityEndpoint.model_construct(
        id=api_view_capability_endpoint_b_id,
        api_view_id=api_view_b_id,
        api_capability_endpoint_id=api_capability_endpoint_b_id,
        action_key="admit_from_b",
        endpoint_ref="identity.admission.admit_from_b",
    )
    action_config_a = ProjectionExperienceViewInvocationActionConfig.model_construct(
        id=view_action_config_a_id,
        projection_experience_view_id=view_a_id,
        api_view_capability_endpoint_id=api_view_capability_endpoint_a_id,
        api_view_capability_endpoint=api_view_capability_endpoint_a,
        experience_invocation_action_config_id=experience_action_config_a_id,
        experience_invocation_action_config=experience_action_config_a,
        action_key="admit_from_a",
    )
    action_config_b = ProjectionExperienceViewInvocationActionConfig.model_construct(
        id=view_action_config_b_id,
        projection_experience_view_id=view_b_id,
        api_view_capability_endpoint_id=api_view_capability_endpoint_b_id,
        api_view_capability_endpoint=api_view_capability_endpoint_b,
        experience_invocation_action_config_id=experience_action_config_b_id,
        experience_invocation_action_config=experience_action_config_b,
        action_key="admit_from_b",
    )
    fake_session = SimpleNamespace(
        imap_all_objects=lambda: [
            experience,
            api_view_a,
            api_view_b,
            view_a,
            view_b,
            binding,
            view_instance_a,
            view_instance_b,
            section_a,
            section_b,
            section_view_a,
            section_view_b,
            experience_action_config_a,
            experience_action_config_b,
            api_view_capability_endpoint_a,
            api_view_capability_endpoint_b,
            action_config_a,
            action_config_b,
        ]
    )

    resolution = resolve_section_observable_view_instance(
        session=fake_session,
        experience_name="aware_live",
        section_id=section_a_id,
        object_projection_graph_observable_id=observable_id,
    )
    actions = resolve_section_observable_invocation_actions(
        session=fake_session,
        experience_name="aware_live",
        section_id=section_a_id,
        object_projection_graph_observable_id=observable_id,
    )

    assert resolution.projection_experience_section_id == section_a_bridge_id
    assert resolution.projection_experience_section_view_id == section_view_a_id
    assert resolution.projection_experience_view_instance_id == view_instance_a_id
    assert resolution.projection_experience_view_id == view_a_id
    assert resolution.view_ref == "aware_live.identity.admission.a"
    assert [action.action_key for action in actions] == ["admit_from_a"]
    assert actions[0].view_invocation_action_config_id == view_action_config_a_id
    assert actions[0].experience_invocation_action_config_id == (
        experience_action_config_a_id
    )
