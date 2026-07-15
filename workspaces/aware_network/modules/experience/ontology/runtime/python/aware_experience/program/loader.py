from __future__ import annotations

from pathlib import Path

import tomllib

from aware_experience.program.spec import (
    AwareProgramsTomlProgramSpec,
    AwareProgramsTomlSpec,
)


class AwareProgramsTomlError(ValueError):
    """Raised when `aware.programs.toml` fails strict validation."""


def load_aware_programs_toml_spec_from_text(
    *, toml_text: str, toml_path: str | Path | None = None
) -> AwareProgramsTomlSpec:
    p = Path(toml_path) if toml_path is not None else None
    path_label = str(p) if p is not None else "<aware.programs.toml>"
    try:
        raw = tomllib.loads(toml_text or "")
    except Exception as exc:
        raise AwareProgramsTomlError(
            f"Failed to parse TOML at {path_label}: {exc}"
        ) from exc
    if not isinstance(raw, dict):
        raise AwareProgramsTomlError(
            f"Expected TOML root to be a table/object at {path_label}"
        )
    return _parse_aware_programs_toml_raw(raw, path_label=path_label)


def load_aware_programs_toml_spec(*, toml_path: str | Path) -> AwareProgramsTomlSpec:
    p = Path(toml_path)
    if not p.exists():
        raise AwareProgramsTomlError(f"aware.programs.toml not found: {p}")

    try:
        raw = tomllib.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AwareProgramsTomlError(f"Failed to parse TOML at {p}: {exc}") from exc

    if not isinstance(raw, dict):
        raise AwareProgramsTomlError(f"Expected TOML root to be a table/object at {p}")
    return _parse_aware_programs_toml_raw(raw, path_label=str(p))


def _parse_aware_programs_toml_raw(
    raw: dict, *, path_label: str
) -> AwareProgramsTomlSpec:
    _expect_keys(raw, required={"aware", "programs"}, optional=set(), ctx="root")
    aware_version = _expect_int(raw, "aware", ctx="root")
    if aware_version != 1:
        raise AwareProgramsTomlError(
            f"Unsupported aware.programs.toml version {aware_version}; expected 1"
        )

    programs_raw = raw.get("programs")
    if not isinstance(programs_raw, list):
        raise AwareProgramsTomlError("Expected root.programs to be an array of tables")
    if not programs_raw:
        raise AwareProgramsTomlError("root.programs must contain at least one entry")

    out: list[AwareProgramsTomlProgramSpec] = []
    seen_refs: set[str] = set()
    seen_paths: set[str] = set()

    for i, row in enumerate(programs_raw):
        if not isinstance(row, dict):
            raise AwareProgramsTomlError(
                f"Expected programs[{i}] to be a table; got {type(row)}"
            )
        _expect_keys(
            row,
            required={"ref", "path", "name"},
            optional={"dependencies", "required_symbols", "optional_symbols"},
            ctx=f"[[programs]] (index={i})",
        )

        ref = _expect_str(row, "ref", ctx=f"programs[{i}]").strip()
        path = _expect_str(row, "path", ctx=f"programs[{i}]").strip()
        name = _expect_str(row, "name", ctx=f"programs[{i}]").strip()
        dependencies = tuple(
            _expect_opt_str_list(row, "dependencies", ctx=f"programs[{i}]") or ()
        )
        required_symbols = tuple(
            _expect_opt_str_list(row, "required_symbols", ctx=f"programs[{i}]") or ()
        )
        optional_symbols = tuple(
            _expect_opt_str_list(row, "optional_symbols", ctx=f"programs[{i}]") or ()
        )

        module_id, program_name = _parse_ref(ref, ctx=f"programs[{i}].ref")
        if name != program_name:
            raise AwareProgramsTomlError(
                f"programs[{i}].name must match ref program name {program_name!r}; got {name!r}"
            )
        _validate_rel_path(path, ctx=f"programs[{i}].path")
        if not path.endswith(".aware"):
            raise AwareProgramsTomlError(
                f"programs[{i}].path must point to a .aware file; got {path!r}"
            )
        _validate_module_id(module_id, ctx=f"programs[{i}].ref")

        for j, dep in enumerate(dependencies):
            _validate_non_empty(dep, ctx=f"programs[{i}].dependencies[{j}]")
        for j, sym in enumerate(required_symbols):
            _validate_symbol_name(sym, ctx=f"programs[{i}].required_symbols[{j}]")
        for j, sym in enumerate(optional_symbols):
            _validate_symbol_name(sym, ctx=f"programs[{i}].optional_symbols[{j}]")

        if ref in seen_refs:
            raise AwareProgramsTomlError(
                f"Duplicate programs[{i}].ref={ref!r} in {path_label}"
            )
        seen_refs.add(ref)

        if path in seen_paths:
            raise AwareProgramsTomlError(
                f"Duplicate programs[{i}].path={path!r} in {path_label}"
            )
        seen_paths.add(path)

        out.append(
            AwareProgramsTomlProgramSpec(
                ref=ref,
                path=path,
                name=name,
                dependencies=dependencies,
                required_symbols=required_symbols,
                optional_symbols=optional_symbols,
            )
        )

    return AwareProgramsTomlSpec(aware=aware_version, programs=tuple(out))


def _expect_keys(
    tbl: dict, *, required: set[str], optional: set[str], ctx: str
) -> None:
    allowed = required | optional
    extra = set(tbl.keys()) - allowed
    missing = required - set(tbl.keys())
    if extra:
        raise AwareProgramsTomlError(f"Unknown keys in {ctx}: {sorted(extra)}")
    if missing:
        raise AwareProgramsTomlError(f"Missing keys in {ctx}: {sorted(missing)}")


def _expect_str(root: dict, key: str, *, ctx: str) -> str:
    val = root.get(key)
    if not isinstance(val, str) or not val.strip():
        raise AwareProgramsTomlError(f"Expected {ctx}.{key} to be a non-empty string")
    return val


def _expect_int(root: dict, key: str, *, ctx: str) -> int:
    val = root.get(key)
    if not isinstance(val, int):
        raise AwareProgramsTomlError(f"Expected {ctx}.{key} to be an int")
    return val


def _expect_opt_str_list(root: dict, key: str, *, ctx: str) -> list[str] | None:
    val = root.get(key, None)
    if val is None:
        return None
    if not isinstance(val, list):
        raise AwareProgramsTomlError(f"Expected {ctx}.{key} to be a list[str] or null")
    out: list[str] = []
    for i, item in enumerate(val):
        if not isinstance(item, str):
            raise AwareProgramsTomlError(f"Expected {ctx}.{key}[{i}] to be a string")
        out.append(item)
    return out


def _parse_ref(ref: str, *, ctx: str) -> tuple[str, str]:
    if ":" not in ref:
        raise AwareProgramsTomlError(
            f"{ctx} must use '<module_id>:<program_name>' format; got {ref!r}"
        )
    module_id, program_name = ref.split(":", 1)
    module_id = module_id.strip()
    program_name = program_name.strip()
    if not module_id or not program_name:
        raise AwareProgramsTomlError(
            f"{ctx} must use '<module_id>:<program_name>' format; got {ref!r}"
        )
    return module_id, program_name


def _validate_module_id(value: str, *, ctx: str) -> None:
    if any(ch.isspace() for ch in value):
        raise AwareProgramsTomlError(f"{ctx} module_id must not contain whitespace")
    for ch in value:
        if ch.isalnum() or ch in "-_":
            continue
        raise AwareProgramsTomlError(
            f"{ctx} module_id contains unsupported character {ch!r}"
        )


def _validate_rel_path(value: str, *, ctx: str) -> None:
    p = Path(value)
    if p.is_absolute():
        raise AwareProgramsTomlError(
            f"{ctx} must be programs-root relative (not absolute): {value!r}"
        )
    if ".." in p.parts:
        raise AwareProgramsTomlError(f"{ctx} must not contain '..': {value!r}")


def _validate_non_empty(value: str, *, ctx: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise AwareProgramsTomlError(f"{ctx} must be a non-empty string")


def _validate_symbol_name(value: str, *, ctx: str) -> None:
    raw = (value or "").strip()
    if not raw:
        raise AwareProgramsTomlError(f"{ctx} must be a non-empty string")
    if raw.startswith("plan.") or raw.startswith("boot."):
        return
    if "." not in raw:
        raise AwareProgramsTomlError(
            f"{ctx} must be namespaced (expected 'plan.*', 'boot.*', or '<ns>.*')"
        )


__all__ = [
    "AwareProgramsTomlError",
    "load_aware_programs_toml_spec",
    "load_aware_programs_toml_spec_from_text",
]
