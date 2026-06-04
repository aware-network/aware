from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_orm.runtime.bundle_sql_metadata import install_sql_metadata_from_bindings_payload
from aware_orm.runtime.sql_metadata import (
    clear_sql_metadata_registry,
    get_sql_metadata_for_class,
)


def _make_bindings_payload(
    *,
    base_path: Path,
    class_fqn: str,
    class_config_id: UUID,
    table_name: str,
    identity_key: str = "canonical_entity_id",
) -> bytes:
    _ = base_path
    bindings = {
        "version": "1.0.0",
        "planner_version": "test",
        "bindings": [
            {
                "class_fqn": class_fqn,
                identity_key: str(class_config_id),
                "sql_mapping": [
                    {
                        "attribute_name": "id",
                        "persisted": True,
                        "table_schema": "public",
                        "table_name": table_name,
                        "column_name": "id",
                        "fk_owner": None,
                        "fk_columns": [],
                        "join_chain": [],
                    }
                ],
            }
        ],
    }
    return json.dumps(bindings).encode("utf-8")


@pytest.mark.parametrize(
    "identity_key",
    ("canonical_entity_id", "canonical_class_config_id"),
)
def test_install_sql_metadata_from_bundle_merges_registries(
    tmp_path: Path,
    identity_key: str,
) -> None:
    clear_sql_metadata_registry()

    a_id = uuid4()
    b_id = uuid4()
    bundle_a = _make_bindings_payload(
        base_path=tmp_path,
        class_fqn="pkg.A",
        class_config_id=a_id,
        table_name="a",
        identity_key=identity_key,
    )
    bundle_b = _make_bindings_payload(
        base_path=tmp_path,
        class_fqn="pkg.B",
        class_config_id=b_id,
        table_name="b",
        identity_key=identity_key,
    )

    res_a = install_sql_metadata_from_bindings_payload(bundle_a, strict=True)
    assert res_a.installed == 1
    meta_a = get_sql_metadata_for_class("pkg.A")
    assert meta_a is not None
    assert meta_a.class_config_id == a_id
    assert get_sql_metadata_for_class("pkg.B") is None

    res_b = install_sql_metadata_from_bindings_payload(bundle_b, strict=True)
    assert res_b.installed == 1
    meta_b = get_sql_metadata_for_class("pkg.B")
    assert meta_b is not None
    assert meta_b.class_config_id == b_id
    assert get_sql_metadata_for_class("pkg.A") is not None
