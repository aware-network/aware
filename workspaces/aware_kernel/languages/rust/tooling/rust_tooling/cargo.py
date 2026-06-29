from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
import platform

from aware_code.language.toolchain import (
    CodePreparedBinaryPlan,
    CodePreparedBinaryReceipt,
    CodeToolchainCommandSpec,
    CodeToolchainResolution,
    CodeToolchainStateRoot,
    CodeToolchainUnavailable,
    env_from_state_roots,
    read_toolchain_version,
    resolve_toolchain_executable,
    run_code_toolchain_command,
)


CARGO_PROVIDER_KEY = "rust_tooling"
CARGO_TOOLCHAIN_KEY = "cargo"
DEFAULT_CARGO_BUILD_TIMEOUT_S = 180.0


@dataclass(frozen=True, slots=True)
class CargoToolchainConfig:
    cargo_path: Path | None = None
    cargo_home: Path | None = None
    target_dir: Path | None = None
    extra_env: Mapping[str, str] = field(default_factory=dict)
    version_timeout_s: float = 10.0


@dataclass(frozen=True, slots=True)
class CargoBuildRequest:
    manifest_path: Path
    bin_name: str
    target_dir: Path | None = None
    cargo_path: Path | None = None
    cargo_home: Path | None = None
    package: str | None = None
    release: bool = False
    quiet: bool = True
    timeout_s: float = DEFAULT_CARGO_BUILD_TIMEOUT_S
    extra_env: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CargoDynamicLibraryBuildRequest:
    manifest_path: Path
    library_name: str
    target_dir: Path | None = None
    cargo_path: Path | None = None
    cargo_home: Path | None = None
    package: str | None = None
    release: bool = False
    quiet: bool = True
    timeout_s: float = DEFAULT_CARGO_BUILD_TIMEOUT_S
    extra_env: Mapping[str, str] = field(default_factory=dict)


def resolve_cargo_toolchain(
    config: CargoToolchainConfig | None = None,
) -> CodeToolchainResolution:
    resolved = config or CargoToolchainConfig()
    cargo_path = _resolve_cargo_path(resolved.cargo_path)
    state_roots = _cargo_state_roots(
        cargo_home=resolved.cargo_home,
        target_dir=resolved.target_dir,
    )
    env = {
        **env_from_state_roots(state_roots),
        **dict(resolved.extra_env),
    }
    version = read_toolchain_version(
        cargo_path,
        env=env,
        timeout_s=resolved.version_timeout_s,
    )
    return CodeToolchainResolution(
        provider_key=CARGO_PROVIDER_KEY,
        toolchain_key=CARGO_TOOLCHAIN_KEY,
        executable_name="cargo",
        executable_path=cargo_path,
        version=version,
        state_roots=state_roots,
        env=env,
        metadata={
            "platform_system": platform.system(),
            "executable_suffix": executable_suffix(),
        },
    )


def build_cargo_binary_plan(
    request: CargoBuildRequest,
    *,
    toolchain: CodeToolchainResolution | None = None,
) -> CodePreparedBinaryPlan:
    manifest_path = request.manifest_path.expanduser().resolve()
    if not manifest_path.is_file():
        raise ValueError(f"Cargo manifest does not exist: {manifest_path.as_posix()}")
    if not request.bin_name.strip():
        raise ValueError("Cargo build requires a binary name.")

    target_dir = (
        request.target_dir.expanduser().resolve()
        if request.target_dir is not None
        else manifest_path.parent / "target"
    )
    resolved_toolchain = toolchain or resolve_cargo_toolchain(
        CargoToolchainConfig(
            cargo_path=request.cargo_path,
            cargo_home=request.cargo_home,
            target_dir=target_dir,
            extra_env=request.extra_env,
        )
    )
    env = {
        **dict(resolved_toolchain.env),
        "CARGO_TARGET_DIR": target_dir.as_posix(),
        **dict(request.extra_env),
    }
    command = [
        resolved_toolchain.executable_path.as_posix(),
        "build",
        "--manifest-path",
        manifest_path.as_posix(),
        "--bin",
        request.bin_name,
    ]
    if request.quiet:
        command.insert(2, "--quiet")
    if request.package is not None:
        command.extend(("--package", request.package))
    if request.release:
        command.append("--release")

    profile = "release" if request.release else "debug"
    output_path = cargo_binary_output_path(
        target_dir=target_dir,
        bin_name=request.bin_name,
        profile=profile,
    )
    command_spec = CodeToolchainCommandSpec(
        provider_key=CARGO_PROVIDER_KEY,
        toolchain_key=CARGO_TOOLCHAIN_KEY,
        role="build",
        command=tuple(command),
        cwd=manifest_path.parent,
        env=env,
        timeout_s=request.timeout_s,
        mutates_targets=True,
        metadata={
            "manifest_path": manifest_path.as_posix(),
            "bin_name": request.bin_name,
            "profile": profile,
            "target_dir": target_dir.as_posix(),
        },
    )
    return CodePreparedBinaryPlan(
        provider_key=CARGO_PROVIDER_KEY,
        toolchain_key=CARGO_TOOLCHAIN_KEY,
        binary_name=request.bin_name,
        profile=profile,
        manifest_path=manifest_path,
        output_path=output_path,
        command=command_spec,
        toolchain=resolved_toolchain,
        metadata={
            "target_dir": target_dir.as_posix(),
            "package": request.package or "",
        },
    )


def build_cargo_dynamic_library_plan(
    request: CargoDynamicLibraryBuildRequest,
    *,
    toolchain: CodeToolchainResolution | None = None,
) -> CodePreparedBinaryPlan:
    manifest_path = request.manifest_path.expanduser().resolve()
    if not manifest_path.is_file():
        raise ValueError(f"Cargo manifest does not exist: {manifest_path.as_posix()}")
    if not request.library_name.strip():
        raise ValueError("Cargo build requires a library name.")

    target_dir = (
        request.target_dir.expanduser().resolve()
        if request.target_dir is not None
        else manifest_path.parent / "target"
    )
    resolved_toolchain = toolchain or resolve_cargo_toolchain(
        CargoToolchainConfig(
            cargo_path=request.cargo_path,
            cargo_home=request.cargo_home,
            target_dir=target_dir,
            extra_env=request.extra_env,
        )
    )
    env = {
        **dict(resolved_toolchain.env),
        "CARGO_TARGET_DIR": target_dir.as_posix(),
        **dict(request.extra_env),
    }
    command = [
        resolved_toolchain.executable_path.as_posix(),
        "build",
        "--manifest-path",
        manifest_path.as_posix(),
        "--lib",
    ]
    if request.quiet:
        command.insert(2, "--quiet")
    if request.package is not None:
        command.extend(("--package", request.package))
    if request.release:
        command.append("--release")

    profile = "release" if request.release else "debug"
    output_path = cargo_dynamic_library_output_path(
        target_dir=target_dir,
        library_name=request.library_name,
        profile=profile,
    )
    command_spec = CodeToolchainCommandSpec(
        provider_key=CARGO_PROVIDER_KEY,
        toolchain_key=CARGO_TOOLCHAIN_KEY,
        role="build",
        command=tuple(command),
        cwd=manifest_path.parent,
        env=env,
        timeout_s=request.timeout_s,
        mutates_targets=True,
        metadata={
            "manifest_path": manifest_path.as_posix(),
            "library_name": request.library_name,
            "profile": profile,
            "target_dir": target_dir.as_posix(),
            "artifact_kind": "cdylib",
        },
    )
    return CodePreparedBinaryPlan(
        provider_key=CARGO_PROVIDER_KEY,
        toolchain_key=CARGO_TOOLCHAIN_KEY,
        binary_name=request.library_name,
        profile=profile,
        manifest_path=manifest_path,
        output_path=output_path,
        command=command_spec,
        toolchain=resolved_toolchain,
        metadata={
            "target_dir": target_dir.as_posix(),
            "package": request.package or "",
            "artifact_kind": "cdylib",
        },
    )


def prepare_cargo_binary(request: CargoBuildRequest) -> CodePreparedBinaryReceipt:
    plan = build_cargo_binary_plan(request)
    target_dir = Path(plan.command.env["CARGO_TARGET_DIR"])
    target_dir.mkdir(parents=True, exist_ok=True)
    result = run_code_toolchain_command(plan.command)
    return CodePreparedBinaryReceipt(
        plan=plan,
        result=result,
        artifact_path=plan.output_path,
    )


def prepare_cargo_dynamic_library(
    request: CargoDynamicLibraryBuildRequest,
) -> CodePreparedBinaryReceipt:
    plan = build_cargo_dynamic_library_plan(request)
    target_dir = Path(plan.command.env["CARGO_TARGET_DIR"])
    target_dir.mkdir(parents=True, exist_ok=True)
    result = run_code_toolchain_command(plan.command)
    return CodePreparedBinaryReceipt(
        plan=plan,
        result=result,
        artifact_path=plan.output_path,
    )


def cargo_binary_output_path(
    *,
    target_dir: Path,
    bin_name: str,
    profile: str,
    platform_system: str | None = None,
) -> Path:
    return (
        target_dir.expanduser().resolve()
        / profile
        / executable_binary_name(bin_name, platform_system=platform_system)
    )


def cargo_dynamic_library_output_path(
    *,
    target_dir: Path,
    library_name: str,
    profile: str,
    platform_system: str | None = None,
) -> Path:
    return (
        target_dir.expanduser().resolve()
        / profile
        / dynamic_library_name(library_name, platform_system=platform_system)
    )


def executable_binary_name(
    bin_name: str,
    *,
    platform_system: str | None = None,
) -> str:
    suffix = executable_suffix(platform_system=platform_system)
    if suffix and not bin_name.endswith(suffix):
        return f"{bin_name}{suffix}"
    return bin_name


def dynamic_library_name(
    library_name: str,
    *,
    platform_system: str | None = None,
) -> str:
    system = (platform_system or platform.system()).lower()
    if system.startswith("win"):
        return f"{library_name}.dll"
    if system == "darwin":
        return f"lib{library_name}.dylib"
    return f"lib{library_name}.so"


def executable_suffix(*, platform_system: str | None = None) -> str:
    system = platform_system or platform.system()
    if system.lower().startswith("win"):
        return ".exe"
    return ""


def _resolve_cargo_path(cargo_path: Path | None) -> Path:
    if cargo_path is not None:
        return resolve_toolchain_executable("cargo", explicit_path=cargo_path)
    try:
        return resolve_toolchain_executable("cargo")
    except CodeToolchainUnavailable:
        home_cargo = Path.home() / ".cargo" / "bin" / executable_binary_name(
            "cargo"
        )
        if home_cargo.is_file():
            return resolve_toolchain_executable("cargo", explicit_path=home_cargo)
        raise


def _cargo_state_roots(
    *,
    cargo_home: Path | None,
    target_dir: Path | None,
) -> tuple[CodeToolchainStateRoot, ...]:
    roots: list[CodeToolchainStateRoot] = []
    if cargo_home is not None:
        roots.append(
            CodeToolchainStateRoot(
                key="cargo_home",
                kind="home",
                path=cargo_home.expanduser().resolve(),
                env_var="CARGO_HOME",
            )
        )
    if target_dir is not None:
        roots.append(
            CodeToolchainStateRoot(
                key="target_dir",
                kind="target",
                path=target_dir.expanduser().resolve(),
                env_var="CARGO_TARGET_DIR",
            )
        )
    return tuple(roots)


__all__ = [
    "CARGO_PROVIDER_KEY",
    "CARGO_TOOLCHAIN_KEY",
    "CargoBuildRequest",
    "CargoDynamicLibraryBuildRequest",
    "CargoToolchainConfig",
    "build_cargo_binary_plan",
    "build_cargo_dynamic_library_plan",
    "cargo_binary_output_path",
    "cargo_dynamic_library_output_path",
    "dynamic_library_name",
    "executable_binary_name",
    "executable_suffix",
    "prepare_cargo_binary",
    "prepare_cargo_dynamic_library",
    "resolve_cargo_toolchain",
]
