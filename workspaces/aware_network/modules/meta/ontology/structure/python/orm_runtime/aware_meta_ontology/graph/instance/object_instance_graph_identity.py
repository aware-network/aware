from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import ObjectInstanceGraphChangeType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_instance_identity import ClassInstanceIdentity
    from aware_meta_ontology.class_.class_instance_relationship_identity import ClassInstanceRelationshipIdentity
    from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
    from aware_meta_ontology.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_meta_ontology.graph.instance.object_instance_graph_change import ObjectInstanceGraphChange
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class ObjectInstanceGraphIdentity(ORMModel):
    """
    Stable identity for a worldline's ObjectInstanceGraph (instance identity).
    IMPORTANT:
    - This is NOT a snapshot graph (no hash, no class instances).
    - Domain commits reference this identity via `object_instance_graph_id`.
    - Snapshots are derived from commits + (OCG, OPG) at materialization time.
    """

    # Relationships
    object_instance_graph: ObjectInstanceGraph | None = Field(default=None, exclude=True)
    class_instance_identities: list[ClassInstanceIdentity] = Field(default_factory=list)
    class_instance_relationship_identities: list[ClassInstanceRelationshipIdentity] = Field(default_factory=list)
    object_instance_graph_changes: list[ObjectInstanceGraphChange] = Field(default_factory=list, exclude=True)
    object_instance_graph_branches: list[ObjectInstanceGraphBranch] = Field(default_factory=list, exclude=True)
    object_instance_graph_commits: list[ObjectInstanceGraphCommit] = Field(default_factory=list, exclude=True)

    # Attributes
    label: str | None = Field(default=None)

    # Foreign Keys
    object_projection_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphIdentity.object_instance_graph_identities"
    )
    object_instance_graph_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphIdentity.object_instance_graph"
    )

    async def upsert_history_from_lane_head(
        self,
        domain_branch_id: UUID,
        domain_projection_hash: str,
        lane_id: UUID,
        head_commit_id: UUID,
        branch_is_main: bool = False,
        branch_name: str | None = None,
    ) -> ObjectInstanceGraphIdentity:
        """
        Upsert the SSOT history plane for a domain lane head.

        Writes (in the `object_instance_graph_identity` projection):
        - OIGB (deterministic id) anchored to this OIGI
        - Branch + Lane(lane_hash=domain_projection_hash) with updated head_commit pointer
        - Commit DAG objects + OIGCommit wrappers for the head commit and any missing ancestors

        IMPORTANT:
        - Reads domain commit payloads from the node commit store (commit-first invariant).
        - Never authors domain commits.
        """

        payload = {
            "domain_branch_id": domain_branch_id,
            "domain_projection_hash": domain_projection_hash,
            "lane_id": lane_id,
            "head_commit_id": head_commit_id,
            "branch_is_main": branch_is_main,
            "branch_name": branch_name,
        }
        result = await invoke_instance(orm_model=self, function_name="upsert_history_from_lane_head", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectInstanceGraphIdentity):
            return value
        return ObjectInstanceGraphIdentity.validate_invocation_value(value)

    async def create_class_instance_identity(
        self, class_instance_id: UUID, label: str | None = None
    ) -> ClassInstanceIdentity:
        """
        Create one deterministic ClassInstanceIdentity under this ObjectInstanceGraphIdentity.

        Contract:
        - Parent-owned propagation edge for projection inclusion (`OIGI -> CII`).
        - Idempotent per `(object_instance_graph_identity_id, class_instance_id)`.
        """

        payload = {"class_instance_id": class_instance_id, "label": label}
        result = await invoke_instance(orm_model=self, function_name="create_class_instance_identity", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.class_.class_instance_identity import ClassInstanceIdentity

        if isinstance(value, ClassInstanceIdentity):
            return value
        return ClassInstanceIdentity.validate_invocation_value(value)

    async def create_class_instance_relationship_identity(
        self, class_instance_relationship_id: UUID, label: str | None = None
    ) -> ClassInstanceRelationshipIdentity:
        """
        Create one deterministic ClassInstanceRelationshipIdentity under this ObjectInstanceGraphIdentity.

        Contract:
        - Parent-owned propagation edge for projection inclusion (`OIGI -> CIRI`).
        - Idempotent per `(object_instance_graph_identity_id, class_instance_relationship_id)`.
        """

        payload = {"class_instance_relationship_id": class_instance_relationship_id, "label": label}
        result = await invoke_instance(
            orm_model=self, function_name="create_class_instance_relationship_identity", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.class_.class_instance_relationship_identity import ClassInstanceRelationshipIdentity

        if isinstance(value, ClassInstanceRelationshipIdentity):
            return value
        return ClassInstanceRelationshipIdentity.validate_invocation_value(value)

    async def create_change(self, change_id: UUID, type: ObjectInstanceGraphChangeType) -> ObjectInstanceGraphChange:
        """
        Create one deterministic ObjectInstanceGraphChange under this ObjectInstanceGraphIdentity.

        Contract:
        - Parent-owned propagation edge for history-plane inclusion (`OIGI -> OIGChange`).
        - The change payload still targets the canonical OIG worldline referenced by this OIGI.
        - Deterministic identity resolves from `(object_instance_graph_identity_id via path, change_id)`.
        """

        payload = {"change_id": change_id, "type": type}
        result = await invoke_instance(orm_model=self, function_name="create_change", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.instance.object_instance_graph_change import ObjectInstanceGraphChange

        if isinstance(value, ObjectInstanceGraphChange):
            return value
        return ObjectInstanceGraphChange.validate_invocation_value(value)

    @classmethod
    async def create_via_object_projection_graph_identity(
        cls, object_projection_graph_identity_id: UUID, object_instance_graph_id: UUID, label: str | None = None
    ) -> ObjectInstanceGraphIdentity:
        """
        Create deterministic ObjectInstanceGraphIdentity for one ObjectInstanceGraph worldline.

        Contract:
        - `ObjectInstanceGraphIdentity.id` is compiler/runtime derived from
          `(object_projection_graph_identity_id via path, object_instance_graph_id)`.
        - `object_instance_graph` is a boundary pointer to the canonical OIG worldline and
          must not be traversed inside the identity projection payload.
        """

        payload = {
            "object_projection_graph_identity_id": object_projection_graph_identity_id,
            "object_instance_graph_id": object_instance_graph_id,
            "label": label,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_object_projection_graph_identity", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectInstanceGraphIdentity):
            return value
        return ObjectInstanceGraphIdentity.validate_invocation_value(value)


class ObjectInstanceGraphIdentityUpsertHistoryFromLaneHeadInput(BaseModel):
    domain_branch_id: UUID
    domain_projection_hash: str
    lane_id: UUID
    head_commit_id: UUID
    branch_is_main: bool = Field(default=False)
    branch_name: str | None = Field(default=None)


class ObjectInstanceGraphIdentityUpsertHistoryFromLaneHeadOutput(BaseModel):
    value: ObjectInstanceGraphIdentity


class ObjectInstanceGraphIdentityCreateClassInstanceIdentityInput(BaseModel):
    class_instance_id: UUID
    label: str | None = Field(default=None)


class ObjectInstanceGraphIdentityCreateClassInstanceIdentityOutput(BaseModel):
    value: ClassInstanceIdentity


class ObjectInstanceGraphIdentityCreateClassInstanceRelationshipIdentityInput(BaseModel):
    class_instance_relationship_id: UUID
    label: str | None = Field(default=None)


class ObjectInstanceGraphIdentityCreateClassInstanceRelationshipIdentityOutput(BaseModel):
    value: ClassInstanceRelationshipIdentity


class ObjectInstanceGraphIdentityCreateChangeInput(BaseModel):
    change_id: UUID
    type: ObjectInstanceGraphChangeType


class ObjectInstanceGraphIdentityCreateChangeOutput(BaseModel):
    value: ObjectInstanceGraphChange


class ObjectInstanceGraphIdentityCreateViaObjectProjectionGraphIdentityInput(BaseModel):
    object_projection_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphIdentity.object_instance_graph_identities"
    )
    object_instance_graph_id: UUID
    label: str | None = Field(default=None)


class ObjectInstanceGraphIdentityCreateViaObjectProjectionGraphIdentityOutput(BaseModel):
    value: ObjectInstanceGraphIdentity


FUNCTIONS = {
    "ObjectInstanceGraphIdentity": {
        "upsert_history_from_lane_head": {
            "canonical": {
                "name": "upsert_history_from_lane_head",
                "description": "Upsert the SSOT history plane for a domain lane head.\n\nWrites (in the `object_instance_graph_identity` projection):\n- OIGB (deterministic id) anchored to this OIGI\n- Branch + Lane(lane_hash=domain_projection_hash) with updated head_commit pointer\n- Commit DAG objects + OIGCommit wrappers for the head commit and any missing ancestors\n\nIMPORTANT:\n- Reads domain commit payloads from the node commit store (commit-first invariant).\n- Never authors domain commits.",
                "is_constructor": False,
            },
            "input": ObjectInstanceGraphIdentityUpsertHistoryFromLaneHeadInput,
            "output": ObjectInstanceGraphIdentityUpsertHistoryFromLaneHeadOutput,
        },
        "create_class_instance_identity": {
            "canonical": {
                "name": "create_class_instance_identity",
                "description": "Create one deterministic ClassInstanceIdentity under this ObjectInstanceGraphIdentity.\n\nContract:\n- Parent-owned propagation edge for projection inclusion (`OIGI -> CII`).\n- Idempotent per `(object_instance_graph_identity_id, class_instance_id)`.",
                "is_constructor": False,
            },
            "input": ObjectInstanceGraphIdentityCreateClassInstanceIdentityInput,
            "output": ObjectInstanceGraphIdentityCreateClassInstanceIdentityOutput,
        },
        "create_class_instance_relationship_identity": {
            "canonical": {
                "name": "create_class_instance_relationship_identity",
                "description": "Create one deterministic ClassInstanceRelationshipIdentity under this ObjectInstanceGraphIdentity.\n\nContract:\n- Parent-owned propagation edge for projection inclusion (`OIGI -> CIRI`).\n- Idempotent per `(object_instance_graph_identity_id, class_instance_relationship_id)`.",
                "is_constructor": False,
            },
            "input": ObjectInstanceGraphIdentityCreateClassInstanceRelationshipIdentityInput,
            "output": ObjectInstanceGraphIdentityCreateClassInstanceRelationshipIdentityOutput,
        },
        "create_change": {
            "canonical": {
                "name": "create_change",
                "description": "Create one deterministic ObjectInstanceGraphChange under this ObjectInstanceGraphIdentity.\n\nContract:\n- Parent-owned propagation edge for history-plane inclusion (`OIGI -> OIGChange`).\n- The change payload still targets the canonical OIG worldline referenced by this OIGI.\n- Deterministic identity resolves from `(object_instance_graph_identity_id via path, change_id)`.",
                "is_constructor": False,
            },
            "input": ObjectInstanceGraphIdentityCreateChangeInput,
            "output": ObjectInstanceGraphIdentityCreateChangeOutput,
        },
        "create_via_object_projection_graph_identity": {
            "canonical": {
                "name": "create_via_object_projection_graph_identity",
                "description": "Create deterministic ObjectInstanceGraphIdentity for one ObjectInstanceGraph worldline.\n\nContract:\n- `ObjectInstanceGraphIdentity.id` is compiler/runtime derived from\n  `(object_projection_graph_identity_id via path, object_instance_graph_id)`.\n- `object_instance_graph` is a boundary pointer to the canonical OIG worldline and\n  must not be traversed inside the identity projection payload.",
                "is_constructor": True,
            },
            "input": ObjectInstanceGraphIdentityCreateViaObjectProjectionGraphIdentityInput,
            "output": ObjectInstanceGraphIdentityCreateViaObjectProjectionGraphIdentityOutput,
        },
    },
}

__all__ = [
    "ObjectInstanceGraphIdentity",
    "ObjectInstanceGraphIdentityUpsertHistoryFromLaneHeadInput",
    "ObjectInstanceGraphIdentityUpsertHistoryFromLaneHeadOutput",
    "ObjectInstanceGraphIdentityCreateClassInstanceIdentityInput",
    "ObjectInstanceGraphIdentityCreateClassInstanceIdentityOutput",
    "ObjectInstanceGraphIdentityCreateClassInstanceRelationshipIdentityInput",
    "ObjectInstanceGraphIdentityCreateClassInstanceRelationshipIdentityOutput",
    "ObjectInstanceGraphIdentityCreateChangeInput",
    "ObjectInstanceGraphIdentityCreateChangeOutput",
    "ObjectInstanceGraphIdentityCreateViaObjectProjectionGraphIdentityInput",
    "ObjectInstanceGraphIdentityCreateViaObjectProjectionGraphIdentityOutput",
    "FUNCTIONS",
]
