# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_CODE = uuid5(NAMESPACE_URL, "aware://code/v1")


def stable_code_id(*, code_package_code_id: UUID, relative_path: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_package_code_id, relative_path"""

    relative_path_norm = (relative_path or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code:{code_package_code_id}:{relative_path_norm}")


def stable_code_module_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_module:{name_norm}")


def stable_code_module_code_package_id(*, code_package_id: UUID, code_module_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_package_id, code_module_id"""

    return uuid5(NS_CODE, f"aware:code_module_code_package:{code_package_id}:{code_module_id}")


def stable_code_module_dependence_id(*, code_module_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_module_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_module_dependence:{code_module_id}:{name_norm}")


def stable_code_package_id(*, code_package_config_id: UUID, package_name: str, language: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_package_config_id, package_name, language"""

    package_name_norm = (package_name or "").casefold().strip()
    language_norm = (language or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_package:{code_package_config_id}:{package_name_norm}:{language_norm}")


def stable_code_package_artifact_id(*, code_package_id: UUID, output_key: str, artifact_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_package_id, output_key, artifact_key"""

    output_key_norm = (output_key or "").casefold().strip()
    artifact_key_norm = (artifact_key or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_package_artifact:{code_package_id}:{output_key_norm}:{artifact_key_norm}")


def stable_code_package_code_id(*, code_package_id: UUID, relative_path: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_package_id, relative_path"""

    relative_path_norm = (relative_path or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_package_code:{code_package_id}:{relative_path_norm}")


def stable_code_package_config_id(*, config_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: config_key"""

    config_key_norm = (config_key or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_package_config:{config_key_norm}")


def stable_code_package_config_input_id(*, code_package_config_id: UUID, input_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_package_config_id, input_key"""

    input_key_norm = (input_key or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_package_config_input:{code_package_config_id}:{input_key_norm}")


def stable_code_package_config_output_id(*, code_package_config_id: UUID, output_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_package_config_id, output_key"""

    output_key_norm = (output_key or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_package_config_output:{code_package_config_id}:{output_key_norm}")


def stable_code_package_config_runtime_context_id(*, code_package_config_id: UUID, context_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_package_config_id, context_key"""

    context_key_norm = (context_key or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_package_config_runtime_context:{code_package_config_id}:{context_key_norm}")


def stable_code_package_delta_producer_id(*, code_package_id: UUID, provider_key: str, producer_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_package_id, provider_key, producer_key"""

    provider_key_norm = (provider_key or "").casefold().strip()
    producer_key_norm = (producer_key or "").casefold().strip()
    return uuid5(
        NS_CODE, f"aware:code_package_delta_producer:{code_package_id}:{provider_key_norm}:{producer_key_norm}"
    )


def stable_code_package_delta_producer_code_id(
    *, code_package_code_id: UUID, code_package_delta_producer_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_package_code_id, code_package_delta_producer_id"""

    return uuid5(
        NS_CODE, f"aware:code_package_delta_producer_code:{code_package_code_id}:{code_package_delta_producer_id}"
    )


def stable_code_package_test_id(*, code_package_id: UUID, code_test_id: UUID, relative_path: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_package_id, code_test_id, relative_path"""

    relative_path_norm = (relative_path or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_package_test:{code_package_id}:{code_test_id}:{relative_path_norm}")


def stable_code_package_test_framework_id(*, code_test_framework_id: UUID, code_package_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_test_framework_id, code_package_id"""

    return uuid5(NS_CODE, f"aware:code_package_test_framework:{code_test_framework_id}:{code_package_id}")


def stable_code_package_test_run_id(*, code_package_test_id: UUID, run_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_package_test_id, run_key"""

    run_key_norm = (run_key or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_package_test_run:{code_package_test_id}:{run_key_norm}")


def stable_code_primitive_type_id(*, signature: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: signature"""

    signature_norm = (signature or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_primitive_type:{signature_norm}")


def stable_code_primitive_type_element_type_id(*, code_primitive_type_id: UUID, position: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_primitive_type_id, position"""

    return uuid5(NS_CODE, f"aware:code_primitive_type_element_type:{code_primitive_type_id}:{position}")


def stable_code_primitive_type_union_type_id(*, code_primitive_type_id: UUID, position: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_primitive_type_id, position"""

    return uuid5(NS_CODE, f"aware:code_primitive_type_union_type:{code_primitive_type_id}:{position}")


def stable_code_section_id(*, code_id: UUID, section_key: str, type: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_id, section_key, type"""

    section_key_norm = (section_key or "").casefold().strip()
    type_norm = (type or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_section:{code_id}:{section_key_norm}:{type_norm}")


def stable_code_section_annotation_id(*, code_section_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_id"""

    return uuid5(NS_CODE, f"aware:code_section_annotation:{code_section_id}")


def stable_code_section_attribute_id(*, code_section_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_id"""

    return uuid5(NS_CODE, f"aware:code_section_attribute:{code_section_id}")


def stable_code_section_binding_id(*, code_section_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_id"""

    return uuid5(NS_CODE, f"aware:code_section_binding:{code_section_id}")


def stable_code_section_binding_map_id(*, code_section_binding_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_binding_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_section_binding_map:{code_section_binding_id}:{name_norm}")


def stable_code_section_class_id(*, code_section_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_id"""

    return uuid5(NS_CODE, f"aware:code_section_class:{code_section_id}")


def stable_code_section_class_attribute_id(*, code_section_class_id: UUID, code_section_attribute_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_class_id, code_section_attribute_id"""

    return uuid5(NS_CODE, f"aware:code_section_class_attribute:{code_section_class_id}:{code_section_attribute_id}")


def stable_code_section_class_base_id(*, code_section_class_id: UUID, base_ref: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_class_id, base_ref"""

    base_ref_norm = (base_ref or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_section_class_base:{code_section_class_id}:{base_ref_norm}")


def stable_code_section_class_function_id(*, code_section_class_id: UUID, code_section_function_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_class_id, code_section_function_id"""

    return uuid5(NS_CODE, f"aware:code_section_class_function:{code_section_class_id}:{code_section_function_id}")


def stable_code_section_comment_id(*, code_section_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_id"""

    return uuid5(NS_CODE, f"aware:code_section_comment:{code_section_id}")


def stable_code_section_comment_content_id(*, code_section_comment_id: UUID, position: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_comment_id, position"""

    return uuid5(NS_CODE, f"aware:code_section_comment_content:{code_section_comment_id}:{position}")


def stable_code_section_decorator_id(*, code_section_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_id"""

    return uuid5(NS_CODE, f"aware:code_section_decorator:{code_section_id}")


def stable_code_section_decorator_expression_id(*, code_section_decorator_id: UUID, position: int = 0) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_decorator_id, position"""

    return uuid5(NS_CODE, f"aware:code_section_decorator_expression:{code_section_decorator_id}:{position}")


def stable_code_section_enum_id(*, code_section_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_id"""

    return uuid5(NS_CODE, f"aware:code_section_enum:{code_section_id}")


def stable_code_section_enum_value_id(*, code_section_id: UUID, value: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_id, value"""

    value_norm = (value or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_section_enum_value:{code_section_id}:{value_norm}")


def stable_code_section_expression_id(*, code_section_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_id"""

    return uuid5(NS_CODE, f"aware:code_section_expression:{code_section_id}")


def stable_code_section_function_id(*, code_section_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_id"""

    return uuid5(NS_CODE, f"aware:code_section_function:{code_section_id}")


def stable_code_section_function_attribute_id(
    *, code_section_function_id: UUID, code_section_attribute_id: UUID
) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_function_id, code_section_attribute_id"""

    return uuid5(
        NS_CODE, f"aware:code_section_function_attribute:{code_section_function_id}:{code_section_attribute_id}"
    )


def stable_code_section_import_id(*, code_section_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_id"""

    return uuid5(NS_CODE, f"aware:code_section_import:{code_section_id}")


def stable_code_section_import_name_id(*, code_section_import_id: UUID, name_text: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_import_id, name_text"""

    name_text_norm = (name_text or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_section_import_name:{code_section_import_id}:{name_text_norm}")


def stable_code_section_mirror_id(*, code_section_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_id"""

    return uuid5(NS_CODE, f"aware:code_section_mirror:{code_section_id}")


def stable_code_section_projection_id(*, code_section_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_id"""

    return uuid5(NS_CODE, f"aware:code_section_projection:{code_section_id}")


def stable_code_section_projection_edge_id(*, code_section_projection_id: UUID, member: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_projection_id, member"""

    member_norm = (member or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_section_projection_edge:{code_section_projection_id}:{member_norm}")


def stable_code_section_projection_view_id(*, code_section_projection_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_section_projection_id"""

    return uuid5(NS_CODE, f"aware:code_section_projection_view:{code_section_projection_id}")


def stable_code_semantic_contract_profile_id(*, profile_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: profile_key"""

    profile_key_norm = (profile_key or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_semantic_contract_profile:{profile_key_norm}")


def stable_code_semantic_contract_profile_import_id(
    *, code_semantic_contract_profile_id: UUID, imported_profile_id: UUID, import_key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_semantic_contract_profile_id, imported_profile_id, import_key"""

    import_key_norm = (import_key or "").casefold().strip()
    return uuid5(
        NS_CODE,
        f"aware:code_semantic_contract_profile_import:{code_semantic_contract_profile_id}:{imported_profile_id}:{import_key_norm}",
    )


def stable_code_semantic_contract_profile_package_id(
    *, code_package_id: UUID, semantic_contract_profile_id: UUID, profile_package_key: str
) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_package_id, semantic_contract_profile_id, profile_package_key"""

    profile_package_key_norm = (profile_package_key or "").casefold().strip()
    return uuid5(
        NS_CODE,
        f"aware:code_semantic_contract_profile_package:{code_package_id}:{semantic_contract_profile_id}:{profile_package_key_norm}",
    )


def stable_code_semantic_contract_runtime_import_id(
    *,
    code_semantic_contract_profile_package_id: UUID,
    import_role: str = "semantic_contract",
    provider_key: str,
    semantic_contract_module: str,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_semantic_contract_profile_package_id, import_role, provider_key, semantic_contract_module"""

    import_role_norm = (import_role or "").casefold().strip() or "semantic_contract"
    provider_key_norm = (provider_key or "").casefold().strip()
    semantic_contract_module_norm = (semantic_contract_module or "").casefold().strip()
    return uuid5(
        NS_CODE,
        f"aware:code_semantic_contract_runtime_import:{code_semantic_contract_profile_package_id}:{import_role_norm}:{provider_key_norm}:{semantic_contract_module_norm}",
    )


def stable_code_semantic_package_binding_id(
    *,
    code_semantic_provider_registration_id: UUID,
    code_package_id: UUID,
    module_package_id: str,
    semantic_contract_name: str,
    semantic_contract_role: str,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_semantic_provider_registration_id, code_package_id, module_package_id, semantic_contract_name, semantic_contract_role"""

    module_package_id_norm = (module_package_id or "").casefold().strip()
    semantic_contract_name_norm = (semantic_contract_name or "").casefold().strip()
    semantic_contract_role_norm = (semantic_contract_role or "").casefold().strip()
    return uuid5(
        NS_CODE,
        f"aware:code_semantic_package_binding:{code_semantic_provider_registration_id}:{code_package_id}:{module_package_id_norm}:{semantic_contract_name_norm}:{semantic_contract_role_norm}",
    )


def stable_code_semantic_provider_registration_id(*, code_module_id: UUID, provider_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_module_id, provider_key"""

    provider_key_norm = (provider_key or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_semantic_provider_registration:{code_module_id}:{provider_key_norm}")


def stable_code_test_id(*, code_id: UUID, framework_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_id, framework_id"""

    return uuid5(NS_CODE, f"aware:code_test:{code_id}:{framework_id}")


def stable_code_test_framework_id(*, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_test_framework:{name_norm}")


def stable_code_test_unit_id(*, code_test_id: UUID, code_section_id: UUID, unit_key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_test_id, code_section_id, unit_key"""

    unit_key_norm = (unit_key or "").casefold().strip()
    return uuid5(NS_CODE, f"aware:code_test_unit:{code_test_id}:{code_section_id}:{unit_key_norm}")


def stable_code_test_unit_run_id(*, code_package_test_run_id: UUID, code_test_unit_id: UUID) -> UUID:
    """Compiler-generated from class-attribute identity keys: code_package_test_run_id, code_test_unit_id"""

    return uuid5(NS_CODE, f"aware:code_test_unit_run:{code_package_test_run_id}:{code_test_unit_id}")


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "08033a11-9e49-53da-953d-69ee9957d60e": ("stable_code_id", ("code_package_code_id", "relative_path")),
    "09b1ce0f-f833-50fe-a7ac-7d8c56740cd3": (
        "stable_code_package_config_output_id",
        ("code_package_config_id", "output_key"),
    ),
    "17d68c10-ff12-50c6-87b0-b6eb17d7f4ee": (
        "stable_code_semantic_provider_registration_id",
        ("code_module_id", "provider_key"),
    ),
    "1901a2f0-0668-55f9-8a5d-44803640bcbf": (
        "stable_code_section_comment_content_id",
        ("code_section_comment_id", "position"),
    ),
    "24ca9328-ee2c-5722-846e-8ade433dced0": (
        "stable_code_primitive_type_union_type_id",
        ("code_primitive_type_id", "position"),
    ),
    "2d81d51c-a191-5801-a3d2-f0e281f79578": (
        "stable_code_package_id",
        ("code_package_config_id", "package_name", "language"),
    ),
    "2eee02e1-b6cd-5f9b-8a85-e79f45c81347": (
        "stable_code_section_projection_edge_id",
        ("code_section_projection_id", "member"),
    ),
    "40210d15-5a8c-55c8-8538-e2b0abaea17c": ("stable_code_section_binding_map_id", ("code_section_binding_id", "name")),
    "43c16ea8-3d4e-53f1-a624-78e35b9b150e": (
        "stable_code_semantic_contract_profile_import_id",
        ("code_semantic_contract_profile_id", "imported_profile_id", "import_key"),
    ),
    "499bb348-e06d-543d-b99b-b35a670eafdc": ("stable_code_section_binding_id", ("code_section_id",)),
    "54a68390-817e-5570-8663-00442fe3b105": (
        "stable_code_module_code_package_id",
        ("code_package_id", "code_module_id"),
    ),
    "54c9bdb7-c956-5286-b3a8-682677347090": (
        "stable_code_section_decorator_expression_id",
        ("code_section_decorator_id", "position"),
    ),
    "56e0131f-9f1a-5db0-9f59-8eb78e369f0c": ("stable_code_section_enum_value_id", ("code_section_id", "value")),
    "64e125db-f4df-59cd-ac66-5ef2f53df6f8": (
        "stable_code_test_unit_id",
        ("code_test_id", "code_section_id", "unit_key"),
    ),
    "65e7c135-e48a-5044-8206-972b08f10102": ("stable_code_primitive_type_id", ("signature",)),
    "70607493-0034-52cb-8cce-dde32057c1ab": ("stable_code_package_config_id", ("config_key",)),
    "719985d1-d20b-58fa-bad7-2e382b0dd4e7": ("stable_code_test_framework_id", ("name",)),
    "75d8aa0d-09db-5103-b55d-d4c02734d6f8": (
        "stable_code_test_unit_run_id",
        ("code_package_test_run_id", "code_test_unit_id"),
    ),
    "79e7c979-b53d-590d-a0c4-5ae9b3c0855d": ("stable_code_section_mirror_id", ("code_section_id",)),
    "7d383e9d-f8cf-5d19-aeb2-d2de1aa674e5": ("stable_code_section_enum_id", ("code_section_id",)),
    "8185614d-1e5f-50b5-bfd8-9adff184bd56": ("stable_code_section_attribute_id", ("code_section_id",)),
    "89f72fe5-e174-59f5-98e2-a414fd5e1df0": ("stable_code_section_id", ("code_id", "section_key", "type")),
    "8bdaf849-747b-5f54-8da5-7eade5dd0faa": ("stable_code_section_comment_id", ("code_section_id",)),
    "8d12567a-a166-5dfb-a30a-00bbb9122301": ("stable_code_section_function_id", ("code_section_id",)),
    "8de0762a-f9e7-58e7-ae74-a489f5dab4d5": (
        "stable_code_package_test_id",
        ("code_package_id", "code_test_id", "relative_path"),
    ),
    "94b36386-5ad5-50df-9f34-7f8deccacebe": ("stable_code_section_import_id", ("code_section_id",)),
    "94eb99a0-c78e-54cc-93f3-88fe55d78202": ("stable_code_module_id", ("name",)),
    "9bb25f70-bc6d-591f-bbb1-265abbdc1a2d": (
        "stable_code_primitive_type_element_type_id",
        ("code_primitive_type_id", "position"),
    ),
    "9c77698f-6562-5d0c-a64f-9fb24ced7c2f": (
        "stable_code_package_delta_producer_id",
        ("code_package_id", "provider_key", "producer_key"),
    ),
    "a372216f-2df0-546f-9a52-2185d7d7953e": ("stable_code_section_annotation_id", ("code_section_id",)),
    "a6a87e97-1b11-5d3a-b507-babef7190f25": ("stable_code_section_expression_id", ("code_section_id",)),
    "a78c1acb-e6d3-5b87-83fd-f3f2e3ed4708": ("stable_code_semantic_contract_profile_id", ("profile_key",)),
    "aa341420-8bf3-58d7-ac69-5f01fc49313e": ("stable_code_section_decorator_id", ("code_section_id",)),
    "ada356a8-38a4-568d-8993-1906c58f2ada": ("stable_code_section_class_id", ("code_section_id",)),
    "b1bac4aa-7ab9-5fd2-a13b-4da38bdc5576": (
        "stable_code_package_config_input_id",
        ("code_package_config_id", "input_key"),
    ),
    "b36b975c-a474-5b7c-a9d4-7954ea186808": (
        "stable_code_package_config_runtime_context_id",
        ("code_package_config_id", "context_key"),
    ),
    "b62ce2d8-813e-5147-abb6-15f8028d0a1f": ("stable_code_module_dependence_id", ("code_module_id", "name")),
    "b6e7e841-be1a-559a-a875-9e4f8b37915f": (
        "stable_code_semantic_contract_runtime_import_id",
        ("code_semantic_contract_profile_package_id", "import_role", "provider_key", "semantic_contract_module"),
    ),
    "bc1502c0-e635-51b5-95f0-421f0dd00cab": (
        "stable_code_semantic_contract_profile_package_id",
        ("code_package_id", "semantic_contract_profile_id", "profile_package_key"),
    ),
    "c3de4ab3-0445-53ff-8b1d-af6f224ffed1": (
        "stable_code_package_artifact_id",
        ("code_package_id", "output_key", "artifact_key"),
    ),
    "c9dffc2b-dcd3-5c6c-a620-4dcac33ce410": (
        "stable_code_package_delta_producer_code_id",
        ("code_package_code_id", "code_package_delta_producer_id"),
    ),
    "cab5c1fd-0a4f-58d7-ac85-9d3ca1bb34b3": (
        "stable_code_section_class_base_id",
        ("code_section_class_id", "base_ref"),
    ),
    "d0590187-6b97-5abd-b5ff-d8149d0b5a78": (
        "stable_code_section_import_name_id",
        ("code_section_import_id", "name_text"),
    ),
    "d64b6151-70f3-587b-9ea4-ff29fac0f765": ("stable_code_package_code_id", ("code_package_id", "relative_path")),
    "dd80e22d-36cc-5ade-a9fb-1665ab2ad3a5": (
        "stable_code_semantic_package_binding_id",
        (
            "code_semantic_provider_registration_id",
            "code_package_id",
            "module_package_id",
            "semantic_contract_name",
            "semantic_contract_role",
        ),
    ),
    "ee3a2837-bb0c-5862-be63-e8605badc69a": ("stable_code_package_test_run_id", ("code_package_test_id", "run_key")),
    "fc24c11c-d977-5eff-a51e-261374dd878d": (
        "stable_code_package_test_framework_id",
        ("code_test_framework_id", "code_package_id"),
    ),
    "fdb9f534-220c-5507-98f2-a5a2e11a3559": ("stable_code_test_id", ("code_id", "framework_id")),
    "ff8cab24-38f3-5b75-b4f9-c800bb499556": ("stable_code_section_projection_id", ("code_section_id",)),
}

__all__ = [
    "stable_code_id",
    "stable_code_module_id",
    "stable_code_module_code_package_id",
    "stable_code_module_dependence_id",
    "stable_code_package_id",
    "stable_code_package_artifact_id",
    "stable_code_package_code_id",
    "stable_code_package_config_id",
    "stable_code_package_config_input_id",
    "stable_code_package_config_output_id",
    "stable_code_package_config_runtime_context_id",
    "stable_code_package_delta_producer_id",
    "stable_code_package_delta_producer_code_id",
    "stable_code_package_test_id",
    "stable_code_package_test_framework_id",
    "stable_code_package_test_run_id",
    "stable_code_primitive_type_id",
    "stable_code_primitive_type_element_type_id",
    "stable_code_primitive_type_union_type_id",
    "stable_code_section_id",
    "stable_code_section_annotation_id",
    "stable_code_section_attribute_id",
    "stable_code_section_binding_id",
    "stable_code_section_binding_map_id",
    "stable_code_section_class_id",
    "stable_code_section_class_attribute_id",
    "stable_code_section_class_base_id",
    "stable_code_section_class_function_id",
    "stable_code_section_comment_id",
    "stable_code_section_comment_content_id",
    "stable_code_section_decorator_id",
    "stable_code_section_decorator_expression_id",
    "stable_code_section_enum_id",
    "stable_code_section_enum_value_id",
    "stable_code_section_expression_id",
    "stable_code_section_function_id",
    "stable_code_section_function_attribute_id",
    "stable_code_section_import_id",
    "stable_code_section_import_name_id",
    "stable_code_section_mirror_id",
    "stable_code_section_projection_id",
    "stable_code_section_projection_edge_id",
    "stable_code_section_projection_view_id",
    "stable_code_semantic_contract_profile_id",
    "stable_code_semantic_contract_profile_import_id",
    "stable_code_semantic_contract_profile_package_id",
    "stable_code_semantic_contract_runtime_import_id",
    "stable_code_semantic_package_binding_id",
    "stable_code_semantic_provider_registration_id",
    "stable_code_test_id",
    "stable_code_test_framework_id",
    "stable_code_test_unit_id",
    "stable_code_test_unit_run_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
