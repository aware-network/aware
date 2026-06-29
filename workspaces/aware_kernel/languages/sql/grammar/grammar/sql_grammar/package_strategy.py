"""SQL-specific ObjectConfigGraph package strategy.

Honesty contract:
- Renderers write into a deterministic staging directory under `.aware/materializations/...`.
- The package strategy owns the final output root and syncs outputs incrementally.

SQL direction (B):
- SQL file layout is namespace-driven and may include synthetic classes
  (e.g., join tables) without code provenance.
"""

from pathlib import Path

from aware_meta.graph.config.package_strategy import (
    ObjectConfigGraphPackageSpec,
    ObjectConfigGraphPackageStrategy,
)
from typing_extensions import override


class SQLPackageStrategy(ObjectConfigGraphPackageStrategy):
    """Builds a SQL artifact package by copying rendered .sql files into the package root."""

    @override
    def build_into(
        self,
        *,
        output_root: Path,
        rendered_files: list[Path],
        spec: ObjectConfigGraphPackageSpec,
    ) -> list[Path]:
        """Populate `output_root` with SQL artifacts."""
        _ = spec
        rendered_paths = [Path(p).resolve() for p in rendered_files]
        files_written: list[Path] = []

        for src_path in rendered_paths:
            if src_path.suffix != ".sql":
                continue
            try:
                rel = src_path.relative_to(self.base_dir)
            except ValueError:
                # Best-effort: keep file name only if it is not under base_dir.
                rel = Path(src_path.name)
            dest = (output_root / rel).resolve()
            self._copy_if_changed(src_path, dest)
            files_written.append(dest)

        return files_written
