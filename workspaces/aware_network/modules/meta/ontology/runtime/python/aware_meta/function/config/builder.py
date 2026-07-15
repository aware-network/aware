"""Build `FunctionConfig` contracts from code sections."""

# Kernel Graph Ontology
from aware_code_ontology.function.code_section_function import CodeSectionFunction
from aware_code_ontology.function.code_section_function_attribute import (
    CodeSectionFunctionAttribute,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import (
    FunctionKind,
    FunctionAttributeType,
    FunctionIdentityKeyOrigin,
)
from aware_meta_ontology.function.function_config_attribute_config import (
    FunctionConfigAttributeConfig,
)

# Code Runtime
from aware_code.primitive_codec import CodePrimitiveCodec
from aware_code.type_descriptor_adapter import CodeTypeDescriptorAdapter

# Aware Meta
from aware_meta.fqn_resolver import FqnScope
from aware_meta.attribute.config.builder import build_attribute_config_from_code
from aware_meta.graph.config.stable_ids import (
    stable_function_config_id,
    stable_function_config_attribute_config_id,
)
from aware_meta.function.verb_policy import validate_function_verb


def build_function_config_from_code(
    fqn_scope: FqnScope,
    primitive_codec: CodePrimitiveCodec,
    type_descriptor_adapter: CodeTypeDescriptorAdapter,
    code_section_function: CodeSectionFunction,
    owner_key: str | None = None,
    owner_class_config: ClassConfig | None = None,
) -> FunctionConfig:
    """
    Convert this CodeSectionFunction to a FunctionConfig.

    Args:
        fqn_scope: FQN scope
        primitive_codec: Primitive codec
        type_descriptor_adapter: Type descriptor adapter
        code_section_function: CodeSectionFunction instance

    Returns:
        A FunctionConfig instance
    """
    if code_section_function.is_classmethod:
        function_config_kind = FunctionKind.class_
    elif code_section_function.is_static:
        function_config_kind = FunctionKind.static
    else:
        function_config_kind = FunctionKind.instance

    # Stable ID contract:
    # - Global functions: owner_key defaults to the canonical namespace prefix.
    # - Methods: callers must provide the owning class FQN.
    effective_owner_key = owner_key or fqn_scope.namespace.prefix()
    verb = validate_function_verb(
        code_section_function.verb,
        context=f"{effective_owner_key}.{code_section_function.name}",
    )

    function_config = FunctionConfig(
        id=stable_function_config_id(
            owner_key=effective_owner_key,
            name=code_section_function.name,
            kind=function_config_kind.value,
        ),
        owner_key=effective_owner_key,
        name=code_section_function.name,
        description=code_section_function.description,
        is_async=code_section_function.is_async,
        kind=function_config_kind,
        verb=verb,
        code_section_function_id=code_section_function.id,
        code_section_function=code_section_function,
    )

    # Get I/O attributes from function attributes
    code_section_function_attributes_input: list[CodeSectionFunctionAttribute] = []
    code_section_function_attributes_output: list[CodeSectionFunctionAttribute] = []
    for code_section_function_attribute in code_section_function.code_section_function_attributes:
        if code_section_function_attribute.is_output:
            code_section_function_attributes_output.append(code_section_function_attribute)
        else:
            code_section_function_attributes_input.append(code_section_function_attribute)

    # Build input attribute configs
    input_attribute_configs = build_attribute_configs_from_function_attributes(
        fqn_scope=fqn_scope,
        primitive_codec=primitive_codec,
        type_descriptor_adapter=type_descriptor_adapter,
        function_config=function_config,
        function_owner_key=effective_owner_key,
        function_io_type=FunctionAttributeType.input,
        code_section_function_attributes=code_section_function_attributes_input,
    )
    function_config.function_config_attribute_configs.extend(input_attribute_configs)

    # Build output attribute configs
    output_attribute_configs = build_attribute_configs_from_function_attributes(
        fqn_scope=fqn_scope,
        primitive_codec=primitive_codec,
        type_descriptor_adapter=type_descriptor_adapter,
        function_config=function_config,
        function_owner_key=effective_owner_key,
        function_io_type=FunctionAttributeType.output,
        code_section_function_attributes=code_section_function_attributes_output,
    )
    function_config.function_config_attribute_configs.extend(output_attribute_configs)

    # Invocation-plan lowering (class methods only in v0):
    # derive canonical call/construct propagation steps from the function body.
    if owner_class_config is not None:
        try:
            from aware_meta.function.impl.builder import (
                build_function_invocation_plan_from_body,
            )
        except ModuleNotFoundError:
            # First compile pass may run before generated ontology modules are refreshed.
            build_function_invocation_plan_from_body = None

        if build_function_invocation_plan_from_body is not None:
            function_config.invocations.extend(
                build_function_invocation_plan_from_body(
                    function_config=function_config,
                    owner_class_config=owner_class_config,
                    fail_on_unresolved=False,
                )
            )
    return function_config


def build_attribute_configs_from_function_attributes(
    fqn_scope: FqnScope,
    primitive_codec: CodePrimitiveCodec,
    type_descriptor_adapter: CodeTypeDescriptorAdapter,
    function_config: FunctionConfig,
    function_owner_key: str,
    function_io_type: FunctionAttributeType,
    code_section_function_attributes: list[CodeSectionFunctionAttribute],
) -> list[FunctionConfigAttributeConfig]:
    """
    Build attribute configs from function attributes.

    Args:
        fqn_scope: FQN scope
        primitive_codec: Primitive codec
        type_descriptor_adapter: Type descriptor adapter
        function_config: Function config
        function_io_type: Function IO type
        code_section_function_attributes: Code section function attributes

    Returns:
        A list of FunctionConfigAttributeConfig instances
    """
    function_config_attribute_configs: list[FunctionConfigAttributeConfig] = []
    code_section_function_attributes = sorted(code_section_function_attributes, key=lambda a: a.position)
    for code_section_function_attribute in code_section_function_attributes:
        code_section_attribute = code_section_function_attribute.code_section_attribute
        is_identity_key = function_io_type == FunctionAttributeType.input and bool(code_section_attribute.is_primary)
        io_owner = f"{function_owner_key}.{function_config.name}::{function_io_type.value.lower()}"
        attr_config = build_attribute_config_from_code(
            fqn_scope=fqn_scope,
            primitive_codec=primitive_codec,
            type_descriptor_adapter=type_descriptor_adapter,
            code_section_attribute=code_section_attribute,
            is_virtual=False,
            owner_key=io_owner,
        )
        # Stable ID contract for function I/O attributes:
        # Keyed by (function owner rail, io role, attribute name) so reordering doesn't change identity.
        # Create FunctionConfigAttributeConfig
        function_config_attribute_config = FunctionConfigAttributeConfig(
            id=stable_function_config_attribute_config_id(
                function_config_id=function_config.id,
                name=attr_config.name,
                type=function_io_type.value,
            ),
            function_config_id=function_config.id,
            attribute_config=attr_config,
            attribute_config_id=attr_config.id,
            name=attr_config.name,
            type=function_io_type,
            position=code_section_function_attribute.position,
            is_identity_key=is_identity_key,
            identity_key_origin=FunctionIdentityKeyOrigin.standalone,
        )
        function_config_attribute_configs.append(function_config_attribute_config)
    return function_config_attribute_configs
