from __future__ import annotations

from pathlib import Path
from typing import cast
from uuid import UUID
from typing_extensions import override

from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code.section.writer import CodeSectionWriter

from aware_meta.graph.config.render.renderer_language import (
    ObjectConfigGraphRendererLanguage,
    ObjectConfigGraphRendererPolicy,
    build_renderer_empty_code,
)
from aware_meta.graph.config.render.layout_strategy import ObjectConfigGraphRenderLayoutStrategy
from aware_meta.graph.config.stable_ids_resolution import load_stable_ids_spec_for_graph
from aware_meta.graph.config.stable_ids_spec.spec import (
    ParamSpec,
    StableIdsSpec,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph


def _snake_to_lower_camel(name: str) -> str:
    parts = [p for p in (name or "").strip().split("_") if p]
    if not parts:
        return ""
    head = parts[0].lower()
    tail = "".join(p[:1].upper() + p[1:] for p in parts[1:])
    return head + tail


def _dart_type(p: ParamSpec) -> str:
    base = {
        "uuid": "UuidValue",
        "str": "String",
        "bytes": "Uint8List",
        "bool": "bool",
        "int": "int",
        "float": "double",
        "str_list": "List<String>",
    }[p.type]
    if p.optional:
        return f"{base}?"
    return base


def _dart_normalize_expr(var: str, ops: tuple[str, ...], *, nullable: bool = False) -> str:
    expr = f"({var} ?? '')" if nullable else var
    for op in ops:
        if op == "strip":
            expr = f"{expr}.trim()"
        elif op in {"lower", "casefold"}:
            expr = f"{expr}.toLowerCase()"
        elif op == "upper":
            expr = f"{expr}.toUpperCase()"
        else:
            raise ValueError(f"Unsupported normalize op for dart: {op!r}")
    return expr


def render_dart_stable_ids_module(*, spec: StableIdsSpec) -> str:
    """
    Emit a compiler-owned `stable_ids.dart` module.

    NOTE: This function must live in the Dart language package (not Meta) so the
    grammar-level output rules are owned by the language plugin.
    """

    import re

    ns_by_name = spec.namespaces_by_name

    used_ns: set[str] = set()
    needs_bytes = False
    for fn in spec.functions:
        if fn.namespace != "NAMESPACE_URL":
            used_ns.add(fn.namespace)
        for p in fn.params:
            if p.type == "bytes":
                needs_bytes = True

    lines: list[str] = []
    lines.append("// GENERATED CODE - DO NOT MODIFY BY HAND")
    lines.append("// Canonical stable-id derivations (UUIDv5).")
    lines.append("")
    if needs_bytes:
        lines.append("import 'dart:typed_data';")
    lines.append("import 'package:uuid/uuid.dart';")
    lines.append("")
    lines.append("final Uuid _uuid = Uuid();")
    lines.append("")

    for ns_name in sorted(used_ns):
        ns = ns_by_name.get(ns_name)
        if ns is None:
            raise ValueError(f"Unknown namespace {ns_name!r} in spec")
        dart_const = _snake_to_lower_camel(ns.name)
        if not dart_const:
            raise ValueError(f"Unable to derive dart namespace var for {ns.name!r}")
        if ns.kind == "ns_url":
            lines.append(
                f"final String {dart_const} = _uuid.v5(Namespace.url.value, {ns.value!r});"
            )
        elif ns.kind == "uuid":
            lines.append(f"const String {dart_const} = {ns.value!r};")
        else:
            raise ValueError(f"Unsupported namespace kind: {ns.kind}")
    if used_ns:
        lines.append("")

    if needs_bytes:
        lines.append("String _bytesToHex(List<int> bytes) {")
        lines.append("  final buffer = StringBuffer();")
        lines.append("  for (final b in bytes) {")
        lines.append("    buffer.write(b.toRadixString(16).padLeft(2, '0'));")
        lines.append("  }")
        lines.append("  return buffer.toString();")
        lines.append("}")
        lines.append("")

    def _dart_ident(name: str) -> str:
        return _snake_to_lower_camel(name)

    def _dart_value_expr(*, var: str, p: ParamSpec) -> str:
        if p.type == "uuid":
            return f"${{{var}.uuid}}"
        return f"${{{var}}}"

    for fn in spec.functions:
        dart_fn_name = fn.dart_name or _snake_to_lower_camel(fn.name)
        if not dart_fn_name:
            raise ValueError(f"Unable to derive dart name for {fn.name!r}")

        params_sig: list[str] = []
        param_by_name: dict[str, ParamSpec] = {}
        dart_name_by_py: dict[str, str] = {}
        for p in fn.params:
            param_by_name[p.name] = p
            dname = _dart_ident(p.name)
            if not dname:
                raise ValueError(f"Unable to derive dart param name for {p.name!r}")
            dart_name_by_py[p.name] = dname
            dtype = _dart_type(p)
            req = "required " if not p.optional and p.default is None else ""
            default = ""
            default_value: object | None = p.default
            if default_value is not None:
                if isinstance(default_value, str):
                    default = f" = {default_value!r}"
                elif isinstance(default_value, bool):
                    default = f" = {'true' if default_value else 'false'}"
                elif isinstance(default_value, int):
                    default = f" = {default_value}"
                else:
                    raise ValueError(
                        f"Unsupported dart default for {fn.name}.{p.name}: {default_value!r}"
                    )
            params_sig.append(f"{req}{dtype} {dname}{default}")

        lines.append(f"UuidValue {dart_fn_name}({{")
        for ps in params_sig:
            lines.append(f"  {ps},")
        lines.append("}) {")

        for p in fn.params:
            if p.type != "str":
                continue
            dname = dart_name_by_py[p.name]
            if p.normalize:
                expr = _dart_normalize_expr(dname, p.normalize, nullable=p.optional)
                norm_name = f"normalized{dname[:1].upper() + dname[1:]}"
                lines.append(f"  final {norm_name} = {expr};")
                dart_name_by_py[p.name] = norm_name
            if p.non_empty:
                var = dart_name_by_py[p.name]
                lines.append(f"  if ({var}.trim().isEmpty) {{")
                lines.append(
                    f"    throw ArgumentError.value({var}, {p.name!r}, 'Must not be empty');"
                )
                lines.append("  }")

        dart_let_name_by_py: dict[str, str] = {}
        for let_cfg in fn.lets:
            if let_cfg.op == "hex":
                if not let_cfg.name or not let_cfg.param:
                    raise ValueError(f"{fn.name}: hex let requires name+param")
                dname = _dart_ident(let_cfg.name)
                src = dart_name_by_py.get(let_cfg.param) or _dart_ident(let_cfg.param)
                lines.append(f"  final {dname} = _bytesToHex({src});")
                dart_let_name_by_py[let_cfg.name] = dname
            elif let_cfg.op == "bool_int":
                if not let_cfg.name or not let_cfg.param:
                    raise ValueError(f"{fn.name}: bool_int let requires name+param")
                dname = _dart_ident(let_cfg.name)
                src = dart_name_by_py.get(let_cfg.param) or _dart_ident(let_cfg.param)
                p = param_by_name.get(let_cfg.param)
                if p is not None and p.optional:
                    lines.append(f"  final {dname} = ({src} ?? false) ? 1 : 0;")
                else:
                    lines.append(f"  final {dname} = {src} ? 1 : 0;")
                dart_let_name_by_py[let_cfg.name] = dname
            elif let_cfg.op == "normalize":
                if not let_cfg.name or not let_cfg.param:
                    raise ValueError(f"{fn.name}: normalize let requires name+param")
                dname = _dart_ident(let_cfg.name)
                src = dart_name_by_py.get(let_cfg.param) or _dart_ident(let_cfg.param)
                ops = let_cfg.normalize or ("lower", "strip")
                src_param = param_by_name.get(let_cfg.param)
                expr = _dart_normalize_expr(
                    src,
                    ops,
                    nullable=src_param is not None and src_param.type == "str" and src_param.optional,
                )
                lines.append(f"  final {dname} = {expr};")
                dart_let_name_by_py[let_cfg.name] = dname
            elif let_cfg.op == "normalize_default":
                if not let_cfg.name or not let_cfg.param or let_cfg.default is None:
                    raise ValueError(
                        f"{fn.name}: normalize_default let requires name+param+default"
                    )
                dname = _dart_ident(let_cfg.name)
                src = dart_name_by_py.get(let_cfg.param) or _dart_ident(let_cfg.param)
                ops = let_cfg.normalize or ("lower", "strip")
                src_param = param_by_name.get(let_cfg.param)
                expr = _dart_normalize_expr(
                    src,
                    ops,
                    nullable=src_param is not None and src_param.type == "str" and src_param.optional,
                )
                lines.append(f"  final {dname}Raw = {expr};")
                lines.append(
                    f"  final {dname} = {dname}Raw.isEmpty ? {let_cfg.default!r} : {dname}Raw;"
                )
                dart_let_name_by_py[let_cfg.name] = dname
            elif let_cfg.op == "prefix_if_set":
                if not let_cfg.name or not let_cfg.param or let_cfg.prefix is None:
                    raise ValueError(
                        f"{fn.name}: prefix_if_set let requires name+param+prefix"
                    )
                dname = _dart_ident(let_cfg.name)
                src = dart_name_by_py.get(let_cfg.param) or _dart_ident(let_cfg.param)
                p = param_by_name.get(let_cfg.param)
                if p is None or p.type != "str":
                    raise ValueError(f"{fn.name}: prefix_if_set requires string param")
                default = let_cfg.default or ""
                if p.optional:
                    expr = (
                        f"({src} == null || {src}!.isEmpty) ? {default!r} : "
                        f"{let_cfg.prefix!r} + {src}!"
                    )
                    lines.append(
                        f"  final {dname} = {expr};"
                    )
                else:
                    lines.append(
                        f"  final {dname} = {src}.isEmpty ? {default!r} : {let_cfg.prefix!r} + {src};"
                    )
                dart_let_name_by_py[let_cfg.name] = dname
            elif let_cfg.op == "uuid_str_default":
                if not let_cfg.name or not let_cfg.param or let_cfg.default is None:
                    raise ValueError(
                        f"{fn.name}: uuid_str_default let requires name+param+default"
                    )
                dname = _dart_ident(let_cfg.name)
                src = dart_name_by_py.get(let_cfg.param) or _dart_ident(let_cfg.param)
                lines.append(f"  final {dname} = {src}?.uuid ?? {let_cfg.default!r};")
                dart_let_name_by_py[let_cfg.name] = dname
            elif let_cfg.op == "int_str_default":
                if not let_cfg.name or not let_cfg.param or let_cfg.default is None:
                    raise ValueError(
                        f"{fn.name}: int_str_default let requires name+param+default"
                    )
                dname = _dart_ident(let_cfg.name)
                src = dart_name_by_py.get(let_cfg.param) or _dart_ident(let_cfg.param)
                p = param_by_name.get(let_cfg.param)
                if p is not None and p.optional:
                    lines.append(
                        f"  final {dname} = ({src} == null || {src} == 0) ? {let_cfg.default!r} : {src}.toString();"
                    )
                else:
                    lines.append(
                        f"  final {dname} = ({src} == 0) ? {let_cfg.default!r} : {src}.toString();"
                    )
                dart_let_name_by_py[let_cfg.name] = dname
            elif let_cfg.op == "sorted_pair":
                if not let_cfg.names or len(let_cfg.names) != 2 or len(let_cfg.params) != 2:
                    raise ValueError(
                        f"{fn.name}: sorted_pair let requires names[2] + params[2]"
                    )
                a_py, b_py = let_cfg.names
                a_d = _dart_ident(a_py)
                b_d = _dart_ident(b_py)
                p1_py, p2_py = let_cfg.params
                p1_d = dart_name_by_py.get(p1_py) or _dart_ident(p1_py)
                p2_d = dart_name_by_py.get(p2_py) or _dart_ident(p2_py)
                lines.append(
                    f"  final ids = <String>[{p1_d}.uuid, {p2_d}.uuid]..sort();"
                )
                lines.append(f"  final {a_d} = ids[0];")
                lines.append(f"  final {b_d} = ids[1];")
                dart_let_name_by_py[a_py] = a_d
                dart_let_name_by_py[b_py] = b_d
            elif let_cfg.op == "list_join":
                if not let_cfg.name or not let_cfg.param or let_cfg.sep is None:
                    raise ValueError(
                        f"{fn.name}: list_join let requires name+param+sep"
                    )
                dname = _dart_ident(let_cfg.name)
                src = dart_name_by_py.get(let_cfg.param) or _dart_ident(let_cfg.param)
                p = param_by_name.get(let_cfg.param)
                iter_expr = (
                    f"{src} ?? const <String>[]"
                    if p is not None and p.optional
                    else src
                )
                items_var = f"_{dname}Items"
                lines.append(f"  final {items_var} = <String>[];")
                lines.append(f"  for (final raw in {iter_expr}) {{")
                item_expr = _dart_normalize_expr("raw", let_cfg.normalize)
                lines.append(f"    final item = {item_expr};")
                lines.append("    if (item.isEmpty) continue;")
                lines.append(f"    {items_var}.add(item);")
                lines.append("  }")
                if let_cfg.unique:
                    # Determinism: loader enforces unique => sort.
                    uniq_var = f"_{dname}Unique"
                    lines.append(
                        f"  final {uniq_var} = {items_var}.toSet().toList()..sort();"
                    )
                    lines.append(f"  final {dname} = {uniq_var}.join({let_cfg.sep!r});")
                elif let_cfg.sort:
                    sorted_var = f"_{dname}Sorted"
                    lines.append(
                        f"  final {sorted_var} = List<String>.from({items_var})..sort();"
                    )
                    lines.append(f"  final {dname} = {sorted_var}.join({let_cfg.sep!r});")
                else:
                    lines.append(f"  final {dname} = {items_var}.join({let_cfg.sep!r});")
                dart_let_name_by_py[let_cfg.name] = dname
            else:
                raise ValueError(f"{fn.name}: unsupported let op {let_cfg.op!r}")

        def _replace(m: re.Match[str]) -> str:
            key = m.group(1)
            if key in dart_let_name_by_py:
                var = dart_let_name_by_py[key]
                return f"${{{var}}}"
            if key in dart_name_by_py:
                p = param_by_name[key]
                var = dart_name_by_py[key]
                return _dart_value_expr(var=var, p=p)
            raise ValueError(f"{fn.name}: unknown template key {key!r}")

        # Replace `{param}` placeholders in the seed template with Dart string interpolation.
        #
        # NOTE: Use a single backslash in the regex to match literal braces. Over-escaping here
        # would fail to match and would silently emit seeds with `{param}` still present.
        dart_seed = re.sub(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", _replace, fn.template)

        if fn.namespace == "NAMESPACE_URL":
            ns_expr = "Namespace.url.value"
        else:
            ns = ns_by_name.get(fn.namespace)
            if ns is None:
                raise ValueError(f"{fn.name}: unknown namespace {fn.namespace!r}")
            ns_expr = _snake_to_lower_camel(ns.name)

        lines.append(f"  final seed = {dart_seed!r};")
        lines.append(f"  return UuidValue.fromString(_uuid.v5({ns_expr}, seed));")
        lines.append("}")
        lines.append("")

    return "\n".join(lines)


class DartStableIdsRendererLanguage(ObjectConfigGraphRendererLanguage):
    """
    Emit a compiler-owned `stable_ids.dart` module for an ontology Dart package.

    This renderer is intentionally file-only:
    - It emits exactly one module (`stable_ids.dart`) when a module-owned stable-ids spec exists.
    - It emits nothing for all regular OCG files (so it cannot clobber model/api outputs).
    """

    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy) -> None:
        super().__init__(layout_strategy=layout_strategy)
        self._stable_ids_spec: StableIdsSpec | None = None
        self._ownership: str = "authored"
        self._resolution_policy: str = "class_strict"
        self._source_graph: ObjectConfigGraph | None = None

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
        # No section assemblers needed; this renderer emits a single full-file module.
        return

    @override
    def set_policy(self, policy: ObjectConfigGraphRendererPolicy | None) -> None:
        if policy is None:
            self._ownership = "authored"
            self._resolution_policy = "class_strict"
            self._source_graph = None
            return
        ownership_mode: str | None = None
        resolution_mode: str | None = None
        if isinstance(policy, dict):
            policy_map = cast(dict[str, object], policy)
            raw_ownership = policy_map.get("stable_ids_ownership")
            if raw_ownership is not None:
                ownership_mode = str(raw_ownership).strip().lower()
            raw_resolution = policy_map.get("stable_ids_resolution_policy")
            if raw_resolution is not None:
                resolution_mode = str(raw_resolution).strip().lower()
            source_graph = policy_map.get("stable_ids_source_graph")
            if isinstance(source_graph, ObjectConfigGraph):
                self._source_graph = source_graph
        else:
            raw_ownership = getattr(policy, "stable_ids_ownership", None)
            if raw_ownership is not None:
                ownership_mode = str(cast(object, raw_ownership)).strip().lower()
            raw_resolution = getattr(policy, "stable_ids_resolution_policy", None)
            if raw_resolution is not None:
                resolution_mode = str(cast(object, raw_resolution)).strip().lower()
            source_graph = getattr(policy, "stable_ids_source_graph", None)
            if isinstance(source_graph, ObjectConfigGraph):
                self._source_graph = source_graph
        if ownership_mode is not None:
            if ownership_mode not in {"authored", "compiler"}:
                raise ValueError(f"stable_ids_ownership must be one of: authored, compiler (got {ownership_mode!r})")
            self._ownership = ownership_mode
        if resolution_mode is not None:
            if resolution_mode != "class_strict":
                raise ValueError(
                    "stable_ids_resolution_policy must be class_strict "
                    + f"(got {resolution_mode!r})"
                )
            self._resolution_policy = resolution_mode

    @override
    def bind_object_config_graph(self, graph: ObjectConfigGraph) -> None:
        source_graph = self._source_graph or graph
        self._stable_ids_spec = load_stable_ids_spec_for_graph(
            graph=source_graph,
            ownership=self._ownership,
            resolution_policy=self._resolution_policy,
        )

    @override
    def extra_output_paths(self) -> list[Path]:
        if self._stable_ids_spec is None:
            return []
        return [Path("stable_ids.dart")]

    @override
    def create_empty_code(self) -> Code:
        return build_renderer_empty_code(
            language=CodeLanguage.dart,
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
        if self._stable_ids_spec is None:
            return

        _ = writer.token(render_dart_stable_ids_module(spec=self._stable_ids_spec))


__all__ = [
    "DartStableIdsRendererLanguage",
]
