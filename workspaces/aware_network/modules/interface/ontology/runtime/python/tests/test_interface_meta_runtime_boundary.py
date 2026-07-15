from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[8]
INTERFACE_RUNTIME_ROOT = (
    REPO_ROOT / "modules" / "interface" / "runtime" / "aware_interface"
)
INTERFACE_SERVICE_ROOT = REPO_ROOT / "services" / "interface" / "aware_interface_service"
INTERFACE_RUNTIME_TEST_ROOT = REPO_ROOT / "modules" / "interface" / "runtime" / "tests"
GENERATED_LEGACY_HANDLER = (
    "workspaces/aware_network/modules/interface/ontology/runtime/python/aware_interface/handlers/_generated/handlers.py"
)
BOUNDARY_TEST = "workspaces/aware_network/modules/interface/ontology/runtime/python/tests/test_interface_meta_runtime_boundary.py"


def test_interface_production_consumers_do_not_import_libs_runtime() -> None:
    offenders = tuple(
        relative
        for root in (
            INTERFACE_RUNTIME_ROOT,
            INTERFACE_SERVICE_ROOT,
            INTERFACE_RUNTIME_TEST_ROOT,
        )
        for relative in _aware_runtime_import_offenders(root)
        if relative not in {GENERATED_LEGACY_HANDLER, BOUNDARY_TEST}
    )

    assert offenders == ()


def _aware_runtime_import_offenders(root: Path) -> tuple[str, ...]:
    return tuple(
        path.relative_to(REPO_ROOT).as_posix()
        for path in sorted(root.rglob("*.py"))
        if "aware_runtime" in path.read_text(encoding="utf-8")
    )
