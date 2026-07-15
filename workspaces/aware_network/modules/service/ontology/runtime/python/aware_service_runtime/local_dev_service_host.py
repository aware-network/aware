from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

LOCAL_SERVICEHOST_BOOT_SOURCE_NONE = "none"
LOCAL_SERVICEHOST_BOOT_SOURCE_ARTIFACT_BOOTSTRAP = "artifact_bootstrap"
LOCAL_SERVICEHOST_BOOT_SOURCE_LOCAL_DEV_IMPLEMENTATION_TOML = (
    "local_dev_implementation_toml"
)


@dataclass(frozen=True, slots=True)
class LocalServiceHostBootDecision:
    service_name: str
    allowed: bool
    source: str
    production_safe: bool
    reason: str
    error: str | None
    bootstrap_config_path: Path | None
    implementation_toml_paths: tuple[Path, ...]

    def to_evidence(self) -> dict[str, object]:
        return {
            "service_name": self.service_name,
            "allowed": self.allowed,
            "source": self.source,
            "production_safe": self.production_safe,
            "reason": self.reason,
            "error": self.error,
            "bootstrap_config_path": (
                self.bootstrap_config_path.as_posix()
                if self.bootstrap_config_path is not None
                else None
            ),
            "implementation_toml_paths": [
                path.as_posix() for path in self.implementation_toml_paths
            ],
        }


def evaluate_local_servicehost_boot_policy(
    *,
    service_name: str,
    bootstrap_config_path: str | Path | None = None,
    implementation_toml_paths: Sequence[str | Path] = (),
    allow_dev_implementation_boot: bool = False,
) -> LocalServiceHostBootDecision:
    """Evaluate whether an SDK/dev surface may start a local ServiceHost."""

    resolved_service_name = service_name.strip() or "local-servicehost"
    resolved_bootstrap_config_path = _optional_path(bootstrap_config_path)
    resolved_implementation_toml_paths = tuple(
        path
        for path in (_optional_path(value) for value in implementation_toml_paths)
        if path is not None
    )

    if resolved_bootstrap_config_path is not None:
        return LocalServiceHostBootDecision(
            service_name=resolved_service_name,
            allowed=True,
            source=LOCAL_SERVICEHOST_BOOT_SOURCE_ARTIFACT_BOOTSTRAP,
            production_safe=True,
            reason="prepared artifact-first ServiceHost bootstrap config",
            error=None,
            bootstrap_config_path=resolved_bootstrap_config_path,
            implementation_toml_paths=resolved_implementation_toml_paths,
        )

    if resolved_implementation_toml_paths and allow_dev_implementation_boot:
        return LocalServiceHostBootDecision(
            service_name=resolved_service_name,
            allowed=True,
            source=LOCAL_SERVICEHOST_BOOT_SOURCE_LOCAL_DEV_IMPLEMENTATION_TOML,
            production_safe=False,
            reason="explicit local-dev implementation TOML boot opt-in",
            error=None,
            bootstrap_config_path=None,
            implementation_toml_paths=resolved_implementation_toml_paths,
        )

    if resolved_implementation_toml_paths:
        error = (
            "Local ServiceHost boot from implementation TOMLs is dev-only and "
            "requires explicit local-dev boot opt-in."
        )
        source = LOCAL_SERVICEHOST_BOOT_SOURCE_LOCAL_DEV_IMPLEMENTATION_TOML
    else:
        error = (
            "Local ServiceHost boot requires a prepared artifact-first ServiceHost "
            "bootstrap config or explicit local-dev implementation TOMLs. SDK "
            "import and client construction must not start services."
        )
        source = LOCAL_SERVICEHOST_BOOT_SOURCE_NONE

    return LocalServiceHostBootDecision(
        service_name=resolved_service_name,
        allowed=False,
        source=source,
        production_safe=True,
        reason="production SDK no-boot default",
        error=error,
        bootstrap_config_path=None,
        implementation_toml_paths=resolved_implementation_toml_paths,
    )


def _optional_path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    return Path(raw).expanduser()


__all__ = [
    "LOCAL_SERVICEHOST_BOOT_SOURCE_ARTIFACT_BOOTSTRAP",
    "LOCAL_SERVICEHOST_BOOT_SOURCE_LOCAL_DEV_IMPLEMENTATION_TOML",
    "LOCAL_SERVICEHOST_BOOT_SOURCE_NONE",
    "LocalServiceHostBootDecision",
    "evaluate_local_servicehost_boot_policy",
]
