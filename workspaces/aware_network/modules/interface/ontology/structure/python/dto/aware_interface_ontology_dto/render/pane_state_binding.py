from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Interface Ontology Dto
from aware_interface_ontology_dto.render.pane_render_enums import (
    PaneStateBindingTargetProperty,
    PaneStateBindingTransform,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute_config import AttributeConfig
    from aware_meta_ontology_dto.class_.class_config import ClassConfig


class PaneStateBinding(BaseModel):
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
