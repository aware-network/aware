from __future__ import annotations

import os
from pathlib import Path

import pytest


def pytest_ignore_collect(
    collection_path: Path,
    config: pytest.Config,
) -> bool | None:
    live_dir = Path(__file__).resolve().parent / "live"
    path = Path(str(collection_path)).resolve()
    if path != live_dir and live_dir not in path.parents:
        return None
    if _live_sdk_enabled():
        return None
    if _live_path_explicitly_selected(config=config, live_dir=live_dir):
        raise pytest.UsageError(
            "Live SDK tests require AWARE_RUN_LIVE_SDK=1 plus live provider "
            "refs. Default module sweeps intentionally do not collect tests/live."
        )
    return True


def _live_sdk_enabled() -> bool:
    value = (os.environ.get("AWARE_RUN_LIVE_SDK") or "").strip().casefold()
    return value in {"1", "true", "yes", "on"}


def _live_path_explicitly_selected(
    *,
    config: pytest.Config,
    live_dir: Path,
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
        if selected == live_dir or live_dir in selected.parents:
            return True
    return False
