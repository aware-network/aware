from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from aware_experience.compiler.models import (
    ExperienceActuatorConfigOwnership,
    ExperienceConnectorConfigOwnership,
    ExperienceConnectorInvocationActionConfigOwnership,
    ExperienceConnectorInvocationRequestFieldOwnership,
    ExperienceConnectorProviderOwnership,
    ExperienceSensorConfigOwnership,
)
from aware_experience.compiler.workspace import ExperienceWorkspace

_IDENT = r"[A-Za-z_][A-Za-z0-9_]*"
_QUALIFIED = r"[A-Za-z_][A-Za-z0-9_\.]*"
_CONNECTOR_HEADER_RE = re.compile(rf"\bconnector\s+({_IDENT})\s*\{{", re.DOTALL)
_CHILD_HEADER_BY_KEYWORD: dict[str, re.Pattern[str]] = {
    keyword: re.compile(rf"\b{keyword}\s+({_IDENT})\s*\{{", re.DOTALL)
    for keyword in ("provider", "sensor", "actuator")
}
_INVOCATION_RE = re.compile(
    rf"\binvocation\s+({_IDENT})\s+(api|sdk|service)\s+({_QUALIFIED})\s*",
    re.DOTALL,
)
_REQUEST_FIELD_RE = re.compile(
    rf"\brequest_field\s+({_IDENT})\s+from\s+({_QUALIFIED})\s*;?",
    re.DOTALL,
)
_FIELD_VALUE_RE = r"(\"[^\"]*\"|'[^']*'|[A-Za-z_][A-Za-z0-9_:\.]*)"


def load_connector_ownership_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    package_name: str | None = None,
    fqn_prefix: str | None = None,
    is_dependency: bool = False,
) -> tuple[ExperienceConnectorConfigOwnership, ...]:
    connectors_by_key: dict[str, ExperienceConnectorConfigOwnership] = {}

    for relpath in source_files:
        rel = relpath.as_posix()
        if not _is_connector_source_path(rel):
            continue
        source_path = (package_root / relpath).resolve()
        _assert_within(
            base=package_root, candidate=source_path, label="connector source"
        )
        text = source_path.read_text(encoding="utf-8")
        source_rel = relpath.as_posix()

        for connector_key, body in _iter_connector_blocks(source_text=text):
            connector_key_folded = connector_key.casefold()
            if connector_key_folded in connectors_by_key:
                raise ValueError(
                    f"Duplicate connector key {connector_key!r} across experience sources"
                )
            connectors_by_key[connector_key_folded] = _parse_connector_ownership(
                connector_key=connector_key,
                body=body,
                source_path=source_rel,
                package_name=_normalize_optional_token(package_name),
                fqn_prefix=_normalize_optional_token(fqn_prefix),
                is_dependency=is_dependency,
            )

    return tuple(
        sorted(
            connectors_by_key.values(),
            key=lambda item: (item.connector_key.casefold(), item.source_path),
        )
    )


def load_dependency_connector_ownership_from_snapshot(
    *,
    snapshot: Any,
) -> tuple[ExperienceConnectorConfigOwnership, ...]:
    connectors: list[ExperienceConnectorConfigOwnership] = []
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
        connectors.extend(
            load_connector_ownership_from_sources(
                package_root=dependency_snapshot.package_root,
                source_files=dependency_snapshot.source_files,
                package_name=dependency_package_name,
                fqn_prefix=dependency_fqn_prefix,
                is_dependency=True,
            )
        )
    connectors.sort(
        key=lambda item: (
            item.package_name or "",
            item.connector_key.casefold(),
            item.source_path,
        )
    )
    return tuple(connectors)


def _parse_connector_ownership(
    *,
    connector_key: str,
    body: str,
    source_path: str,
    package_name: str | None,
    fqn_prefix: str | None,
    is_dependency: bool,
) -> ExperienceConnectorConfigOwnership:
    root_body = _strip_child_blocks(
        body=body, keywords=("provider", "sensor", "actuator")
    )
    connector_kind = _required_field(
        body=root_body,
        field_name="kind",
        context=f"connector {connector_key!r}",
    )

    providers = _parse_provider_ownership(body=body, source_path=source_path)
    sensors = _parse_sensor_ownership(body=body, source_path=source_path)
    actuators = _parse_actuator_ownership(body=body, source_path=source_path)
    return ExperienceConnectorConfigOwnership(
        connector_key=connector_key,
        connector_kind=connector_kind,
        source_path=source_path,
        label=_optional_field(body=root_body, field_name="label"),
        description=_optional_field(body=root_body, field_name="description"),
        providers=providers,
        sensor_configs=sensors,
        actuator_configs=actuators,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        is_dependency=is_dependency,
    )


def _parse_provider_ownership(
    *,
    body: str,
    source_path: str,
) -> tuple[ExperienceConnectorProviderOwnership, ...]:
    providers_by_key: dict[str, ExperienceConnectorProviderOwnership] = {}
    for provider_key, provider_body in _iter_child_blocks(
        body=body, keyword="provider"
    ):
        key = provider_key.casefold()
        if key in providers_by_key:
            raise ValueError(f"Duplicate connector provider key {provider_key!r}")
        providers_by_key[key] = ExperienceConnectorProviderOwnership(
            provider_key=provider_key,
            provider_kind=_required_field(
                body=provider_body,
                field_name="kind",
                context=f"provider {provider_key!r}",
            ),
            source_path=source_path,
            provider_ref=_optional_field(body=provider_body, field_name="ref"),
            label=_optional_field(body=provider_body, field_name="label"),
            description=_optional_field(body=provider_body, field_name="description"),
        )
    return tuple(
        sorted(providers_by_key.values(), key=lambda item: item.provider_key.casefold())
    )


def _parse_sensor_ownership(
    *,
    body: str,
    source_path: str,
) -> tuple[ExperienceSensorConfigOwnership, ...]:
    sensors_by_key: dict[str, ExperienceSensorConfigOwnership] = {}
    for sensor_key, sensor_body in _iter_child_blocks(body=body, keyword="sensor"):
        key = sensor_key.casefold()
        if key in sensors_by_key:
            raise ValueError(f"Duplicate connector sensor key {sensor_key!r}")
        config_body = _strip_invocation_blocks(body=sensor_body)
        _forbid_field(
            body=config_body,
            field_name="payload_schema_ref",
            context=f"sensor {sensor_key!r}",
        )
        sensors_by_key[key] = ExperienceSensorConfigOwnership(
            sensor_key=sensor_key,
            sensor_kind=_required_field(
                body=config_body,
                field_name="kind",
                context=f"sensor {sensor_key!r}",
            ),
            source_path=source_path,
            source_ref=_optional_field(body=config_body, field_name="source_ref"),
            observed_state_node_refs=_repeated_field(
                body=config_body,
                field_name="observed_state_node",
                context=f"sensor {sensor_key!r}",
            ),
            label=_optional_field(body=config_body, field_name="label"),
            description=_optional_field(config_body, field_name="description"),
            invocation_action_configs=_parse_invocation_ownership(
                body=sensor_body,
                source_path=source_path,
                context=f"sensor {sensor_key!r}",
            ),
        )
    return tuple(
        sorted(sensors_by_key.values(), key=lambda item: item.sensor_key.casefold())
    )


def _parse_actuator_ownership(
    *,
    body: str,
    source_path: str,
) -> tuple[ExperienceActuatorConfigOwnership, ...]:
    actuators_by_key: dict[str, ExperienceActuatorConfigOwnership] = {}
    for actuator_key, actuator_body in _iter_child_blocks(
        body=body, keyword="actuator"
    ):
        key = actuator_key.casefold()
        if key in actuators_by_key:
            raise ValueError(f"Duplicate connector actuator key {actuator_key!r}")
        config_body = _strip_invocation_blocks(body=actuator_body)
        _forbid_field(
            body=config_body,
            field_name="payload_schema_ref",
            context=f"actuator {actuator_key!r}",
        )
        actuators_by_key[key] = ExperienceActuatorConfigOwnership(
            actuator_key=actuator_key,
            actuator_kind=_required_field(
                body=config_body,
                field_name="kind",
                context=f"actuator {actuator_key!r}",
            ),
            source_path=source_path,
            target_ref=_optional_field(body=config_body, field_name="target_ref"),
            affected_state_node_refs=_repeated_field(
                body=config_body,
                field_name="affected_state_node",
                context=f"actuator {actuator_key!r}",
            ),
            label=_optional_field(body=config_body, field_name="label"),
            description=_optional_field(config_body, field_name="description"),
            invocation_action_configs=_parse_invocation_ownership(
                body=actuator_body,
                source_path=source_path,
                context=f"actuator {actuator_key!r}",
            ),
        )
    return tuple(
        sorted(actuators_by_key.values(), key=lambda item: item.actuator_key.casefold())
    )


def _parse_invocation_ownership(
    *,
    body: str,
    source_path: str,
    context: str,
) -> tuple[ExperienceConnectorInvocationActionConfigOwnership, ...]:
    invocations_by_key: dict[
        str, ExperienceConnectorInvocationActionConfigOwnership
    ] = {}
    cursor = 0
    while True:
        match = _INVOCATION_RE.search(body, cursor)
        if match is None:
            break
        action_key = (match.group(1) or "").strip()
        action_kind = (match.group(2) or "").strip()
        target_ref = (match.group(3) or "").strip()
        body_start = match.end()
        block = ""
        if body_start < len(body) and body[body_start] == "{":
            body_end = _find_matching_brace(source_text=body, start=body_start)
            block = body[body_start + 1 : body_end]
            cursor = body_end + 1
        else:
            cursor = body_start + 1

        key = action_key.casefold()
        if key in invocations_by_key:
            raise ValueError(
                f"Duplicate invocation action key {action_key!r} in {context}"
            )
        invocations_by_key[key] = ExperienceConnectorInvocationActionConfigOwnership(
            action_key=action_key,
            action_kind=action_kind,
            target_ref=target_ref,
            source_path=source_path,
            label=_optional_field(body=block, field_name="label"),
            receipt_policy=_optional_field(body=block, field_name="receipt"),
            confirmation_policy=_optional_field(body=block, field_name="confirmation"),
            optimistic_policy=_optional_field(body=block, field_name="optimistic"),
            request_fields=_parse_request_field_ownership(
                body=block,
                context=f"{context} invocation {action_key!r}",
            ),
        )
    return tuple(
        sorted(invocations_by_key.values(), key=lambda item: item.action_key.casefold())
    )


def _parse_request_field_ownership(
    *,
    body: str,
    context: str,
) -> tuple[ExperienceConnectorInvocationRequestFieldOwnership, ...]:
    request_fields: list[ExperienceConnectorInvocationRequestFieldOwnership] = []
    seen: set[str] = set()
    for match in _REQUEST_FIELD_RE.finditer(body):
        attribute = (match.group(1) or "").strip()
        source_ref = (match.group(2) or "").strip()
        key = attribute.casefold()
        if key in seen:
            raise ValueError(
                f"Duplicate request_field attribute {attribute!r} in {context}"
            )
        seen.add(key)
        request_fields.append(
            ExperienceConnectorInvocationRequestFieldOwnership(
                attribute=attribute,
                source_ref=source_ref,
                required=True,
            )
        )
    return tuple(request_fields)


def _iter_connector_blocks(*, source_text: str) -> tuple[tuple[str, str], ...]:
    rows: list[tuple[str, str]] = []
    cursor = 0
    while True:
        match = _CONNECTOR_HEADER_RE.search(source_text, cursor)
        if match is None:
            break
        connector_key = (match.group(1) or "").strip()
        body_start = match.end()
        body_end = _find_matching_brace(source_text=source_text, start=body_start - 1)
        rows.append((connector_key, source_text[body_start:body_end]))
        cursor = body_end + 1
    return tuple(rows)


def _iter_child_blocks(*, body: str, keyword: str) -> tuple[tuple[str, str], ...]:
    pattern = _CHILD_HEADER_BY_KEYWORD[keyword]
    rows: list[tuple[str, str]] = []
    cursor = 0
    while True:
        match = pattern.search(body, cursor)
        if match is None:
            break
        key = (match.group(1) or "").strip()
        body_start = match.end()
        body_end = _find_matching_brace(source_text=body, start=body_start - 1)
        rows.append((key, body[body_start:body_end]))
        cursor = body_end + 1
    return tuple(rows)


def _strip_child_blocks(*, body: str, keywords: tuple[str, ...]) -> str:
    stripped = body
    for keyword in keywords:
        pattern = _CHILD_HEADER_BY_KEYWORD[keyword]
        stripped = _replace_block_matches(body=stripped, pattern=pattern)
    return stripped


def _strip_invocation_blocks(*, body: str) -> str:
    return _replace_block_matches(body=body, pattern=_INVOCATION_RE)


def _replace_block_matches(*, body: str, pattern: re.Pattern[str]) -> str:
    chars = list(body)
    cursor = 0
    while True:
        match = pattern.search(body, cursor)
        if match is None:
            break
        start = match.start()
        block_start = match.end()
        end = block_start
        if block_start < len(body) and body[block_start] == "{":
            end = _find_matching_brace(source_text=body, start=block_start) + 1
        else:
            while end < len(body) and body[end] != "\n":
                end += 1
        for idx in range(start, end):
            chars[idx] = " "
        cursor = end
    return "".join(chars)


def _required_field(*, body: str, field_name: str, context: str) -> str:
    value = _optional_field(body=body, field_name=field_name)
    if value is None:
        raise ValueError(f"Missing {field_name!r} in {context}")
    return value


def _optional_field(body: str, *, field_name: str) -> str | None:
    pattern = re.compile(rf"\b{field_name}\s+{_FIELD_VALUE_RE}\s*;?", re.DOTALL)
    match = pattern.search(body)
    if match is None:
        return None
    return _clean_value(match.group(1))


def _repeated_field(*, body: str, field_name: str, context: str) -> tuple[str, ...]:
    pattern = re.compile(rf"\b{field_name}\s+{_FIELD_VALUE_RE}\s*;?", re.DOTALL)
    values: list[str] = []
    seen: set[str] = set()
    for match in pattern.finditer(body):
        value = _clean_value(match.group(1))
        value_key = value.casefold()
        if value_key in seen:
            raise ValueError(f"Duplicate {field_name!r} value {value!r} in {context}")
        seen.add(value_key)
        values.append(value)
    return tuple(values)


def _forbid_field(*, body: str, field_name: str, context: str) -> None:
    if _optional_field(body=body, field_name=field_name) is not None:
        raise ValueError(
            f"{field_name!r} is deprecated in {context}; use projection-node "
            "footprint fields instead"
        )


def _clean_value(value: str) -> str:
    token = (value or "").strip()
    if (token.startswith('"') and token.endswith('"')) or (
        token.startswith("'") and token.endswith("'")
    ):
        return token[1:-1]
    return token


def _find_matching_brace(*, source_text: str, start: int) -> int:
    if start < 0 or start >= len(source_text) or source_text[start] != "{":
        raise ValueError(
            "Invalid connector block start while parsing connector declarations"
        )

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

    raise ValueError("Unclosed connector block while parsing connector declarations")


def _normalize_optional_token(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    token = raw.strip()
    return token or None


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


def _is_connector_source_path(path: str) -> bool:
    rel = (path or "").strip()
    if not rel:
        return False
    if "/connectors/" in f"/{rel}" or rel.startswith("connectors/"):
        return True
    return Path(rel).name in {"connector.aware", "connectors.aware"}


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if (
        candidate_resolved == base_resolved
        or base_resolved in candidate_resolved.parents
    ):
        return
    raise ValueError(
        f"{label} resolved outside package boundary: "
        f"base={base_resolved} candidate={candidate_resolved}"
    )


__all__ = [
    "load_dependency_connector_ownership_from_snapshot",
    "load_connector_ownership_from_sources",
]
