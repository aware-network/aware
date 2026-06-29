from typing import Any, Mapping
from uuid import UUID

from aware_meta.graph.support.member import GraphMember

from aware_meta_ontology.attribute.attribute import Attribute

from aware_meta.graph.instance.member_kind import ObjectInstanceGraphMemberKind


class AttributeMember(GraphMember[ObjectInstanceGraphMemberKind]):
    """
    GraphMember wrapper for an Attribute entity.
    """

    attribute: Attribute

    def get_id(self) -> UUID | None:
        return self.attribute.id

    def node_kind(self) -> ObjectInstanceGraphMemberKind:
        return ObjectInstanceGraphMemberKind.attribute

    def get_path_key(self) -> str:
        """
        Semantic identity for an attribute.

        First pass: use attribute_config_id; later we can enrich this with
        instance + config names via OIGContext/OCG index.
        """
        attribute_config_id = self.attribute.attribute_config_id
        return f"attr:{attribute_config_id}" if attribute_config_id is not None else "attr:unknown"

    def get_content_fields(self) -> Mapping[str, Any]:
        return {
            "attribute_config_id": self.attribute.attribute_config_id,
        }

    # ---- Projections for content fields ----

    @property
    def attribute_config_id(self) -> UUID | None:  # type: ignore[override]
        return self.attribute.attribute_config_id
