from __future__ import annotations

"""
Runtime models manifest schema used by the canonical package rail.

Important layering constraint:
- `aware_orm.runtime` must be import-light because generated ontology packages import it
  during bootstrap (`__init__.py`).
- Therefore this schema lives in `aware_orm` (not `aware_environment`) to avoid importing
  the heavy `aware_environment/__init__.py` during ontology package install.
"""

from uuid import UUID

from pydantic import BaseModel, Field


class FunctionModelEntry(BaseModel):
    """Mapping from FunctionConfig id to canonical IO model paths."""

    function_config_id: UUID
    name: str
    input_model: str
    output_model: str


class ClassModelEntry(BaseModel):
    """Mapping from ClassConfig id to canonical model path."""

    class_config_id: UUID
    module: str
    name: str
    aware_class_ref: str | None = None
    functions: list[FunctionModelEntry] = Field(default_factory=list)


class EnumModelEntry(BaseModel):
    """Mapping from EnumConfig id to canonical model path."""

    enum_config_id: UUID
    module: str
    name: str


class ModelsManifest(BaseModel):
    """Models manifest embedded inside generated ontology packages."""

    language: str
    classes: list[ClassModelEntry] = Field(default_factory=list)
    enums: list[EnumModelEntry] = Field(default_factory=list)


__all__ = [
    "ClassModelEntry",
    "EnumModelEntry",
    "FunctionModelEntry",
    "ModelsManifest",
]
