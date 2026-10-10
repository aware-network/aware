"""Fixed profile-pair product validation; configuration never grants admission."""

from dataclasses import dataclass, field

from .contracts import (
    ContentDigest,
    ContractViolation,
    SemanticContractInvocation,
    SemanticImplementationCoordinate,
    canonical_json_bytes,
)
from .dependency_input_codec import (
    DEPENDENCY_INPUT_CODEC_IMPLEMENTATION,
    SemanticDependencyProductInputCodec,
    _validate_dependency_product_invocation,
)
from .dependency_inputs import SemanticDependencyProductInput
from .profile import SemanticContractProfileDeclaration


def _implementation(
    profiles: tuple[str, str, str, str],
) -> SemanticImplementationCoordinate:
    return SemanticImplementationCoordinate(
        "aware.code.profile-bound-dependency-product-input.codec.v1",
        ContentDigest.of_bytes(
            canonical_json_bytes(
                {
                    "base_implementation": DEPENDENCY_INPUT_CODEC_IMPLEMENTATION.to_wire(),
                    "source_profile_ref": profiles[0],
                    "source_profile_digest": profiles[1],
                    "consumer_profile_ref": profiles[2],
                    "consumer_profile_digest": profiles[3],
                }
            )
        ),
    )


@dataclass(frozen=True, slots=True, init=False)
class ProfileBoundDependencyProductInputCodec(SemanticDependencyProductInputCodec):
    """Preserve the producer demand profile while checking the consumer invocation.

    The original factory binds this portable configuration to its actual profiles.
    A successful decode/validation is not original dependency-product admission.
    """

    _profiles: tuple[str, str, str, str]
    implementation: SemanticImplementationCoordinate = field(init=False)

    def __init__(
        self,
        *,
        source_profile: SemanticContractProfileDeclaration,
        consumer_profile: SemanticContractProfileDeclaration,
    ) -> None:
        if (
            type(source_profile) is not SemanticContractProfileDeclaration
            or type(consumer_profile) is not SemanticContractProfileDeclaration
        ):
            raise TypeError("exact source and consumer profiles required")
        source_profile.__post_init__()
        consumer_profile.__post_init__()
        if source_profile.profile_ref == consumer_profile.profile_ref:
            raise ContractViolation("distinct stage profile refs required")
        profiles = (
            source_profile.profile_ref,
            source_profile.digest.to_wire(),
            consumer_profile.profile_ref,
            consumer_profile.digest.to_wire(),
        )
        object.__setattr__(self, "_profiles", profiles)
        object.__setattr__(self, "implementation", _implementation(profiles))

    def _check(self) -> None:
        if self.implementation != _implementation(self._profiles):
            raise ContractViolation("dependency codec profile configuration changed")

    def encode(self, value: object) -> bytes:
        self._check()
        return SemanticDependencyProductInputCodec.encode(self, value)

    def decode(self, canonical_body: bytes) -> SemanticDependencyProductInput:
        self._check()
        return SemanticDependencyProductInputCodec.decode(self, canonical_body)

    def validate_invocation(
        self,
        value: object,
        invocation: SemanticContractInvocation,
    ) -> None:
        self._check()
        if type(invocation) is not SemanticContractInvocation:
            raise TypeError("exact Code invocation required")
        if (
            invocation.profile_ref,
            invocation.profile_digest.to_wire(),
        ) != self._profiles[2:]:
            raise ContractViolation("dependency consumer profile differs")
        _validate_dependency_product_invocation(
            value,
            invocation,
            source_profile_ref=self._profiles[0],
            source_profile_digest=ContentDigest.of_wire(self._profiles[1]),
        )
