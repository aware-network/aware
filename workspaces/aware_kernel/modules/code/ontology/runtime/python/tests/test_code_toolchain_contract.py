from __future__ import annotations

import sys
from pathlib import Path

import pytest

from aware_code.language.toolchain import (
    CodeToolchainCommandSpec,
    CodeToolchainStateRoot,
    CodeToolchainUnavailable,
    env_from_state_roots,
    resolve_toolchain_executable,
    run_code_toolchain_command,
)
from aware_code_ontology.code.code_enums import CodeLanguage


def test_resolve_toolchain_executable_uses_explicit_path() -> None:
    executable = resolve_toolchain_executable(
        "python",
        explicit_path=Path(sys.executable),
    )

    assert executable == Path(sys.executable).absolute()


def test_resolve_toolchain_executable_fails_closed_for_missing_path(
    tmp_path: Path,
) -> None:
    with pytest.raises(CodeToolchainUnavailable, match="does not exist"):
        resolve_toolchain_executable(
            "missing",
            explicit_path=tmp_path / "missing-tool",
        )


def test_run_code_toolchain_command_passes_env_without_shell() -> None:
    result = run_code_toolchain_command(
        CodeToolchainCommandSpec(
            provider_key="test_provider",
            toolchain_key="python",
            role="version",
            command=(
                sys.executable,
                "-c",
                "import os; print(os.environ['AWARE_TOOLCHAIN_TEST'])",
            ),
            env={"AWARE_TOOLCHAIN_TEST": "ok"},
        )
    )

    assert result.status == "succeeded"
    assert result.stdout.strip() == "ok"
    assert result.command[0] == sys.executable


def test_env_from_state_roots_uses_resolved_paths(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    env = env_from_state_roots(
        (
            CodeToolchainStateRoot(
                key="target",
                kind="target",
                path=target_dir,
                env_var="AWARE_TOOLCHAIN_TARGET",
            ),
        )
    )

    assert env == {
        "AWARE_TOOLCHAIN_TARGET": target_dir.resolve().as_posix(),
    }


def test_toolchain_contract_does_not_add_rust_code_language() -> None:
    assert "rust" not in {language.value for language in CodeLanguage}
