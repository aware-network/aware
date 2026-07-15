from __future__ import annotations

from pathlib import Path

from ._environment_runtime_test_paths import (
    ENVIRONMENT_AWARE,
    ENVIRONMENT_RUNTIME_ROOT,
)

_RETIRED_FUNCTION_NAME = "resolve_actor_directory"
_DEPRECATED_IMPORT_MARKERS = (
    "aware_" "runtime",
    "aware_" "environment_artifacts",
)


def test_thread_actor_directory_db_bridge_is_retired_from_environment_source() -> None:
    source_paths = (
        ENVIRONMENT_AWARE / "thread/thread.aware",
        ENVIRONMENT_RUNTIME_ROOT / "aware_environment/handlers/impl/thread/thread.py",
        ENVIRONMENT_RUNTIME_ROOT
        / "aware_environment/handlers/_generated/meta_handlers.py",
    )

    for path in source_paths:
        text = path.read_text(encoding="utf-8")
        assert _RETIRED_FUNCTION_NAME not in text


def test_thread_actor_directory_tests_no_longer_bootstrap_deprecated_runtime() -> None:
    test_paths = (
        Path(__file__),
        Path(__file__).with_name("test_thread_resolve_actor_directory_fs.py"),
    )

    for path in test_paths:
        text = path.read_text(encoding="utf-8")
        assert not any(marker in text for marker in _DEPRECATED_IMPORT_MARKERS)
