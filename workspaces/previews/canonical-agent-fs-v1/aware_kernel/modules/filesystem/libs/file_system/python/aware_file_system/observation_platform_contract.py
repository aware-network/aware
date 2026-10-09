from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

PLATFORM_RECEIPT_SCHEMA = "aware.file_system.observation_platform_receipt.v3"
CROSS_PLATFORM_RECEIPT_SET_SCHEMA = (
    "aware.file_system.observation_cross_platform_receipt_set.v3"
)


@dataclass(frozen=True, slots=True)
class ObservationPlatformClass:
    key: str
    platform_key: str
    sys_platform: str
    os_name: str
    architecture_class: str
    target_triple: str

    def as_receipt(self) -> dict[str, Any]:
        return asdict(self)


SUPPORTED_PLATFORM_CLASSES = {
    "linux": ObservationPlatformClass(
        key="linux_x86_64",
        platform_key="linux",
        sys_platform="linux",
        os_name="posix",
        architecture_class="x86_64",
        target_triple="x86_64-unknown-linux-gnu",
    ),
    "macos": ObservationPlatformClass(
        key="macos_arm64",
        platform_key="macos",
        sys_platform="darwin",
        os_name="posix",
        architecture_class="arm64",
        target_triple="aarch64-apple-darwin",
    ),
    "windows": ObservationPlatformClass(
        key="windows_x86_64",
        platform_key="windows",
        sys_platform="win32",
        os_name="nt",
        architecture_class="x86_64",
        target_triple="x86_64-pc-windows-msvc",
    ),
}

_MACHINE_ARCHITECTURE_CLASSES = {
    "aarch64": "arm64",
    "amd64": "x86_64",
    "arm64": "arm64",
    "x64": "x86_64",
    "x86_64": "x86_64",
}


def architecture_class(machine: str) -> str:
    return _MACHINE_ARCHITECTURE_CLASSES.get(machine.strip().lower(), "unsupported")


def resolve_supported_platform_class(
    *,
    platform_key: str,
    sys_platform: str,
    os_name: str,
    machine: str,
    target_triple: str,
) -> ObservationPlatformClass | None:
    expected = SUPPORTED_PLATFORM_CLASSES.get(platform_key)
    if expected is None:
        return None
    if (
        sys_platform != expected.sys_platform
        or os_name != expected.os_name
        or architecture_class(machine) != expected.architecture_class
        or target_triple != expected.target_triple
    ):
        return None
    return expected
