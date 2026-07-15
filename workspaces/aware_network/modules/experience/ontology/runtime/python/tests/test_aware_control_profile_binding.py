from __future__ import annotations

from pathlib import Path

from aware_experience.compiler.models import (
    ExperienceProjectionExperienceOwnership,
)
from aware_experience.environment_profile.compiler import (
    load_environment_profile_ownership_from_sources,
)
from aware_experience.graph.compiler import load_graph_ownership_from_sources
from aware_experience.projection.compiler import (
    load_projection_experience_ownership_from_sources,
)


def _repo_root() -> Path:
    for path in Path(__file__).resolve().parents:
        if (path / "workspaces/aware_network/aware.workspace.toml").is_file():
            return path
    raise RuntimeError("Aware repo root not found")


def test_aware_control_declares_identity_admission_binding_surface_and_graph() -> None:
    repo_root = _repo_root()
    control_root = (
        repo_root
        / "workspaces"
        / "aware_network"
        / "modules"
        / "interface"
        / "experiences"
        / "aware_control"
    )
    projection_ownership = load_projection_experience_ownership_from_sources(
        package_root=control_root,
        source_files=(Path("experiences.aware"),),
    )
    identity_experience = _projection_experience_by_name(
        projection_ownership,
        "aware_control_identity",
    )

    assert identity_experience.projection == "Identity"
    assert len(identity_experience.nodes) == 1
    node = identity_experience.nodes[0]
    assert node.name == "identity.Identity"
    assert node.identities[0].key == "default"

    surfaces_by_key = {
        surface.surface_key: surface for surface in identity_experience.section_surfaces
    }
    identity_surface = surfaces_by_key["identity.admission"]
    assert identity_surface.section_key == "identity_admission"
    assert identity_surface.observable_key == "identity"
    assert identity_surface.view_key == "admission.v1"
    assert identity_surface.graph_identity_ref == "default"

    graph_ownership = load_graph_ownership_from_sources(
        package_root=control_root,
        source_files=(Path("graphs.aware"),),
        projection_experience_ownership=projection_ownership,
    )
    assert len(graph_ownership) == 1
    graph = graph_ownership[0]
    assert graph.name == "identity_admission_default"
    assert graph.experience == "aware_control_identity"
    assert graph.root == "default"

    profiles = load_environment_profile_ownership_from_sources(
        package_root=control_root,
        source_files=(Path("profiles.aware"),),
        projection_experience_ownership=projection_ownership,
    )

    assert len(profiles) == 1
    profile = profiles[0]
    assert profile.experience_name == "aware_control_identity"
    assert profile.key == "os.default"

    process = profile.process_configs[0]
    thread = process.thread_configs[0]
    layout = thread.layout_configs[0]
    section = layout.sections[0]
    assert section.section_key == "identity_admission"
    assert section.projection_experience_name == "aware_control_identity"
    assert section.view_key == "identity.admission.v1"
    assert section.section_graph_binding_key == "identity.admission"


def _projection_experience_by_name(
    projection_ownership: tuple[ExperienceProjectionExperienceOwnership, ...],
    name: str,
) -> ExperienceProjectionExperienceOwnership:
    for ownership in projection_ownership:
        if ownership.name == name:
            return ownership
    raise AssertionError(f"Missing projection experience: {name}")
