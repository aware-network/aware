from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from aware_history_ontology.change.change_enums import ChangeType
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)

from aware_orm.projection.plan import (
    ProjectionColumnPlan,
    ProjectionPlan,
    ProjectionTablePlan,
)
from aware_meta.graph.instance.orm_projector import stage_lane_projection_writes
from aware_orm.runtime.sql_metadata import (
    SQLRuntimeMetadata,
    clear_sql_metadata_registry,
    register_sql_metadata,
)
from aware_orm.session.session import Session


def test_required_mapping_defaults_to_json_string_when_column_is_text() -> None:
    cc_id = uuid4()
    attr_cfg_id = uuid4()
    instance_id = uuid4()

    plan = ProjectionPlan(
        projection_hash="sha256:test:proj",
        opg_name="test",
        dialect="postgres",
        tables=(
            ProjectionTablePlan(
                table_key="test.mapping_text",
                class_config_id=cc_id,
                primary_key=("branch_id", "projection_hash", "id"),
                columns=(
                    ProjectionColumnPlan(
                        column_name="branch_id", source="branch_id", nullable=False
                    ),
                    ProjectionColumnPlan(
                        column_name="projection_hash",
                        source="projection_hash",
                        nullable=False,
                    ),
                    ProjectionColumnPlan(column_name="id", source="id", nullable=False),
                    ProjectionColumnPlan(
                        column_name="payload",
                        source="attribute",
                        attribute_config_id=attr_cfg_id,
                        sql_type_hint="TEXT",
                        nullable=False,
                    ),
                ),
            ),
        ),
        associations=tuple(),
    )

    before_oig = SimpleNamespace(class_instances=[], class_instance_relationships=[])
    after_oig = SimpleNamespace(
        class_instances=[
            # Attribute is intentionally missing; projector must still emit a non-null value.
            SimpleNamespace(id=instance_id, class_config_id=cc_id, attributes=[]),
        ],
        class_instance_relationships=[],
    )

    changes = [
        SimpleNamespace(
            class_instance_changes=[
                SimpleNamespace(
                    class_instance_id=instance_id,
                    change=SimpleNamespace(type=ChangeType.create),
                )
            ],
            class_instance_relationship_changes=[],
        )
    ]

    branch_id = uuid4()
    session = Session(branch_id=branch_id, skip_db=False)

    attribute_configs_by_id = {
        attr_cfg_id: SimpleNamespace(
            type_descriptor=SimpleNamespace(kind=AttributeTypeDescriptorKind.mapping)
        )
    }

    stage_lane_projection_writes(
        session=session,
        plan=plan,
        branch_id=branch_id,
        projection_hash=plan.projection_hash,
        before_oig=before_oig,  # type: ignore[arg-type]
        after_oig=after_oig,  # type: ignore[arg-type]
        changes=changes,  # type: ignore[arg-type]
        enum_option_value_by_id={},
        attribute_configs_by_id=attribute_configs_by_id,  # type: ignore[arg-type]
    )

    assert len(session._pending_inserts) == 1
    _sql, params = session._pending_inserts[0]
    assert params[3] == "{}"


def test_default_projection_table_key_uses_unique_sql_runtime_metadata_schema() -> None:
    clear_sql_metadata_registry()
    cc_id = uuid4()
    instance_id = uuid4()

    register_sql_metadata(
        SQLRuntimeMetadata(
            class_config_id=cc_id,
            table_schema="service",
            table_name="service",
            column_by_attribute={"id": "id"},
            persisted_attributes=frozenset({"id"}),
            fk_owner_by_attribute={},
            fk_columns_by_attribute={},
            join_chain_by_attribute={},
        )
    )

    plan = ProjectionPlan(
        projection_hash="sha256:test:service",
        opg_name="service",
        dialect="postgres",
        tables=(
            ProjectionTablePlan(
                table_key="default.service",
                class_config_id=cc_id,
                primary_key=("branch_id", "projection_hash", "id"),
                columns=(
                    ProjectionColumnPlan(
                        column_name="branch_id", source="branch_id", nullable=False
                    ),
                    ProjectionColumnPlan(
                        column_name="projection_hash",
                        source="projection_hash",
                        nullable=False,
                    ),
                    ProjectionColumnPlan(column_name="id", source="id", nullable=False),
                ),
            ),
        ),
        associations=tuple(),
    )

    before_oig = SimpleNamespace(class_instances=[], class_instance_relationships=[])
    after_oig = SimpleNamespace(
        class_instances=[
            SimpleNamespace(id=instance_id, class_config_id=cc_id, attributes=[]),
        ],
        class_instance_relationships=[],
    )
    changes = [
        SimpleNamespace(
            class_instance_changes=[
                SimpleNamespace(
                    class_instance_id=instance_id,
                    change=SimpleNamespace(type=ChangeType.create),
                )
            ],
            class_instance_relationship_changes=[],
        )
    ]
    branch_id = uuid4()
    session = Session(branch_id=branch_id, skip_db=False)

    try:
        stage_lane_projection_writes(
            session=session,
            plan=plan,
            branch_id=branch_id,
            projection_hash=plan.projection_hash,
            before_oig=before_oig,  # type: ignore[arg-type]
            after_oig=after_oig,  # type: ignore[arg-type]
            changes=changes,  # type: ignore[arg-type]
            enum_option_value_by_id={},
            attribute_configs_by_id={},
        )
    finally:
        clear_sql_metadata_registry()

    assert len(session._pending_inserts) == 1
    sql, _params = session._pending_inserts[0]
    assert sql.startswith('INSERT INTO "service"."service"')
    assert not sql.startswith('INSERT INTO "default"."service"')
