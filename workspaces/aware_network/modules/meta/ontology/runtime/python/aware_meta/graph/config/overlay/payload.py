"""Flattened OCG overlay payload schema for materializers."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ObjectOverlayPayload(BaseModel):
    """Per-language overrides for an ObjectConfig."""

    rendered_name: str | None = Field(default=None)
    file_hint: str | None = Field(default=None)


class ClassOverlayPayload(BaseModel):
    """Per-language overrides for a ClassConfig."""

    rendered_name: str | None = Field(default=None)
    lang_flags: dict | None = Field(default=None)


class EnumOverlayPayload(BaseModel):
    """Per-language overrides for an EnumConfig."""

    rendered_name: str | None = Field(default=None)


class EnumOptionOverlayPayload(BaseModel):
    """Per-language overrides for an EnumOption."""

    rendered_name: str | None = Field(default=None)
    wire_name: str | None = Field(default=None)


class AttributeOverlayPayload(BaseModel):
    """Per-language overrides for an AttributeConfig."""

    rendered_name: str | None = Field(default=None)
    wire_name: str | None = Field(default=None)


class FunctionOverlayPayload(BaseModel):
    """Per-language overrides for a FunctionConfig."""

    rendered_name: str | None = Field(default=None)
    lang_flags: dict | None = Field(default=None)


class ObjectConfigGraphOverlayPayload(BaseModel):
    """Language-specific overlay payload keyed by canonical OCG UUID strings."""

    language: str = Field(...)
    object_overlays: dict[str, ObjectOverlayPayload] = Field(default_factory=dict)
    class_overlays: dict[str, ClassOverlayPayload] = Field(default_factory=dict)
    enum_overlays: dict[str, EnumOverlayPayload] = Field(default_factory=dict)
    enum_option_overlays: dict[str, EnumOptionOverlayPayload] = Field(
        default_factory=dict
    )
    attribute_overlays: dict[str, AttributeOverlayPayload] = Field(default_factory=dict)
    function_overlays: dict[str, FunctionOverlayPayload] = Field(default_factory=dict)


__all__ = [
    "AttributeOverlayPayload",
    "ClassOverlayPayload",
    "EnumOptionOverlayPayload",
    "EnumOverlayPayload",
    "FunctionOverlayPayload",
    "ObjectConfigGraphOverlayPayload",
    "ObjectOverlayPayload",
]
