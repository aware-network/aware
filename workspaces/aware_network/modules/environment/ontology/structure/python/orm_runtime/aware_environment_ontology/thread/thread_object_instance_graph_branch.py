from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_meta_ontology.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity


class ThreadObjectInstanceGraphBranch(ORMModel):
    # Relationships
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None, exclude=True)
    object_instance_graph_identity: ObjectInstanceGraphIdentity | None = Field(
        default=None,
        exclude=True,
        description="Cross-OPG: target lane branch id for resolving `object_instance_graph_branch`.\nWhy:\n- `object_instance_graph_branch_id` (OIGB id) is stable but not invertible, so the UI\ncannot derive the OIGI lane branch id from it.\n- Runtime sets this from the domain lane HEAD `object_instance_graph_id` (commit-first).\nHard rule:\n- This must never encode `projection_hash` (internal lane coordinate).",
    )

    # Attributes
    is_active: bool = Field(default=True)
    title: str | None = Field(default=None)

    # Foreign Keys
    thread_id: UUID = Field(description="Foreign key for Thread.thread_object_instance_graph_branches")
    object_instance_graph_branch_id: UUID = Field(
        description="Foreign key for ThreadObjectInstanceGraphBranch.object_instance_graph_branch"
    )
    object_instance_graph_identity_id: UUID | None = Field(
        default=None, description="Foreign key for ThreadObjectInstanceGraphBranch.object_instance_graph_identity"
    )

    @classmethod
    async def create_for_lane(
        cls,
        thread_id: UUID,
        domain_branch_id: UUID,
        projection_hash: str,
        title: str | None = None,
        is_active: bool = True,
    ) -> ThreadObjectInstanceGraphBranch:
        """
        Create an attachment edge for an existing global lane (branch_id, projection_hash).

        Canonical v0 intent:
        - OS lane metadata only: creates deterministic Branch/Lane/OIGB objects if missing.
        - Does not author domain commits; lane HEAD comes from the commit store (SSOT).
        """

        payload = {
            "thread_id": thread_id,
            "domain_branch_id": domain_branch_id,
            "projection_hash": projection_hash,
            "title": title,
            "is_active": is_active,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_for_lane", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ThreadObjectInstanceGraphBranch):
            return value
        return ThreadObjectInstanceGraphBranch.validate_invocation_value(value)

    async def backfill_identity_anchor(
        self, object_instance_graph_identity_id: UUID
    ) -> ThreadObjectInstanceGraphBranch:
        """
        Backfill `object_instance_graph_identity_id` for legacy associations.

        Why:
        - Older OS commits were created before the environment projection included the
          `object_instance_graph_identity` portal, so the association may be missing the
          OIGI anchor on replay/materialization.

        Canonical rules:
        - Mutates only this association instance (mutate-self-only invariant).
        - Idempotent: no-op when already set.
        """

        payload = {"object_instance_graph_identity_id": object_instance_graph_identity_id}
        result = await invoke_instance(orm_model=self, function_name="backfill_identity_anchor", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ThreadObjectInstanceGraphBranch):
            return value
        return ThreadObjectInstanceGraphBranch.validate_invocation_value(value)


class ThreadObjectInstanceGraphBranchCreateForLaneInput(BaseModel):
    thread_id: UUID
    domain_branch_id: UUID
    projection_hash: str
    title: str | None = Field(default=None)
    is_active: bool = Field(default=True)


class ThreadObjectInstanceGraphBranchCreateForLaneOutput(BaseModel):
    value: ThreadObjectInstanceGraphBranch


class ThreadObjectInstanceGraphBranchBackfillIdentityAnchorInput(BaseModel):
    object_instance_graph_identity_id: UUID


class ThreadObjectInstanceGraphBranchBackfillIdentityAnchorOutput(BaseModel):
    value: ThreadObjectInstanceGraphBranch


FUNCTIONS = {
    "ThreadObjectInstanceGraphBranch": {
        "create_for_lane": {
            "canonical": {
                "name": "create_for_lane",
                "description": "Create an attachment edge for an existing global lane (branch_id, projection_hash).\n\nCanonical v0 intent:\n- OS lane metadata only: creates deterministic Branch/Lane/OIGB objects if missing.\n- Does not author domain commits; lane HEAD comes from the commit store (SSOT).",
                "is_constructor": True,
            },
            "input": ThreadObjectInstanceGraphBranchCreateForLaneInput,
            "output": ThreadObjectInstanceGraphBranchCreateForLaneOutput,
        },
        "backfill_identity_anchor": {
            "canonical": {
                "name": "backfill_identity_anchor",
                "description": "Backfill `object_instance_graph_identity_id` for legacy associations.\n\nWhy:\n- Older OS commits were created before the environment projection included the\n  `object_instance_graph_identity` portal, so the association may be missing the\n  OIGI anchor on replay/materialization.\n\nCanonical rules:\n- Mutates only this association instance (mutate-self-only invariant).\n- Idempotent: no-op when already set.",
                "is_constructor": False,
            },
            "input": ThreadObjectInstanceGraphBranchBackfillIdentityAnchorInput,
            "output": ThreadObjectInstanceGraphBranchBackfillIdentityAnchorOutput,
        },
    },
}

__all__ = [
    "ThreadObjectInstanceGraphBranch",
    "ThreadObjectInstanceGraphBranchCreateForLaneInput",
    "ThreadObjectInstanceGraphBranchCreateForLaneOutput",
    "ThreadObjectInstanceGraphBranchBackfillIdentityAnchorInput",
    "ThreadObjectInstanceGraphBranchBackfillIdentityAnchorOutput",
    "FUNCTIONS",
]
