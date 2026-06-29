"""Python Meta-runtime handler provider renderer.

This renderer emits Meta-native generated language-handler provider modules.
It does not emit or adapt old ``aware_runtime`` handler manifests.
"""

from __future__ import annotations

import json
import re
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from collections.abc import Iterator
from typing import Mapping
from uuid import UUID

from aware_code.section.writer import CodeSectionWriter
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta.graph.config.render.renderer_language import (
    ObjectConfigGraphRendererLanguage,
    build_renderer_empty_code,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_attribute_config import (
    FunctionConfigAttributeConfig,
)
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_utils.string_transform import to_snake_case
from python_grammar.import_grouping import (
    PythonImportGroupingPolicy,
    group_python_imports,
    semantic_import_roots_from_renderer_inputs,
)
from python_grammar.renderer_runtime_handlers import (
    _safe_identifier,
    runtime_handler_impl_module_import,
    runtime_handler_impl_relative_path,
)
from python_grammar.renderer_runtime_handlers_aware import (
    _GeneratedImplLogic,
    PythonRendererRuntimeHandlersAware,
    _RenderedSignature,
)
from python_grammar.renderer_policy import DEFAULT_ORM_SUPPORT_IMPORT_ROOTS
from python_grammar.renderer_stable_ids import (
    PYTHON_STABLE_IDS_IMPORT_ROOT_POLICY_KEY,
    resolve_python_stable_ids_module_import,
)


def _emit_token(writer: CodeSectionWriter, txt: str) -> None:
    _ = writer.token(txt)


def _iter_graph_function_configs(
    graph: ObjectConfigGraph,
) -> Iterator[FunctionConfig]:
    seen: set[UUID] = set()
    for node in graph.object_config_graph_nodes:
        cls = node.class_config
        if cls is None:
            continue
        for link in cls.class_config_function_configs:
            fn = link.function_config
            if fn.id in seen:
                continue
            seen.add(fn.id)
            yield fn


def _index_graph_function_configs(
    graph: ObjectConfigGraph,
) -> tuple[dict[UUID, FunctionConfig], dict[UUID, FunctionConfig]]:
    by_id: dict[UUID, FunctionConfig] = {}
    by_code_section_id: dict[UUID, FunctionConfig] = {}
    for fn in _iter_graph_function_configs(graph):
        by_id[fn.id] = fn
        code_section_id = fn.code_section_function_id
        if code_section_id is not None and code_section_id not in by_code_section_id:
            by_code_section_id[code_section_id] = fn
    return by_id, by_code_section_id


class _IndentWriter:
    def __init__(self, writer: CodeSectionWriter, *, indent_size: int):
        self._writer = writer
        self._indent_size = indent_size
        self._level = 0

    def __enter__(self) -> _IndentWriter:
        self._level += 1
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self._level -= 1

    def write(self, txt: str) -> None:
        if self._level <= 0:
            _emit_token(self._writer, txt)
            return
        prefix = " " * (self._level * self._indent_size)
        out: list[str] = []
        for line in txt.splitlines(keepends=True):
            out.append(prefix + line if line.strip() else line)
        _emit_token(self._writer, "".join(out))


class PythonMetaRuntimeHandlersRenderer(ObjectConfigGraphRendererLanguage):
    """Emit ``AWARE_META_GRAPH_HANDLERS`` provider modules."""

    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy):
        super().__init__(layout_strategy)
        self._warnings: list[str] = []
        self._class_by_id: dict[UUID, ClassConfig] = {}
        self._stable_ids_source_graph: ObjectConfigGraph | None = None
        self._function_impl_source_by_id: dict[UUID, FunctionConfig] = {}
        self._function_impl_source_by_code_section_id: dict[UUID, FunctionConfig] = {}
        self._stable_ids_import_root: str | None = None
        self._bound_graph: ObjectConfigGraph | None = None
        self._function_impl_ownership: str = "authored"
        self._function_impl_parity_policy: str = "off"
        self._compiler_delegate: PythonRendererRuntimeHandlersAware | None = None
        self._compiler_render_cache: dict[
            tuple[str, str, str],
            tuple[_RenderedSignature, _GeneratedImplLogic | None],
        ] = {}
        self._owner_snake_name_cache: dict[tuple[str, str], str] = {}
        self._function_token_cache: dict[tuple[str, str, str, str], str] = {}
        self._callable_name_cache: dict[tuple[str, str, str, str, str], str] = {}
        self._class_function_edge_cache: dict[
            tuple[str, str],
            ClassConfigFunctionConfig | None,
        ] = {}
        self._input_edges_cache: dict[
            str,
            tuple[FunctionConfigAttributeConfig, ...],
        ] = {}
        self._identity_edges_cache: dict[
            str,
            tuple[FunctionConfigAttributeConfig, ...],
        ] = {}
        self._render_phase_timings: dict[str, float] = {}

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    @property
    def indent(self) -> int:
        return 4

    @property
    def comment_prefix(self) -> str:
        return "#"

    def define_assemblers(self):
        return None

    def clear_warnings(self) -> None:
        self._warnings = []

    def get_warnings(self) -> list[str]:
        return list(self._warnings)

    def get_render_phase_timings(self) -> dict[str, float]:
        return dict(self._render_phase_timings)

    def set_policy(self, policy: object | None) -> None:
        self._clear_compiler_render_cache()
        self._clear_bound_graph_fact_cache()
        self._stable_ids_source_graph = None
        self._function_impl_source_by_id = {}
        self._function_impl_source_by_code_section_id = {}
        self._stable_ids_import_root = None
        self._function_impl_ownership = "authored"
        self._function_impl_parity_policy = "off"
        if policy is None:
            return
        if not isinstance(policy, Mapping):
            return
        raw_import_root = policy.get(PYTHON_STABLE_IDS_IMPORT_ROOT_POLICY_KEY)
        if raw_import_root is not None:
            self._stable_ids_import_root = str(raw_import_root).strip() or None
        source_graph = policy.get("stable_ids_source_graph")
        if isinstance(source_graph, ObjectConfigGraph):
            self._stable_ids_source_graph = source_graph
        function_impl_source_graph = policy.get("function_impl_source_graph")
        if isinstance(function_impl_source_graph, ObjectConfigGraph):
            (
                self._function_impl_source_by_id,
                self._function_impl_source_by_code_section_id,
            ) = _index_graph_function_configs(function_impl_source_graph)
        ownership_raw = policy.get("function_impl_ownership")
        if ownership_raw is not None:
            ownership = str(ownership_raw).strip().lower()
            if ownership not in {"authored", "compiler"}:
                raise ValueError("function_impl_ownership must be one of: authored, compiler " + f"(got {ownership!r})")
            self._function_impl_ownership = ownership
        parity_raw = policy.get("function_impl_parity_policy")
        if parity_raw is not None:
            parity = str(parity_raw).strip().lower()
            if parity not in {"off", "warn", "error"}:
                raise ValueError("function_impl_parity_policy must be one of: off, warn, error " + f"(got {parity!r})")
            self._function_impl_parity_policy = parity

    def create_empty_code(self) -> Code:
        return build_renderer_empty_code(
            language=CodeLanguage.python,
            renderer_key=type(self).__name__,
        )

    def bind_object_config_graph(self, graph: ObjectConfigGraph) -> None:
        self._clear_compiler_render_cache()
        self._clear_bound_graph_fact_cache()
        self._bound_graph = graph
        self._class_by_id = {
            node.class_config.id: node.class_config
            for node in graph.object_config_graph_nodes
            if node.class_config is not None
        }

    def bind_profile_inputs(self, profile_inputs: Mapping[str, object]) -> None:
        self._clear_compiler_render_cache()
        super().bind_profile_inputs(profile_inputs)

    def set_external_class_lookup(self, external_class_lookup: dict[UUID, ClassConfig]) -> None:
        self._clear_compiler_render_cache()
        super().set_external_class_lookup(external_class_lookup)

    def set_external_graphs(self, external_graphs: list[ObjectConfigGraph]) -> None:
        self._clear_compiler_render_cache()
        super().set_external_graphs(external_graphs)

    def _clear_compiler_render_cache(self) -> None:
        self._compiler_delegate = None
        self._compiler_render_cache.clear()

    def _clear_bound_graph_fact_cache(self) -> None:
        self._owner_snake_name_cache.clear()
        self._function_token_cache.clear()
        self._callable_name_cache.clear()
        self._class_function_edge_cache.clear()
        self._input_edges_cache.clear()
        self._identity_edges_cache.clear()

    @contextmanager
    def _record_render_phase(self, name: str) -> Iterator[None]:
        started_at = perf_counter()
        try:
            yield
        finally:
            duration_s = round(max(perf_counter() - started_at, 0.0), 6)
            self._render_phase_timings[name] = round(
                self._render_phase_timings.get(name, 0.0) + duration_s,
                6,
            )

    def extra_output_paths(self) -> list[Path]:
        ext = self.layout_strategy.get_file_extension()
        return [Path("handlers") / "_generated" / f"meta_handlers{ext}"]

    def renders_only_extra_output_paths(self) -> bool:
        return True

    def requires_graph_metadata_hydration(self) -> bool:
        return self._function_impl_ownership == "compiler"

    def emit_file(
        self,
        meta_objects: list[object],
        writer: CodeSectionWriter,
        schema: str = "default",
        class_to_class_config_map: dict[UUID, ClassConfig] | None = None,
        base_class_module: str | None = None,
        base_class_name: str | None = None,
    ) -> None:
        _ = schema, class_to_class_config_map, base_class_module, base_class_name
        if meta_objects and not all(isinstance(obj, FunctionConfig) for obj in meta_objects):
            return
        self._emit_meta_handlers_file(writer=writer)

    def _emit_meta_handlers_file(self, *, writer: CodeSectionWriter) -> None:
        self._render_phase_timings.clear()
        with self._record_render_phase("entries"):
            entries = self._handler_entries()
        _emit_token(writer, "# This file is generated by AWARE. Do not edit.\n")
        _emit_token(writer, "from __future__ import annotations\n\n")
        with self._record_render_phase("base_imports"):
            imports = {
                "typing": {"cast"},
                "uuid": {"UUID"},
                "aware_code.types": {"JsonArray", "JsonObject"},
                "aware_meta.graph.instance.builder": {"build_object_instance_graph"},
                "aware_meta.graph.instance.diff_orm": {"build_object_instance_graph_changes_from_orm_change_set"},
                "aware_meta.runtime.handler_executor.contracts": {
                    "MetaGraphHandlerExecutionRequest",
                    "MetaGraphPreState",
                },
                "aware_meta.runtime.handler_executor.language_handler": {
                    "MetaGraphGeneratedLanguageHandlerCallable",
                    "MetaGraphGeneratedLanguageHandlerKey",
                    "MetaGraphGeneratedInvocationHandlerCallable",
                    "MetaGraphLanguageHandlerExecution",
                    "MetaGraphLanguageHandlerExecutionError",
                },
                "aware_meta.runtime.oig_model_reifier": {
                    "reify_oig_root_model",
                },
                "aware_meta.runtime.handler_executor.pre_state": {
                    "MetaGraphEmptyLaneBootstrap",
                    "MetaGraphEmptyLaneBootstrapCallable",
                },
                "aware_meta.runtime.handler_executor.argument_coercion": {
                    "coerce_meta_handler_call_kwargs",
                },
                "aware_meta.runtime.value_resolvers": {
                    "default_meta_enum_option_resolver",
                },
                "aware_meta_ontology.class_.class_config": {"ClassConfig"},
                "aware_meta_ontology.graph.instance.object_instance_graph": {
                    "ObjectInstanceGraph",
                },
                "aware_orm.models.orm_model": {"ORMModel"},
                "aware_orm.registry": {"ORMModelRegistry"},
                "aware_orm.session.change_collector": {"current_change_collector"},
                "pydantic": {"BaseModel"},
            }
        with self._record_render_phase("compiler_imports"):
            imports = self._merge_imports(
                imports,
                self._compiler_generated_imports(entries=entries),
            )
        with self._record_render_phase("grouped_imports"):
            self._emit_grouped_imports(writer=writer, imports=imports)
        with self._record_render_phase("generated_helpers"):
            self._emit_generated_helpers(writer=writer, entries=entries)
        with self._record_render_phase("constructor_entries"):
            constructor_entries = [(owner, link, fn) for owner, link, fn in entries if link.is_constructor]
        with self._record_render_phase("wrappers"):
            for owner, link, fn in entries:
                self._emit_wrapper(
                    writer=writer,
                    owner=owner,
                    link=link,
                    fn=fn,
                )
                _emit_token(writer, "\n\n")
                if not link.is_constructor:
                    continue
                self._emit_bootstrap(
                    writer=writer,
                    owner=owner,
                    fn=fn,
                )
                _emit_token(writer, "\n\n")

        with self._record_render_phase("invocation_wrappers"):
            for owner, link, fn in entries:
                self._emit_invocation_wrapper(
                    writer=writer,
                    owner=owner,
                    link=link,
                    fn=fn,
                )
                _emit_token(writer, "\n\n")

        with self._record_render_phase("registries"):
            self._emit_registry(
                writer=writer,
                entries=entries,
                registry_name="AWARE_META_GRAPH_HANDLERS",
                callable_suffix="handler",
                value_type="MetaGraphGeneratedLanguageHandlerCallable",
            )
            _emit_token(writer, "\n")
            self._emit_registry(
                writer=writer,
                entries=entries,
                registry_name="AWARE_META_GRAPH_INVOCATION_HANDLERS",
                callable_suffix="invocation_handler",
                value_type="MetaGraphGeneratedInvocationHandlerCallable",
            )
            _emit_token(writer, "\n")
            self._emit_registry(
                writer=writer,
                entries=constructor_entries,
                registry_name="AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS",
                callable_suffix="empty_lane_bootstrap",
                value_type="MetaGraphEmptyLaneBootstrapCallable",
            )
            _emit_token(writer, "\n")
        with self._record_render_phase("exports"):
            _emit_token(
                writer,
                "__all__ = [\n"
                '    "AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS",\n'
                '    "AWARE_META_GRAPH_HANDLERS",\n'
                '    "AWARE_META_GRAPH_INVOCATION_HANDLERS",\n'
                "]\n",
            )

    def _handler_entries(
        self,
    ) -> list[tuple[ClassConfig, ClassConfigFunctionConfig, FunctionConfig]]:
        entries: list[tuple[ClassConfig, ClassConfigFunctionConfig, FunctionConfig]] = []
        for owner in self._class_by_id.values():
            for link in owner.class_config_function_configs:
                entries.append((owner, link, link.function_config))
        entries.sort(key=lambda item: (item[0].name, item[1].position, str(item[2].id)))
        return entries

    def _emit_wrapper(
        self,
        *,
        writer: CodeSectionWriter,
        owner: ClassConfig,
        link: ClassConfigFunctionConfig,
        fn: FunctionConfig,
    ) -> None:
        wrapper_name = self._callable_name(owner=owner, fn=fn, suffix="handler")
        _emit_token(
            writer,
            f"async def {wrapper_name}(\n"
            "    request: MetaGraphHandlerExecutionRequest,\n"
            "    pre_state: MetaGraphPreState,\n"
            "    positional: JsonArray,\n"
            "    keyword: JsonObject,\n"
            ") -> MetaGraphLanguageHandlerExecution:\n",
        )
        with _IndentWriter(writer, indent_size=self.indent) as iw:
            iw.write(
                f"bound_input = _bind_{self._function_token(owner=owner, fn=fn)}"
                "(positional=positional, keyword=keyword)\n"
            )
            if not link.is_constructor:
                iw.write("root_model, target = _root_and_target_models_from_pre_state(\n")
                with iw:
                    iw.write("request=request,\n")
                    iw.write("pre_state=pre_state,\n")
                    iw.write(f"expected_class_name={owner.name!r},\n")
                iw.write(")\n")
                iw.write(
                    f"result = await _call_{self._function_token(owner=owner, fn=fn)}"
                    "(bound_input=bound_input, target=target)\n"
                )
                iw.write("changes, constructed_class_instance_ids = " "_changes_from_current_collector(\n")
                with iw:
                    iw.write("request=request,\n")
                    iw.write("pre_state=pre_state,\n")
                iw.write(")\n")
                iw.write(
                    "return MetaGraphLanguageHandlerExecution(\n"
                    "    success=True,\n"
                    '    payload=JsonObject({"value": _json_payload_value(result)}),\n'
                    "    changes=changes,\n"
                    "    root_object_id=root_model.id,\n"
                    "    root_class_instance_identity_id=pre_state.root_class_instance_identity_id,\n"
                    "    constructed_class_instance_ids=constructed_class_instance_ids,\n"
                    ")\n"
                )
                return
            iw.write(f"result = await _call_{self._function_token(owner=owner, fn=fn)}" "(bound_input=bound_input)\n")
            iw.write("if not isinstance(result, ORMModel):\n")
            with iw:
                iw.write(
                    "raise MetaGraphLanguageHandlerExecutionError(\n"
                    '    "Generated Meta constructor handler must return ORMModel."\n'
                    ")\n"
                )
            iw.write("_assert_constructor_owner_class(request=request, " f"expected_class_name={owner.name!r})\n")
            iw.write("root_object_id = pre_state.root_object_id\n")
            iw.write("if isinstance(root_object_id, UUID):\n")
            with iw:
                iw.write("result.id = root_object_id\n")
            iw.write("post_oig = _post_oig_with_root_model(\n")
            with iw:
                iw.write("request=request,\n")
                iw.write("pre_state=pre_state,\n")
                iw.write("root_model=result,\n")
            iw.write(")\n")
            iw.write(
                "return MetaGraphLanguageHandlerExecution(\n"
                "    success=True,\n"
                '    payload=JsonObject({"value": _json_payload_value(result)}),\n'
                "    post_oig=post_oig,\n"
                "    root_object_id=result.id,\n"
                "    root_class_instance_identity_id=pre_state.root_class_instance_identity_id,\n"
                "    constructed_class_instance_ids=_constructed_class_instance_ids_from_post_oig(\n"
                "        pre_state=pre_state,\n"
                "        post_oig=post_oig,\n"
                "    ),\n"
                ")\n"
            )

    def _emit_invocation_wrapper(
        self,
        *,
        writer: CodeSectionWriter,
        owner: ClassConfig,
        link: ClassConfigFunctionConfig,
        fn: FunctionConfig,
    ) -> None:
        wrapper_name = self._callable_name(owner=owner, fn=fn, suffix="invocation_handler")
        _emit_token(
            writer,
            f"async def {wrapper_name}(\n"
            "    request: MetaGraphHandlerExecutionRequest,\n"
            "    pre_state: MetaGraphPreState,\n"
            "    target: ORMModel | type[ORMModel],\n"
            "    positional: JsonArray,\n"
            "    keyword: JsonObject,\n"
            ") -> object:\n",
        )
        with _IndentWriter(writer, indent_size=self.indent) as iw:
            iw.write("_ = request, pre_state\n")
            iw.write(
                f"bound_input = _bind_{self._function_token(owner=owner, fn=fn)}"
                "(positional=positional, keyword=keyword)\n"
            )
            if link.is_constructor:
                iw.write("if not isinstance(target, type) or not issubclass(target, ORMModel):\n")
                with iw:
                    iw.write(
                        "raise MetaGraphLanguageHandlerExecutionError(\n"
                        '    "Generated Meta constructor invocation requires ORMModel class target."\n'
                        ")\n"
                    )
                iw.write(f"return await _call_{self._function_token(owner=owner, fn=fn)}" "(bound_input=bound_input)\n")
                return
            iw.write("if not isinstance(target, ORMModel):\n")
            with iw:
                iw.write(
                    "raise MetaGraphLanguageHandlerExecutionError(\n"
                    '    "Generated Meta instance invocation requires ORMModel target."\n'
                    ")\n"
                )
            iw.write(
                f"return await _call_{self._function_token(owner=owner, fn=fn)}"
                "(bound_input=bound_input, target=target)\n"
            )

    def _emit_bootstrap(
        self,
        *,
        writer: CodeSectionWriter,
        owner: ClassConfig,
        fn: FunctionConfig,
    ) -> None:
        bootstrap_name = self._callable_name(
            owner=owner,
            fn=fn,
            suffix="empty_lane_bootstrap",
        )
        _emit_token(
            writer,
            f"def {bootstrap_name}(\n"
            "    request: MetaGraphHandlerExecutionRequest,\n"
            ") -> MetaGraphEmptyLaneBootstrap:\n",
        )
        with _IndentWriter(writer, indent_size=self.indent) as iw:
            iw.write(f"bound_input = _bind_{self._function_token(owner=owner, fn=fn)}" "(\n")
            with iw:
                iw.write("positional=JsonArray(list(request.request.args)),\n")
                iw.write("keyword=JsonObject(dict(request.request.kwargs)),\n")
            iw.write(")\n")
            iw.write(
                f"root_object_id = _root_id_{self._function_token(owner=owner, fn=fn)}"
                "(request=request, bound_input=bound_input)\n"
            )
            description = f"Meta constructor bootstrap for {owner.name}."
            iw.write(
                "return MetaGraphEmptyLaneBootstrap(\n"
                "    root_object_id=root_object_id,\n"
                f"    name={owner.name!r},\n"
                f"    description={description!r},\n"
                ")\n"
            )

    def _emit_registry(
        self,
        *,
        writer: CodeSectionWriter,
        entries: list[tuple[ClassConfig, ClassConfigFunctionConfig, FunctionConfig]],
        registry_name: str,
        callable_suffix: str,
        value_type: str,
    ) -> None:
        _emit_token(
            writer,
            f"{registry_name}: dict[MetaGraphGeneratedLanguageHandlerKey, " f"{value_type}] = {{\n",
        )
        for owner, link, fn in entries:
            _ = link
            _emit_token(writer, "    MetaGraphGeneratedLanguageHandlerKey(\n")
            _emit_token(writer, f"        owner_key={fn.owner_key!r},\n")
            _emit_token(writer, f"        function_name={fn.name!r},\n")
            _emit_token(writer, f"        is_constructor={bool(link.is_constructor)!r},\n")
            _emit_token(writer, f"        owner_class_fqn={self._class_fqn(owner)!r},\n")
            _emit_token(writer, f"        owner_class_name={owner.name!r},\n")
            _emit_token(writer, "    ): ")
            _emit_token(
                writer,
                self._callable_name(owner=owner, fn=fn, suffix=callable_suffix),
            )
            _emit_token(writer, ",\n")
        _emit_token(writer, "}\n")

    def _emit_bind_helpers(self, *, writer: CodeSectionWriter) -> None:
        _ = writer

    def _function_token(self, *, owner: ClassConfig, fn: FunctionConfig) -> str:
        cache_key = (str(owner.id), owner.name, str(fn.id), fn.name)
        cached = self._function_token_cache.get(cache_key)
        if cached is not None:
            return cached
        token = _safe_identifier(f"{self._owner_snake_name(owner)}__{fn.name}")
        self._function_token_cache[cache_key] = token
        return token

    def _callable_name(
        self,
        *,
        owner: ClassConfig,
        fn: FunctionConfig,
        suffix: str,
    ) -> str:
        cache_key = (str(owner.id), owner.name, str(fn.id), fn.name, suffix)
        cached = self._callable_name_cache.get(cache_key)
        if cached is not None:
            return cached
        name = _safe_identifier(f"{self._function_token(owner=owner, fn=fn)}__{suffix}")
        self._callable_name_cache[cache_key] = name
        return name

    def _bind_helper_source(
        self,
        *,
        owner: ClassConfig,
        fn: FunctionConfig,
    ) -> str:
        _ = owner
        input_edges = self._input_edges(fn)
        field_names = tuple(edge.attribute_config.name for edge in input_edges)
        lines: list[str] = [
            f"def _bind_{self._function_token(owner=owner, fn=fn)}("
            "*, positional: JsonArray, keyword: JsonObject) -> JsonObject:",
            "    return _bind_keyword_payload(",
            "        positional=positional,",
            "        keyword=keyword,",
            f"        field_names={field_names!r},",
            f"        function_name={fn.name!r},",
            "    )",
            "",
        ]
        return "\n".join(lines)

    def _call_helper_source(
        self,
        *,
        owner: ClassConfig,
        fn: FunctionConfig,
    ) -> str:
        link = self._class_function_edge(owner=owner, fn=fn)
        if self._function_impl_ownership == "compiler":
            if link is None:
                raise ValueError(
                    "Generated Meta compiler-owned handler missing class/function edge: " + f"{owner.name}.{fn.name}"
                )
            authored_impl_name = self._authored_impl_function_name(owner=owner, fn=fn)
            if authored_impl_name is not None:
                return self._authored_impl_call_helper_source(
                    owner=owner,
                    link=link,
                    fn=fn,
                    impl_function=authored_impl_name,
                )
            return self._compiler_call_helper_source(owner=owner, link=link, fn=fn)

        return self._authored_impl_call_helper_source(
            owner=owner,
            link=link,
            fn=fn,
            impl_function=(self._authored_impl_function_name(owner=owner, fn=fn) or _safe_identifier(fn.name)),
        )

    def _authored_impl_call_helper_source(
        self,
        *,
        owner: ClassConfig,
        link: ClassConfigFunctionConfig | None,
        fn: FunctionConfig,
        impl_function: str,
    ) -> str:
        impl_module = runtime_handler_impl_module_import(
            layout_strategy=self.layout_strategy,
            class_config=owner,
            import_root=self._runtime_handlers_import_root(),
        )
        return_type = "ORMModel" if link is not None and link.is_constructor else "object"
        lines = [
            f"async def _call_{self._function_token(owner=owner, fn=fn)}("
            f"*, bound_input: JsonObject, target: ORMModel | None = None) -> {return_type}:",
            f"    from {impl_module} import {impl_function} as _impl",
            "    call_kwargs = coerce_meta_handler_call_kwargs(_impl, dict(bound_input))",
        ]
        if link is not None and link.is_constructor:
            lines.append("    result = await _impl(**call_kwargs)")
            lines.append("    return cast(ORMModel, result)")
        else:
            owner_arg_name = self._owner_arg_name(owner)
            lines.extend(
                [
                    "    if target is None:",
                    "        raise MetaGraphLanguageHandlerExecutionError(",
                    f"            {'Generated Meta instance invocation requires target: ' + owner.name + '.' + fn.name!r}",
                    "        )",
                    f"    result = await _impl({owner_arg_name}=target, **call_kwargs)",
                    "    return result",
                ]
            )
        lines.extend(
            [
                "",
            ]
        )
        return "\n".join(lines)

    def _authored_impl_function_name(
        self,
        *,
        owner: ClassConfig,
        fn: FunctionConfig,
    ) -> str | None:
        base_dir = getattr(self.layout_strategy, "base_dir", None)
        if base_dir is None:
            return None
        path = Path(base_dir) / runtime_handler_impl_relative_path(
            layout_strategy=self.layout_strategy,
            class_config=owner,
        )
        if not path.is_file():
            return None
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            return None
        source_fn = self._source_function_for_runtime_function(fn)
        candidate = _safe_identifier((source_fn or fn).name)
        function_name = re.escape(candidate)
        if re.search(rf"^async\s+def\s+{function_name}\s*\(", source, re.M):
            return candidate
        return None

    def _source_function_for_runtime_function(
        self,
        fn: FunctionConfig,
    ) -> FunctionConfig | None:
        code_section_id = fn.code_section_function_id
        if code_section_id is not None:
            source_fn = self._function_impl_source_by_code_section_id.get(code_section_id)
            if source_fn is not None:
                return source_fn
        return self._function_impl_source_by_id.get(fn.id)

    def _compiler_call_helper_source(
        self,
        *,
        owner: ClassConfig,
        link: ClassConfigFunctionConfig,
        fn: FunctionConfig,
    ) -> str:
        sig, generated = self._compiler_render_artifacts(owner=owner, link=link, fn=fn)
        return_type = "ORMModel" if link.is_constructor else "object"
        impl_signature = self._compiler_nested_impl_signature(
            owner=owner,
            link=link,
            fn=fn,
            sig=sig,
        )
        impl_body = (
            generated.body
            if generated is not None
            else (
                "raise MetaGraphLanguageHandlerExecutionError("
                + repr("Compiler-owned FunctionImpl lowering unavailable for " f"{owner.name}.{fn.name}")
                + ")"
            )
        )
        lines = [
            f"async def _call_{self._function_token(owner=owner, fn=fn)}("
            f"*, bound_input: JsonObject, target: ORMModel | None = None) -> {return_type}:",
            f"    {impl_signature}",
        ]
        for body_line in impl_body.splitlines() or ["pass"]:
            lines.append(f"        {body_line}" if body_line.strip() else "")
        lines.append("    call_kwargs = coerce_meta_handler_call_kwargs(_impl, dict(bound_input))")
        if link.is_constructor:
            lines.append("    result = await _impl(**call_kwargs)")
            lines.append("    return cast(ORMModel, result)")
        else:
            owner_arg_name = self._owner_arg_name(owner)
            lines.extend(
                [
                    "    if target is None:",
                    "        raise MetaGraphLanguageHandlerExecutionError(",
                    f"            {'Generated Meta instance invocation requires target: ' + owner.name + '.' + fn.name!r}",
                    "        )",
                    f"    result = await _impl({owner_arg_name}=target, **call_kwargs)",
                    "    return result",
                ]
            )
        lines.append("")
        return "\n".join(lines)

    def _compiler_nested_impl_signature(
        self,
        *,
        owner: ClassConfig,
        link: ClassConfigFunctionConfig,
        fn: FunctionConfig,
        sig: _RenderedSignature,
    ) -> str:
        params: list[str] = []
        if not link.is_constructor:
            owner_arg_name = self._owner_arg_name(owner)
            params.append(f"{owner_arg_name}: {owner.name}")
        for param in sig.params:
            rendered = f"{param.name}: {param.type_annotation}"
            if param.default_expr is not None:
                rendered += f" = {param.default_expr}"
            params.append(rendered)
        return "async def _impl(" + ", ".join(params) + f") -> {sig.return_type}:"

    def _compiler_renderer_delegate(self) -> PythonRendererRuntimeHandlersAware:
        if self._compiler_delegate is not None:
            return self._compiler_delegate
        if self._bound_graph is None:
            raise ValueError("PythonMetaRuntimeHandlersRenderer requires a bound ObjectConfigGraph.")
        delegate = PythonRendererRuntimeHandlersAware(self.layout_strategy)
        delegate.set_policy(
            {
                "function_impl_ownership": self._function_impl_ownership,
                "function_impl_parity_policy": self._function_impl_parity_policy,
            }
        )
        delegate.bind_profile_inputs(dict(self.profile_inputs))
        delegate.set_external_graphs(list(self.external_graphs))
        delegate.set_external_class_lookup(dict(self.external_class_lookup))
        delegate.import_overrides = dict(self.import_overrides or {})
        delegate.bind_object_config_graph(self._bound_graph)
        self._compiler_delegate = delegate
        return delegate

    def _compiler_render_artifacts(
        self,
        *,
        owner: ClassConfig,
        link: ClassConfigFunctionConfig,
        fn: FunctionConfig,
    ) -> tuple[_RenderedSignature, _GeneratedImplLogic | None]:
        cache_key = (str(owner.id), str(link.function_config_id), str(fn.id))
        cached = self._compiler_render_cache.get(cache_key)
        if cached is not None:
            return cached
        delegate = self._compiler_renderer_delegate()
        sig = delegate._render_signature(fn=fn)  # noqa: SLF001
        generated = delegate._build_generated_impl_logic(  # noqa: SLF001
            class_config=owner,
            fn_link=link,
            fn=fn,
        )
        cached = (sig, generated)
        self._compiler_render_cache[cache_key] = cached
        return cached

    def _compiler_generated_imports(
        self,
        *,
        entries: list[tuple[ClassConfig, ClassConfigFunctionConfig, FunctionConfig]],
    ) -> dict[str, set[str]]:
        if self._function_impl_ownership != "compiler":
            return {}
        delegate = self._compiler_renderer_delegate()
        imports: dict[str, set[str]] = {}
        for owner, link, fn in entries:
            sig, generated = self._compiler_render_artifacts(
                owner=owner,
                link=link,
                fn=fn,
            )
            if generated is not None:
                imports = self._merge_imports(imports, generated.runtime_imports)
            for param in sig.params:
                delegate._collect_type_imports(  # noqa: SLF001
                    imports,
                    type_annotation=param.type_annotation,
                )
                delegate._collect_type_imports_by_id(  # noqa: SLF001
                    imports,
                    type_id=param.type_id,
                    type_name=param.type_name,
                )
                if (
                    param.default_expr is not None
                    and param.type_id is not None
                    and param.type_name is not None
                    and param.default_expr.startswith(f"{param.type_name}.")
                ):
                    module = delegate._resolve_type_module_by_id(param.type_id)  # noqa: SLF001
                    if module:
                        imports.setdefault(module, set()).add(param.type_name)
            delegate._collect_type_imports(  # noqa: SLF001
                imports,
                type_annotation=sig.return_type,
            )
            delegate._collect_type_imports_by_id(  # noqa: SLF001
                imports,
                type_id=sig.return_type_id,
                type_name=sig.return_type_name,
            )
        return imports

    def _root_id_helper_source(
        self,
        *,
        owner: ClassConfig,
        fn: FunctionConfig,
    ) -> str:
        identity_edges = self._identity_edges(fn)
        lines = [
            f"def _root_id_{self._function_token(owner=owner, fn=fn)}"
            "(*, request: MetaGraphHandlerExecutionRequest, bound_input: JsonObject):",
        ]
        if not identity_edges:
            lines.extend(
                [
                    "    _ = bound_input",
                    "    return request.execution_plan.staged_call.lane_scope.domain_branch_id",
                    "",
                ]
            )
            return "\n".join(lines)
        stable_ids_module = self._stable_ids_module(owner=owner)
        lines.append("    from importlib import import_module")
        lines.append(f"    from {stable_ids_module} import CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID")
        input_edges = self._input_edges(fn)
        for edge in input_edges:
            attr = edge.attribute_config
            name = _safe_identifier(attr.name)
            lines.append(f"    {name} = bound_input.get({attr.name!r})")
            default_expr = self._default_literal(edge)
            if default_expr is not None:
                lines.append(f"    if {name} is None:")
                lines.append(f"        {name} = {default_expr}")
        input_names = [_safe_identifier(edge.attribute_config.name) for edge in input_edges]
        values_expr = ", ".join(f"{name!r}: {name}" for name in input_names)
        lines.append(f"    _aware_self_values = {{{values_expr}}}")
        lines.append(
            "    _aware_self_binding = "
            "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID.get(" + f"{str(owner.id)!r})"
        )
        lines.append("    if _aware_self_binding is None:")
        lines.append("        raise MetaGraphLanguageHandlerExecutionError(")
        lines.append(
            f"            {('Generated Meta constructor bootstrap cannot resolve stable-id binding: ' + owner.name + '.' + fn.name)!r}"
        )
        lines.append("        )")
        lines.append("    _aware_self_fn, _aware_self_key_names = _aware_self_binding")
        lines.append(
            "    _aware_missing_self_keys = ["
            "key for key in _aware_self_key_names "
            "if key not in _aware_self_values or _aware_self_values[key] is None"
            "]"
        )
        lines.append("    if _aware_missing_self_keys:")
        lines.append("        raise MetaGraphLanguageHandlerExecutionError(")
        lines.append(
            f"            {('Missing stable-id input for generated Meta constructor bootstrap: ' + owner.name + '.' + fn.name)!r}"
            " + f': {_aware_missing_self_keys}'"
        )
        lines.append("        )")
        lines.append(
            "    _aware_self_stable_values = {"
            "key: getattr(_aware_self_values[key], 'value', _aware_self_values[key]) "
            "for key in _aware_self_key_names"
            "}"
        )
        lines.append(
            f"    return getattr(import_module({stable_ids_module!r}), _aware_self_fn)" "(**_aware_self_stable_values)"
        )
        lines.append("")
        return "\n".join(lines)

    def _emit_generated_helpers(
        self,
        *,
        writer: CodeSectionWriter,
        entries: list[tuple[ClassConfig, ClassConfigFunctionConfig, FunctionConfig]],
    ) -> None:
        _emit_token(
            writer,
            "def _bind_keyword_payload(\n"
            "    *,\n"
            "    positional: JsonArray,\n"
            "    keyword: JsonObject,\n"
            "    field_names: tuple[str, ...],\n"
            "    function_name: str,\n"
            ") -> JsonObject:\n"
            "    if len(positional) > len(field_names):\n"
            "        raise MetaGraphLanguageHandlerExecutionError(\n"
            '            "Too many positional arguments for generated Meta language handler: "\n'
            '            f"function_name={function_name} have={len(positional)} max={len(field_names)}"\n'
            "        )\n"
            "    payload = JsonObject(dict(keyword))\n"
            "    unknown_names = sorted(set(payload) - set(field_names))\n"
            "    if unknown_names:\n"
            "        raise MetaGraphLanguageHandlerExecutionError(\n"
            '            "Unknown generated Meta language-handler argument(s): "\n'
            '            f"function_name={function_name} names={unknown_names}"\n'
            "        )\n"
            "    for position, value in enumerate(positional):\n"
            "        field_name = field_names[position]\n"
            "        if field_name in payload:\n"
            "            raise MetaGraphLanguageHandlerExecutionError(\n"
            '                "Generated Meta language-handler argument provided twice: "\n'
            '                f"function_name={function_name} name={field_name}"\n'
            "            )\n"
            "        payload[field_name] = value\n"
            "    return payload\n\n",
        )
        _emit_token(
            writer,
            "def _assert_constructor_owner_class(\n"
            "    *, request: MetaGraphHandlerExecutionRequest, expected_class_name: str\n"
            ") -> None:\n"
            "    owner_class_config = request.execution_plan.implementation.owner_class_config\n"
            "    if not isinstance(owner_class_config, ClassConfig):\n"
            "        raise MetaGraphLanguageHandlerExecutionError(\n"
            '            "Generated Meta constructor requires a resolved owner ClassConfig."\n'
            "        )\n"
            "    if owner_class_config.name != expected_class_name:\n"
            "        raise MetaGraphLanguageHandlerExecutionError(\n"
            '            "Generated Meta constructor owner mismatch: "\n'
            '            f"expected={expected_class_name} got={owner_class_config.name}"\n'
            "        )\n\n",
        )
        _emit_token(
            writer,
            "def _post_oig_with_root_model(\n"
            "    *,\n"
            "    request: MetaGraphHandlerExecutionRequest,\n"
            "    pre_state: MetaGraphPreState,\n"
            "    root_model: ORMModel,\n"
            ") -> ObjectInstanceGraph:\n"
            "    before_oig = pre_state.before_oig\n"
            "    return build_object_instance_graph(\n"
            "        root_instance=root_model,\n"
            "        object_config_graph=request.execution_plan.index.ocg,\n"
            "        object_projection_graph=request.execution_plan.object_projection_graph,\n"
            "        key=before_oig.key or str(before_oig.id),\n"
            "        name=before_oig.name or request.execution_plan.object_projection_graph.name,\n"
            '        description=before_oig.description or "",\n'
            "        oig_id=before_oig.id,\n"
            "        enum_option_resolver=default_meta_enum_option_resolver,\n"
            "    )\n"
            "\n",
        )
        _emit_token(
            writer,
            "def _changes_from_current_collector(\n"
            "    *,\n"
            "    request: MetaGraphHandlerExecutionRequest,\n"
            "    pre_state: MetaGraphPreState,\n"
            "):\n"
            "    collector = current_change_collector()\n"
            "    if collector is None:\n"
            "        raise MetaGraphLanguageHandlerExecutionError(\n"
            '            "Generated Meta instance handler requires an active ORM change collector."\n'
            "        )\n"
            "    change_set = collector.snapshot()\n"
            "    changes = tuple(\n"
            "        build_object_instance_graph_changes_from_orm_change_set(\n"
            "            before_oig=pre_state.before_oig,\n"
            "            object_instance_graph_identity_id=(\n"
            "                request.staged_call.lane_scope.object_instance_graph_identity_id\n"
            "            ),\n"
            "            ocg=request.execution_plan.index.ocg,\n"
            "            opg=request.execution_plan.object_projection_graph,\n"
            "            change_set=change_set,\n"
            "            class_configs_by_id=dict(request.execution_plan.index.class_configs_by_id),\n"
            "            relationships_by_id=dict(request.execution_plan.index.relationships_by_id),\n"
            "            enum_option_resolver=default_meta_enum_option_resolver,\n"
            "        )\n"
            "    )\n"
            "    constructed_class_instance_ids = tuple(\n"
            "        class_change.class_instance_id\n"
            "        for root_change in changes\n"
            "        for class_change in root_change.class_instance_changes\n"
            '        if class_change.change.type.value == "create"\n'
            "    )\n"
            "    return changes, constructed_class_instance_ids\n"
            "\n",
        )
        _emit_token(
            writer,
            "def _root_and_target_models_from_pre_state(\n"
            "    *,\n"
            "    request: MetaGraphHandlerExecutionRequest,\n"
            "    pre_state: MetaGraphPreState,\n"
            "    expected_class_name: str,\n"
            ") -> tuple[ORMModel, ORMModel]:\n"
            "    owner_class_config = request.execution_plan.implementation.owner_class_config\n"
            "    if not isinstance(owner_class_config, ClassConfig):\n"
            "        raise MetaGraphLanguageHandlerExecutionError(\n"
            '            "Generated Meta instance handler requires a resolved owner ClassConfig."\n'
            "        )\n"
            "    if owner_class_config.name != expected_class_name:\n"
            "        raise MetaGraphLanguageHandlerExecutionError(\n"
            '            "Generated Meta instance handler owner mismatch: "\n'
            '            f"expected={expected_class_name} got={owner_class_config.name}"\n'
            "        )\n"
            "    target_object_id = (\n"
            "        pre_state.target_object_id\n"
            "        or request.execution_plan.target_object_id\n"
            "        or request.request.target_object_id\n"
            "        or pre_state.root_object_id\n"
            "    )\n"
            "    if target_object_id is None:\n"
            "        raise MetaGraphLanguageHandlerExecutionError(\n"
            '            "Generated Meta instance handler requires a target object id."\n'
            "        )\n"
            "    root_model = _root_model_from_pre_state(request=request, pre_state=pre_state)\n"
            "    target_source_object_id = _target_source_object_id_from_pre_state(\n"
            "        pre_state=pre_state,\n"
            "        target_class_instance_id=target_object_id,\n"
            "    )\n"
            "    target = _find_orm_model_by_id(root_model, target_source_object_id)\n"
            "    target_orm_class = ORMModelRegistry.get_class_by_class_config_id(owner_class_config.id)\n"
            "    if target_orm_class is None:\n"
            "        raise MetaGraphLanguageHandlerExecutionError(\n"
            '            "Generated Meta instance handler cannot resolve ORM class: "\n'
            '            f"class_config_id={owner_class_config.id} class_name={owner_class_config.name}"\n'
            "        )\n"
            "    if not isinstance(target, target_orm_class):\n"
            "        raise MetaGraphLanguageHandlerExecutionError(\n"
            '            "Generated Meta instance handler cannot resolve target model in "\n'
            '            "the rooted projection model: "\n'
            '            f"class_name={owner_class_config.name} target_object_id={target_object_id}"\n'
            "        )\n"
            "    return root_model, target\n\n",
        )
        _emit_token(
            writer,
            "def _root_model_from_pre_state(\n"
            "    *,\n"
            "    request: MetaGraphHandlerExecutionRequest,\n"
            "    pre_state: MetaGraphPreState,\n"
            ") -> ORMModel:\n"
            "    root_orm_class = _root_orm_class_from_projection(request)\n"
            "    root_object_id = _root_source_object_id_from_pre_state(pre_state)\n"
            "    root = reify_oig_root_model(\n"
            "        index=request.execution_plan.index,\n"
            "        opg=request.execution_plan.object_projection_graph,\n"
            "        oig=pre_state.before_oig,\n"
            "        model_type=root_orm_class,\n"
            "        root_id=root_object_id,\n"
            "        branch_id=request.execution_plan.staged_call.lane_scope.domain_branch_id,\n"
            "    )\n"
            "    if root is None:\n"
            "        raise MetaGraphLanguageHandlerExecutionError(\n"
            '            "Generated Meta instance handler cannot reify rooted projection model: "\n'
            '            f"root_object_id={root_object_id}"\n'
            "        )\n"
            "    return root\n\n",
        )
        _emit_token(
            writer,
            "def _root_orm_class_from_projection(\n"
            "    request: MetaGraphHandlerExecutionRequest,\n"
            ") -> type[ORMModel]:\n"
            "    root_nodes = [\n"
            "        node\n"
            "        for node in request.execution_plan.object_projection_graph.object_projection_graph_nodes\n"
            "        if node.is_root\n"
            "    ]\n"
            "    if len(root_nodes) != 1:\n"
            "        raise MetaGraphLanguageHandlerExecutionError(\n"
            '            "Generated Meta handler requires exactly one OPG root node: "\n'
            '            f"have={len(root_nodes)} "\n'
            '            f"object_projection_graph_id={request.execution_plan.object_projection_graph.id}"\n'
            "        )\n"
            "    orm_class = ORMModelRegistry.get_class_by_class_config_id(root_nodes[0].class_config_id)\n"
            "    if orm_class is None:\n"
            "        raise MetaGraphLanguageHandlerExecutionError(\n"
            '            "Generated Meta handler cannot resolve root ORM class: "\n'
            '            f"class_config_id={root_nodes[0].class_config_id}"\n'
            "        )\n"
            "    return cast(type[ORMModel], orm_class)\n\n",
        )
        _emit_token(
            writer,
            "def _root_source_object_id_from_pre_state(pre_state: MetaGraphPreState):\n"
            "    if pre_state.root_object_id is not None:\n"
            "        return pre_state.root_object_id\n"
            "    root_class_instance = pre_state.before_oig.root_class_instance\n"
            "    if root_class_instance is None and pre_state.before_oig.root_class_instance_id is not None:\n"
            "        root_class_instance = next(\n"
            "            (\n"
            "                instance\n"
            "                for instance in pre_state.before_oig.class_instances\n"
            "                if instance.id == pre_state.before_oig.root_class_instance_id\n"
            "            ),\n"
            "            None,\n"
            "        )\n"
            "    if root_class_instance is None:\n"
            "        raise MetaGraphLanguageHandlerExecutionError(\n"
            '            "Generated Meta handler cannot resolve root source object id."\n'
            "        )\n"
            "    return root_class_instance.source_object_id\n\n",
        )
        _emit_token(
            writer,
            "def _target_source_object_id_from_pre_state(\n"
            "    *,\n"
            "    pre_state: MetaGraphPreState,\n"
            "    target_class_instance_id,\n"
            "):\n"
            "    if pre_state.oig_index is None:\n"
            "        raise MetaGraphLanguageHandlerExecutionError(\n"
            '            "Generated Meta handler requires pre-state OIG index."\n'
            "        )\n"
            "    target_class_instance = pre_state.oig_index.class_instances_by_id.get(\n"
            "        target_class_instance_id\n"
            "    )\n"
            "    if target_class_instance is None:\n"
            "        raise MetaGraphLanguageHandlerExecutionError(\n"
            '            "Generated Meta handler cannot resolve target class instance: "\n'
            '            f"target_class_instance_id={target_class_instance_id}"\n'
            "        )\n"
            "    return target_class_instance.source_object_id\n\n",
        )
        _emit_token(
            writer,
            "def _find_orm_model_by_id(root_model: ORMModel, object_id) -> ORMModel | None:\n"
            "    stack: list[object] = [root_model]\n"
            "    seen: set[int] = set()\n"
            "    while stack:\n"
            "        current = stack.pop()\n"
            "        identity = id(current)\n"
            "        if identity in seen:\n"
            "            continue\n"
            "        seen.add(identity)\n"
            "        if isinstance(current, ORMModel):\n"
            "            if current.id == object_id:\n"
            "                return current\n"
            "            stack.extend(current.__dict__.values())\n"
            "            continue\n"
            "        if isinstance(current, (list, tuple, set)):\n"
            "            stack.extend(current)\n"
            "            continue\n"
            "        if isinstance(current, dict):\n"
            "            stack.extend(current.values())\n"
            "    return None\n\n",
        )
        _emit_token(
            writer,
            "def _constructed_class_instance_ids_from_post_oig(\n"
            "    *,\n"
            "    pre_state: MetaGraphPreState,\n"
            "    post_oig: ObjectInstanceGraph,\n"
            ") -> tuple:\n"
            "    before_ids = {instance.id for instance in pre_state.before_oig.class_instances}\n"
            "    return tuple(\n"
            "        instance.id\n"
            "        for instance in post_oig.class_instances\n"
            "        if instance.id not in before_ids\n"
            "    )\n\n",
        )
        _emit_token(
            writer,
            "def _json_payload_value(value: object) -> object:\n"
            "    if isinstance(value, BaseModel):\n"
            '        return value.model_dump(mode="json")\n'
            "    if isinstance(value, tuple):\n"
            "        return [_json_payload_value(item) for item in value]\n"
            "    if isinstance(value, list):\n"
            "        return [_json_payload_value(item) for item in value]\n"
            "    if isinstance(value, dict):\n"
            "        return {str(key): _json_payload_value(item) for key, item in value.items()}\n"
            "    return value\n\n",
        )
        for owner, _link, fn in entries:
            _emit_token(
                writer,
                self._bind_helper_source(owner=owner, fn=fn),
            )
            _emit_token(writer, "\n")
            _emit_token(
                writer,
                self._call_helper_source(owner=owner, fn=fn),
            )
            _emit_token(writer, "\n")
            link = self._class_function_edge(owner=owner, fn=fn)
            if link is not None and link.is_constructor:
                _emit_token(
                    writer,
                    self._root_id_helper_source(owner=owner, fn=fn),
                )
                _emit_token(writer, "\n")

    def _class_function_edge(
        self,
        *,
        owner: ClassConfig,
        fn: FunctionConfig,
    ) -> ClassConfigFunctionConfig | None:
        cache_key = (str(owner.id), str(fn.id))
        if cache_key in self._class_function_edge_cache:
            return self._class_function_edge_cache[cache_key]
        for edge in owner.class_config_function_configs:
            if edge.function_config_id == fn.id:
                self._class_function_edge_cache[cache_key] = edge
                return edge
            if edge.function_config is fn:
                self._class_function_edge_cache[cache_key] = edge
                return edge
        self._class_function_edge_cache[cache_key] = None
        return None

    def _input_edges(
        self,
        fn: FunctionConfig,
    ) -> tuple[FunctionConfigAttributeConfig, ...]:
        cache_key = str(fn.id)
        cached = self._input_edges_cache.get(cache_key)
        if cached is not None:
            return cached
        edges = [edge for edge in fn.function_config_attribute_configs if edge.type == FunctionAttributeType.input]
        edges.sort(key=lambda edge: int(edge.position))
        cached = tuple(edges)
        self._input_edges_cache[cache_key] = cached
        return cached

    def _identity_edges(
        self,
        fn: FunctionConfig,
    ) -> tuple[FunctionConfigAttributeConfig, ...]:
        cache_key = str(fn.id)
        cached = self._identity_edges_cache.get(cache_key)
        if cached is not None:
            return cached
        cached = tuple(edge for edge in self._input_edges(fn) if bool(edge.is_identity_key))
        self._identity_edges_cache[cache_key] = cached
        return cached

    def _owner_snake_name(self, owner: ClassConfig) -> str:
        cache_key = (str(owner.id), owner.name)
        cached = self._owner_snake_name_cache.get(cache_key)
        if cached is not None:
            return cached
        name = to_snake_case(owner.name)
        self._owner_snake_name_cache[cache_key] = name
        return name

    def _owner_arg_name(self, owner: ClassConfig) -> str:
        return _safe_identifier(self._owner_snake_name(owner))

    def _default_literal(
        self,
        edge: FunctionConfigAttributeConfig,
    ) -> str | None:
        default_value = edge.attribute_config.default_value
        if default_value is None:
            return None
        try:
            return repr(json.loads(default_value))
        except Exception:
            return repr(default_value)

    def _runtime_handlers_import_root(self) -> str:
        return self.layout_strategy.import_root or ""

    def _stable_ids_module(self, *, owner: ClassConfig) -> str:
        return resolve_python_stable_ids_module_import(
            graph=self._stable_ids_source_graph or self._bound_graph,
            owner=owner,
            import_overrides=self.import_overrides,
            explicit_import_root=self._stable_ids_import_root,
        )

    def _schema_for_class(self, cc: ClassConfig) -> str:
        rel = runtime_handler_impl_relative_path(
            layout_strategy=self.layout_strategy,
            class_config=cc,
        )
        parts = rel.parts
        try:
            idx = parts.index("impl")
            return _safe_identifier(parts[idx + 1])
        except Exception:
            return "default"

    def _class_fqn(self, cc: ClassConfig) -> str:
        return cc.class_fqn or cc.name

    def _emit_grouped_imports(
        self,
        *,
        writer: CodeSectionWriter,
        imports: dict[str, set[str]],
    ) -> None:
        package_groups = group_python_imports(
            imports,
            policy=PythonImportGroupingPolicy(
                semantic_import_roots=semantic_import_roots_from_renderer_inputs(
                    import_root=self.layout_strategy.import_root,
                    import_overrides=self.import_overrides,
                    external_graph_fqn_prefixes=(graph.fqn_prefix for graph in self.external_graphs),
                ),
                support_import_roots=DEFAULT_ORM_SUPPORT_IMPORT_ROOTS,
            ),
        )
        for package_name, package_imports in package_groups.items():
            if package_name:
                _emit_token(writer, f"# {package_name.replace('_', ' ')}\n")
            for module in sorted(package_imports.keys()):
                items = sorted(package_imports[module])
                joined = ", ".join(items)
                _emit_token(writer, f"from {module} import {joined}\n")
            _emit_token(writer, "\n")

    def _merge_imports(
        self,
        left: dict[str, set[str]],
        right: dict[str, set[str]],
    ) -> dict[str, set[str]]:
        merged = {module: set(symbols) for module, symbols in left.items()}
        for module, symbols in right.items():
            merged.setdefault(module, set()).update(symbols)
        return merged


__all__ = ["PythonMetaRuntimeHandlersRenderer"]
