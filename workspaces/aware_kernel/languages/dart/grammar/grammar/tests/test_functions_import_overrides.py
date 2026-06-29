from __future__ import annotations

from pathlib import Path

# Aware Content
from aware_content.builder import get_text

# Code Runtime
from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter

# Aware ORM
from aware_orm.session.autobind import disable_autobind

# Kernel Graph Ontology
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.function.function_config_attribute_config import (
    FunctionConfigAttributeConfig,
)
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionKind,
)
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig

# Dart Grammar
from dart_grammar.layout_strategy import DartLayoutStrategyTemplateMixin
from dart_grammar.renderer_functions import DartFunctionsRenderer
from dart_grammar_test_support import (
    function_attr_link,
    function_io_owner_key,
    function_owner_key,
    make_attribute,
    make_class,
    make_function,
)


def _string_attribute(name: str, *, owner_key: str, is_required: bool = True) -> AttributeConfig:
    prim = build_code_primitive_type(base_type=CodePrimitiveBaseType.string)
    prim_cfg = PrimitiveConfig(primitive_type=prim, primitive_type_id=prim.id)
    td = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive,
        primitive_config=prim_cfg,
        primitive_config_id=prim_cfg.id,
    )
    return make_attribute(name=name, owner_key=owner_key, type_descriptor=td, is_required=is_required)


def test_functions_renderer_uses_import_override_for_external_class(tmp_path: Path) -> None:
    layout = DartLayoutStrategyTemplateMixin(
        base_dir=tmp_path,
        entity_template_paths={},
        import_root="aware_environment_ontology",
    )
    renderer = DartFunctionsRenderer(layout_strategy=layout)

    with disable_autobind():
        patch_cls = make_class(name="EnvironmentConfigPatch")
        repo_cls = make_class(name="EnvironmentConfig")
        patch_td = AttributeTypeDescriptor(
            kind=AttributeTypeDescriptorKind.class_,
            class_config=patch_cls,
            class_config_id=patch_cls.id,
        )
        fn_cfg = make_function(name="apply_patch", owner_key=function_owner_key(repo_cls), kind=FunctionKind.instance)
        patch_attr = make_attribute(
            name="patch",
            owner_key=function_io_owner_key(fn_cfg, FunctionAttributeType.input),
            type_descriptor=patch_td,
            is_required=True,
        )
        fn_cfg.function_config_attribute_configs = [
            function_attr_link(fn_cfg, patch_attr, type=FunctionAttributeType.input, position=0)
        ]
        repo_cls.class_config_function_configs = [
            ClassConfigFunctionConfig(
                function_config=fn_cfg,
                function_config_id=fn_cfg.id,
                class_config_id=repo_cls.id,
            )
        ]

    renderer.import_overrides = {
        str(patch_cls.id): "package:aware_environment_api/environment/environment_config_patch_model.dart"
    }

    code = renderer.create_empty_code()
    with CodeSectionWriter(code, CodeSectionBuilderIndex(), indent_size=renderer.indent) as writer:
        renderer.emit_file([repo_cls], writer, schema="default", class_to_class_config_map={repo_cls.id: repo_cls})

    dart_source = get_text(code.content_part_text)
    assert "package:aware_environment_api/environment/environment_config_patch_model.dart" in dart_source
    assert "aware_environment_ontology/default/environment_config_patch_model.dart" not in dart_source


def test_functions_renderer_avoids_local_name_collisions(tmp_path: Path) -> None:
    layout = DartLayoutStrategyTemplateMixin(
        base_dir=tmp_path,
        entity_template_paths={},
        import_root="aware_environment_ontology",
    )
    renderer = DartFunctionsRenderer(layout_strategy=layout)

    with disable_autobind():
        enum_option_cls = make_class(name="EnumOption")
        enum_cls = make_class(name="EnumConfig")

        instance_fn = make_function(
            name="resolve_option",
            owner_key=function_owner_key(enum_cls),
            kind=FunctionKind.instance,
        )
        input_names = [
            "value",
            "args",
            "client",
            "request",
            "response",
            "response_payload",
            "json",
            "context",
        ]
        instance_links: list[FunctionConfigAttributeConfig] = []
        for position, input_name in enumerate(input_names):
            attr = _string_attribute(
                input_name,
                owner_key=function_io_owner_key(instance_fn, FunctionAttributeType.input),
            )
            instance_links.append(
                function_attr_link(instance_fn, attr, type=FunctionAttributeType.input, position=position)
            )

        option_td = AttributeTypeDescriptor(
            kind=AttributeTypeDescriptorKind.class_,
            class_config=enum_option_cls,
            class_config_id=enum_option_cls.id,
        )
        option_attr = make_attribute(
            name="value",
            owner_key=function_io_owner_key(instance_fn, FunctionAttributeType.output),
            type_descriptor=option_td,
            is_required=True,
        )
        instance_links.append(
            function_attr_link(
                instance_fn,
                option_attr,
                type=FunctionAttributeType.output,
                position=len(instance_links),
            )
        )
        instance_fn.function_config_attribute_configs = instance_links

        constructor_fn = make_function(
            name="construct_option",
            owner_key=function_owner_key(enum_cls),
            kind=FunctionKind.instance,
            verb="construct",
        )
        constructor_links: list[FunctionConfigAttributeConfig] = []
        for position, input_name in enumerate(["args", "client", "request", "response", "context"]):
            attr = _string_attribute(
                input_name,
                owner_key=function_io_owner_key(constructor_fn, FunctionAttributeType.input),
            )
            constructor_links.append(
                function_attr_link(
                    constructor_fn,
                    attr,
                    type=FunctionAttributeType.input,
                    position=position,
                )
            )
        constructor_fn.function_config_attribute_configs = constructor_links

        enum_cls.class_config_function_configs = [
            ClassConfigFunctionConfig(
                function_config=instance_fn,
                function_config_id=instance_fn.id,
                class_config_id=enum_cls.id,
            ),
            ClassConfigFunctionConfig(
                function_config=constructor_fn,
                function_config_id=constructor_fn.id,
                class_config_id=enum_cls.id,
            ),
        ]

    code = renderer.create_empty_code()
    with CodeSectionWriter(code, CodeSectionBuilderIndex(), indent_size=renderer.indent) as writer:
        renderer.emit_file(
            [enum_cls, enum_option_cls],
            writer,
            schema="default",
            class_to_class_config_map={
                enum_cls.id: enum_cls,
                enum_option_cls.id: enum_option_cls,
            },
        )

    dart_source = get_text(code.content_part_text)
    assert "Future<EnumOption> resolveOption(" in dart_source
    assert "required String context2," in dart_source
    assert "final args2 = <FunctionInvocationArgument>[];" in dart_source
    assert "final client2 = AwareApiLocator.of();" in dart_source
    assert "final request2 = FunctionInvocationRequest(" in dart_source
    assert "final response2 = await client2.invokeFunctionByName(request2);" in dart_source
    assert "final responsePayload2 = response2.payload;" in dart_source
    assert "dynamic responseValue = responsePayload2;" in dart_source
    assert "payload_decoders.decodeMap(responseValue)" in dart_source
    assert "dynamic value = responsePayload" not in dart_source
    assert "static Future<FunctionCallResult> constructOption(" in dart_source
