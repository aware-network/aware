from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from aware_code_ontology.code.code import Code
from aware_meta.fqn_resolver import FqnResolver, NamespacePath


@dataclass(frozen=True, slots=True)
class CodeLanguageServiceSnapshot:
    context: object
    fqn_resolver: FqnResolver
    codes_by_uri: dict[str, Code]
    text_by_uri: dict[str, str]
    uri_by_code_id: dict[UUID, str]
    namespace_by_code_id: dict[UUID, NamespacePath]
    rel_path_by_uri: dict[str, str]


__all__ = ["CodeLanguageServiceSnapshot"]
