from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from aware_experience.compiler.models import (
    ExperienceActionOwnership,
    ExperienceActionProgramBindingOwnership,
)
from aware_experience.compiler.workspace import ExperienceWorkspace

_ACTION_HEADER_RE = re.compile(
    r"\baction\s+([A-Za-z_][A-Za-z0-9_]*)\s*(\([^{}]*\))?\s*\{",
    re.DOTALL,
)
_PROGRAM_STMT_RE = re.compile(
    r"\bprogram\s+([A-Za-z_][A-Za-z0-9_\.]*)\s*(\((.*?)\))?\s*;?",
    re.DOTALL,
)
_ACTION_NAME_STMT_RE = re.compile(
    r"\bname\s+(\"[^\"]+\"|'[^']+'|[A-Za-z_][A-Za-z0-9_:\.]*)\s*;?",
    re.DOTALL,
)


def load_action_ownership_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    package_name: str | None = None,
    fqn_prefix: str | None = None,
    is_dependency: bool = False,
) -> tuple[ExperienceActionOwnership, ...]:
    action_by_symbol: dict[str, ExperienceActionOwnership] = {}
    action_name_keys: set[str] = set()

    for relpath in source_files:
        rel = relpath.as_posix()
        if not _is_action_source_path(rel):
            continue
        source_path = (package_root / relpath).resolve()
        _assert_within(base=package_root, candidate=source_path, label="action source")
        text = source_path.read_text(encoding="utf-8")
        source_rel = relpath.as_posix()

        for symbol, raw_params, body in _iter_action_blocks(source_text=text):
            if symbol in action_by_symbol:
                raise ValueError(
                    f"Duplicate action symbol {symbol!r} across experience sources"
                )
            action_name = _normalize_action_name(
                _parse_action_name_override(body=body) or symbol
            )
            if action_name in action_name_keys:
                raise ValueError(
                    f"Duplicate action name {action_name!r} across experience sources"
                )
            action_name_keys.add(action_name)

            params = _parse_param_names(raw_params)
            program_bindings = _parse_action_program_bindings(body)
            action_by_symbol[symbol] = ExperienceActionOwnership(
                symbol=symbol,
                action_name=action_name,
                source_path=source_rel,
                params=params,
                program_bindings=program_bindings,
                package_name=_normalize_optional_token(package_name),
                fqn_prefix=_normalize_optional_token(fqn_prefix),
                is_dependency=is_dependency,
            )

    return tuple(
        sorted(
            action_by_symbol.values(),
            key=lambda item: (item.action_name, item.symbol, item.source_path),
        )
    )


def load_dependency_action_ownership_from_snapshot(
    *,
    snapshot: Any,
) -> tuple[ExperienceActionOwnership, ...]:
    actions: list[ExperienceActionOwnership] = []
    for dependency in (
        getattr(getattr(snapshot, "spec", None), "dependencies", ()) or ()
    ):
        package_name = _normalize_optional_token(
            getattr(dependency, "package_name", None)
        )
        if package_name is None:
            continue
        dependency_snapshot = _resolve_dependency_experience_snapshot(
            snapshot=snapshot,
            package_name=package_name,
        )
        if dependency_snapshot is None:
            continue
        dependency_package_name = _normalize_optional_token(
            dependency_snapshot.spec.experience.package_name
        )
        dependency_fqn_prefix = _normalize_optional_token(
            dependency_snapshot.spec.experience.fqn_prefix
        )
        actions.extend(
            load_action_ownership_from_sources(
                package_root=dependency_snapshot.package_root,
                source_files=dependency_snapshot.source_files,
                package_name=dependency_package_name,
                fqn_prefix=dependency_fqn_prefix,
                is_dependency=True,
            )
        )
    actions.sort(
        key=lambda item: (
            item.package_name or "",
            item.action_name.casefold(),
            item.symbol.casefold(),
            item.source_path,
        )
    )
    return tuple(actions)


def _iter_action_blocks(*, source_text: str) -> tuple[tuple[str, str | None, str], ...]:
    rows: list[tuple[str, str | None, str]] = []
    cursor = 0
    while True:
        match = _ACTION_HEADER_RE.search(source_text, cursor)
        if match is None:
            break
        symbol = (match.group(1) or "").strip()
        params = match.group(2)
        body_start = match.end()
        body_end = _find_matching_brace(source_text=source_text, start=body_start - 1)
        body = source_text[body_start:body_end].strip()
        rows.append((symbol, params, body))
        cursor = body_end + 1
    return tuple(rows)


def _find_matching_brace(*, source_text: str, start: int) -> int:
    if start < 0 or start >= len(source_text) or source_text[start] != "{":
        raise ValueError("Invalid action block start while parsing action declarations")

    depth = 0
    idx = start
    in_single = False
    in_double = False
    in_triple = False
    while idx < len(source_text):
        token = source_text[idx]
        nxt = source_text[idx : idx + 3]

        if in_triple:
            if nxt == '"""':
                in_triple = False
                idx += 3
                continue
            idx += 1
            continue
        if in_single:
            if token == "'" and source_text[idx - 1] != "\\":
                in_single = False
            idx += 1
            continue
        if in_double:
            if token == '"' and source_text[idx - 1] != "\\":
                in_double = False
            idx += 1
            continue

        if nxt == '"""':
            in_triple = True
            idx += 3
            continue
        if token == "'":
            in_single = True
            idx += 1
            continue
        if token == '"':
            in_double = True
            idx += 1
            continue
        if token == "{":
            depth += 1
        elif token == "}":
            depth -= 1
            if depth == 0:
                return idx
        idx += 1

    raise ValueError("Unclosed action block while parsing action declarations")


def _parse_param_names(raw_params: str | None) -> tuple[str, ...]:
    token = (raw_params or "").strip()
    if not token:
        return ()
    if not (token.startswith("(") and token.endswith(")")):
        return ()
    inner = token[1:-1].strip()
    if not inner:
        return ()
    rows = _split_csv(inner)
    names: list[str] = []
    for row in rows:
        entry = row.strip()
        if not entry:
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)", entry)
        if match is None:
            continue
        names.append(match.group(1))
    return tuple(names)


def _parse_action_name_override(*, body: str) -> str | None:
    match = _ACTION_NAME_STMT_RE.search(body)
    if match is None:
        return None
    return _clean_value(match.group(1))


def _parse_action_program_bindings(
    body: str,
) -> tuple[ExperienceActionProgramBindingOwnership, ...]:
    bindings: list[ExperienceActionProgramBindingOwnership] = []
    for match in _PROGRAM_STMT_RE.finditer(body):
        program = (match.group(1) or "").strip()
        if not program:
            continue
        args_raw = (match.group(3) or "").strip()
        args = tuple(_split_csv(args_raw)) if args_raw else ()
        bindings.append(
            ExperienceActionProgramBindingOwnership(
                program=program,
                args=tuple(arg.strip() for arg in args if arg.strip()),
            )
        )
    bindings.sort(key=lambda item: (item.program, tuple(item.args)))
    return tuple(bindings)


def _split_csv(payload: str) -> tuple[str, ...]:
    items: list[str] = []
    buff: list[str] = []
    depth = 0
    in_single = False
    in_double = False
    idx = 0
    while idx < len(payload):
        ch = payload[idx]
        if in_single:
            buff.append(ch)
            if ch == "'" and payload[idx - 1] != "\\":
                in_single = False
            idx += 1
            continue
        if in_double:
            buff.append(ch)
            if ch == '"' and payload[idx - 1] != "\\":
                in_double = False
            idx += 1
            continue
        if ch == "'":
            in_single = True
            buff.append(ch)
            idx += 1
            continue
        if ch == '"':
            in_double = True
            buff.append(ch)
            idx += 1
            continue
        if ch == "(":
            depth += 1
            buff.append(ch)
            idx += 1
            continue
        if ch == ")":
            depth = max(0, depth - 1)
            buff.append(ch)
            idx += 1
            continue
        if ch == "," and depth == 0:
            items.append("".join(buff).strip())
            buff = []
            idx += 1
            continue
        buff.append(ch)
        idx += 1
    if buff:
        items.append("".join(buff).strip())
    return tuple(item for item in items if item)


def _normalize_action_name(symbol: str) -> str:
    return (symbol or "").strip().casefold()


def _normalize_optional_token(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    token = raw.strip()
    return token or None


def _clean_value(value: str) -> str:
    token = (value or "").strip()
    if (token.startswith('"') and token.endswith('"')) or (
        token.startswith("'") and token.endswith("'")
    ):
        return token[1:-1]
    return token


def _is_action_source_path(path: str) -> bool:
    rel = (path or "").strip()
    if not rel:
        return False
    if "/actions/" in f"/{rel}" or rel.startswith("actions/"):
        return True
    return Path(rel).name == "actions.aware"


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if (
        candidate_resolved == base_resolved
        or base_resolved in candidate_resolved.parents
    ):
        return
    raise ValueError(
        f"{label} resolved outside package boundary: base={base_resolved} candidate={candidate_resolved}"
    )


def _resolve_dependency_experience_snapshot(
    *,
    snapshot: Any,
    package_name: str,
) -> Any | None:
    repo_root = getattr(snapshot, "repo_root", None)
    current_spec_path = getattr(snapshot, "spec_path", None)
    if not isinstance(repo_root, Path):
        return None
    current_spec_resolved = (
        current_spec_path.resolve() if isinstance(current_spec_path, Path) else None
    )
    for manifest_path in _iter_experience_manifest_candidates(repo_root=repo_root):
        resolved_manifest_path = manifest_path.resolve()
        if (
            current_spec_resolved is not None
            and resolved_manifest_path == current_spec_resolved
        ):
            continue
        try:
            dependency_snapshot = ExperienceWorkspace.from_toml(
                toml_path=resolved_manifest_path,
                repo_root=repo_root,
            ).build_snapshot()
        except Exception:
            continue
        candidate_package_name = _normalize_optional_token(
            dependency_snapshot.spec.experience.package_name
        )
        if candidate_package_name == package_name:
            return dependency_snapshot
    return None


def _iter_experience_manifest_candidates(*, repo_root: Path) -> tuple[Path, ...]:
    roots = (
        repo_root / "experiences",
        repo_root / "workspaces",
        repo_root / "modules",
    )
    manifests: dict[str, Path] = {}
    for root in roots:
        if not root.exists():
            continue
        for candidate in root.rglob("aware.experience.toml"):
            if candidate.is_file():
                manifests[candidate.resolve().as_posix()] = candidate
    return tuple(manifests[key] for key in sorted(manifests))


__all__ = [
    "load_dependency_action_ownership_from_snapshot",
    "load_action_ownership_from_sources",
]
