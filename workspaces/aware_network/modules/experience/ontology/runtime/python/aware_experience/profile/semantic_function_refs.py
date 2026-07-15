from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    EXPERIENCE_PROFILE_UPDATE_TITLE_FUNCTION: Any


EXPERIENCE_PROFILE_UPDATE_TITLE_FUNCTION_REF = (
    "aware_experience_ontology.environment.environment_experience_profile_config."
    "EnvironmentExperienceProfileConfig.update_title"
)


def __getattr__(name: str) -> Any:
    if name != "EXPERIENCE_PROFILE_UPDATE_TITLE_FUNCTION":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    ontology_module = import_module(
        "aware_experience_ontology.environment." "environment_experience_profile_config"
    )
    function_ref_module = import_module("aware_meta.materialization.function_refs")
    function = function_ref_module.meta_ontology_function_ref(
        ontology_module.EnvironmentExperienceProfileConfig.update_title
    )
    if function.ref != EXPERIENCE_PROFILE_UPDATE_TITLE_FUNCTION_REF:
        raise RuntimeError(
            "Experience profile update-title Function ref drift: "
            f"declared={EXPERIENCE_PROFILE_UPDATE_TITLE_FUNCTION_REF!r} "
            f"generated={function.ref!r}"
        )
    globals()[name] = function
    return function


__all__ = [
    "EXPERIENCE_PROFILE_UPDATE_TITLE_FUNCTION",
    "EXPERIENCE_PROFILE_UPDATE_TITLE_FUNCTION_REF",
]
