"""Annotation compilation protocol (optional override hook).

The canonical pipeline is:
  Grammar -> CodeSectionAnnotation (primitive)
  Meta (generic) -> CodeSectionAnnotation* views + ObjectConfigGraphAnnotation wrappers

MetaLanguagePlugin may optionally override compilation via this protocol, but by default
the canonical generic compiler is used.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from aware_code_ontology.annotation.code_section_annotation import CodeSectionAnnotation
from aware_meta_ontology.graph.config.object_config_graph_annotation import (
    ObjectConfigGraphAnnotation,
)

from aware_meta.fqn_resolver import FqnResolver


class MetaAnnotationCompiler(Protocol):
    def __call__(
        self,
        code_section_annotations: list[CodeSectionAnnotation],
        fqn_resolver: FqnResolver,
        *,
        object_config_graph_id: UUID | None = None,
    ) -> list[ObjectConfigGraphAnnotation]: ...


__all__ = [
    "MetaAnnotationCompiler",
]
