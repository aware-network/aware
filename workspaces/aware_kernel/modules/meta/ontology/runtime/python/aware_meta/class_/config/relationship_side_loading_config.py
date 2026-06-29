"""Typed configuration for overriding relationship loading strategies."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator
from typing import Optional

from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipSideLoadingStrategy,
)


class ClassConfigRelationshipSideLoadingOverrides(BaseModel):
    forward: ClassConfigRelationshipSideLoadingStrategy | None = None
    reverse: ClassConfigRelationshipSideLoadingStrategy | None = None


class ClassConfigRelationshipSideLoadingEntry(BaseModel):
    namespace: str | None = Field(default=None, description="Package-relative namespace.")
    class_name: str | None = Field(default=None, description="ClassConfig class name (CamelCase).")
    attribute: str | None = Field(default=None, description="Relationship attribute name defined on the object.")
    edge: str | None = Field(default=None, description="Association edge ClassConfig class name.")
    forward: ClassConfigRelationshipSideLoadingStrategy | None = Field(
        default=None,
        description="Override applied to the forward/source relationship side.",
    )
    reverse: ClassConfigRelationshipSideLoadingStrategy | None = Field(
        default=None,
        description="Override applied to the reverse/target relationship side.",
    )

    @model_validator(mode="after")
    def _validate_scope(self):
        if bool(self.attribute) == bool(self.edge):
            raise ValueError(
                "ObjectConfigRelationshipSideLoadingEntry must define exactly one of 'attribute' or 'edge'"
            )
        return self


class ClassConfigRelationshipSideLoadingConfig(BaseModel):
    """Collection of loading overrides resolved in priority order."""

    entries: list[ClassConfigRelationshipSideLoadingEntry] = Field(default_factory=list)

    def resolve_for_attribute(
        self,
        *,
        namespace: Optional[str],
        class_name: Optional[str],
        attribute_name: Optional[str],
    ) -> ClassConfigRelationshipSideLoadingOverrides:
        if not attribute_name:
            return ClassConfigRelationshipSideLoadingOverrides()
        namespace_norm = _normalize(namespace)
        class_name_norm = _normalize(class_name)
        attribute_norm = _normalize(attribute_name)
        for entry in self.entries:
            if entry.attribute is None:
                continue
            if entry.namespace and _normalize(entry.namespace) != namespace_norm:
                continue
            if entry.class_name and _normalize(entry.class_name) != class_name_norm:
                continue
            if entry.attribute and _normalize(entry.attribute) != attribute_norm:
                continue
            return ClassConfigRelationshipSideLoadingOverrides(forward=entry.forward, reverse=entry.reverse)
        return ClassConfigRelationshipSideLoadingOverrides()

    def resolve_for_edge(
        self,
        *,
        namespace: Optional[str],
        edge_name: Optional[str],
    ) -> ClassConfigRelationshipSideLoadingOverrides:
        if not edge_name:
            return ClassConfigRelationshipSideLoadingOverrides()
        namespace_norm = _normalize(namespace)
        edge_norm = _normalize(edge_name)
        for entry in self.entries:
            if entry.edge is None:
                continue
            if entry.namespace and _normalize(entry.namespace) != namespace_norm:
                continue
            if _normalize(entry.edge) != edge_norm:
                continue
            return ClassConfigRelationshipSideLoadingOverrides(forward=entry.forward, reverse=entry.reverse)
        return ClassConfigRelationshipSideLoadingOverrides()


def _normalize(value: Optional[str]) -> Optional[str]:
    return value.lower() if value else None


__all__ = [
    "ClassConfigRelationshipSideLoadingStrategy",
    "ClassConfigRelationshipSideLoadingOverrides",
    "ClassConfigRelationshipSideLoadingEntry",
    "ClassConfigRelationshipSideLoadingConfig",
]
