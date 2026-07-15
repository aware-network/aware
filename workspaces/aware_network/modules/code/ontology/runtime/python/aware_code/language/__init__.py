from __future__ import annotations

from enum import Enum

from aware_code_ontology.code.code_enums import CodeLanguage


def normalize_code_language(value: CodeLanguage | str | Enum) -> CodeLanguage:
    if isinstance(value, CodeLanguage):
        return value
    if isinstance(value, Enum):
        return CodeLanguage(str(value.value))
    return CodeLanguage(str(value))
