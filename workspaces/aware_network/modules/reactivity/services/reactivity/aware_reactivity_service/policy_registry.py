from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_types import JsonObject
from aware_reactivity.stable_ids import (
    stable_action_config_id,
    stable_condition_config_id,
    stable_event_config_action_config_id,
    stable_event_config_condition_config_id,
    stable_event_config_id,
)
from aware_reactivity_ontology.stable_ids import (
    stable_event_config_meaning_resolver_config_id,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleEnsureRequest,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleEnsureResponse,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleListRequest,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleListResponse,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleReceipt,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleSpec,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyConditionConfigSpec,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyConditionPredicateSpec,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyEventActionBindingSpec,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyEventConditionBindingSpec,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyEventMeaningResolverBindingSpec,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyInstalledActionConfig,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyInstalledConditionConfig,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyInstalledEventActionBinding,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyInstalledEventConditionBinding,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyInstalledEventConfig,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyInstalledEventMeaningResolverBinding,
)

_BUNDLE_NAMESPACE = uuid5(NAMESPACE_URL, "aware://reactivity/policy-bundle/v0")
SERVICE_CONDITION_RESOLUTION_MODE = "name_only_v0"
DISABLED_CONDITION_RESOLUTION_MODE = "disabled_name_only_v0"
_SUPPORTED_NAME_ONLY_LOGIC_STRATEGY = "all"
_UNSUPPORTED_CONDITION_METADATA_KEYS = frozenset(
    {
        "attribute",
        "attributes",
        "attributepolicy",
        "class",
        "classes",
        "classpolicy",
        "enum",
        "enumsetpolicy",
        "evaluate",
        "evaluator",
        "operator",
        "predicate",
        "predicates",
        "primitive",
        "primitivepolicy",
        "relationship",
        "relationships",
        "relationshippolicy",
    }
)
_BINDING_ARBITRATION_CONTRACT = (
    f"service dispatch is {SERVICE_CONDITION_RESOLUTION_MODE} and does not "
    "enforce binding arbitration semantics yet"
)


@dataclass(frozen=True, slots=True)
class ReactivityResolvedPolicyEvent:
    owner_ref: str
    policy_key: str
    event_type: str
    event_config_id: UUID
    event_config_condition_config_id: UUID | None = None
    condition_resolution_mode: str = SERVICE_CONDITION_RESOLUTION_MODE


@dataclass(frozen=True, slots=True)
class ReactivityResolvedPolicyActionBinding:
    owner_ref: str
    policy_key: str
    event_config_condition_config_id: UUID
    event_config_action_config_id: UUID
    action_config_id: UUID
    action_type: str


@dataclass(frozen=True, slots=True)
class ReactivityResolvedEventMeaningProvider:
    owner_ref: str
    policy_key: str
    resolver_key: str
    event_config_id: UUID
    event_config_meaning_resolver_config_id: UUID
    action_config_id: UUID
    api_capability_endpoint_id: UUID
    priority: int


@dataclass(slots=True)
class ReactivityPolicyRegistry:
    """In-process policy bundle registry for the generated Reactivity service API."""

    _receipts_by_id: dict[UUID, ReactivityPolicyBundleReceipt] = field(
        default_factory=dict
    )

    def ensure_bundle(
        self,
        request: ReactivityPolicyBundleEnsureRequest,
    ) -> ReactivityPolicyBundleEnsureResponse:
        try:
            receipt = _build_receipt(request.bundle)
            if not request.validate_only:
                existing = self._receipts_by_id.get(receipt.bundle_id)
                if existing is not None and existing != receipt:
                    raise ValueError(
                        "policy bundle conflicts with existing registration: "
                        f"{receipt.owner_ref}:{receipt.policy_key}:v{receipt.version}"
                    )
                self._receipts_by_id[receipt.bundle_id] = receipt.model_copy(deep=True)
            return ReactivityPolicyBundleEnsureResponse(
                request_id=request.request_id,
                accepted=True,
                validate_only=request.validate_only,
                status="validated" if request.validate_only else "ensured",
                receipt=receipt,
                info=(
                    "reactivity policy bundle validated"
                    if request.validate_only
                    else "reactivity policy bundle ensured"
                ),
            )
        except ValueError as exc:
            return ReactivityPolicyBundleEnsureResponse(
                request_id=request.request_id,
                accepted=False,
                validate_only=request.validate_only,
                status="rejected",
                error=str(exc),
            )

    def list_bundles(
        self,
        request: ReactivityPolicyBundleListRequest,
    ) -> ReactivityPolicyBundleListResponse:
        owner_ref = _optional_text(request.owner_ref)
        policy_key = _optional_text(request.policy_key)
        receipts = [
            receipt.model_copy(deep=True)
            for receipt in self._sorted_receipts()
            if (owner_ref is None or receipt.owner_ref == owner_ref)
            and (policy_key is None or receipt.policy_key == policy_key)
        ]
        return ReactivityPolicyBundleListResponse(
            request_id=request.request_id,
            accepted=True,
            receipts=receipts,
            info=f"{len(receipts)} reactivity policy bundle(s)",
        )

    def resolve_events_for_operation_label(
        self,
        operation_label: str | None,
        *,
        environment_id: UUID | None = None,
    ) -> tuple[ReactivityResolvedPolicyEvent, ...]:
        label = _optional_text(operation_label)
        if label is None:
            return ()

        resolved: list[ReactivityResolvedPolicyEvent] = []
        for receipt in self._sorted_receipts():
            if not _receipt_applies_to_environment(
                receipt=receipt,
                environment_id=environment_id,
            ):
                continue
            enabled_condition_config_ids = _enabled_condition_config_ids(receipt)
            event_configs_by_id = {
                config.event_config_id: config for config in receipt.event_configs
            }
            matching_event_config_ids: set[UUID] = set()
            if _text_matches(receipt.policy_key, label):
                matching_event_config_ids.update(event_configs_by_id)

            for event_config in receipt.event_configs:
                if _text_matches(event_config.name, label):
                    matching_event_config_ids.add(event_config.event_config_id)

            for condition_config in receipt.condition_configs:
                if (
                    condition_config.condition_config_id
                    not in enabled_condition_config_ids
                ):
                    continue
                if not _text_matches(condition_config.name, label):
                    continue
                for binding in receipt.event_condition_bindings:
                    if (
                        binding.condition_config_id
                        == condition_config.condition_config_id
                    ):
                        matching_event_config_ids.add(binding.event_config_id)

            for event_config_id in sorted(
                matching_event_config_ids,
                key=lambda item: event_configs_by_id[item].name.casefold(),
            ):
                event_config = event_configs_by_id[event_config_id]
                binding_id = _first_enabled_event_condition_binding_id(
                    receipt=receipt,
                    event_config_id=event_config_id,
                    enabled_condition_config_ids=enabled_condition_config_ids,
                )
                if binding_id is None and _has_event_condition_binding(
                    receipt=receipt,
                    event_config_id=event_config_id,
                ):
                    continue
                resolved.append(
                    ReactivityResolvedPolicyEvent(
                        owner_ref=receipt.owner_ref,
                        policy_key=receipt.policy_key,
                        event_type=event_config.name,
                        event_config_id=event_config_id,
                        event_config_condition_config_id=binding_id,
                    )
                )
        return tuple(resolved)

    def resolve_action_bindings_for_event_condition_config(
        self,
        event_config_condition_config_id: UUID | None,
        *,
        environment_id: UUID | None = None,
    ) -> tuple[ReactivityResolvedPolicyActionBinding, ...]:
        if event_config_condition_config_id is None:
            return ()

        resolved: list[ReactivityResolvedPolicyActionBinding] = []
        for receipt in self._sorted_receipts():
            if not _receipt_applies_to_environment(
                receipt=receipt,
                environment_id=environment_id,
            ):
                continue
            enabled_condition_config_ids = _enabled_condition_config_ids(receipt)
            event_config_ids = {
                binding.event_config_id
                for binding in receipt.event_condition_bindings
                if (
                    binding.event_config_condition_config_id
                    == event_config_condition_config_id
                    and binding.condition_config_id in enabled_condition_config_ids
                )
            }
            if not event_config_ids:
                continue

            action_types_by_id = {
                action_config.action_config_id: action_config.action_type
                for action_config in receipt.action_configs
            }
            for binding in receipt.event_action_bindings:
                if binding.event_config_id not in event_config_ids:
                    continue
                action_type = action_types_by_id.get(binding.action_config_id)
                if action_type is None:
                    continue
                resolved.append(
                    ReactivityResolvedPolicyActionBinding(
                        owner_ref=receipt.owner_ref,
                        policy_key=receipt.policy_key,
                        event_config_condition_config_id=(
                            event_config_condition_config_id
                        ),
                        event_config_action_config_id=(
                            binding.event_config_action_config_id
                        ),
                        action_config_id=binding.action_config_id,
                        action_type=action_type,
                    )
                )

        resolved.sort(
            key=lambda binding: (
                binding.action_type.casefold(),
                str(binding.event_config_action_config_id),
            )
        )
        return tuple(resolved)

    def resolve_event_condition_config_resolution_mode(
        self,
        event_config_condition_config_id: UUID | None,
        *,
        environment_id: UUID | None = None,
    ) -> str | None:
        if event_config_condition_config_id is None:
            return None

        disabled_match = False
        for receipt in self._sorted_receipts():
            if not _receipt_applies_to_environment(
                receipt=receipt,
                environment_id=environment_id,
            ):
                continue
            enabled_condition_config_ids = _enabled_condition_config_ids(receipt)
            for binding in receipt.event_condition_bindings:
                if (
                    binding.event_config_condition_config_id
                    != event_config_condition_config_id
                ):
                    continue
                if binding.condition_config_id in enabled_condition_config_ids:
                    return SERVICE_CONDITION_RESOLUTION_MODE
                disabled_match = True
        return DISABLED_CONDITION_RESOLUTION_MODE if disabled_match else None

    def resolve_event_meaning_providers(
        self,
        *,
        event_type: str,
        event_config_id: UUID | None = None,
        resolver_key: str | None = None,
        environment_id: UUID | None = None,
    ) -> tuple[ReactivityResolvedEventMeaningProvider, ...]:
        normalized_event_type = _required_text(event_type, "event.event_type")
        normalized_resolver_key = _optional_text(resolver_key)
        resolved: list[ReactivityResolvedEventMeaningProvider] = []
        for receipt in self._sorted_receipts():
            if not _receipt_applies_to_environment(
                receipt=receipt,
                environment_id=environment_id,
            ):
                continue
            matching_event_ids = {
                config.event_config_id
                for config in receipt.event_configs
                if config.name.casefold() == normalized_event_type.casefold()
                and (
                    event_config_id is None or config.event_config_id == event_config_id
                )
            }
            if not matching_event_ids:
                continue
            for binding in receipt.event_meaning_resolver_bindings:
                if binding.event_config_id not in matching_event_ids:
                    continue
                if binding.status != "ensured":
                    continue
                if (
                    normalized_resolver_key is not None
                    and binding.resolver_key.casefold()
                    != normalized_resolver_key.casefold()
                ):
                    continue
                resolved.append(
                    ReactivityResolvedEventMeaningProvider(
                        owner_ref=receipt.owner_ref,
                        policy_key=receipt.policy_key,
                        resolver_key=binding.resolver_key,
                        event_config_id=binding.event_config_id,
                        event_config_meaning_resolver_config_id=(
                            binding.event_config_meaning_resolver_config_id
                        ),
                        action_config_id=binding.action_config_id,
                        api_capability_endpoint_id=(binding.api_capability_endpoint_id),
                        priority=binding.priority,
                    )
                )
        resolved.sort(
            key=lambda item: (
                -item.priority,
                item.owner_ref,
                item.policy_key,
                item.resolver_key,
                str(item.event_config_meaning_resolver_config_id),
            )
        )
        return tuple(resolved)

    def _sorted_receipts(self) -> list[ReactivityPolicyBundleReceipt]:
        return sorted(
            self._receipts_by_id.values(),
            key=lambda receipt: (
                receipt.owner_ref,
                receipt.policy_key,
                receipt.version,
                str(receipt.bundle_id),
            ),
        )


def _build_receipt(bundle: ReactivityPolicyBundleSpec) -> ReactivityPolicyBundleReceipt:
    owner_ref = _required_text(bundle.owner_ref, "bundle.owner_ref")
    policy_key = _required_text(bundle.policy_key, "bundle.policy_key")
    if bundle.version < 1:
        raise ValueError("bundle.version must be greater than zero")

    condition_configs = [_condition_config(spec) for spec in bundle.condition_configs]
    event_configs = [
        ReactivityPolicyInstalledEventConfig(
            name=_required_text(spec.name, "event_configs.name"),
            event_config_id=spec.config_id or stable_event_config_id(name=spec.name),
        )
        for spec in bundle.event_configs
    ]
    action_configs = [
        ReactivityPolicyInstalledActionConfig(
            name=_required_text(spec.name, "action_configs.name"),
            action_config_id=spec.config_id or stable_action_config_id(name=spec.name),
            action_type=_required_text(spec.action_type, "action_configs.action_type"),
        )
        for spec in bundle.action_configs
    ]

    condition_ids_by_name = {
        config.name: config.condition_config_id for config in condition_configs
    }
    event_ids_by_name = {
        config.name: config.event_config_id for config in event_configs
    }
    action_ids_by_name = {
        config.name: config.action_config_id for config in action_configs
    }

    event_condition_bindings = [
        _event_condition_binding(
            event_config_id=_resolve_event_config_id(
                event_ids_by_name=event_ids_by_name,
                explicit_id=spec.event_config_id,
                name=spec.event_config_name,
            ),
            condition_config_id=_resolve_condition_config_id(
                condition_ids_by_name=condition_ids_by_name,
                explicit_id=spec.condition_config_id,
                name=spec.condition_config_name,
            ),
            spec=spec,
            binding_id=spec.binding_id,
        )
        for spec in bundle.event_condition_bindings
    ]
    event_action_bindings = [
        _event_action_binding(
            event_config_id=_resolve_event_config_id(
                event_ids_by_name=event_ids_by_name,
                explicit_id=spec.event_config_id,
                name=spec.event_config_name,
            ),
            action_config_id=_resolve_action_config_id(
                action_ids_by_name=action_ids_by_name,
                explicit_id=spec.action_config_id,
                name=spec.action_config_name,
            ),
            spec=spec,
            binding_id=spec.binding_id,
        )
        for spec in bundle.event_action_bindings
    ]
    event_meaning_resolver_bindings = [
        _event_meaning_resolver_binding(
            event_config_id=_resolve_event_config_id(
                event_ids_by_name=event_ids_by_name,
                explicit_id=spec.event_config_id,
                name=spec.event_config_name,
            ),
            action_config_id=_resolve_action_config_id(
                action_ids_by_name=action_ids_by_name,
                explicit_id=spec.action_config_id,
                name=spec.action_config_name,
            ),
            spec=spec,
        )
        for spec in bundle.event_meaning_resolver_bindings
    ]
    _validate_meaning_resolver_actions(
        bindings=event_meaning_resolver_bindings,
        action_config_ids=set(action_ids_by_name.values()),
    )

    metadata = JsonObject(bundle.metadata)
    metadata.setdefault("condition_resolution_mode", SERVICE_CONDITION_RESOLUTION_MODE)
    metadata.setdefault("condition_evaluator", "not_invoked")
    environment_id = _metadata_uuid(bundle.metadata, "environment_id")
    if environment_id is not None:
        metadata.setdefault("environment_id", str(environment_id))
    profile_key = _optional_text(bundle.profile_key)
    if profile_key is not None:
        metadata.setdefault("profile_key", profile_key)

    return ReactivityPolicyBundleReceipt(
        bundle_id=_stable_bundle_id(
            owner_ref=owner_ref,
            policy_key=policy_key,
            version=bundle.version,
            semantic_source_ref=bundle.semantic_source_ref,
            environment_id=environment_id,
            profile_key=profile_key,
            idempotency_key=bundle.idempotency_key,
        ),
        owner_ref=owner_ref,
        policy_key=policy_key,
        version=bundle.version,
        semantic_source_ref=_optional_text(bundle.semantic_source_ref),
        idempotency_key=_optional_text(bundle.idempotency_key),
        condition_configs=condition_configs,
        event_configs=event_configs,
        action_configs=action_configs,
        event_condition_bindings=event_condition_bindings,
        event_action_bindings=event_action_bindings,
        event_meaning_resolver_bindings=event_meaning_resolver_bindings,
        metadata=metadata,
    )


def _condition_config(
    spec: ReactivityPolicyConditionConfigSpec,
) -> ReactivityPolicyInstalledConditionConfig:
    name = _required_text(spec.name, "condition_configs.name")
    _validate_name_only_condition_config(spec, name=name)
    return ReactivityPolicyInstalledConditionConfig(
        name=name,
        condition_config_id=spec.config_id or stable_condition_config_id(name=name),
        status=(
            SERVICE_CONDITION_RESOLUTION_MODE
            if spec.is_enabled
            else DISABLED_CONDITION_RESOLUTION_MODE
        ),
    )


def _validate_name_only_condition_config(
    spec: ReactivityPolicyConditionConfigSpec,
    *,
    name: str,
) -> None:
    logic_strategy = _optional_text(spec.logic_strategy) or (
        _SUPPORTED_NAME_ONLY_LOGIC_STRATEGY
    )
    if logic_strategy.casefold() != _SUPPORTED_NAME_ONLY_LOGIC_STRATEGY:
        raise ValueError(
            "Reactivity service policy condition "
            f"{name!r} uses unsupported logic_strategy {logic_strategy!r}; "
            f"service dispatch is {SERVICE_CONDITION_RESOLUTION_MODE} and does not "
            "evaluate typed predicates"
        )
    unsupported_paths = _unsupported_condition_metadata_paths(spec.metadata)
    if unsupported_paths:
        joined = ", ".join(unsupported_paths)
        raise ValueError(
            "Reactivity service policy condition "
            f"{name!r} declares predicate-shaped metadata ({joined}); "
            f"service dispatch is {SERVICE_CONDITION_RESOLUTION_MODE} until typed "
            "predicate authoring is materialized"
        )
    predicate = spec.predicate
    if predicate is not None and _condition_predicate_has_payload(predicate):
        raise ValueError(
            "Reactivity service policy condition "
            f"{name!r} declares typed predicate payload; service dispatch is "
            f"{SERVICE_CONDITION_RESOLUTION_MODE} and does not evaluate typed "
            "predicates yet"
        )


def _event_condition_binding(
    *,
    event_config_id: UUID,
    condition_config_id: UUID,
    spec: ReactivityPolicyEventConditionBindingSpec,
    binding_id: UUID | None,
) -> ReactivityPolicyInstalledEventConditionBinding:
    _validate_default_event_condition_binding(spec)
    return ReactivityPolicyInstalledEventConditionBinding(
        event_config_id=event_config_id,
        condition_config_id=condition_config_id,
        event_config_condition_config_id=binding_id
        or stable_event_config_condition_config_id(
            event_config_id=event_config_id,
            condition_config_id=condition_config_id,
        ),
    )


def _event_action_binding(
    *,
    event_config_id: UUID,
    action_config_id: UUID,
    spec: ReactivityPolicyEventActionBindingSpec,
    binding_id: UUID | None,
) -> ReactivityPolicyInstalledEventActionBinding:
    _validate_default_event_action_binding(spec)
    return ReactivityPolicyInstalledEventActionBinding(
        event_config_id=event_config_id,
        action_config_id=action_config_id,
        event_config_action_config_id=binding_id
        or stable_event_config_action_config_id(
            event_config_id=event_config_id,
            action_config_id=action_config_id,
        ),
    )


def _event_meaning_resolver_binding(
    *,
    event_config_id: UUID,
    action_config_id: UUID,
    spec: ReactivityPolicyEventMeaningResolverBindingSpec,
) -> ReactivityPolicyInstalledEventMeaningResolverBinding:
    resolver_key = _required_text(spec.resolver_key, "resolver_key")
    if spec.priority != 0:
        raise ValueError(
            "event meaning resolver priority arbitration is not supported in v0"
        )
    return ReactivityPolicyInstalledEventMeaningResolverBinding(
        event_config_id=event_config_id,
        action_config_id=action_config_id,
        event_config_meaning_resolver_config_id=(
            spec.binding_id
            or stable_event_config_meaning_resolver_config_id(
                event_config_id=event_config_id,
                action_config_id=action_config_id,
                resolver_key=resolver_key,
            )
        ),
        resolver_key=resolver_key,
        api_capability_endpoint_id=spec.api_capability_endpoint_id,
        priority=spec.priority,
        status="ensured" if spec.is_enabled else "disabled",
    )


def _validate_meaning_resolver_actions(
    *,
    bindings: list[ReactivityPolicyInstalledEventMeaningResolverBinding],
    action_config_ids: set[UUID],
) -> None:
    seen: set[tuple[UUID, str]] = set()
    for binding in bindings:
        if binding.action_config_id not in action_config_ids:
            raise ValueError(
                "event meaning resolver action_config must be declared in the same "
                f"policy bundle: {binding.action_config_id}"
            )
        key = (binding.event_config_id, binding.resolver_key.casefold())
        if key in seen:
            raise ValueError(
                "event meaning resolver key is duplicated for EventConfig: "
                f"{binding.event_config_id}:{binding.resolver_key}"
            )
        seen.add(key)


def _resolve_condition_config_id(
    *,
    condition_ids_by_name: dict[str, UUID],
    explicit_id: UUID | None,
    name: str | None,
) -> UUID:
    if explicit_id is not None:
        return explicit_id
    resolved_name = _required_text(name, "condition_config_name")
    return condition_ids_by_name.get(resolved_name) or stable_condition_config_id(
        name=resolved_name
    )


def _validate_default_event_condition_binding(
    spec: ReactivityPolicyEventConditionBindingSpec,
) -> None:
    unsupported_fields: list[str] = []
    if spec.execution_order != 0:
        unsupported_fields.append("execution_order")
    if spec.priority != 0:
        unsupported_fields.append("priority")
    if not spec.is_enabled:
        unsupported_fields.append("is_enabled=false")
    if spec.is_required:
        unsupported_fields.append("is_required=true")
    if not spec.continue_on_fail:
        unsupported_fields.append("continue_on_fail=false")
    if spec.stop_on_match:
        unsupported_fields.append("stop_on_match=true")
    if spec.cache_result:
        unsupported_fields.append("cache_result=true")
    if spec.cache_ttl_seconds is not None:
        unsupported_fields.append("cache_ttl_seconds")
    if unsupported_fields:
        joined = ", ".join(unsupported_fields)
        raise ValueError(
            "Reactivity service policy event-condition binding declares "
            f"unsupported arbitration fields ({joined}); "
            f"{_BINDING_ARBITRATION_CONTRACT}"
        )


def _validate_default_event_action_binding(
    spec: ReactivityPolicyEventActionBindingSpec,
) -> None:
    unsupported_fields: list[str] = []
    if spec.execution_order != 0:
        unsupported_fields.append("execution_order")
    if spec.priority != 0:
        unsupported_fields.append("priority")
    if not spec.is_enabled:
        unsupported_fields.append("is_enabled=false")
    if spec.is_required:
        unsupported_fields.append("is_required=true")
    if not spec.continue_on_fail:
        unsupported_fields.append("continue_on_fail=false")
    if unsupported_fields:
        joined = ", ".join(unsupported_fields)
        raise ValueError(
            "Reactivity service policy event-action binding declares unsupported "
            f"arbitration fields ({joined}); {_BINDING_ARBITRATION_CONTRACT}"
        )


def _resolve_event_config_id(
    *,
    event_ids_by_name: dict[str, UUID],
    explicit_id: UUID | None,
    name: str | None,
) -> UUID:
    if explicit_id is not None:
        return explicit_id
    resolved_name = _required_text(name, "event_config_name")
    return event_ids_by_name.get(resolved_name) or stable_event_config_id(
        name=resolved_name
    )


def _resolve_action_config_id(
    *,
    action_ids_by_name: dict[str, UUID],
    explicit_id: UUID | None,
    name: str | None,
) -> UUID:
    if explicit_id is not None:
        return explicit_id
    resolved_name = _required_text(name, "action_config_name")
    return action_ids_by_name.get(resolved_name) or stable_action_config_id(
        name=resolved_name
    )


def _stable_bundle_id(
    *,
    owner_ref: str,
    policy_key: str,
    version: int,
    semantic_source_ref: str | None,
    environment_id: UUID | None,
    profile_key: str | None,
    idempotency_key: str | None,
) -> UUID:
    semantic_source = _optional_text(semantic_source_ref) or ""
    environment_ref = str(environment_id) if environment_id is not None else ""
    profile_ref = _optional_text(profile_key) or ""
    idempotency_ref = _optional_text(idempotency_key) or ""
    return uuid5(
        _BUNDLE_NAMESPACE,
        ":".join(
            (
                owner_ref.casefold(),
                policy_key.casefold(),
                str(version),
                semantic_source.casefold(),
                environment_ref,
                profile_ref.casefold(),
                idempotency_ref.casefold(),
            )
        ),
    )


def _required_text(value: str | None, field_name: str) -> str:
    normalized = _optional_text(value)
    if normalized is None:
        raise ValueError(f"{field_name} is required")
    return normalized


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _text_matches(left: str, right: str) -> bool:
    return left.casefold().strip() == right.casefold().strip()


def _receipt_applies_to_environment(
    *,
    receipt: ReactivityPolicyBundleReceipt,
    environment_id: UUID | None,
) -> bool:
    receipt_environment_id = _metadata_text(receipt.metadata, "environment_id")
    if receipt_environment_id is None:
        return True
    if environment_id is None:
        return False
    return receipt_environment_id == str(environment_id)


def _metadata_text(metadata: JsonObject, key: str) -> str | None:
    value = metadata.get(key)
    if value is None:
        return None
    return _optional_text(str(value))


def _metadata_uuid(metadata: JsonObject, key: str) -> UUID | None:
    value = metadata.get(key)
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    text = _optional_text(str(value))
    if text is None:
        return None
    try:
        return UUID(text)
    except ValueError as exc:
        raise ValueError(f"bundle.metadata.{key} must be a UUID string") from exc


def _condition_config_is_enabled(
    config: ReactivityPolicyInstalledConditionConfig,
) -> bool:
    return config.status != DISABLED_CONDITION_RESOLUTION_MODE


def _enabled_condition_config_ids(
    receipt: ReactivityPolicyBundleReceipt,
) -> set[UUID]:
    return {
        config.condition_config_id
        for config in receipt.condition_configs
        if _condition_config_is_enabled(config)
    }


def _has_event_condition_binding(
    *,
    receipt: ReactivityPolicyBundleReceipt,
    event_config_id: UUID,
) -> bool:
    return any(
        binding.event_config_id == event_config_id
        for binding in receipt.event_condition_bindings
    )


def _first_enabled_event_condition_binding_id(
    *,
    receipt: ReactivityPolicyBundleReceipt,
    event_config_id: UUID,
    enabled_condition_config_ids: set[UUID],
) -> UUID | None:
    for binding in receipt.event_condition_bindings:
        if (
            binding.event_config_id == event_config_id
            and binding.condition_config_id in enabled_condition_config_ids
        ):
            return binding.event_config_condition_config_id
    return None


def _unsupported_condition_metadata_paths(
    value: object,
    *,
    prefix: str = "metadata",
) -> tuple[str, ...]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for raw_key, raw_value in value.items():
            key = str(raw_key)
            path = f"{prefix}.{key}"
            if _normalize_metadata_key(key) in _UNSUPPORTED_CONDITION_METADATA_KEYS:
                paths.append(path)
            paths.extend(_unsupported_condition_metadata_paths(raw_value, prefix=path))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            paths.extend(
                _unsupported_condition_metadata_paths(
                    item,
                    prefix=f"{prefix}[{index}]",
                )
            )
    return tuple(paths)


def _condition_predicate_has_payload(
    predicate: ReactivityPolicyConditionPredicateSpec,
) -> bool:
    logic_strategy = _optional_text(predicate.logic_strategy) or (
        _SUPPORTED_NAME_ONLY_LOGIC_STRATEGY
    )
    return logic_strategy.casefold() != _SUPPORTED_NAME_ONLY_LOGIC_STRATEGY or bool(
        predicate.classes
    )


def _normalize_metadata_key(key: str) -> str:
    return "".join(character for character in key.casefold() if character.isalnum())


__all__ = [
    "DISABLED_CONDITION_RESOLUTION_MODE",
    "ReactivityPolicyRegistry",
    "ReactivityResolvedPolicyActionBinding",
    "ReactivityResolvedPolicyEvent",
    "SERVICE_CONDITION_RESOLUTION_MODE",
]
