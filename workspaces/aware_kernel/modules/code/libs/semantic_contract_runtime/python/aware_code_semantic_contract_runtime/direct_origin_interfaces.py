"""Direct command consumer signatures, not bootstrap or lifetime authority.

Original issuer, factory and method entrances must be authenticated by Code's
bootstrap before invocation. Protocol matching and construction grant nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol, TypeVar

from .contracts import (
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticImplementationCoordinate,
)
from .materialization_catalog import AdmittedCodeSemanticContractCatalog
from .runtime import SemanticContractRuntime

if TYPE_CHECKING:
    from .selected_provider import AdmittedSemanticProviderRegistration


# Keep the source-only tuple stable for existing original compositions.
RESOURCE_ROLES = (
    "catalog",
    "code_runtime",
    "composition_factory",
    "lifetime_runtime",
    "membership_runtime",
    "observation_runtime",
    "policy_producer",
    "repository_store",
    "scope_adapter",
    "scope_runtime",
    "semantic_issuer",
)


TWO_STAGE_RESOURCE_ROLES = ("authority_code_runtime", *RESOURCE_ROLES)
# The declaration issuer retains the observer, declaration membership and one
# selected package source. None of the v1/v2 whole-root membership or semantic
# issuer resources exist on this rail. Keep the older tuple exactly as-is.
DECLARATION_V3_RESOURCE_ROLES = (
    "catalog",
    "code_runtime",
    "composition_factory",
    "declaration_scope_runtime",
    "lifetime_runtime",
    "policy_producer",
)
DECLARATION_V3_TWO_STAGE_RESOURCE_ROLES = (
    "authority_code_runtime", *DECLARATION_V3_RESOURCE_ROLES
)


@dataclass(frozen=True, slots=True, eq=False)
class RetainedSemanticStageRuntimeExpectation:
    """Expected original references only; no registration or lifetime admission.

    Fixed bootstrap must authenticate the instances and Code must validate the
    original live registration/profile. Non-None markers can describe expected
    identity but cannot pass that later nominal boundary by construction alone.
    """

    stage: Literal["source_planning", "authority_derivation"]
    runtime: SemanticContractRuntime
    registration: AdmittedSemanticProviderRegistration

    def __post_init__(self) -> None:
        if type(self.stage) is not str or self.stage not in (
            "source_planning",
            "authority_derivation",
        ):
            raise ContractViolation("exact retained semantic stage required")
        if self.runtime is None or self.registration is None:
            raise ContractViolation(
                "stage runtime and registration references required"
            )


@dataclass(frozen=True, slots=True, eq=False)
class RetainedSemanticProductRuntimeExpectation:
    """Expected original graph-product registration, never execution authority."""

    runtime: SemanticContractRuntime
    registration: AdmittedSemanticProviderRegistration

    def __post_init__(self) -> None:
        if self.runtime is None or self.registration is None:
            raise ContractViolation(
                "product runtime and registration references required"
            )


@dataclass(frozen=True, slots=True, eq=False)
class DirectCommandResourceBinding:
    """Original reference plus explicit cleanup disposition; not ownership proof."""

    role: str
    resource: object
    disposition: Literal["owned", "borrowed"]

    def __post_init__(self) -> None:
        if type(self.role) is not str or self.role not in (
            *TWO_STAGE_RESOURCE_ROLES,
            *DECLARATION_V3_TWO_STAGE_RESOURCE_ROLES,
        ):
            raise ContractViolation("unknown resource role")
        if self.resource is None:
            raise ContractViolation("original resource required")
        if type(self.disposition) is not str or self.disposition not in (
            "owned",
            "borrowed",
        ):
            raise ContractViolation("explicit resource disposition required")


@dataclass(frozen=True, slots=True, eq=False)
class DirectCommandExpectedContext:
    """Expectation only; original issuer compares identities using 'is'.

    Bind the complete context once after assembly, before origin registration.
    Implementation/configuration coordinates compare by value. No placeholders,
    serialization, implicit provenance or mutable late resource binding.
    """

    invocation_identity: object
    epoch_identity: object
    process_id: int
    runtime: SemanticContractRuntime
    catalog: AdmittedCodeSemanticContractCatalog
    composition_implementation: SemanticImplementationCoordinate
    composition_configuration: SemanticConfigurationCoordinate
    policy_implementation: SemanticImplementationCoordinate
    policy_configuration: SemanticConfigurationCoordinate
    resources: tuple[DirectCommandResourceBinding, ...]
    stage_runtime_bindings: tuple[RetainedSemanticStageRuntimeExpectation, ...] = ()
    source_rail: Literal["existing", "declaration_v3"] = "existing"
    product_runtime_bindings: tuple[RetainedSemanticProductRuntimeExpectation, ...] = ()

    def __post_init__(self) -> None:
        if self.invocation_identity is None or self.epoch_identity is None:
            raise ContractViolation("original invocation and epoch required")
        if type(self.process_id) is not int or self.process_id <= 0:
            raise ContractViolation("exact positive process id required")
        stages = self.stage_runtime_bindings
        if (
            type(stages) is not tuple
            or len(stages) > 8192
            or (len(stages) != 0 and (len(stages) < 2 or len(stages) % 2))
        ):
            raise ContractViolation("source-only or complete stage pairs required")
        for stage in stages:
            if type(stage) is not RetainedSemanticStageRuntimeExpectation:
                raise ContractViolation("exact stage runtime expectation required")
            stage.__post_init__()
        if stages:
            for offset in range(0, len(stages), 2):
                planning, authority = stages[offset : offset + 2]
                if (planning.stage, authority.stage) != (
                    "source_planning",
                    "authority_derivation",
                ):
                    raise ContractViolation(
                        "complete stage pairs in execution order required"
                    )
                if (
                    authority.runtime is planning.runtime
                    or authority.registration is planning.registration
                ):
                    raise ContractViolation(
                        "stage runtime or registration identity differs"
                    )
            if stages[0].runtime is not self.runtime:
                raise ContractViolation("first planning runtime resource differs")
        products = self.product_runtime_bindings
        if type(products) is not tuple or len(products) > 4096:
            raise ContractViolation("bounded product runtime bindings required")
        for product in products:
            if type(product) is not RetainedSemanticProductRuntimeExpectation:
                raise ContractViolation("exact product runtime expectation required")
            product.__post_init__()
            if any(
                product.runtime is stage.runtime
                or product.registration is stage.registration
                for stage in stages
            ):
                raise ContractViolation("product and package stages must be distinct")
        for index, product in enumerate(products):
            if any(
                product.runtime is earlier.runtime
                or product.registration is earlier.registration
                for earlier in products[:index]
            ):
                raise ContractViolation("duplicate product runtime or registration")
        if type(self.source_rail) is not str or self.source_rail not in (
            "existing", "declaration_v3"
        ):
            raise ContractViolation("exact direct source rail required")
        if self.source_rail == "declaration_v3":
            roles = (
                DECLARATION_V3_TWO_STAGE_RESOURCE_ROLES
                if stages else DECLARATION_V3_RESOURCE_ROLES
            )
        else:
            roles = TWO_STAGE_RESOURCE_ROLES if stages else RESOURCE_ROLES
        if type(self.resources) is not tuple or len(self.resources) != len(roles):
            raise ContractViolation("complete resource tuple required")
        for binding in self.resources:
            if type(binding) is not DirectCommandResourceBinding:
                raise ContractViolation("exact resource binding required")
            binding.__post_init__()
        if tuple(binding.role for binding in self.resources) != roles:
            raise ContractViolation("resources must be complete, unique and ordered")
        by_role = {binding.role: binding.resource for binding in self.resources}
        if (
            by_role["code_runtime"] is not self.runtime
            or by_role["catalog"] is not self.catalog
        ):
            raise ContractViolation("runtime or catalog resource differs")
        if stages and by_role["authority_code_runtime"] is not stages[1].runtime:
            raise ContractViolation("authority runtime resource differs")
        for value, kind in (
            (self.composition_implementation, SemanticImplementationCoordinate),
            (self.policy_implementation, SemanticImplementationCoordinate),
            (self.composition_configuration, SemanticConfigurationCoordinate),
            (self.policy_configuration, SemanticConfigurationCoordinate),
        ):
            if type(value) is not kind:
                raise ContractViolation("exact implementation/configuration required")
            value.__post_init__()


@dataclass(frozen=True, slots=True, eq=False)
class DirectWorkspaceOriginProduct:
    """Original factory product, never a self-authenticating registration.

    Resources/entrances are resolved from expected.resources by authenticated
    bootstrap. No callback field can nominate an alternative trusted verifier.
    """

    lifetime: object
    expected: DirectCommandExpectedContext


_Lifetime_contra = TypeVar("_Lifetime_contra", contravariant=True)
_Guard = TypeVar("_Guard")


class DirectCommandLifetimeValidator(Protocol[_Lifetime_contra]):
    def validate_command_lifetime(
        self, lifetime: _Lifetime_contra, *, expected: DirectCommandExpectedContext
    ) -> None:
        """Check original context, process, epoch and live state."""
        ...


class DirectCommandPublicationRuntime(Protocol[_Lifetime_contra, _Guard]):
    def acquire_command_publication_guard(
        self, lifetime: _Lifetime_contra, *, expected: DirectCommandExpectedContext
    ) -> _Guard:
        """Acquire owner lock then check live context; unwind internally on failure.

        Return owner-nominal single-use guard bound to process/thread/lifetime.
        """
        ...

    def validate_command_publication_guard(
        self,
        guard: _Guard,
        *,
        lifetime: _Lifetime_contra,
        expected: DirectCommandExpectedContext,
    ) -> None:
        """Require original active guard and acquiring thread while lock is held."""
        ...

    def release_command_publication_guard(self, guard: _Guard) -> None:
        """Release in finally on original thread and retire; duplicate release rejects."""
        ...


class DirectWorkspaceOriginFactory(Protocol[_Lifetime_contra]):
    def create_direct_semantic_origin(
        self, lifetime: _Lifetime_contra
    ) -> DirectWorkspaceOriginProduct:
        """Return already assembled original context; accepts no authority overrides."""
        ...
