from __future__ import annotations

from typing import Literal

from aware_code.grammar_anchor.render_delta import (
    resolve_code_grammar_anchor_render_delta,
)
from aware_code.semantic_capability import SemanticCapabilityTypedOperation

from aware_experience.profile.semantic_operation_resolution import (
    EXPERIENCE_PROFILE_TITLE_UPDATE_OPERATION,
)
from aware_experience.profile.source_projection import (
    resolve_experience_profile_source_projection,
)


_SOURCE = """experience home_story {
    profile os.default {
        title "Home Story OS"
    }
    profile guest {
        title "Guest Home"
    }
}
"""


def _operation(
    *,
    family: Literal["update", "delete"] = "update",
) -> SemanticCapabilityTypedOperation:
    return SemanticCapabilityTypedOperation(
        operation_key="aware_experience.profile.title:home_story:os.default:update",
        operation_family=family,
        semantic_operation_type=EXPERIENCE_PROFILE_TITLE_UPDATE_OPERATION,
        semantic_key="experience.profile:home_story:os.default",
        semantic_subject_type=(
            "aware_experience.EnvironmentExperienceProfileConfig"
        ),
        field_path="title",
        source_refs=("profiles.aware",),
        before_payload={"title": "Home Story OS"},
        after_payload={"title": "Aware Home OS"},
        requires_baseline_object_identity=True,
    )


def test_profile_title_source_projection_selects_exact_semantic_anchor() -> None:
    projection = resolve_experience_profile_source_projection(
        typed_operations=(_operation(),),
        package_name="home-story-experience",
        package_root="modules/home/experiences/home_story",
        sources_root=".",
        source_text_by_ref={"profiles.aware": _SOURCE},
    )

    assert projection.ready is True
    assert projection.request is not None
    assert projection.request.bindings[0].semantic_key_template == (
        "experience.profile:{experience_name}:{profile_key}"
    )
    response = resolve_code_grammar_anchor_render_delta(request=projection.request)

    assert response.success is True
    assert response.resolved is True
    assert response.render_entry_count == 1
    assert response.package_delta is not None
    assert len(response.package_delta.paths) == 1
    rendered = response.package_delta.paths[0].content_text
    assert rendered is not None
    assert 'profile os.default {\n        title "Aware Home OS"' in rendered
    assert 'profile guest {\n        title "Guest Home"' in rendered
    assert 'profile guest {\n        title "Aware Home OS"' not in rendered


def test_profile_title_source_projection_delete_fails_closed() -> None:
    projection = resolve_experience_profile_source_projection(
        typed_operations=(_operation(family="delete"),),
        package_name="home-story-experience",
        package_root="modules/home/experiences/home_story",
        sources_root=".",
        source_text_by_ref={"profiles.aware": _SOURCE},
    )

    assert projection.ready is False
    assert projection.request is None
    assert projection.blockers == (
        "experience_profile_source_projection_update_required",
    )


def test_profile_title_source_projection_exposes_workspace_hook_shape() -> None:
    projection = resolve_experience_profile_source_projection(
        typed_operations=(_operation(),),
        package_name="home-story-experience",
        package_root="modules/home/experiences/home_story",
        sources_root=".",
        source_text_by_ref={"profiles.aware": _SOURCE},
    )

    result = projection.provider_delta_result(
        package_name="home-story-experience",
        source_session_context={"source_session_id": "source-session-1"},
        commit_ids=("commit-1",),
        head_commit_ids=("head-1",),
    )

    assert result["provider_key"] == "aware_experience"
    assert result["head_commit_ids"] == ("head-1",)
    details = result["details"]
    assert isinstance(details, dict)
    stage = details["provider_delta_source_projection"]
    assert isinstance(stage, dict)
    assert stage["ready"] is True
    assert "grammar_anchor_render_delta_request" in stage
