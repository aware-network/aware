from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib
from typing import Any


class KernelSeedSpecError(ValueError):
    pass


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise KernelSeedSpecError(f"Seed spec missing required string: {key}")
    return value.strip()


def _optional_str(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise KernelSeedSpecError(f"Seed spec field must be a string: {key}")
    stripped = value.strip()
    return stripped or None


@dataclass(frozen=True, slots=True)
class SeedMeta:
    seed_id: str
    version: int
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class KernelConfig:
    environment_config_id: str | None = None


@dataclass(frozen=True, slots=True)
class SystemSpec:
    key_label: str
    public_key: str


@dataclass(frozen=True, slots=True)
class OrganizationSpec:
    key_label: str
    public_key: str


@dataclass(frozen=True, slots=True)
class ExecutorSpec:
    key_label: str
    public_key: str
    role: str = "member"


@dataclass(frozen=True, slots=True)
class EconomySpec:
    smart_contract_config_name: str = "AwareMembership"
    smart_contract_type: str = "utility"
    smart_contract_address: str = "dev:membership"


@dataclass(frozen=True, slots=True)
class ServiceSpec:
    service_config_name: str = "Aware Catalog"
    inference_service_name: str = "Aware Inference"


@dataclass(frozen=True, slots=True)
class KernelSeedSpec:
    aware: int
    meta: SeedMeta
    kernel: KernelConfig
    system: SystemSpec
    organization: OrganizationSpec
    executors: tuple[ExecutorSpec, ...]
    service: ServiceSpec
    economy: EconomySpec

    @staticmethod
    def load(path: Path) -> "KernelSeedSpec":
        path = Path(path).expanduser()
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise KernelSeedSpecError(f"Seed spec root must be a TOML table: {path}")

        aware = raw.get("aware")
        if aware != 1:
            raise KernelSeedSpecError(f"Seed spec must set aware = 1: {path}")

        seed_table = raw.get("seed")
        if not isinstance(seed_table, dict):
            raise KernelSeedSpecError("Seed spec missing [seed] table")
        seed_id = _require_str(seed_table, "id")
        version = seed_table.get("version")
        if not isinstance(version, int) or version < 1:
            raise KernelSeedSpecError("Seed spec [seed].version must be an int >= 1")
        title = _optional_str(seed_table, "title")
        description = _optional_str(seed_table, "description")

        kernel_table = raw.get("kernel")
        if not isinstance(kernel_table, dict):
            kernel_table = {}
        kernel = KernelConfig(
            environment_config_id=_optional_str(kernel_table, "environment_config_id")
        )

        system_table = raw.get("system")
        if not isinstance(system_table, dict):
            raise KernelSeedSpecError("Seed spec missing [system] table")
        system = SystemSpec(
            key_label=_require_str(system_table, "key_label"),
            public_key=_require_str(system_table, "public_key"),
        )

        org_table = raw.get("organization")
        if not isinstance(org_table, dict):
            raise KernelSeedSpecError("Seed spec missing [organization] table")
        organization = OrganizationSpec(
            key_label=_require_str(org_table, "key_label"),
            public_key=_require_str(org_table, "public_key"),
        )

        executors_raw = raw.get("executors")
        executors: list[ExecutorSpec] = []
        if executors_raw is None:
            executors_raw = []
        if not isinstance(executors_raw, list):
            raise KernelSeedSpecError(
                "Seed spec [[executors]] must be an array of tables"
            )
        for item in executors_raw:
            if not isinstance(item, dict):
                raise KernelSeedSpecError(
                    "Seed spec [[executors]] entries must be tables"
                )
            role = _optional_str(item, "role") or "member"
            executors.append(
                ExecutorSpec(
                    key_label=_require_str(item, "key_label"),
                    public_key=_require_str(item, "public_key"),
                    role=role,
                )
            )

        economy_table = raw.get("economy")
        if not isinstance(economy_table, dict):
            economy_table = {}
        legacy_service_keys = {
            "service_config_name",
            "membership_service_name",
            "inference_service_name",
            "agent_service_name",
        }
        present_legacy_service_keys = sorted(
            key for key in legacy_service_keys if key in economy_table
        )
        if present_legacy_service_keys:
            joined = ", ".join(present_legacy_service_keys)
            raise KernelSeedSpecError(
                "Seed spec [economy] must not contain service catalog fields; "
                f"move to [service]: {joined}"
            )

        service_table = raw.get("service")
        if not isinstance(service_table, dict):
            service_table = {}
        service = ServiceSpec(
            service_config_name=_optional_str(service_table, "service_config_name")
            or "Aware Catalog",
            inference_service_name=_optional_str(
                service_table, "inference_service_name"
            )
            or "Aware Inference",
        )
        economy = EconomySpec(
            smart_contract_config_name=_optional_str(
                economy_table, "smart_contract_config_name"
            )
            or "AwareMembership",
            smart_contract_type=_optional_str(economy_table, "smart_contract_type")
            or "utility",
            smart_contract_address=_optional_str(
                economy_table, "smart_contract_address"
            )
            or "dev:membership",
        )

        return KernelSeedSpec(
            aware=1,
            meta=SeedMeta(
                seed_id=seed_id, version=version, title=title, description=description
            ),
            kernel=kernel,
            system=system,
            organization=organization,
            executors=tuple(executors),
            service=service,
            economy=economy,
        )


__all__ = [
    "EconomySpec",
    "ExecutorSpec",
    "KernelConfig",
    "KernelSeedSpec",
    "KernelSeedSpecError",
    "OrganizationSpec",
    "SeedMeta",
    "ServiceSpec",
    "SystemSpec",
]
