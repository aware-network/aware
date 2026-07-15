"""Flattened overlay payload schema for materializers.

This module defines the JSON-friendly shape of per-language overlays that
environment-artifacts emits and materializers (Dart, Python, SQL) consume.
It deliberately avoids ORM types and uses canonical IDs as strings.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = [
    "ObjectOverlayPayload",
    "ClassOverlayPayload",
    "EnumOverlayPayload",
    "EnumOptionOverlayPayload",
    "AttributeOverlayPayload",
    "FunctionOverlayPayload",
    "ObjectConfigGraphOverlayPayload",
]


class ObjectOverlayPayload(BaseModel):
    """Per-language overrides for an ObjectConfig."""

    rendered_name: str | None = Field(
        default=None,
        description="Rendered object/type identifier in the target language.",
    )
    file_hint: str | None = Field(
        default=None,
        description="Optional file/module hint for this object in the target language.",
    )


class ClassOverlayPayload(BaseModel):
    """Per-language overrides for a ClassConfig."""

    rendered_name: str | None = Field(
        default=None,
        description="Rendered class identifier in the target language.",
    )
    lang_flags: dict | None = Field(
        default=None,
        description="Language-specific flags (e.g., async/extension markers).",
    )


class EnumOverlayPayload(BaseModel):
    """Per-language overrides for an EnumConfig."""

    rendered_name: str | None = Field(
        default=None,
        description="Rendered enum identifier in the target language.",
    )


class EnumOptionOverlayPayload(BaseModel):
    """Per-language overrides for an EnumOption."""

    rendered_name: str | None = Field(
        default=None,
        description="Rendered enum case identifier in the target language.",
    )
    wire_name: str | None = Field(
        default=None,
        description="Wire/serialized value when different from rendered_name/canonical.",
    )


class AttributeOverlayPayload(BaseModel):
    """Per-language overrides for an AttributeConfig."""

    rendered_name: str | None = Field(
        default=None,
        description="Rendered field identifier in the target language.",
    )
    wire_name: str | None = Field(
        default=None,
        description="Wire/serialized key when different from rendered_name/canonical.",
    )


class FunctionOverlayPayload(BaseModel):
    """Per-language overrides for a FunctionConfig."""

    rendered_name: str | None = Field(
        default=None,
        description="Rendered function/method identifier in the target language.",
    )
    lang_flags: dict | None = Field(
        default=None,
        description="Language-specific flags (e.g., async, throws, annotations).",
    )


class ObjectConfigGraphOverlayPayload(BaseModel):
    """Flattened, language-specific overlay payload keyed by canonical IDs.

    All keys in the maps are canonical UUIDs (as strings) from the ObjectConfigGraph.
    Materializers use these maps to override identifiers/annotations while keeping
    canonical OCG semantics intact.
    """

    language: str = Field(
        ..., description="CodeLanguage value for this overlay payload."
    )

    object_overlays: dict[str, ObjectOverlayPayload] = Field(
        default_factory=dict,
        description="ObjectConfig overlays keyed by object_config_id.",
    )
    class_overlays: dict[str, ClassOverlayPayload] = Field(
        default_factory=dict,
        description="ClassConfig overlays keyed by class_config_id.",
    )
    enum_overlays: dict[str, EnumOverlayPayload] = Field(
        default_factory=dict,
        description="EnumConfig overlays keyed by enum_config_id.",
    )
    enum_option_overlays: dict[str, EnumOptionOverlayPayload] = Field(
        default_factory=dict,
        description="EnumOption overlays keyed by enum_option_id.",
    )
    attribute_overlays: dict[str, AttributeOverlayPayload] = Field(
        default_factory=dict,
        description="AttributeConfig overlays keyed by attribute_config_id.",
    )
    function_overlays: dict[str, FunctionOverlayPayload] = Field(
        default_factory=dict,
        description="FunctionConfig overlays keyed by function_config_id.",
    )
