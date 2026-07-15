from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, List, Literal, Optional

from aware_code_ontology.code.code_enums import CodeLanguage


class ObjectConfigGraphOverlayOverride(BaseModel):
    """Declarative overlay intent for a single ObjectConfigGraph entity."""

    kind: Literal["object", "class", "enum", "enum_option", "attribute", "function"]
    # Canonical owner path (e.g., \"meta.attribute.AttributeType\")
    class_path: str = Field(..., description="Canonical path for the owning type/enum.")
    # Member inside the owner (attribute/function/enum option); optional for object/class-level overrides
    member_name: Optional[str] = Field(
        default=None,
        description="Member name (attribute/function/enum option) when applicable.",
    )
    # Per-language identifier
    rename: Optional[str] = Field(
        default=None, description="Rendered identifier in the target language."
    )
    # Wire/serialized name or value when it differs from rename/canonical
    wire_name: Optional[str] = Field(
        default=None,
        description="Serialized name/value when different from rename/canonical.",
    )
    # Optional language-specific flags (e.g., {\"is_async\": true})
    lang_flags: Optional[dict[str, Any]] = Field(default=None)


class ObjectConfigGraphOverlayConfig(BaseModel):
    """ObjectConfigGraph overlay configuration driving overlay model construction."""

    language: CodeLanguage
    overrides: List[ObjectConfigGraphOverlayOverride] = Field(default_factory=list)
