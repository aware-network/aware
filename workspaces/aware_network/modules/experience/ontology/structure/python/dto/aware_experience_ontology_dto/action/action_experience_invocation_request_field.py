from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute_config import AttributeConfig


class ActionExperienceInvocationRequestField(BaseModel):
    """
    Declared request-field composition for one action invocation binding.
    Contract:
    - Parent scope is `ActionExperienceInvocation::request_fields`.
    - The target request field is relational: `attribute_config` points to the
    endpoint request ClassConfig attribute, not a string field name.
    - `source_ref` is the closed Experience dispatch-context vocabulary:
    `event.*`, `commit.*`, `intent.*`, `execution.*`, `api_call.key`,
    `binding.*`, `binding.node.<alias>.class_instance_identity_id`,
    `binding.node.<alias>.class_config_id`, `actor.id`, and
    `subscription.id`.
    - The composer is a pure projection of dispatch context into the endpoint
    request payload. It must not read graph state, call services, or evaluate
    arbitrary expressions.
    """

    # Relationships
    attribute_config: AttributeConfig

    # Attributes
    source_ref: str
    required: bool = Field(default=True)
    position: int | None = Field(default=None)
