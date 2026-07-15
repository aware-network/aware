from __future__ import annotations

from pathlib import Path

import pytest
from aware_utils import secrets

from aware_service_runtime.manifest.spec import AwareServiceTomlRuntimeSpec
from aware_service_runtime.runtime_secrets import (
    ServiceRuntimeSecretError,
    configure_service_runtime_secrets,
    require_service_runtime_secret,
    require_service_runtime_value,
)


@pytest.fixture(autouse=True)
def isolated_secrets_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AWARE_TEST_SERVICE_SECRET", raising=False)
    secrets.reset_secrets_state_for_tests()


def test_service_runtime_secret_directory_env_overrides_canonical(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    selected = tmp_path / "selected"
    selected.mkdir()
    (selected / "AWARE_TEST_SERVICE_SECRET").write_text(
        "from-selected\n",
        encoding="utf-8",
    )
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    (canonical / "AWARE_TEST_SERVICE_SECRET").write_text(
        "from-canonical\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("AWARE_TEST_SECRETS_DIR", selected.as_posix())

    resolved = configure_service_runtime_secrets(
        AwareServiceTomlRuntimeSpec(
            secrets_dir_env="AWARE_TEST_SECRETS_DIR",
            canonical_secrets_dir=canonical.as_posix(),
        )
    )

    assert resolved == selected.resolve()
    assert require_service_runtime_secret("AWARE_TEST_SERVICE_SECRET") == (
        "from-selected"
    )


def test_service_runtime_secret_uses_canonical_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    (canonical / "AWARE_TEST_SERVICE_SECRET").write_text(
        "from-canonical\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("AWARE_TEST_SECRETS_DIR", raising=False)

    configure_service_runtime_secrets(
        AwareServiceTomlRuntimeSpec(
            secrets_dir_env="AWARE_TEST_SECRETS_DIR",
            canonical_secrets_dir=canonical.as_posix(),
        )
    )

    assert require_service_runtime_secret("AWARE_TEST_SERVICE_SECRET") == (
        "from-canonical"
    )


def test_service_runtime_value_failure_names_requirement_without_value() -> None:
    with pytest.raises(
        ServiceRuntimeSecretError,
        match="Required Service runtime value is unavailable: AWARE_MISSING_SECRET",
    ):
        require_service_runtime_value("AWARE_MISSING_SECRET")
