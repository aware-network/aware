from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    ContentDigest,
    ContractViolation,
    SemanticContractProviderDeclaration,
    SemanticContractRef,
    WireObject,
    canonical_json_bytes,
)


def _token(value: object, path: str) -> str:
    if (
        type(value) is not str
        or not value
        or any(character.isspace() for character in value)
    ):
        raise ContractViolation(f"{path} must be a nonempty token")
    return value


def _exact_tuple(value: object, expected: type, path: str) -> tuple:
    if type(value) is not tuple:
        raise TypeError(f"{path} must be exact tuple")
    for index, item in enumerate(value):
        if type(item) is not expected:
            raise TypeError(f"{path}[{index}] must be exact {expected.__name__}")
        item.to_wire()
    return value


@dataclass(frozen=True, slots=True, order=True)
class ProfileInputDeclaration:
    role: str
    contract: SemanticContractRef

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", _token(self.role, "profile_input.role"))
        if type(self.contract) is not SemanticContractRef:
            raise TypeError("profile_input.contract must be exact SemanticContractRef")
        self.contract.to_wire()

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {"contract": self.contract.to_wire(), "role": self.role}


@dataclass(frozen=True, slots=True, order=True)
class RoleBinding:
    target_role: str
    source_role: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "target_role", _token(self.target_role, "binding.target_role")
        )
        object.__setattr__(
            self, "source_role", _token(self.source_role, "binding.source_role")
        )

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {"source_role": self.source_role, "target_role": self.target_role}


@dataclass(frozen=True, slots=True, order=True)
class ProfileStepDeclaration:
    step_key: str
    provider_key: str
    bindings: tuple[RoleBinding, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "step_key", _token(self.step_key, "step.step_key"))
        object.__setattr__(
            self, "provider_key", _token(self.provider_key, "step.provider_key")
        )
        bindings = _exact_tuple(self.bindings, RoleBinding, "step.bindings")
        keys = tuple(item.target_role for item in bindings)
        if keys != tuple(sorted(set(keys), key=str.encode)):
            raise ContractViolation(
                "step bindings must be target-role unique and ordered"
            )

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {
            "bindings": [item.to_wire() for item in self.bindings],
            "provider_key": self.provider_key,
            "step_key": self.step_key,
        }


@dataclass(frozen=True, slots=True)
class SemanticContractProfileDeclaration:
    profile_ref: str
    version: str
    package_kinds: tuple[str, ...]
    operation_kinds: tuple[str, ...]
    inputs: tuple[ProfileInputDeclaration, ...]
    providers: tuple[SemanticContractProviderDeclaration, ...]
    steps: tuple[ProfileStepDeclaration, ...]
    terminal_result_role: str
    terminal_effect_role: str
    terminal_output_roles: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "profile_ref", _token(self.profile_ref, "profile.profile_ref")
        )
        object.__setattr__(self, "version", _token(self.version, "profile.version"))
        self._validate_tokens(
            self.package_kinds, "profile.package_kinds", nonempty=True
        )
        self._validate_tokens(
            self.operation_kinds, "profile.operation_kinds", nonempty=True
        )
        inputs = _exact_tuple(self.inputs, ProfileInputDeclaration, "profile.inputs")
        self._require_ordered_unique(
            tuple(item.role for item in inputs), "profile inputs"
        )
        providers = _exact_tuple(
            self.providers, SemanticContractProviderDeclaration, "profile.providers"
        )
        self._require_ordered_unique(
            tuple(item.provider_key for item in providers), "profile providers"
        )
        steps = _exact_tuple(self.steps, ProfileStepDeclaration, "profile.steps")
        self._require_ordered_unique(
            tuple(item.step_key for item in steps), "profile steps"
        )
        object.__setattr__(
            self,
            "terminal_result_role",
            _token(self.terminal_result_role, "profile.terminal_result_role"),
        )
        object.__setattr__(
            self,
            "terminal_effect_role",
            _token(self.terminal_effect_role, "profile.terminal_effect_role"),
        )
        self._validate_tokens(
            self.terminal_output_roles, "profile.terminal_output_roles"
        )
        resolve_profile(self)

    @staticmethod
    def _require_ordered_unique(values: tuple[str, ...], path: str) -> None:
        if values != tuple(sorted(set(values), key=str.encode)):
            raise ContractViolation(f"{path} must be unique and UTF-8 byte ordered")

    @classmethod
    def _validate_tokens(
        cls, value: object, path: str, *, nonempty: bool = False
    ) -> None:
        if type(value) is not tuple:
            raise TypeError(f"{path} must be exact tuple")
        values = tuple(
            _token(item, f"{path}[{index}]") for index, item in enumerate(value)
        )
        if nonempty and not values:
            raise ContractViolation(f"{path} must not be empty")
        cls._require_ordered_unique(values, path)

    @property
    def digest(self) -> ContentDigest:
        self.__post_init__()
        return ContentDigest.of_bytes(canonical_json_bytes(self._wire_without_digest()))

    def _wire_without_digest(self) -> WireObject:
        return {
            "inputs": [item.to_wire() for item in self.inputs],
            "operation_kinds": list(self.operation_kinds),
            "package_kinds": list(self.package_kinds),
            "profile_ref": self.profile_ref,
            "providers": [item.to_wire() for item in self.providers],
            "schema": "aware.code.semantic-contract-profile.v1",
            "steps": [item.to_wire() for item in self.steps],
            "terminal_effect_role": self.terminal_effect_role,
            "terminal_output_roles": list(self.terminal_output_roles),
            "terminal_result_role": self.terminal_result_role,
            "version": self.version,
        }

    def to_wire(self) -> WireObject:
        self.__post_init__()
        return {**self._wire_without_digest(), "digest": self.digest.to_wire()}


def resolve_profile(
    profile: SemanticContractProfileDeclaration,
) -> tuple[ProfileStepDeclaration, ...]:
    if type(profile) is not SemanticContractProfileDeclaration:
        raise TypeError("profile must be exact SemanticContractProfileDeclaration")

    providers = {item.provider_key: item for item in profile.providers}
    producers: dict[str, tuple[str | None, SemanticContractRef]] = {
        item.role: (None, item.contract) for item in profile.inputs
    }
    for step in profile.steps:
        provider = providers.get(step.provider_key)
        if provider is None:
            raise ContractViolation(
                f"step {step.step_key} selects an undeclared provider"
            )
        for produced in (
            provider.result_role,
            provider.effect_role,
            *provider.output_roles,
        ):
            if produced.role in producers:
                raise ContractViolation(f"role {produced.role} has multiple producers")
            producers[produced.role] = (step.step_key, produced.contract)

    dependencies: dict[str, set[str]] = {step.step_key: set() for step in profile.steps}
    for step in profile.steps:
        provider = providers[step.provider_key]
        bindings = {item.target_role: item.source_role for item in step.bindings}
        expected = {item.role for item in provider.consumed_roles}
        required = {item.role for item in provider.consumed_roles if item.required}
        if not required.issubset(bindings) or not set(bindings).issubset(expected):
            raise ContractViolation(
                f"step {step.step_key} does not bind its exact consumed closure"
            )
        for consumed in provider.consumed_roles:
            if consumed.role not in bindings:
                continue
            source = producers.get(bindings[consumed.role])
            if source is None:
                raise ContractViolation(
                    f"step {step.step_key} binds an unknown source role"
                )
            source_step, source_contract = source
            if source_contract not in consumed.accepted_contracts:
                raise ContractViolation(
                    f"step {step.step_key} binds an incompatible contract"
                )
            if source_step is not None:
                dependencies[step.step_key].add(source_step)

    for role, expected_kind in (
        (profile.terminal_result_role, "result"),
        (profile.terminal_effect_role, "effect"),
    ):
        if role not in producers or producers[role][0] is None:
            raise ContractViolation(
                f"terminal {expected_kind} role has no provider producer"
            )
    for role in profile.terminal_output_roles:
        if role not in producers or producers[role][0] is None:
            raise ContractViolation(
                f"terminal output role {role} has no provider producer"
            )

    remaining = {key: set(value) for key, value in dependencies.items()}
    step_by_key = {item.step_key: item for item in profile.steps}
    ordered: list[ProfileStepDeclaration] = []
    while remaining:
        ready = sorted(
            (key for key, value in remaining.items() if not value), key=str.encode
        )
        if not ready:
            raise ContractViolation("profile role graph contains a cycle")
        for key in ready:
            ordered.append(step_by_key[key])
            del remaining[key]
            for value in remaining.values():
                value.discard(key)
    return tuple(ordered)


__all__ = [
    "ProfileInputDeclaration",
    "ProfileStepDeclaration",
    "RoleBinding",
    "SemanticContractProfileDeclaration",
    "resolve_profile",
]
