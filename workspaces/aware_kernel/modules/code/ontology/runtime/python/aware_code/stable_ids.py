"""Code stable-id exports (compiler-owned formulas)."""

from __future__ import annotations

from typing import Callable, cast
from uuid import NAMESPACE_URL, UUID, uuid5

import aware_code_ontology.stable_ids as _ontology_stable_ids  # type: ignore[import-not-found]
from aware_code_ontology.code.code_enums import CodeLanguage

NS_CODE = uuid5(NAMESPACE_URL, "aware://code/v1")


def _enum_text(value: object) -> str:
    return str(getattr(value, "value", value) or "").casefold().strip()


def code_package_source_config_key(
    *,
    manifest_kind: object,
    surface: object,
) -> str:
    return f"source:{_enum_text(manifest_kind)}:{_enum_text(surface)}"


def code_package_generated_config_key(
    *,
    materialization_source: str,
    renderer_kind: str | None,
    language: object,
    surface: object,
    manifest_kind: object,
) -> str:
    return (
        "generated:"
        f"{(materialization_source or '').casefold().strip()}:"
        f"{(renderer_kind or '').casefold().strip()}:"
        f"{_enum_text(language)}:"
        f"{_enum_text(surface)}:"
        f"{_enum_text(manifest_kind)}"
    )


def stable_code_id(
    *,
    code_package_code_id: UUID | None = None,
    code_package_id: UUID | None = None,
    relative_path: str | None = None,
    key: str | None = None,
) -> UUID:
    if code_package_code_id is not None:
        if relative_path is None:
            raise TypeError(
                "stable_code_id requires relative_path when code_package_code_id is provided"
            )
        relative_path_norm = (relative_path or "").casefold().strip()
        return uuid5(NS_CODE, f"aware:code:{code_package_code_id}:{relative_path_norm}")
    if code_package_id is not None:
        if relative_path is None:
            raise TypeError(
                "stable_code_id requires relative_path when code_package_id is provided"
            )
        relative_path_norm = (relative_path or "").casefold().strip()
        return uuid5(NS_CODE, f"aware:code:{code_package_id}:{relative_path_norm}")
    if key is not None:
        key_norm = (key or "").casefold().strip()
        return uuid5(NS_CODE, f"aware:code:{key_norm}")
    if relative_path is not None:
        relative_path_norm = (relative_path or "").casefold().strip()
        return uuid5(NS_CODE, f"aware:code:{relative_path_norm}")
    raise TypeError(
        "stable_code_id requires key, code_package_code_id + relative_path, "
        + "or code_package_id + relative_path"
    )


stable_code_module_id = cast(
    Callable[..., UUID], _ontology_stable_ids.stable_code_module_id
)


def stable_code_module_code_package_id(
    *, code_module_id: UUID, code_package_id: UUID
) -> UUID:
    return uuid5(
        NS_CODE, f"aware:code_module_code_package:{code_package_id}:{code_module_id}"
    )


stable_code_module_dependence_id = cast(
    Callable[..., UUID], _ontology_stable_ids.stable_code_module_dependence_id
)


def stable_code_package_config_id(*, config_key: str) -> UUID:
    config_key_norm = (config_key or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_package_config:{config_key_norm}")


def stable_code_package_id(
    *,
    package_name: str,
    language: CodeLanguage | str,
    code_package_config_id: UUID | None = None,
) -> UUID:
    package_name_norm = (package_name or "").casefold().strip()
    language_value = language.value if isinstance(language, CodeLanguage) else language
    language_norm = str(language_value or "").casefold().strip()
    if code_package_config_id is None:
        return uuid5(NS_CODE, f"aware:code_package:{package_name_norm}:{language_norm}")
    return uuid5(
        NS_CODE,
        f"aware:code_package:{code_package_config_id}:{package_name_norm}:{language_norm}",
    )


def stable_code_package_code_id(*, code_package_id: UUID, relative_path: str) -> UUID:
    relative_path_norm = (relative_path or "").casefold().strip()
    return uuid5(
        NS_CODE, f"aware:code_package_code:{code_package_id}:{relative_path_norm}"
    )


stable_code_package_artifact_id = cast(
    Callable[..., UUID], _ontology_stable_ids.stable_code_package_artifact_id
)
stable_code_package_test_id = cast(
    Callable[..., UUID], _ontology_stable_ids.stable_code_package_test_id
)
stable_code_package_config_input_id = cast(
    Callable[..., UUID], _ontology_stable_ids.stable_code_package_config_input_id
)
stable_code_package_config_output_id = cast(
    Callable[..., UUID], _ontology_stable_ids.stable_code_package_config_output_id
)
stable_code_package_config_runtime_context_id = cast(
    Callable[..., UUID],
    _ontology_stable_ids.stable_code_package_config_runtime_context_id,
)
stable_code_package_delta_producer_id = cast(
    Callable[..., UUID],
    _ontology_stable_ids.stable_code_package_delta_producer_id,
)
stable_code_package_delta_producer_code_id = cast(
    Callable[..., UUID],
    _ontology_stable_ids.stable_code_package_delta_producer_code_id,
)
stable_code_package_test_framework_id = cast(
    Callable[..., UUID],
    _ontology_stable_ids.stable_code_package_test_framework_id,
)
stable_code_package_test_run_id = cast(
    Callable[..., UUID], _ontology_stable_ids.stable_code_package_test_run_id
)
stable_code_primitive_type_id = cast(
    Callable[..., UUID], _ontology_stable_ids.stable_code_primitive_type_id
)
stable_code_primitive_type_element_type_id = cast(
    Callable[..., UUID],
    _ontology_stable_ids.stable_code_primitive_type_element_type_id,
)
stable_code_primitive_type_union_type_id = cast(
    Callable[..., UUID],
    _ontology_stable_ids.stable_code_primitive_type_union_type_id,
)
stable_code_semantic_contract_profile_id = cast(
    Callable[..., UUID],
    _ontology_stable_ids.stable_code_semantic_contract_profile_id,
)
stable_code_semantic_contract_profile_import_id = cast(
    Callable[..., UUID],
    _ontology_stable_ids.stable_code_semantic_contract_profile_import_id,
)
stable_code_semantic_package_binding_id = cast(
    Callable[..., UUID],
    _ontology_stable_ids.stable_code_semantic_package_binding_id,
)
stable_code_semantic_provider_registration_id = cast(
    Callable[..., UUID],
    _ontology_stable_ids.stable_code_semantic_provider_registration_id,
)
stable_code_section_id = cast(
    Callable[..., UUID], _ontology_stable_ids.stable_code_section_id
)
stable_code_section_annotation_id = cast(
    Callable[..., UUID], _ontology_stable_ids.stable_code_section_annotation_id
)
stable_code_section_import_id = cast(
    Callable[..., UUID], _ontology_stable_ids.stable_code_section_import_id
)
stable_code_section_import_name_id = cast(
    Callable[..., UUID], _ontology_stable_ids.stable_code_section_import_name_id
)
stable_code_test_id = cast(
    Callable[..., UUID], _ontology_stable_ids.stable_code_test_id
)
stable_code_test_framework_id = cast(
    Callable[..., UUID], _ontology_stable_ids.stable_code_test_framework_id
)
stable_code_test_unit_id = cast(
    Callable[..., UUID], _ontology_stable_ids.stable_code_test_unit_id
)
stable_code_test_unit_run_id = cast(
    Callable[..., UUID], _ontology_stable_ids.stable_code_test_unit_run_id
)


__all__ = [
    "stable_code_id",
    "code_package_generated_config_key",
    "code_package_source_config_key",
    "stable_code_primitive_type_id",
    "stable_code_primitive_type_element_type_id",
    "stable_code_primitive_type_union_type_id",
    "stable_code_semantic_contract_profile_id",
    "stable_code_semantic_contract_profile_import_id",
    "stable_code_semantic_package_binding_id",
    "stable_code_semantic_provider_registration_id",
    "stable_code_module_id",
    "stable_code_module_code_package_id",
    "stable_code_module_dependence_id",
    "stable_code_package_config_id",
    "stable_code_package_config_input_id",
    "stable_code_package_config_output_id",
    "stable_code_package_config_runtime_context_id",
    "stable_code_package_id",
    "stable_code_package_artifact_id",
    "stable_code_package_code_id",
    "stable_code_package_delta_producer_id",
    "stable_code_package_delta_producer_code_id",
    "stable_code_package_test_id",
    "stable_code_package_test_framework_id",
    "stable_code_package_test_run_id",
    "stable_code_section_id",
    "stable_code_section_annotation_id",
    "stable_code_section_import_id",
    "stable_code_section_import_name_id",
    "stable_code_test_id",
    "stable_code_test_framework_id",
    "stable_code_test_unit_id",
    "stable_code_test_unit_run_id",
]
