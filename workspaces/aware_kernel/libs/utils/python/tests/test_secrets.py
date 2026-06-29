from __future__ import annotations

from pathlib import Path

import pytest

from aware_utils import secrets


@pytest.fixture(autouse=True)
def isolated_secrets_state() -> None:
    secrets.reset_secrets_state_for_tests()


def test_resolve_secret_prefers_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWARE_UTILS_TEST_SECRET", "from-env")
    assert secrets.resolve_secret("AWARE_UTILS_TEST_SECRET") == "from-env"


def test_use_dotenv_loads_when_env_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("AWARE_UTILS_DOT_SECRET", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text("AWARE_UTILS_DOT_SECRET=from-dotenv\n", encoding="utf-8")

    secrets.use_dotenv(env_file)
    assert secrets.resolve_secret("AWARE_UTILS_DOT_SECRET") == "from-dotenv"


def test_use_dotenv_does_not_override_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AWARE_UTILS_DOT_SECRET", "from-env")

    env_file = tmp_path / ".env"
    env_file.write_text("AWARE_UTILS_DOT_SECRET=from-dotenv\n", encoding="utf-8")

    secrets.use_dotenv(env_file)
    assert secrets.resolve_secret("AWARE_UTILS_DOT_SECRET") == "from-env"


def test_use_secrets_dir_loads_file(tmp_path: Path) -> None:
    secret_dir = tmp_path / "secrets"
    secret_dir.mkdir()
    (secret_dir / "AWARE_UTILS_DIR_SECRET").write_text("from-dir\n", encoding="utf-8")

    secrets.use_secrets_dir(secret_dir)
    assert secrets.resolve_secret("AWARE_UTILS_DIR_SECRET") == "from-dir"


def test_use_secrets_dir_does_not_override_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AWARE_UTILS_DIR_SECRET", "from-env")
    secret_dir = tmp_path / "secrets"
    secret_dir.mkdir()
    (secret_dir / "AWARE_UTILS_DIR_SECRET").write_text("from-dir\n", encoding="utf-8")

    secrets.use_secrets_dir(secret_dir)
    assert secrets.resolve_secret("AWARE_UTILS_DIR_SECRET") == "from-env"


def test_require_secret_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISSING_SECRET", raising=False)
    with pytest.raises(KeyError):
        secrets.require_secret("MISSING_SECRET")
