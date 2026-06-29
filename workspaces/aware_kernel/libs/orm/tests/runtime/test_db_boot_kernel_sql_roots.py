from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_orm.runtime.db_boot import ensure_db_schema_installed_multi


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


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.mark.asyncio
async def test_db_boot_can_plan_and_strip_fks_across_explicit_sql_roots(
    tmp_path: Path,
) -> None:
    identity_root = tmp_path / "identity_sql"
    actor_root = tmp_path / "actor_sql"
    _write(
        identity_root / "identity" / "identity.sql",
        """
CREATE TABLE identity (
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  PRIMARY KEY (branch_id, projection_hash, id)
);
""".strip()
        + "\n",
    )
    _write(
        actor_root / "actor" / "actor.sql",
        """
CREATE TABLE actor (
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  identity_id UUID NOT NULL,
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, identity_id) REFERENCES identity(branch_id, projection_hash, id)
);
""".strip()
        + "\n",
    )

    conn = _NoopConnection()
    env_id = uuid4()
    res = await ensure_db_schema_installed_multi(
        connection=conn,
        sql_roots=[identity_root, actor_root],
        environment_id=env_id,
        ocg_hash="sha256:test",
    )
    assert res.installed is True
    assert res.step_count > 0
    assert res.schema_count > 0

    create_actor = next(sql for sql in conn.executed if sql.startswith("CREATE TABLE actor"))
    assert "FOREIGN KEY" not in create_actor
    assert "REFERENCES identity" not in create_actor
    assert (
        'ALTER TABLE "actor"."actor" ADD FOREIGN KEY ("branch_id", "projection_hash", "identity_id") '
        'REFERENCES "identity"."identity" ("branch_id", "projection_hash", "id");'
    ) in conn.executed
