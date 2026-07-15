from __future__ import annotations

from enum import Enum
from typing import cast

from aware_code.language import normalize_code_language
from aware_code.ontology.materialization import build_code_content_plan_from_text
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import CodeContentPlan
from aware_code_ontology.package.code_package import CodePackage


def resolve_code_package_text_language(
    *, code_package: CodePackage, language: CodeLanguage | str | Enum | None
) -> CodeLanguage:
    resolved_language = language or code_package.language
    if resolved_language is None:
        raise ValueError("CodePackage text upsert requires language when CodePackage.language is not set")
    return normalize_code_language(resolved_language)


def build_code_content_plan_copy_from_text(
    *, content_text: str, language: CodeLanguage | str | Enum
) -> CodeContentPlan:
    plan = build_code_content_plan_from_text(
        content_text=content_text,
        language=normalize_code_language(language),
    )
    return cast(
        CodeContentPlan,
        plan.model_copy(deep=True),
    )
