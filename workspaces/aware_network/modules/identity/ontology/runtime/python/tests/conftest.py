from __future__ import annotations

import asyncio
from collections.abc import Iterator
import os
from pathlib import Path

import pytest
from _pytest.fixtures import FixtureRequest

_DB_TEST_FILES = frozenset(
    {
        "test_identity_db_constraints.py",
        "test_identity_profile_search_db.py",
    }
)


def pytest_ignore_collect(
    collection_path: Path,
    config: pytest.Config,
) -> bool | None:
    path = Path(str(collection_path)).resolve()
    if path.name not in _DB_TEST_FILES:
        return None
    if _db_tests_enabled():
        return None
    if _db_path_explicitly_selected(config=config, path=path):
        raise pytest.UsageError(
            "Identity DB proofs require AWARE_RUN_DB_TESTS=1 plus DB connection "
            "environment. Default module sweeps intentionally do not collect DB "
            "proof files."
        )
    return True


@pytest.fixture(autouse=True)
def _drain_pending_async_generators(request: FixtureRequest) -> Iterator[None]:
    marker = request.node.get_closest_marker("asyncio")
    if marker is None or marker.kwargs.get("scope", "function") != "function":
        yield
        return

    event_loop = request.getfixturevalue("event_loop")
    yield
    event_loop.run_until_complete(asyncio.sleep(0))
    event_loop.run_until_complete(event_loop.shutdown_asyncgens())


def _db_tests_enabled() -> bool:
    value = (os.environ.get("AWARE_RUN_DB_TESTS") or "").strip().casefold()
    if value in {"1", "true", "yes", "on"}:
        return True
    return bool(
        os.environ.get("AWARE_DB_TEST_ADMIN_URL")
        or os.environ.get("AWARE_DB_TEST_URL")
        or (
            os.environ.get("AWARE_DB_TEST_BOOTSTRAP")
            and os.environ.get("AWARE_DB_TEST_BOOTSTRAP_URL")
        )
    )


def _db_path_explicitly_selected(
    *,
    config: pytest.Config,
    path: Path,
) -> bool:
    invocation_dir = Path(str(config.invocation_params.dir)).resolve()
    for raw_arg in config.args:
        raw_path = str(raw_arg).split("::", maxsplit=1)[0]
        if not raw_path:
            continue
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = invocation_dir / candidate
        try:
            selected = candidate.resolve()
        except OSError:
            continue
        if selected == path:
            return True
    return False
