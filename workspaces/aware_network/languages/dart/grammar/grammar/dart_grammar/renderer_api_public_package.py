from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from uuid import UUID

from typing_extensions import override

from aware_code.section.writer import CodeSectionWriter
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta.graph.config.render.renderer_language import (
    ObjectConfigGraphRendererLanguage,
    ObjectConfigGraphRendererPolicy,
    build_renderer_empty_code,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_utils.string_transform import to_camel_case, to_pascal_case


@dataclass(frozen=True)
class _DartTypeBinding:
    class_ref: str
    class_name: str
    module_path: str
    class_config: ClassConfig


@dataclass(frozen=True)
class _EndpointRenderBinding:
    endpoint_ref: str
    discriminant: str
    api_name: str
    capability_name: str
    endpoint_name: str
    description: str | None
    request: _DartTypeBinding
    response: _DartTypeBinding | None
    stream_events: tuple[_DartTypeBinding, ...]
    stream_base: _DartTypeBinding | None

    @property
    def endpoint_ref_constant_name(self) -> str:
        return _endpoint_constant_name(
            self.api_name,
            self.capability_name,
            self.endpoint_name,
            suffix="endpoint_ref",
        )

    @property
    def discriminant_constant_name(self) -> str:
        return _endpoint_constant_name(
            self.api_name,
            self.capability_name,
            self.endpoint_name,
            suffix="discriminant",
        )

    @property
    def capability_client_class_name(self) -> str:
        return f"{to_pascal_case(self.api_name)}{to_pascal_case(self.capability_name)}CapabilityClient"

    @property
    def api_client_class_name(self) -> str:
        return f"{to_pascal_case(self.api_name)}ApiClient"

    @property
    def method_name(self) -> str:
        return _safe_dart_identifier(self.endpoint_name)

    @property
    def stream_alias_name(self) -> str:
        return (
            f"{to_pascal_case(self.api_name)}"
            f"{to_pascal_case(self.capability_name)}"
            f"{to_pascal_case(self.endpoint_name)}StreamEvent"
        )

    @property
    def capability_property_name(self) -> str:
        return _safe_dart_identifier(self.capability_name)


class _DartApiPublicPackageRendererBase(ObjectConfigGraphRendererLanguage):
    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy):
        super().__init__(layout_strategy=layout_strategy)
        self._type_bindings_by_identity: dict[str, _DartTypeBinding] = {}
        self._type_bindings_by_class_id: dict[UUID, _DartTypeBinding] = {}
        self._enum_module_paths: set[str] = set()

    @property
    @override
    def language(self) -> CodeLanguage:
        return CodeLanguage.dart

    @property
    @override
    def indent(self) -> int:
        return 2

    @property
    @override
    def comment_prefix(self) -> str:
        return "//"

    @override
    def define_assemblers(self) -> None:
        return

    @override
    def set_policy(self, policy: ObjectConfigGraphRendererPolicy | None) -> None:
        _ = policy

    @override
    def bind_object_config_graph(self, graph: ObjectConfigGraph) -> None:
        bindings_by_identity: dict[str, _DartTypeBinding] = {}
        bindings_by_class_id: dict[UUID, _DartTypeBinding] = {}
        enum_module_paths: set[str] = set()
        for node in graph.object_config_graph_nodes:
            enum_config = node.enum_config
            if isinstance(enum_config, EnumConfig):
                enum_module_paths.add(
                    self.layout_strategy.get_module_import_path(
                        self.layout_strategy.get_enum_file_path(enum_config)
                    )
                )

            class_config = node.class_config
            if class_config is None:
                continue
            import_class_config = _variant_import_owner(class_config)
            module_path = self.layout_strategy.get_module_import_path(
                self.layout_strategy.get_class_file_path(import_class_config)
            )
            binding = _DartTypeBinding(
                class_ref=class_config.class_fqn,
                class_name=class_config.name,
                module_path=module_path,
                class_config=class_config,
            )
            bindings_by_class_id[class_config.id] = binding
            for identity in {
                _normalize_token(class_config.class_fqn),
                _normalize_token(class_config.name),
                _leaf_token(class_config.class_fqn),
                _leaf_token(class_config.name),
            }:
                bindings_by_identity.setdefault(identity, binding)

        self._type_bindings_by_identity = bindings_by_identity
        self._type_bindings_by_class_id = bindings_by_class_id
        self._enum_module_paths = enum_module_paths

    @override
    def create_empty_code(self) -> Code:
        return build_renderer_empty_code(
            language=CodeLanguage.dart,
            renderer_key=type(self).__name__,
        )

    def _require_payload(self, key: str) -> dict[str, object]:
        payload = self.profile_inputs.get(key)
        if not isinstance(payload, dict):
            raise ValueError(f"Expected profile input {key!r} to be a JSON object.")
        return payload

    def _package_name(self) -> str:
        public_plan = self._require_payload("api.public_package_plan")
        return _require_string(public_plan, "package_name")

    def _library_file_name(self) -> str:
        public_plan = self._require_payload("api.public_package_plan")
        token = _optional_string(public_plan, "fqn_prefix") or self._package_name()
        return token.replace("-", "_")

    def _all_type_bindings(self) -> tuple[_DartTypeBinding, ...]:
        return tuple(
            sorted(
                self._type_bindings_by_class_id.values(),
                key=lambda item: (item.module_path.casefold(), item.class_ref.casefold()),
            )
        )

    def _endpoint_bindings(self) -> tuple[_EndpointRenderBinding, ...]:
        public_plan = self._require_payload("api.public_package_plan")
        invocation_manifest = self._require_payload("api.invocation_manifest")
        interface_spec = self._require_payload("api.interface_spec")

        interface_refs = _collect_interface_endpoint_refs(interface_spec=interface_spec)
        invocation_by_ref = _build_invocation_endpoint_index(invocation_manifest=invocation_manifest)

        bindings: list[_EndpointRenderBinding] = []
        for api in _iter_object_list(public_plan.get("apis"), label="api.public_package_plan.apis"):
            api_name = _require_string(api, "name")
            for capability in _iter_object_list(api.get("capabilities"), label=f"{api_name}.capabilities"):
                capability_name = _require_string(capability, "name")
                for endpoint in _iter_object_list(
                    capability.get("endpoints"),
                    label=f"{api_name}.{capability_name}.endpoints",
                ):
                    endpoint_name = _require_string(endpoint, "name")
                    endpoint_ref = _require_string(endpoint, "discriminant")
                    if endpoint_ref not in interface_refs:
                        raise ValueError(
                            "API public-package renderer missing interface endpoint "
                            + f"{endpoint_ref!r} in api.interface_spec"
                        )

                    invocation = invocation_by_ref.get(endpoint_ref)
                    if invocation is None:
                        raise ValueError(
                            "API public-package renderer missing invocation endpoint "
                            + f"{endpoint_ref!r} in api.invocation_manifest"
                        )

                    request_payload = _require_object(endpoint.get("request"), label=f"{endpoint_ref}.request")
                    request_ref = _require_string(request_payload, "class_ref")
                    request_binding = self._resolve_type_binding(request_ref)

                    response_binding = None
                    response_payload = endpoint.get("response")
                    if response_payload is not None:
                        response_binding = self._resolve_type_binding(
                            _require_string(
                                _require_object(response_payload, label=f"{endpoint_ref}.response"),
                                "class_ref",
                            )
                        )

                    stream_event_bindings: list[_DartTypeBinding] = []
                    stream_payload = endpoint.get("stream")
                    if stream_payload is not None:
                        stream_object = _require_object(stream_payload, label=f"{endpoint_ref}.stream")
                        for event in _iter_object_list(
                            stream_object.get("events"),
                            label=f"{endpoint_ref}.stream.events",
                        ):
                            stream_event_bindings.append(
                                self._resolve_type_binding(_require_string(event, "class_ref"))
                            )

                    invocation_request_ref = _require_string(
                        _require_object(invocation.get("request"), label=f"{endpoint_ref}.invocation.request"),
                        "class_ref",
                    )
                    if _normalize_token(invocation_request_ref) != _normalize_token(request_ref):
                        raise ValueError(
                            "API public-package renderer request class drift for "
                            + f"{endpoint_ref!r}: public_plan={request_ref!r}, invocation={invocation_request_ref!r}"
                        )

                    bindings.append(
                        _EndpointRenderBinding(
                            endpoint_ref=endpoint_ref,
                            discriminant=_require_string(invocation, "discriminant"),
                            api_name=api_name,
                            capability_name=capability_name,
                            endpoint_name=endpoint_name,
                            description=_optional_string(endpoint, "description"),
                            request=request_binding,
                            response=response_binding,
                            stream_events=tuple(stream_event_bindings),
                            stream_base=self._resolve_common_stream_binding(stream_event_bindings),
                        )
                    )

        return tuple(
            sorted(
                bindings,
                key=lambda item: (
                    item.api_name.casefold(),
                    item.capability_name.casefold(),
                    item.endpoint_name.casefold(),
                    item.endpoint_ref,
                ),
            )
        )

    def _resolve_type_binding(self, class_ref: str) -> _DartTypeBinding:
        normalized = _normalize_token(class_ref)
        binding = self._type_bindings_by_identity.get(normalized)
        if binding is not None:
            return binding

        matches: list[_DartTypeBinding] = []
        seen_class_ids: set[UUID] = set()
        for identity, candidate in self._type_bindings_by_identity.items():
            if not (identity.endswith(f".{normalized}") or identity == _leaf_token(normalized)):
                continue
            if candidate.class_config.id in seen_class_ids:
                continue
            matches.append(candidate)
            seen_class_ids.add(candidate.class_config.id)
        if not matches:
            raise ValueError(f"Could not resolve API Dart type binding for class_ref {class_ref!r}.")
        if len(matches) > 1:
            raise ValueError(f"Ambiguous API Dart type binding for class_ref {class_ref!r}.")
        return matches[0]

    def _resolve_common_stream_binding(
        self,
        bindings: Iterable[_DartTypeBinding],
    ) -> _DartTypeBinding | None:
        stream_bindings = list(bindings)
        if not stream_bindings:
            return None
        if len(stream_bindings) == 1:
            return stream_bindings[0]

        lineages = [_class_lineage(binding.class_config) for binding in stream_bindings]
        shortest = min(len(lineage) for lineage in lineages)
        common: ClassConfig | None = None
        for index in range(shortest):
            candidate = lineages[0][index]
            if all(lineage[index].id == candidate.id for lineage in lineages[1:]):
                common = candidate
                continue
            break
        if common is None:
            return None
        return self._type_bindings_by_class_id.get(common.id)


class DartApiPublicPackageBindingsRendererLanguage(_DartApiPublicPackageRendererBase):
    @override
    def extra_output_paths(self) -> list[Path]:
        return [Path("bindings.dart")]

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
        _ = schema
        _ = class_to_class_config_map
        _ = base_class_module
        _ = base_class_name
        if meta_objects:
            return

        public_plan = self._require_payload("api.public_package_plan")
        interface_spec = self._require_payload("api.interface_spec")
        invocation_manifest = self._require_payload("api.invocation_manifest")
        bindings = self._endpoint_bindings()

        _ = writer.token("// GENERATED CODE - DO NOT MODIFY BY HAND\n")
        _ = writer.token("// Compiled API bindings for generated Dart SDK wrappers.\n\n")
        _ = writer.token("import 'dart:convert' as convert;\n\n")

        _ = writer.token(
            f"const String apiPackageName = {json.dumps(_require_string(public_plan, 'package_name'))};\n"
        )
        _ = writer.token(
            f"const String apiFqnPrefix = {json.dumps(_require_string(public_plan, 'fqn_prefix'))};\n\n"
        )

        _ = writer.token(
            "final Map<String, Object?> apiInterfaceSpecPayload = _decodeJsonObject(\n"
        )
        _ = writer.token(_render_json_string_literal(interface_spec))
        _ = writer.token(");\n\n")
        _ = writer.token(
            "final Map<String, Object?> apiInvocationManifestPayload = _decodeJsonObject(\n"
        )
        _ = writer.token(_render_json_string_literal(invocation_manifest))
        _ = writer.token(");\n\n")

        for binding in bindings:
            _ = writer.token(
                f"const String {binding.endpoint_ref_constant_name} = {json.dumps(binding.endpoint_ref)};\n"
            )
            _ = writer.token(
                f"const String {binding.discriminant_constant_name} = {json.dumps(binding.discriminant)};\n"
            )
        if bindings:
            _ = writer.token("\n")

        _ = writer.token("Map<String, Object?> _decodeJsonObject(String raw) {\n")
        _ = writer.token("  final decoded = convert.jsonDecode(raw);\n")
        _ = writer.token("  if (decoded is! Map) {\n")
        _ = writer.token("    throw StateError('Expected compiled API payload to decode to a JSON object.');\n")
        _ = writer.token("  }\n")
        _ = writer.token("  return Map<String, Object?>.from(decoded);\n")
        _ = writer.token("}\n")


class DartApiPublicPackageClientRendererLanguage(_DartApiPublicPackageRendererBase):
    @override
    def extra_output_paths(self) -> list[Path]:
        return [Path("client.dart")]

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
        _ = schema
        _ = class_to_class_config_map
        _ = base_class_module
        _ = base_class_name
        if meta_objects:
            return

        bindings = self._endpoint_bindings()
        imported_types = _collect_imported_types(endpoint_bindings=bindings)
        module_aliases = _build_module_aliases(type_bindings=imported_types)
        api_names = sorted({binding.api_name for binding in bindings}, key=str.casefold)
        root_client_class_name = f"{to_pascal_case(self._library_file_name())}Client"

        _ = writer.token("// GENERATED CODE - DO NOT MODIFY BY HAND\n")
        _ = writer.token("// Thin typed API wrapper over package:aware_api/aware_api.dart.\n\n")
        _ = writer.token("import 'dart:async';\n\n")
        _ = writer.token("import 'package:aware_api/aware_api.dart';\n\n")
        _ = writer.token("import 'bindings.dart';\n")
        for module_path, alias in sorted(module_aliases.items(), key=lambda item: item[0].casefold()):
            _ = writer.token(f"import '{module_path}' as {alias};\n")
        if module_aliases:
            _ = writer.token("\n")

        for binding in bindings:
            if not binding.stream_events or binding.stream_base is None:
                continue
            _ = writer.token(
                f"typedef {binding.stream_alias_name} = "
                f"{_type_reference(binding.stream_base, module_aliases)};\n"
            )
        if any(binding.stream_events and binding.stream_base is not None for binding in bindings):
            _ = writer.token("\n")

        by_api: dict[str, dict[str, list[_EndpointRenderBinding]]] = {}
        for binding in bindings:
            by_api.setdefault(binding.api_name, {}).setdefault(binding.capability_name, []).append(binding)

        for api_name in sorted(by_api, key=str.casefold):
            capability_bindings = by_api[api_name]
            for capability_name in sorted(capability_bindings, key=str.casefold):
                lines = _render_capability_client_class(
                    class_name=f"{to_pascal_case(api_name)}{to_pascal_case(capability_name)}CapabilityClient",
                    endpoint_bindings=tuple(capability_bindings[capability_name]),
                    module_aliases=module_aliases,
                )
                for line in lines:
                    _ = writer.token(f"{line}\n")
                _ = writer.token("\n")

        for api_name in api_names:
            lines = _render_api_client_class(
                api_name=api_name,
                capability_names=tuple(sorted(by_api.get(api_name, {}), key=str.casefold)),
            )
            for line in lines:
                _ = writer.token(f"{line}\n")
            _ = writer.token("\n")

        lines = _render_root_client_class(
            class_name=root_client_class_name,
            api_names=api_names,
        )
        for line in lines:
            _ = writer.token(f"{line}\n")
        _ = writer.token("\n")

        _ = writer.token("Map<String, dynamic> _requireJsonMap(Object? payload, {required String endpointRef}) {\n")
        _ = writer.token("  if (payload is Map<String, dynamic>) {\n")
        _ = writer.token("    return payload;\n")
        _ = writer.token("  }\n")
        _ = writer.token("  if (payload is Map) {\n")
        _ = writer.token("    return Map<String, dynamic>.from(payload);\n")
        _ = writer.token("  }\n")
        _ = writer.token(
            "  throw StateError('Expected API payload for $endpointRef to decode to a JSON object.');\n"
        )
        _ = writer.token("}\n")


class DartApiPublicPackageLibraryRendererLanguage(_DartApiPublicPackageRendererBase):
    @override
    def extra_output_paths(self) -> list[Path]:
        return [Path(f"{self._library_file_name()}.dart")]

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
        _ = schema
        _ = class_to_class_config_map
        _ = base_class_module
        _ = base_class_name
        if meta_objects:
            return

        _ = writer.token("// GENERATED CODE - DO NOT MODIFY BY HAND\n")
        _ = writer.token("// Root export barrel for the generated Dart API package.\n\n")
        _ = writer.token("export 'bindings.dart';\n")
        _ = writer.token("export 'client.dart';\n")

        exported_modules = {
            binding.module_path
            for binding in self._all_type_bindings()
        }
        exported_modules.update(self._enum_module_paths)
        for module_path in sorted(exported_modules, key=str.casefold):
            _ = writer.token(f"export '{module_path}';\n")


def _render_capability_client_class(
    *,
    class_name: str,
    endpoint_bindings: tuple[_EndpointRenderBinding, ...],
    module_aliases: dict[str, str],
) -> list[str]:
    lines: list[str] = [f"class {class_name} {{"]
    lines.append(f"  {class_name}(AwareApiClient client) : _client = client;")
    lines.append("")
    lines.append("  final AwareApiClient _client;")
    for binding in endpoint_bindings:
        request_type = _type_reference(binding.request, module_aliases)
        response_type = _response_type_reference(binding=binding, module_aliases=module_aliases)
        lines.append("")
        if binding.description:
            lines.append(f"  /// {_sanitize_doc_comment(binding.description)}")
        lines.append(
            f"  Future<{response_type}> {binding.method_name}("
            f"{request_type} request, {{Duration timeout = const Duration(seconds: 30)}}) async {{"
        )
        lines.extend(
            [
                f"    return _client.invokeApiEndpoint<{response_type}>(",
                f"      endpointRef: {binding.endpoint_ref_constant_name},",
                f"      discriminant: {binding.discriminant_constant_name},",
                "      requestPayload: request.toJson(),",
                "      decodeResponse: (payload) => "
                + _response_decode_expression(binding=binding, module_aliases=module_aliases)
                + ",",
                "      timeout: timeout,",
                "    );",
                "  }",
            ]
        )

        if binding.stream_events and binding.stream_base is not None:
            lines.append("")
            if binding.description:
                lines.append(f"  /// {_sanitize_doc_comment(binding.description)}")
            lines.append(
                f"  Stream<{binding.stream_alias_name}> stream{to_pascal_case(binding.method_name)}("
                f"{request_type} request, {{Duration timeout = const Duration(seconds: 30)}}) {{"
            )
            lines.extend(
                [
                    f"    return _client.streamApiEndpoint<{binding.stream_alias_name}>(",
                    f"      endpointRef: {binding.endpoint_ref_constant_name},",
                    f"      discriminant: {binding.discriminant_constant_name},",
                    "      requestPayload: request.toJson(),",
                    "      decodeEvent: (payload) => "
                    + _stream_decode_expression(binding=binding, module_aliases=module_aliases)
                    + ",",
                    "      timeout: timeout,",
                    "    );",
                    "  }",
                ]
            )

    lines.append("}")
    return lines


def _render_api_client_class(
    *,
    api_name: str,
    capability_names: tuple[str, ...],
) -> list[str]:
    class_name = f"{to_pascal_case(api_name)}ApiClient"
    lines: list[str] = [f"class {class_name} {{"]
    lines.append(f"  {class_name}(AwareApiClient client)")
    initializers = [
        f"{_safe_dart_identifier(capability_name)} = "
        f"{to_pascal_case(api_name)}{to_pascal_case(capability_name)}CapabilityClient(client)"
        for capability_name in capability_names
    ]
    if initializers:
        if len(initializers) == 1:
            lines[-1] = f"{lines[-1]} : {initializers[0]};"
        else:
            lines[-1] = f"{lines[-1]} : {initializers[0]},"
            for initializer in initializers[1:-1]:
                lines.append(f"        {initializer},")
            lines.append(f"        {initializers[-1]};")
    else:
        lines[-1] += ";"
    lines.append("")
    for capability_name in capability_names:
        lines.append(
            f"  final {to_pascal_case(api_name)}{to_pascal_case(capability_name)}CapabilityClient "
            f"{_safe_dart_identifier(capability_name)};"
        )
    lines.append("}")
    return lines


def _render_root_client_class(
    *,
    class_name: str,
    api_names: list[str],
) -> list[str]:
    lines: list[str] = [f"class {class_name} {{"]
    if api_names:
        lines.append(f"  {class_name}(AwareApiClient client) :")
        for index, api_name in enumerate(api_names):
            suffix = "," if index < len(api_names) - 1 else ";"
            lines.append(
                f"        {to_camel_case(api_name)} = {to_pascal_case(api_name)}ApiClient(client){suffix}"
            )
    else:
        lines.append(f"  {class_name}(AwareApiClient client);")
    lines.append("")
    lines.append("  final Map<String, Object?> interfaceSpecPayload = apiInterfaceSpecPayload;")
    lines.append("  final Map<String, Object?> invocationManifestPayload = apiInvocationManifestPayload;")
    for api_name in api_names:
        lines.append(f"  final {to_pascal_case(api_name)}ApiClient {to_camel_case(api_name)};")
    lines.append("}")
    return lines


def _collect_interface_endpoint_refs(*, interface_spec: dict[str, object]) -> set[str]:
    refs: set[str] = set()
    for api in _iter_object_list(interface_spec.get("apis"), label="api.interface_spec.apis"):
        api_name = _require_string(api, "name")
        for capability in _iter_object_list(api.get("capabilities"), label=f"{api_name}.capabilities"):
            capability_name = _require_string(capability, "name")
            for endpoint in _iter_object_list(
                capability.get("endpoints"),
                label=f"{api_name}.{capability_name}.endpoints",
            ):
                refs.add(_require_string(endpoint, "discriminant"))
    return refs


def _build_invocation_endpoint_index(
    *,
    invocation_manifest: dict[str, object],
) -> dict[str, dict[str, object]]:
    endpoints: dict[str, dict[str, object]] = {}
    for api in _iter_object_list(invocation_manifest.get("apis"), label="api.invocation_manifest.apis"):
        api_name = _require_string(api, "name")
        for capability in _iter_object_list(api.get("capabilities"), label=f"{api_name}.capabilities"):
            capability_name = _require_string(capability, "name")
            for endpoint in _iter_object_list(
                capability.get("endpoints"),
                label=f"{api_name}.{capability_name}.endpoints",
            ):
                endpoints[_require_string(endpoint, "endpoint_ref")] = endpoint
    return endpoints


def _collect_imported_types(
    *,
    endpoint_bindings: tuple[_EndpointRenderBinding, ...],
) -> tuple[_DartTypeBinding, ...]:
    ordered: dict[str, _DartTypeBinding] = {}
    for binding in endpoint_bindings:
        ordered.setdefault(binding.request.class_ref, binding.request)
        if binding.response is not None:
            ordered.setdefault(binding.response.class_ref, binding.response)
        if binding.stream_base is not None:
            ordered.setdefault(binding.stream_base.class_ref, binding.stream_base)
    return tuple(ordered.values())


def _build_module_aliases(
    *,
    type_bindings: Iterable[_DartTypeBinding],
) -> dict[str, str]:
    aliases: dict[str, str] = {}
    used: set[str] = set()
    for binding in sorted(type_bindings, key=lambda item: item.module_path.casefold()):
        candidate = _safe_dart_identifier(
            "_".join(part for part in binding.module_path.replace(".dart", "").split("/") if part)
        )
        alias = candidate or "api_type"
        counter = 2
        while alias in used:
            alias = f"{candidate}_{counter}"
            counter += 1
        aliases[binding.module_path] = alias
        used.add(alias)
    return aliases


def _type_reference(binding: _DartTypeBinding, module_aliases: dict[str, str]) -> str:
    alias = module_aliases[binding.module_path]
    return f"{alias}.{binding.class_name}"


def _response_type_reference(
    *,
    binding: _EndpointRenderBinding,
    module_aliases: dict[str, str],
) -> str:
    if binding.response is None:
        return "Object?"
    return _type_reference(binding.response, module_aliases)


def _response_decode_expression(
    *,
    binding: _EndpointRenderBinding,
    module_aliases: dict[str, str],
) -> str:
    if binding.response is None:
        return "payload"
    return (
        f"{_type_reference(binding.response, module_aliases)}.fromJson("
        f"_requireJsonMap(payload, endpointRef: {binding.endpoint_ref_constant_name}))"
    )


def _stream_decode_expression(
    *,
    binding: _EndpointRenderBinding,
    module_aliases: dict[str, str],
) -> str:
    if binding.stream_base is None:
        return "payload"
    return (
        f"{_type_reference(binding.stream_base, module_aliases)}.fromJson("
        f"_requireJsonMap(payload, endpointRef: {binding.endpoint_ref_constant_name}))"
    )


def _endpoint_constant_name(api_name: str, capability_name: str, endpoint_name: str, *, suffix: str) -> str:
    token = "_".join([api_name, capability_name, endpoint_name, suffix])
    return _safe_dart_identifier(token)


def _safe_dart_identifier(value: str) -> str:
    candidate = to_camel_case(value or "").strip("_") or "value"
    candidate = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in candidate)
    if candidate and candidate[0].isdigit():
        candidate = f"_{candidate}"
    return candidate


def _sanitize_doc_comment(value: str) -> str:
    return " ".join(part for part in value.strip().splitlines() if part).strip()


def _normalize_token(value: str) -> str:
    return (value or "").strip().casefold()


def _leaf_token(value: str) -> str:
    normalized = _normalize_token(value)
    if "." not in normalized:
        return normalized
    return normalized.rsplit(".", 1)[-1]


def _class_lineage(class_config: ClassConfig) -> list[ClassConfig]:
    lineage: list[ClassConfig] = []
    cursor: ClassConfig | None = class_config
    while cursor is not None:
        lineage.append(cursor)
        cursor = cursor.parent_class
    lineage.reverse()
    return lineage


def _variant_import_owner(class_config: ClassConfig) -> ClassConfig:
    parent = class_config.parent_class
    return parent if parent is not None else class_config


def _render_json_string_literal(payload: dict[str, object]) -> str:
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    return "  r'''\n" + rendered + "\n''',\n"


def _iter_object_list(value: object, *, label: str) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"Expected {label} to be a list of objects.")
    result: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"Expected {label} entries to be JSON objects.")
        result.append(item)
    return result


def _require_object(value: object, *, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"Expected {label} to be a JSON object.")
    return value


def _require_string(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Expected key {key!r} to be a non-empty string.")
    return value


def _optional_string(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Expected key {key!r} to be a string when present.")
    return value


__all__ = [
    "DartApiPublicPackageBindingsRendererLanguage",
    "DartApiPublicPackageClientRendererLanguage",
    "DartApiPublicPackageLibraryRendererLanguage",
]
