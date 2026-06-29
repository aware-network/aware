from __future__ import annotations

from pathlib import Path


def _kernel_root() -> Path:
    current = Path(__file__).resolve()
    for parent in (current, *current.parents):
        if (parent / "aware.workspace.toml").is_file():
            return parent
    raise AssertionError("Could not locate aware_kernel workspace root")


def test_public_runtime_packages_do_not_import_aware_root_discovery() -> None:
    kernel_root = _kernel_root()
    roots = (
        kernel_root / "languages" / "dart" / "grammar" / "grammar" / "dart_grammar",
        kernel_root / "libs" / "orm" / "aware_orm" / "runtime",
        kernel_root / "libs" / "orm" / "aware_orm" / "session",
        kernel_root / "modules" / "code" / "ontology" / "runtime" / "python",
        kernel_root / "modules" / "filesystem" / "libs" / "file_system" / "python",
        kernel_root / "modules" / "meta" / "ontology" / "runtime" / "python",
        kernel_root / "modules" / "meta" / "services" / "meta" / "aware_meta_service",
        kernel_root
        / "modules"
        / "ontology"
        / "services"
        / "ontology"
        / "aware_ontology_service",
    )
    offenders: list[str] = []
    for root in roots:
        for path in sorted(root.rglob("*.py")):
            if "tests" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            banned_tokens = (
                "aware_utils.find_aware_root",
                "aware_root_discovery",
                "find_aware_repo_root",
            )
            for token in banned_tokens:
                if token in text:
                    offenders.append(f"{path.relative_to(kernel_root).as_posix()}:{token}")

    assert offenders == []
