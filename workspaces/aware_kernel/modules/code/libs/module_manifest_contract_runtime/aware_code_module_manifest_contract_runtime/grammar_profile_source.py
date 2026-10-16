"""Authored grammar requirements through original parsers, never admission.

The receiving composition supplies original bytes and exact selected keys.
These data functions do not select occurrences, import providers, read files,
reconstruct Language contributions or grant source/currentness authority.
"""

from __future__ import annotations

from .codec import encode_module_manifest_meaning
from .models import (
    AwareModulePackageSemanticContractSyntaxSpec,
    AwareModulePackageSpec,
    AwareModuleSpec,
)
from .parser import AwareModuleTomlError, parse_module_manifest
from .profile_codec import encode_profile_manifest
from .profile_models import (
    CodeSemanticContractProfileManifestSpec,
    CodeSemanticContractProfileManifestSpecV2,
    CodeSemanticContractProfileProviderSpecV2,
)
from .profile_parser import parse_profile_manifest
from .v2_parser import thaw
from .v3_models import AwareModuleSpecV3

MAX_GRAMMAR_SOURCE_BYTES = 8 * 1024 * 1024
MAX_GRAMMAR_PROFILE_PROVIDERS = 256


class GrammarProfileSourceError(AwareModuleTomlError):
    """A refused authored selection, not a source-admission or effect receipt."""

    reason: str

    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


def _body(value: object) -> bytes:
    if type(value) is not bytes:
        raise GrammarProfileSourceError(
            "grammar source requires exact bytes", reason="authored_source_invalid"
        )
    if not 1 <= len(value) <= MAX_GRAMMAR_SOURCE_BYTES:
        raise GrammarProfileSourceError(
            "grammar source byte bound exceeded", reason="authored_source_bound"
        )
    return value


def _selector(value: object) -> str:
    if type(value) is not str:
        raise GrammarProfileSourceError(
            "grammar selector requires exact text", reason="authored_selector_invalid"
        )
    try:
        length = len(value.encode("utf-8"))
    except UnicodeError as exc:
        raise GrammarProfileSourceError(
            "grammar selector requires UTF-8", reason="authored_selector_invalid"
        ) from exc
    if not 1 <= length <= 512 or any(part.isspace() for part in value):
        raise GrammarProfileSourceError(
            "grammar selector requires a bounded nonempty token",
            reason="authored_selector_invalid",
        )
    return value


def parse_registered_grammar_profile(
    body: bytes, *, profile_key: str
) -> CodeSemanticContractProfileManifestSpec:
    """Interpret supplied original profile bytes without replacing its parser.

    Only the new grammar path requires active, required registered providers.
    Legacy profile parsing and dynamic admission behavior remain unchanged.
    The complete original parsed value, including authored provider order and
    package key, is returned. A matching selector cannot establish source origin.
    """
    raw = _body(body)
    key = _selector(profile_key)
    value = parse_profile_manifest(raw)
    if len(value.providers) > MAX_GRAMMAR_PROFILE_PROVIDERS:
        raise GrammarProfileSourceError(
            "grammar profile provider bound exceeded", reason="authored_source_bound"
        )
    # Original codec validates the entire value; do not crop optional providers
    # or manufacture a smaller profile and call it the authored declaration.
    _ = encode_profile_manifest(value)
    version = value.aware_semantic_contract_profile
    if type(version) is not int or version not in (1, 2):
        raise GrammarProfileSourceError(
            "grammar profile requires integer format 1",
            reason="unsupported_profile_mode",
        )
    if version == 2 and (
        type(value) is not CodeSemanticContractProfileManifestSpecV2
        or len(value.providers) != 1
        or type(value.providers[0]) is not CodeSemanticContractProfileProviderSpecV2
        or value.providers[0].exposure != "graph_product"
    ):
        raise GrammarProfileSourceError(
            "grammar V2 requires one exact graph product",
            reason="unsupported_profile_mode",
        )
    if value.profile.key != key:
        raise GrammarProfileSourceError(
            "grammar profile differs from the explicit selector",
            reason="profile_selection_mismatch",
        )
    if (
        value.profile.runtime_import_mode != "registered_contracts"
        or value.profile.runtime_import_required is not True
        or value.profile.status != "active"
        or any(
            provider.required is not True or provider.status != "active"
            for provider in value.providers
        )
    ):
        raise GrammarProfileSourceError(
            "grammar profile requires active required registered contracts",
            reason="unsupported_profile_mode",
        )
    return value


def _read_grammar_v2_product_nomination(
    module: AwareModuleSpecV3,
    *,
    declared: CodeSemanticContractProfileProviderSpecV2,
) -> tuple[str, str, str]:
    """Read an original registration nomination; detached data is not admission."""

    def mismatch() -> GrammarProfileSourceError:
        return GrammarProfileSourceError(
            "grammar V2 package/registration/product declaration differs",
            reason="syntax_provider_declaration_mismatch",
        )

    if (
        type(module) is not AwareModuleSpecV3
        or type(declared) is not CodeSemanticContractProfileProviderSpecV2
        or declared.exposure != "graph_product"
    ):
        raise mismatch()
    # Reuse the complete original codec before inspecting nested owner values.
    _ = encode_module_manifest_meaning(module)
    packages = tuple(row for row in module.packages if row.id == declared.package_id)
    declarations = tuple(
        row
        for row in module.package_declarations
        if row.package_id == declared.package_id
    )
    if len(packages) != 1 or len(declarations) != 1:
        raise mismatch()
    parent = packages[0].semantic_contract
    if (
        type(parent) is not AwareModulePackageSemanticContractSyntaxSpec
        or parent.contract != "aware.semantic_provider"
        or parent.provider_key != declared.provider_key
    ):
        raise mismatch()
    registrations = tuple(thaw(row) for row in declarations[0].registrations)
    matches = tuple(
        row for row in registrations if row["key"] == declared.registration_key
    )
    if len(matches) != 1:
        raise mismatch()
    registration = matches[0]
    profiles = registration["profiles"]
    if (
        registration["semantic_contract"]["provider_key"] != declared.provider_key
        or len(profiles) != 1
        or profiles[0]["stage"] != "graph_product"
    ):
        raise mismatch()
    nomination = profiles[0]
    return (
        nomination["profile_ref"],
        nomination["profile_version"],
        nomination["profile_digest"],
    )


def parse_grammar_provider_module(
    body: bytes, *, package_id: str, provider_key: str
) -> tuple[AwareModuleSpec, AwareModulePackageSpec]:
    """Return the complete module and explicitly selected syntax-provider package.

    Original composition determines the qualified module/package occurrence
    before this function. Provider key alone never chooses another package.
    Full provider/consumer runtime contract refs and contribution/scanner bodies
    must be joined separately; the module's broad contract label cannot supply
    a full registered provider identity.
    """
    raw = _body(body)
    selected_package = _selector(package_id)
    selected_provider = _selector(provider_key)
    module = parse_module_manifest(raw)
    _ = encode_module_manifest_meaning(module)
    if type(module.aware) is not int:
        raise GrammarProfileSourceError(
            "grammar provider module requires integer format",
            reason="authored_source_invalid",
        )
    matches = tuple(item for item in module.packages if item.id == selected_package)
    if len(matches) != 1:
        raise GrammarProfileSourceError(
            "explicit grammar provider package is unavailable",
            reason="syntax_provider_declaration_missing",
        )
    package = matches[0]
    declaration = package.semantic_contract
    if type(declaration) is not AwareModulePackageSemanticContractSyntaxSpec:
        raise GrammarProfileSourceError(
            "selected package lacks an authored syntax provider",
            reason="syntax_provider_declaration_missing",
        )
    if (
        declaration.contract != "aware.semantic_provider"
        or declaration.provider_key != selected_provider
    ):
        raise GrammarProfileSourceError(
            "selected package differs from the grammar provider",
            reason="syntax_provider_declaration_mismatch",
        )
    return module, package
