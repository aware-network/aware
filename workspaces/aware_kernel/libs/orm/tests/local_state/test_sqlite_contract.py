from __future__ import annotations

from pathlib import Path

from pydantic import Field

from aware_orm.local_state.sqlite import (
    SQLiteOrmModelTable,
    SQLiteOrmPredicate,
    SQLiteOrmSchema,
    SQLiteOrmSchemaContract,
    SQLiteOrmSchemaContractDescriptor,
    inspect_sqlite_orm_schema_health,
    load_sqlite_orm_schema_contract_descriptor,
    open_sqlite_orm_memory_connection,
)
from aware_orm.models.orm_model import ORMModel


class LocalStateContractRow(ORMModel):
    name: str
    payload: dict[str, object] = Field(default_factory=dict)


def _write_contract(tmp_path: Path) -> SQLiteOrmSchemaContract:
    schema_root = tmp_path / "sqlite" / "default"
    schema_root.mkdir(parents=True)
    _ = (schema_root / "local_state_contract_row.sql").write_text(
        """
CREATE TABLE local_state_contract_row (
  id TEXT PRIMARY KEY NOT NULL,
  name TEXT NOT NULL,
  payload TEXT NOT NULL
);

CREATE UNIQUE INDEX idx_local_state_contract_row_name
ON local_state_contract_row (name);
""".strip()
        + "\n",
        encoding="utf-8",
    )
    table = SQLiteOrmModelTable(
        table="local_state_contract_row",
        columns=("id", "name", "payload"),
        model_type=LocalStateContractRow,
        json_columns=frozenset({"payload"}),
    )
    return SQLiteOrmSchemaContract(
        schema_contract="aware.test.local_state.sqlite",
        schema_version=1,
        schema=SQLiteOrmSchema(
            schema_path=schema_root / "local_state_contract_row.sql",
            tables=(table,),
        ),
        expected_storage_indexes={
            "local_state_contract_row": ((True, ("name",)),),
        },
    )


def test_sqlite_orm_schema_contract_installs_and_inspects_health(
    tmp_path: Path,
) -> None:
    contract = _write_contract(tmp_path)

    with open_sqlite_orm_memory_connection() as connection:
        missing_health = inspect_sqlite_orm_schema_health(
            connection=connection,
            contract=contract,
        )
        assert missing_health.status == "schema_drift"
        assert missing_health.tables[0].status == "missing"

        contract.ensure_installed(connection)
        health = contract.inspect_health(connection)

    assert health.schema_contract == "aware.test.local_state.sqlite"
    assert health.schema_version == 1
    assert health.status == "ok"
    assert health.table_count == 1
    assert health.healthy_table_count == 1
    assert health.storage_index_coverage is True
    assert health.issues == ()


def test_sqlite_orm_schema_repair_recreates_table_with_existing_generated_index(
    tmp_path: Path,
) -> None:
    contract = _write_contract(tmp_path)
    table = contract.schema.tables[0]
    assert isinstance(table, SQLiteOrmModelTable)
    legacy_id = "a7a0db1d-4f62-4810-8d96-1f76c9fa23f2"

    with open_sqlite_orm_memory_connection() as connection:
        _ = connection.executescript(
            """
CREATE TABLE local_state_contract_row (
  id TEXT PRIMARY KEY NOT NULL,
  name TEXT NOT NULL,
  payload TEXT NOT NULL,
  retired_column TEXT
);

CREATE UNIQUE INDEX idx_local_state_contract_row_name
ON local_state_contract_row (name);
""".strip()
        )
        _ = connection.execute(
            """
            INSERT INTO local_state_contract_row (
              id,
              name,
              payload,
              retired_column
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                legacy_id,
                "workspace-sdk",
                '{"state":"legacy"}',
                "retired",
            ),
        )

        contract.ensure_installed(connection)
        health = contract.inspect_health(connection)
        loaded = table.select_one(
            connection,
            predicates=(SQLiteOrmPredicate("name", "workspace-sdk"),),
        )

    assert health.status == "ok"
    assert health.storage_index_coverage is True
    assert loaded is not None
    assert str(loaded.id) == legacy_id
    assert loaded.payload == {"state": "legacy"}


def test_sqlite_orm_schema_contract_repairs_missing_storage_index(
    tmp_path: Path,
) -> None:
    contract = _write_contract(tmp_path)
    table = contract.schema.tables[0]
    assert isinstance(table, SQLiteOrmModelTable)
    existing_id = "6a59eaf8-4f9e-45a7-a02e-4d16084d32dd"

    with open_sqlite_orm_memory_connection() as connection:
        _ = connection.executescript(
            """
CREATE TABLE local_state_contract_row (
  id TEXT PRIMARY KEY NOT NULL,
  name TEXT NOT NULL,
  payload TEXT NOT NULL
);
""".strip()
        )
        _ = connection.execute(
            """
            INSERT INTO local_state_contract_row (id, name, payload)
            VALUES (?, ?, ?)
            """,
            (
                existing_id,
                "workspace-sdk",
                '{"state":"missing-index"}',
            ),
        )

        before = contract.inspect_health(connection)
        contract.ensure_installed(connection)
        after = contract.inspect_health(connection)
        loaded = table.select_one(
            connection,
            predicates=(SQLiteOrmPredicate("name", "workspace-sdk"),),
        )

    assert before.status == "schema_drift"
    assert before.storage_index_coverage is False
    assert after.status == "ok"
    assert after.storage_index_coverage is True
    assert loaded is not None
    assert str(loaded.id) == existing_id
    assert loaded.payload == {"state": "missing-index"}


def test_sqlite_orm_model_table_round_trips_model_json(
    tmp_path: Path,
) -> None:
    contract = _write_contract(tmp_path)
    table = contract.schema.tables[0]
    assert isinstance(table, SQLiteOrmModelTable)
    row = LocalStateContractRow(
        name="workspace-sdk",
        payload={"state": "dirty", "count": 2},
    )

    with open_sqlite_orm_memory_connection() as connection:
        contract.ensure_installed(connection)
        table.replace(connection, row)
        loaded = table.select_one(
            connection,
            predicates=(SQLiteOrmPredicate("name", "workspace-sdk"),),
        )

    assert loaded is not None
    assert loaded.id == row.id
    assert loaded.name == "workspace-sdk"
    assert loaded.payload == {"state": "dirty", "count": 2}


def test_sqlite_orm_schema_contract_descriptor_binds_generated_models(
    tmp_path: Path,
) -> None:
    contract_path = tmp_path / "sqlite_orm_schema_contract.json"
    _ = contract_path.write_text(
        """
{
  "schema": "aware.orm.local_state.sqlite.schema_contract.v1",
  "schema_contract": "aware.test.local_state.sqlite",
  "schema_version": 1,
  "tables": [
    {
      "table": "local_state_contract_row",
      "columns": ["id", "name", "payload"],
      "json_columns": ["payload"],
      "storage_indexes": [
        {"unique": true, "columns": ["name"]}
      ]
    }
  ]
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    descriptor = load_sqlite_orm_schema_contract_descriptor(contract_path)
    model_tables = descriptor.model_tables(
        {"local_state_contract_row": LocalStateContractRow}
    )

    assert isinstance(descriptor, SQLiteOrmSchemaContractDescriptor)
    assert descriptor.schema_contract == "aware.test.local_state.sqlite"
    assert descriptor.expected_storage_indexes == {
        "local_state_contract_row": ((True, ("name",)),)
    }
    assert model_tables[0].columns == ("id", "name", "payload")
    assert model_tables[0].json_columns == frozenset({"payload"})
