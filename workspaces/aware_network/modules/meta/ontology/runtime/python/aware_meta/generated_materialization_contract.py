from __future__ import annotations

from dataclasses import dataclass


TARGET_DESCRIPTOR_SOURCE_PROFILE_SELECTION = (
    "aware_meta.target_language_profile_selection"
)
ORM_RUNTIME_GENERATED_MATERIALIZATION_PRODUCT_INTENT = "orm_runtime"


@dataclass(frozen=True, slots=True)
class GeneratedMaterializationTargetProfile:
    descriptor_key: str
    target_language: str | None
    renderer_profile: str
    materialization_source: str
    descriptor_source: str = TARGET_DESCRIPTOR_SOURCE_PROFILE_SELECTION

    @property
    def target_key(self) -> str:
        return self.descriptor_key

    def target_metadata(self) -> dict[str, object]:
        metadata: dict[str, object] = {
            "descriptor_key": self.descriptor_key,
            "capability_key": self.descriptor_key,
            "target_descriptor_source": self.descriptor_source,
            "renderer_profile": self.renderer_profile,
            "materialization_source": self.materialization_source,
        }
        if self.target_language is not None:
            metadata["target_language"] = self.target_language
        return metadata

    def apply_to_target(self, target: dict[str, object]) -> None:
        for key, value in self.target_metadata().items():
            target.setdefault(key, value)


ORM_RUNTIME_TARGET_PROFILE = GeneratedMaterializationTargetProfile(
    descriptor_key="orm_runtime",
    target_language=None,
    renderer_profile="orm_runtime",
    materialization_source="ontology_orm_models",
)


def generated_materialization_intent_target_metadata(
    *,
    policy_key: str,
    materialization_target: str,
    target_language: str | None = None,
) -> dict[str, object]:
    """Return Meta-owned generated materialization intent metadata."""

    metadata: dict[str, object] = {
        "policy_key": policy_key,
        "materialization_target": materialization_target,
        "target_profile": ORM_RUNTIME_TARGET_PROFILE.descriptor_key,
        "renderer_profile": ORM_RUNTIME_TARGET_PROFILE.renderer_profile,
        "materialization_source": ORM_RUNTIME_TARGET_PROFILE.materialization_source,
        "product_intent": ORM_RUNTIME_GENERATED_MATERIALIZATION_PRODUCT_INTENT,
    }
    if target_language is not None:
        metadata["target_language"] = target_language
    return metadata


__all__ = [
    "GeneratedMaterializationTargetProfile",
    "ORM_RUNTIME_GENERATED_MATERIALIZATION_PRODUCT_INTENT",
    "ORM_RUNTIME_TARGET_PROFILE",
    "TARGET_DESCRIPTOR_SOURCE_PROFILE_SELECTION",
    "generated_materialization_intent_target_metadata",
]
