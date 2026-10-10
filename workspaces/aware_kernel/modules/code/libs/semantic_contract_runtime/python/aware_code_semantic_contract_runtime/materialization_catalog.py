"""Code-owned semantic materialization catalog and exact matching."""

from __future__ import annotations

import hashlib
import inspect
import json
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from threading import RLock
from types import MethodType
from typing import Never, Protocol, cast
from weakref import WeakKeyDictionary

from .contracts import (
    ConsumedRoleDeclaration,
    ContentDigest,
    ContractViolation,
    ProducedRoleDeclaration,
    ProviderExecutionBinding,
    SemanticConfigurationCoordinate,
    SemanticContractProviderDeclaration,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    SemanticPackageCoordinate,
    canonical_json_bytes,
)
from .dependency_inputs import SemanticDependencyPlanningInput
from .materialization_planning import (
    CodeComposedSemanticMaterializationIntent,
    CodeSemanticMaterializationIntent,
    CodeSemanticRequiredResultProduct,
    SemanticDependencyDemand,
    SemanticDependencyDemandSet,
    _compose_prevalidated_dependency_demands,
)
from .profile import (
    ProfileInputDeclaration,
    ProfileStepDeclaration,
    RoleBinding,
    SemanticContractProfileDeclaration,
)
from .retained_input_projection_codec import DependencyPlanningInputCodec

CODE_SEMANTIC_MATERIALIZATION_PROFILE_BINDING = (
    "aware.code.semantic-materialization-profile-binding.v1"
)
CODE_SEMANTIC_CONTRACT_CATALOG = "aware.code.semantic-contract-catalog.v1"
CODE_SEMANTIC_PACKAGE_PLANNING_CONTEXT = (
    "aware.code.semantic-package-planning-context.v1"
)
CODE_SEMANTIC_CONTRACT_MATCH = "aware.code.semantic-contract-match.v1"
CODE_SEMANTIC_CONTRACT_MATCH_ADMISSION = (
    "aware.code.semantic-contract-match-admission.v1"
)
_INTERNAL_JSON_ENCODER = json.JSONEncoder(
    ensure_ascii=False,
    allow_nan=False,
    sort_keys=True,
    separators=(",", ":"),
)


def _digest(contract: str, payload: Mapping[str, object]) -> ContentDigest:
    value = (
        "sha256:"
        + hashlib.sha256(
            _INTERNAL_JSON_ENCODER.encode({"contract": contract, **payload}).encode(
                "utf-8"
            )
        ).hexdigest()
    )
    return _frozen_value(ContentDigest, value=value)


def _token(value: object, path: str) -> str:
    if (
        type(value) is not str
        or not value
        or any(character.isspace() for character in value)
    ):
        raise TypeError(f"{path} must be nonempty token text")
    return value


def _nonnegative(value: object, path: str) -> int:
    if type(value) is not int or value < 0:
        raise TypeError(f"{path} must be exact nonnegative integer")
    return value


def _exact[T](value: object, expected: type[T], path: str) -> T:
    if type(value) is not expected:
        raise TypeError(f"{path} must be exact {expected.__name__}")
    return value


def _frozen_value[T](expected: type[T], **fields: object) -> T:
    result = object.__new__(expected)
    for name, value in fields.items():
        object.__setattr__(result, name, value)
    return result


def _exact_tuple[T](value: object, expected: type[T], path: str) -> tuple[T, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{path} must be exact tuple")
    result: list[T] = []
    for index, item in enumerate(value):
        result.append(_exact(item, expected, f"{path}[{index}]"))
    return tuple(result)


def _token_tuple(
    value: object, path: str, *, nonempty: bool = False
) -> tuple[str, ...]:
    values = _exact_tuple(value, str, path)
    result = tuple(
        _token(item, f"{path}[{index}]") for index, item in enumerate(values)
    )
    if nonempty and not result:
        raise ContractViolation(f"{path} must not be empty")
    if result != tuple(sorted(set(result), key=str.encode)):
        raise ContractViolation(f"{path} must be unique and ordered")
    return result


def _validated_tuple[T](
    value: object, expected: type[T], path: str, *, nonempty: bool = False
) -> tuple[T, ...]:
    values = _exact_tuple(value, expected, path)
    if nonempty and not values:
        raise ContractViolation(f"{path} must not be empty")
    for item in values:
        post_init = getattr(item, "__post_init__", None)
        if not callable(post_init):
            raise TypeError(f"{path} item lacks module validation")
        post_init()
    return values


def _canonical_tuple[T](
    value: object,
    expected: type[T],
    path: str,
    *,
    key: Callable[[T], bytes],
    nonempty: bool = False,
) -> tuple[T, ...]:
    values = _validated_tuple(value, expected, path, nonempty=nonempty)
    keys = tuple(key(item) for item in values)
    if keys != tuple(sorted(set(keys))):
        raise ContractViolation(f"{path} must be unique and canonical")
    return values


@dataclass(frozen=True, slots=True)
class CodeSemanticMaterializationProfileBinding:
    semantic_owner_key: str
    semantic_provider_key: str
    package_families: tuple[str, ...]
    package_roles: tuple[str, ...]
    manifest_contracts: tuple[SemanticContractRef, ...]
    profile_declaration: SemanticContractProfileDeclaration
    provider_execution_bindings: tuple[ProviderExecutionBinding, ...]
    dependency_planner_contract: SemanticContractRef
    dependency_planner_implementation: SemanticImplementationCoordinate
    dependency_planner_configuration: SemanticConfigurationCoordinate
    dependency_demand_contract: SemanticContractRef
    dependency_target_intent_contract: SemanticContractRef
    result_product_contracts: tuple[CodeSemanticRequiredResultProduct, ...]
    priority: int
    binding_digest: ContentDigest

    @classmethod
    def create(cls, **values: object) -> CodeSemanticMaterializationProfileBinding:
        payload = _binding_payload(**values)
        return _frozen_value(
            cls,
            **values,
            binding_digest=_digest(
                CODE_SEMANTIC_MATERIALIZATION_PROFILE_BINDING, payload
            ),
        )

    def __post_init__(self) -> None:
        payload = _binding_payload(
            semantic_owner_key=self.semantic_owner_key,
            semantic_provider_key=self.semantic_provider_key,
            package_families=self.package_families,
            package_roles=self.package_roles,
            manifest_contracts=self.manifest_contracts,
            profile_declaration=self.profile_declaration,
            provider_execution_bindings=self.provider_execution_bindings,
            dependency_planner_contract=self.dependency_planner_contract,
            dependency_planner_implementation=self.dependency_planner_implementation,
            dependency_planner_configuration=self.dependency_planner_configuration,
            dependency_demand_contract=self.dependency_demand_contract,
            dependency_target_intent_contract=self.dependency_target_intent_contract,
            result_product_contracts=self.result_product_contracts,
            priority=self.priority,
        )
        _exact(
            self.binding_digest, ContentDigest, "binding.binding_digest"
        ).__post_init__()
        if self.binding_digest != _digest(
            CODE_SEMANTIC_MATERIALIZATION_PROFILE_BINDING, payload
        ):
            raise ContractViolation("profile binding digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": CODE_SEMANTIC_MATERIALIZATION_PROFILE_BINDING,
            **_binding_payload(
                semantic_owner_key=self.semantic_owner_key,
                semantic_provider_key=self.semantic_provider_key,
                package_families=self.package_families,
                package_roles=self.package_roles,
                manifest_contracts=self.manifest_contracts,
                profile_declaration=self.profile_declaration,
                provider_execution_bindings=self.provider_execution_bindings,
                dependency_planner_contract=self.dependency_planner_contract,
                dependency_planner_implementation=self.dependency_planner_implementation,
                dependency_planner_configuration=self.dependency_planner_configuration,
                dependency_demand_contract=self.dependency_demand_contract,
                dependency_target_intent_contract=self.dependency_target_intent_contract,
                result_product_contracts=self.result_product_contracts,
                priority=self.priority,
            ),
            "binding_digest": self.binding_digest.to_wire(),
        }


def _binding_payload(**values: object) -> dict[str, object]:
    profile = _exact(
        values["profile_declaration"],
        SemanticContractProfileDeclaration,
        "binding.profile_declaration",
    )
    profile.__post_init__()
    provider_bindings = _canonical_tuple(
        values["provider_execution_bindings"],
        ProviderExecutionBinding,
        "binding.provider_execution_bindings",
        key=lambda item: item.provider_key.encode(),
        nonempty=True,
    )
    if tuple(item.provider_key for item in provider_bindings) != tuple(
        item.provider_key for item in profile.providers
    ):
        raise ContractViolation("profile providers and execution bindings differ")
    manifest_contracts = _canonical_tuple(
        values["manifest_contracts"],
        SemanticContractRef,
        "binding.manifest_contracts",
        key=lambda item: canonical_json_bytes(item.to_wire()),
        nonempty=True,
    )
    results = _validated_tuple(
        values["result_product_contracts"],
        CodeSemanticRequiredResultProduct,
        "binding.result_product_contracts",
        nonempty=True,
    )
    if tuple(item.role for item in results) != tuple(
        sorted({item.role for item in results}, key=str.encode)
    ):
        raise ContractViolation(
            "binding result products must be role-unique and ordered"
        )
    produced: dict[str, SemanticContractRef] = {}
    for provider in profile.providers:
        for role in (
            provider.result_role,
            provider.effect_role,
            *provider.output_roles,
        ):
            produced[role.role] = role.contract
    terminal_roles = (
        profile.terminal_result_role,
        profile.terminal_effect_role,
        *profile.terminal_output_roles,
    )
    expected = {role: produced[role] for role in terminal_roles if role in produced}
    if {item.role: item.contract for item in results} != expected:
        raise ContractViolation(
            "binding result products do not close profile terminals"
        )
    planner_contract = _exact(
        values["dependency_planner_contract"],
        SemanticContractRef,
        "binding.dependency_planner_contract",
    )
    planner_implementation = _exact(
        values["dependency_planner_implementation"],
        SemanticImplementationCoordinate,
        "binding.dependency_planner_implementation",
    )
    planner_configuration = _exact(
        values["dependency_planner_configuration"],
        SemanticConfigurationCoordinate,
        "binding.dependency_planner_configuration",
    )
    demand_contract = _exact(
        values["dependency_demand_contract"],
        SemanticContractRef,
        "binding.dependency_demand_contract",
    )
    intent_contract = _exact(
        values["dependency_target_intent_contract"],
        SemanticContractRef,
        "binding.dependency_target_intent_contract",
    )
    for item in (
        planner_contract,
        planner_implementation,
        planner_configuration,
        demand_contract,
        intent_contract,
    ):
        item.__post_init__()
    return {
        "dependency_demand_contract": demand_contract.to_wire(),
        "dependency_planner_configuration": planner_configuration.to_wire(),
        "dependency_planner_contract": planner_contract.to_wire(),
        "dependency_planner_implementation": planner_implementation.to_wire(),
        "dependency_target_intent_contract": intent_contract.to_wire(),
        "manifest_contracts": [item.to_wire() for item in manifest_contracts],
        "package_families": list(
            _token_tuple(
                values["package_families"], "binding.package_families", nonempty=True
            )
        ),
        "package_roles": list(
            _token_tuple(
                values["package_roles"], "binding.package_roles", nonempty=True
            )
        ),
        "priority": _nonnegative(values["priority"], "binding.priority"),
        "profile_declaration": profile.to_wire(),
        "provider_execution_bindings": [item.to_wire() for item in provider_bindings],
        "result_product_contracts": [item.to_wire() for item in results],
        "semantic_owner_key": _token(
            values["semantic_owner_key"], "binding.semantic_owner_key"
        ),
        "semantic_provider_key": _token(
            values["semantic_provider_key"], "binding.semantic_provider_key"
        ),
    }


@dataclass(frozen=True, slots=True)
class CodeSemanticContractCatalog:
    catalog_ref: str
    catalog_generation: int
    entries: tuple[CodeSemanticMaterializationProfileBinding, ...]
    catalog_root_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        catalog_ref: str,
        catalog_generation: int,
        entries: tuple[CodeSemanticMaterializationProfileBinding, ...],
    ) -> CodeSemanticContractCatalog:
        payload = _catalog_payload(
            catalog_ref=catalog_ref,
            catalog_generation=catalog_generation,
            entries=entries,
        )
        return cls(
            catalog_ref=catalog_ref,
            catalog_generation=catalog_generation,
            entries=entries,
            catalog_root_digest=_digest(CODE_SEMANTIC_CONTRACT_CATALOG, payload),
        )

    def __post_init__(self) -> None:
        payload = _catalog_payload(
            catalog_ref=self.catalog_ref,
            catalog_generation=self.catalog_generation,
            entries=self.entries,
        )
        _exact(self.catalog_root_digest, ContentDigest, "catalog.root").__post_init__()
        if self.catalog_root_digest != _digest(CODE_SEMANTIC_CONTRACT_CATALOG, payload):
            raise ContractViolation("Code catalog root mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": CODE_SEMANTIC_CONTRACT_CATALOG,
            **_catalog_payload(
                catalog_ref=self.catalog_ref,
                catalog_generation=self.catalog_generation,
                entries=self.entries,
            ),
            "catalog_root_digest": self.catalog_root_digest.to_wire(),
        }


def _catalog_payload(**values: object) -> dict[str, object]:
    entries = _validated_tuple(
        values["entries"],
        CodeSemanticMaterializationProfileBinding,
        "catalog.entries",
    )
    keys = tuple(
        (
            item.semantic_owner_key,
            item.semantic_provider_key,
            item.profile_declaration.profile_ref,
            item.profile_declaration.digest.value,
        )
        for item in entries
    )
    if keys != tuple(
        sorted(set(keys), key=lambda item: tuple(part.encode() for part in item))
    ):
        raise ContractViolation("Code catalog entries must be unique and ordered")
    return {
        "catalog_generation": _nonnegative(
            values["catalog_generation"], "catalog.generation"
        ),
        "catalog_ref": _token(values["catalog_ref"], "catalog.ref"),
        "entries": [item.to_wire() for item in entries],
    }


@dataclass(frozen=True, slots=True)
class CodeSemanticPackagePlanningContext:
    package: SemanticPackageCoordinate
    package_family: str
    package_role: str
    manifest_contract: SemanticContractRef
    code_intent: CodeSemanticMaterializationIntent
    required_result_products: tuple[CodeSemanticRequiredResultProduct, ...]
    required_semantic_provider_keys: tuple[str, ...]
    context_digest: ContentDigest

    @classmethod
    def create(cls, **values: object) -> CodeSemanticPackagePlanningContext:
        payload = _context_payload(**values)
        return _frozen_value(
            cls,
            **values,
            context_digest=_digest(CODE_SEMANTIC_PACKAGE_PLANNING_CONTEXT, payload),
        )

    def __post_init__(self) -> None:
        payload = _context_payload(
            package=self.package,
            package_family=self.package_family,
            package_role=self.package_role,
            manifest_contract=self.manifest_contract,
            code_intent=self.code_intent,
            required_result_products=self.required_result_products,
            required_semantic_provider_keys=self.required_semantic_provider_keys,
        )
        _exact(self.context_digest, ContentDigest, "context.digest").__post_init__()
        if self.context_digest != _digest(
            CODE_SEMANTIC_PACKAGE_PLANNING_CONTEXT, payload
        ):
            raise ContractViolation("planning context digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": CODE_SEMANTIC_PACKAGE_PLANNING_CONTEXT,
            **_context_payload(
                package=self.package,
                package_family=self.package_family,
                package_role=self.package_role,
                manifest_contract=self.manifest_contract,
                code_intent=self.code_intent,
                required_result_products=self.required_result_products,
                required_semantic_provider_keys=self.required_semantic_provider_keys,
            ),
            "context_digest": self.context_digest.to_wire(),
        }


def _context_payload(**values: object) -> dict[str, object]:
    package = _exact(values["package"], SemanticPackageCoordinate, "context.package")
    manifest = _exact(
        values["manifest_contract"], SemanticContractRef, "context.manifest_contract"
    )
    intent = _exact(
        values["code_intent"], CodeSemanticMaterializationIntent, "context.intent"
    )
    for item in (package, manifest, intent):
        item.__post_init__()
    requirements = _validated_tuple(
        values["required_result_products"],
        CodeSemanticRequiredResultProduct,
        "context.required_result_products",
        nonempty=True,
    )
    roles = tuple(item.role for item in requirements)
    if roles != tuple(sorted(set(roles), key=str.encode)):
        raise ContractViolation(
            "context result requirements must be role-unique and ordered"
        )
    if roles != intent.requested_terminal_output_roles:
        raise ContractViolation(
            "context requirements differ from intent terminal roles"
        )
    return {
        "code_intent": intent.to_wire(),
        "manifest_contract": manifest.to_wire(),
        "package": package.to_wire(),
        "package_family": _token(values["package_family"], "context.package_family"),
        "package_role": _token(values["package_role"], "context.package_role"),
        "required_result_products": [item.to_wire() for item in requirements],
        "required_semantic_provider_keys": list(
            _token_tuple(
                values["required_semantic_provider_keys"],
                "context.required_semantic_provider_keys",
            )
        ),
    }


@dataclass(frozen=True, slots=True)
class CodeSemanticContractMatch:
    context_digest: ContentDigest
    selected_entry_digest: ContentDigest
    selected_binding: CodeSemanticMaterializationProfileBinding
    match_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        context: CodeSemanticPackagePlanningContext,
        selected_binding: CodeSemanticMaterializationProfileBinding,
    ) -> CodeSemanticContractMatch:
        _exact(
            context, CodeSemanticPackagePlanningContext, "match.context"
        ).__post_init__()
        _exact(
            selected_binding, CodeSemanticMaterializationProfileBinding, "match.binding"
        ).__post_init__()
        payload = _match_payload(
            context_digest=context.context_digest,
            selected_entry_digest=selected_binding.binding_digest,
            selected_binding=selected_binding,
        )
        return cls(
            context_digest=context.context_digest,
            selected_entry_digest=selected_binding.binding_digest,
            selected_binding=selected_binding,
            match_digest=_digest(CODE_SEMANTIC_CONTRACT_MATCH, payload),
        )

    def __post_init__(self) -> None:
        payload = _match_payload(
            context_digest=self.context_digest,
            selected_entry_digest=self.selected_entry_digest,
            selected_binding=self.selected_binding,
        )
        if _exact(self.match_digest, ContentDigest, "match.digest") != _digest(
            CODE_SEMANTIC_CONTRACT_MATCH, payload
        ):
            raise ContractViolation("Code semantic match digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": CODE_SEMANTIC_CONTRACT_MATCH,
            **_match_payload(
                context_digest=self.context_digest,
                selected_entry_digest=self.selected_entry_digest,
                selected_binding=self.selected_binding,
            ),
            "match_digest": self.match_digest.to_wire(),
        }


def _match_payload(**values: object) -> dict[str, object]:
    context_digest = _exact(
        values["context_digest"], ContentDigest, "match.context_digest"
    )
    entry_digest = _exact(
        values["selected_entry_digest"], ContentDigest, "match.entry_digest"
    )
    binding = _exact(
        values["selected_binding"],
        CodeSemanticMaterializationProfileBinding,
        "match.selected_binding",
    )
    for item in (context_digest, entry_digest):
        item.__post_init__()
    binding.__post_init__()
    if entry_digest != binding.binding_digest:
        raise ContractViolation("match entry digest differs from binding")
    return {
        "context_digest": context_digest.to_wire(),
        "selected_binding": binding.to_wire(),
        "selected_entry_digest": entry_digest.to_wire(),
    }


@dataclass(frozen=True, slots=True)
class CodeSemanticContractMatchAdmission:
    match_digest: ContentDigest
    catalog_ref: str
    catalog_generation: int
    catalog_root_digest: ContentDigest
    admission_digest: ContentDigest

    @classmethod
    def create(
        cls,
        *,
        match: CodeSemanticContractMatch,
        catalog: CodeSemanticContractCatalog,
    ) -> CodeSemanticContractMatchAdmission:
        _exact(match, CodeSemanticContractMatch, "admission.match").__post_init__()
        _exact(
            catalog, CodeSemanticContractCatalog, "admission.catalog"
        ).__post_init__()
        if all(
            item.binding_digest != match.selected_entry_digest
            for item in catalog.entries
        ):
            raise ContractViolation("match entry is absent from Code catalog")
        payload = _admission_payload(
            match_digest=match.match_digest,
            catalog_ref=catalog.catalog_ref,
            catalog_generation=catalog.catalog_generation,
            catalog_root_digest=catalog.catalog_root_digest,
        )
        return cls(
            match_digest=match.match_digest,
            catalog_ref=catalog.catalog_ref,
            catalog_generation=catalog.catalog_generation,
            catalog_root_digest=catalog.catalog_root_digest,
            admission_digest=_digest(CODE_SEMANTIC_CONTRACT_MATCH_ADMISSION, payload),
        )

    def __post_init__(self) -> None:
        payload = _admission_payload(
            match_digest=self.match_digest,
            catalog_ref=self.catalog_ref,
            catalog_generation=self.catalog_generation,
            catalog_root_digest=self.catalog_root_digest,
        )
        if _exact(self.admission_digest, ContentDigest, "admission.digest") != _digest(
            CODE_SEMANTIC_CONTRACT_MATCH_ADMISSION, payload
        ):
            raise ContractViolation("match admission digest mismatched")

    def to_wire(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "contract": CODE_SEMANTIC_CONTRACT_MATCH_ADMISSION,
            **_admission_payload(
                match_digest=self.match_digest,
                catalog_ref=self.catalog_ref,
                catalog_generation=self.catalog_generation,
                catalog_root_digest=self.catalog_root_digest,
            ),
            "admission_digest": self.admission_digest.to_wire(),
        }


def _admission_payload(**values: object) -> dict[str, object]:
    match_digest = _exact(
        values["match_digest"], ContentDigest, "admission.match_digest"
    )
    root = _exact(
        values["catalog_root_digest"], ContentDigest, "admission.catalog_root"
    )
    match_digest.__post_init__()
    root.__post_init__()
    return {
        "catalog_generation": _nonnegative(
            values["catalog_generation"], "admission.catalog_generation"
        ),
        "catalog_ref": _token(values["catalog_ref"], "admission.catalog_ref"),
        "catalog_root_digest": root.to_wire(),
        "match_digest": match_digest.to_wire(),
    }


@dataclass(frozen=True, slots=True)
class _CatalogAdmissionState:
    catalog: CodeSemanticContractCatalog
    dependency_planners: dict[ContentDigest, CodeSemanticDependencyPlanner]
    planner_entrances: dict[ContentDigest, tuple[object, MethodType]]
    executable_closure: tuple[object, ...]
    host_liveness: Callable[[], bool]


_CATALOG_ADMISSIONS: WeakKeyDictionary[
    AdmittedCodeSemanticContractCatalog, _CatalogAdmissionState
] = WeakKeyDictionary()
_CATALOG_ADMISSION_LOCK = RLock()


class AdmittedCodeSemanticContractCatalog:
    def __new__(cls) -> AdmittedCodeSemanticContractCatalog:  # noqa: PYI034
        raise TypeError("Code catalog admission is module-issued only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("Code catalog admission is sealed")

    def __reduce__(self) -> Never:
        raise TypeError("Code catalog admission is not serializable")


class CodeSemanticDependencyPlanner(Protocol):
    async def plan(
        self,
        *,
        package: SemanticPackageCoordinate,
        intent: CodeSemanticMaterializationIntent,
        selected_match: CodeSemanticContractMatch,
        planning_input: SemanticDependencyPlanningInput,
    ) -> SemanticDependencyDemandSet: ...


@dataclass(frozen=True, slots=True)
class _ExecutableBinding:
    implementation: SemanticImplementationCoordinate
    configuration: SemanticConfigurationCoordinate
    executable: object


def _host_executable_bindings(
    value: object, path: str
) -> tuple[_ExecutableBinding, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{path} must be exact tuple")
    result: list[_ExecutableBinding] = []
    coordinates: set[
        tuple[SemanticImplementationCoordinate, SemanticConfigurationCoordinate]
    ] = set()
    for index, item in enumerate(value):
        if type(item) is not tuple or len(item) != 3:
            raise TypeError(f"{path}[{index}] must be exact three-item tuple")
        implementation = _exact(
            item[0], SemanticImplementationCoordinate, f"{path}[{index}].implementation"
        )
        configuration = _exact(
            item[1], SemanticConfigurationCoordinate, f"{path}[{index}].configuration"
        )
        implementation.__post_init__()
        configuration.__post_init__()
        if item[2] is None:
            raise TypeError(f"{path}[{index}].executable must be an object")
        coordinate = (implementation, configuration)
        if coordinate in coordinates:
            raise ContractViolation(f"{path} contains duplicate executable coordinate")
        coordinates.add(coordinate)
        result.append(_ExecutableBinding(implementation, configuration, item[2]))
    return tuple(result)


def _issue_code_semantic_contract_catalog(
    *,
    catalog: CodeSemanticContractCatalog,
    provider_executable_bindings: tuple[
        tuple[
            SemanticImplementationCoordinate,
            SemanticConfigurationCoordinate,
            object,
        ],
        ...,
    ],
    dependency_planner_bindings: tuple[
        tuple[
            SemanticImplementationCoordinate,
            SemanticConfigurationCoordinate,
            CodeSemanticDependencyPlanner,
        ],
        ...,
    ],
    host_liveness: Callable[[], bool],
) -> AdmittedCodeSemanticContractCatalog:
    catalog = _detached_catalog_snapshot(catalog)
    if not callable(host_liveness) or host_liveness() is not True:
        raise ContractViolation("Code catalog host admission is not live")
    provider_bindings = _host_executable_bindings(
        provider_executable_bindings, "provider_executable_bindings"
    )
    planner_bindings = _host_executable_bindings(
        dependency_planner_bindings, "dependency_planner_bindings"
    )
    provider_by_coordinate = {
        (item.implementation, item.configuration): item.executable
        for item in provider_bindings
    }
    planner_by_coordinate = {
        (item.implementation, item.configuration): item.executable
        for item in planner_bindings
    }
    required_providers = {
        (binding.implementation, binding.configuration)
        for entry in catalog.entries
        for binding in entry.provider_execution_bindings
    }
    required_planners = {
        (
            entry.dependency_planner_implementation,
            entry.dependency_planner_configuration,
        )
        for entry in catalog.entries
    }
    if set(provider_by_coordinate) != required_providers:
        raise ContractViolation(
            "deployment provider executable closure differs from Code catalog"
        )
    if set(planner_by_coordinate) != required_planners:
        raise ContractViolation(
            "deployment planner executable closure differs from Code catalog"
        )
    if host_liveness() is not True:
        raise ContractViolation("Code catalog host admission moved")
    planners_by_binding: dict[ContentDigest, CodeSemanticDependencyPlanner] = {
        entry.binding_digest: cast(
            CodeSemanticDependencyPlanner,
            planner_by_coordinate[
                (
                    entry.dependency_planner_implementation,
                    entry.dependency_planner_configuration,
                )
            ],
        )
        for entry in catalog.entries
    }
    planner_entrances = {}
    for digest, planner in planners_by_binding.items():
        descriptor = inspect.getattr_static(planner, "plan")
        entrance = planner.plan
        if not inspect.ismethod(entrance) or entrance.__self__ is not planner:
            raise ContractViolation("original bound dependency planner required")
        planner_entrances[digest] = (descriptor, entrance)
    result = object.__new__(AdmittedCodeSemanticContractCatalog)
    with _CATALOG_ADMISSION_LOCK:
        _CATALOG_ADMISSIONS[result] = _CatalogAdmissionState(
            catalog=catalog,
            dependency_planners=planners_by_binding,
            planner_entrances=planner_entrances,
            executable_closure=tuple(
                item.executable for item in (*provider_bindings, *planner_bindings)
            ),
            host_liveness=host_liveness,
        )
    return result


def _original_planner_entrance(state, digest):
    planner = state.dependency_planners.get(digest)
    retained = state.planner_entrances.get(digest)
    if planner is None or retained is None:
        raise ContractViolation("original catalog planner entrance unavailable")
    descriptor, entrance = retained
    if (
        entrance.__self__ is not planner
        or inspect.getattr_static(planner, "plan") is not descriptor
    ):
        raise ContractViolation("original catalog planner entrance substituted")
    return entrance


def _catalog_snapshot_bytes(value: object, path: str) -> bytes:
    catalog = _exact(value, CodeSemanticContractCatalog, path)
    return canonical_json_bytes(catalog.to_wire())


def _detached_catalog_snapshot(
    catalog: CodeSemanticContractCatalog,
) -> CodeSemanticContractCatalog:
    """Capture one byte-stable catalog graph without retaining caller aliases."""

    initial = _catalog_snapshot_bytes(catalog, "catalog")
    snapshot = deepcopy(catalog)
    admitted = _exact(snapshot, CodeSemanticContractCatalog, "catalog.snapshot")
    if _catalog_snapshot_bytes(admitted, "catalog.snapshot") != initial:
        raise ContractViolation("Code catalog changed while snapshotting")
    if _catalog_snapshot_bytes(catalog, "catalog") != initial:
        raise ContractViolation("Code catalog changed while snapshotting")
    return admitted


def _slot_descriptors(owner: type, names: tuple[str, ...]) -> tuple[object, ...]:
    namespace = owner.__dict__
    return tuple(namespace[name] for name in names)


_DIGEST_FIELDS = ("value",)
_DIGEST_SLOTS = _slot_descriptors(ContentDigest, _DIGEST_FIELDS)
_CONTRACT_FIELDS = ("key", "version", "schema_digest")
_CONTRACT_SLOTS = _slot_descriptors(SemanticContractRef, _CONTRACT_FIELDS)
_IMPLEMENTATION_FIELDS = ("implementation_ref", "closure_digest")
_IMPLEMENTATION_SLOTS = _slot_descriptors(
    SemanticImplementationCoordinate, _IMPLEMENTATION_FIELDS
)
_CONFIGURATION_FIELDS = ("configuration_ref", "digest")
_CONFIGURATION_SLOTS = _slot_descriptors(
    SemanticConfigurationCoordinate, _CONFIGURATION_FIELDS
)
_CONSUMED_FIELDS = ("role", "accepted_contracts", "required")
_CONSUMED_SLOTS = _slot_descriptors(ConsumedRoleDeclaration, _CONSUMED_FIELDS)
_PRODUCED_FIELDS = ("role", "contract")
_PRODUCED_SLOTS = _slot_descriptors(ProducedRoleDeclaration, _PRODUCED_FIELDS)
_PROVIDER_FIELDS = (
    "provider_key",
    "provider_contract",
    "package_kinds",
    "operation_kinds",
    "consumed_roles",
    "result_role",
    "transition_contract",
    "effect_role",
    "effect_contract",
    "output_roles",
    "allows_typed_empty",
    "predecessor_required",
    "terminal_statuses",
    "counter_keys",
)
_PROVIDER_SLOTS = _slot_descriptors(
    SemanticContractProviderDeclaration, _PROVIDER_FIELDS
)
_EXECUTION_FIELDS = ("provider_key", "implementation", "configuration")
_EXECUTION_SLOTS = _slot_descriptors(ProviderExecutionBinding, _EXECUTION_FIELDS)
_INPUT_FIELDS = ("role", "contract")
_INPUT_SLOTS = _slot_descriptors(ProfileInputDeclaration, _INPUT_FIELDS)
_ROLE_BINDING_FIELDS = ("target_role", "source_role")
_ROLE_BINDING_SLOTS = _slot_descriptors(RoleBinding, _ROLE_BINDING_FIELDS)
_STEP_FIELDS = ("step_key", "provider_key", "bindings")
_STEP_SLOTS = _slot_descriptors(ProfileStepDeclaration, _STEP_FIELDS)
_PROFILE_FIELDS = (
    "profile_ref",
    "version",
    "package_kinds",
    "operation_kinds",
    "inputs",
    "providers",
    "steps",
    "terminal_result_role",
    "terminal_effect_role",
    "terminal_output_roles",
)
_PROFILE_SLOTS = _slot_descriptors(SemanticContractProfileDeclaration, _PROFILE_FIELDS)
_REQUIREMENT_FIELDS = ("role", "contract", "requirement_digest")
_REQUIREMENT_SLOTS = _slot_descriptors(
    CodeSemanticRequiredResultProduct, _REQUIREMENT_FIELDS
)
_BINDING_FIELDS = (
    "semantic_owner_key",
    "semantic_provider_key",
    "package_families",
    "package_roles",
    "manifest_contracts",
    "profile_declaration",
    "provider_execution_bindings",
    "dependency_planner_contract",
    "dependency_planner_implementation",
    "dependency_planner_configuration",
    "dependency_demand_contract",
    "dependency_target_intent_contract",
    "result_product_contracts",
    "priority",
    "binding_digest",
)
_BINDING_SLOTS = _slot_descriptors(
    CodeSemanticMaterializationProfileBinding, _BINDING_FIELDS
)
_CATALOG_FIELDS = (
    "catalog_ref",
    "catalog_generation",
    "entries",
    "catalog_root_digest",
)
_CATALOG_SLOTS = _slot_descriptors(CodeSemanticContractCatalog, _CATALOG_FIELDS)


def _require_exact_slots(
    value: object,
    expected: type,
    names: tuple[str, ...],
    descriptors: tuple[object, ...],
    path: str,
) -> None:
    if type(value) is not expected:
        raise TypeError(f"{path} must be exact {expected.__name__}")
    namespace = expected.__dict__
    if any(
        namespace.get(name) is not descriptor
        for name, descriptor in zip(names, descriptors, strict=True)
    ):
        raise ContractViolation(f"{path} field descriptor substituted")


@dataclass(frozen=True, slots=True, eq=False)
class _RetainedScalarCoordinate:
    scalar_type: type
    value: object


@dataclass(frozen=True, slots=True, eq=False)
class _RetainedTupleCoordinate:
    value: tuple[object, ...]
    items: tuple[object, ...]


@dataclass(frozen=True, slots=True, eq=False)
class _RetainedObjectCoordinate:
    value: object
    fields: tuple[object, ...]


def _scalar_coordinate(
    value: object,
    expected: type,
    path: str,
    retained: object | None = None,
) -> _RetainedScalarCoordinate:
    if type(value) is not expected:
        raise TypeError(f"{path} must be exact {expected.__name__}")
    if retained is None:
        return _RetainedScalarCoordinate(expected, value)
    if (
        type(retained) is not _RetainedScalarCoordinate
        or retained.scalar_type is not expected
    ):
        raise ContractViolation(f"{path} retained scalar coordinate differs")
    admitted = cast(_RetainedScalarCoordinate, retained)
    # Exact built-in scalar types were established above, so this comparison
    # cannot dispatch to caller-owned equality behavior.
    if value != admitted.value:
        raise ContractViolation(f"{path} retained scalar changed")
    return admitted


def _string(
    value: object, path: str, retained: object | None = None
) -> _RetainedScalarCoordinate:
    return _scalar_coordinate(value, str, path, retained)


def _integer(
    value: object, path: str, retained: object | None = None
) -> _RetainedScalarCoordinate:
    return _scalar_coordinate(value, int, path, retained)


def _boolean(
    value: object, path: str, retained: object | None = None
) -> _RetainedScalarCoordinate:
    return _scalar_coordinate(value, bool, path, retained)


def _tuple_coordinate(
    value: object,
    path: str,
    item_coordinate,
    retained: object | None = None,
) -> _RetainedTupleCoordinate:
    if type(value) is not tuple:
        raise TypeError(f"{path} must be exact tuple")
    items = cast(tuple[object, ...], value)
    if retained is None:
        previous: tuple[object | None, ...] = (None,) * len(items)
    else:
        if type(retained) is not _RetainedTupleCoordinate:
            raise ContractViolation(f"{path} retained tuple coordinate differs")
        admitted = cast(_RetainedTupleCoordinate, retained)
        if items is not admitted.value:
            raise ContractViolation(f"{path} retained tuple identity changed")
        if len(items) != len(admitted.items):
            raise ContractViolation(f"{path} retained tuple length changed")
        previous = admitted.items
    children = tuple(
        item_coordinate(item, f"{path}[{index}]", previous[index])
        for index, item in enumerate(items)
    )
    if retained is not None:
        return cast(_RetainedTupleCoordinate, retained)
    return _RetainedTupleCoordinate(items, children)


def _strings(
    value: object, path: str, retained: object | None = None
) -> _RetainedTupleCoordinate:
    return _tuple_coordinate(value, path, _string, retained)


def _begin_object(
    value: object,
    expected: type,
    names: tuple[str, ...],
    descriptors: tuple[object, ...],
    path: str,
    retained: object | None,
    field_count: int,
) -> tuple[object, tuple[object | None, ...]]:
    _require_exact_slots(value, expected, names, descriptors, path)
    if retained is None:
        return value, (None,) * field_count
    if type(retained) is not _RetainedObjectCoordinate:
        raise ContractViolation(f"{path} retained object coordinate differs")
    admitted = cast(_RetainedObjectCoordinate, retained)
    if value is not admitted.value:
        raise ContractViolation(f"{path} retained object identity changed")
    if len(admitted.fields) != field_count:
        raise ContractViolation(f"{path} retained object shape changed")
    return value, admitted.fields


def _finish_object(
    value: object,
    children: tuple[object, ...],
    retained: object | None,
) -> _RetainedObjectCoordinate:
    if retained is not None:
        return cast(_RetainedObjectCoordinate, retained)
    return _RetainedObjectCoordinate(value, children)


def _digest_coordinate(
    value: object, path: str, retained: object | None = None
) -> _RetainedObjectCoordinate:
    raw, previous = _begin_object(
        value, ContentDigest, _DIGEST_FIELDS, _DIGEST_SLOTS, path, retained, 1
    )
    item = cast(ContentDigest, raw)
    children = (_string(item.value, f"{path}.value", previous[0]),)
    return _finish_object(item, children, retained)


def _contract_coordinate(
    value: object, path: str, retained: object | None = None
) -> _RetainedObjectCoordinate:
    raw, previous = _begin_object(
        value, SemanticContractRef, _CONTRACT_FIELDS, _CONTRACT_SLOTS, path, retained, 3
    )
    item = cast(SemanticContractRef, raw)
    children = (
        _string(item.key, f"{path}.key", previous[0]),
        _string(item.version, f"{path}.version", previous[1]),
        _digest_coordinate(item.schema_digest, f"{path}.schema_digest", previous[2]),
    )
    return _finish_object(item, children, retained)


def _implementation_coordinate(
    value: object, path: str, retained: object | None = None
) -> _RetainedObjectCoordinate:
    raw, previous = _begin_object(
        value,
        SemanticImplementationCoordinate,
        _IMPLEMENTATION_FIELDS,
        _IMPLEMENTATION_SLOTS,
        path,
        retained,
        2,
    )
    item = cast(SemanticImplementationCoordinate, raw)
    children = (
        _string(item.implementation_ref, f"{path}.implementation_ref", previous[0]),
        _digest_coordinate(item.closure_digest, f"{path}.closure_digest", previous[1]),
    )
    return _finish_object(item, children, retained)


def _configuration_coordinate(
    value: object, path: str, retained: object | None = None
) -> _RetainedObjectCoordinate:
    raw, previous = _begin_object(
        value,
        SemanticConfigurationCoordinate,
        _CONFIGURATION_FIELDS,
        _CONFIGURATION_SLOTS,
        path,
        retained,
        2,
    )
    item = cast(SemanticConfigurationCoordinate, raw)
    children = (
        _string(item.configuration_ref, f"{path}.configuration_ref", previous[0]),
        _digest_coordinate(item.digest, f"{path}.digest", previous[1]),
    )
    return _finish_object(item, children, retained)


def _consumed_coordinate(
    value: object, path: str, retained: object | None = None
) -> _RetainedObjectCoordinate:
    raw, previous = _begin_object(
        value,
        ConsumedRoleDeclaration,
        _CONSUMED_FIELDS,
        _CONSUMED_SLOTS,
        path,
        retained,
        3,
    )
    item = cast(ConsumedRoleDeclaration, raw)
    children = (
        _string(item.role, f"{path}.role", previous[0]),
        _tuple_coordinate(
            item.accepted_contracts,
            f"{path}.accepted_contracts",
            _contract_coordinate,
            previous[1],
        ),
        _boolean(item.required, f"{path}.required", previous[2]),
    )
    return _finish_object(item, children, retained)


def _produced_coordinate(
    value: object, path: str, retained: object | None = None
) -> _RetainedObjectCoordinate:
    raw, previous = _begin_object(
        value,
        ProducedRoleDeclaration,
        _PRODUCED_FIELDS,
        _PRODUCED_SLOTS,
        path,
        retained,
        2,
    )
    item = cast(ProducedRoleDeclaration, raw)
    children = (
        _string(item.role, f"{path}.role", previous[0]),
        _contract_coordinate(item.contract, f"{path}.contract", previous[1]),
    )
    return _finish_object(item, children, retained)


def _provider_coordinate(
    value: object, path: str, retained: object | None = None
) -> _RetainedObjectCoordinate:
    raw, p = _begin_object(
        value,
        SemanticContractProviderDeclaration,
        _PROVIDER_FIELDS,
        _PROVIDER_SLOTS,
        path,
        retained,
        14,
    )
    item = cast(SemanticContractProviderDeclaration, raw)
    children = (
        _string(item.provider_key, f"{path}.provider_key", p[0]),
        _contract_coordinate(item.provider_contract, f"{path}.provider_contract", p[1]),
        _strings(item.package_kinds, f"{path}.package_kinds", p[2]),
        _strings(item.operation_kinds, f"{path}.operation_kinds", p[3]),
        _tuple_coordinate(
            item.consumed_roles, f"{path}.consumed_roles", _consumed_coordinate, p[4]
        ),
        _produced_coordinate(item.result_role, f"{path}.result_role", p[5]),
        _contract_coordinate(
            item.transition_contract, f"{path}.transition_contract", p[6]
        ),
        _produced_coordinate(item.effect_role, f"{path}.effect_role", p[7]),
        _contract_coordinate(item.effect_contract, f"{path}.effect_contract", p[8]),
        _tuple_coordinate(
            item.output_roles, f"{path}.output_roles", _produced_coordinate, p[9]
        ),
        _boolean(item.allows_typed_empty, f"{path}.allows_typed_empty", p[10]),
        _boolean(item.predecessor_required, f"{path}.predecessor_required", p[11]),
        _strings(item.terminal_statuses, f"{path}.terminal_statuses", p[12]),
        _strings(item.counter_keys, f"{path}.counter_keys", p[13]),
    )
    return _finish_object(item, children, retained)


def _execution_coordinate(
    value: object, path: str, retained: object | None = None
) -> _RetainedObjectCoordinate:
    raw, p = _begin_object(
        value,
        ProviderExecutionBinding,
        _EXECUTION_FIELDS,
        _EXECUTION_SLOTS,
        path,
        retained,
        3,
    )
    item = cast(ProviderExecutionBinding, raw)
    children = (
        _string(item.provider_key, f"{path}.provider_key", p[0]),
        _implementation_coordinate(item.implementation, f"{path}.implementation", p[1]),
        _configuration_coordinate(item.configuration, f"{path}.configuration", p[2]),
    )
    return _finish_object(item, children, retained)


def _input_coordinate(
    value: object, path: str, retained: object | None = None
) -> _RetainedObjectCoordinate:
    raw, p = _begin_object(
        value, ProfileInputDeclaration, _INPUT_FIELDS, _INPUT_SLOTS, path, retained, 2
    )
    item = cast(ProfileInputDeclaration, raw)
    children = (
        _string(item.role, f"{path}.role", p[0]),
        _contract_coordinate(item.contract, f"{path}.contract", p[1]),
    )
    return _finish_object(item, children, retained)


def _role_binding_coordinate(
    value: object, path: str, retained: object | None = None
) -> _RetainedObjectCoordinate:
    raw, p = _begin_object(
        value, RoleBinding, _ROLE_BINDING_FIELDS, _ROLE_BINDING_SLOTS, path, retained, 2
    )
    item = cast(RoleBinding, raw)
    children = (
        _string(item.target_role, f"{path}.target_role", p[0]),
        _string(item.source_role, f"{path}.source_role", p[1]),
    )
    return _finish_object(item, children, retained)


def _step_coordinate(
    value: object, path: str, retained: object | None = None
) -> _RetainedObjectCoordinate:
    raw, p = _begin_object(
        value, ProfileStepDeclaration, _STEP_FIELDS, _STEP_SLOTS, path, retained, 3
    )
    item = cast(ProfileStepDeclaration, raw)
    children = (
        _string(item.step_key, f"{path}.step_key", p[0]),
        _string(item.provider_key, f"{path}.provider_key", p[1]),
        _tuple_coordinate(
            item.bindings, f"{path}.bindings", _role_binding_coordinate, p[2]
        ),
    )
    return _finish_object(item, children, retained)


def _profile_coordinate(
    value: object, path: str, retained: object | None = None
) -> _RetainedObjectCoordinate:
    raw, p = _begin_object(
        value,
        SemanticContractProfileDeclaration,
        _PROFILE_FIELDS,
        _PROFILE_SLOTS,
        path,
        retained,
        10,
    )
    item = cast(SemanticContractProfileDeclaration, raw)
    children = (
        _string(item.profile_ref, f"{path}.profile_ref", p[0]),
        _string(item.version, f"{path}.version", p[1]),
        _strings(item.package_kinds, f"{path}.package_kinds", p[2]),
        _strings(item.operation_kinds, f"{path}.operation_kinds", p[3]),
        _tuple_coordinate(item.inputs, f"{path}.inputs", _input_coordinate, p[4]),
        _tuple_coordinate(
            item.providers, f"{path}.providers", _provider_coordinate, p[5]
        ),
        _tuple_coordinate(item.steps, f"{path}.steps", _step_coordinate, p[6]),
        _string(item.terminal_result_role, f"{path}.terminal_result_role", p[7]),
        _string(item.terminal_effect_role, f"{path}.terminal_effect_role", p[8]),
        _strings(item.terminal_output_roles, f"{path}.terminal_output_roles", p[9]),
    )
    return _finish_object(item, children, retained)


def _requirement_coordinate(
    value: object, path: str, retained: object | None = None
) -> _RetainedObjectCoordinate:
    raw, p = _begin_object(
        value,
        CodeSemanticRequiredResultProduct,
        _REQUIREMENT_FIELDS,
        _REQUIREMENT_SLOTS,
        path,
        retained,
        3,
    )
    item = cast(CodeSemanticRequiredResultProduct, raw)
    children = (
        _string(item.role, f"{path}.role", p[0]),
        _contract_coordinate(item.contract, f"{path}.contract", p[1]),
        _digest_coordinate(item.requirement_digest, f"{path}.requirement_digest", p[2]),
    )
    return _finish_object(item, children, retained)


def _binding_coordinate(
    value: object, path: str, retained: object | None = None
) -> _RetainedObjectCoordinate:
    raw, p = _begin_object(
        value,
        CodeSemanticMaterializationProfileBinding,
        _BINDING_FIELDS,
        _BINDING_SLOTS,
        path,
        retained,
        15,
    )
    item = cast(CodeSemanticMaterializationProfileBinding, raw)
    children = (
        _string(item.semantic_owner_key, f"{path}.semantic_owner_key", p[0]),
        _string(item.semantic_provider_key, f"{path}.semantic_provider_key", p[1]),
        _strings(item.package_families, f"{path}.package_families", p[2]),
        _strings(item.package_roles, f"{path}.package_roles", p[3]),
        _tuple_coordinate(
            item.manifest_contracts,
            f"{path}.manifest_contracts",
            _contract_coordinate,
            p[4],
        ),
        _profile_coordinate(
            item.profile_declaration, f"{path}.profile_declaration", p[5]
        ),
        _tuple_coordinate(
            item.provider_execution_bindings,
            f"{path}.provider_execution_bindings",
            _execution_coordinate,
            p[6],
        ),
        _contract_coordinate(
            item.dependency_planner_contract,
            f"{path}.dependency_planner_contract",
            p[7],
        ),
        _implementation_coordinate(
            item.dependency_planner_implementation,
            f"{path}.dependency_planner_implementation",
            p[8],
        ),
        _configuration_coordinate(
            item.dependency_planner_configuration,
            f"{path}.dependency_planner_configuration",
            p[9],
        ),
        _contract_coordinate(
            item.dependency_demand_contract, f"{path}.dependency_demand_contract", p[10]
        ),
        _contract_coordinate(
            item.dependency_target_intent_contract,
            f"{path}.dependency_target_intent_contract",
            p[11],
        ),
        _tuple_coordinate(
            item.result_product_contracts,
            f"{path}.result_product_contracts",
            _requirement_coordinate,
            p[12],
        ),
        _integer(item.priority, f"{path}.priority", p[13]),
        _digest_coordinate(item.binding_digest, f"{path}.binding_digest", p[14]),
    )
    return _finish_object(item, children, retained)


def _retained_catalog_coordinate(
    value: object, retained: object | None = None
) -> _RetainedObjectCoordinate:
    path = "catalog"
    raw, p = _begin_object(
        value,
        CodeSemanticContractCatalog,
        _CATALOG_FIELDS,
        _CATALOG_SLOTS,
        path,
        retained,
        4,
    )
    item = cast(CodeSemanticContractCatalog, raw)
    children = (
        _string(item.catalog_ref, "catalog.catalog_ref", p[0]),
        _integer(item.catalog_generation, "catalog.catalog_generation", p[1]),
        _tuple_coordinate(item.entries, "catalog.entries", _binding_coordinate, p[2]),
        _digest_coordinate(
            item.catalog_root_digest, "catalog.catalog_root_digest", p[3]
        ),
    )
    return _finish_object(item, children, retained)


def _revoke_code_semantic_contract_catalog(
    admission: AdmittedCodeSemanticContractCatalog,
) -> None:
    if type(admission) is not AdmittedCodeSemanticContractCatalog:
        raise TypeError("catalog admission must be exact")
    with _CATALOG_ADMISSION_LOCK:
        _CATALOG_ADMISSIONS.pop(admission, None)


def _admitted_catalog_state(
    admission: AdmittedCodeSemanticContractCatalog,
) -> _CatalogAdmissionState:
    if type(admission) is not AdmittedCodeSemanticContractCatalog:
        raise TypeError("catalog admission must be exact")
    with _CATALOG_ADMISSION_LOCK:
        state = _CATALOG_ADMISSIONS.get(admission)
    if state is None:
        raise ContractViolation("Code catalog admission is not registered")
    if state.host_liveness() is not True:
        raise ContractViolation("Code catalog host admission is not live")
    return state


class CodeSemanticContractCatalogResolver:
    def __init__(
        self,
        admission: AdmittedCodeSemanticContractCatalog,
    ) -> None:
        self._admission = admission
        admission_state = _admitted_catalog_state(admission)
        catalog = admission_state.catalog
        catalog.__post_init__()
        self._catalog = catalog
        index: dict[str, list[CodeSemanticMaterializationProfileBinding]] = {}
        for entry in catalog.entries:
            for kind in entry.profile_declaration.package_kinds:
                index.setdefault(kind, []).append(entry)
        self._index = {
            key: tuple(sorted(values, key=lambda item: item.binding_digest.value))
            for key, values in index.items()
        }
        self._entry_wires = {
            item.binding_digest: item.to_wire() for item in catalog.entries
        }
        self._entry_wire_bytes = {
            digest: canonical_json_bytes(wire)
            for digest, wire in self._entry_wires.items()
        }
        self._match_contract_wire = canonical_json_bytes(CODE_SEMANTIC_CONTRACT_MATCH)
        self._admission_contract_wire = canonical_json_bytes(
            CODE_SEMANTIC_CONTRACT_MATCH_ADMISSION
        )
        self._catalog_ref_wire = canonical_json_bytes(catalog.catalog_ref)
        self._catalog_root_wire = canonical_json_bytes(
            catalog.catalog_root_digest.to_wire()
        )
        self._profile_digests = {
            item.binding_digest: item.profile_declaration.digest
            for item in catalog.entries
        }
        self._dependency_planners = dict(admission_state.dependency_planners)
        self._executable_closure = admission_state.executable_closure
        # Some nested contract values establish private canonical seals during
        # their first codec validation. Capture only after all resolver indexes
        # and canonical wires have completed that one-time initialization.
        self._retained_catalog_coordinate = _retained_catalog_coordinate(catalog)

    @property
    def catalog(self) -> CodeSemanticContractCatalog:
        _admitted_catalog_state(self._admission)
        self._catalog.__post_init__()
        return _detached_catalog_snapshot(self._catalog)

    def read_profile_binding(
        self,
        *,
        profile: SemanticContractProfileDeclaration,
        semantic_provider_key: str,
    ) -> CodeSemanticMaterializationProfileBinding:
        """Read one exact admitted binding; this performs no capability selection.

        Integrity and liveness bracket the detached entry copy. All catalog
        entries remain validated, including entries not selected by this read.
        """
        _exact(profile, SemanticContractProfileDeclaration, "profile")
        semantic_provider_key = _token(semantic_provider_key, "semantic_provider_key")
        self.validate_catalog()
        matches = tuple(
            entry
            for entry in self._catalog.entries
            if entry.profile_declaration == profile
            and entry.semantic_provider_key == semantic_provider_key
        )
        if len(matches) != 1:
            raise ContractViolation("exact planning catalog entry unavailable")
        original = matches[0]
        expected = self._entry_wire_bytes.get(original.binding_digest)
        if expected is None:
            raise ContractViolation("original catalog entry unavailable")
        snapshot = deepcopy(original)
        if canonical_json_bytes(snapshot.to_wire()) != expected:
            raise ContractViolation("catalog entry changed while snapshotting")
        self.validate_catalog()
        current = tuple(
            entry
            for entry in self._catalog.entries
            if entry.profile_declaration == profile
            and entry.semantic_provider_key == semantic_provider_key
        )
        if (
            len(current) != 1
            or current[0] is not original
            or canonical_json_bytes(original.to_wire()) != expected
        ):
            raise ContractViolation("catalog entry changed while snapshotting")
        _admitted_catalog_state(self._admission)
        return snapshot

    def validate_catalog(self) -> None:
        """Validate live admission and full catalog integrity without exporting data."""
        _admitted_catalog_state(self._admission)
        self._catalog.__post_init__()
        # Validation does not extend admission lifetime.
        _admitted_catalog_state(self._admission)

    def _validate_retained_catalog_coordinate(
        self,
    ) -> tuple[str, int, ContentDigest]:
        """Validate one admitted immutable catalog graph inside its host lifetime.

        Full catalog semantics were established when the admission and this
        resolver were created.  This entrance proves that the same admission,
        catalog object, complete nested object graph and scalar leaves remain
        live and unchanged.  It returns no reusable admission and exports no
        catalog data.
        """

        state = _admitted_catalog_state(self._admission)
        if state.catalog is not self._catalog:
            raise ContractViolation("original Code catalog substituted")
        _retained_catalog_coordinate(self._catalog, self._retained_catalog_coordinate)
        if _admitted_catalog_state(self._admission) is not state:
            raise ContractViolation("Code catalog admission moved")
        return (
            self._catalog.catalog_ref,
            self._catalog.catalog_generation,
            self._catalog.catalog_root_digest,
        )

    def _assert_valid(self) -> None:
        _admitted_catalog_state(self._admission)

    def _catalog_coordinates(self) -> tuple[str, int, ContentDigest]:
        _admitted_catalog_state(self._admission)
        return (
            self._catalog.catalog_ref,
            self._catalog.catalog_generation,
            self._catalog.catalog_root_digest,
        )

    def _create_prevalidated_context(
        self,
        *,
        package: SemanticPackageCoordinate,
        package_family: str,
        package_role: str,
        manifest_contract: SemanticContractRef,
        code_intent: CodeSemanticMaterializationIntent,
        code_intent_wire: dict[str, object],
        required_result_products: tuple[CodeSemanticRequiredResultProduct, ...],
        required_semantic_provider_keys: tuple[str, ...],
    ) -> CodeSemanticPackagePlanningContext:
        _admitted_catalog_state(self._admission)
        package_value = _exact(package, SemanticPackageCoordinate, "context.package")
        manifest = _exact(
            manifest_contract, SemanticContractRef, "context.manifest_contract"
        )
        intent = _exact(
            code_intent, CodeSemanticMaterializationIntent, "context.intent"
        )
        requirements = _exact_tuple(
            required_result_products,
            CodeSemanticRequiredResultProduct,
            "context.required_result_products",
        )
        roles = tuple(item.role for item in requirements)
        if (
            not requirements
            or roles != tuple(sorted(set(roles), key=str.encode))
            or roles != intent.requested_terminal_output_roles
        ):
            raise ContractViolation("context result requirements differ from intent")
        if (
            type(code_intent_wire) is not dict
            or code_intent_wire.get("intent_digest") != intent.intent_digest.to_wire()
        ):
            raise ContractViolation("prevalidated Code intent wire differs")
        payload = {
            "code_intent": code_intent_wire,
            "manifest_contract": manifest.to_wire(),
            "package": package_value.to_wire(),
            "package_family": _token(package_family, "context.package_family"),
            "package_role": _token(package_role, "context.package_role"),
            "required_result_products": [item.to_wire() for item in requirements],
            "required_semantic_provider_keys": list(
                _token_tuple(
                    required_semantic_provider_keys,
                    "context.required_semantic_provider_keys",
                )
            ),
        }
        return _frozen_value(
            CodeSemanticPackagePlanningContext,
            package=package_value,
            package_family=package_family,
            package_role=package_role,
            manifest_contract=manifest,
            code_intent=intent,
            required_result_products=requirements,
            required_semantic_provider_keys=required_semantic_provider_keys,
            context_digest=_digest(CODE_SEMANTIC_PACKAGE_PLANNING_CONTEXT, payload),
        )

    def _compose_prevalidated_target_intent(
        self,
        *,
        target_package: SemanticPackageCoordinate,
        demands: tuple[SemanticDependencyDemand, ...],
    ) -> CodeComposedSemanticMaterializationIntent:
        _admitted_catalog_state(self._admission)
        return _compose_prevalidated_dependency_demands(
            target_package=target_package,
            demands=demands,
        )

    def resolve(
        self, context: CodeSemanticPackagePlanningContext
    ) -> tuple[CodeSemanticContractMatch, CodeSemanticContractMatchAdmission]:
        self._assert_valid()
        _exact(context, CodeSemanticPackagePlanningContext, "context").__post_init__()
        return self._resolve_prevalidated_context(context)

    def _resolve_prevalidated_context(
        self, context: CodeSemanticPackagePlanningContext
    ) -> tuple[CodeSemanticContractMatch, CodeSemanticContractMatchAdmission]:
        if type(context) is not CodeSemanticPackagePlanningContext:
            raise TypeError("planning context must be exact")
        candidates = tuple(
            entry
            for entry in self._index.get(context.package.package_kind, ())
            if _entry_matches(entry, context)
        )
        if not candidates:
            raise ContractViolation("semantic_contract_match_absent")
        priority = max(item.priority for item in candidates)
        winners = tuple(item for item in candidates if item.priority == priority)
        if len(winners) != 1:
            raise ContractViolation("semantic_contract_match_ambiguous")
        selected = winners[0]
        context_digest_wire = canonical_json_bytes(context.context_digest.to_wire())
        selected_entry_digest_wire = canonical_json_bytes(
            selected.binding_digest.to_wire()
        )
        match_digest = _frozen_value(
            ContentDigest,
            value="sha256:"
            + hashlib.sha256(
                b'{"context_digest":'
                + context_digest_wire
                + b',"contract":'
                + self._match_contract_wire
                + b',"selected_binding":'
                + self._entry_wire_bytes[selected.binding_digest]
                + b',"selected_entry_digest":'
                + selected_entry_digest_wire
                + b"}"
            ).hexdigest(),
        )
        match = _frozen_value(
            CodeSemanticContractMatch,
            context_digest=context.context_digest,
            selected_entry_digest=selected.binding_digest,
            selected_binding=selected,
            match_digest=match_digest,
        )
        match_digest_wire = canonical_json_bytes(match_digest.to_wire())
        admission_digest = _frozen_value(
            ContentDigest,
            value="sha256:"
            + hashlib.sha256(
                b'{"catalog_generation":'
                + str(self._catalog.catalog_generation).encode("ascii")
                + b',"catalog_ref":'
                + self._catalog_ref_wire
                + b',"catalog_root_digest":'
                + self._catalog_root_wire
                + b',"contract":'
                + self._admission_contract_wire
                + b',"match_digest":'
                + match_digest_wire
                + b"}"
            ).hexdigest(),
        )
        admission = _frozen_value(
            CodeSemanticContractMatchAdmission,
            match_digest=match.match_digest,
            catalog_ref=self._catalog.catalog_ref,
            catalog_generation=self._catalog.catalog_generation,
            catalog_root_digest=self._catalog.catalog_root_digest,
            admission_digest=admission_digest,
        )
        return match, admission

    async def plan_dependencies(
        self,
        *,
        context: CodeSemanticPackagePlanningContext,
        match: CodeSemanticContractMatch,
        planning_input: SemanticDependencyPlanningInput,
    ) -> SemanticDependencyDemandSet:
        self._assert_valid()
        _exact(context, CodeSemanticPackagePlanningContext, "context").__post_init__()
        codec = DependencyPlanningInputCodec()
        planning_input_body = codec.encode(planning_input)
        result = await self._plan_dependencies_for_prevalidated_context(
            context=context,
            match=match,
            planning_input=planning_input,
            planning_input_body=planning_input_body,
        )
        if codec.encode(planning_input) != planning_input_body:
            raise ContractViolation("original dependency planning input changed")
        return result

    async def _plan_dependencies_for_prevalidated_context(
        self,
        *,
        context: CodeSemanticPackagePlanningContext,
        match: CodeSemanticContractMatch,
        planning_input: SemanticDependencyPlanningInput,
        planning_input_body: bytes,
    ) -> SemanticDependencyDemandSet:
        if type(context) is not CodeSemanticPackagePlanningContext:
            raise TypeError("planning context must be exact")
        if type(match) is not CodeSemanticContractMatch:
            raise TypeError("dependency planner match must be exact")
        _admitted_catalog_state(self._admission)
        if (
            match.context_digest != context.context_digest
            or match.selected_entry_digest not in self._entry_wires
        ):
            raise ContractViolation("dependency planner match differs from catalog")
        binding = match.selected_binding
        planner = self._dependency_planners.get(binding.binding_digest)
        if planner is None:
            raise ContractViolation("dependency planner implementation unavailable")
        codec = DependencyPlanningInputCodec()
        if type(planning_input) is not SemanticDependencyPlanningInput:
            raise TypeError("exact dependency planning input required")
        if planning_input.package != context.package:
            raise ContractViolation("dependency planning input package differs")
        if type(planning_input_body) is not bytes:
            raise TypeError("canonical dependency planning input body required")
        input_bytes = planning_input_body
        input_digest = ContentDigest.of_bytes(input_bytes)
        supplied = codec.decode(input_bytes)
        if supplied != planning_input:
            raise ContractViolation("canonical dependency planning input body differs")
        admission_state = _admitted_catalog_state(self._admission)
        entrance = _original_planner_entrance(admission_state, binding.binding_digest)
        if (
            admission_state.dependency_planners.get(binding.binding_digest)
            is not planner
        ):
            raise ContractViolation("resolver planner differs from admitted original")
        self._assert_valid()
        result = await entrance(
            planning_input=supplied,
            package=context.package,
            intent=context.code_intent,
            selected_match=match,
        )
        self._assert_valid()
        if (
            self._dependency_planners.get(binding.binding_digest) is not planner
            or _original_planner_entrance(admission_state, binding.binding_digest)
            is not entrance
            or ContentDigest.of_bytes(codec.encode(supplied)) != input_digest
        ):
            raise ContractViolation(
                "dependency planner or original planning input changed"
            )
        if type(result) is not SemanticDependencyDemandSet:
            raise TypeError("dependency planner result must be exact demand set")
        result.__post_init__()
        if (
            result.package != context.package
            or result.intent_digest != context.code_intent.intent_digest
            or result.profile_ref != binding.profile_declaration.profile_ref
            or result.profile_digest != self._profile_digests[binding.binding_digest]
            or result.contract_profile_binding_digest != binding.binding_digest
            or result.planner_implementation_ref
            != binding.dependency_planner_implementation.implementation_ref
            or result.planner_implementation_digest
            != binding.dependency_planner_implementation.closure_digest
            or result.planner_configuration_ref
            != binding.dependency_planner_configuration.configuration_ref
            or result.planner_configuration_digest
            != binding.dependency_planner_configuration.digest
        ):
            raise ContractViolation(
                "dependency planner result differs from exact binding"
            )
        return result


def _entry_matches(
    entry: CodeSemanticMaterializationProfileBinding,
    context: CodeSemanticPackagePlanningContext,
) -> bool:
    profile = entry.profile_declaration
    if (
        context.package_family not in entry.package_families
        or context.package_role not in entry.package_roles
        or context.manifest_contract not in entry.manifest_contracts
        or context.code_intent.operation_kind not in profile.operation_kinds
    ):
        return False
    provided = {item.role: item.contract for item in entry.result_product_contracts}
    if any(
        provided.get(item.role) != item.contract
        for item in context.required_result_products
    ):
        return False
    provider_keys = {entry.semantic_provider_key} | {
        item.provider_key for item in entry.provider_execution_bindings
    }
    if not set(context.required_semantic_provider_keys) <= provider_keys:
        return False
    configuration = context.code_intent.semantic_configuration_coordinate
    admitted_configurations = {
        entry.dependency_planner_configuration,
        *(item.configuration for item in entry.provider_execution_bindings),
    }
    return configuration is None or configuration in admitted_configurations


__all__ = [
    "CODE_SEMANTIC_CONTRACT_CATALOG",
    "CODE_SEMANTIC_CONTRACT_MATCH",
    "CODE_SEMANTIC_CONTRACT_MATCH_ADMISSION",
    "CODE_SEMANTIC_MATERIALIZATION_PROFILE_BINDING",
    "CODE_SEMANTIC_PACKAGE_PLANNING_CONTEXT",
    "AdmittedCodeSemanticContractCatalog",
    "CodeSemanticContractCatalog",
    "CodeSemanticContractCatalogResolver",
    "CodeSemanticContractMatch",
    "CodeSemanticContractMatchAdmission",
    "CodeSemanticDependencyPlanner",
    "CodeSemanticMaterializationProfileBinding",
    "CodeSemanticPackagePlanningContext",
]
