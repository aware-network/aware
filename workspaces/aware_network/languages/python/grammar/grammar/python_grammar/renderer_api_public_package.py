from __future__ import annotations

import keyword
from dataclasses import dataclass
from pathlib import Path
from pprint import pformat
from typing import Iterable, cast
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
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_utils.string_transform import to_pascal_case, to_snake_case


@dataclass(frozen=True)
class _PythonTypeBinding:
    class_ref: str
    class_name: str
    module_path: str
    absolute_import: bool = False


@dataclass(frozen=True)
class _EndpointRenderBinding:
    endpoint_ref: str
    api_name: str
    capability_name: str
    endpoint_name: str
    description: str | None
    request: _PythonTypeBinding
    response: _PythonTypeBinding | None
    stream_events: tuple[_PythonTypeBinding, ...]

    @property
    def endpoint_constant_name(self) -> str:
        return _endpoint_constant_name(self.endpoint_ref)

    @property
    def capability_client_class_name(self) -> str:
        return f"{to_pascal_case(self.api_name)}{to_pascal_case(self.capability_name)}CapabilityClient"

    @property
    def method_name(self) -> str:
        return _safe_python_identifier(self.endpoint_name)

    @property
    def stream_alias_name(self) -> str:
        return (
            f"{to_pascal_case(self.api_name)}"
            f"{to_pascal_case(self.capability_name)}"
            f"{to_pascal_case(self.endpoint_name)}StreamEvent"
        )


class _PythonApiPublicPackageRendererBase(ObjectConfigGraphRendererLanguage):
    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy):
        super().__init__(layout_strategy=layout_strategy)
        self._type_bindings_by_identity: dict[str, _PythonTypeBinding] = {}
        self._external_type_bindings_by_identity: dict[str, _PythonTypeBinding] = {}

    @property
    @override
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    @property
    @override
    def indent(self) -> int:
        return 4

    @property
    @override
    def comment_prefix(self) -> str:
        return "#"

    @override
    def define_assemblers(self) -> None:
        return

    @override
    def set_policy(self, policy: ObjectConfigGraphRendererPolicy | None) -> None:
        _ = policy

    @override
    def bind_object_config_graph(self, graph: ObjectConfigGraph) -> None:
        self._type_bindings_by_identity = _build_python_type_binding_index(
            graph=graph,
            layout_strategy=self.layout_strategy,
        )
        self._external_type_bindings_by_identity = _build_external_python_type_binding_index(
            payload=self.profile_inputs.get("api.external_python_type_index")
        )

    @override
    def create_empty_code(self) -> Code:
        raise NotImplementedError

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
        _ = meta_objects
        _ = writer
        _ = schema
        _ = class_to_class_config_map
        _ = base_class_module
        _ = base_class_name
        raise NotImplementedError

    def _require_payload(self, key: str) -> dict[str, object]:
        payload = self.profile_inputs.get(key)
        if not isinstance(payload, dict):
            raise ValueError(f"Expected profile input {key!r} to be a JSON object.")
        return payload

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
                            "Product A renderer missing interface endpoint "
                            + f"{endpoint_ref!r} in api.interface_spec"
                        )

                    invocation = invocation_by_ref.get(endpoint_ref)
                    if invocation is None:
                        raise ValueError(
                            "Product A renderer missing invocation endpoint "
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

                    stream_event_bindings: list[_PythonTypeBinding] = []
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
                            "Product A renderer request class drift for "
                            + f"{endpoint_ref!r}: public_plan={request_ref!r}, invocation={invocation_request_ref!r}"
                        )

                    bindings.append(
                        _EndpointRenderBinding(
                            endpoint_ref=endpoint_ref,
                            api_name=api_name,
                            capability_name=capability_name,
                            endpoint_name=endpoint_name,
                            description=_optional_string(endpoint, "description"),
                            request=request_binding,
                            response=response_binding,
                            stream_events=tuple(stream_event_bindings),
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

    def _resolve_type_binding(self, class_ref: str) -> _PythonTypeBinding:
        normalized = _normalize_token(class_ref)
        for identity in _type_binding_identities(class_ref):
            external_binding = self._external_type_bindings_by_identity.get(identity)
            if external_binding is not None:
                return external_binding

        for identity in _type_binding_identities(class_ref):
            binding = self._type_bindings_by_identity.get(identity)
            if binding is not None:
                return binding

        external_matches = {
            candidate
            for identity, candidate in self._external_type_bindings_by_identity.items()
            if identity.endswith(f".{normalized}") or identity == _leaf_token(normalized)
        }
        if len(external_matches) == 1:
            return next(iter(external_matches))
        if len(external_matches) > 1:
            raise ValueError(f"Ambiguous Product A external Python type binding for class_ref {class_ref!r}.")

        matches = {
            candidate
            for identity, candidate in self._type_bindings_by_identity.items()
            if identity.endswith(f".{normalized}") or identity == _leaf_token(normalized)
        }
        if not matches:
            raise ValueError(f"Could not resolve Product A Python type binding for class_ref {class_ref!r}.")
        if len(matches) > 1:
            raise ValueError(f"Ambiguous Product A Python type binding for class_ref {class_ref!r}.")
        return next(iter(matches))


class PythonApiPublicPackageBindingsRendererLanguage(_PythonApiPublicPackageRendererBase):
    """Emit compiled `_bindings.py` for Python Product A public packages."""

    @override
    def extra_output_paths(self) -> list[Path]:
        return [Path("_bindings.py")]

    @override
    def create_empty_code(self) -> Code:
        return build_renderer_empty_code(
            language=CodeLanguage.python,
            renderer_key=type(self).__name__,
        )

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
        _ = writer.token(
            render_python_api_public_package_bindings_module(
                import_root=self.layout_strategy.import_root,
                public_plan=public_plan,
                interface_spec=interface_spec,
                invocation_manifest=invocation_manifest,
                endpoint_bindings=bindings,
            )
        )


class PythonApiPublicPackageClientRendererLanguage(_PythonApiPublicPackageRendererBase):
    """Emit compiled `client.py` wrappers for Python Product A public packages."""

    @override
    def extra_output_paths(self) -> list[Path]:
        return [Path("client.py")]

    @override
    def create_empty_code(self) -> Code:
        return build_renderer_empty_code(
            language=CodeLanguage.python,
            renderer_key=type(self).__name__,
        )

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
        _ = writer.token(
            render_python_api_public_package_client_module(
                import_root=self.layout_strategy.import_root,
                endpoint_bindings=bindings,
            )
        )


def render_python_api_public_package_bindings_module(
    *,
    import_root: str | None,
    public_plan: dict[str, object],
    interface_spec: dict[str, object],
    invocation_manifest: dict[str, object],
    endpoint_bindings: tuple[_EndpointRenderBinding, ...],
) -> str:
    package_name = _require_string(public_plan, "package_name")
    fqn_prefix = _require_string(public_plan, "fqn_prefix")
    endpoint_constants = sorted(
        ((binding.endpoint_constant_name, binding.endpoint_ref) for binding in endpoint_bindings),
        key=lambda item: item[0],
    )

    lines: list[str] = []
    lines.append("# GENERATED CODE - DO NOT MODIFY BY HAND")
    lines.append("# Compiled API client bindings for Python SDK wrappers.")
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from typing import Final")
    lines.append("")
    lines.append("from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload")
    lines.append("from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload")
    lines.append("")
    lines.append(f"API_PACKAGE_NAME: Final[str] = {package_name!r}")
    lines.append(f"API_FQN_PREFIX: Final[str] = {fqn_prefix!r}")
    lines.append("")
    enriched_interface_spec = _attach_python_binding_refs_to_api_payload(
        payload=interface_spec,
        endpoint_bindings=endpoint_bindings,
        import_root=import_root,
        endpoint_ref_key="discriminant",
        include_python_model_refs=False,
        label="api.interface_spec",
    )
    lines.append("API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(")
    lines.append(
        _indent_block(
            pformat(_scrub_public_api_client_payload(enriched_interface_spec), width=100, sort_dicts=True),
            prefix="    ",
        )
    )
    lines.append(")")
    lines.append("")
    lines.append("API_INVOCATION_MANIFEST: Final[LoadedApiInvocationManifest] = load_api_invocation_manifest_payload(")
    enriched_invocation_manifest = _attach_python_binding_refs_to_api_payload(
        payload=invocation_manifest,
        endpoint_bindings=endpoint_bindings,
        import_root=import_root,
        endpoint_ref_key="endpoint_ref",
        include_python_model_refs=True,
        label="api.invocation_manifest",
    )
    lines.append(
        _indent_block(
            pformat(_scrub_public_api_client_payload(enriched_invocation_manifest), width=100, sort_dicts=True),
            prefix="    ",
        )
    )
    lines.append(")")
    lines.append("")
    for constant_name, endpoint_ref in endpoint_constants:
        lines.append(f"{constant_name}: Final[str] = {endpoint_ref!r}")
    lines.append("")
    lines.append("ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {")
    for constant_name, endpoint_ref in endpoint_constants:
        lines.append(f"    {endpoint_ref!r}: {constant_name},")
    lines.append("}")
    lines.append("")
    lines.append("__all__ = [")
    lines.append("    'API_FQN_PREFIX',")
    lines.append("    'API_INTERFACE_SPEC',")
    lines.append("    'API_INVOCATION_MANIFEST',")
    lines.append("    'API_PACKAGE_NAME',")
    lines.append("    'ENDPOINT_REF_BY_NAME',")
    for constant_name, _ in endpoint_constants:
        lines.append(f"    {constant_name!r},")
    lines.append("]")
    lines.append("")
    return "\n".join(lines)


def render_python_api_public_package_client_module(
    *,
    import_root: str | None,
    endpoint_bindings: tuple[_EndpointRenderBinding, ...],
) -> str:
    root_client_class = _root_client_class_name(import_root=import_root)
    type_bindings = _collect_imported_types(endpoint_bindings=endpoint_bindings)
    import_aliases = _build_import_aliases(type_bindings=type_bindings)

    lines: list[str] = []
    lines.append("# GENERATED CODE - DO NOT MODIFY BY HAND")
    lines.append("# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.")
    lines.append("from __future__ import annotations")
    lines.append("")
    typing_imports: list[str] = []
    if any(binding.response is None for binding in endpoint_bindings):
        typing_imports.append("Any")
    if any(binding.stream_events for binding in endpoint_bindings):
        typing_imports.append("AsyncIterator")
    typing_imports.append("cast")
    lines.append(f"from typing import {', '.join(typing_imports)}")
    lines.append("")
    lines.append("from aware_api import AwareApiEndpointInvoker")
    lines.append("from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST")

    endpoint_constants = sorted({binding.endpoint_constant_name for binding in endpoint_bindings})
    if endpoint_constants:
        lines.append(f"from ._bindings import {', '.join(endpoint_constants)}")

    imports_by_module: dict[str, list[tuple[str, str]]] = {}
    absolute_import_modules: set[str] = set()
    for type_binding in type_bindings:
        alias = import_aliases[type_binding.class_ref]
        imports_by_module.setdefault(type_binding.module_path, []).append((type_binding.class_name, alias))
        if type_binding.absolute_import:
            absolute_import_modules.add(type_binding.module_path)

    for module_path in sorted(imports_by_module, key=str.casefold):
        rendered_symbols: list[str] = []
        seen: set[tuple[str, str]] = set()
        for class_name, alias in sorted(imports_by_module[module_path], key=lambda item: (item[0], item[1])):
            key = (class_name, alias)
            if key in seen:
                continue
            seen.add(key)
            rendered_symbols.append(class_name if alias == class_name else f"{class_name} as {alias}")
        relative_module_path = module_path
        if import_root:
            prefix = f"{import_root}."
            if relative_module_path.startswith(prefix):
                relative_module_path = relative_module_path[len(prefix):]
        if module_path in absolute_import_modules:
            lines.append(f"from {module_path} import {', '.join(rendered_symbols)}")
        else:
            lines.append(f"from .{relative_module_path} import {', '.join(rendered_symbols)}")

    lines.append("")

    stream_alias_names: list[str] = []
    for binding in endpoint_bindings:
        if not binding.stream_events:
            continue
        stream_alias_names.append(binding.stream_alias_name)
        alias_targets = " | ".join(import_aliases[event.class_ref] for event in binding.stream_events)
        lines.append(f"{binding.stream_alias_name} = {alias_targets}")
    if stream_alias_names:
        lines.append("")

    by_api: dict[str, dict[str, list[_EndpointRenderBinding]]] = {}
    for binding in endpoint_bindings:
        by_api.setdefault(binding.api_name, {}).setdefault(binding.capability_name, []).append(binding)

    api_client_class_names: list[str] = []
    capability_client_class_names: list[str] = []

    for api_name in sorted(by_api, key=str.casefold):
        capability_bindings = by_api[api_name]
        for capability_name in sorted(capability_bindings, key=str.casefold):
            ordered_bindings = sorted(
                capability_bindings[capability_name],
                key=lambda item: (item.endpoint_name.casefold(), item.endpoint_ref),
            )
            capability_client_class_names.append(ordered_bindings[0].capability_client_class_name)
            lines.extend(
                _render_capability_client_class(
                    class_name=ordered_bindings[0].capability_client_class_name,
                    endpoint_bindings=ordered_bindings,
                    import_aliases=import_aliases,
                )
            )
            lines.append("")

        api_client_class_name = f"{to_pascal_case(api_name)}ApiClient"
        api_client_class_names.append(api_client_class_name)
        lines.extend(
            _render_api_client_class(
                api_name=api_name,
                class_name=api_client_class_name,
                capability_names=tuple(sorted(capability_bindings, key=str.casefold)),
            )
        )
        lines.append("")

    lines.extend(
        _render_root_client_class(
            class_name=root_client_class,
            api_names=tuple(sorted(by_api, key=str.casefold)),
        )
    )
    lines.append("")
    lines.append("__all__ = [")
    lines.append(f"    {root_client_class!r},")
    for class_name in api_client_class_names:
        lines.append(f"    {class_name!r},")
    for class_name in capability_client_class_names:
        lines.append(f"    {class_name!r},")
    for alias_name in sorted(stream_alias_names):
        lines.append(f"    {alias_name!r},")
    lines.append("]")
    lines.append("")
    return "\n".join(lines)


def _render_capability_client_class(
    *,
    class_name: str,
    endpoint_bindings: list[_EndpointRenderBinding],
    import_aliases: dict[str, str],
) -> list[str]:
    lines: list[str] = []
    lines.append(f"class {class_name}:")
    lines.append("    def __init__(self, client: AwareApiEndpointInvoker) -> None:")
    lines.append("        self._client = client")
    for binding in endpoint_bindings:
        response_annotation = _response_annotation(binding=binding, import_aliases=import_aliases)
        lines.append("")
        lines.append(
            "    async def "
            + f"{binding.method_name}(self, request: {import_aliases[binding.request.class_ref]}) "
            + f"-> {response_annotation}:"
        )
        if binding.description:
            lines.append(f'        """{_sanitize_docstring(binding.description)}"""')
        lines.append("        return cast(")
        lines.append(f"            {response_annotation},")
        lines.append("            await self._client.invoke_api_endpoint(")
        lines.append("                manifest=API_INVOCATION_MANIFEST,")
        lines.append(f"                endpoint_ref={binding.endpoint_constant_name},")
        lines.append("                request_payload=request,")
        lines.append("            ),")
        lines.append("        )")
        if binding.stream_events:
            stream_annotation = binding.stream_alias_name
            lines.append("")
            lines.append(
                "    async def "
                + f"stream_{binding.method_name}(self, request: {import_aliases[binding.request.class_ref]}) "
                + f"-> AsyncIterator[{stream_annotation}]:"
            )
            if binding.description:
                lines.append(f'        """{_sanitize_docstring(binding.description)}"""')
            lines.append("        async for event in self._client.stream_api_endpoint(")
            lines.append("            manifest=API_INVOCATION_MANIFEST,")
            lines.append(f"            endpoint_ref={binding.endpoint_constant_name},")
            lines.append("            request_payload=request,")
            lines.append("        ):")
            lines.append(f"            yield cast({stream_annotation}, event)")
    return lines


def _render_api_client_class(
    *,
    api_name: str,
    class_name: str,
    capability_names: tuple[str, ...],
) -> list[str]:
    lines: list[str] = []
    lines.append(f"class {class_name}:")
    lines.append("    def __init__(self, client: AwareApiEndpointInvoker) -> None:")
    lines.append("        self._client = client")
    for capability_name in capability_names:
        capability_class_name = f"{to_pascal_case(api_name)}{to_pascal_case(capability_name)}CapabilityClient"
        lines.append(f"        self.{_safe_python_identifier(capability_name)} = {capability_class_name}(client)")
    return lines


def _render_root_client_class(
    *,
    class_name: str,
    api_names: tuple[str, ...],
) -> list[str]:
    lines: list[str] = []
    lines.append(f"class {class_name}:")
    lines.append("    def __init__(self, client: AwareApiEndpointInvoker) -> None:")
    lines.append("        self._client = client")
    lines.append("        self.interface_spec = API_INTERFACE_SPEC")
    lines.append("        self.invocation_manifest = API_INVOCATION_MANIFEST")
    for api_name in api_names:
        api_client_class_name = f"{to_pascal_case(api_name)}ApiClient"
        lines.append(f"        self.{_safe_python_identifier(api_name)} = {api_client_class_name}(client)")
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


def _attach_python_binding_refs_to_api_payload(
    *,
    payload: dict[str, object],
    endpoint_bindings: tuple[_EndpointRenderBinding, ...],
    import_root: str | None,
    endpoint_ref_key: str,
    include_python_model_refs: bool,
    label: str,
) -> dict[str, object]:
    copied = _copy_json_like(payload)
    if not isinstance(copied, dict):
        raise ValueError(f"Expected {label} to be a JSON object.")
    copied_payload = cast(dict[str, object], copied)

    bindings_by_ref = {binding.endpoint_ref: binding for binding in endpoint_bindings}
    for api in _iter_object_list(copied_payload.get("apis"), label=f"{label}.apis"):
        api_name = _require_string(api, "name")
        for capability in _iter_object_list(api.get("capabilities"), label=f"{api_name}.capabilities"):
            capability_name = _require_string(capability, "name")
            for endpoint in _iter_object_list(
                capability.get("endpoints"),
                label=f"{api_name}.{capability_name}.endpoints",
            ):
                endpoint_ref = _require_string(endpoint, endpoint_ref_key)
                binding = bindings_by_ref.get(endpoint_ref)
                if binding is None:
                    continue

                request = _require_object(endpoint.get("request"), label=f"{endpoint_ref}.request")
                request["class_ref"] = binding.request.class_ref
                if include_python_model_refs:
                    request["python_model_ref"] = _python_model_ref(
                        binding=binding.request,
                        import_root=import_root,
                    )

                response = endpoint.get("response")
                if response is not None and binding.response is not None:
                    response_object = _require_object(response, label=f"{endpoint_ref}.response")
                    response_object["class_ref"] = binding.response.class_ref
                    if include_python_model_refs:
                        response_object["python_model_ref"] = _python_model_ref(
                            binding=binding.response,
                            import_root=import_root,
                        )

                stream = endpoint.get("stream")
                if stream is None:
                    continue
                stream_object = _require_object(stream, label=f"{endpoint_ref}.stream")
                stream_bindings_by_ref: dict[str, _PythonTypeBinding] = {}
                for stream_event_binding in binding.stream_events:
                    for identity in _type_binding_identities(stream_event_binding.class_ref):
                        stream_bindings_by_ref.setdefault(identity, stream_event_binding)
                for event in _iter_object_list(
                    stream_object.get("events"),
                    label=f"{endpoint_ref}.stream.events",
                ):
                    stream_binding = None
                    for identity in _type_binding_identities(
                        _require_string(event, "class_ref")
                    ):
                        stream_binding = stream_bindings_by_ref.get(identity)
                        if stream_binding is not None:
                            break
                    if stream_binding is None:
                        continue
                    event["class_ref"] = stream_binding.class_ref
                    if include_python_model_refs:
                        event["python_model_ref"] = _python_model_ref(
                            binding=stream_binding,
                            import_root=import_root,
                        )

    return copied_payload


def _python_model_ref(*, binding: _PythonTypeBinding, import_root: str | None) -> str:
    module_path = binding.module_path.strip(".")
    root = (import_root or "").strip(".")
    if binding.absolute_import:
        return f"{module_path}.{binding.class_name}"
    if root and module_path and not module_path.startswith(f"{root}."):
        module_path = f"{root}.{module_path}"
    elif root and not module_path:
        module_path = root
    return f"{module_path}.{binding.class_name}"


def _copy_json_like(value: object) -> object:
    if isinstance(value, dict):
        return {key: _copy_json_like(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy_json_like(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_copy_json_like(item) for item in value)
    return value


def _build_python_type_binding_index(
    *,
    graph: ObjectConfigGraph,
    layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
) -> dict[str, _PythonTypeBinding]:
    bindings: dict[str, _PythonTypeBinding] = {}
    for node in graph.object_config_graph_nodes:
        class_config = node.class_config
        if class_config is None:
            continue
        module_path = layout_strategy.get_module_import_path(layout_strategy.get_class_file_path(class_config))
        binding = _PythonTypeBinding(
            class_ref=class_config.class_fqn,
            class_name=class_config.name,
            module_path=module_path,
        )
        for identity in {
            *_type_binding_identities(class_config.class_fqn),
            *_type_binding_identities(class_config.name),
        }:
            bindings.setdefault(identity, binding)
    return bindings


def _build_external_python_type_binding_index(*, payload: object) -> dict[str, _PythonTypeBinding]:
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError("Expected profile input 'api.external_python_type_index' to be a JSON object.")

    bindings: dict[str, _PythonTypeBinding] = {}
    for label in ("classes", "enums"):
        raw_entries = payload.get(label, {})
        if not isinstance(raw_entries, dict):
            raise ValueError(
                "Expected profile input 'api.external_python_type_index' field "
                + f"{label!r} to be a JSON object."
            )
        for raw_entry in raw_entries.values():
            if not isinstance(raw_entry, dict):
                raise ValueError(
                    "Expected profile input 'api.external_python_type_index' entries "
                    + f"under {label!r} to be JSON objects."
                )
            class_ref = _optional_string(raw_entry, "class_ref") or _optional_string(raw_entry, "enum_ref")
            if not class_ref:
                continue
            module_path = _require_string(raw_entry, "module")
            class_name = _require_string(raw_entry, "name")
            binding = _PythonTypeBinding(
                class_ref=class_ref,
                class_name=class_name,
                module_path=module_path,
                absolute_import=True,
            )
            for identity in {
                *_type_binding_identities(class_ref),
                *_type_binding_identities(class_name),
            }:
                bindings.setdefault(identity, binding)
    return bindings


def _collect_imported_types(
    *,
    endpoint_bindings: tuple[_EndpointRenderBinding, ...],
) -> tuple[_PythonTypeBinding, ...]:
    ordered: dict[str, _PythonTypeBinding] = {}
    for binding in endpoint_bindings:
        ordered.setdefault(binding.request.class_ref, binding.request)
        if binding.response is not None:
            ordered.setdefault(binding.response.class_ref, binding.response)
        for event in binding.stream_events:
            ordered.setdefault(event.class_ref, event)
    return tuple(ordered.values())


def _build_import_aliases(
    *,
    type_bindings: Iterable[_PythonTypeBinding],
) -> dict[str, str]:
    grouped: dict[str, list[_PythonTypeBinding]] = {}
    for binding in type_bindings:
        grouped.setdefault(binding.class_name, []).append(binding)

    aliases: dict[str, str] = {}
    for class_name, bindings in grouped.items():
        if len(bindings) == 1:
            aliases[bindings[0].class_ref] = class_name
            continue
        for binding in sorted(bindings, key=lambda item: (item.module_path.casefold(), item.class_ref.casefold())):
            module_suffix = "_".join(
                _safe_python_identifier(part)
                for part in binding.module_path.split(".")[-2:]
                if part
            )
            aliases[binding.class_ref] = f"{class_name}_{module_suffix}" if module_suffix else class_name
    return aliases


def _response_annotation(
    *,
    binding: _EndpointRenderBinding,
    import_aliases: dict[str, str],
) -> str:
    if binding.response is not None:
        return import_aliases[binding.response.class_ref]
    return "Any"


def _root_client_class_name(*, import_root: str | None) -> str:
    token = import_root or "AwareApiPublicPackage"
    return f"{to_pascal_case(token)}Client"


def _endpoint_constant_name(endpoint_ref: str) -> str:
    token = endpoint_ref.replace(".", "__").replace("-", "_")
    token = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in token)
    token = token.upper().strip("_")
    return f"{token}_ENDPOINT_REF"


def _safe_python_identifier(value: str) -> str:
    candidate = to_snake_case(value or "").strip("_") or "value"
    candidate = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in candidate)
    if candidate and candidate[0].isdigit():
        candidate = f"_{candidate}"
    if keyword.iskeyword(candidate):
        candidate = f"{candidate}_"
    return candidate


def _sanitize_docstring(value: str) -> str:
    return _scrub_public_api_client_text(value).replace('"""', '\\"\\"\\"').strip()


def _scrub_public_api_client_text(value: str) -> str:
    return (
        value.replace("Product A/Product B", "API/service")
        .replace("Generated Product A", "Generated API client")
        .replace("generated Product A", "generated API client")
        .replace("Product A consumers", "API client consumers")
        .replace("Product A", "generated API client")
        .replace("Generated Product B", "Generated service protocol")
        .replace("generated Product B", "generated service protocol")
        .replace("Product B", "service protocol")
        .replace("product A", "generated API client")
        .replace("product B", "service protocol")
    )


def _scrub_public_api_client_payload(value: object) -> object:
    if isinstance(value, str):
        return _scrub_public_api_client_text(value)
    if isinstance(value, list):
        return [_scrub_public_api_client_payload(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_scrub_public_api_client_payload(item) for item in value)
    if isinstance(value, dict):
        return {
            key: _scrub_public_api_client_payload(item)
            for key, item in value.items()
        }
    return value


def _normalize_token(value: str) -> str:
    return (value or "").strip().casefold()


def _type_binding_identities(value: str) -> tuple[str, ...]:
    normalized = _normalize_token(value)
    if not normalized:
        return ()
    variants = {normalized, _leaf_token(normalized)}
    parts = [part for part in normalized.split(".") if part]
    if "default" in parts[1:-1]:
        variants.add(".".join(part for part in parts if part != "default"))
    return tuple(sorted(variant for variant in variants if variant))


def _leaf_token(value: str) -> str:
    normalized = _normalize_token(value)
    if "." not in normalized:
        return normalized
    return normalized.rsplit(".", 1)[-1]


def _indent_block(text: str, *, prefix: str) -> str:
    return "\n".join(f"{prefix}{line}" if line else prefix.rstrip() for line in text.splitlines())


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
    "PythonApiPublicPackageBindingsRendererLanguage",
    "PythonApiPublicPackageClientRendererLanguage",
    "render_python_api_public_package_bindings_module",
    "render_python_api_public_package_client_module",
]
