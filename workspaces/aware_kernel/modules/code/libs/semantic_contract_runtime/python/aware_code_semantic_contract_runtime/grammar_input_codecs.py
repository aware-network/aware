"""Grammar input owner adapters and portable correspondence, never admission."""

from __future__ import annotations

from .contracts import (
    ContractViolation,
    SemanticContractRef,
    SemanticImplementationCoordinate,
)
from .grammar_product_contracts import (
    GRAMMAR_SOURCE_ROLE_SELECTION_REF,
    CodeGrammarSourceRoleSelectionV1,
    decode_grammar_source_role_selection,
    encode_grammar_source_role_selection,
)
from .grammar_profile_codec import _implementation
from .grammar_profile_contract import CodeGrammarDeclarationSourceV1, _exact
from .grammar_profile_join import read_grammar_declaration_context
from .grammar_source_group import CodeGrammarSourceGroupCodec
from .retained_declaration_scope_codec import CodeRetainedDeclarationScopeCodec
from .semantic_input_producer import SemanticInputProductionInput
from .source_origin import decode_source_origin

GRAMMAR_SOURCE_ROLE_SELECTION_CODEC_IMPLEMENTATION = _implementation(
    GRAMMAR_SOURCE_ROLE_SELECTION_REF,
    "aware.code.grammar-source-role-selection.codec.v1",
    "closed descriptor expanded with original declaration-source fields/bounds; compare complete selection against original ordinary input and scope/group before and after",
)


class CodeGrammarSourceRoleSelectionCodec:
    """Original portable selection wire; original producers check its source."""

    contract: SemanticContractRef = GRAMMAR_SOURCE_ROLE_SELECTION_REF
    implementation: SemanticImplementationCoordinate = (
        GRAMMAR_SOURCE_ROLE_SELECTION_CODEC_IMPLEMENTATION
    )

    def encode(self, value: object) -> bytes:
        return encode_grammar_source_role_selection(
            _exact(value, CodeGrammarSourceRoleSelectionV1)
        )

    def decode(self, canonical_body: bytes) -> CodeGrammarSourceRoleSelectionV1:
        return decode_grammar_source_role_selection(canonical_body)


def grammar_input_body_codecs() -> dict[
    SemanticContractRef,
    CodeRetainedDeclarationScopeCodec
    | CodeGrammarSourceRoleSelectionCodec
    | CodeGrammarSourceGroupCodec,
]:
    """Fresh three-input table, not a complete or source-admitted product.

    Syntax's retained profile input and every result/output require their own
    original bindings. Factories must still bind source/result validation and
    perform original admission; this table registers nothing globally.
    """
    codecs = (
        CodeRetainedDeclarationScopeCodec(),
        CodeGrammarSourceRoleSelectionCodec(),
        CodeGrammarSourceGroupCodec(),
    )
    return {codec.contract: codec for codec in codecs}


def validate_grammar_source_role_selection(
    selection: CodeGrammarSourceRoleSelectionV1,
    *,
    input: SemanticInputProductionInput,
) -> None:
    """Freshly join selection to complete supplied owner input, not its authority.

    Call inside original registered production before and after interpretation.
    The existing receiving helper checks both contexts, the complete root source
    inventory, original input digest and shared aggregate budget. No reader,
    callback, cache or issuer is introduced; self-consistent detached values
    remain data, and cannot establish currentness or renew a retired use.
    """
    selected = _exact(selection, CodeGrammarSourceRoleSelectionV1)
    selected.__post_init__()
    owner_input = _exact(input, SemanticInputProductionInput)
    group, closure = read_grammar_declaration_context(owner_input)
    if (
        selected.operation_ref != owner_input.operation_ref
        or selected.stage != owner_input.stage
        or selected.input_digest != owner_input.input_digest
        or selected.root_occurrence_ref != group.root_occurrence_ref
    ):
        raise ContractViolation("grammar selection differs from original input")
    root = next(
        member
        for member in group.members
        if member.occurrence_ref == group.root_occurrence_ref
    )
    origin = decode_source_origin(bytes.fromhex(root.origin_body_hex))
    if closure.consumer_scope_key != origin.occurrence.scope_key:
        raise ContractViolation("grammar selection consumer scope differs")
    source = selected.profile_source
    publications = tuple(
        profile
        for profile in closure.local_profiles
        if profile.owning_scope_key == source.scope_key
        and profile.profile_key == selected.profile_key
    )
    if len(publications) != 1:
        raise ContractViolation("grammar selected profile publication unavailable")
    manifest = publications[0].manifest
    expected = CodeGrammarDeclarationSourceV1(
        closure.repository_binding_ref,
        publications[0].owning_scope_key,
        "profile",
        manifest.relative_path,
        manifest.body_ref,
        manifest.content_digest,
        len(manifest.body),
    )
    if source != expected:
        raise ContractViolation("grammar selection complete profile source differs")
    if source.scope_key != closure.consumer_scope_key:
        # The original V3 validator already binds each association to its exact
        # edge/declaration and selected local profile. Closure membership alone
        # cannot permit an unrelated scope's otherwise matching publication.
        if not any(
            association.declaring_scope_key == closure.consumer_scope_key
            and association.target_scope_key == source.scope_key
            and association.manifest == manifest
            for association in closure.profile_associations
        ):
            raise ContractViolation(
                "grammar selected imported profile lacks association"
            )


__all__ = [
    "CodeGrammarSourceRoleSelectionCodec",
    "GRAMMAR_SOURCE_ROLE_SELECTION_CODEC_IMPLEMENTATION",
    "grammar_input_body_codecs",
    "validate_grammar_source_role_selection",
]
