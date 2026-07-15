from typing import Any, Mapping
from uuid import UUID

from aware_meta.graph.support.member import GraphMember

from aware_meta_ontology.primitive.primitive import Primitive

from aware_meta.graph.instance.member_kind import ObjectInstanceGraphMemberKind


class PrimitiveMember(GraphMember[ObjectInstanceGraphMemberKind]):
    primitive: Primitive

    def get_id(self) -> UUID | None:
        return self.primitive.id

    def node_kind(self) -> ObjectInstanceGraphMemberKind:
        return ObjectInstanceGraphMemberKind.primitive

    def get_path_key(self) -> str:
        # Primitive identity is anchored by its owning Attribute; within that
        # context we treat the scalar payload as a single logical \"value\".
        # Using a stable literal here avoids coupling reconciliation to
        # storage-layer PrimitiveConfig identifiers.
        return "value"

    def get_content_fields(self) -> Mapping[str, Any]:
        # Primitive.value is stored as a Json object at the ORM layer.
        # For diffing we expose the logical scalar payload (if present)
        # so field changes see "old" vs "new" instead of the wrapper dict.
        raw_value = self.primitive.value
        scalar_value = raw_value.get("value") if isinstance(raw_value, dict) else raw_value
        return {
            "value": scalar_value,
        }

    # ---- Projections for content fields ----

    @property
    def value(self) -> Any:  # type: ignore[override]
        return self.primitive.value
