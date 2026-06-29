from __future__ import annotations

from pathlib import Path
from typing import Mapping, cast
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
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta.graph.config.stable_ids_resolution import load_stable_ids_spec_for_graph
from aware_meta.graph.config.stable_ids_spec.spec import (
    ParamSpec,
    StableIdsSpec,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_utils.string_transform import to_snake_case


_CONSTRUCTOR_BINDINGS_EXPORT = "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID"
PYTHON_STABLE_IDS_IMPORT_ROOT_POLICY_KEY = "stable_ids_import_root"


def resolve_python_stable_ids_module_import(
    *,
    graph: ObjectConfigGraph | None = None,
    owner: ClassConfig | None = None,
    import_overrides: Mapping[str, str] | None = None,
    explicit_import_root: str | None = None,
) -> str:
    """Resolve the generated Python stable-id module for a rendered ontology package."""

    root = _normalize_stable_ids_import_root(explicit_import_root)
    if root is not None:
        return f"{root}.stable_ids"

    if owner is not None:
        override_module = (import_overrides or {}).get(str(owner.id))
        root = _ontology_root_from_module(override_module)
        if root is not None:
            return f"{root}.stable_ids"
        root = _ontology_root_from_module(owner.class_fqn)
        if root is not None:
            return f"{root}.stable_ids"

    if graph is not None:
        root = _ontology_root_from_fqn_prefix(graph.fqn_prefix or graph.name)
        if root is not None:
            return f"{root}.stable_ids"

    if owner is not None:
        root = _ontology_root_from_module(owner.class_fqn, allow_suffix=False)
        if root is not None:
            return f"{root}_ontology.stable_ids"

    raise ValueError("Unable to resolve Python stable_ids module import root.")


def _normalize_stable_ids_import_root(value: str | None) -> str | None:
    root = str(value or "").strip().replace("-", "_")
    if not root:
        return None
    if root.endswith(".stable_ids"):
        root = root[: -len(".stable_ids")]
    return root or None


def _ontology_root_from_module(
    value: str | None,
    *,
    allow_suffix: bool = True,
) -> str | None:
    root = str(value or "").strip().split(".", maxsplit=1)[0].replace("-", "_")
    if not root:
        return None
    if allow_suffix and not root.endswith("_ontology"):
        return None
    return root


def _ontology_root_from_fqn_prefix(value: str | None) -> str | None:
    root = str(value or "").strip().replace("-", "_")
    if not root:
        return None
    return root if root.endswith("_ontology") else f"{root}_ontology"


def _python_type(p: ParamSpec) -> str:
    base = {
        "uuid": "UUID",
        "str": "str",
        "bytes": "bytes",
        "bool": "bool",
        "int": "int",
        "float": "float",
        "str_list": "list[str]",
    }[p.type]
    if p.optional:
        return f"{base} | None"
    return base


def _py_repr_default(value: object) -> str:
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return repr(value)
    raise ValueError(f"Unsupported default literal: {value!r}")


def _python_normalize_expr(var: str, ops: tuple[str, ...]) -> str:
    expr = f'({var} or "")'
    for op in ops:
        if op == "strip":
            expr = f"{expr}.strip()"
        elif op in {"lower", "casefold"}:
            method = "casefold" if op == "casefold" else "lower"
            expr = f"{expr}.{method}()"
        elif op == "upper":
            expr = f"{expr}.upper()"
        else:
            raise ValueError(f"Unsupported normalize op for python: {op!r}")
    return expr


def _function_attr_sort_key(edge: object) -> tuple[int, str]:
    raw = cast(object | None, getattr(edge, "position", None))
    pos = int(raw) if isinstance(raw, int) else 0
    return (pos, str(getattr(edge, "id", "")))


def _derive_constructor_stable_id_bindings(
    *,
    graph: ObjectConfigGraph,
    spec: StableIdsSpec,
) -> dict[str, tuple[str, tuple[str, ...]]]:
    helper_param_names_by_name = {
        fn.name: tuple(param.name for param in fn.params) for fn in spec.functions
    }
    class_configs = sorted(
        [
            node.class_config
            for node in (graph.object_config_graph_nodes or [])
            if node.class_config is not None
        ],
        key=lambda cc: (str(cc.name or "").casefold(), str(cc.id)),
    )

    bindings: dict[str, tuple[str, tuple[str, ...]]] = {}
    for class_config in class_configs:
        class_name = str(class_config.name or "").strip()
        if not class_name:
            continue
        helper_name = f"stable_{to_snake_case(class_name)}_id"
        helper_param_names = helper_param_names_by_name.get(helper_name)
        if not helper_param_names:
            continue

        identity_signatures: dict[tuple[str, ...], list[str]] = {}
        fn_links = sorted(
            class_config.class_config_function_configs,
            key=lambda edge: (
                str(getattr(getattr(edge, "function_config", None), "name", "") or ""),
                str(edge.id),
            ),
        )
        for fn_link in fn_links:
            function_config = fn_link.function_config
            verb = str(getattr(function_config, "verb", "") or "").strip().casefold()
            is_constructor = bool(fn_link.is_constructor)
            if not is_constructor and verb != "construct":
                continue
            function_name = str(function_config.name or "").strip() or "<anonymous>"

            identity_names: list[str] = []
            fn_attrs = sorted(
                function_config.function_config_attribute_configs,
                key=_function_attr_sort_key,
            )
            for fn_attr in fn_attrs:
                if fn_attr.type != FunctionAttributeType.input:
                    continue
                if not fn_attr.is_identity_key:
                    continue
                attr_name = str(fn_attr.attribute_config.name or "").strip()
                if not attr_name:
                    continue
                identity_names.append(attr_name)
            if not identity_names:
                continue
            key = tuple(identity_names)
            identity_signatures.setdefault(key, []).append(function_name)

        if not identity_signatures:
            continue
        if len(identity_signatures) != 1:
            # This artifact is runtime constructor-binding metadata, not stable-id
            # ownership. A class with multiple constructor signatures does not have
            # one honest class-scoped binding row in the current artifact shape, so
            # we fail closed by omitting the row entirely.
            continue

        identity_signature = next(iter(identity_signatures.keys()))
        if not set(identity_signature).issubset(set(helper_param_names)):
            continue
        bindings[str(class_config.id)] = (helper_name, helper_param_names)

    return bindings


def render_python_stable_ids_module(
    *,
    spec: StableIdsSpec,
    constructor_bindings: dict[str, tuple[str, tuple[str, ...]]] | None = None,
) -> str:
    """
    Emit a compiler-owned `stable_ids.py` module.

    NOTE: This function must live in the Python language package (not Meta) so the
    grammar-level output rules are owned by the language plugin.
    """

    ns_by_name = spec.namespaces_by_name

    used_ns: set[str] = set()
    for fn in spec.functions:
        if fn.namespace != "NAMESPACE_URL":
            used_ns.add(fn.namespace)

    lines: list[str] = []
    lines.append("# GENERATED CODE - DO NOT MODIFY BY HAND")
    lines.append("# Canonical stable-id derivations (UUIDv5).")
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from uuid import NAMESPACE_URL, UUID, uuid5")
    lines.append("")

    for ns_name in sorted(used_ns):
        ns = ns_by_name.get(ns_name)
        if ns is None:
            raise ValueError(f"Unknown namespace {ns_name!r} in spec")
        if ns.kind == "ns_url":
            lines.append(f"{ns.name} = uuid5(NAMESPACE_URL, {ns.value!r})")
        elif ns.kind == "uuid":
            lines.append(f"{ns.name} = UUID({ns.value!r})")
        else:
            raise ValueError(f"Unsupported namespace kind: {ns.kind}")
    if used_ns:
        lines.append("")

    for fn in spec.functions:
        params_sig: list[str] = []
        for p in fn.params:
            default = None
            if p.default is not None:
                default = _py_repr_default(cast(object, p.default))
            elif p.optional:
                default = "None"
            ann = _python_type(p)
            if default is None:
                params_sig.append(f"{p.name}: {ann}")
            else:
                params_sig.append(f"{p.name}: {ann} = {default}")

        sig = ", ".join(params_sig)
        lines.append(f"def {fn.name}(*, {sig}) -> UUID:")

        if fn.doc:
            doc_lines = fn.doc.splitlines() or [fn.doc]
            lines.append('    """' + doc_lines[0])
            for dl in doc_lines[1:]:
                lines.append(f"    {dl}")
            lines.append('    """')
            lines.append("")

        for p in fn.params:
            if p.type != "str":
                continue
            if p.normalize:
                expr = _python_normalize_expr(p.name, p.normalize)
                lines.append(f"    {p.name} = {expr}")
            if p.non_empty:
                lines.append(f"    if not ({p.name} or '').strip():")
                lines.append(f"        raise ValueError({fn.name!r} + ' requires non-empty {p.name}')")

        for let_cfg in fn.lets:
            if let_cfg.op == "hex":
                if not let_cfg.name or not let_cfg.param:
                    raise ValueError(f"{fn.name}: hex let requires name+param")
                lines.append(f"    {let_cfg.name} = {let_cfg.param}.hex()")
            elif let_cfg.op == "bool_int":
                if not let_cfg.name or not let_cfg.param:
                    raise ValueError(f"{fn.name}: bool_int let requires name+param")
                lines.append(f"    {let_cfg.name} = int({let_cfg.param})")
            elif let_cfg.op == "normalize":
                if not let_cfg.name or not let_cfg.param:
                    raise ValueError(f"{fn.name}: normalize let requires name+param")
                expr = _python_normalize_expr(let_cfg.param, let_cfg.normalize or ("casefold", "strip"))
                lines.append(f"    {let_cfg.name} = {expr}")
            elif let_cfg.op == "normalize_default":
                if not let_cfg.name or not let_cfg.param or let_cfg.default is None:
                    raise ValueError(f"{fn.name}: normalize_default let requires name+param+default")
                expr = _python_normalize_expr(let_cfg.param, let_cfg.normalize or ("casefold", "strip"))
                lines.append(f"    {let_cfg.name} = {expr} or {let_cfg.default!r}")
            elif let_cfg.op == "prefix_if_set":
                if not let_cfg.name or not let_cfg.param or let_cfg.prefix is None:
                    raise ValueError(f"{fn.name}: prefix_if_set let requires name+param+prefix")
                default = let_cfg.default or ""
                prefixed_expr = let_cfg.prefix + "{" + let_cfg.param + "}"
                lines.append(
                    f"    {let_cfg.name} = "
                    + f"f{prefixed_expr!r} if {let_cfg.param} else {default!r}"
                )
            elif let_cfg.op == "uuid_str_default":
                if not let_cfg.name or not let_cfg.param or let_cfg.default is None:
                    raise ValueError(f"{fn.name}: uuid_str_default let requires name+param+default")
                lines.append(
                    f"    {let_cfg.name} = str({let_cfg.param}) if {let_cfg.param} is not None else {let_cfg.default!r}"
                )
            elif let_cfg.op == "int_str_default":
                if not let_cfg.name or not let_cfg.param or let_cfg.default is None:
                    raise ValueError(f"{fn.name}: int_str_default let requires name+param+default")
                # Match the common `x or ''` stable-id pattern: treat `0` as empty.
                lines.append(f"    {let_cfg.name} = str({let_cfg.param}) if {let_cfg.param} else {let_cfg.default!r}")
            elif let_cfg.op == "sorted_pair":
                if not let_cfg.names or len(let_cfg.names) != 2 or len(let_cfg.params) != 2:
                    raise ValueError(f"{fn.name}: sorted_pair let requires names[2] + params[2]")
                a, b = let_cfg.names
                p1, p2 = let_cfg.params
                lines.append(f"    {a}, {b} = sorted(({p1}, {p2}), key=str)")
            elif let_cfg.op == "list_join":
                if not let_cfg.name or not let_cfg.param or let_cfg.sep is None:
                    raise ValueError(f"{fn.name}: list_join let requires name+param+sep")
                items_var = f"_{let_cfg.name}_items"
                norm_expr = _python_normalize_expr("x", let_cfg.normalize)
                lines.append(f"    {items_var} = [{norm_expr} for x in ({let_cfg.param} or [])]")
                lines.append(f"    {items_var} = [x for x in {items_var} if x]")
                if let_cfg.unique:
                    lines.append(f"    {items_var} = sorted(set({items_var}))")
                elif let_cfg.sort:
                    lines.append(f"    {items_var} = sorted({items_var})")
                lines.append(f"    {let_cfg.name} = {let_cfg.sep!r}.join({items_var})")
            else:
                raise ValueError(f"{fn.name}: unsupported let op {let_cfg.op!r}")

        ns_expr = "NAMESPACE_URL" if fn.namespace == "NAMESPACE_URL" else fn.namespace
        lines.append(f"    return uuid5({ns_expr}, f{fn.template!r})")
        lines.append("")

    bindings = constructor_bindings or {}
    lines.append(f"{_CONSTRUCTOR_BINDINGS_EXPORT}: dict[str, tuple[str, tuple[str, ...]]] = {{")
    for class_config_id, (helper_name, identity_names) in sorted(bindings.items(), key=lambda kv: kv[0]):
        lines.append(
            f"    {class_config_id!r}: ({helper_name!r}, {tuple(identity_names)!r}),"
        )
    lines.append("}")
    lines.append("")

    export_names = [fn.name for fn in spec.functions]
    export_names.append(_CONSTRUCTOR_BINDINGS_EXPORT)
    lines.append("__all__ = [")
    for name in export_names:
        lines.append(f"    {name!r},")
    lines.append("]")
    lines.append("")

    return "\n".join(lines)


class PythonStableIdsRendererLanguage(ObjectConfigGraphRendererLanguage):
    """
    Emit a compiler-owned `stable_ids.py` module for an ontology package.

    Canonical policy:
    - Stable-id formulas are authored once in `modules/<module>/structure/ontology/stable_ids.toml`.
    - Materialization emits `stable_ids.py` into the rendered output root (then packaging copies it
      under the python import_root).
    - This renderer must be a no-op for all other files (it must not clobber model outputs).
    """

    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy):
        super().__init__(layout_strategy=layout_strategy)
        self._stable_ids_spec: StableIdsSpec | None = None
        self._constructor_bindings: dict[str, tuple[str, tuple[str, ...]]] = {}
        self._ownership: str = "authored"
        self._resolution_policy: str = "class_strict"
        self._source_graph: ObjectConfigGraph | None = None
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
            policy_dict = cast(dict[str, object], policy)
            raw_ownership = policy_dict.get("stable_ids_ownership")
            if raw_ownership is not None:
                ownership_mode = str(raw_ownership).strip().lower()
            raw_resolution = policy_dict.get("stable_ids_resolution_policy")
            if raw_resolution is not None:
                resolution_mode = str(raw_resolution).strip().lower()
            source_graph = policy_dict.get("stable_ids_source_graph")
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
                raise ValueError(
                    "stable_ids_ownership must be one of: authored, compiler " + f"(got {ownership_mode!r})"
                )
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
        # Resolve stable ids spec by the graph's fqn_prefix (module-owned).
        source_graph = self._source_graph or graph
        self._stable_ids_spec = load_stable_ids_spec_for_graph(
            graph=source_graph,
            ownership=self._ownership,
            resolution_policy=self._resolution_policy,
        )
        self._constructor_bindings = _derive_constructor_stable_id_bindings(
            graph=source_graph,
            spec=self._stable_ids_spec,
        )

    @override
    def extra_output_paths(self) -> list[Path]:
        if self._stable_ids_spec is None:
            return []
        return [Path("stable_ids.py")]

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

        # Only emit content for the renderer-injected extra output file (meta_objects is empty).
        if meta_objects:
            return
        if self._stable_ids_spec is None:
            return

        _ = writer.token(
            render_python_stable_ids_module(
                spec=self._stable_ids_spec,
                constructor_bindings=self._constructor_bindings,
            )
        )


__all__ = [
    "PythonStableIdsRendererLanguage",
]
