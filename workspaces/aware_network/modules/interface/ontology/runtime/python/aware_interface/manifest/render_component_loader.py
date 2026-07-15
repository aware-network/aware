from __future__ import annotations

from pathlib import Path
from typing import cast

import tomllib

from aware_interface.manifest.render_component_spec import (
    AwareRenderComponentTomlBuildSpec,
    AwareRenderComponentTomlDartFlutterSpec,
    AwareRenderComponentTomlDartSpec,
    AwareRenderComponentTomlPackageSpec,
    AwareRenderComponentTomlPythonSpec,
    AwareRenderComponentTomlPythonTextualSpec,
    AwareRenderComponentTomlSpec,
)


class AwareRenderComponentTomlError(ValueError):
    """Raised when `aware.render_component.toml` fails strict validation."""


def load_aware_render_component_toml_spec_from_text(
    *,
    toml_text: str,
    toml_path: str | Path | None = None,
) -> AwareRenderComponentTomlSpec:
    p = Path(toml_path) if toml_path is not None else None
    path_label = str(p) if p is not None else "<aware.render_component.toml>"
    try:
        raw_obj = cast(object, tomllib.loads(toml_text or ""))
    except Exception as exc:
        raise AwareRenderComponentTomlError(
            f"Failed to parse TOML at {path_label}: {exc}"
        ) from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {path_label}")
    return _parse_aware_render_component_toml_raw(raw, path_label=path_label)


def load_aware_render_component_toml_spec(
    *,
    toml_path: str | Path,
) -> AwareRenderComponentTomlSpec:
    p = Path(toml_path)
    if not p.exists():
        raise AwareRenderComponentTomlError(f"aware.render_component.toml not found: {p}")
    try:
        raw_obj = cast(object, tomllib.loads(p.read_text(encoding="utf-8")))
    except Exception as exc:
        raise AwareRenderComponentTomlError(f"Failed to parse TOML at {p}: {exc}") from exc
    raw = _as_table(raw_obj, ctx=f"TOML root at {p}")
    return _parse_aware_render_component_toml_raw(raw, path_label=str(p))


def _parse_aware_render_component_toml_raw(
    raw: dict[str, object],
    *,
    path_label: str,
) -> AwareRenderComponentTomlSpec:
    _expect_keys(
        raw,
        required={"aware_render_component", "render_component", "build"},
        optional={"python", "dart"},
        ctx="root",
    )
    spec_version = _expect_int(raw, "aware_render_component", ctx="root")
    if spec_version != 1:
        raise AwareRenderComponentTomlError(
            f"Unsupported aware.render_component.toml version {spec_version}; expected 1"
        )

    package_tbl = _expect_table(raw, "render_component", ctx="root")
    _expect_keys(
        package_tbl,
        required={"package_name", "fqn_prefix"},
        optional={"version_number", "title", "description"},
        ctx="[render_component]",
    )
    package_name = _expect_str(package_tbl, "package_name", ctx="[render_component]")
    fqn_prefix = _expect_str(package_tbl, "fqn_prefix", ctx="[render_component]")
    version_number = _expect_opt_int(
        package_tbl,
        "version_number",
        ctx="[render_component]",
    ) or 1
    title = _expect_opt_str(package_tbl, "title", ctx="[render_component]")
    description = _expect_opt_str(package_tbl, "description", ctx="[render_component]")

    _validate_package_name(package_name, ctx="[render_component].package_name")
    _validate_fqn_prefix(fqn_prefix, ctx="[render_component].fqn_prefix")

    build_tbl = _expect_table(raw, "build", ctx="root")
    _expect_keys(
        build_tbl,
        required=set(),
        optional={"sources_dir", "include_paths", "exclude_paths", "force_fresh_scan"},
        ctx="[build]",
    )
    sources_dir = _expect_opt_str(build_tbl, "sources_dir", ctx="[build]") or "."
    include_paths = _expect_opt_str_list(build_tbl, "include_paths", ctx="[build]") or [
        "**/*.aware"
    ]
    exclude_paths = _expect_opt_str_list(build_tbl, "exclude_paths", ctx="[build]") or []
    force_fresh_scan = _expect_opt_bool(build_tbl, "force_fresh_scan", ctx="[build]")

    _validate_rel_path(sources_dir, ctx="[build].sources_dir")
    for index, include_path in enumerate(include_paths):
        _validate_rel_path(include_path, ctx=f"[build].include_paths[{index}]")
    for index, exclude_path in enumerate(exclude_paths):
        _validate_rel_path(exclude_path, ctx=f"[build].exclude_paths[{index}]")

    python_spec = None
    if "python" in raw:
        python_tbl = _expect_table(raw, "python", ctx="root")
        _expect_keys(
            python_tbl,
            required={"package_path", "import_root"},
            optional={"textual"},
            ctx="[python]",
        )
        package_path = _expect_str(python_tbl, "package_path", ctx="[python]")
        import_root = _expect_str(python_tbl, "import_root", ctx="[python]")
        _validate_rel_path(package_path, ctx="[python].package_path")
        _validate_module_ref(import_root, ctx="[python].import_root")
        textual_spec = None
        if "textual" in python_tbl:
            textual_tbl = _expect_table(python_tbl, "textual", ctx="[python]")
            _expect_keys(
                textual_tbl,
                required={"module", "symbol"},
                optional=set(),
                ctx="[python.textual]",
            )
            module = _expect_str(textual_tbl, "module", ctx="[python.textual]")
            symbol = _expect_str(textual_tbl, "symbol", ctx="[python.textual]")
            _validate_module_ref(module, ctx="[python.textual].module")
            _validate_symbol_ref(symbol, ctx="[python.textual].symbol")
            textual_spec = AwareRenderComponentTomlPythonTextualSpec(
                module=module,
                symbol=symbol,
            )
        python_spec = AwareRenderComponentTomlPythonSpec(
            package_path=package_path,
            import_root=import_root,
            textual=textual_spec,
        )

    dart_spec = None
    if "dart" in raw:
        dart_tbl = _expect_table(raw, "dart", ctx="root")
        _expect_keys(
            dart_tbl,
            required={"package_path", "package_name"},
            optional={"flutter"},
            ctx="[dart]",
        )
        dart_package_path = _expect_str(dart_tbl, "package_path", ctx="[dart]")
        dart_package_name = _expect_str(dart_tbl, "package_name", ctx="[dart]")
        _validate_rel_path(dart_package_path, ctx="[dart].package_path")
        _validate_dart_package_name(dart_package_name, ctx="[dart].package_name")
        flutter_spec = None
        if "flutter" in dart_tbl:
            flutter_tbl = _expect_table(dart_tbl, "flutter", ctx="[dart]")
            _expect_keys(
                flutter_tbl,
                required={"library", "symbol"},
                optional=set(),
                ctx="[dart.flutter]",
            )
            library = _expect_str(flutter_tbl, "library", ctx="[dart.flutter]")
            symbol = _expect_str(flutter_tbl, "symbol", ctx="[dart.flutter]")
            _validate_dart_library_ref(
                library,
                package_name=dart_package_name,
                ctx="[dart.flutter].library",
            )
            _validate_symbol_ref(symbol, ctx="[dart.flutter].symbol")
            flutter_spec = AwareRenderComponentTomlDartFlutterSpec(
                library=library,
                symbol=symbol,
            )
        dart_spec = AwareRenderComponentTomlDartSpec(
            package_path=dart_package_path,
            package_name=dart_package_name,
            flutter=flutter_spec,
        )

    return AwareRenderComponentTomlSpec(
        aware_render_component=spec_version,
        render_component=AwareRenderComponentTomlPackageSpec(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
            version_number=version_number,
            title=title,
            description=description,
        ),
        build=AwareRenderComponentTomlBuildSpec(
            sources_dir=sources_dir,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            force_fresh_scan=True if force_fresh_scan is None else force_fresh_scan,
        ),
        python=python_spec,
        dart=dart_spec,
    )


def _as_table(value: object, *, ctx: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AwareRenderComponentTomlError(f"Expected {ctx} to be a table/object")
    payload = cast(dict[object, object], value)
    return {str(k): v for k, v in payload.items()}


def _expect_keys(
    table: dict[str, object],
    *,
    required: set[str],
    optional: set[str],
    ctx: str,
) -> None:
    allowed = required | optional
    extra = set(table.keys()) - allowed
    missing = required - set(table.keys())
    if extra:
        raise AwareRenderComponentTomlError(f"Unknown keys in {ctx}: {sorted(extra)}")
    if missing:
        raise AwareRenderComponentTomlError(f"Missing keys in {ctx}: {sorted(missing)}")


def _expect_table(root: dict[str, object], key: str, *, ctx: str) -> dict[str, object]:
    val = root.get(key)
    if not isinstance(val, dict):
        raise AwareRenderComponentTomlError(
            f"Expected {ctx}.{key} to be a table; got {type(val)}"
        )
    payload = cast(dict[object, object], val)
    return {str(k): v for k, v in payload.items()}


def _expect_str(root: dict[str, object], key: str, *, ctx: str) -> str:
    val = root.get(key)
    if not isinstance(val, str) or not val.strip():
        raise AwareRenderComponentTomlError(
            f"Expected {ctx}.{key} to be a non-empty string"
        )
    return val


def _expect_opt_str(root: dict[str, object], key: str, *, ctx: str) -> str | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, str):
        raise AwareRenderComponentTomlError(f"Expected {ctx}.{key} to be a string or null")
    return val


def _expect_int(root: dict[str, object], key: str, *, ctx: str) -> int:
    val = root.get(key)
    if not isinstance(val, int):
        raise AwareRenderComponentTomlError(f"Expected {ctx}.{key} to be an int")
    return val


def _expect_opt_int(root: dict[str, object], key: str, *, ctx: str) -> int | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, int):
        raise AwareRenderComponentTomlError(f"Expected {ctx}.{key} to be an int or null")
    return val


def _expect_opt_bool(root: dict[str, object], key: str, *, ctx: str) -> bool | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, bool):
        raise AwareRenderComponentTomlError(f"Expected {ctx}.{key} to be a bool or null")
    return val


def _expect_opt_str_list(
    root: dict[str, object],
    key: str,
    *,
    ctx: str,
) -> list[str] | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, list):
        raise AwareRenderComponentTomlError(f"Expected {ctx}.{key} to be a list of strings")
    out: list[str] = []
    for index, item in enumerate(val):
        if not isinstance(item, str) or not item.strip():
            raise AwareRenderComponentTomlError(
                f"Expected {ctx}.{key}[{index}] to be a non-empty string"
            )
        out.append(item)
    return out


def _validate_package_name(value: str, *, ctx: str) -> None:
    if any(ch.isspace() for ch in value):
        raise AwareRenderComponentTomlError(
            f"{ctx} must not contain whitespace; got {value!r}"
        )


def _validate_fqn_prefix(value: str, *, ctx: str) -> None:
    if "." in value:
        raise AwareRenderComponentTomlError(
            f"{ctx} must not contain '.' (single-segment namespace); got {value!r}"
        )
    if any(ch.isspace() for ch in value):
        raise AwareRenderComponentTomlError(
            f"{ctx} must not contain whitespace; got {value!r}"
        )


def _validate_module_ref(value: str, *, ctx: str) -> None:
    if any(ch.isspace() for ch in value):
        raise AwareRenderComponentTomlError(
            f"{ctx} must not contain whitespace; got {value!r}"
        )
    if "/" in value or "\\" in value:
        raise AwareRenderComponentTomlError(
            f"{ctx} must use module notation, not path separators; got {value!r}"
        )


def _validate_symbol_ref(value: str, *, ctx: str) -> None:
    if any(ch.isspace() for ch in value):
        raise AwareRenderComponentTomlError(
            f"{ctx} must not contain whitespace; got {value!r}"
        )
    if "." in value:
        raise AwareRenderComponentTomlError(f"{ctx} must not contain '.'; got {value!r}")


def _validate_dart_package_name(value: str, *, ctx: str) -> None:
    _validate_package_name(value, ctx=ctx)
    if not value.replace("_", "").isalnum():
        raise AwareRenderComponentTomlError(
            f"{ctx} must contain only lowercase letters, digits, or underscores; got {value!r}"
        )
    if value.lower() != value:
        raise AwareRenderComponentTomlError(f"{ctx} must be lowercase; got {value!r}")


def _validate_dart_library_ref(value: str, *, package_name: str, ctx: str) -> None:
    if any(ch.isspace() for ch in value):
        raise AwareRenderComponentTomlError(
            f"{ctx} must not contain whitespace; got {value!r}"
        )
    prefix = f"package:{package_name}/"
    if not value.startswith(prefix):
        raise AwareRenderComponentTomlError(
            f"{ctx} must start with {prefix!r} for Dart package {package_name!r}; got {value!r}"
        )
    if not value.endswith(".dart"):
        raise AwareRenderComponentTomlError(f"{ctx} must end with '.dart'; got {value!r}")


def _validate_rel_path(value: str, *, ctx: str) -> None:
    path = Path(value)
    if path.is_absolute():
        raise AwareRenderComponentTomlError(f"{ctx} must be relative; got {value!r}")
    if ".." in path.parts:
        raise AwareRenderComponentTomlError(
            f"{ctx} must not contain '..'; got {value!r}"
        )


__all__ = [
    "AwareRenderComponentTomlError",
    "load_aware_render_component_toml_spec",
    "load_aware_render_component_toml_spec_from_text",
]
