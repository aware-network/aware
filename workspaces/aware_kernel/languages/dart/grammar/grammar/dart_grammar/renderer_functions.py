"""
Dart functions renderer for generating per-object extension files with real bodies.

This renderer complements the structural Dart model renderer by emitting
extension methods that mirror the OIG materializer behavior:
- Per-object `*Functions` extensions with EnvClient-backed methods for each
  FunctionConfig attached to the class.

The initial implementation focuses on:
- Method signatures derived from FunctionConfig + AttributeConfig type
  descriptors.
- EnvClient invocation wiring with a simple payload cast for return values.
More advanced behaviors (tuple result classes, full CLI flag mapping, enum
mapping helpers) can be layered on top of this structure.
"""

from pathlib import Path
from typing import cast
from uuid import UUID
from typing_extensions import override

from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType

# Code Runtime
from aware_code.section.writer import CodeSectionWriter

# Meta Ontology
from aware_meta_ontology.annotation.code_section_annotation_overlay_enums import (
    CodeSectionAnnotationOverlayEntity,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_config_overlay import AttributeConfigOverlay
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_attribute_config import FunctionConfigAttributeConfig
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType, FunctionKind
from aware_meta.graph.config.render.layout_strategy import ObjectConfigGraphRenderLayoutStrategy

# Meta Runtime
from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info

# Dart Grammar
from dart_grammar.renderer import DartRenderer
from dart_grammar.layout_strategy import DartFunctionsLayoutStrategy, DartModelLayoutStrategy
from aware_meta.graph.config.render.renderer_language import build_renderer_empty_code

# Utils
from aware_utils.string_transform import to_camel_case, to_pascal_case, to_snake_case


class DartFunctionsRenderer(DartRenderer):
    """
    Dart implementation of ObjectConfigGraphRendererLanguage that focuses on
    per-object function extensions.

    It reuses DartRenderer's type-mapping helpers to derive Dart types from
    AttributeConfigTypeDescriptor trees.
    """

    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy) -> None:
        """Wrap the incoming layout strategy so class outputs go to *_functions.dart."""
        functions_layout = DartFunctionsLayoutStrategy.from_parent(layout_strategy)
        super().__init__(layout_strategy=functions_layout)

    @override
    def emit_file(
        self,
        meta_objects: list[object],
        writer: CodeSectionWriter,
        schema: str = "default",
        class_to_class_config_map: dict[UUID, ClassConfig] | None = None,
        base_class_module: str | None = None,
        base_class_name: str | None = None,
    ) -> None:
        """
        Emit a per-file extension module.

        We assume meta_objects contains at least one ClassConfig; if not, this
        renderer emits nothing for the file.
        """
        if class_to_class_config_map is None:
            class_to_class_config_map = {}

        classes = sorted(
            [obj for obj in meta_objects if isinstance(obj, ClassConfig)],
            key=lambda c: c.name,
        )
        if not classes:
            return

        # Only emit a file if at least one class has functions.
        has_functions = any(cls.class_config_function_configs for cls in classes)
        if not has_functions:
            return

        # Derive the model file basename from the *inner* layout strategy so we
        # import the Freezed/JsonSerializable model file (e.g. `content_model.dart`)
        # rather than the API barrel (`content.dart`) or extension file
        # (`content_functions.dart`).
        inner_layout = self.layout_strategy.get_parent()
        if inner_layout is None:
            raise ValueError("No parent layout strategy found")
        model_layout = cast(DartModelLayoutStrategy, DartModelLayoutStrategy.from_parent(inner_layout))
        model_path = model_layout.get_class_file_path(classes[0])

        _ = writer.token("// GENERATED CODE - DO NOT MODIFY BY HAND\n")
        _ = writer.token("// Function extensions for Dart OCG objects.\n\n")

        _ = writer.token(f"import '{model_path.name}';\n")

        # Imports driven by function parameter/return types.
        attrs: list[AttributeConfig] = []
        for cls in classes:
            for link in cls.class_config_function_configs:
                func_cfg = link.function_config
                if not func_cfg or func_cfg.kind != FunctionKind.instance:
                    continue
                for fl in func_cfg.function_config_attribute_configs:
                    if fl.attribute_config:
                        attrs.append(fl.attribute_config)

        # Bring in any referenced class types that are not defined in the model file
        # we're extending. Importing the defining library is required in Dart; imported
        # types are not re-exported by the model file.
        referenced_class_imports: set[str] = set()
        referenced_enum_imports: set[str] = set()
        for attr in attrs:
            type_info = resolve_type_info(attr)
            if type_info.kind == AttributeTypeDescriptorKind.class_:
                class_config = type_info.class_config
                if class_config is None:
                    raise ValueError(f"Class config is None for attribute {attr.name}")
                module = self._resolve_reference_module(
                    model_layout=model_layout,
                    model_path=model_path,
                    entity_id=class_config.id,
                    entity_path=model_layout.get_class_file_path(class_config),
                )
                if module:
                    referenced_class_imports.add(module)

            if type_info.kind == AttributeTypeDescriptorKind.enum:
                enum_config = type_info.enum_config
                if enum_config is None:
                    raise ValueError(f"Enum config is None for attribute {attr.name}")
                module = self._resolve_reference_module(
                    model_layout=model_layout,
                    model_path=model_path,
                    entity_id=enum_config.id,
                    entity_path=model_layout.get_enum_file_path(enum_config),
                )
                if module:
                    referenced_enum_imports.add(module)

        for module in sorted(referenced_class_imports):
            _ = writer.token(f"import '{module}';\n")

        for module in sorted(referenced_enum_imports):
            _ = writer.token(f"import '{module}';\n")

        has_uuid = any(self._attribute_is_base_type(attr, CodePrimitiveBaseType.uuid) for attr in attrs)
        has_uint8list = any(self._attribute_is_base_type(attr, CodePrimitiveBaseType.bytes) for attr in attrs)

        if has_uuid:
            _ = writer.token("import 'package:uuid/uuid.dart';\n")

        if has_uint8list:
            _ = writer.token("import 'dart:typed_data';\n")

        _ = writer.token("import 'package:aware_model_helpers/payload_decoders.dart' as payload_decoders;\n")

        # EnvClient imports – mirror aware_materializer wiring
        _ = writer.token("import 'package:aware_api/aware_api.dart';\n\n")

        for cls in classes:
            self._emit_result_classes_for_object(writer, cls)

        for cls in classes:
            instance_functions: list[FunctionConfig] = []
            constructor_functions: list[FunctionConfig] = []

            for link in cls.class_config_function_configs:
                func_cfg = link.function_config
                if not func_cfg or func_cfg.kind != FunctionKind.instance:
                    continue
                if self._is_constructor_function(func_cfg):
                    constructor_functions.append(func_cfg)
                else:
                    instance_functions.append(func_cfg)

            if instance_functions:
                _ = writer.token(f"extension {cls.name}Functions on {cls.name} ")
                _ = writer.token("{\n")
                for func_cfg in instance_functions:
                    self._emit_instance_function_method(writer, cls, func_cfg)
                _ = writer.token("}\n\n")

            if constructor_functions:
                _ = writer.token(f"class {cls.name}Constructors {{\n")
                for func_cfg in constructor_functions:
                    self._emit_constructor_function_method(writer, cls, func_cfg)
                _ = writer.token("}\n\n")

    def _resolve_reference_module(
        self,
        *,
        model_layout: DartModelLayoutStrategy,
        model_path: Path,
        entity_id: UUID,
        entity_path: Path,
    ) -> str | None:
        """Resolve the import module for a referenced entity (class/enum)."""
        if self.import_overrides:
            override = self.import_overrides.get(str(entity_id))
            if override:
                return override

        if str(entity_id) in model_layout.entity_template_paths:
            ref_path = entity_path
            if ref_path == model_path:
                return None
            if ref_path.parent == model_path.parent:
                return ref_path.name
            return model_layout.get_module_import_path(ref_path)

        return None

    def _emit_result_classes_for_object(self, writer: CodeSectionWriter, cls: ClassConfig) -> None:
        """Emit result wrapper classes for tuple-output functions."""
        for link in cls.class_config_function_configs:
            func_cfg = link.function_config
            if not func_cfg or func_cfg.kind != FunctionKind.instance:
                continue

            output_params: list[FunctionConfigAttributeConfig] = []
            for fl in func_cfg.function_config_attribute_configs:
                if fl.type == FunctionAttributeType.output:
                    output_params.append(fl)

            if len(output_params) <= 1:
                continue

            raw_name = func_cfg.name
            class_name = f"{cls.name}{to_pascal_case(raw_name)}Result"

            _ = writer.token(f"/// Result for `{cls.name}.{raw_name}`.\n")
            _ = writer.token(f"class {class_name} {{\n")

            _ = writer.token(f"  const {class_name}({{\n")
            for link in output_params:
                attr = link.attribute_config
                dart_type = self._get_type_from_attribute_config(attr)
                rendered_name, _wire_name = self._resolve_invocation_names(attr)
                is_optional = self._is_optional_on_runtime(attr)
                prefix = "" if is_optional else "required "
                _ = writer.token(f"    {prefix}this.{rendered_name},\n")
            _ = writer.token("  });\n\n")

            for link in output_params:
                attr = link.attribute_config
                dart_type = self._get_type_from_attribute_config(attr)
                rendered_name, _wire_name = self._resolve_invocation_names(attr)
                is_optional = self._is_optional_on_runtime(attr)
                _ = writer.token(f"  final {dart_type}")
                if is_optional:
                    _ = writer.token("?")
                _ = writer.token(f" {rendered_name};\n")

            _ = writer.token("\n")
            _ = writer.token(f"  factory {class_name}.fromJson(Map<String, dynamic> json) {{\n")
            _ = writer.token(f"    return {class_name}(\n")
            for link in output_params:
                attr = link.attribute_config
                rendered_name, wire_name = self._resolve_invocation_names(attr)
                is_optional = self._is_optional_on_runtime(attr)
                decode_expr = self._render_decode_expression(
                    attr_config=attr,
                    value_expr=f"json['{wire_name}']",
                    is_optional=is_optional,
                )
                _ = writer.token(f"      {rendered_name}: {decode_expr},\n")
            _ = writer.token("    );\n")
            _ = writer.token("  }\n")

            _ = writer.token("}\n\n")

    def _resolve_invocation_names(self, attr_config: AttributeConfig) -> tuple[str, str]:
        """
        Resolve (rendered_name, wire_name) for a FunctionConfig attribute.

        For function invocation args/kwargs and output decoding we need:
        - rendered_name: safe Dart identifier (respects overlays like `enum_`)
        - wire_name: canonical wire key expected by the runtime (`enum`)
        """
        rendered_name = to_camel_case(attr_config.name)
        wire_name = attr_config.name

        overlay = self.get_overlay_by_entity_id(CodeSectionAnnotationOverlayEntity.attribute, attr_config.id)
        if overlay is not None:
            if not isinstance(overlay, AttributeConfigOverlay):
                raise ValueError(f"Overlay for attribute {attr_config.id} is not an AttributeConfigOverlay")
            if overlay.rendered_name:
                rendered_name = overlay.rendered_name
            if overlay.wire_name:
                wire_name = overlay.wire_name

        return rendered_name, wire_name

    def _is_constructor_function(self, func_cfg: FunctionConfig) -> bool:
        """Return True when a FunctionConfig is declared as a constructor (`construct`)."""
        verb = (func_cfg.verb or "").strip().lower()
        return verb == "construct"

    def _reserve_identifier(self, base_name: str, used_identifiers: set[str]) -> str:
        """
        Reserve a collision-safe identifier in method scope.

        Function inputs are user-defined, so generated locals must avoid shadowing them.
        """
        if base_name not in used_identifiers:
            used_identifiers.add(base_name)
            return base_name

        suffix = 2
        while True:
            candidate = f"{base_name}{suffix}"
            if candidate not in used_identifiers:
                used_identifiers.add(candidate)
                return candidate
            suffix += 1

    def _build_input_param_bindings(
        self,
        input_params: list[FunctionConfigAttributeConfig],
        *,
        reserved_names: set[str] | None = None,
    ) -> tuple[list[tuple[AttributeConfig, str, str, bool]], set[str]]:
        """
        Build deterministic, collision-safe method parameter bindings.

        Returns tuple:
        - list of (AttributeConfig, rendered_param_name, wire_name, is_optional)
        - used identifiers set that can be reused to reserve local vars safely
        """
        used_identifiers = set(reserved_names or set())
        bindings: list[tuple[AttributeConfig, str, str, bool]] = []
        for link in input_params:
            attr = link.attribute_config
            base_param_name, wire_name = self._resolve_invocation_names(attr)
            param_name = self._reserve_identifier(base_param_name, used_identifiers)
            bindings.append((attr, param_name, wire_name, self._is_optional_on_runtime(attr)))

        return bindings, used_identifiers

    def _emit_instance_function_method(
        self,
        writer: CodeSectionWriter,
        cls: ClassConfig,
        func_cfg: FunctionConfig,
    ) -> None:
        """
        Emit a single EnvClient-backed method for a FunctionConfig.
        """
        # Translate function name from snake_case to lowerCamelCase
        raw_name = func_cfg.name
        method_name = to_camel_case(raw_name)

        # Partition parameters into input/output
        input_params: list[FunctionConfigAttributeConfig] = []
        output_params: list[FunctionConfigAttributeConfig] = []
        for link in func_cfg.function_config_attribute_configs:
            if link.type == FunctionAttributeType.input:
                input_params.append(link)
            elif link.type == FunctionAttributeType.output:
                output_params.append(link)
        input_param_bindings, used_identifiers = self._build_input_param_bindings(
            input_params,
            reserved_names={"context"},
        )

        return_type = "void"
        result_class_name: str | None = None
        if len(output_params) == 1:
            attr = output_params[0].attribute_config
            return_type = self._get_type_from_attribute_config(attr)
        elif len(output_params) > 1:
            result_class_name = f"{cls.name}{to_pascal_case(raw_name)}Result"
            return_type = result_class_name

        _ = writer.token("\n")
        if func_cfg.description:
            for line in func_cfg.description.split("\n"):
                _ = writer.token(f"  /// {line.strip()}\n")

        # !! NOTE: AVOID CANONICAL ID UNTIL COMMIT IS STABLE to ensure stability during rebuilds.
        # writer.token(f"  /// Function ID: {func_cfg.id}\n")

        # Method signature
        _ = writer.token(f"  Future<{return_type}> {method_name}(")
        # Named parameters with FunctionInvocationContext first
        _ = writer.token("{\n")
        _ = writer.token("    required FunctionInvocationContext context,\n")

        for attr, param_name, _wire_name, is_optional in input_param_bindings:
            dart_type = self._get_type_from_attribute_config(attr)
            prefix = "" if is_optional else "required "
            _ = writer.token(f"    {prefix}{dart_type}")
            if is_optional:
                _ = writer.token("?")
            _ = writer.token(f" {param_name},\n")

        _ = writer.token("  }) async {\n")
        args_var = self._reserve_identifier("args", used_identifiers)
        client_var = self._reserve_identifier("client", used_identifiers)
        request_var = self._reserve_identifier("request", used_identifiers)
        response_var = self._reserve_identifier("response", used_identifiers)
        response_payload_var = self._reserve_identifier("responsePayload", used_identifiers)

        # Arguments list
        _ = writer.token(f"    final {args_var} = <FunctionInvocationArgument>[];\n")
        for _attr, param_name, wire_name, is_optional in input_param_bindings:
            if not is_optional:
                _ = writer.token(f"    {args_var}.add(FunctionInvocationArgument(\n")
                _ = writer.token(f"      name: '{wire_name}',\n")
                _ = writer.token(f"      value: {param_name},\n")
                _ = writer.token("    ));\n")
            else:
                _ = writer.token(f"    if ({param_name} != null) {{\n")
                _ = writer.token(f"      {args_var}.add(FunctionInvocationArgument(\n")
                _ = writer.token(f"        name: '{wire_name}',\n")
                _ = writer.token(f"        value: {param_name},\n")
                _ = writer.token("      ));\n")
                _ = writer.token("    }\n")

        # EnvClient invocation
        _ = writer.token(f"    final {client_var} = AwareApiLocator.of();\n")
        _ = writer.token(f"    final {request_var} = FunctionInvocationRequest(\n")
        object_type = to_snake_case(cls.name).replace("_", "-")
        _ = writer.token(f"      objectType: '{object_type}',\n")
        _ = writer.token("      objectId: id,\n")
        function_name = raw_name.replace("_", "-")
        _ = writer.token(f"      functionName: '{function_name}',\n")
        _ = writer.token("      threadId: context.threadId,\n")
        _ = writer.token("      branchId: context.branchId,\n")
        _ = writer.token("      projectionHash: context.projectionHash,\n")
        _ = writer.token(f"      arguments: {args_var},\n")
        _ = writer.token("    );\n")

        _ = writer.token(f"    final {response_var} = await {client_var}.invokeFunctionByName({request_var});\n")
        _ = writer.token(f"    if (!{response_var}.isSuccess) {{\n")
        _ = writer.token(
            f"      throw StateError('Function {cls.name}.{raw_name} failed: ' "
            + f"+ ({response_var}.error ?? {response_var}.status.name));\n"
        )
        _ = writer.token("    }\n")

        if return_type == "void":
            _ = writer.token("    return;\n")
            _ = writer.token("  }\n")
            return

        _ = writer.token(f"    final {response_payload_var} = {response_var}.payload;\n")

        if result_class_name is not None:
            _ = writer.token(f"    if ({response_payload_var} is! Map) {{\n")
            _ = writer.token(
                f"      throw StateError('Expected Map payload for {cls.name}.{raw_name} but received "
            )
            _ = writer.token("${")
            _ = writer.token(f"{response_payload_var}.runtimeType")
            _ = writer.token("}');\n")
            _ = writer.token("    }\n")
            json_var = self._reserve_identifier("json", used_identifiers)
            _ = writer.token(f"    final {json_var} = Map<String, dynamic>.from({response_payload_var} as Map);\n")
            _ = writer.token(f"    return {result_class_name}.fromJson({json_var});\n")
            _ = writer.token("  }\n")
            return

        # Single output: accept either direct payload or `{wire_key: value}` envelopes.
        output_attr = output_params[0].attribute_config
        _rendered_name, wire_name = self._resolve_invocation_names(output_attr)
        response_value_var = self._reserve_identifier("responseValue", used_identifiers)

        _ = writer.token(f"    dynamic {response_value_var} = {response_payload_var};\n")
        _ = writer.token(f"    if ({response_payload_var} is Map && {response_payload_var}.containsKey(")
        _ = writer.token(f"'{wire_name}'")
        _ = writer.token(")) {\n")
        _ = writer.token(f"      {response_value_var} = {response_payload_var}['{wire_name}'];\n")
        _ = writer.token("    }\n")

        decode_expr = self._render_decode_expression(
            attr_config=output_attr,
            value_expr=response_value_var,
            is_optional=self._is_optional_on_runtime(output_attr),
        )
        _ = writer.token(f"    return {decode_expr};\n")
        _ = writer.token("  }\n")

    def _emit_constructor_function_method(
        self,
        writer: CodeSectionWriter,
        cls: ClassConfig,
        func_cfg: FunctionConfig,
    ) -> None:
        """Emit a static EnvClient-backed constructor invocation (OPG constructor)."""
        raw_name = func_cfg.name
        method_name = to_camel_case(raw_name)

        input_params: list[FunctionConfigAttributeConfig] = []
        for link in func_cfg.function_config_attribute_configs:
            if link.type == FunctionAttributeType.input:
                input_params.append(link)
        input_param_bindings, used_identifiers = self._build_input_param_bindings(
            input_params,
            reserved_names={"context"},
        )

        _ = writer.token("\n")
        if func_cfg.description:
            for line in func_cfg.description.split("\n"):
                _ = writer.token(f"  /// {line.strip()}\n")

        _ = writer.token(f"  static Future<FunctionCallResult> {method_name}(")
        _ = writer.token("{\n")
        _ = writer.token("    required FunctionInvocationContext context,\n")

        for attr, param_name, _wire_name, is_optional in input_param_bindings:
            dart_type = self._get_type_from_attribute_config(attr)
            prefix = "" if is_optional else "required "
            _ = writer.token(f"    {prefix}{dart_type}")
            if is_optional:
                _ = writer.token("?")
            _ = writer.token(f" {param_name},\n")

        _ = writer.token("  }) async {\n")
        args_var = self._reserve_identifier("args", used_identifiers)
        client_var = self._reserve_identifier("client", used_identifiers)
        request_var = self._reserve_identifier("request", used_identifiers)
        response_var = self._reserve_identifier("response", used_identifiers)

        _ = writer.token(f"    final {args_var} = <FunctionInvocationArgument>[];\n")
        for _attr, param_name, wire_name, is_optional in input_param_bindings:
            if not is_optional:
                _ = writer.token(f"    {args_var}.add(FunctionInvocationArgument(\n")
                _ = writer.token(f"      name: '{wire_name}',\n")
                _ = writer.token(f"      value: {param_name},\n")
                _ = writer.token("    ));\n")
            else:
                _ = writer.token(f"    if ({param_name} != null) {{\n")
                _ = writer.token(f"      {args_var}.add(FunctionInvocationArgument(\n")
                _ = writer.token(f"        name: '{wire_name}',\n")
                _ = writer.token(f"        value: {param_name},\n")
                _ = writer.token("      ));\n")
                _ = writer.token("    }\n")

        _ = writer.token(f"    final {client_var} = AwareApiLocator.of();\n")
        _ = writer.token(f"    final {request_var} = FunctionInvocationRequest(\n")
        object_type = to_snake_case(cls.name).replace("_", "-")
        _ = writer.token(f"      objectType: '{object_type}',\n")
        function_name = raw_name.replace("_", "-")
        _ = writer.token(f"      functionName: '{function_name}',\n")
        _ = writer.token("      threadId: context.threadId,\n")
        _ = writer.token("      branchId: context.branchId,\n")
        _ = writer.token("      projectionHash: context.projectionHash,\n")
        _ = writer.token("      callTarget: FunctionInvocationCallTarget.opgConstructor,\n")
        _ = writer.token("      objectProjectionGraphId: context.opgId,\n")
        _ = writer.token(f"      arguments: {args_var},\n")
        _ = writer.token("    );\n")
        _ = writer.token(f"    final {response_var} = await {client_var}.invokeFunctionByName({request_var});\n")
        _ = writer.token(f"    if (!{response_var}.isSuccess) {{\n")
        _ = writer.token(
            f"      throw StateError('Function {cls.name}.{raw_name} failed: ' + "
            + f"({response_var}.error ?? {response_var}.status.name));\n"
        )
        _ = writer.token("    }\n")
        _ = writer.token(f"    return {response_var};\n")
        _ = writer.token("  }\n")

    def _render_decode_expression(
        self,
        *,
        attr_config: AttributeConfig,
        value_expr: str,
        is_optional: bool,
    ) -> str:
        """
        Render a Dart expression that decodes a dynamic JSON payload into the expected Dart type.

        The function bodies are generated without build_runner, so we rely on simple runtime
        coercion utilities (String/UuidValue/DateTime/List/Map) and the generated model `fromJson`.
        """
        type_info = resolve_type_info(attr_config)

        def _decode_leaf(expr: str, *, optional: bool) -> str:
            if type_info.kind == AttributeTypeDescriptorKind.primitive and type_info.primitive_config is not None:
                prim = CodePrimitiveType.model_validate(type_info.primitive_config.primitive_type)
                base = prim.base_type
                if base == CodePrimitiveBaseType.uuid:
                    return (
                        f"payload_decoders.decodeUuidValueOrNull({expr})"
                        if optional
                        else f"payload_decoders.decodeUuidValue({expr})"
                    )
                if base == CodePrimitiveBaseType.datetime:
                    return (
                        f"payload_decoders.decodeDateTimeOrNull({expr})"
                        if optional
                        else f"payload_decoders.decodeDateTime({expr})"
                    )
                if base == CodePrimitiveBaseType.integer:
                    return (
                        f"payload_decoders.decodeIntOrNull({expr})"
                        if optional
                        else f"payload_decoders.decodeInt({expr})"
                    )
                if base == CodePrimitiveBaseType.float:
                    return (
                        f"payload_decoders.decodeDoubleOrNull({expr})"
                        if optional
                        else f"payload_decoders.decodeDouble({expr})"
                    )
                if base == CodePrimitiveBaseType.boolean:
                    return (
                        f"payload_decoders.decodeBoolOrNull({expr})"
                        if optional
                        else f"payload_decoders.decodeBool({expr})"
                    )
                if base == CodePrimitiveBaseType.json:
                    return (
                        f"payload_decoders.decodeJsonObjectOrNull({expr})"
                        if optional
                        else f"payload_decoders.decodeJsonObject({expr})"
                    )
                if base == CodePrimitiveBaseType.bytes:
                    return (
                        f"payload_decoders.decodeBytesOrNull({expr})"
                        if optional
                        else f"payload_decoders.decodeBytes({expr})"
                    )
                if base == CodePrimitiveBaseType.string:
                    return (
                        f"payload_decoders.decodeStringOrNull({expr})"
                        if optional
                        else f"payload_decoders.decodeString({expr})"
                    )
                return expr

            if type_info.kind == AttributeTypeDescriptorKind.enum and type_info.enum_config is not None:
                enum_name = type_info.enum_config.name
                if optional:
                    return f"({expr} == null ? null : {enum_name}.values.byName({expr}.toString()))"
                return f"{enum_name}.values.byName({expr}.toString())"

            if type_info.kind == AttributeTypeDescriptorKind.class_ and type_info.class_config is not None:
                class_name = to_pascal_case(type_info.class_config.name)
                inner = f"{class_name}.fromJson(payload_decoders.decodeMap({expr}))"
                if optional:
                    return f"({expr} == null ? null : {inner})"
                return inner

            return expr

        if type_info.collection_kind == AttributeCollectionType.list:
            element_expr = _decode_leaf("item", optional=False)
            fn = "payload_decoders.decodeListOrNull" if is_optional else "payload_decoders.decodeList"
            return f"{fn}({value_expr}, (item) => {element_expr})"

        if type_info.collection_kind == AttributeCollectionType.set:
            element_expr = _decode_leaf("item", optional=False)
            fn = "payload_decoders.decodeSetOrNull" if is_optional else "payload_decoders.decodeSet"
            return f"{fn}({value_expr}, (item) => {element_expr})"

        return _decode_leaf(value_expr, optional=is_optional)

    @override
    def create_empty_code(self) -> Code:
        return build_renderer_empty_code(
            language=CodeLanguage.dart,
            renderer_key=type(self).__name__,
        )
