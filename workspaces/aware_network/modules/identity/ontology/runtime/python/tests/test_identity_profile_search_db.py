from __future__ import annotations

import json
import os
from pathlib import Path
import tomllib
from uuid import UUID

import pytest

from aware_orm.testing import db_test_database
from ._paths import IDENTITY_MODULE_ROOT, REPO_ROOT


def _identity_runtime_manifest_path(repo_root: Path) -> Path:
    manifest_path = (
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/.aware/ontology/runtime/ontology.runtime.manifest.json"
    )
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Identity runtime manifest not found: {manifest_path}")
    return manifest_path


def _manifest_identity(manifest_path: Path) -> tuple[UUID, str]:
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Environment manifest is not a JSON object: {manifest_path}")
    env = raw.get("environment") if isinstance(raw.get("environment"), dict) else {}
    env_id_raw = env.get("id")
    if not isinstance(env_id_raw, str) or not env_id_raw:
        raise ValueError(
            f"Environment manifest missing environment.id: {manifest_path}"
        )
    ocg_hash = raw.get("ocg_hash")
    if not isinstance(ocg_hash, str) or not ocg_hash:
        ocg = raw.get("ocg") if isinstance(raw.get("ocg"), dict) else {}
        ocg_hash = ocg.get("hash")
    if not isinstance(ocg_hash, str) or not ocg_hash:
        raise ValueError(f"Environment manifest missing ocg hash: {manifest_path}")
    return UUID(env_id_raw), ocg_hash


def _identity_db_sql_roots(repo_root: Path) -> tuple[Path, ...]:
    roots = (
        repo_root / "workspaces/aware_network/modules/identity/ontology/structure/sql",
        repo_root / "workspaces/aware_kernel/modules/meta/ontology/structure/sql",
    )
    missing = tuple(root for root in roots if not root.is_dir())
    if missing:
        raise FileNotFoundError(
            "Identity DB proof SQL roots are missing: "
            + ", ".join(str(root) for root in missing)
        )
    return tuple(sorted((root.resolve() for root in roots), key=str))


def _required_postgres_extensions_for_module(
    *, repo_root: Path, module_id: str
) -> list[str]:
    if module_id == "identity":
        module_toml = IDENTITY_MODULE_ROOT / "aware.module.toml"
    else:
        module_toml = repo_root / "modules" / module_id / "aware.module.toml"
    raw = tomllib.loads(module_toml.read_text(encoding="utf-8"))
    plugins = raw.get("plugins", [])
    if not isinstance(plugins, list):
        raise ValueError(f"Expected plugins list in {module_toml}")

    extensions: set[str] = set()
    for plugin in plugins:
        if not isinstance(plugin, dict):
            continue
        if plugin.get("kind") != "db.postgres.extension":
            continue
        if plugin.get("required", True) is False:
            continue
        name = plugin.get("name")
        if isinstance(name, str) and name:
            extensions.add(name)
    return sorted(extensions)


def _quote_postgres_extension_name(name: str) -> str:
    # Extensions are identifiers; asyncpg cannot bind identifiers as parameters.
    if not name or any(
        ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
        for ch in name
    ):
        raise ValueError(f"Invalid Postgres extension name: {name!r}")
    return f'"{name}"'


async def _insert_identity_profile(
    *,
    conn: object,
    branch_id: UUID,
    projection_hash: str,
    identity_id: UUID,
    identity_profile_id: UUID,
    public_key: str,
    public_handle: str,
    display_name: str,
    full_name: str,
    bio: str,
) -> None:
    await conn.execute(
        """
INSERT INTO "identity"."identity_profile"
  (branch_id, projection_hash, id, public_handle, display_name, full_name, country_code, language_code, bio)
VALUES
  ($1, $2, $3, $4, $5, $6, 'US', 'en', $7);
""".strip(),
        branch_id,
        projection_hash,
        identity_profile_id,
        public_handle,
        display_name,
        full_name,
        bio,
    )
    await conn.execute(
        """
INSERT INTO "identity"."identity"
  (branch_id, projection_hash, id, public_key, type_, identity_profile_id)
VALUES
  ($1, $2, $3, $4, 'human', $5);
""".strip(),
        branch_id,
        projection_hash,
        identity_id,
        public_key,
        identity_profile_id,
    )


async def _search_identity_profiles(
    *,
    conn: object,
    query: str,
    excluded_identity_ids: list[UUID],
    result_count: int,
    min_similarity: float,
) -> list[dict[str, object]]:
    rows = await conn.fetch(
        """
WITH ranked AS (
  SELECT
    i.id AS identity_id,
    p.id AS identity_profile_id,
    p.public_handle,
    p.display_name,
    p.full_name,
    p.country_code,
    p.language_code,
    p.bio,
    GREATEST(
      similarity(p.public_handle, $1),
      similarity(p.display_name, $1),
      similarity(p.full_name, $1),
      similarity(COALESCE(p.bio, ''), $1)
    ) AS search_rank
  FROM "identity"."identity_profile" p
  JOIN "identity"."identity" i
    ON i.branch_id = p.branch_id
   AND i.projection_hash = p.projection_hash
   AND i.identity_profile_id = p.id
  WHERE NOT (i.id = ANY($2::uuid[]))
)
SELECT *
FROM ranked
WHERE search_rank >= $3
ORDER BY search_rank DESC, public_handle ASC
LIMIT $4;
""".strip(),
        query,
        excluded_identity_ids,
        min_similarity,
        result_count,
    )
    return [dict(row) for row in rows]


@pytest.mark.asyncio
@pytest.mark.db
async def test_identity_profile_search_db() -> None:
    db_admin_url = os.getenv("AWARE_DB_TEST_ADMIN_URL") or os.getenv(
        "AWARE_DB_TEST_URL"
    )
    bootstrap_enabled = bool(os.getenv("AWARE_DB_TEST_BOOTSTRAP"))
    bootstrap_url = os.getenv("AWARE_DB_TEST_BOOTSTRAP_URL") or os.getenv(
        "AWARE_DB_TEST_URL"
    )
    if not db_admin_url and not (bootstrap_enabled and bootstrap_url):
        raise RuntimeError(
            "AWARE_DB_TEST_ADMIN_URL is required for DB-backed identity proof "
            "(or set AWARE_DB_TEST_BOOTSTRAP=1 with AWARE_DB_TEST_BOOTSTRAP_URL)."
        )

    try:
        import asyncpg
    except ModuleNotFoundError as exc:
        raise RuntimeError("Identity DB proofs require asyncpg.") from exc

    repo_root = REPO_ROOT

    from aware_identity_ontology.stable_ids import (
        stable_identity_id,
        stable_identity_profile_id,
    )

    env_id, ocg_hash = _manifest_identity(_identity_runtime_manifest_path(repo_root))
    sql_roots = _identity_db_sql_roots(repo_root)

    projection_hash = "sha256:test:identity:profile-search"
    public_key_a = f"ed25519:{'11' * 32}"
    identity_a = stable_identity_id(public_key=public_key_a, type="human")
    profile_a = stable_identity_profile_id(public_handle="luis")
    public_key_b = f"ed25519:{'22' * 32}"
    identity_b = stable_identity_id(public_key=public_key_b, type="human")
    profile_b = stable_identity_profile_id(public_handle="alice")

    async with db_test_database(admin_url=db_admin_url) as db_url:
        conn = await asyncpg.connect(db_url)
        try:
            for extension in _required_postgres_extensions_for_module(
                repo_root=repo_root, module_id="identity"
            ):
                await conn.execute(
                    "CREATE EXTENSION IF NOT EXISTS "
                    f"{_quote_postgres_extension_name(extension)};"
                )

            from aware_orm.db.boot import ensure_db_schema_installed_multi

            await ensure_db_schema_installed_multi(
                connection=conn,
                sql_roots=sql_roots,
                ocg_hash=ocg_hash,
            )

            await _insert_identity_profile(
                conn=conn,
                branch_id=identity_a,
                projection_hash=projection_hash,
                identity_id=identity_a,
                identity_profile_id=profile_a,
                public_key=public_key_a,
                public_handle="luis",
                display_name="Luis",
                full_name="Luis Aware",
                bio="Canonical year",
            )
            await _insert_identity_profile(
                conn=conn,
                branch_id=identity_b,
                projection_hash=projection_hash,
                identity_id=identity_b,
                identity_profile_id=profile_b,
                public_key=public_key_b,
                public_handle="alice",
                display_name="Alice",
                full_name="Alice Example",
                bio="Hello world",
            )

            results = await _search_identity_profiles(
                conn=conn,
                query="lui",
                excluded_identity_ids=[],
                result_count=10,
                min_similarity=0.1,
            )
            assert any(
                row["public_handle"] == "luis"
                and row["identity_id"] == identity_a
                and row["identity_profile_id"] == profile_a
                and float(row["search_rank"]) >= 0.1
                for row in results
            )

            excluded = await _search_identity_profiles(
                conn=conn,
                query="lui",
                excluded_identity_ids=[identity_a],
                result_count=10,
                min_similarity=0.1,
            )
            assert all(row["identity_id"] != identity_a for row in excluded)
        finally:
            await conn.close()
