import re
from pathlib import Path


_LEGACY_PROJECT_ANN_RE = re.compile(r"^\\s*ann\\s+\\S+\\s+project\\b")
_IGNORE_DIRS = {
    ".aware",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    ".uv-cache",
    "__pycache__",
    "dist",
    "node_modules",
}


def _repo_root(start: Path) -> Path:
    for p in (start, *start.parents):
        if (p / "pyproject.toml").exists():
            return p
    return start


def test_repo_has_no_legacy_ann_project_in_aware_sources() -> None:
    """
    Canonical: projection membership must be authored via `projection { ... }`
    (not legacy `ann <path> project ...` statements).
    """
    repo_root = _repo_root(Path(__file__).resolve())
    offenders: list[str] = []

    for path in repo_root.rglob("*.aware"):
        if any(part in _IGNORE_DIRS for part in path.parts):
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            # Best-effort scan (repo may contain non-utf8 fixtures).
            continue

        for lineno, line in enumerate(text.splitlines(), start=1):
            if _LEGACY_PROJECT_ANN_RE.search(line):
                offenders.append(f"{path}:{lineno}: {line.strip()}")
                if len(offenders) >= 25:
                    break
        if len(offenders) >= 25:
            break

    assert offenders == [], (
        "Found legacy `ann ... project ...` statements. "
        + "Use `projection { ... }` declarations instead.\n"
        + "\n".join(offenders)
    )
