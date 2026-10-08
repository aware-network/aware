"""Strict `aware.spec.toml` parsing and semantic joins."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from typing import Any, cast

from aware_specification_runtime import phase_ref
from jsonschema import Draft202012Validator


class ManifestError(ValueError):
    pass


_INVARIANT_PATH = re.compile(r"invariants/[0-9]{2,}-[a-z][a-z0-9-]*/README\.md\Z")
_PHASE_PATH = re.compile(r"phases/([0-9]{2,})-[a-z][a-z0-9-]*/README\.md\Z")
_ITERATION_PATH = re.compile(
    r"phases/[0-9]{2,}-[a-z][a-z0-9-]*/iterations/"
    r"[0-9]{2,}-[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z][a-z0-9-]*/README\.md\Z"
)


@dataclass(frozen=True, slots=True)
class ParsedManifest:
    body: dict[str, object]
    specification: dict[str, object]
    invariants: tuple[dict[str, object], ...]
    phases: tuple[dict[str, object], ...]
    dependencies: tuple[dict[str, object], ...]
    iterations: tuple[dict[str, object], ...]


def _strip_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    for index, character in enumerate(line):
        if quote == '"':
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
        elif quote == "'":
            if character == quote:
                quote = None
        elif character in {'"', "'"}:
            quote = character
        elif character == "#":
            return line[:index]
    if quote is not None:
        # tomllib supplies the final typed error; do not guess multiline syntax.
        return line
    return line


def reject_raw_dotted_keys(body: str) -> None:
    if type(body) is not str:
        raise ManifestError("manifest body must be exact text")
    in_multiline: str | None = None
    for raw_line in body.splitlines():
        line = raw_line
        for marker in ('"""', "'''"):
            if in_multiline == marker:
                if marker in line:
                    in_multiline = None
                line = ""
                break
            if marker in line:
                before, _, _ = line.partition(marker)
                line = before
                in_multiline = marker
                break
        candidate = _strip_comment(line).strip()
        if not candidate:
            continue
        if candidate.startswith("["):
            end = candidate.find("]")
            if end < 0:
                continue
            header = candidate.lstrip("[").split("]", 1)[0].rstrip("]")
            if "." in _unquoted_text(header):
                raise ManifestError("raw dotted table keys are forbidden")
            continue
        if "=" in candidate:
            lhs = candidate.split("=", 1)[0].strip()
            if "." in _unquoted_text(lhs):
                raise ManifestError("raw dotted assignment keys are forbidden")


def _unquoted_text(value: str) -> str:
    result: list[str] = []
    quote: str | None = None
    escaped = False
    for character in value:
        if quote == '"':
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
        elif quote == "'":
            if character == quote:
                quote = None
        elif character in {'"', "'"}:
            quote = character
        else:
            result.append(character)
    return "".join(result)


def _exact_dict(value: object, name: str) -> dict[str, object]:
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise ManifestError(f"{name} must be an exact string-keyed object")
    return cast(dict[str, object], value)


def _object_tuple(value: object, name: str) -> tuple[dict[str, object], ...]:
    if type(value) is not list:
        raise ManifestError(f"{name} must be an exact array")
    return tuple(_exact_dict(item, name) for item in value)


def parse_manifest(
    body: str, validator: Draft202012Validator | None = None
) -> ParsedManifest:
    reject_raw_dotted_keys(body)
    try:
        parsed = tomllib.loads(body)
    except (tomllib.TOMLDecodeError, ValueError) as error:
        raise ManifestError("manifest TOML is malformed") from error
    root = _exact_dict(parsed, "manifest")
    if validator is not None:
        errors = tuple(validator.iter_errors(cast(Any, root)))
        if errors:
            raise ManifestError("manifest does not match the installed schema")
    required = {
        "aware",
        "specification",
        "invariants",
        "phases",
        "phase_dependencies",
        "iterations",
    }
    if set(root) != required or type(root["aware"]) is not int or root["aware"] != 1:
        raise ManifestError("manifest root is invalid")
    specification = _exact_dict(root["specification"], "specification")
    invariants = _object_tuple(root["invariants"], "invariants")
    phases = _object_tuple(root["phases"], "phases")
    dependencies = _object_tuple(root["phase_dependencies"], "phase_dependencies")
    iterations = _object_tuple(root["iterations"], "iterations")
    _validate_exact_shape(specification, invariants, phases, dependencies, iterations)
    _validate_semantic_joins(
        specification, invariants, phases, dependencies, iterations
    )
    return ParsedManifest(
        root, specification, invariants, phases, dependencies, iterations
    )


def _require_fields(
    value: dict[str, object], expected: frozenset[str], name: str
) -> None:
    if set(value) != expected:
        raise ManifestError(f"{name} fields are invalid")


def _positive_int(value: object, name: str, *, zero: bool = False) -> int:
    minimum = 0 if zero else 1
    if type(value) is not int or value < minimum:
        raise ManifestError(f"{name} must be an exact bounded integer")
    return value


def _nonempty_text(value: object, name: str, *, empty: bool = False) -> str:
    if type(value) is not str or (not empty and not value):
        raise ManifestError(f"{name} must be exact text")
    return value


def _validate_exact_shape(
    specification: dict[str, object],
    invariants: tuple[dict[str, object], ...],
    phases: tuple[dict[str, object], ...],
    dependencies: tuple[dict[str, object], ...],
    iterations: tuple[dict[str, object], ...],
) -> None:
    _require_fields(
        specification,
        frozenset(
            {
                "profile",
                "key",
                "semantic_version",
                "entrypoint",
                "invariant_index",
                "phase_index",
            }
        ),
        "specification",
    )
    for name in ("profile", "key", "entrypoint", "invariant_index", "phase_index"):
        _nonempty_text(specification[name], name)
    _positive_int(specification["semantic_version"], "semantic_version")
    if not invariants or not phases:
        raise ManifestError("canonical manifest requires invariants and phases")
    for invariant in invariants:
        _require_fields(
            invariant,
            frozenset({"key", "semantic_revision", "entrypoint"}),
            "invariant",
        )
        _nonempty_text(invariant["key"], "invariant key")
        _nonempty_text(invariant["entrypoint"], "invariant entrypoint")
        _positive_int(invariant["semantic_revision"], "semantic_revision")
    for phase in phases:
        _require_fields(
            phase,
            frozenset(
                {
                    "key",
                    "ordinal",
                    "entrypoint",
                    "gate_key",
                    "gate_contract",
                    "evidence_schema_ref",
                    "invariant_refs",
                }
            ),
            "phase",
        )
        for name in (
            "key",
            "entrypoint",
            "gate_key",
            "gate_contract",
            "evidence_schema_ref",
        ):
            _nonempty_text(phase[name], name)
        _positive_int(phase["ordinal"], "ordinal", zero=True)
        if type(phase["invariant_refs"]) is not list or any(
            type(item) is not str
            for item in cast(list[object], phase["invariant_refs"])
        ):
            raise ManifestError("invariant_refs must be an exact text array")
    for dependency in dependencies:
        _require_fields(
            dependency,
            frozenset(
                {
                    "key",
                    "owner_phase_ref",
                    "kind",
                    "required_phase_ref",
                    "required_gate_digest",
                    "rationale",
                }
            ),
            "phase dependency",
        )
        for name in dependency:
            _nonempty_text(dependency[name], name, empty=name == "rationale")
    for iteration in iterations:
        _require_fields(
            iteration,
            frozenset({"key", "phase_ref", "plan_revision", "entrypoint"}),
            "iteration",
        )
        for name in ("key", "phase_ref", "entrypoint"):
            _nonempty_text(iteration[name], name)
        _positive_int(iteration["plan_revision"], "plan_revision")


def _text(item: dict[str, object], name: str) -> str:
    value = item.get(name)
    if type(value) is not str:
        raise ManifestError(f"{name} must be exact text")
    return value


def _validate_semantic_joins(
    specification: dict[str, object],
    invariants: tuple[dict[str, object], ...],
    phases: tuple[dict[str, object], ...],
    dependencies: tuple[dict[str, object], ...],
    iterations: tuple[dict[str, object], ...],
) -> None:
    key = _text(specification, "key")
    if _text(specification, "profile") != "specification_fs_v1":
        raise ManifestError("manifest profile is foreign")
    if (
        _text(specification, "entrypoint") != "SPEC.md"
        or _text(specification, "invariant_index") != "invariants/README.md"
        or _text(specification, "phase_index") != "PHASES.md"
    ):
        raise ManifestError("manifest index entrypoints are invalid")

    invariant_keys = tuple(_text(item, "key") for item in invariants)
    phase_keys = tuple(_text(item, "key") for item in phases)
    if invariant_keys != tuple(sorted(set(invariant_keys))):
        raise ManifestError("invariants must be unique and sorted")
    if phase_keys != tuple(sorted(set(phase_keys))):
        raise ManifestError("phases must be unique and sorted")
    invariant_refs = {
        f"specification:{key}/invariant:{item}" for item in invariant_keys
    }
    phase_refs = {phase_ref(key, item) for item in phase_keys}

    entrypoints = ["SPEC.md", "invariants/README.md", "PHASES.md"]
    for item in invariants:
        entrypoint = _text(item, "entrypoint")
        if _INVARIANT_PATH.fullmatch(entrypoint) is None:
            raise ManifestError("invariant entrypoint is invalid")
        entrypoints.append(entrypoint)
    for item in phases:
        entrypoint = _text(item, "entrypoint")
        match = _PHASE_PATH.fullmatch(entrypoint)
        if (
            match is None
            or type(item.get("ordinal")) is not int
            or int(match.group(1)) != item["ordinal"]
        ):
            raise ManifestError("phase entrypoint and ordinal disagree")
        refs = item.get("invariant_refs")
        if type(refs) is not list or any(type(ref) is not str for ref in refs):
            raise ManifestError("phase invariant refs are invalid")
        if (
            tuple(refs) != tuple(sorted(set(cast(list[str], refs))))
            or not set(refs) <= invariant_refs
        ):
            raise ManifestError("phase invariant ownership is invalid")
        entrypoints.append(entrypoint)

    dependency_ids: list[tuple[str, str]] = []
    targets: dict[str, set[str]] = {}
    for item in dependencies:
        owner = _text(item, "owner_phase_ref")
        target = _text(item, "required_phase_ref")
        dep_key = _text(item, "key")
        if owner not in phase_refs:
            raise ManifestError("dependency owner must be package-local")
        dependency_ids.append((owner, dep_key))
        if target in targets.setdefault(owner, set()):
            raise ManifestError("dependency target is duplicated")
        targets[owner].add(target)
    if dependency_ids != sorted(set(dependency_ids)):
        raise ManifestError("dependencies must be canonically ordered")

    iteration_ids: list[tuple[str, str]] = []
    for item in iterations:
        owner = _text(item, "phase_ref")
        entrypoint = _text(item, "entrypoint")
        if owner not in phase_refs or _ITERATION_PATH.fullmatch(entrypoint) is None:
            raise ManifestError("iteration ownership or entrypoint is invalid")
        owner_key = owner.rsplit(":", 1)[1]
        owner_path = next(
            _text(phase, "entrypoint")
            for phase in phases
            if _text(phase, "key") == owner_key
        )
        if not entrypoint.startswith(
            owner_path.removesuffix("README.md") + "iterations/"
        ):
            raise ManifestError("iteration is outside its owner phase")
        iteration_ids.append((owner, _text(item, "key")))
        entrypoints.append(entrypoint)
    if iteration_ids != sorted(set(iteration_ids)):
        raise ManifestError("iterations must be canonically ordered")
    if len(entrypoints) != len(set(entrypoints)):
        raise ManifestError("semantic entrypoint is duplicated")


def manifest_entrypoints(value: ParsedManifest) -> dict[str, str]:
    result = {
        "SPEC.md": "specification",
        "invariants/README.md": "invariant_index",
        "PHASES.md": "phase_index",
    }
    result.update({_text(item, "entrypoint"): "invariant" for item in value.invariants})
    result.update({_text(item, "entrypoint"): "phase" for item in value.phases})
    result.update({_text(item, "entrypoint"): "iteration" for item in value.iterations})
    return result
