# Kernel Graph Ontology
from uuid import UUID

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.enum.enum_option import EnumOption
from aware_code_ontology.enum.code_section_enum import CodeSectionEnum

from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.model_bootstrap import build_enum_config
from aware_meta.graph.config.stable_ids import (
    stable_enum_config_id,
    stable_object_config_graph_id,
    stable_object_config_graph_node_id,
    stable_enum_option_id,
)
from aware_utils.string_transform import to_snake_case


def standardize_enum_value(value_text: str) -> str:
    """
    Standardize enum value to lower_snake_case while preserving word boundaries.

    This ensures enum values stay canonical across .aware, SQL, Python, and Dart
    without relying on per-language casing conversions.

    Examples:
        'agent_process_thread' → 'agent_process_thread'
        'agentProcessThread' → 'agent_process_thread'
        'AgentProcessThread' → 'agent_process_thread'
        'AAL1' → 'aal1'
        'read' → 'read'
        'READ' → 'read'
        'FINISHED_FAILED' → 'finished_failed'
    """
    return to_snake_case(value_text)


def build_enum_config_from_code(*, code_section_enum: CodeSectionEnum, namespace: NamespacePath) -> EnumConfig:
    """
    Convert a CodeSectionEnum to an EnumConfig.

    NOTE: Standard is: Name in PascalCase and values in lower_snake_case.

    Args:
        code_section_enum: CodeSectionEnum to convert

    Returns:
        An EnumConfig instance
    """
    # Convert enum definitions to EnumConfig objects
    enum_fqn = namespace.fqn(code_section_enum.name)
    object_config_graph_id = stable_object_config_graph_id(
        fqn_prefix=namespace.package,
        language=CodeLanguage.aware.value,
    )
    object_config_graph_node_id = stable_object_config_graph_node_id(
        object_config_graph_id=object_config_graph_id,
        type="enum",
        node_key=enum_fqn,
    )
    enum_id: UUID = stable_enum_config_id(
        object_config_graph_node_id=object_config_graph_node_id,
        enum_fqn=enum_fqn,
    )
    enum_config = build_enum_config(
        enum_config_id=enum_id,
        object_config_graph_node_id=object_config_graph_node_id,
        enum_fqn=enum_fqn,
        name=code_section_enum.name,
        description=code_section_enum.description,
    )
    enum_config.code_section_enum_id = code_section_enum.id
    enum_config.code_section_enum = code_section_enum
    for enum_value in code_section_enum.code_section_enum_values:
        # Add enum options with both label and value
        value_text = enum_value.value
        # Remove surrounding quotes from SQL string literals ('value')
        if value_text.startswith("'") and value_text.endswith("'"):
            value_text = value_text[1:-1]
        # Standardize to lower_snake_case for deterministic cross-language conversion
        value_text = standardize_enum_value(value_text)

        # Create label from value (can be customized later)
        label_text = value_text

        option_id: UUID = stable_enum_option_id(enum_config_id=enum_id, value=value_text)
        enum_option = EnumOption(
            id=option_id,
            enum_config_id=enum_config.id,
            label=label_text,
            value=value_text,
            description=enum_value.description,
            position=enum_value.position,
        )
        enum_config.enum_options.append(enum_option)
    return enum_config
