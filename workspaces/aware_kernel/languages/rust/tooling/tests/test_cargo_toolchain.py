from __future__ import annotations

import sys
from pathlib import Path

import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
CODE_ROOT = WORKSPACE_ROOT / "modules" / "code" / "ontology" / "runtime" / "python"
RUST_TOOLING_ROOT = Path(__file__).resolve().parents[1]
for path in (CODE_ROOT, RUST_TOOLING_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from aware_code.language.toolchain import CodeToolchainUnavailable  # noqa: E402
from rust_tooling.cargo import (  # noqa: E402
    CARGO_PROVIDER_KEY,
    CARGO_TOOLCHAIN_KEY,
    CargoBuildRequest,
    CargoDynamicLibraryBuildRequest,
    CargoToolchainConfig,
    build_cargo_binary_plan,
    build_cargo_dynamic_library_plan,
    cargo_binary_output_path,
    cargo_dynamic_library_output_path,
    dynamic_library_name,
    executable_binary_name,
    prepare_cargo_binary,
    prepare_cargo_dynamic_library,
    resolve_cargo_toolchain,
)


def test_resolve_cargo_toolchain_accepts_explicit_path(tmp_path: Path) -> None:
    target_dir = tmp_path / "cargo-target"
    toolchain = resolve_cargo_toolchain(
        CargoToolchainConfig(
            cargo_path=Path(sys.executable),
            target_dir=target_dir,
        )
    )

    assert toolchain.provider_key == CARGO_PROVIDER_KEY
    assert toolchain.toolchain_key == CARGO_TOOLCHAIN_KEY
    assert toolchain.executable_path == Path(sys.executable).absolute()
    assert toolchain.env["CARGO_TARGET_DIR"] == target_dir.resolve().as_posix()
    assert toolchain.state_roots[0].key == "target_dir"
    assert toolchain.version is not None


def test_cargo_binary_output_path_is_cross_platform(tmp_path: Path) -> None:
    assert (
        cargo_binary_output_path(
            target_dir=tmp_path,
            bin_name="aware-tool",
            profile="debug",
            platform_system="Linux",
        )
        == tmp_path.resolve() / "debug" / "aware-tool"
    )
    assert executable_binary_name("aware-tool", platform_system="Windows") == (
        "aware-tool.exe"
    )


def test_cargo_dynamic_library_output_path_is_cross_platform(tmp_path: Path) -> None:
    assert (
        cargo_dynamic_library_output_path(
            target_dir=tmp_path,
            library_name="aware_tool",
            profile="debug",
            platform_system="Linux",
        )
        == tmp_path.resolve() / "debug" / "libaware_tool.so"
    )
    assert dynamic_library_name("aware_tool", platform_system="Darwin") == (
        "libaware_tool.dylib"
    )
    assert dynamic_library_name("aware_tool", platform_system="Windows") == (
        "aware_tool.dll"
    )


def test_build_cargo_binary_plan_binds_target_dir(tmp_path: Path) -> None:
    manifest = tmp_path / "Cargo.toml"
    manifest.write_text(
        '[package]\nname = "aware-demo"\nversion = "0.1.0"\nedition = "2021"\n',
        encoding="utf-8",
    )

    plan = build_cargo_binary_plan(
        CargoBuildRequest(
            manifest_path=manifest,
            bin_name="aware-demo",
            target_dir=tmp_path / "target",
            cargo_path=Path(sys.executable),
        )
    )

    assert plan.provider_key == CARGO_PROVIDER_KEY
    assert plan.binary_name == "aware-demo"
    assert plan.profile == "debug"
    assert (
        plan.command.env["CARGO_TARGET_DIR"]
        == (tmp_path / "target").resolve().as_posix()
    )
    assert "--manifest-path" in plan.command.command
    assert (
        plan.output_path
        == (
            tmp_path / "target" / "debug" / executable_binary_name("aware-demo")
        ).resolve()
    )


def test_build_cargo_dynamic_library_plan_binds_target_dir(tmp_path: Path) -> None:
    manifest = tmp_path / "Cargo.toml"
    manifest.write_text(
        '[package]\nname = "aware-demo"\nversion = "0.1.0"\nedition = "2021"\n',
        encoding="utf-8",
    )

    plan = build_cargo_dynamic_library_plan(
        CargoDynamicLibraryBuildRequest(
            manifest_path=manifest,
            library_name="aware_demo",
            target_dir=tmp_path / "target",
            cargo_path=Path(sys.executable),
        )
    )

    assert plan.provider_key == CARGO_PROVIDER_KEY
    assert plan.binary_name == "aware_demo"
    assert plan.profile == "debug"
    assert (
        plan.command.env["CARGO_TARGET_DIR"]
        == (tmp_path / "target").resolve().as_posix()
    )
    assert "--manifest-path" in plan.command.command
    assert "--lib" in plan.command.command
    assert plan.command.metadata["artifact_kind"] == "cdylib"
    assert (
        plan.output_path
        == (
            tmp_path / "target" / "debug" / dynamic_library_name("aware_demo")
        ).resolve()
    )


def test_prepare_file_system_native_apply_binary_with_cargo(
    tmp_path: Path,
) -> None:
    manifest_path = (
        WORKSPACE_ROOT
        / "modules"
        / "filesystem"
        / "libs"
        / "file_system"
        / "rust"
        / "aware_file_system_native"
        / "Cargo.toml"
    )
    try:
        receipt = prepare_cargo_binary(
            CargoBuildRequest(
                manifest_path=manifest_path,
                bin_name="aware-file-system-native-apply",
                target_dir=tmp_path / "cargo-target",
                timeout_s=240.0,
            )
        )
    except CodeToolchainUnavailable as exc:
        pytest.skip(str(exc))

    assert receipt.status == "succeeded", receipt.to_mapping()
    assert receipt.artifact_exists is True
    assert receipt.plan.output_path == receipt.artifact_path
    assert receipt.plan.toolchain.version is not None
    assert (
        receipt.to_mapping()["plan"]["metadata"]["target_dir"]
        == (tmp_path / "cargo-target").resolve().as_posix()
    )


def test_prepare_file_system_native_dynamic_library_with_cargo(
    tmp_path: Path,
) -> None:
    manifest_path = (
        WORKSPACE_ROOT
        / "modules"
        / "filesystem"
        / "libs"
        / "file_system"
        / "rust"
        / "aware_file_system_native"
        / "Cargo.toml"
    )
    try:
        receipt = prepare_cargo_dynamic_library(
            CargoDynamicLibraryBuildRequest(
                manifest_path=manifest_path,
                library_name="aware_file_system_native",
                target_dir=tmp_path / "cargo-target",
                timeout_s=240.0,
            )
        )
    except CodeToolchainUnavailable as exc:
        pytest.skip(str(exc))

    assert receipt.status == "succeeded", receipt.to_mapping()
    assert receipt.artifact_exists is True
    assert receipt.plan.output_path == receipt.artifact_path
    assert receipt.plan.toolchain.version is not None
    assert receipt.to_mapping()["plan"]["metadata"]["artifact_kind"] == "cdylib"
