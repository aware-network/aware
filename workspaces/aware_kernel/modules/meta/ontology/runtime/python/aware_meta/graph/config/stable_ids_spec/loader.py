from __future__ import annotations

from pathlib import Path
from typing import cast
import re
import tomllib

from aware_meta.manifest.loader import load_aware_toml_spec
from aware_meta.manifest.spec import AwarePackageKind
from aware_meta.graph.config.stable_ids_spec.spec import (
    FunctionSpec,
    LetOp,
    LetSpec,
    NamespaceKind,
    NamespaceSpec,
    ParamSpec,
    ParamType,
    ParsedDefaultPrimitive,
    StableIdsSpec,
)


_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_TEMPLATE_KEY_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")

_VALID_NAMESPACE_KINDS: set[str] = {"ns_url", "uuid"}
_VALID_PARAM_TYPES: set[str] = {
    "uuid",
    "str",
    "bytes",
    "bool",
    "int",
    "float",
    "str_list",
}
_VALID_LET_OPS: set[str] = {
    "hex",
    "normalize",
    "normalize_default",
    "prefix_if_set",
    "sorted_pair",
    "bool_int",
    "uuid_str_default",
    "int_str_default",
    "list_join",
}

# Cache: repo_root -> fqn_prefix -> stable_ids.toml path
_STABLE_IDS_TOML_INDEX: dict[Path, dict[str, Path]] = {}


def _ensure_ident(name: str, *, ctx: str) -> str:
    normalized = (name or "").strip()
    if not _IDENT_RE.match(normalized):
        raise ValueError(f"Invalid identifier {normalized!r} ({ctx})")
    return normalized


def _require_table(*, value: object, ctx: str, source_label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{ctx} must be a table: {source_label}")
    return cast(dict[str, object], value)


def _require_table_list(
    *, value: object, ctx: str, source_label: str
) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{ctx} must be a list: {source_label}")
    result: list[dict[str, object]] = []
    for index, item in enumerate(cast(list[object], value)):
        if not isinstance(item, dict):
            raise ValueError(f"{ctx}[{index}] must be a table: {source_label}")
        result.append(cast(dict[str, object], item))
    return result


def _load_spec_from_raw(*, raw: object, source_label: str) -> StableIdsSpec:
    root = _require_table(value=raw, ctx="stable_ids.toml", source_label=source_label)
    version_raw = root.get("version")
    if version_raw is None:
        version = 0
    elif isinstance(version_raw, int):
        version = version_raw
    else:
        version = int(str(version_raw))
    if version != 1:
        raise ValueError(
            f"Unsupported stable_ids.toml version={version} (expected 1): {source_label}"
        )

    namespaces: list[NamespaceSpec] = []
    for i, item in enumerate(
        _require_table_list(
            value=root.get("namespaces"), ctx="namespaces", source_label=source_label
        )
    ):
        name = _ensure_ident(str(item.get("name") or ""), ctx=f"namespaces[{i}].name")
        kind = str(item.get("kind") or "").strip()
        if kind not in _VALID_NAMESPACE_KINDS:
            raise ValueError(
                f"namespaces[{i}].kind must be ns_url|uuid (got {kind!r}): {source_label}"
            )
        value = str(item.get("value") or "").strip()
        if not value:
            raise ValueError(f"namespaces[{i}].value is required: {source_label}")
        namespaces.append(
            NamespaceSpec(name=name, kind=cast(NamespaceKind, kind), value=value)
        )

    functions: list[FunctionSpec] = []
    for i, item in enumerate(
        _require_table_list(
            value=root.get("functions"), ctx="functions", source_label=source_label
        )
    ):
        fn_name = _ensure_ident(str(item.get("name") or ""), ctx=f"functions[{i}].name")
        namespace = _ensure_ident(
            str(item.get("namespace") or ""), ctx=f"functions[{i}].namespace"
        )
        template = str(item.get("template") or "")
        if not template:
            raise ValueError(f"functions[{i}].template is required: {source_label}")

        params: list[ParamSpec] = []
        for j, param_item in enumerate(
            _require_table_list(
                value=item.get("params"),
                ctx=f"functions[{i}].params",
                source_label=source_label,
            )
        ):
            p_name = _ensure_ident(
                str(param_item.get("name") or ""),
                ctx=f"functions[{i}].params[{j}].name",
            )
            p_type = str(param_item.get("type") or "").strip()
            if p_type not in _VALID_PARAM_TYPES:
                raise ValueError(
                    f"functions[{i}].params[{j}].type unsupported: {p_type!r}"
                )
            optional = bool(param_item.get("optional") or False)
            default_raw = param_item.get("default", None)
            param_default: ParsedDefaultPrimitive
            if default_raw is None:
                param_default = None
            elif isinstance(default_raw, bool):
                param_default = default_raw
            elif isinstance(default_raw, int):
                param_default = default_raw
            elif isinstance(default_raw, float):
                param_default = default_raw
            elif isinstance(default_raw, str):
                param_default = default_raw
            else:
                param_default = str(default_raw)
            non_empty = bool(param_item.get("non_empty") or False)
            normalize_raw = param_item.get("normalize")
            if normalize_raw is None:
                normalize_raw = []
            if not isinstance(normalize_raw, list):
                raise ValueError(
                    f"functions[{i}].params[{j}].normalize must be a list: {source_label}"
                )
            normalize = tuple(
                str(x).strip()
                for x in cast(list[object], normalize_raw)
                if str(x).strip()
            )
            params.append(
                ParamSpec(
                    name=p_name,
                    type=cast(ParamType, p_type),
                    optional=optional,
                    default=param_default,
                    non_empty=non_empty,
                    normalize=normalize,
                )
            )

        lets: list[LetSpec] = []
        for j, let_item in enumerate(
            _require_table_list(
                value=item.get("lets"),
                ctx=f"functions[{i}].lets",
                source_label=source_label,
            )
        ):
            op = str(let_item.get("op") or "").strip()
            if op not in _VALID_LET_OPS:
                raise ValueError(f"functions[{i}].lets[{j}].op unsupported: {op!r}")
            let_name = let_item.get("name")
            if let_name is not None:
                let_name = _ensure_ident(
                    str(let_name), ctx=f"functions[{i}].lets[{j}].name"
                )

            names_raw = let_item.get("names")
            if names_raw is None:
                names_list: list[object] = []
            elif isinstance(names_raw, list):
                names_list = cast(list[object], names_raw)
            else:
                raise ValueError(
                    f"functions[{i}].lets[{j}].names must be a list: {source_label}"
                )
            names = tuple(
                _ensure_ident(str(n), ctx=f"functions[{i}].lets[{j}].names")
                for n in names_list
            )

            param = let_item.get("param")
            if param is not None:
                param = _ensure_ident(str(param), ctx=f"functions[{i}].lets[{j}].param")

            params_raw = let_item.get("params")
            if params_raw is None:
                params_list: list[object] = []
            elif isinstance(params_raw, list):
                params_list = cast(list[object], params_raw)
            else:
                raise ValueError(
                    f"functions[{i}].lets[{j}].params must be a list: {source_label}"
                )
            let_params = tuple(
                _ensure_ident(str(n), ctx=f"functions[{i}].lets[{j}].params[{k}]")
                for k, n in enumerate(params_list)
            )

            normalize_raw = let_item.get("normalize")
            if normalize_raw is None:
                normalize_raw = []
            if not isinstance(normalize_raw, list):
                raise ValueError(
                    f"functions[{i}].lets[{j}].normalize must be a list: {source_label}"
                )
            normalize = tuple(
                str(x).strip()
                for x in cast(list[object], normalize_raw)
                if str(x).strip()
            )

            default_raw = let_item.get("default")
            default: str | None = None if default_raw is None else str(default_raw)
            prefix_raw = let_item.get("prefix")
            prefix: str | None = None if prefix_raw is None else str(prefix_raw)
            sep_raw = let_item.get("sep")
            sep: str | None = None if sep_raw is None else str(sep_raw)
            unique = bool(let_item.get("unique") or False)
            sort = bool(let_item.get("sort") or False)

            if op == "list_join":
                if sep is None or not sep.strip():
                    raise ValueError(
                        f"functions[{i}].lets[{j}].sep is required for list_join"
                    )
                if unique and not sort:
                    raise ValueError(
                        f"functions[{i}].lets[{j}]: list_join unique=true requires sort=true"
                    )
            if op == "prefix_if_set":
                if sep is not None:
                    raise ValueError(
                        f"functions[{i}].lets[{j}]: prefix_if_set does not support sep"
                    )
                if prefix is None:
                    raise ValueError(
                        f"functions[{i}].lets[{j}].prefix is required for prefix_if_set"
                    )

            lets.append(
                LetSpec(
                    op=cast(LetOp, op),
                    name=let_name,
                    names=names,
                    param=param,
                    params=let_params,
                    normalize=normalize,
                    default=default,
                    prefix=prefix,
                    sep=sep,
                    unique=unique,
                    sort=sort,
                )
            )

        allowed_keys: set[str] = {p.name for p in params}
        for let_spec in lets:
            if let_spec.name:
                allowed_keys.add(let_spec.name)
            allowed_keys.update(let_spec.names)
        for match in _TEMPLATE_KEY_RE.finditer(template):
            key = match.group(1)
            if key not in allowed_keys:
                raise ValueError(
                    f"{fn_name}: unknown template key {key!r} (spec={source_label})"
                )

        doc_raw = item.get("doc")
        doc: str | None = None if doc_raw is None else str(doc_raw).rstrip()
        dart_name_raw = item.get("dart_name")
        dart_name: str | None = None
        if dart_name_raw is not None:
            dart_name = _ensure_ident(
                str(dart_name_raw), ctx=f"functions[{i}].dart_name"
            )

        functions.append(
            FunctionSpec(
                name=fn_name,
                namespace=namespace,
                template=template,
                params=tuple(params),
                lets=tuple(lets),
                doc=doc,
                dart_name=dart_name,
            )
        )

    return StableIdsSpec(
        version=version,
        namespaces=tuple(namespaces),
        functions=tuple(functions),
    )


def load_stable_ids_spec_from_path(*, spec_path: Path) -> StableIdsSpec:
    return _load_spec_from_raw(
        raw=tomllib.loads(spec_path.read_text(encoding="utf-8")),
        source_label=str(spec_path),
    )


def load_stable_ids_spec_from_toml_text(
    *, toml_text: str, source_label: str = "<memory>"
) -> StableIdsSpec:
    return _load_spec_from_raw(
        raw=tomllib.loads(toml_text),
        source_label=source_label,
    )


def _build_stable_ids_toml_index(*, repo_root: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    modules_root = (repo_root / "modules").resolve()
    if not modules_root.exists():
        return index

    for module_root in sorted(modules_root.iterdir(), key=lambda p: p.as_posix()):
        if not module_root.is_dir():
            continue
        aware_toml = module_root / "structure" / "ontology" / "aware.toml"
        if not aware_toml.exists():
            continue
        try:
            spec = load_aware_toml_spec(toml_path=aware_toml)
        except Exception:
            continue
        if spec.package.kind != AwarePackageKind.ontology:
            continue
        stable_ids_toml = aware_toml.parent / "stable_ids.toml"
        if stable_ids_toml.exists():
            index[spec.package.fqn_prefix] = stable_ids_toml.resolve()
    return index


def resolve_stable_ids_toml_path_for_fqn_prefix(
    *,
    fqn_prefix: str,
    repo_root: Path,
) -> Path | None:
    key = (fqn_prefix or "").strip()
    if not key:
        return None
    repo_root = repo_root.expanduser().resolve()
    index = _STABLE_IDS_TOML_INDEX.get(repo_root)
    if index is None:
        index = _build_stable_ids_toml_index(repo_root=repo_root)
        _STABLE_IDS_TOML_INDEX[repo_root] = index
    return index.get(key)


def count_authored_functions_in_spec_path(*, spec_path: Path) -> int:
    try:
        payload = _require_table(
            value=tomllib.loads(spec_path.read_text(encoding="utf-8")),
            ctx="stable_ids.toml",
            source_label=str(spec_path),
        )
    except Exception:
        # Keep compiler ownership fail-closed: malformed authored specs cannot silently pass.
        return 1
    function_tables = _require_table_list(
        value=payload.get("functions"),
        ctx="functions",
        source_label=str(spec_path),
    )
    return len(function_tables)


__all__ = [
    "count_authored_functions_in_spec_path",
    "load_stable_ids_spec_from_path",
    "load_stable_ids_spec_from_toml_text",
    "resolve_stable_ids_toml_path_for_fqn_prefix",
]
