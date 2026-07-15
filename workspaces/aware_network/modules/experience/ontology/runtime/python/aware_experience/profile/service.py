from __future__ import annotations

from pathlib import Path

from aware_experience.profile.api_models import (
    ExperienceGraphIdentityProfile,
    ExperienceGraphIdentityProfileCatalogReadRequest,
    ExperienceGraphIdentityProfileCatalogReadResponse,
    ExperienceGraphIdentityProfileReadRequest,
    ExperienceGraphIdentityProfileReadResponse,
)
from aware_experience.profile.catalog import resolve_profile_catalog_source


def _filter_profiles(
    *,
    profiles: tuple[ExperienceGraphIdentityProfile, ...],
    graph_identity_refs: list[str],
) -> list[ExperienceGraphIdentityProfile]:
    if not graph_identity_refs:
        return list(profiles)

    profiles_by_ref = {profile.graph_identity_ref: profile for profile in profiles}
    selected_profiles: list[ExperienceGraphIdentityProfile] = []
    seen_graph_identity_refs: set[str] = set()
    for raw_ref in graph_identity_refs:
        graph_identity_ref = (raw_ref or "").strip()
        if not graph_identity_ref or graph_identity_ref in seen_graph_identity_refs:
            continue
        seen_graph_identity_refs.add(graph_identity_ref)
        profile = profiles_by_ref.get(graph_identity_ref)
        if profile is not None:
            selected_profiles.append(profile)
    return selected_profiles


def read_graph_identity_profile_catalog(
    *,
    request: ExperienceGraphIdentityProfileCatalogReadRequest,
    catalog_root: Path,
) -> ExperienceGraphIdentityProfileCatalogReadResponse:
    source = resolve_profile_catalog_source(
        experience_name=request.experience_name,
        graph_name=request.graph_name,
        catalog_root=catalog_root,
    )
    return ExperienceGraphIdentityProfileCatalogReadResponse(
        experience_name=source.experience_name,
        graph_name=source.graph_name,
        catalog_revision=source.catalog_revision,
        profiles=list(source.profiles),
    )


def read_graph_identity_profile(
    *,
    request: ExperienceGraphIdentityProfileReadRequest,
    catalog_root: Path,
) -> ExperienceGraphIdentityProfileReadResponse:
    source = resolve_profile_catalog_source(
        experience_name=request.experience_name,
        graph_name=request.graph_name,
        catalog_root=catalog_root,
    )
    return ExperienceGraphIdentityProfileReadResponse(
        experience_name=source.experience_name,
        graph_name=source.graph_name,
        catalog_revision=source.catalog_revision,
        profiles=_filter_profiles(
            profiles=source.profiles,
            graph_identity_refs=request.graph_identity_refs,
        ),
    )
