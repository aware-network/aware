from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Interface Ontology Orm Models
from aware_interface_ontology_orm_models.render.pane_render_enums import (
    PaneStateBindingTargetProperty,
    PaneStateBindingTransform,
)

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute_config import AttributeConfig
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig


class PaneStateBinding(ORMModel):
    # Relationships
    state_model: ClassConfig | None = Field(default=None)
    state_attribute_config: AttributeConfig | None = Field(default=None)

    # Attributes
    binding_key: str
    target_property: PaneStateBindingTargetProperty
    json_path: str
    transform: PaneStateBindingTransform = Field(default=PaneStateBindingTransform.raw)
    fallback_value: str | None = Field(default=None)
    component_input_port_key: str | None = Field(default=None)

    # Foreign Keys
    pane_render_node_id: UUID = Field(description="Foreign key for PaneRenderNode.state_bindings")
    state_model_id: UUID | None = Field(default=None, description="Foreign key for PaneStateBinding.state_model")
    state_attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for PaneStateBinding.state_attribute_config"
    )
