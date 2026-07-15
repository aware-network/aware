from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import NotRequired, TypedDict

_ERROR_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*){2,}$")


class ErrorCategory(StrEnum):
    runtime_invariant = "runtime_invariant"
    internal_failure = "internal_failure"


class ErrorSeverity(StrEnum):
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class ResolutionStatus(StrEnum):
    unresolved = "unresolved"
    partial = "partial"
    resolved = "resolved"


class ErrorCodeDefinition(TypedDict):
    code: str
    category: ErrorCategory
    default_severity: ErrorSeverity
    title: str
    description: str
    owner_package: str
    docs_ref: NotRequired[str | None]
    introduced_at: NotRequired[str | None]
    deprecated: NotRequired[bool]
    replacement_code: NotRequired[str | None]


@dataclass(frozen=True, slots=True)
class RegisteredErrorCodeDefinition:
    code: str
    category: ErrorCategory
    default_severity: ErrorSeverity
    title: str
    description: str
    owner_package: str
    docs_ref: str | None = None
    introduced_at: str | None = None
    deprecated: bool = False
    replacement_code: str | None = None


class ErrorCodeRegistry:
    def __init__(
        self,
        *,
        definitions: Iterable[
            Mapping[str, object] | RegisteredErrorCodeDefinition
        ] = (),
    ) -> None:
        self.definitions = tuple(
            _coerce_definition(definition) for definition in definitions
        )
        self._validate_definitions()

    def _validate_definitions(self) -> None:
        seen: set[str] = set()
        known_codes = {definition.code for definition in self.definitions}
        for definition in self.definitions:
            if definition.code in seen:
                raise ValueError(f"Duplicate runtime error code: {definition.code}")
            seen.add(definition.code)
            if (
                definition.replacement_code is not None
                and definition.replacement_code not in known_codes
            ):
                raise ValueError(
                    f"replacement_code for {definition.code} must reference another registered code"
                )

    def definition_for(self, code: str) -> RegisteredErrorCodeDefinition:
        normalized = _validate_error_code(code)
        for definition in self.definitions:
            if definition.code == normalized:
                return definition
        raise ValueError(f"Unknown runtime error code: {normalized}")

    def validate_diagnostic(
        self,
        *,
        code: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
    ) -> RegisteredErrorCodeDefinition:
        definition = self.definition_for(code)
        if definition.category != category:
            raise ValueError(
                f"Runtime diagnostic category mismatch for {definition.code}: "
                f"expected {definition.category.value}, got {category.value}"
            )
        if definition.default_severity != severity:
            raise ValueError(
                f"Runtime diagnostic severity mismatch for {definition.code}: "
                f"expected {definition.default_severity.value}, got {severity.value}"
            )
        return definition


def _coerce_definition(
    definition: Mapping[str, object] | RegisteredErrorCodeDefinition,
) -> RegisteredErrorCodeDefinition:
    if isinstance(definition, RegisteredErrorCodeDefinition):
        return definition
    code = _required_text(definition, "code")
    replacement_code = _optional_text(definition.get("replacement_code"))
    deprecated = bool(definition.get("deprecated", False))
    if replacement_code is not None and not deprecated:
        raise ValueError("replacement_code requires deprecated=True")
    if replacement_code == code:
        raise ValueError("replacement_code must differ from code")
    return RegisteredErrorCodeDefinition(
        code=_validate_error_code(code),
        category=ErrorCategory(str(definition["category"])),
        default_severity=ErrorSeverity(str(definition["default_severity"])),
        title=_required_text(definition, "title"),
        description=_required_text(definition, "description"),
        owner_package=_required_text(definition, "owner_package"),
        docs_ref=_optional_text(definition.get("docs_ref")),
        introduced_at=_optional_text(definition.get("introduced_at")),
        deprecated=deprecated,
        replacement_code=replacement_code,
    )


def _validate_error_code(value: str) -> str:
    normalized = value.strip()
    if not _ERROR_CODE_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Error codes must use dotted lowercase namespaces like "
            "'service.temporal_mutation.missing_session_id'"
        )
    return normalized


def _required_text(definition: Mapping[str, object], key: str) -> str:
    value = definition.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Error code definition requires {key}.")
    return value.strip()


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"Expected text value or None, got {type(value).__name__}.")
    stripped = value.strip()
    return stripped or None


__all__ = [
    "ErrorCategory",
    "ErrorCodeDefinition",
    "ErrorCodeRegistry",
    "ErrorSeverity",
    "RegisteredErrorCodeDefinition",
    "ResolutionStatus",
]
