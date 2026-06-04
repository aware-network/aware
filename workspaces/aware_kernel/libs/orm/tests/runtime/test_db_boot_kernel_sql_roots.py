from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_orm.runtime.db_boot import DBBootPlanError, build_sql_boot_plan_multi, ensure_db_schema_installed_multi
from aware_orm._support import find_aware_repo_root


class _NoopTransaction:
    async def __aenter__(self) -> object:  # pragma: no cover
        return self

    async def __aexit__(  # pragma: no cover
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None,
    ) -> object:
        return False


class _NoopConnection:
    def __init__(self) -> None:
        self._marker_by_env: dict[UUID, dict[str, object]] = {}
        self.executed: list[str] = []

    def transaction(self) -> _NoopTransaction:
        return _NoopTransaction()

    async def execute(self, query: str, *args: object) -> object:
        sql = query.strip().lower()
        self.executed.append(query.strip())
        if sql.startswith("insert into public.aware_bootstrap_marker"):
            env_id = args[0]
            ocg_hash = args[1]
            ocg_head_commit_id = args[2]
            assert isinstance(env_id, UUID)
            assert isinstance(ocg_hash, str)
            assert ocg_head_commit_id is None or isinstance(ocg_head_commit_id, UUID)
            self._marker_by_env[env_id] = {
                "ocg_hash": ocg_hash,
                "ocg_head_commit_id": ocg_head_commit_id,
            }
        return "OK"

    async def fetchrow(self, query: str, *args: object) -> dict[str, object] | None:
        env_id = args[0]
        assert isinstance(env_id, UUID)
        marker = self._marker_by_env.get(env_id)
        if marker is None:
            return None
        return dict(marker)


def _module_sql_roots(modules_root: Path) -> list[Path]:
    sql_roots: list[Path] = []
    for module_dir in sorted([p for p in modules_root.iterdir() if p.is_dir()], key=lambda p: p.name):
        candidates = [
            module_dir / "structure" / "ontology" / "sql",
            module_dir / "structure" / "structure" / "ontology" / "sql",
        ]
        for sql_root in candidates:
            if sql_root.exists():
                sql_roots.append(sql_root)
                break
    return sql_roots


def _select_non_conflicting_sql_roots(sql_roots: list[Path]) -> list[Path]:
    """Select the largest deterministic prefix-ish subset that has one table owner per schema/name."""
    selected: list[Path] = []
    for sql_root in sql_roots:
        candidate = [*selected, sql_root]
        try:
            build_sql_boot_plan_multi(sql_roots=candidate)
        except DBBootPlanError:
            continue
        selected = candidate
    return selected


@pytest.mark.asyncio
async def test_db_boot_can_plan_and_strip_fks_across_kernel_module_sql_roots() -> None:
    repo_root = find_aware_repo_root()
    modules_root = repo_root / "modules"
    if not modules_root.exists():
        pytest.skip("monorepo modules/ directory not available")

    all_sql_roots = _module_sql_roots(modules_root)
    sql_roots = _select_non_conflicting_sql_roots(all_sql_roots)

    if not sql_roots:
        pytest.skip("no non-conflicting module SQL roots found under modules/*/structure/**/ontology/sql")

    conn = _NoopConnection()
    env_id = uuid4()
    res = await ensure_db_schema_installed_multi(
        connection=conn,
        sql_roots=sql_roots,
        environment_id=env_id,
        ocg_hash="sha256:test",
    )
    assert res.installed is True
    assert res.step_count > 0
    assert res.schema_count > 0
    assert any("ADD FOREIGN KEY" in sql for sql in conn.executed)
