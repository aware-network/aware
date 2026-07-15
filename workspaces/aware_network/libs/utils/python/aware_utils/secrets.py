"""Secret resolution helpers for Aware runtime libraries.

Goals:
- Prefer process environment variables.
- Support file-based secret mounts (e.g. Kubernetes secrets as files).
- Support `.env` files for local development without overriding env.
- Provide diagnostics about which resolvers were attempted.

This module never logs secret values.
"""

from __future__ import annotations

import os
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Protocol


@dataclass(frozen=True)
class SecretSpec:
    name: str
    description: str = ""
    scopes: tuple[str, ...] = ()


class SecretResolver(Protocol):
    def resolve(self, spec: SecretSpec) -> Optional[str]:  # pragma: no cover - interface
        ...

    def describe(self) -> dict[str, object]:  # pragma: no cover - optional hook
        return {}


@dataclass(frozen=True)
class SecretAttempt:
    resolver: str
    source: str
    success: bool
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SecretResolutionInfo:
    name: str
    value: Optional[str]
    resolver: Optional[str]
    source: Optional[str]
    details: dict[str, object]
    attempts: List[SecretAttempt]


@dataclass
class _RegisteredResolver:
    priority: int
    resolver: SecretResolver
    name: str
    source: str
    details: dict[str, object]


_secret_specs: dict[str, SecretSpec] = {}
_resolvers: List[_RegisteredResolver] = []


def register_secret(spec: SecretSpec) -> None:
    _secret_specs.setdefault(spec.name, spec)


def register_resolver(
    resolver: SecretResolver,
    priority: int = 0,
    *,
    name: Optional[str] = None,
    source: Optional[str] = None,
    details: Optional[dict[str, object]] = None,
) -> None:
    entry = _RegisteredResolver(
        priority=priority,
        resolver=resolver,
        name=name or resolver.__class__.__name__,
        source=source or (name or resolver.__class__.__name__),
        details=dict(details or {}),
    )
    _resolvers.append(entry)
    _resolvers.sort(key=lambda item: item.priority, reverse=True)


class EnvResolver:
    """Resolve secrets from process environment variables."""

    def resolve(self, spec: SecretSpec) -> Optional[str]:
        value = os.getenv(spec.name)
        return value if value else None

    def describe(self) -> dict[str, object]:
        return {"type": "env"}


register_resolver(EnvResolver(), priority=0, name="env", source="env")


class _DotEnvResolver:
    """Minimal `.env` loader.

    - Supports `export KEY=value`
    - Uses shlex to parse quoted values
    - Never overrides values already present in `os.environ`
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self._loaded = False
        self._warnings: List[str] = []
        self._values: Dict[str, str] = {}

    def resolve(self, spec: SecretSpec) -> Optional[str]:
        self._ensure_loaded()
        value = os.getenv(spec.name)
        if value:
            return value
        value = self._values.get(spec.name)
        if value and spec.name not in os.environ:
            os.environ[spec.name] = value
        return value if value else None

    def describe(self) -> dict[str, object]:
        return {
            "type": "dotenv",
            "path": str(self.path),
            "exists": self.path.exists(),
            "loaded": self._loaded,
            "warnings": list(self._warnings),
        }

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not self.path.exists():
            return
        try:
            content = self.path.read_text(encoding="utf-8")
        except OSError as exc:  # pragma: no cover
            self._warnings.append(f"read-error: {exc}")
            return

        for idx, line in enumerate(content.splitlines(), start=1):
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue
            if raw.lower().startswith("export "):
                raw = raw[6:].strip()
            if "=" not in raw:
                self._warnings.append(f"line {idx}: missing '='")
                continue
            key, value_part = raw.split("=", 1)
            key = key.strip()
            if not key:
                self._warnings.append(f"line {idx}: empty key")
                continue
            try:
                tokens = shlex.split(value_part, posix=True, comments=True)
            except ValueError as exc:  # pragma: no cover
                self._warnings.append(f"line {idx}: {exc}")
                continue
            value = " ".join(tokens)
            if key in self._values:
                self._warnings.append(f"line {idx}: duplicate key '{key}' (overriding previous value)")
            self._values[key] = value
            if key not in os.environ:
                os.environ[key] = value


def use_dotenv(path: str | Path, *, priority: int = -10) -> None:
    resolved = str(Path(path))
    name = f"dotenv:{resolved}"
    if any(entry.name == name for entry in _resolvers):
        return
    resolver = _DotEnvResolver(Path(path))
    register_resolver(
        resolver,
        priority=priority,
        name=name,
        source="dotenv",
        details={"path": resolved},
    )
    # Eagerly load so non-secret config keys (e.g., endpoints) become available via `os.getenv`.
    resolver._ensure_loaded()


class SecretsDirResolver:
    """Resolve secrets from individual files in a directory.

    Example: if `path=/run/secrets` and secret name is `OPENAI_API_KEY`,
    resolve from `/run/secrets/OPENAI_API_KEY`.
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def resolve(self, spec: SecretSpec) -> Optional[str]:
        if not self.path.exists() or not self.path.is_dir():
            return None

        candidate = self.path / spec.name
        if not candidate.exists() or not candidate.is_file():
            return None
        try:
            value = candidate.read_text(encoding="utf-8")
        except OSError:  # pragma: no cover
            return None

        value = value.strip()
        if not value:
            return None

        if spec.name not in os.environ:
            os.environ[spec.name] = value
        return value

    def describe(self) -> dict[str, object]:
        return {
            "type": "secrets_dir",
            "path": str(self.path),
            "exists": self.path.exists(),
            "is_dir": self.path.is_dir(),
        }


def use_secrets_dir(path: str | Path, *, priority: int = -5) -> None:
    resolved = str(Path(path))
    name = f"secrets_dir:{resolved}"
    if any(entry.name == name for entry in _resolvers):
        return
    resolver = SecretsDirResolver(Path(path))
    register_resolver(
        resolver,
        priority=priority,
        name=name,
        source="secrets_dir",
        details={"path": resolved},
    )


def resolve_secret(name: str) -> Optional[str]:
    info = resolve_secret_info(name)
    return info.value


def resolve_secret_info(name: str) -> SecretResolutionInfo:
    spec = _secret_specs.get(name, SecretSpec(name=name))
    attempts: List[SecretAttempt] = []

    for entry in _resolvers:
        details = dict(entry.details)
        describe = getattr(entry.resolver, "describe", None)

        value = entry.resolver.resolve(spec)

        if callable(describe):
            try:
                extra = describe()
            except Exception:  # pragma: no cover
                extra = {}
            if isinstance(extra, dict):
                details.update(extra)

        success = bool(value)
        attempt = SecretAttempt(
            resolver=entry.name,
            source=entry.source,
            success=success,
            details=details,
        )
        attempts.append(attempt)
        if success:
            return SecretResolutionInfo(
                name=spec.name,
                value=value,
                resolver=entry.name,
                source=entry.source,
                details=details,
                attempts=attempts,
            )

    return SecretResolutionInfo(
        name=spec.name,
        value=None,
        resolver=None,
        source=None,
        details={},
        attempts=attempts,
    )


def require_secret(name: str) -> str:
    info = resolve_secret_info(name)
    if info.value:
        return info.value

    attempted = ", ".join(attempt.resolver for attempt in info.attempts if attempt.resolver)
    suffix = f" Tried resolvers: {attempted}." if attempted else ""
    raise KeyError(f"Missing required secret: {name}.{suffix}")


def list_secrets() -> List[SecretSpec]:
    return list(_secret_specs.values())


def describe_secret(name: str) -> dict[str, object]:
    spec = _secret_specs.get(name, SecretSpec(name=name))
    info = resolve_secret_info(name)
    return {
        "name": spec.name,
        "description": spec.description,
        "scopes": list(spec.scopes),
        "present": info.value is not None,
        "resolver": info.resolver,
        "source": info.source,
        "details": info.details,
        "attempts": [
            {
                "resolver": attempt.resolver,
                "source": attempt.source,
                "success": attempt.success,
                "details": attempt.details,
            }
            for attempt in info.attempts
        ],
    }


def reset_secrets_state_for_tests() -> None:
    """Reset the in-process registry (tests only)."""

    _secret_specs.clear()
    _resolvers.clear()
    register_resolver(EnvResolver(), priority=0, name="env", source="env")


__all__ = [
    "SecretAttempt",
    "SecretResolutionInfo",
    "SecretResolver",
    "SecretSpec",
    "describe_secret",
    "list_secrets",
    "register_resolver",
    "register_secret",
    "require_secret",
    "resolve_secret",
    "resolve_secret_info",
    "reset_secrets_state_for_tests",
    "use_dotenv",
    "use_secrets_dir",
]
