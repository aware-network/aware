import json
from pathlib import Path
from uuid import uuid4

import pytest

from aware_orm.session import Session
from aware_orm.helpers import get_main_branch_id


@pytest.fixture()
def fs_runtime_dir(tmp_path, monkeypatch):
    """Isolate filesystem backend writes to a temporary directory."""
    monkeypatch.setenv("AWARE_PERSISTENCE_BACKEND", "fs")

    aware_root = tmp_path / "aware_root"
    (aware_root / ".aware").mkdir(parents=True, exist_ok=True)
    (aware_root / "pyproject.toml").write_text('[tool.poetry]\nname = "aware"\n', encoding="utf-8")

    def _fake_find_root():
        return aware_root

    monkeypatch.setattr("aware_orm.session.backends.fs_backend.find_aware_root", _fake_find_root)

    try:
        yield aware_root / ".aware" / "runtime" / "orm"
    finally:
        monkeypatch.delenv("AWARE_PERSISTENCE_BACKEND", raising=False)


@pytest.mark.asyncio
async def test_fs_backend_insert_update_delete(fs_runtime_dir: Path):
    session = Session(skip_db=True)
    branch_id = str(get_main_branch_id())

    # INSERT
    record_id = str(uuid4())
    insert_sql = (
        "INSERT INTO interface.interface_identity " "(id, interface_id, identity_id, branch_id) VALUES ($1, $2, $3, $4)"
    )
    session.add_insert(insert_sql, (record_id, str(uuid4()), str(uuid4()), branch_id))
    await session.commit()

    record_path = fs_runtime_dir / "interface" / "interface_identity" / branch_id / f"{record_id}.json"
    assert record_path.exists(), "Insert should create JSON record"
    payload = json.loads(record_path.read_text(encoding="utf-8"))
    assert payload["id"] == record_id

    # UPDATE
    update_sql = "UPDATE interface.interface_identity SET last_seen_at = $1, name = $2 WHERE id = $3"
    session.add_update(update_sql, ("timestamp", "Studio", record_id))
    await session.commit()

    payload = json.loads(record_path.read_text(encoding="utf-8"))
    assert payload["last_seen_at"] == "timestamp"
    assert payload["name"] == "Studio"

    # SELECT
    results = await session.execute_query(
        "SELECT * FROM interface.interface_identity WHERE id = $1",
        record_id,
    )
    assert len(results) == 1
    assert results[0]["id"] == record_id

    # DELETE
    delete_sql = "DELETE FROM interface.interface_identity WHERE id = $1"
    session.add_delete(delete_sql, (record_id,))
    await session.commit()
    assert not record_path.exists()


@pytest.mark.asyncio
async def test_fs_backend_filter_scan(fs_runtime_dir: Path):
    session = Session(skip_db=True)
    branch_id = str(get_main_branch_id())
    interface_id = str(uuid4())

    # create two records
    insert_sql = (
        "INSERT INTO interface.interface_session_network_binding "
        "(id, interface_identity_network_node_id, interface_session_id, branch_id) "
        "VALUES ($1, $2, $3, $4)"
    )
    rec_a = str(uuid4())
    rec_b = str(uuid4())
    shared_node = str(uuid4())
    session.add_insert(insert_sql, (rec_a, shared_node, str(uuid4()), branch_id))
    session.add_insert(insert_sql, (rec_b, shared_node, str(uuid4()), branch_id))
    await session.commit()

    # query using filters (EqFilter equivalent)
    results = await session.execute_query(
        "SELECT * FROM interface.interface_session_network_binding " "WHERE interface_identity_network_node_id = $1",
        shared_node,
    )
    ids = {row["id"] for row in results}
    assert {rec_a, rec_b} == ids


@pytest.mark.asyncio
async def test_fs_backend_supports_projector_upsert_and_composite_delete(
    fs_runtime_dir: Path,
):
    session = Session(skip_db=True)
    branch_id = str(get_main_branch_id())
    projection_hash = "sha256:test:projection"
    record_id = str(uuid4())

    upsert_sql = (
        'INSERT INTO "identity"."identity" '
        '("branch_id", "projection_hash", "id", "public_key", "type_") '
        "VALUES ($1, $2, $3, $4, $5) "
        'ON CONFLICT ("branch_id", "projection_hash", "id") '
        'DO UPDATE SET "public_key" = EXCLUDED."public_key", "type_" = EXCLUDED."type_"'
    )

    session.add_insert(
        upsert_sql,
        (
            branch_id,
            projection_hash,
            record_id,
            "ed25519:old",
            "agent",
        ),
    )
    await session.commit()

    record_path = fs_runtime_dir / "identity" / "identity" / branch_id / f"{record_id}.json"
    assert record_path.exists()
    payload = json.loads(record_path.read_text(encoding="utf-8"))
    assert payload["public_key"] == "ed25519:old"

    session.add_insert(
        upsert_sql,
        (
            branch_id,
            projection_hash,
            record_id,
            "ed25519:new",
            "agent",
        ),
    )
    await session.commit()

    payload = json.loads(record_path.read_text(encoding="utf-8"))
    assert payload["public_key"] == "ed25519:new"

    delete_sql = 'DELETE FROM "Identity"."Identity" ' 'WHERE "branch_id" = $1 AND "projection_hash" = $2 AND "id" = $3'
    session.add_delete(delete_sql, (branch_id, projection_hash, record_id))
    await session.commit()
    assert not record_path.exists()
