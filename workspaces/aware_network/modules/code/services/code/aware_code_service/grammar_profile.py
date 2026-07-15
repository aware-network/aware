from __future__ import annotations

from collections.abc import Sequence

from aware_code_sdk.dto import (
    CodeGrammarAnchorCoverageDiagnostic,
    CodeGrammarBackendDescriptor,
    CodeGrammarProfile,
    CodeGrammarProfileDiagnostic,
    CodeGrammarProfileResolutionStatus,
    CodeGrammarRuleBinding,
    CodeGrammarRuleDeclaration,
    CodeSemanticContract,
    ResolveCodeGrammarProfileRequest,
    ResolveCodeGrammarProfileResponse,
)
from aware_grammar.semantic_profile import (
    AwareGrammarDeclarationCoverageProfile,
    AwareGrammarSemanticProfile,
    AwareGrammarSemanticProfileError,
    build_aware_grammar_declaration_coverage_profile,
    build_aware_grammar_semantic_profile,
)
from aware_types import JsonObject

CODE_GRAMMAR_PROFILE_LANGUAGE = "aware"
CODE_GRAMMAR_PROFILE_BACKEND_KEY = "aware_kernel"
CODE_GRAMMAR_PROFILE_CONTRACT_VERSION = "code.grammar_profile.aware.v0"
DEFAULT_CODE_GRAMMAR_PROFILE_KEY = "code.grammar_profile.aware_kernel"


def resolve_code_grammar_profile(
    *,
    request: ResolveCodeGrammarProfileRequest,
    available_semantic_contracts: Sequence[CodeSemanticContract] = (),
) -> ResolveCodeGrammarProfileResponse:
    """Resolve a Code grammar profile from Code-owned semantic contract DTOs."""

    language = _optional_text(request.language) or CODE_GRAMMAR_PROFILE_LANGUAGE
    if language != CODE_GRAMMAR_PROFILE_LANGUAGE:
        return _grammar_profile_blocked_response(
            request=request,
            diagnostics=[
                CodeGrammarProfileDiagnostic(
                    reason="unsupported_language",
                    message=(
                        "Code grammar profile resolution currently supports "
                        f"only {CODE_GRAMMAR_PROFILE_LANGUAGE!r}."
                    ),
                    metadata=JsonObject({"language": language}),
                )
            ],
        )

    backend_key = (
        _optional_text(request.backend_key) or CODE_GRAMMAR_PROFILE_BACKEND_KEY
    )
    if backend_key != CODE_GRAMMAR_PROFILE_BACKEND_KEY:
        return _grammar_profile_blocked_response(
            request=request,
            diagnostics=[
                CodeGrammarProfileDiagnostic(
                    reason="unsupported_backend",
                    message=(
                        "Code grammar profile resolution currently supports "
                        f"only {CODE_GRAMMAR_PROFILE_BACKEND_KEY!r}."
                    ),
                    metadata=JsonObject({"backend_key": backend_key}),
                )
            ],
        )

    contracts, missing_provider_keys = _grammar_profile_contracts(
        request=request,
        available_semantic_contracts=available_semantic_contracts,
    )
    if missing_provider_keys:
        return _grammar_profile_blocked_response(
            request=request,
            diagnostics=[
                CodeGrammarProfileDiagnostic(
                    reason="semantic_contract_unavailable",
                    message=(
                        "Code grammar profile resolution could not resolve "
                        f"semantic contract provider {provider_key!r}."
                    ),
                    provider_key=provider_key,
                )
                for provider_key in missing_provider_keys
            ],
            missing_provider_keys=missing_provider_keys,
            provider_count=len(contracts),
            lane_count=sum(len(contract.syntax_lanes) for contract in contracts),
        )

    profile_key = (
        _optional_text(request.profile_key) or DEFAULT_CODE_GRAMMAR_PROFILE_KEY
    )
    coverage_requested = (
        request.include_declaration_coverage
        or bool(request.source_meaning_contracts)
        or request.strict_anchor_coverage
    )
    coverage: AwareGrammarDeclarationCoverageProfile | None = None
    try:
        if coverage_requested:
            coverage = build_aware_grammar_declaration_coverage_profile(
                profile_key=profile_key,
                semantic_contracts=contracts,
                source_meaning_contracts=request.source_meaning_contracts,
            )
            profile = coverage.profile
        else:
            profile = build_aware_grammar_semantic_profile(
                profile_key=profile_key,
                semantic_contracts=contracts,
                include_current_code_sections=request.include_current_code_sections,
            )
    except AwareGrammarSemanticProfileError as exc:
        invalid_rule_names = _invalid_grammar_rule_names_from_error(exc)
        return _grammar_profile_blocked_response(
            request=request,
            diagnostics=[
                CodeGrammarProfileDiagnostic(
                    reason="invalid_rule_names",
                    message=str(exc),
                    rule_name=rule_name,
                )
                for rule_name in invalid_rule_names
            ]
            or [
                CodeGrammarProfileDiagnostic(
                    reason="aware_grammar_profile_invalid",
                    message=str(exc),
                )
            ],
            invalid_rule_names=invalid_rule_names,
            provider_count=len(contracts),
            lane_count=sum(len(contract.syntax_lanes) for contract in contracts),
        )

    anchor_diagnostics = _code_anchor_coverage_diagnostics_from_coverage(coverage)
    missing_rule_declarations = (
        list(coverage.missing_rule_declarations) if coverage is not None else []
    )
    if coverage is not None and coverage.invalid_declaration_rules:
        invalid_rule_names = tuple(coverage.invalid_declaration_rules)
        return _grammar_profile_blocked_response(
            request=request,
            diagnostics=[
                CodeGrammarProfileDiagnostic(
                    reason="invalid_declaration_rule_names",
                    message=(
                        "Code grammar profile declaration coverage found "
                        f"unknown parser rule {rule_name!r}."
                    ),
                    rule_name=rule_name,
                    metadata=JsonObject(
                        {"source": "aware_code_service.grammar_profile"}
                    ),
                )
                for rule_name in invalid_rule_names
            ],
            invalid_rule_names=invalid_rule_names,
            missing_rule_declarations=missing_rule_declarations,
            anchor_diagnostics=anchor_diagnostics,
            provider_count=len(contracts),
            lane_count=sum(len(contract.syntax_lanes) for contract in contracts),
            declaration_rule_count=len(coverage.rule_declarations),
        )
    if request.strict_anchor_coverage and anchor_diagnostics:
        return _grammar_profile_blocked_response(
            request=request,
            diagnostics=[
                CodeGrammarProfileDiagnostic(
                    reason=diagnostic.reason,
                    message=diagnostic.message,
                    provider_key=diagnostic.provider_key,
                    rule_name=diagnostic.grammar_rule_name,
                    metadata=JsonObject(
                        {
                            "binding_key": diagnostic.binding_key,
                            "semantic_owner": diagnostic.semantic_owner,
                            "anchor_field_path": diagnostic.anchor_field_path,
                            "source": "aware_code_service.grammar_profile",
                        }
                    ),
                )
                for diagnostic in anchor_diagnostics
            ],
            missing_rule_declarations=missing_rule_declarations,
            anchor_diagnostics=anchor_diagnostics,
            provider_count=len(contracts),
            lane_count=sum(len(contract.syntax_lanes) for contract in contracts),
            declaration_rule_count=len(coverage.rule_declarations),
        )

    profile_dto = _code_grammar_profile_from_aware_profile(
        profile=profile,
        language=language,
        backend_key=backend_key,
        coverage=coverage,
    )
    return ResolveCodeGrammarProfileResponse(
        request_id=request.request_id,
        success=True,
        status=CodeGrammarProfileResolutionStatus.resolved,
        resolved=True,
        profile=profile_dto,
        diagnostics=[],
        missing_rule_declarations=missing_rule_declarations,
        anchor_diagnostics=anchor_diagnostics,
        provider_count=len(profile_dto.provider_keys),
        lane_count=len(profile_dto.lane_keys),
        rule_count=len(profile_dto.grammar_rules),
        declaration_rule_count=len(profile_dto.rule_declarations),
        anchor_diagnostic_count=len(anchor_diagnostics),
    )


def _grammar_profile_contracts(
    *,
    request: ResolveCodeGrammarProfileRequest,
    available_semantic_contracts: Sequence[CodeSemanticContract],
) -> tuple[tuple[CodeSemanticContract, ...], list[str]]:
    contracts_by_provider: dict[str, CodeSemanticContract] = {}
    for contract in request.semantic_contracts:
        provider_key = _optional_text(contract.provider_key)
        if provider_key is not None and provider_key not in contracts_by_provider:
            contracts_by_provider[provider_key] = contract

    available_by_provider = {
        provider_key: contract
        for contract in available_semantic_contracts
        if (provider_key := _optional_text(contract.provider_key)) is not None
    }
    missing_provider_keys: list[str] = []
    requested_provider_keys = tuple(
        dict.fromkeys(
            provider_key
            for provider_key in (
                _optional_text(provider_key) for provider_key in request.provider_keys
            )
            if provider_key is not None
        )
    )
    for provider_key in requested_provider_keys:
        if provider_key in contracts_by_provider:
            continue
        contract = available_by_provider.get(provider_key)
        if contract is None:
            missing_provider_keys.append(provider_key)
            continue
        contracts_by_provider[provider_key] = contract

    if not requested_provider_keys and not contracts_by_provider:
        contracts_by_provider.update(available_by_provider)

    return tuple(contracts_by_provider.values()), missing_provider_keys


def _code_grammar_profile_from_aware_profile(
    *,
    profile: AwareGrammarSemanticProfile,
    language: str,
    backend_key: str,
    coverage: AwareGrammarDeclarationCoverageProfile | None = None,
) -> CodeGrammarProfile:
    rule_bindings = [
        CodeGrammarRuleBinding(
            rule_name=str(binding.rule_name),
            provider_key=str(binding.provider_key),
            lane_key=str(binding.lane_key),
            semantic_owner=str(binding.semantic_owner),
            compiler_owner=str(binding.compiler_owner),
            code_section_type=(
                _enum_text(binding.code_section_type)
                if binding.code_section_type is not None
                else None
            ),
            semantic_token_types=list(binding.semantic_token_types),
            semantic_token_modifiers=list(binding.semantic_token_modifiers),
            metadata=JsonObject(
                {"source": "aware_code_service.grammar_profile.aware_backend"}
            ),
        )
        for binding in profile.rule_bindings
    ]
    rule_declarations = (
        _code_rule_declarations_from_coverage(coverage) if coverage is not None else []
    )
    anchor_diagnostics = _code_anchor_coverage_diagnostics_from_coverage(coverage)
    return CodeGrammarProfile(
        profile_key=str(profile.profile_key),
        language=language,
        backend_key=backend_key,
        backend=CodeGrammarBackendDescriptor(
            backend_key=backend_key,
            language=language,
            parser_kind="tree_sitter",
            grammar_contract_version=CODE_GRAMMAR_PROFILE_CONTRACT_VERSION,
            metadata=JsonObject(
                {
                    "backend_module": "aware_grammar.semantic_profile",
                    "source": "aware_code_service.grammar_profile",
                }
            ),
        ),
        provider_keys=list(profile.provider_keys),
        lane_keys=list(profile.lane_keys),
        grammar_rules=list(profile.grammar_rules),
        code_section_types=[
            _enum_text(section_type) for section_type in profile.code_section_types
        ],
        rule_bindings=rule_bindings,
        rule_declarations=rule_declarations,
        missing_rule_declarations=(
            list(coverage.missing_rule_declarations) if coverage is not None else []
        ),
        anchor_diagnostics=anchor_diagnostics,
        diagnostics=[],
        metadata=JsonObject(
            {
                "contract": CODE_GRAMMAR_PROFILE_CONTRACT_VERSION,
                "source": "aware_code_service.grammar_profile",
            }
        ),
    )


def _code_rule_declarations_from_coverage(
    coverage: AwareGrammarDeclarationCoverageProfile,
) -> list[CodeGrammarRuleDeclaration]:
    return [
        CodeGrammarRuleDeclaration(
            provider_key=item.provider_key,
            semantic_owner=item.semantic_owner,
            rule_name=item.rule_name,
            language=item.language,
            grammar_backend=item.grammar_backend,
            declared_anchor_fields=list(item.declared_anchor_fields),
            top_level=item.top_level,
            generation_status=item.generation_status,
            metadata=JsonObject(
                {"source": "aware_code_service.grammar_profile.declaration_coverage"}
            ),
        )
        for item in coverage.rule_declarations
    ]


def _code_anchor_coverage_diagnostics_from_coverage(
    coverage: AwareGrammarDeclarationCoverageProfile | None,
) -> list[CodeGrammarAnchorCoverageDiagnostic]:
    if coverage is None:
        return []
    return [
        CodeGrammarAnchorCoverageDiagnostic(
            reason=item.reason,
            message=item.message(),
            provider_key=item.provider_key,
            semantic_owner=item.semantic_owner,
            binding_key=item.binding_key,
            grammar_rule_name=item.grammar_rule_name,
            anchor_field_path=item.anchor_field_path,
            metadata=JsonObject(
                {"source": "aware_code_service.grammar_profile.declaration_coverage"}
            ),
        )
        for item in coverage.anchor_diagnostics
    ]


def _grammar_profile_blocked_response(
    *,
    request: ResolveCodeGrammarProfileRequest,
    diagnostics: list[CodeGrammarProfileDiagnostic],
    missing_provider_keys: list[str] | None = None,
    invalid_rule_names: tuple[str, ...] = (),
    missing_rule_declarations: list[str] | None = None,
    anchor_diagnostics: list[CodeGrammarAnchorCoverageDiagnostic] | None = None,
    provider_count: int = 0,
    lane_count: int = 0,
    declaration_rule_count: int = 0,
) -> ResolveCodeGrammarProfileResponse:
    return ResolveCodeGrammarProfileResponse(
        request_id=request.request_id,
        success=False,
        status=CodeGrammarProfileResolutionStatus.blocked,
        resolved=False,
        profile=None,
        diagnostics=diagnostics,
        missing_provider_keys=missing_provider_keys or [],
        invalid_rule_names=list(invalid_rule_names),
        missing_rule_declarations=missing_rule_declarations or [],
        anchor_diagnostics=anchor_diagnostics or [],
        provider_count=provider_count,
        lane_count=lane_count,
        rule_count=0,
        declaration_rule_count=declaration_rule_count,
        anchor_diagnostic_count=len(anchor_diagnostics or []),
        error=diagnostics[0].message if diagnostics else None,
    )


def _invalid_grammar_rule_names_from_error(
    error: AwareGrammarSemanticProfileError,
) -> tuple[str, ...]:
    marker = "unknown rules:"
    message = str(error)
    if marker not in message:
        return ()
    details = message.split(marker, 1)[1].strip()
    rule_names: list[str] = []
    for fragment in details.split("),"):
        rule_name = fragment.split("(", 1)[0].strip().strip(",")
        if rule_name:
            rule_names.append(rule_name)
    return tuple(dict.fromkeys(rule_names))


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _enum_text(value: object) -> str:
    raw_value = getattr(value, "value", value)
    return raw_value if isinstance(raw_value, str) else str(raw_value)


__all__ = [
    "CODE_GRAMMAR_PROFILE_BACKEND_KEY",
    "CODE_GRAMMAR_PROFILE_CONTRACT_VERSION",
    "CODE_GRAMMAR_PROFILE_LANGUAGE",
    "DEFAULT_CODE_GRAMMAR_PROFILE_KEY",
    "resolve_code_grammar_profile",
]
