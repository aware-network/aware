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
from aware_orm.session.session import Session


def test_required_collection_defaults_to_empty_array_when_missing() -> None:
    # A required collection attribute may be omitted from the OIG snapshot when empty.
    # The projector must still stage a non-null value for NOT NULL array columns.
    cc_id = uuid4()
    attr_cfg_id = uuid4()
    instance_id = uuid4()

    plan = ProjectionPlan(
        projection_hash="sha256:test:proj",
        opg_name="test",
        dialect="postgres",
        tables=(
            ProjectionTablePlan(
                table_key="annotation.code_section_annotation_one_of",
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
                        column_name="attribute_names",
                        source="attribute",
                        attribute_config_id=attr_cfg_id,
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
            type_descriptor=SimpleNamespace(kind=AttributeTypeDescriptorKind.collection)
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
    assert params[3] == []
