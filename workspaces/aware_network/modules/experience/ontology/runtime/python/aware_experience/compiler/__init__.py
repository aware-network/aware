from __future__ import annotations

from importlib import import_module
from typing import cast

_EXPORTS: dict[str, tuple[str, str]] = {
    "ExperienceCompileResult": ("aware_experience.compiler.compile", "ExperienceCompileResult"),
    "compile_experience_workspace": ("aware_experience.compiler.compile", "compile_experience_workspace"),
    "ExperienceActionOwnership": ("aware_experience.compiler.models", "ExperienceActionOwnership"),
    "ExperienceActionProgramBindingOwnership": (
        "aware_experience.compiler.models",
        "ExperienceActionProgramBindingOwnership",
    ),
    "ExperienceActorOwnership": ("aware_experience.compiler.models", "ExperienceActorOwnership"),
    "ExperienceActorRoleContract": ("aware_experience.compiler.models", "ExperienceActorRoleContract"),
    "ExperienceCompilePlan": ("aware_experience.compiler.models", "ExperienceCompilePlan"),
    "ExperienceCompilePlanArtifact": ("aware_experience.compiler.models", "ExperienceCompilePlanArtifact"),
    "ExperienceEnvironmentEventActionOwnership": (
        "aware_experience.compiler.models",
        "ExperienceEnvironmentEventActionOwnership",
    ),
    "ExperienceEnvironmentEventOwnership": (
        "aware_experience.compiler.models",
        "ExperienceEnvironmentEventOwnership",
    ),
    "ExperienceEnvironmentOwnership": ("aware_experience.compiler.models", "ExperienceEnvironmentOwnership"),
    "ExperienceEnvironmentProgramOwnership": (
        "aware_experience.compiler.models",
        "ExperienceEnvironmentProgramOwnership",
    ),
    "ExperienceEnvironmentActorBinding": ("aware_experience.compiler.models", "ExperienceEnvironmentActorBinding"),
    "ExperienceEventBindingOwnership": ("aware_experience.compiler.models", "ExperienceEventBindingOwnership"),
    "ExperienceEventOwnership": ("aware_experience.compiler.models", "ExperienceEventOwnership"),
    "ExperienceProgramOwnership": ("aware_experience.compiler.models", "ExperienceProgramOwnership"),
    "ExperienceProjectionAPIOwnership": ("aware_experience.compiler.models", "ExperienceProjectionAPIOwnership"),
    "ExperienceProjectionAPIContractOwnership": (
        "aware_experience.compiler.models",
        "ExperienceProjectionAPIContractOwnership",
    ),
    "ExperienceProjectionAPIContractParamOwnership": (
        "aware_experience.compiler.models",
        "ExperienceProjectionAPIContractParamOwnership",
    ),
    "ExperienceProjectionBranchOwnership": ("aware_experience.compiler.models", "ExperienceProjectionBranchOwnership"),
    "ExperienceProjectionExperienceOwnership": (
        "aware_experience.compiler.models",
        "ExperienceProjectionExperienceOwnership",
    ),
    "ExperienceProjectionObservableOwnership": (
        "aware_experience.compiler.models",
        "ExperienceProjectionObservableOwnership",
    ),
    "ExperienceProjectionViewOwnership": ("aware_experience.compiler.models", "ExperienceProjectionViewOwnership"),
    "ExperienceViewApiViewOwnership": (
        "aware_experience.compiler.models",
        "ExperienceViewApiViewOwnership",
    ),
    "ExperienceViewApiOwnership": ("aware_experience.compiler.models", "ExperienceViewApiOwnership"),
    "ExperienceRoleOwnership": ("aware_experience.compiler.models", "ExperienceRoleOwnership"),
    "build_experience_view_api_compile_plan": (
        "aware_experience.view_api",
        "build_experience_view_api_compile_plan",
    ),
    "build_experience_view_api_ownership": (
        "aware_experience.view_api",
        "build_experience_view_api_ownership",
    ),
    "build_experience_compile_plan": ("aware_experience.compiler.builder", "build_experience_compile_plan"),
    "emit_experience_compile_plan_artifact": (
        "aware_experience.compiler.builder",
        "emit_experience_compile_plan_artifact",
    ),
    "ExperienceWorkspace": ("aware_experience.compiler.workspace", "ExperienceWorkspace"),
    "ExperienceWorkspaceSnapshot": ("aware_experience.compiler.workspace", "ExperienceWorkspaceSnapshot"),
}


def __getattr__(name: str) -> object:
    export = _EXPORTS.get(name)
    if export is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = export
    module = import_module(module_name)
    value = cast(object, getattr(module, attr_name))
    globals()[name] = value
    return value
