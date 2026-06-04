from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from pydantic import Field, ValidationError

from aware_orm.models.orm_model import ORMModel


class _InvocationTarget(ORMModel):
    name: str


class _InvocationEdge(ORMModel):
    handle: str
    target: _InvocationTarget
    target_id: UUID | None = Field(default=None)


class _NestedInvocationTarget(ORMModel):
    leaf: _InvocationTarget
    leaf_id: UUID | None = Field(default=None)


class _NestedInvocationEdge(ORMModel):
    handle: str
    target: _NestedInvocationTarget
    target_id: UUID | None = Field(default=None)


class _InvocationEdgeListOwner(ORMModel):
    handle: str
    edges: list[_InvocationEdge] = Field(default_factory=list)


def test_validate_invocation_value_accepts_fk_backed_missing_reference() -> None:
    target_id = uuid4()

    edge = _InvocationEdge.validate_invocation_value(
        {
            "id": uuid4(),
            "handle": "edge",
            "target_id": target_id,
        }
    )

    assert edge.handle == "edge"
    assert edge.target_id == target_id
    assert edge.target is None


def test_validate_invocation_value_does_not_hide_non_reference_missing_fields() -> None:
    with pytest.raises(ValidationError):
        _ = _InvocationEdge.validate_invocation_value(
            {
                "id": uuid4(),
                "target_id": uuid4(),
            }
        )


def test_validate_invocation_value_accepts_fk_backed_nested_missing_reference() -> None:
    target_id = uuid4()
    leaf_id = uuid4()

    edge = _NestedInvocationEdge.validate_invocation_value(
        {
            "id": uuid4(),
            "handle": "edge",
            "target_id": target_id,
            "target": {
                "id": target_id,
                "leaf_id": leaf_id,
            },
        }
    )

    assert edge.handle == "edge"
    assert edge.target_id == target_id
    assert edge.target is None


def test_validate_invocation_value_accepts_fk_backed_missing_reference_in_edge_list() -> None:
    target_id = uuid4()

    owner = _InvocationEdgeListOwner.validate_invocation_value(
        {
            "id": uuid4(),
            "handle": "owner",
            "edges": [
                {
                    "id": uuid4(),
                    "handle": "edge",
                    "target_id": target_id,
                }
            ],
        }
    )

    assert owner.handle == "owner"
    assert len(owner.edges) == 1
    assert owner.edges[0].handle == "edge"
    assert owner.edges[0].target_id == target_id
    assert owner.edges[0].target is None
