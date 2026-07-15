from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "ActionMaterializationSpec",
    "ExperiencePackageInstallScope",
    "ExperiencePackageMaterializationResult",
    "ExperiencePackageMaterializationSpec",
    "ExperienceProfilePublicationSummary",
    "MaterializationExecutionError",
    "ProgramMaterializationSpec",
    "ProjectionExperienceLayoutGraphBindingSpec",
    "ProjectionExperienceSectionSurfaceBindingSpec",
    "ProjectionExperienceSectionSurfaceMaterializationSpec",
    "build_action_materialization_plan",
    "build_program_materialization_plan",
    "build_section_surface_materialization_plan",
    "decode_program_materialization_step_payload",
    "decode_section_surface_materialization_step_payload",
    "encode_program_materialization_step_payload",
    "encode_section_surface_materialization_step_payload",
    "load_experience_compile_plan_payloads",
    "materialize_experience_compile_plan_actions",
    "materialize_experience_compile_plan_connector_configs",
    "materialize_experience_compile_plan_graphs",
    "materialize_experience_compile_plan_programs",
    "materialize_experience_compile_plan_section_surfaces",
    "materialize_experience_package_from_manifest",
    "materialize_experience_connector_config_ontology",
    "materialize_experience_program_ontology",
    "materialize_experience_section_surface_ontology",
    "resolve_action_materialization_specs",
    "resolve_experience_package_materialization_spec",
    "resolve_experience_profile_publication_summary",
    "resolve_program_materialization_specs",
    "resolve_section_surface_materialization_specs",
]


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(name)
    service = import_module("aware_experience.materialization.service")
    value = getattr(service, name)
    globals()[name] = value
    return value
