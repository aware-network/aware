from __future__ import annotations

from pathlib import Path

import pytest

from aware_experience.profile.api_models import (
    ExperienceGraphIdentityProfileCatalogReadRequest,
    ExperienceGraphIdentityProfileReadRequest,
)
from aware_experience.profile.catalog import (
    resolve_profile_catalog_source,
)
from aware_experience.profile.service import (
    read_graph_identity_profile,
    read_graph_identity_profile_catalog,
)


def _write_profile_catalog(
    *,
    path: Path,
    experience_name: str,
    graph_name: str,
    review_label: str,
    graph_identity_ref: str = "doors.front_door",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[sample]",
                f'experience_name = "{experience_name}"',
                'projection_key = "home"',
                f'graph_name = "{graph_name}"',
                "",
                "[[graph_identity_profiles]]",
                f'graph_identity_ref = "{graph_identity_ref}"',
                f'review_label = "{review_label}"',
                'resolution_prompts = ["door"]',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_home_story_profile_catalog(*, root: Path) -> None:
    path = root / "profiles" / "home_story.instance-profiles.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[sample]",
                'experience_name = "home_story"',
                'projection_key = "home"',
                'graph_name = "home_default"',
                "",
                "[[graph_identity_profiles]]",
                'graph_identity_ref = "doors.front_door"',
                'review_label = "Front Door"',
                'resolution_prompts = ["door", "front door", "door handle"]',
                'aliases = ["entry door"]',
                "",
                "[[graph_identity_profiles.exemplars]]",
                'key = "front_door_interior"',
                'label = "Front door interior"',
                'prompt_hint = "front door interior"',
                "is_primary = true",
                "",
                "[[graph_identity_profiles]]",
                'graph_identity_ref = "tvs.living_room_tv"',
                'review_label = "Living Room TV"',
                'resolution_prompts = ["tv", "living room tv"]',
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_read_graph_identity_profile_catalog_returns_home_story_profiles(
    tmp_path: Path,
) -> None:
    _write_home_story_profile_catalog(root=tmp_path)

    response = read_graph_identity_profile_catalog(
        request=ExperienceGraphIdentityProfileCatalogReadRequest(
            experience_name="home_story",
            graph_name="home_default",
        ),
        catalog_root=tmp_path,
    )

    assert response.experience_name == "home_story"
    assert response.graph_name == "home_default"
    assert response.catalog_revision is not None
    assert len(response.catalog_revision) == 64
    assert [profile.graph_identity_ref for profile in response.profiles] == [
        "doors.front_door",
        "tvs.living_room_tv",
    ]

    front_door_profile = response.profiles[0]
    assert front_door_profile.review_label == "Front Door"
    assert front_door_profile.resolution_prompts == [
        "door",
        "front door",
        "door handle",
    ]
    assert front_door_profile.aliases == ["entry door"]
    assert len(front_door_profile.exemplars) == 1
    assert front_door_profile.exemplars[0].key == "front_door_interior"
    assert front_door_profile.exemplars[0].is_primary is True


def test_read_graph_identity_profile_filters_refs_in_request_order(
    tmp_path: Path,
) -> None:
    _write_home_story_profile_catalog(root=tmp_path)

    response = read_graph_identity_profile(
        request=ExperienceGraphIdentityProfileReadRequest(
            experience_name="home_story",
            graph_name="home_default",
            graph_identity_refs=[
                "tvs.living_room_tv",
                "doors.front_door",
                "tvs.living_room_tv",
                "",
            ],
        ),
        catalog_root=tmp_path,
    )

    assert [profile.graph_identity_ref for profile in response.profiles] == [
        "tvs.living_room_tv",
        "doors.front_door",
    ]


def test_read_graph_identity_profile_catalog_fails_closed_when_missing() -> None:
    with pytest.raises(FileNotFoundError):
        read_graph_identity_profile_catalog(
            request=ExperienceGraphIdentityProfileCatalogReadRequest(
                experience_name="missing_experience",
                graph_name="missing_graph",
            ),
            catalog_root=Path("/tmp/experience-profile-service-empty-root"),
        )


def test_resolve_profile_catalog_source_fails_closed_when_ambiguous(
    tmp_path: Path,
) -> None:
    _write_profile_catalog(
        path=tmp_path
        / "workspace_a"
        / "profiles"
        / "home_story.instance-profiles.toml",
        experience_name="home_story",
        graph_name="home_default",
        review_label="Front Door A",
    )
    _write_profile_catalog(
        path=tmp_path / "workspace_b" / "profiles" / "duplicate.instance-profiles.toml",
        experience_name="home_story",
        graph_name="home_default",
        review_label="Front Door B",
    )

    with pytest.raises(
        ValueError, match="Ambiguous Experience graph-identity profile catalogs"
    ):
        resolve_profile_catalog_source(
            experience_name="home_story",
            graph_name="home_default",
            catalog_root=tmp_path,
        )
