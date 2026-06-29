"""
Python runtime-handlers renderer (AWARE-managed).

Goal: generate *managed* handler implementation stubs + a generated registry module so:
- Devs edit only:
  - USER_IMPORTS block
  - LOGIC blocks inside handler bodies
- Signatures + file layout are compiler-owned and rewritten deterministically from the OCG.

This renderer is opt-in via workflows: `renderer_kind="runtime_handlers"` and
`source="runtime_handlers"`.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
import keyword
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from uuid import UUID
from typing_extensions import override

# Code Ontology
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage

# Code Runtime
from aware_code.section.writer import CodeSectionWriter

# Content Runtime
# Meta Ontology
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

# Meta Runtime
from aware_meta.attribute.config.type_descriptor_helpers import (
    AttributeTypeInfo,
    resolve_type_info,
)
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta.graph.config.render.renderer_language import (
    ObjectConfigGraphRendererLanguage,
    build_renderer_empty_code,
)

# Python Grammar
from python_grammar.primitive_codec import PythonPrimitiveCodec
from python_grammar.import_grouping import (
    PythonImportGroupingPolicy,
    group_python_imports,
    semantic_import_roots_from_renderer_inputs,
)
from python_grammar.renderer_policy import DEFAULT_ORM_SUPPORT_IMPORT_ROOTS

# Aware Utils
from aware_utils.string_transform import to_snake_case

_PRIMITIVE_CODEC = PythonPrimitiveCodec()
_DOCSTRING_WRAP_WIDTH = 100
_MAX_IMPORT_LINE_LENGTH = 120


def _wrap_docstring_lines(description: str) -> list[str]:
    lines: list[str] = []
    for raw_line in description.strip("\n").splitlines():
        if not raw_line.strip():
            lines.append("")
            continue
        lines.extend(
            textwrap.wrap(
                raw_line,
                width=_DOCSTRING_WRAP_WIDTH,
                break_long_words=False,
                break_on_hyphens=False,
            )
            or [""]
        )
    return lines


_USER_IMPORTS_START = "# --- AWARE: USER_IMPORTS START"
_USER_IMPORTS_END = "# --- AWARE: USER_IMPORTS END"
_MANAGED_IMPORTS_START = "# --- AWARE: MANAGED_IMPORTS START"
_MANAGED_IMPORTS_END = "# --- AWARE: MANAGED_IMPORTS END"
_META_RUNTIME_HANDLER_IMPORT_REPLACEMENTS = (
    (
        "from aware_runtime.function_call.handler_execution_context import",
        "from aware_meta.runtime.handler_context import",
    ),
    (
        "from aware_runtime.function_call.author import resolve_author_id",
        "from aware_meta.runtime.author import resolve_author_id",
    ),
    (
        "# Runtime\nfrom aware_meta.runtime.handler_context",
        "# Meta Runtime\nfrom aware_meta.runtime.handler_context",
    ),
    (
        "# Runtime\nfrom aware_meta.runtime.author",
        "# Meta Runtime\nfrom aware_meta.runtime.author",
    ),
)
_META_RUNTIME_HANDLER_IMPORT_MIGRATION_WARNING = (
    "Deprecated Meta handler USER_IMPORTS migrated from "
    "`aware_runtime.function_call.*` to `aware_meta.runtime.*`."
)


def _logic_start(name: str) -> str:
    return f"# --- AWARE: LOGIC START {name}"


def _logic_end(name: str) -> str:
    return f"# --- AWARE: LOGIC END {name}"


def _safe_identifier(name: str) -> str:
    if not name:
        return name
    if keyword.iskeyword(name):
        return f"{name}_"
    return name


def runtime_handler_impl_relative_path(
    *,
    layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
    class_config: ClassConfig,
) -> Path:
    layout_path = _layout_relative_path(
        layout_strategy=layout_strategy,
        path=layout_strategy.get_class_file_path(class_config),
    )
    parts = tuple(part for part in layout_path.parts if part and part != ".")
    if not parts:
        return layout_path

    handler_impl_parts = _handler_impl_parts(parts)
    return _safe_runtime_impl_path(Path(*handler_impl_parts))


def runtime_handler_impl_module_import(
    *,
    layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
    class_config: ClassConfig,
    import_root: str | None,
) -> str:
    file_path = runtime_handler_impl_relative_path(
        layout_strategy=layout_strategy,
        class_config=class_config,
    )
    parts = list(file_path.parts)
    if parts:
        parts[-1] = Path(parts[-1]).stem
    module_parts = [part for part in parts if part]
    if import_root:
        module_parts.insert(0, import_root)
    return ".".join(module_parts).strip(".")


def _layout_relative_path(
    *,
    layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
    path: Path,
) -> Path:
    rel = Path(path)
    if not rel.is_absolute():
        return rel
    try:
        return rel.relative_to(Path(layout_strategy.base_dir).resolve())
    except ValueError:
        return rel


def _handler_impl_parts(parts: tuple[str, ...]) -> tuple[str, ...]:
    for index in range(0, len(parts) - 1):
        if parts[index] == "handlers" and parts[index + 1] == "impl":
            return parts[index:]
    if "impl" in parts:
        index = parts.index("impl")
        # `impl` can be a semantic schema name, for example
        # `program/impl/program_impl.py`. Keep that schema segment under the
        # handler implementation root instead of collapsing it into the root.
        return ("handlers", "impl", *parts[index:])
    if (
        len(parts) >= 3
        and parts[0] == "graph"
        and parts[1]
        in {
            "config",
            "instance",
            "projection",
        }
    ):
        return ("handlers", "impl", *parts[1:])
    return ("handlers", "impl", *parts)


def _safe_runtime_impl_path(rel: Path) -> Path:
    parts = list(rel.parts)
    if not parts:
        return rel
    if "impl" in parts:
        idx = parts.index("impl") + 1
    else:
        idx = 0
    if idx >= len(parts):
        return rel

    # Keyword-safe module segments for schema/subpackages.
    for seg_idx in range(idx, len(parts) - 1):
        parts[seg_idx] = _safe_identifier(parts[seg_idx])

    # Keyword-safe file stem for `from ... import ...` module imports.
    file_name = parts[-1]
    file_path = Path(file_name)
    if file_path.suffix:
        safe_stem = _safe_identifier(file_path.stem)
        parts[-1] = f"{safe_stem}{file_path.suffix}"
    else:
        parts[-1] = _safe_identifier(file_name)
    return Path(*parts)


def _emit_token(writer: CodeSectionWriter, txt: str) -> None:
    _ = writer.token(txt)


class _IndentWriter:
    def __init__(self, writer: CodeSectionWriter, *, indent_size: int):
        self._writer: CodeSectionWriter = writer
        self._indent_size: int = indent_size
        self._level: int = 0

    @contextmanager
    def indent(self):
        self._level += 1
        try:
            yield
        finally:
            self._level -= 1

    def write(self, txt: str) -> None:
        if self._level <= 0:
            _emit_token(self._writer, txt)
            return

        prefix = " " * (self._level * self._indent_size)
        lines = txt.splitlines(keepends=True)
        out: list[str] = []
        for line in lines:
            if line.strip():
                out.append(prefix + line)
            else:
                out.append(line)
        _emit_token(self._writer, "".join(out))


@dataclass(frozen=True)
class _RenderedParam:
    name: str
    type_annotation: str
    default_expr: str | None
    type_id: UUID | None
    type_name: str | None


@dataclass(frozen=True)
class _RenderedSignature:
    params: list[_RenderedParam]
    return_type: str
    return_type_id: UUID | None
    return_type_name: str | None


def _parse_user_imports(src: str) -> str:
    """Return the raw user-imports block (without markers)."""
    lines = src.splitlines(keepends=True)
    try:
        start = next(
            i for i, line in enumerate(lines) if line.strip() == _USER_IMPORTS_START
        )
        end = next(
            i for i, line in enumerate(lines) if line.strip() == _USER_IMPORTS_END
        )
    except StopIteration:
        return ""
    if end <= start:
        return ""
    return "".join(lines[start + 1 : end])


def _parse_managed_import_modules_by_symbol(src: str) -> dict[str, str]:
    """Return prior managed `from module import Symbol` mappings.

    Managed imports are compiler-owned, but existing handler impl files are the
    only available stable source for ontology import modules when older
    materialization paths omit `import_overrides`. The renderer still
    re-selects symbols from the current signatures; this parser only supplies
    module names for those required symbols.
    """
    lines = src.splitlines()
    try:
        start = next(
            i for i, line in enumerate(lines) if line.strip() == _MANAGED_IMPORTS_START
        )
        end = next(
            i for i, line in enumerate(lines) if line.strip() == _MANAGED_IMPORTS_END
        )
    except StopIteration:
        return {}
    if end <= start:
        return {}

    out: dict[str, str] = {}
    block = lines[start + 1 : end]
    i = 0
    while i < len(block):
        line = block[i].strip()
        if not line.startswith("from ") or " import " not in line:
            i += 1
            continue

        module_part, items_part = line.split(" import ", 1)
        module = module_part.removeprefix("from ").strip()
        raw_items: list[str] = []
        items_part = items_part.strip()
        if items_part.startswith("("):
            trailing = items_part.removeprefix("(").strip()
            if trailing and trailing != ")":
                raw_items.append(trailing)
            i += 1
            while i < len(block):
                candidate = block[i].strip()
                if candidate.startswith(")"):
                    break
                raw_items.append(candidate)
                i += 1
        else:
            raw_items.append(items_part)

        for raw_item in raw_items:
            for fragment in raw_item.split(","):
                symbol = fragment.split("#", 1)[0].strip().rstrip(",")
                if not symbol:
                    continue
                if " as " in symbol:
                    symbol = symbol.split(" as ", 1)[0].strip()
                if symbol.isidentifier():
                    out.setdefault(symbol, module)
        i += 1

    return out


def _normalize_preserved_user_imports_for_runtime_handlers(
    *,
    import_root: str,
    preserved_imports: str,
) -> str:
    if import_root != "aware_meta":
        return preserved_imports

    normalized_imports = preserved_imports
    for old_import, new_import in _META_RUNTIME_HANDLER_IMPORT_REPLACEMENTS:
        normalized_imports = normalized_imports.replace(old_import, new_import)
    return normalized_imports


def _normalize_runtime_handler_imports(
    imports: dict[str, set[str]]
) -> dict[str, set[str]]:
    normalized: dict[str, set[str]] = {}
    for module, symbols in imports.items():
        _add_runtime_handler_import_symbols(
            normalized,
            module=module,
            symbols=symbols,
        )
    return normalized


def _add_runtime_handler_import_symbols(
    out: dict[str, set[str]],
    *,
    module: str,
    symbols: set[str],
) -> None:
    module_name = module.strip()
    if not _is_python_module_path(module_name):
        return
    for raw_symbol in symbols:
        for raw_line in raw_symbol.splitlines():
            line = raw_line.strip().rstrip(",")
            if not line:
                continue
            if line.startswith("from ") and " import " in line:
                module_part, imported_part = line.split(" import ", 1)
                imported_module = module_part.removeprefix("from ").strip()
                if _is_python_module_path(imported_module):
                    _add_imported_symbols(
                        out, module=imported_module, symbols_expr=imported_part
                    )
                continue
            _add_imported_symbols(out, module=module_name, symbols_expr=line)


def _add_imported_symbols(
    out: dict[str, set[str]], *, module: str, symbols_expr: str
) -> None:
    for fragment in symbols_expr.strip().strip("()").split(","):
        symbol = fragment.split("#", 1)[0].strip().rstrip(",")
        if " as " in symbol:
            symbol = symbol.split(" as ", 1)[0].strip()
        if symbol.isidentifier():
            out.setdefault(module, set()).add(symbol)


def _is_python_module_path(value: str) -> bool:
    return bool(value) and all(part.isidentifier() for part in value.split("."))


def _parse_logic_blocks(src: str) -> dict[str, str]:
    """Map `logic_name` -> raw block content (including indentation, without markers)."""
    lines = src.splitlines(keepends=True)
    out: dict[str, str] = {}
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("# --- AWARE: LOGIC START "):
            name = stripped.removeprefix("# --- AWARE: LOGIC START ").strip()
            try:
                end_idx = next(
                    j
                    for j in range(i + 1, len(lines))
                    if lines[j].strip() == _logic_end(name)
                )
            except StopIteration:
                i += 1
                continue
            raw = "".join(lines[i + 1 : end_idx])
            # Stored logic blocks are always nested under an indented function body.
            # Dedent here so regenerated output stays stable (writer re-indents per scope).
            out[name] = textwrap.dedent(raw)
            i = end_idx + 1
            continue
        i += 1
    return out


class PythonRendererRuntimeHandlers(ObjectConfigGraphRendererLanguage):
    """
    Emit:
    - `handlers/impl/<schema>/<class>.py`: managed stubs for human-authored logic.
    - `handlers/_generated/handlers.py`: managed wrapper + `AWARE_HANDLERS` registry.
    """

    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy):
        super().__init__(layout_strategy)
        self._warnings: list[str] = []
        self._class_by_id: dict[UUID, ClassConfig] = {}
        self._enum_id_by_name: dict[str, UUID] = {}
        self._owner_by_function_id: dict[UUID, ClassConfig] = {}
        self._link_by_function_id: dict[UUID, ClassConfigFunctionConfig] = {}
        self._impl_name_by_function_id: dict[UUID, str] = {}
        self._rendered_class_by_id: dict[UUID, ClassConfig] = {}
        self._managed_import_module_by_symbol: dict[str, str] = {}
        self._runtime_surface_class_by_id: dict[UUID, ClassConfig] = {}
        self._runtime_surface_class_by_fqn: dict[str, ClassConfig] = {}
        self._runtime_surface_class_by_name: dict[str, ClassConfig] = {}

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
    def define_assemblers(self):
        return None

    @override
    def create_empty_code(self) -> Code:
        return build_renderer_empty_code(
            language=CodeLanguage.python,
            renderer_key=type(self).__name__,
        )

    @override
    def clear_warnings(self) -> None:
        self._warnings = []

    @override
    def get_warnings(self) -> list[str]:
        return list(self._warnings)

    @override
    def set_policy(self, policy) -> None:
        self._runtime_surface_class_by_id = {}
        self._runtime_surface_class_by_fqn = {}
        self._runtime_surface_class_by_name = {}
        policy_map = policy if isinstance(policy, dict) else {}
        source_graph = policy_map.get("stable_ids_source_graph")
        if not isinstance(source_graph, ObjectConfigGraph):
            return
        for node in source_graph.object_config_graph_nodes:
            cc = node.class_config
            if cc is not None:
                self._runtime_surface_class_by_id[cc.id] = cc
                if cc.class_fqn:
                    self._runtime_surface_class_by_fqn[cc.class_fqn] = cc
                if cc.name:
                    self._runtime_surface_class_by_name.setdefault(cc.name, cc)

    def _runtime_surface_class_for(self, class_config: ClassConfig) -> ClassConfig:
        by_id = self._runtime_surface_class_by_id.get(class_config.id)
        by_fqn = self._runtime_surface_class_by_fqn.get(class_config.class_fqn)
        by_name = self._runtime_surface_class_by_name.get(class_config.name)
        return by_id or by_fqn or by_name or class_config

    @override
    def bind_object_config_graph(self, graph: ObjectConfigGraph) -> None:
        self._class_by_id = {}
        self._enum_id_by_name = {}
        self._owner_by_function_id = {}
        self._link_by_function_id = {}
        self._impl_name_by_function_id = {}
        self._rendered_class_by_id = {}

        # Index classes
        for node in graph.object_config_graph_nodes:
            cc = node.class_config
            if cc is None:
                continue
            self._class_by_id[cc.id] = cc

        # Index enums by name for best-effort type imports.
        for node in graph.object_config_graph_nodes:
            ec = node.enum_config
            if ec is None:
                continue
            self._enum_id_by_name[ec.name] = ec.id

        # Index function ownership and constructor-ness.
        for cc in self._class_by_id.values():
            fn_links = sorted(
                cc.class_config_function_configs,
                key=lambda link: (link.position, str(link.function_config_id)),
            )
            for link in fn_links:
                fn = link.function_config
                self._owner_by_function_id[fn.id] = cc
                self._link_by_function_id[fn.id] = link

            impl_name_by_fn = self._compute_impl_names_for_class(fn_links=fn_links)
            self._impl_name_by_function_id.update(impl_name_by_fn)

    def _compute_impl_names_for_class(
        self, *, fn_links: list[ClassConfigFunctionConfig]
    ) -> dict[UUID, str]:
        proposed_by_fn_id: dict[UUID, str] = {}
        used_names: dict[str, list[UUID]] = {}

        for link in fn_links:
            fn = link.function_config
            proposed = self._propose_impl_name(fn=fn, fn_link=link)
            proposed_by_fn_id[fn.id] = proposed
            used_names.setdefault(proposed, []).append(fn.id)

        out: dict[UUID, str] = {}
        for base_name, fn_ids in used_names.items():
            if len(fn_ids) == 1:
                out[fn_ids[0]] = base_name
                continue

            for fn_id in sorted(fn_ids, key=str):
                suffix = str(fn_id).split("-", 1)[0]
                out[fn_id] = _safe_identifier(f"{base_name}_{suffix}")
        return out

    def _propose_impl_name(
        self, *, fn: FunctionConfig, fn_link: ClassConfigFunctionConfig
    ) -> str:
        _ = fn_link
        # Runtime wrapper -> impl mapping is one-to-one with compiler function names.
        # Do not collapse `_via_<path>` suffixes; path-scoped constructors are distinct.
        return _safe_identifier(fn.name)

    @override
    def extra_output_paths(self) -> list[Path]:
        ext = self.layout_strategy.get_file_extension()
        return [Path("handlers") / "_generated" / f"handlers{ext}"]

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
        _ = schema, class_to_class_config_map, base_class_module, base_class_name

        cls = next(
            (obj for obj in meta_objects if isinstance(obj, ClassConfig)),
            None,
        )
        if cls is not None:
            self._emit_impl_file(writer=writer, class_config=cls)
            return

        # Emit generated registry for:
        # - explicit extra output path (empty meta_objects), and
        # - function-mapped generated path (meta_objects contains FunctionConfig entries).
        if not meta_objects or all(
            isinstance(obj, FunctionConfig) for obj in meta_objects
        ):
            self._emit_generated_handlers_file(writer=writer)
        return

    # ---------------------------------------------------------------------
    # Impl stubs
    # ---------------------------------------------------------------------
    def _emit_impl_file(
        self, *, writer: CodeSectionWriter, class_config: ClassConfig
    ) -> None:
        class_config = self._runtime_surface_class_for(class_config)
        self._rendered_class_by_id[class_config.id] = class_config
        fn_links = sorted(
            class_config.class_config_function_configs,
            key=lambda link: (
                link.position,
                str(link.function_config_id),
            ),
        )
        # Do not emit stubs for classes that have no functions.
        # This keeps `handlers/impl/**` minimal and avoids generating empty "placeholder" files.
        if not fn_links:
            return

        file_path = runtime_handler_impl_relative_path(
            layout_strategy=self.layout_strategy,
            class_config=class_config,
        )
        output_path = (
            Path(self.layout_strategy.base_dir).resolve() / file_path
        ).resolve()

        existing_src = ""
        if output_path.exists():
            try:
                existing_src = output_path.read_text(encoding="utf-8")
            except Exception:
                existing_src = ""

        raw_preserved_imports = (
            _parse_user_imports(existing_src) if existing_src else ""
        )
        preserved_imports = _normalize_preserved_user_imports_for_runtime_handlers(
            import_root=self._runtime_handlers_import_root(),
            preserved_imports=raw_preserved_imports,
        )
        if preserved_imports != raw_preserved_imports:
            self._warnings.append(
                _META_RUNTIME_HANDLER_IMPORT_MIGRATION_WARNING
                + f" impl_output={output_path}"
            )
        preserved_logic = _parse_logic_blocks(existing_src) if existing_src else {}
        managed_import_module_by_symbol = (
            _parse_managed_import_modules_by_symbol(existing_src)
            if existing_src
            else {}
        )

        impl_name_by_fn_id = self._compute_impl_names_for_class(fn_links=fn_links)
        allowed_logic_names: set[str] = set()
        for link in fn_links:
            fn = link.function_config
            allowed_logic_names.add(_safe_identifier(fn.name))
            allowed_logic_names.add(
                impl_name_by_fn_id.get(fn.id, _safe_identifier(fn.name))
            )
        unknown_logic_names = set(preserved_logic.keys()) - allowed_logic_names
        if unknown_logic_names:
            current_function_names = sorted(allowed_logic_names)
            unknown_blocks = sorted(unknown_logic_names)
            message = (
                "AWARE runtime handler impl contains unknown/legacy logic blocks; "
                + f"class={class_config.name!r}; "
                + f"impl_output={output_path}; "
                + f"unknown_logic_blocks={unknown_blocks}; "
                + f"current_function_names={current_function_names}. "
                + "Rename the blocks to match the current function names."
            )
            raise ValueError(message)

        # Managed header
        _emit_token(writer, "from __future__ import annotations\n\n")

        previous_managed_import_module_by_symbol = self._managed_import_module_by_symbol
        self._managed_import_module_by_symbol = managed_import_module_by_symbol
        try:
            # Managed imports: required at runtime for default expressions (e.g. EnumType.DEFAULT),
            # plus TYPE_CHECKING imports for signatures (compiler-owned).
            runtime_imports: dict[str, set[str]] = {}
            for link in fn_links:
                fn = link.function_config
                sig = self._render_signature(fn=fn)
                for p in sig.params:
                    if p.default_expr is None:
                        continue
                    # Enum defaults are emitted as `EnumName.VALUE` and must be importable at runtime.
                    if (
                        p.type_id
                        and p.type_name
                        and p.default_expr.startswith(f"{p.type_name}.")
                    ):
                        mod = self._resolve_type_module_by_id_or_name(
                            type_id=p.type_id,
                            type_name=p.type_name,
                        )
                        if mod:
                            runtime_imports.setdefault(mod, set()).add(p.type_name)

            # Type-only imports (best-effort; full import graph is owned by the generated ontology/DTO packages).
            type_imports: dict[str, set[str]] = {}

            # Import the owning class type for instance handler `self` params (when available).
            class_mod = (self.import_overrides or {}).get(
                str(class_config.id)
            ) or self._managed_import_module_by_symbol.get(class_config.name)
            if class_mod:
                type_imports.setdefault(class_mod, set()).add(class_config.name)

            # Import types referenced by function signatures (inputs + outputs).
            for link in fn_links:
                fn = link.function_config
                sig = self._render_signature(fn=fn)
                for p in sig.params:
                    self._collect_type_imports(
                        type_imports, type_annotation=p.type_annotation
                    )
                    self._collect_type_imports_by_id(
                        type_imports,
                        type_id=p.type_id,
                        type_name=p.type_name,
                    )
                self._collect_type_imports(
                    type_imports, type_annotation=sig.return_type
                )
                self._collect_type_imports_by_id(
                    type_imports,
                    type_id=sig.return_type_id,
                    type_name=sig.return_type_name,
                )
        finally:
            self._managed_import_module_by_symbol = (
                previous_managed_import_module_by_symbol
            )

        # Avoid duplicating runtime imports inside TYPE_CHECKING when possible.
        for module in list(type_imports.keys()):
            if module in runtime_imports:
                type_imports[module] = type_imports[module] - runtime_imports[module]
                if not type_imports[module]:
                    del type_imports[module]

        _emit_token(writer, f"{_MANAGED_IMPORTS_START}\n")
        _emit_token(writer, "# fmt: off\n")
        combined_imports = self._merge_imports(runtime_imports, type_imports)
        self._emit_grouped_imports(writer=writer, imports=combined_imports)
        _emit_token(writer, "# fmt: on\n")
        _emit_token(writer, f"{_MANAGED_IMPORTS_END}\n\n")

        _emit_token(writer, f"{_USER_IMPORTS_START}\n")
        _emit_token(writer, preserved_imports if preserved_imports else "")
        if preserved_imports and not preserved_imports.endswith("\n"):
            _emit_token(writer, "\n")
        _emit_token(writer, f"{_USER_IMPORTS_END}\n\n")

        # Emit functions
        for link in fn_links:
            fn = link.function_config

            impl_name = impl_name_by_fn_id.get(fn.id, _safe_identifier(fn.name))
            preserved = preserved_logic.get(impl_name, "")
            if not preserved.strip():
                preserved = preserved_logic.get(_safe_identifier(fn.name), "")
            self._emit_impl_function(
                writer=writer,
                class_config=class_config,
                fn_link=link,
                fn=fn,
                impl_name=_safe_identifier(impl_name),
                preserved_logic=preserved,
            )
            _emit_token(writer, "\n\n")

    def _emit_impl_function(
        self,
        *,
        writer: CodeSectionWriter,
        class_config: ClassConfig,
        fn_link: ClassConfigFunctionConfig,
        fn: FunctionConfig,
        impl_name: str,
        preserved_logic: str,
    ) -> None:
        sig = self._render_signature(fn=fn)

        # Build signature string
        params: list[str] = []
        if not fn_link.is_constructor:
            self_name = _safe_identifier(to_snake_case(class_config.name))
            params.append(f"{self_name}: {class_config.name}")
        for p in sig.params:
            part = f"{_safe_identifier(p.name)}: {p.type_annotation}"
            if p.default_expr is not None:
                part += f" = {p.default_expr}"
            params.append(part)
        signature = "(" + (", ".join(params)) + ")"

        # Runtime handler implementations are always async (even for non-async `.aware`),
        # because propagation and runtime IO are async and wrappers always `await` the impl.
        _emit_token(writer, f"async def {impl_name}{signature} -> {sig.return_type}:\n")

        iw = _IndentWriter(writer, indent_size=self.indent)
        with iw.indent():
            if fn.description:
                iw.write('"""\n')
                for line in _wrap_docstring_lines(fn.description):
                    iw.write(f"{line}\n" if line else "\n")
                iw.write('"""\n\n')

            logic_name = impl_name
            iw.write(f"{_logic_start(logic_name)}\n")

            if preserved_logic.strip():
                preserved = (
                    preserved_logic
                    if preserved_logic.endswith("\n")
                    else preserved_logic + "\n"
                )
                iw.write(preserved)
            else:
                iw.write(
                    'raise NotImplementedError("AWARE: implement handler logic")\n'
                )

            iw.write(f"{_logic_end(logic_name)}\n")

    def _render_signature(
        self,
        *,
        fn: FunctionConfig,
    ) -> _RenderedSignature:
        input_edges = [
            e
            for e in fn.function_config_attribute_configs
            if e.type == FunctionAttributeType.input
        ]
        output_edges = [
            e
            for e in fn.function_config_attribute_configs
            if e.type == FunctionAttributeType.output
        ]
        input_edges.sort(key=lambda e: int(e.position))
        output_edges.sort(key=lambda e: int(e.position))

        params: list[_RenderedParam] = []
        for edge in input_edges:
            attr = edge.attribute_config
            assert attr is not None
            name = _safe_identifier(attr.name)
            type_info = resolve_type_info(attr)
            type_annotation = self._render_type_annotation(attr, type_info=type_info)
            default_expr = self._render_default_expr(attr, type_info=type_info)
            type_id, type_name = self._type_ref_from_info(type_info)
            params.append(
                _RenderedParam(
                    name=name,
                    type_annotation=type_annotation,
                    default_expr=default_expr,
                    type_id=type_id,
                    type_name=type_name,
                )
            )

        # Return type: prefer single output, otherwise None/Any.
        return_type = "None"
        return_type_id: UUID | None = None
        return_type_name: str | None = None
        if len(output_edges) == 1:
            out_attr = output_edges[0].attribute_config
            assert out_attr is not None
            type_info = resolve_type_info(out_attr)
            return_type = self._render_type_annotation(out_attr, type_info=type_info)
            return_type_id, return_type_name = self._type_ref_from_info(type_info)
        elif len(output_edges) > 1:
            return_type = "dict[str, Any]"

        return _RenderedSignature(
            params=params,
            return_type=return_type,
            return_type_id=return_type_id,
            return_type_name=return_type_name,
        )

    def _render_type_annotation(
        self, attr: AttributeConfig, *, type_info: AttributeTypeInfo | None = None
    ) -> str:
        type_info = type_info or resolve_type_info(attr)

        base_type = "Any"
        if (
            type_info.kind == AttributeTypeDescriptorKind.primitive
            and type_info.primitive_config
        ):
            prim = CodePrimitiveType.model_validate(
                type_info.primitive_config.primitive_type
            )
            base_type = _PRIMITIVE_CODEC.render(prim) or "Any"
        elif (
            type_info.kind == AttributeTypeDescriptorKind.enum and type_info.enum_config
        ):
            base_type = type_info.enum_config.name
        elif (
            type_info.kind == AttributeTypeDescriptorKind.class_
            and type_info.class_config
        ):
            base_type = type_info.class_config.name

        type_annotation = base_type
        if type_info.is_collection:
            type_annotation = f"list[{type_annotation}]"

        # Nullable if explicitly optional (default_value parses to null) or non-required.
        nullable = False
        if attr.is_required is False:
            nullable = True
        if attr.default_value is not None:
            try:
                if json.loads(attr.default_value) is None:
                    nullable = True
            except Exception:
                pass

        if nullable and not type_info.is_collection:
            type_annotation = f"{type_annotation} | None"
        return type_annotation

    def _render_default_expr(
        self,
        attr: AttributeConfig,
        *,
        type_info: AttributeTypeInfo | None = None,
    ) -> str | None:
        type_info = type_info or resolve_type_info(attr)
        if attr.default_value is not None:
            default_value = cast(object, json.loads(attr.default_value))
            if (
                type_info.kind == AttributeTypeDescriptorKind.primitive
                and type_info.primitive_config is not None
            ):
                primitive_type = CodePrimitiveType.model_validate(
                    type_info.primitive_config.primitive_type
                )
                if primitive_type.base_type == CodePrimitiveBaseType.json:
                    rendered_json_default = self._render_json_default_expr(
                        default_value=default_value,
                        primitive_type=primitive_type,
                    )
                    if rendered_json_default is not None:
                        return rendered_json_default
            if (
                type_info.kind == AttributeTypeDescriptorKind.enum
                and type_info.enum_config
            ):
                if type_info.is_collection and isinstance(default_value, list):
                    rendered_items: list[str] = []
                    for item in cast(list[object], default_value):
                        rendered_items.append(
                            (
                                "None"
                                if item is None or item in {"NULL", "None"}
                                else f"{type_info.enum_config.name}.{item}"
                            )
                        )
                    return "[" + ", ".join(rendered_items) + "]"
                if default_value is None or default_value in {"NULL", "None"}:
                    return "None"
                return f"{type_info.enum_config.name}.{default_value}"
            return _PRIMITIVE_CODEC.to_literal_string(default_value)

        # If optional, default to None.
        if attr.is_required is False:
            return "None"

        # No default.
        return None

    def _render_json_default_expr(
        self,
        *,
        default_value: object,
        primitive_type: CodePrimitiveType,
    ) -> str | None:
        json_kind = None
        if primitive_type.constraints:
            kind_value = primitive_type.constraints.get("json_kind")
            if isinstance(kind_value, str):
                json_kind = kind_value.lower()

        parsed = default_value
        if isinstance(parsed, str):
            try:
                parsed = cast(object, json.loads(parsed))
            except Exception:
                parsed = default_value

        if parsed is None:
            return "None"

        if json_kind == "array":
            if not isinstance(parsed, list):
                raise ValueError(
                    f"Invalid default for JsonArray handler parameter: expected array, got {type(parsed).__name__}"
                )
            if not parsed:
                return "JsonArray()"
            literal = _PRIMITIVE_CODEC.to_literal_string(cast(object, parsed))
            return f"JsonArray({literal})"

        if json_kind == "object":
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Invalid default for JsonObject handler parameter: expected object, got {type(parsed).__name__}"
                )
            if not parsed:
                return "JsonObject()"
            literal = _PRIMITIVE_CODEC.to_literal_string(cast(object, parsed))
            return f"JsonObject({literal})"

        return None

    def _type_ref_from_info(
        self, type_info: AttributeTypeInfo
    ) -> tuple[UUID | None, str | None]:
        if (
            type_info.kind == AttributeTypeDescriptorKind.class_
            and type_info.class_config
        ):
            return type_info.class_config.id, type_info.class_config.name
        if type_info.kind == AttributeTypeDescriptorKind.enum and type_info.enum_config:
            return type_info.enum_config.id, type_info.enum_config.name
        return None, None

    def _collect_type_imports(
        self, imports: dict[str, set[str]], *, type_annotation: str
    ) -> None:
        # Very small parser: extract identifiers that are likely class/enum names.
        # We rely on `import_overrides` to provide module paths for ClassConfig/EnumConfig ids.
        tokens: list[str] = []
        buf = ""
        for ch in type_annotation:
            if ch.isalnum() or ch == "_":
                buf += ch
            else:
                if buf:
                    tokens.append(buf)
                    buf = ""
        if buf:
            tokens.append(buf)

        # Skip builtins/typing primitives.
        skip = {
            "Any",
            "None",
            "str",
            "int",
            "float",
            "bool",
            "list",
            "dict",
            "tuple",
            "set",
        }
        for tok in tokens:
            if tok in skip:
                continue

            # Best-effort: resolve class/enum module from the graph indexes.
            mod = self._resolve_type_module_by_name(tok)
            if mod:
                imports.setdefault(mod, set()).add(tok)

    def _collect_type_imports_by_id(
        self,
        imports: dict[str, set[str]],
        *,
        type_id: UUID | None,
        type_name: str | None,
    ) -> None:
        if not type_id or not type_name:
            return
        mod = self._resolve_type_module_by_id_or_name(
            type_id=type_id,
            type_name=type_name,
        )
        if mod:
            imports.setdefault(mod, set()).add(type_name)

    def _resolve_type_module_by_id_or_name(
        self, *, type_id: UUID | None, type_name: str | None
    ) -> str | None:
        mod = self._resolve_type_module_by_id(type_id)
        if mod:
            return mod
        if type_name:
            return self._managed_import_module_by_symbol.get(type_name)
        return None

    def _resolve_type_module_by_id(self, type_id: UUID | None) -> str | None:
        if type_id is None:
            return None
        return (self.import_overrides or {}).get(str(type_id))

    def _resolve_type_module_by_name(self, name: str) -> str | None:
        # Built-in library types (not part of the OCG).
        if name == "datetime":
            return "datetime"
        if name == "UUID":
            return "uuid"

        # AWARE primitive helper types.
        if name in {
            "Json",
            "JsonArray",
            "JsonObject",
            "JsonValue",
            "Vector",
            "VectorDim",
        }:
            return "aware_code.types"

        # Try local class configs
        for cc in self._class_by_id.values():
            if cc.name == name:
                mod = (self.import_overrides or {}).get(str(cc.id))
                if mod:
                    return mod

        enum_id = self._enum_id_by_name.get(name)
        if enum_id is not None:
            mod = (self.import_overrides or {}).get(str(enum_id))
            if mod:
                return mod

        return None

    # ---------------------------------------------------------------------
    # Generated wrapper module
    # ---------------------------------------------------------------------
    def _emit_generated_handlers_file(self, *, writer: CodeSectionWriter) -> None:
        _emit_token(writer, "# This file is generated by AWARE. Do not edit.\n")
        _emit_token(writer, "from __future__ import annotations\n\n")

        # Stable ordering: class name then function position then function name.
        entries: list[
            tuple[str, int, str, ClassConfig, ClassConfigFunctionConfig, FunctionConfig]
        ] = []
        class_pool = (
            list(self._rendered_class_by_id.values())
            if self._rendered_class_by_id
            else list(self._class_by_id.values())
        )
        impl_name_by_fn = dict(self._impl_name_by_function_id)
        for owner in class_pool:
            fn_links = sorted(
                owner.class_config_function_configs,
                key=lambda link: (link.position, str(link.function_config_id)),
            )
            impl_name_by_fn.update(
                self._compute_impl_names_for_class(fn_links=fn_links)
            )
            for link in fn_links:
                fn = link.function_config
                pos = link.position
                entries.append((owner.name, pos, str(fn.id), owner, link, fn))
        entries.sort(key=lambda t: (t[0], t[1], t[2]))

        has_constructor = any(link.is_constructor for _, _, _, _, link, _ in entries)
        has_instance = any(not link.is_constructor for _, _, _, _, link, _ in entries)
        needs_cast = False
        for _, _, _, _, _, fn in entries:
            for edge in fn.function_config_attribute_configs:
                if edge.type != FunctionAttributeType.input:
                    continue
                attr = edge.attribute_config
                if "| None" in self._render_type_annotation(attr):
                    needs_cast = True
                    break
            if needs_cast:
                break
        imports: dict[str, set[str]] = {}
        if entries:
            typing_symbols = {"TYPE_CHECKING"}
            if needs_cast:
                typing_symbols.add("cast")
            imports["typing"] = typing_symbols
            declarative_symbols: set[str] = set()
            if has_constructor:
                declarative_symbols.add("constructor")
            if has_instance:
                declarative_symbols.add("instance")
            if declarative_symbols:
                imports["aware_meta.runtime.generated_handlers"] = declarative_symbols
        if imports:
            self._emit_grouped_imports(writer=writer, imports=imports)
        if entries:
            _emit_token(writer, "if TYPE_CHECKING:\n")
            _emit_token(
                writer,
                "    from aware_meta_ontology.function.function_call import FunctionCall\n",
            )
            _emit_token(writer, "    from aware_orm.models.orm_model import ORMModel\n")
            _emit_token(writer, "    from aware_orm.session.session import Session\n")
            _emit_token(
                writer,
                "    from aware_meta.runtime.generated_handlers import HandlerContext\n\n",
            )

        handler_rows: list[str] = []
        for _owner_name, _pos, _fn_id_str, owner, link, fn in entries:
            snake_class = to_snake_case(owner.name)
            impl_mod = runtime_handler_impl_module_import(
                layout_strategy=self.layout_strategy,
                class_config=owner,
                import_root=self._runtime_handlers_import_root(),
            )
            impl_fn = impl_name_by_fn.get(fn.id, _safe_identifier(fn.name))
            wrapper_name = f"{snake_class}__{fn.name}__handler"
            wrapper_name = _safe_identifier(wrapper_name)

            class_fqn = self._class_fqn(owner)

            self._emit_wrapper_function(
                writer=writer,
                wrapper_name=wrapper_name,
                impl_module=impl_mod,
                impl_function=impl_fn,
                class_config=owner,
                fn_link=link,
                fn=fn,
            )
            _emit_token(writer, "\n\n")

            if link.is_constructor:
                handler_rows.append(
                    f"    constructor({class_fqn!r}, {fn.name!r}, {wrapper_name}),"
                )
            else:
                handler_rows.append(
                    f"    instance({class_fqn!r}, {fn.name!r}, {wrapper_name}),"
                )

        _emit_token(writer, "AWARE_HANDLERS = [\n")
        for row in handler_rows:
            _emit_token(writer, f"{row}\n")
        _emit_token(writer, "]\n\n")
        _emit_token(writer, '__all__ = ["AWARE_HANDLERS"]\n')

    def _emit_wrapper_function(
        self,
        *,
        writer: CodeSectionWriter,
        wrapper_name: str,
        impl_module: str,
        impl_function: str,
        class_config: ClassConfig,
        fn_link: ClassConfigFunctionConfig,
        fn: FunctionConfig,
    ) -> None:
        sig = self._render_signature(fn=fn)
        input_edges = [
            e
            for e in fn.function_config_attribute_configs
            if e.type == FunctionAttributeType.input
        ]
        input_edges.sort(key=lambda e: int(e.position))

        # Wrapper signature is internal to the runtime registry: do not change.
        if fn_link.is_constructor:
            header = (
                "async def {name}(session: Session, ctx: HandlerContext, orm_class: type[ORMModel], "
                "args: list[object], kwargs: dict[str, object], function_call: FunctionCall) "
                "-> tuple[ORMModel, object]:\n"
            ).format(name=wrapper_name)
            ignored_params = "session, ctx, orm_class, kwargs, function_call"
        else:
            header = (
                "async def {name}(session: Session, ctx: HandlerContext, orm_model: ORMModel, "
                "args: list[object], kwargs: dict[str, object], function_call: FunctionCall) -> object:\n"
            ).format(name=wrapper_name)
            ignored_params = "session, ctx, kwargs, function_call"
        _emit_token(writer, header)
        iw = _IndentWriter(writer, indent_size=self.indent)
        with iw.indent():
            iw.write(f"_ = {ignored_params}\n")

            # Local imports keep handler manifest building light (no ontology import at import time).
            if input_edges:
                iw.write("from pydantic import TypeAdapter\n")
            iw.write(f"from {impl_module} import {impl_function} as _impl\n")

            # Import types needed for TypeAdapter expressions.
            needed_imports: dict[str, set[str]] = {}
            for p in sig.params:
                self._collect_type_imports(
                    needed_imports, type_annotation=p.type_annotation
                )
                self._collect_type_imports_by_id(
                    needed_imports,
                    type_id=p.type_id,
                    type_name=p.type_name,
                )
            needed_imports = _normalize_runtime_handler_imports(needed_imports)
            for module, symbols in sorted(needed_imports.items(), key=lambda kv: kv[0]):
                if not module or not symbols:
                    continue
                joined = ", ".join(sorted(symbols))
                iw.write(f"from {module} import {joined}\n")

            # Bind inputs
            for idx, edge in enumerate(input_edges):
                attr = edge.attribute_config
                assert attr is not None
                name = _safe_identifier(attr.name)
                type_annotation = self._render_type_annotation(attr)
                default_expr = self._render_default_expr(attr)

                iw.write(f"_raw_{name}: object | None = None\n")
                iw.write(f"if {json.dumps(attr.name)} in kwargs:\n")
                with iw.indent():
                    iw.write(f"_raw_{name} = kwargs[{json.dumps(attr.name)}]\n")
                iw.write("elif len(args) > {idx}:\n".format(idx=idx))
                with iw.indent():
                    iw.write(f"_raw_{name} = args[{idx}]\n")
                if default_expr is not None:
                    iw.write(f"if _raw_{name} is None:\n")
                    with iw.indent():
                        iw.write(f"_raw_{name} = {default_expr}\n")
                if "| None" in type_annotation:
                    validated_expr = (
                        f"TypeAdapter({type_annotation}).validate_python(_raw_{name})"
                    )
                    iw.write(
                        f"{name}: {type_annotation} = cast({type_annotation}, {validated_expr})\n"
                    )
                else:
                    iw.write(
                        f"{name}: {type_annotation} = TypeAdapter({type_annotation}).validate_python(_raw_{name})\n"
                    )

            # Invoke
            if fn_link.is_constructor:
                call_args = ", ".join(
                    f"{_safe_identifier(e.attribute_config.name)}={_safe_identifier(e.attribute_config.name)}"
                    for e in input_edges
                )  # type: ignore[union-attr]
                iw.write(
                    f"result = await _impl({call_args})\n"
                    if call_args
                    else "result = await _impl()\n"
                )
                iw.write("return result, result\n")
            else:
                self_name = _safe_identifier(to_snake_case(class_config.name))
                call_args = ", ".join(
                    f"{_safe_identifier(e.attribute_config.name)}={_safe_identifier(e.attribute_config.name)}"
                    for e in input_edges
                )  # type: ignore[union-attr]
                if call_args:
                    iw.write(
                        f"result = await _impl({self_name}=orm_model, {call_args})\n"
                    )
                else:
                    iw.write(f"result = await _impl({self_name}=orm_model)\n")
                iw.write("return result\n")

    def _runtime_handlers_import_root(self) -> str:
        # Runtime handler materializations write into a package rooted at the graph fqn_prefix.
        # Import overrides should use that as the package name.
        base = self.layout_strategy.import_root
        if base:
            return base
        # Fall back to parsing from base_dir (best-effort).
        return ""

    def _schema_for_class(self, cc: ClassConfig) -> str:
        rel = runtime_handler_impl_relative_path(
            layout_strategy=self.layout_strategy,
            class_config=cc,
        )
        parts = rel.parts
        try:
            idx = parts.index("impl")
            return parts[idx + 1]
        except Exception:
            return "default"

    def _safe_runtime_impl_path(self, rel: Path) -> Path:
        return _safe_runtime_impl_path(rel)

    def _class_fqn(self, cc: ClassConfig) -> str:
        module = (self.import_overrides or {}).get(str(cc.id))
        if module:
            return f"{module}.{cc.name}"
        return f"{cc.name}"

    def _merge_imports(self, *imports: dict[str, set[str]]) -> dict[str, set[str]]:
        merged: dict[str, set[str]] = {}
        for bucket in imports:
            for module, symbols in _normalize_runtime_handler_imports(bucket).items():
                if not module or not symbols:
                    continue
                merged.setdefault(module, set()).update(symbols)
        return merged

    def _emit_grouped_imports(
        self, *, writer: CodeSectionWriter, imports: dict[str, set[str]]
    ) -> None:
        if not imports:
            return
        package_groups = group_python_imports(
            imports,
            policy=PythonImportGroupingPolicy(
                semantic_import_roots=semantic_import_roots_from_renderer_inputs(
                    import_root=self.layout_strategy.import_root,
                    import_overrides=self.import_overrides,
                    external_graph_fqn_prefixes=(
                        graph.fqn_prefix for graph in self.external_graphs
                    ),
                ),
                support_import_roots=DEFAULT_ORM_SUPPORT_IMPORT_ROOTS,
            ),
        )
        for package_name, package_imports in package_groups.items():
            if package_name:
                _emit_token(writer, f"# {package_name.replace('_', ' ')}\n")

            def _module_sort_key(m: str) -> tuple[int, str]:
                return (0, m) if m.endswith("_enums") else (1, m)

            for module in sorted(package_imports.keys(), key=_module_sort_key):
                items = sorted(package_imports[module])
                _emit_token(
                    writer, self._render_from_import(module=module, items=items)
                )
            _emit_token(writer, "\n")

    def _render_from_import(self, *, module: str, items: list[str]) -> str:
        items_str = self._render_import_items(items, multiline=len(items) > 1)
        first_line_item = items_str.split("\n", 1)[0]
        import_line = f"from {module} import {first_line_item}"
        if len(import_line) <= _MAX_IMPORT_LINE_LENGTH:
            return f"from {module} import {items_str}\n"

        multiline_items = self._render_import_items(items, multiline=True)
        if len(f"from {module} import (") <= _MAX_IMPORT_LINE_LENGTH:
            return f"from {module} import {multiline_items}\n"

        wrapped_items = self._render_import_items(items, multiline=True, nested=True)
        return self._render_wrapped_from_import_module(
            module=module,
            items_str=wrapped_items,
        )

    def _render_import_items(
        self,
        items: list[str],
        *,
        multiline: bool,
        nested: bool = False,
    ) -> str:
        if not items:
            return ""
        if not multiline:
            return items[0]
        item_indent = "        " if nested else "    "
        close_indent = "    " if nested else ""
        return (
            "(\n"
            + "".join([f"{item_indent}{item},\n" for item in items])
            + f"{close_indent})"
        )

    def _render_wrapped_from_import_module(
        self,
        *,
        module: str,
        items_str: str,
    ) -> str:
        parts = module.split(".")
        if len(parts) <= 1:
            return f"from {module} import {items_str}\n"

        first_line_item = items_str.split("\n", 1)[0]
        lines: list[str] = []
        current = f"from {parts[0]}"
        for index, part in enumerate(parts[1:], start=1):
            is_last = index == len(parts) - 1
            suffix = f" import {first_line_item}" if is_last else ".\\"
            candidate = f"{current}.{part}"
            if (
                len(candidate + suffix) > _MAX_IMPORT_LINE_LENGTH
                and current != f"from {parts[0]}"
            ):
                lines.append(f"{current}.\\")
                current = f"    {part}"
            else:
                current = candidate

        lines.append(f"{current} import {items_str}")
        return "\n".join(lines) + "\n"


class _RuntimeHandlerImplLayoutStrategy(ObjectConfigGraphRenderLayoutStrategy):
    def __init__(self, wrapped: ObjectConfigGraphRenderLayoutStrategy):
        super().__init__(
            base_dir=wrapped.base_dir,
            import_root=wrapped.import_root,
            parent=wrapped,
            generated_ocg_node_manifest=getattr(
                wrapped, "generated_ocg_node_manifest", None
            ),
            template_paths=dict(getattr(wrapped, "template_paths", {})),
            entity_template_paths=dict(getattr(wrapped, "entity_template_paths", {})),
        )
        self._wrapped = wrapped

    @property
    @override
    def language(self) -> CodeLanguage:
        return self._wrapped.language

    @override
    def bind_graph(self, graph: ObjectConfigGraph) -> None:
        self._wrapped.bind_graph(graph)
        self.entity_layout_paths = dict(self._wrapped.entity_layout_paths)
        self.entity_layout_positions = dict(self._wrapped.entity_layout_positions)

    @override
    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return runtime_handler_impl_relative_path(
            layout_strategy=self._wrapped,
            class_config=class_config,
        )

    @override
    def get_enum_file_path(self, enum_config: EnumConfig) -> Path:
        return (
            Path("handlers")
            / "impl"
            / "_enums"
            / f"{_safe_identifier(to_snake_case(enum_config.name))}.py"
        )

    @override
    def get_function_file_path(self, function_config: FunctionConfig) -> Path:
        original_path = self._wrapped.get_function_file_path(function_config)
        parts = tuple(part for part in original_path.parts if part and part != ".")
        if not parts:
            return original_path
        return _safe_runtime_impl_path(Path(*_handler_impl_parts(parts)))

    @override
    def get_file_extension(self) -> str:
        return self._wrapped.get_file_extension()

    @override
    def get_module_import_path(self, file_path: Path) -> str:
        return self._wrapped.get_module_import_path(file_path)


class PythonRendererRuntimeHandlerImplStubs(PythonRendererRuntimeHandlers):
    """Emit only authored runtime handler implementation stubs."""

    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy):
        super().__init__(_RuntimeHandlerImplLayoutStrategy(layout_strategy))

    @override
    def extra_output_paths(self) -> list[Path]:
        return []

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
        _ = schema, class_to_class_config_map, base_class_module, base_class_name
        cls = next(
            (obj for obj in meta_objects if isinstance(obj, ClassConfig)),
            None,
        )
        if cls is not None:
            self._emit_impl_file(writer=writer, class_config=cls)


__all__ = [
    "PythonRendererRuntimeHandlerImplStubs",
    "PythonRendererRuntimeHandlers",
]
