from __future__ import annotations

from abc import ABC
import re
from difflib import get_close_matches

from aware_meta.manifest.loader import load_aware_toml_spec_from_text

from aware_code.language_service.features.base import ServiceMixinBase
from aware_code.language_service.features.diagnostics_capabilities.contracts import (
    AwareDiagnostic,
    DiagnosticRangeDict,
)
from aware_code.language_service.position import (
    ByteRange,
    Utf16Position,
    Utf16PositionMapper,
)


_TOML_LINE_COL_RE = re.compile(r"\(at line (?P<line>\d+), column (?P<col>\d+)\)")


def _toml_error_line_col(message: str) -> tuple[int, int] | None:
    match = _TOML_LINE_COL_RE.search(message or "")
    if match is None:
        return None
    try:
        line = int(match.group("line"))
        col = int(match.group("col"))
    except Exception:
        return None
    if line <= 0 or col <= 0:
        return None
    return line, col


def _range_for_line_col(mapper: Utf16PositionMapper, *, line: int, col: int) -> DiagnosticRangeDict:
    start = Utf16Position(line=max(0, line - 1), character=max(0, col - 1))
    end = Utf16Position(line=start.line, character=start.character + 1)
    # Clamp into the document so clients don't reject the range.
    start_byte = mapper.position_to_byte_offset(start)
    end_byte = mapper.position_to_byte_offset(end)
    start_pos, end_pos = mapper.byte_range_to_positions(ByteRange(start=start_byte, end=end_byte))
    return {
        "start": {"line": start_pos.line, "character": start_pos.character},
        "end": {"line": end_pos.line, "character": end_pos.character},
    }


def _default_range(mapper: Utf16PositionMapper) -> DiagnosticRangeDict:
    return _range_for_line_col(mapper, line=1, col=1)


def _find_dependency_name_ranges(*, text: str, dependency_name: str) -> list[ByteRange]:
    ranges: list[ByteRange] = []
    if not dependency_name:
        return ranges
    needle_bytes = dependency_name.encode("utf-8")
    if not needle_bytes:
        return ranges

    in_dependencies = False
    offset = 0
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("[[") and stripped.endswith("]]"):
            in_dependencies = stripped == "[[dependencies]]"
        elif stripped.startswith("[") and stripped.endswith("]"):
            in_dependencies = False

        line_bytes = line.encode("utf-8")
        if in_dependencies and "package_name" in stripped:
            idx = line_bytes.find(needle_bytes)
            if idx != -1:
                ranges.append(ByteRange(start=offset + idx, end=offset + idx + len(needle_bytes)))
        offset += len(line_bytes)
    return ranges


def _parse_unknown_keys(message: str) -> list[str]:
    if "Unknown keys in" not in message:
        return []
    if ":" not in message:
        return []
    tail = message.split(":", 1)[1].strip()
    keys: list[str] = []
    for match in re.finditer(r"""['"]([^'"]+)['"]""", tail):
        key = match.group(1).strip()
        if key:
            keys.append(key)
    return keys


def _find_key_ranges(*, text: str, key: str) -> list[ByteRange]:
    key = (key or "").strip()
    if not key:
        return []
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=", flags=re.MULTILINE)
    ranges: list[ByteRange] = []
    for match in pattern.finditer(text):
        match_text = match.group(0)
        key_idx = match_text.find(key)
        if key_idx == -1:
            continue
        start = match.start() + key_idx
        end = start + len(key)
        try:
            start_b = len(text[:start].encode("utf-8"))
            end_b = len(text[:end].encode("utf-8"))
        except Exception:
            continue
        if end_b <= start_b:
            continue
        ranges.append(ByteRange(start=start_b, end=end_b))
    return ranges


class ConfigDiagnosticsMixin(ServiceMixinBase, ABC):
    def config_diagnostics_for_uri(self, *, uri: str) -> list[AwareDiagnostic]:
        if uri.endswith("aware.toml"):
            return self._aware_toml_diagnostics(uri=uri)
        return []

    def _aware_toml_diagnostics(self, *, uri: str) -> list[AwareDiagnostic]:
        try:
            path = self._workspace.uri_to_path(uri)
        except Exception as exc:
            return [
                {
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 0, "character": 1},
                    },
                    "message": f"Invalid URI for aware.toml: {exc}",
                    "severity": 1,
                    "source": "aware",
                    "code": "aware.toml.invalid_uri",
                }
            ]

        try:
            text = self._workspace.get_document_text(uri)
        except Exception as exc:
            return [
                {
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 0, "character": 1},
                    },
                    "message": f"Failed to read aware.toml: {exc}",
                    "severity": 1,
                    "source": "aware",
                    "code": "aware.toml.read_error",
                }
            ]

        ctx = self._document_context(uri=uri, document_text=text)
        mapper = ctx.mapper
        diagnostics: list[AwareDiagnostic] = []

        try:
            spec = load_aware_toml_spec_from_text(toml_text=text, toml_path=path)
        except Exception as exc:
            message = str(exc)
            pos = _toml_error_line_col(message)
            rng = _range_for_line_col(mapper, line=pos[0], col=pos[1]) if pos is not None else _default_range(mapper)

            for key in _parse_unknown_keys(message):
                for key_rng in _find_key_ranges(text=text, key=key):
                    start, end = mapper.byte_range_to_positions(key_rng)
                    diagnostics.append(
                        {
                            "range": {
                                "start": {
                                    "line": start.line,
                                    "character": start.character,
                                },
                                "end": {"line": end.line, "character": end.character},
                            },
                            "message": message,
                            "severity": 1,
                            "source": "aware",
                            "code": "aware.toml.unknown_key",
                        }
                    )

            if diagnostics:
                return diagnostics

            diagnostics.append(
                {
                    "range": rng,
                    "message": message,
                    "severity": 1,
                    "source": "aware",
                    "code": "aware.toml.invalid",
                }
            )
            return diagnostics

        env_root = self._workspace.environment_root_for_uri(uri=uri)
        package_names: list[str] = []
        if env_root is not None:
            try:
                packages = self._workspace.environment_packages(env_root=env_root)
                package_names = sorted(packages.keys())
            except Exception:
                package_names = []

        known = set(package_names)
        for dep in spec.dependencies:
            dep_name = dep.package_name.strip()
            if not dep_name:
                continue
            if known and dep_name in known:
                continue

            suggestions = get_close_matches(dep_name, package_names, n=3, cutoff=0.6) if package_names else []
            ranges = _find_dependency_name_ranges(text=text, dependency_name=dep_name)
            if not ranges:
                ranges = [ByteRange(start=0, end=min(1, len(mapper.source_bytes)))]

            for r in ranges:
                start, end = mapper.byte_range_to_positions(r)
                diag: AwareDiagnostic = {
                    "range": {
                        "start": {"line": start.line, "character": start.character},
                        "end": {"line": end.line, "character": end.character},
                    },
                    "message": f"Unknown dependency package_name: {dep_name!r}",
                    "severity": 2,
                    "source": "aware",
                    "code": "aware.toml.dependency_unknown",
                }
                if suggestions:
                    diag["data"] = {"suggestions": suggestions}
                diagnostics.append(diag)

        return diagnostics
