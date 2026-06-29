from __future__ import annotations

from pathlib import Path


def _join(*parts: str) -> str:
    return "".join(parts)


TEST_ROOT = Path(__file__).resolve().parent
RUNTIME_ROOT = TEST_ROOT.parent / "aware_meta"
STALE_PROVIDER_DELTA_TEST_TOKENS = (
    _join("compatibility", "_facade"),
    _join("compatibility", " facade"),
)
RETIRED_STABLE_ID_ALIASES = (
    _join("stable_", "ocg_", "node_id"),
    _join("stable_object_projection_graph_", "view_id"),
)


def test_provider_delta_contract_tests_use_aggregate_export_language() -> None:
    test_paths = tuple(
        sorted(TEST_ROOT.glob("test_meta_provider_delta_*contract*.py"))
    ) + tuple(sorted(TEST_ROOT.glob("test_meta_provider_delta_*contract_modules.py")))

    offenders: list[str] = []
    for path in test_paths:
        source = path.read_text()
        for token in STALE_PROVIDER_DELTA_TEST_TOKENS:
            if token in source:
                offenders.append(f"{path.relative_to(TEST_ROOT)}: {token}")

    assert offenders == []


def test_retired_stable_id_aliases_are_not_present_in_meta_runtime() -> None:
    offenders: list[str] = []
    for path in sorted(RUNTIME_ROOT.rglob("*.py")):
        if "_generated" in path.parts or "__pycache__" in path.parts:
            continue
        source = path.read_text()
        for token in RETIRED_STABLE_ID_ALIASES:
            if token in source:
                offenders.append(f"{path.relative_to(RUNTIME_ROOT)}: {token}")

    assert offenders == []
