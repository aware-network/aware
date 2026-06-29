from __future__ import annotations

from typing import cast

from aware_code.parse import build_code_content_plan
from aware_code.setup_language_plugins import setup_code_plugins
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import CodeContentPlan
from aware_code_ontology.package.code_package import CodePackage
from aware_code_ontology.package.code_package_code import CodePackageCode


def build_code_content_plan_from_text(
    *,
    content_text: str,
    language: CodeLanguage,
) -> CodeContentPlan:
    setup_code_plugins()
    return build_code_content_plan(
        content=content_text,
        language=language,
    )


async def apply_code_content_plan(
    *,
    code: Code,
    plan: CodeContentPlan,
) -> None:
    await code.apply_content_plan(
        plan=cast(
            CodeContentPlan,
            plan.model_copy(deep=True),
        )
    )


async def replace_code_content_from_text(
    *,
    code: Code,
    content_text: str,
    language: CodeLanguage | None = None,
) -> None:
    resolved_language = language or code.language
    if resolved_language is None:
        raise ValueError("Code.replace_content requires language when Code.language is not set")

    plan = build_code_content_plan_from_text(
        content_text=content_text,
        language=resolved_language,
    )
    await apply_code_content_plan(
        code=code,
        plan=plan,
    )


async def create_code_in_package_from_text(
    *,
    code_package: CodePackage,
    relative_path: str,
    content_text: str,
    language: CodeLanguage | None = None,
) -> CodePackageCode:
    resolved_language = language or code_package.language
    plan = build_code_content_plan_from_text(
        content_text=content_text,
        language=resolved_language,
    )
    return await code_package.create_code(
        relative_path=relative_path,
        plan=cast(
            CodeContentPlan,
            plan.model_copy(deep=True),
        ),
    )


async def upsert_code_in_package_from_text(
    *,
    code_package: CodePackage,
    relative_path: str,
    content_text: str,
    language: CodeLanguage | None = None,
) -> CodePackageCode:
    resolved_language = language or code_package.language
    plan = build_code_content_plan_from_text(
        content_text=content_text,
        language=resolved_language,
    )
    return await code_package.upsert_code(
        relative_path=relative_path,
        plan=cast(
            CodeContentPlan,
            plan.model_copy(deep=True),
        ),
    )
