from uuid import UUID

# Code Ontology
from aware_code_ontology.class_.code_section_class import CodeSectionClass

# Code Runtime
from aware_code.primitive_codec import CodePrimitiveCodec
from aware_code.type_descriptor_adapter import CodeTypeDescriptorAdapter

# Meta Ontology
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_enums import ClassValueMode

# Meta Runtime
from aware_meta.attribute.config.builder import build_attribute_config_from_code
from aware_meta.function.config.builder import build_function_config_from_code
from aware_meta.fqn_resolver import FqnResolver, FqnScope
from aware_meta.graph.config.stable_ids import (
    stable_class_config_attribute_config_id,
    stable_class_config_function_config_id,
)
from aware_meta.function.verb_policy import is_constructor_verb

# Aware Utils
from aware_utils.logging import logger


def build_class_config_from_code(
    code_section_class: CodeSectionClass,
    parent_class_id: UUID | None = None,
    *,
    value_mode: ClassValueMode = ClassValueMode.graph_ref,
    class_fqn: str | None = None,
    object_config_graph_node_id: UUID | None = None,
) -> ClassConfig:
    """
    Convert a CodeSectionClass to a ClassConfig.

    NOTE: This does not build attribute and function configs for the class config.
    Use build_class_config_attribute_configs and build_class_config_function_configs to build attribute and function configs for the class config.
    """
    is_base = parent_class_id is None
    if value_mode == ClassValueMode.inline_value and (code_section_class.is_edge):
        raise ValueError(
            "INLINE_VALUE classes cannot be edge: "
            f"class={code_section_class.name} is_edge={code_section_class.is_edge}"
        )

    if object_config_graph_node_id is not None:
        return ClassConfig(
            class_fqn=class_fqn or code_section_class.name,
            object_config_graph_node_id=object_config_graph_node_id,
            name=code_section_class.name,
            description=code_section_class.description,
            parent_class_id=parent_class_id,
            code_section_class_id=code_section_class.id,
            code_section_class=code_section_class,
            is_base=is_base,
            is_edge=code_section_class.is_edge,
            value_mode=value_mode,
        )

    return ClassConfig(
        class_fqn=class_fqn or code_section_class.name,
        name=code_section_class.name,
        description=code_section_class.description,
        parent_class_id=parent_class_id,
        code_section_class_id=code_section_class.id,
        code_section_class=code_section_class,
        is_base=is_base,
        is_edge=code_section_class.is_edge,
        value_mode=value_mode,
    )


def build_class_config_attribute_configs(
    class_config: ClassConfig,
    code_section_class: CodeSectionClass,
    fqn_scope: FqnScope,
    primitive_codec: CodePrimitiveCodec,
    type_descriptor_adapter: CodeTypeDescriptorAdapter,
) -> list[ClassConfigAttributeConfig]:
    """
    Build attribute configs for a class config.

    Args:
        class_config: Class config to build attribute configs for
        code_section_class: Code section class to build attribute configs from
        fqn_scope: FQN scope
        primitive_codec: Primitive codec
        type_descriptor_adapter: Type descriptor adapter
    """
    class_config_attribute_configs: list[ClassConfigAttributeConfig] = []
    class_fqn = fqn_scope.namespace.fqn(class_config.name)
    # Sort code section attributes and functions by position
    code_section_class_attributes = sorted(code_section_class.code_section_class_attributes, key=lambda x: x.position)
    for code_section_class_attribute in code_section_class_attributes:
        code_section_attribute = code_section_class_attribute.code_section_attribute
        # Determine visibility first so we can short-circuit private class attributes
        is_public = code_section_attribute.is_public
        if not is_public:
            # Private/protected attributes are implementation details and should not surface in OCG metadata
            continue

        # Convert CodeSectionAttribute to AttributeConfig
        attr_config = build_attribute_config_from_code(
            fqn_scope=fqn_scope,
            primitive_codec=primitive_codec,
            type_descriptor_adapter=type_descriptor_adapter,
            code_section_attribute=code_section_attribute,
            is_virtual=False,
            owner_key=class_fqn,
        )
        class_attr_config = ClassConfigAttributeConfig(
            id=stable_class_config_attribute_config_id(
                class_config_id=class_config.id,
                attribute_config_id=attr_config.id,
            ),
            class_config_id=class_config.id,
            attribute_config=attr_config,
            attribute_config_id=attr_config.id,
            name=attr_config.name,
            position=code_section_class_attribute.position,
            is_identity_key=bool(attr_config.is_primary),
        )
        class_config_attribute_configs.append(class_attr_config)
    return class_config_attribute_configs


def build_class_config_function_configs(
    class_config: ClassConfig,
    code_section_class: CodeSectionClass,
    fqn_scope: FqnScope,
    primitive_codec: CodePrimitiveCodec,
    type_descriptor_adapter: CodeTypeDescriptorAdapter,
) -> list[ClassConfigFunctionConfig]:
    """
    Build function configs for a class config.

    Args:
        class_config: Class config to build function configs for
        code_section_class: Code section class to build function configs from
        fqn_scope: FQN scope
        primitive_codec: Primitive codec
        type_descriptor_adapter: Type descriptor adapter
    """
    class_config_function_configs: list[ClassConfigFunctionConfig] = []
    class_fqn = fqn_scope.namespace.fqn(class_config.name)
    # Sort code section functions by position
    code_section_functions = sorted(code_section_class.code_section_class_functions, key=lambda x: x.position)
    for code_section_class_function in code_section_functions:
        code_section_function = code_section_class_function.code_section_function
        # Convert CodeSectionFunction to FunctionConfig
        func_config = build_function_config_from_code(
            fqn_scope=fqn_scope,
            primitive_codec=primitive_codec,
            type_descriptor_adapter=type_descriptor_adapter,
            code_section_function=code_section_function,
            owner_key=class_fqn,
            owner_class_config=class_config,
        )

        is_constructor = is_constructor_verb(func_config.verb)
        class_config_function_config = ClassConfigFunctionConfig(
            id=stable_class_config_function_config_id(
                class_config_id=class_config.id,
                function_config_id=func_config.id,
            ),
            class_config_id=class_config.id,
            function_config=func_config,
            function_config_id=func_config.id,
            is_public=code_section_function.is_public,
            is_constructor=is_constructor,
            position=code_section_class_function.position,
        )
        class_config_function_configs.append(class_config_function_config)
    return class_config_function_configs


def build_class_config_members(
    cls_cfg: ClassConfig,
    fqn_resolver: FqnResolver,
    primitive_codec: CodePrimitiveCodec,
    type_descriptor_adapter: CodeTypeDescriptorAdapter,
) -> None:
    """
    Build class attribute and function configs for the given class config.

    Args:
        cls_cfg: ClassConfig to build members for
        fqn_resolver: FqnResolver to use for resolving FQNs
        primitive_codec: CodePrimitiveCodec to use for primitive codec
        type_descriptor_adapter: CodeTypeDescriptorAdapter to use for type descriptor adapter
    """
    cs = cls_cfg.code_section_class
    if cs is None:
        return
    fqn_scope = fqn_resolver.scope_for_code_id(cs.code_section.code_id)
    try:
        cls_cfg.class_config_attribute_configs = build_class_config_attribute_configs(
            class_config=cls_cfg,
            code_section_class=cs,
            fqn_scope=fqn_scope,
            primitive_codec=primitive_codec,
            type_descriptor_adapter=type_descriptor_adapter,
        )
    except Exception as e:
        logger.error(f"Error building class attribute configs for class {cls_cfg.name}: {e}")
        raise e
    try:
        cls_cfg.class_config_function_configs = build_class_config_function_configs(
            class_config=cls_cfg,
            code_section_class=cs,
            fqn_scope=fqn_scope,
            primitive_codec=primitive_codec,
            type_descriptor_adapter=type_descriptor_adapter,
        )
    except Exception as e:
        logger.error(f"Error building class function configs for class {cls_cfg.name}: {e}")
        raise
