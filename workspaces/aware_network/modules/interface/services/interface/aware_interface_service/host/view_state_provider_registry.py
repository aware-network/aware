from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from importlib import import_module
from typing import Any, TypeVar, cast
from uuid import UUID

from aware_types import JsonObject, JsonValue
from aware_interface_service.host.view_state_ontology_dto import (
    materialize_latest_ontology,
    raw_ontology_deltas_for_result,
)


ViewStateProviderCallable = Callable[..., object]
ViewStateProviderInputResolverCallable = Callable[
    ["InterfaceViewStateProviderContext"],
    object,
]

_T = TypeVar("_T")


class InterfaceViewStateProviderError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class InterfaceViewStateProviderInput:
    pane: object
    result: object
    assets: object
    provenance: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class InterfaceViewStateProviderContext:
    pane: object
    result: object
    assets: object
    provenance: Mapping[str, object]

    def latest_ontology(self, model: type[_T]) -> _T | None:
        return materialize_latest_ontology(
            model=model,
            result=self.result,
            assets=self.assets,
        )

    def raw_ontology_deltas(self) -> tuple[JsonObject, ...]:
        return raw_ontology_deltas_for_result(self.result)


@dataclass(frozen=True, slots=True)
class InterfaceResolvedViewState:
    state: JsonObject
    view_ref: str | None = None
    view_key: str | None = None
    state_model_ref: str | None = None
    version: str | None = None
    registry_module: str | None = None
    contract_validated: bool = False


@dataclass(frozen=True, slots=True)
class _PaneViewIdentity:
    view_ref: str | None = None
    view_key: str | None = None


@dataclass(frozen=True, slots=True)
class _GeneratedViewModelContract:
    view_ref: str
    view_key: str
    state_model_ref: str
    version: str
    model: Any
    registry_module: str


_REGISTERED_PROVIDERS: dict[str, ViewStateProviderCallable] = {}
_LOADED_PROVIDERS: dict[str, ViewStateProviderCallable] = {}
_REGISTERED_PROVIDER_INPUT_RESOLVERS: dict[
    str,
    ViewStateProviderInputResolverCallable,
] = {}
_LOADED_PROVIDER_INPUT_RESOLVERS: dict[str, ViewStateProviderInputResolverCallable] = {}


def register_view_state_provider(
    provider_ref: str,
    provider: ViewStateProviderCallable,
    *,
    input_resolver: ViewStateProviderInputResolverCallable | None = None,
) -> None:
    normalized_ref = _normalize_provider_ref(provider_ref)
    if not callable(provider):
        raise InterfaceViewStateProviderError(
            f"View-state provider is not callable: provider_ref={normalized_ref!r}"
        )
    _REGISTERED_PROVIDERS[normalized_ref] = provider
    _LOADED_PROVIDERS.pop(normalized_ref, None)
    if input_resolver is not None:
        register_view_state_provider_input_resolver(
            normalized_ref,
            input_resolver,
        )
    else:
        _REGISTERED_PROVIDER_INPUT_RESOLVERS.pop(normalized_ref, None)
        _LOADED_PROVIDER_INPUT_RESOLVERS.pop(normalized_ref, None)


def register_view_state_provider_input_resolver(
    provider_ref: str,
    input_resolver: ViewStateProviderInputResolverCallable,
) -> None:
    normalized_ref = _normalize_provider_ref(provider_ref)
    if not callable(input_resolver):
        raise InterfaceViewStateProviderError(
            "View-state provider input resolver is not callable: "
            + f"provider_ref={normalized_ref!r}"
        )
    _REGISTERED_PROVIDER_INPUT_RESOLVERS[normalized_ref] = input_resolver
    _LOADED_PROVIDER_INPUT_RESOLVERS.pop(normalized_ref, None)


def reset_view_state_providers() -> None:
    _REGISTERED_PROVIDERS.clear()
    _LOADED_PROVIDERS.clear()
    _REGISTERED_PROVIDER_INPUT_RESOLVERS.clear()
    _LOADED_PROVIDER_INPUT_RESOLVERS.clear()


def resolve_view_state(
    provider_input: InterfaceViewStateProviderInput,
) -> InterfaceResolvedViewState:
    provider_ref = _pane_provider_ref(provider_input.pane)
    if provider_ref is None:
        return InterfaceResolvedViewState(state=JsonObject())

    provider_kind = _pane_provider_kind(provider_input.pane)
    if provider_kind != "runtime_callable":
        raise InterfaceViewStateProviderError(
            "Unsupported Interface view-state provider kind: "
            + f"provider_ref={provider_ref!r} provider_kind={provider_kind!r}"
        )

    provider = _load_provider(provider_ref)
    provider_context = InterfaceViewStateProviderContext(
        pane=provider_input.pane,
        result=provider_input.result,
        assets=provider_input.assets,
        provenance=provider_input.provenance,
    )
    input_resolver = _load_provider_input_resolver(provider_ref, provider)
    typed_provider_input = input_resolver(provider_context)
    raw_state = provider(provider_input=typed_provider_input)
    if raw_state is None:
        identity = _pane_view_identity(provider_input.pane)
        return InterfaceResolvedViewState(
            state=JsonObject(),
            view_ref=identity.view_ref,
            view_key=identity.view_key,
        )

    contract = _load_generated_view_model_contract(provider_input.pane)
    if contract is not None:
        _assert_raw_state_contract(raw_state=raw_state, contract=contract)
        try:
            view_state = contract.model.model_validate(raw_state)
        except Exception as exc:
            raise InterfaceViewStateProviderError(
                "Interface view-state provider output does not match declared "
                "view contract: "
                + f"provider_ref={provider_ref!r} view_ref={contract.view_ref!r} "
                + f"state_model_ref={contract.state_model_ref!r}"
            ) from exc
        raw_payload = view_state.model_dump(mode="json", exclude_none=True)
        if not isinstance(raw_payload, Mapping):
            raise InterfaceViewStateProviderError(
                "Generated Interface view-state model did not dump to a mapping: "
                + f"provider_ref={provider_ref!r} view_ref={contract.view_ref!r}"
            )
        return InterfaceResolvedViewState(
            state=_json_object(raw_payload),
            view_ref=contract.view_ref,
            view_key=contract.view_key,
            state_model_ref=contract.state_model_ref,
            version=contract.version,
            registry_module=contract.registry_module,
            contract_validated=True,
        )

    model_dump = getattr(raw_state, "model_dump", None)
    if callable(model_dump):
        raw_state = model_dump(mode="json", exclude_none=True)
    if not isinstance(raw_state, Mapping):
        raise InterfaceViewStateProviderError(
            "Interface view-state provider must return a mapping or pydantic model: "
            + f"provider_ref={provider_ref!r} result_type={type(raw_state).__name__}"
        )
    identity = _pane_view_identity(provider_input.pane)
    return InterfaceResolvedViewState(
        state=_json_object(raw_state),
        view_ref=identity.view_ref,
        view_key=identity.view_key,
    )


def _pane_provider_ref(pane: object) -> str | None:
    raw_ref = getattr(pane, "state_provider_ref", None)
    if raw_ref is None:
        return None
    provider_ref = _normalize_provider_ref(str(raw_ref))
    return provider_ref or None


def _pane_provider_kind(pane: object) -> str:
    raw_kind = getattr(pane, "state_provider_kind", None)
    return (str(raw_kind).strip() if raw_kind is not None else "") or "runtime_callable"


def _normalize_provider_ref(provider_ref: str) -> str:
    return (provider_ref or "").strip()


def _pane_view_identity(pane: object) -> _PaneViewIdentity:
    return _PaneViewIdentity(
        view_ref=_optional_pane_text(pane, "view_ref"),
        view_key=_optional_pane_text(pane, "projection_view_key"),
    )


def _optional_pane_text(pane: object, attr: str) -> str | None:
    raw = getattr(pane, attr, None)
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _load_generated_view_model_contract(
    pane: object,
) -> _GeneratedViewModelContract | None:
    identity = _pane_view_identity(pane)
    view_ref = identity.view_ref
    if view_ref is None:
        return None

    experience_name = view_ref.split(".", 1)[0].strip()
    if not experience_name:
        return None
    registry_module_name = f"{experience_name}.view_model_registry"
    try:
        registry_module = import_module(registry_module_name)
    except ModuleNotFoundError as exc:
        if exc.name in {experience_name, registry_module_name}:
            return None
        raise InterfaceViewStateProviderError(
            "Failed to import generated Interface view-state registry: "
            + f"view_ref={view_ref!r} registry_module={registry_module_name!r}"
        ) from exc

    contracts = getattr(registry_module, "VIEW_MODEL_CONTRACTS", None)
    if contracts is None:
        return None

    view_key = identity.view_key
    for contract in contracts:
        contract_view_ref = _optional_contract_text(contract, "view_ref")
        contract_view_key = _optional_contract_text(contract, "view_key")
        if contract_view_ref != view_ref:
            continue
        if view_key is not None and contract_view_key != view_key:
            raise InterfaceViewStateProviderError(
                "Generated Interface view-state contract view key does not match "
                "resolved pane view key: "
                + f"view_ref={view_ref!r} expected_view_key={view_key!r} "
                + f"contract_view_key={contract_view_key!r}"
            )
        model = getattr(contract, "model", None)
        if model is None or not hasattr(model, "model_validate"):
            raise InterfaceViewStateProviderError(
                "Generated Interface view-state contract is missing a pydantic model: "
                + f"view_ref={view_ref!r} registry_module={registry_module_name!r}"
            )
        return _GeneratedViewModelContract(
            view_ref=contract_view_ref or view_ref,
            view_key=contract_view_key or view_key or "",
            state_model_ref=_optional_contract_text(contract, "state_model_ref") or "",
            version=_optional_contract_text(contract, "version") or "",
            model=model,
            registry_module=registry_module_name,
        )

    raise InterfaceViewStateProviderError(
        "Generated Interface view-state registry has no contract for resolved pane view: "
        + f"view_ref={view_ref!r} projection_view_key={view_key!r} "
        + f"registry_module={registry_module_name!r}"
    )


def _optional_contract_text(contract: object, attr: str) -> str | None:
    raw = getattr(contract, attr, None)
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _assert_raw_state_contract(
    *,
    raw_state: object,
    contract: _GeneratedViewModelContract,
) -> None:
    raw_view_ref = _optional_contract_text(raw_state, "VIEW_REF")
    raw_view_key = _optional_contract_text(raw_state, "VIEW_KEY")
    raw_state_model_ref = _optional_contract_text(raw_state, "STATE_MODEL_REF")
    mismatches: list[str] = []
    if raw_view_ref is not None and raw_view_ref != contract.view_ref:
        mismatches.append(f"VIEW_REF={raw_view_ref!r}")
    if raw_view_key is not None and raw_view_key != contract.view_key:
        mismatches.append(f"VIEW_KEY={raw_view_key!r}")
    if (
        raw_state_model_ref is not None
        and raw_state_model_ref != contract.state_model_ref
    ):
        mismatches.append(f"STATE_MODEL_REF={raw_state_model_ref!r}")
    if mismatches:
        raise InterfaceViewStateProviderError(
            "Interface view-state provider returned a model for the wrong "
            "view contract: "
            + f"expected_view_ref={contract.view_ref!r} "
            + f"expected_state_model_ref={contract.state_model_ref!r} "
            + f"actual={', '.join(mismatches)}"
        )


def _load_provider(provider_ref: str) -> ViewStateProviderCallable:
    registered = _REGISTERED_PROVIDERS.get(provider_ref)
    if registered is not None:
        return registered

    loaded = _LOADED_PROVIDERS.get(provider_ref)
    if loaded is not None:
        return loaded

    module_name, _, callable_name = provider_ref.rpartition(".")
    if not module_name or not callable_name:
        raise InterfaceViewStateProviderError(
            "Runtime callable view-state provider refs must be import paths: "
            + f"provider_ref={provider_ref!r}"
        )
    try:
        module = import_module(module_name)
        provider = getattr(module, callable_name)
    except Exception as exc:
        raise InterfaceViewStateProviderError(
            "Failed to load Interface view-state provider: "
            + f"provider_ref={provider_ref!r}"
        ) from exc
    if not callable(provider):
        raise InterfaceViewStateProviderError(
            f"Loaded Interface view-state provider is not callable: provider_ref={provider_ref!r}"
        )
    _LOADED_PROVIDERS[provider_ref] = provider
    return provider


def _load_provider_input_resolver(
    provider_ref: str,
    provider: ViewStateProviderCallable,
) -> ViewStateProviderInputResolverCallable:
    registered = _REGISTERED_PROVIDER_INPUT_RESOLVERS.get(provider_ref)
    if registered is not None:
        return registered

    loaded = _LOADED_PROVIDER_INPUT_RESOLVERS.get(provider_ref)
    if loaded is not None:
        return loaded

    resolver = getattr(provider, "provider_input_resolver", None)
    if resolver is None:
        resolver = getattr(provider, "VIEW_PROVIDER_INPUT_RESOLVER", None)
    if not callable(resolver):
        raise InterfaceViewStateProviderError(
            "Interface view-state provider requires an explicit provider input "
            "resolver: "
            + f"provider_ref={provider_ref!r}"
        )
    typed_resolver = cast(ViewStateProviderInputResolverCallable, resolver)
    _LOADED_PROVIDER_INPUT_RESOLVERS[provider_ref] = typed_resolver
    return typed_resolver


def _json_object(raw: Mapping[object, object]) -> JsonObject:
    return JsonObject(
        {
            str(key): _json_value(value)
            for key, value in raw.items()
            if value is not None
        }
    )


def _json_value(value: object) -> JsonValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Mapping):
        return cast(JsonValue, _json_object(value))
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_value(item) for item in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="json", exclude_none=True)
        if isinstance(dumped, Mapping):
            return cast(JsonValue, _json_object(dumped))
        return _json_value(dumped)
    return str(value)


__all__ = [
    "InterfaceResolvedViewState",
    "InterfaceViewStateProviderContext",
    "InterfaceViewStateProviderError",
    "InterfaceViewStateProviderInput",
    "register_view_state_provider",
    "register_view_state_provider_input_resolver",
    "reset_view_state_providers",
    "resolve_view_state",
]
