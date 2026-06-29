from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import (
    JsonObject,
    JsonValue,
)


class ReactivityPolicyPrimitivePredicateSpec(BaseModel):
    """
    Reactivity policy bundle registration DTOs.
    Contract:
    - Producers describe condition/event/action policy bundles through the
    Reactivity API.
    - Reactivity owns deterministic id resolution and policy installation.
    - v0 service tests may use an in-memory registry; durable installation must
    later write config graph truth through generated Meta/Environment rails.
    """

    # Attributes
    value: JsonValue | None = Field(default=None)
    range_min: JsonValue | None = Field(default=None)
    range_max: JsonValue | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ReactivityPolicyEnumPredicateSpec(BaseModel):
    # Attributes
    enum_config_id: UUID | None = Field(default=None)
    enum_config_ref: str | None = Field(default=None)
    enum_option_ids: list[UUID] = Field(default_factory=list)
    enum_option_refs: list[str] = Field(default_factory=list)
    match_mode: str = Field(default="any_of")
    metadata: JsonObject = Field(default_factory=JsonObject)


class ReactivityPolicyRelationshipPredicateSpec(BaseModel):
    # Attributes
    class_config_relationship_id: UUID | None = Field(default=None)
    relationship_ref: str | None = Field(default=None)
    eval_mode: str = Field(default="exists")
    count_threshold: int | None = Field(default=None)
    nested_condition_config_id: UUID | None = Field(default=None)
    nested_condition_name: str | None = Field(default=None)
    nested_condition: ReactivityPolicyConditionPredicateSpec | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ReactivityPolicyAttributePredicateSpec(BaseModel):
    # Attributes
    attribute_config_id: UUID | None = Field(default=None)
    attribute_ref: str | None = Field(default=None)
    operator: str = Field(default="equals")
    negate: bool = Field(default=False)
    primitive: ReactivityPolicyPrimitivePredicateSpec | None = Field(default=None)
    enum: ReactivityPolicyEnumPredicateSpec | None = Field(default=None)
    relationship: ReactivityPolicyRelationshipPredicateSpec | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ReactivityPolicyClassPredicateSpec(BaseModel):
    # Attributes
    class_config_id: UUID | None = Field(default=None)
    class_ref: str | None = Field(default=None)
    class_selection: str = Field(default="base_class")
    class_logic: str = Field(default="all")
    require_existence: bool = Field(default=True)
    attributes: list[ReactivityPolicyAttributePredicateSpec] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ReactivityPolicyConditionPredicateSpec(BaseModel):
    # Attributes
    logic_strategy: str = Field(default="all")
    classes: list[ReactivityPolicyClassPredicateSpec] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ReactivityPolicyConditionConfigSpec(BaseModel):
    # Attributes
    name: str
    description: str
    logic_strategy: str = Field(default="all")
    is_enabled: bool = Field(default=True)
    is_system: bool = Field(default=False)
    config_id: UUID | None = Field(default=None)
    predicate: ReactivityPolicyConditionPredicateSpec | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ReactivityPolicyEventConfigSpec(BaseModel):
    # Attributes
    name: str
    description: str
    event_type: str = Field(default="condition")
    delivery_mode: str = Field(default="immediate")
    priority: str = Field(default="normal")
    is_enabled: bool = Field(default=True)
    is_system: bool = Field(default=False)
    require_authentication: bool = Field(default=True)
    valid_sources: list[str] = Field(default_factory=list)
    allowed_roles: list[str] = Field(default_factory=list)
    event_schema: JsonObject = Field(default_factory=JsonObject)
    batch_window_ms: int | None = Field(default=None)
    config_id: UUID | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ReactivityPolicyActionConfigSpec(BaseModel):
    # Attributes
    name: str
    description: str
    action_type: str
    is_enabled: bool = Field(default=True)
    is_system: bool = Field(default=False)
    require_authentication: bool = Field(default=True)
    allowed_roles: list[str] = Field(default_factory=list)
    action_schema: JsonObject = Field(default_factory=JsonObject)
    config_id: UUID | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ReactivityPolicyEventConditionBindingSpec(BaseModel):
    # Attributes
    event_config_name: str | None = Field(default=None)
    condition_config_name: str | None = Field(default=None)
    event_config_id: UUID | None = Field(default=None)
    condition_config_id: UUID | None = Field(default=None)
    execution_order: int = Field(default=0)
    priority: int = Field(default=0)
    is_enabled: bool = Field(default=True)
    is_required: bool = Field(default=False)
    continue_on_fail: bool = Field(default=True)
    stop_on_match: bool = Field(default=False)
    cache_result: bool = Field(default=False)
    cache_ttl_seconds: int | None = Field(default=None)
    binding_id: UUID | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ReactivityPolicyEventActionBindingSpec(BaseModel):
    # Attributes
    event_config_name: str | None = Field(default=None)
    action_config_name: str | None = Field(default=None)
    event_config_id: UUID | None = Field(default=None)
    action_config_id: UUID | None = Field(default=None)
    execution_order: int = Field(default=0)
    priority: int = Field(default=0)
    is_enabled: bool = Field(default=True)
    is_required: bool = Field(default=False)
    continue_on_fail: bool = Field(default=True)
    binding_id: UUID | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ReactivityPolicyBundleSpec(BaseModel):
    # Attributes
    owner_ref: str
    policy_key: str
    version: int = Field(default=1)
    semantic_source_ref: str | None = Field(default=None)
    profile_key: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)
    condition_configs: list[ReactivityPolicyConditionConfigSpec] = Field(default_factory=list)
    event_configs: list[ReactivityPolicyEventConfigSpec] = Field(default_factory=list)
    action_configs: list[ReactivityPolicyActionConfigSpec] = Field(default_factory=list)
    event_condition_bindings: list[ReactivityPolicyEventConditionBindingSpec] = Field(default_factory=list)
    event_action_bindings: list[ReactivityPolicyEventActionBindingSpec] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ReactivityPolicyInstalledConditionConfig(BaseModel):
    # Attributes
    name: str
    condition_config_id: UUID
    status: str = Field(default="ensured")


class ReactivityPolicyInstalledEventConfig(BaseModel):
    # Attributes
    name: str
    event_config_id: UUID
    status: str = Field(default="ensured")


class ReactivityPolicyInstalledActionConfig(BaseModel):
    # Attributes
    name: str
    action_config_id: UUID
    action_type: str
    status: str = Field(default="ensured")


class ReactivityPolicyInstalledEventConditionBinding(BaseModel):
    # Attributes
    event_config_id: UUID
    condition_config_id: UUID
    event_config_condition_config_id: UUID
    status: str = Field(default="ensured")


class ReactivityPolicyInstalledEventActionBinding(BaseModel):
    # Attributes
    event_config_id: UUID
    action_config_id: UUID
    event_config_action_config_id: UUID
    status: str = Field(default="ensured")


class ReactivityPolicyBundleReceipt(BaseModel):
    # Attributes
    bundle_id: UUID
    owner_ref: str
    policy_key: str
    version: int
    semantic_source_ref: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)
    condition_configs: list[ReactivityPolicyInstalledConditionConfig] = Field(default_factory=list)
    event_configs: list[ReactivityPolicyInstalledEventConfig] = Field(default_factory=list)
    action_configs: list[ReactivityPolicyInstalledActionConfig] = Field(default_factory=list)
    event_condition_bindings: list[ReactivityPolicyInstalledEventConditionBinding] = Field(default_factory=list)
    event_action_bindings: list[ReactivityPolicyInstalledEventActionBinding] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ReactivityPolicyBundleEnsureRequest(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    subscriber_id: str | None = Field(default=None)
    bundle: ReactivityPolicyBundleSpec
    validate_only: bool = Field(default=False)


class ReactivityPolicyBundleEnsureResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    accepted: bool = Field(default=True)
    validate_only: bool = Field(default=False)
    status: str = Field(default="ensured")
    receipt: ReactivityPolicyBundleReceipt | None = Field(default=None)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)


class ReactivityPolicyBundleListRequest(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    subscriber_id: str | None = Field(default=None)
    owner_ref: str | None = Field(default=None)
    policy_key: str | None = Field(default=None)


class ReactivityPolicyBundleListResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    accepted: bool = Field(default=True)
    receipts: list[ReactivityPolicyBundleReceipt] = Field(default_factory=list)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)
