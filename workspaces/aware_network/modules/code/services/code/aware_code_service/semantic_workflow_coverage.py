from __future__ import annotations

from collections.abc import Sequence

from aware_code_sdk.dto import (
    CodeGrammarProfileDiagnostic,
    CodeGrammarRuleBinding,
    CodeSemanticContract,
    CodeSemanticWorkflowCoverageDiagnostic,
    CodeSemanticWorkflowCoverageEntry,
    CodeSemanticWorkflowCoverageStatus,
    CodeSemanticWorkflowGrammarRuleEvidence,
    CodeSemanticWorkflowGraphBindingCoverage,
    ResolveCodeGrammarProfileRequest,
    ResolveCodeSemanticWorkflowCoverageRequest,
    ResolveCodeSemanticWorkflowCoverageResponse,
)
from aware_types import JsonObject

from .grammar_profile import resolve_code_grammar_profile


CODE_SEMANTIC_WORKFLOW_COVERAGE_SOURCE = (
    "aware_code_service.semantic_workflow_coverage"
)


def resolve_code_semantic_workflow_coverage(
    *,
    request: ResolveCodeSemanticWorkflowCoverageRequest,
    available_semantic_contracts: Sequence[CodeSemanticContract] = (),
) -> ResolveCodeSemanticWorkflowCoverageResponse:
    """Resolve Code-owned workflow grammar/source/graph-binding coverage."""

    contracts, missing_provider_keys = _coverage_contracts(
        request=request,
        available_semantic_contracts=available_semantic_contracts,
    )
    diagnostics: list[CodeSemanticWorkflowCoverageDiagnostic] = []
    if missing_provider_keys:
        diagnostics.extend(
            CodeSemanticWorkflowCoverageDiagnostic(
                reason="semantic_contract_unavailable",
                message=(
                    "Code semantic workflow coverage could not resolve "
                    f"semantic contract provider {provider_key!r}."
                ),
                provider_key=provider_key,
            )
            for provider_key in missing_provider_keys
        )
        return _coverage_response(
            request=request,
            status=CodeSemanticWorkflowCoverageStatus.blocked,
            covered=False,
            diagnostics=diagnostics,
            missing_provider_keys=missing_provider_keys,
            provider_count=len(contracts),
        )

    provider_keys = [contract.provider_key for contract in contracts]
    grammar_response = resolve_code_grammar_profile(
        request=ResolveCodeGrammarProfileRequest(
            profile_key=request.profile_key,
            language=request.language,
            backend_key=request.backend_key,
            provider_keys=provider_keys,
            semantic_contracts=list(contracts),
            include_current_code_sections=request.include_current_code_sections,
            strict=request.strict,
            metadata=request.metadata,
        )
    )
    if not grammar_response.resolved or grammar_response.profile is None:
        diagnostics.extend(
            _coverage_diagnostic_from_grammar_diagnostic(diagnostic)
            for diagnostic in grammar_response.diagnostics
        )
        return _coverage_response(
            request=request,
            status=CodeSemanticWorkflowCoverageStatus.blocked,
            covered=False,
            diagnostics=diagnostics,
            missing_provider_keys=list(grammar_response.missing_provider_keys),
            invalid_rule_names=list(grammar_response.invalid_rule_names),
            provider_count=grammar_response.provider_count,
        )

    rule_bindings_by_rule = {
        binding.rule_name: binding
        for binding in grammar_response.profile.rule_bindings
    }
    requested_workflow_keys = _normalized_token_set(request.workflow_keys)
    entries: list[CodeSemanticWorkflowCoverageEntry] = []
    for contract in contracts:
        for workflow in sorted(
            contract.semantic_workflows,
            key=lambda item: (item.priority, item.semantic_owner, item.workflow_key),
        ):
            if (
                requested_workflow_keys
                and _normalize_text(workflow.workflow_key) not in requested_workflow_keys
            ):
                continue
            entries.append(
                _coverage_entry(
                    contract=contract,
                    workflow=workflow,
                    rule_bindings_by_rule=rule_bindings_by_rule,
                    grammar_profile_key=grammar_response.profile.profile_key,
                )
            )

    if not entries:
        diagnostics.append(
            CodeSemanticWorkflowCoverageDiagnostic(
                reason="semantic_workflow_unavailable",
                message="No semantic workflows matched the coverage request.",
                metadata=JsonObject(
                    {
                        "provider_keys": provider_keys,
                        "workflow_keys": list(requested_workflow_keys),
                    }
                ),
            )
        )

    covered = bool(entries) and all(entry.covered for entry in entries)
    status = (
        CodeSemanticWorkflowCoverageStatus.covered
        if covered
        else CodeSemanticWorkflowCoverageStatus.blocked
    )
    return _coverage_response(
        request=request,
        status=status,
        covered=covered,
        entries=entries,
        diagnostics=diagnostics,
        provider_count=len(contracts),
    )


def _coverage_entry(
    *,
    contract: CodeSemanticContract,
    workflow,
    rule_bindings_by_rule: dict[str, CodeGrammarRuleBinding],
    grammar_profile_key: str,
) -> CodeSemanticWorkflowCoverageEntry:
    diagnostics: list[CodeSemanticWorkflowCoverageDiagnostic] = []
    if not _non_empty_tokens(workflow.grammar_profile_refs):
        diagnostics.append(
            _workflow_diagnostic(
                reason="missing_grammar_profile_ref",
                message="Semantic workflow must declare at least one grammar profile ref.",
                provider_key=contract.provider_key,
                workflow_key=workflow.workflow_key,
                ref_kind="grammar_profile",
            )
        )
    if not _non_empty_tokens(workflow.source_meaning_refs):
        diagnostics.append(
            _workflow_diagnostic(
                reason="missing_source_meaning_ref",
                message="Semantic workflow must declare at least one source-meaning ref.",
                provider_key=contract.provider_key,
                workflow_key=workflow.workflow_key,
                ref_kind="source_meaning",
            )
        )
    if not _non_empty_tokens(workflow.graph_binding_refs):
        diagnostics.append(
            _workflow_diagnostic(
                reason="missing_graph_binding_ref",
                message="Semantic workflow must declare at least one graph-binding ref.",
                provider_key=contract.provider_key,
                workflow_key=workflow.workflow_key,
                ref_kind="graph_binding",
            )
        )

    graph_binding_coverage: list[CodeSemanticWorkflowGraphBindingCoverage] = []
    grammar_rule_evidence: list[CodeSemanticWorkflowGrammarRuleEvidence] = []
    seen_rule_names: set[str] = set()
    for graph_binding_ref in _non_empty_tokens(workflow.graph_binding_refs):
        rule_name = _rule_name_from_graph_binding_ref(graph_binding_ref)
        binding = rule_bindings_by_rule.get(rule_name)
        covered = binding is not None
        graph_binding_coverage.append(
            CodeSemanticWorkflowGraphBindingCoverage(
                graph_binding_ref=graph_binding_ref,
                rule_name=rule_name,
                covered=covered,
                metadata=JsonObject(
                    {
                        "source": CODE_SEMANTIC_WORKFLOW_COVERAGE_SOURCE,
                        "match": "graph_binding_ref_terminal_rule_name",
                    }
                ),
            )
        )
        if binding is None:
            diagnostics.append(
                _workflow_diagnostic(
                    reason="graph_binding_rule_uncovered",
                    message=(
                        "Semantic workflow graph-binding ref is not covered "
                        f"by the resolved grammar profile rule {rule_name!r}."
                    ),
                    provider_key=contract.provider_key,
                    workflow_key=workflow.workflow_key,
                    ref_kind="graph_binding",
                    ref=graph_binding_ref,
                    rule_name=rule_name,
                )
            )
            continue
        if binding.rule_name not in seen_rule_names:
            seen_rule_names.add(binding.rule_name)
            grammar_rule_evidence.append(
                _grammar_rule_evidence(
                    binding=binding,
                    grammar_profile_key=grammar_profile_key,
                )
            )

    covered = not diagnostics
    return CodeSemanticWorkflowCoverageEntry(
        provider_key=contract.provider_key,
        workflow_key=workflow.workflow_key,
        semantic_owner=workflow.semantic_owner,
        stage_keys=list(workflow.stage_keys),
        status=(
            CodeSemanticWorkflowCoverageStatus.covered
            if covered
            else CodeSemanticWorkflowCoverageStatus.blocked
        ),
        covered=covered,
        grammar_profile_refs=list(_non_empty_tokens(workflow.grammar_profile_refs)),
        source_meaning_refs=list(_non_empty_tokens(workflow.source_meaning_refs)),
        ontology_feature_refs=list(_non_empty_tokens(workflow.ontology_feature_refs)),
        graph_binding_refs=list(_non_empty_tokens(workflow.graph_binding_refs)),
        grammar_rule_evidence=grammar_rule_evidence,
        graph_binding_coverage=graph_binding_coverage,
        diagnostics=diagnostics,
        metadata=JsonObject(
            {
                "source": CODE_SEMANTIC_WORKFLOW_COVERAGE_SOURCE,
                "grammar_profile_key": grammar_profile_key,
            }
        ),
    )


def _coverage_contracts(
    *,
    request: ResolveCodeSemanticWorkflowCoverageRequest,
    available_semantic_contracts: Sequence[CodeSemanticContract],
) -> tuple[tuple[CodeSemanticContract, ...], list[str]]:
    contracts_by_provider: dict[str, CodeSemanticContract] = {}
    for contract in request.semantic_contracts:
        provider_key = _normalize_text(contract.provider_key)
        if provider_key is not None and provider_key not in contracts_by_provider:
            contracts_by_provider[provider_key] = contract

    available_by_provider = {
        provider_key: contract
        for contract in available_semantic_contracts
        if (provider_key := _normalize_text(contract.provider_key)) is not None
    }
    missing_provider_keys: list[str] = []
    requested_provider_keys = tuple(
        dict.fromkeys(
            provider_key
            for provider_key in (
                _normalize_text(provider_key) for provider_key in request.provider_keys
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

    return (
        tuple(
            sorted(
                contracts_by_provider.values(),
                key=lambda item: item.provider_key,
            )
        ),
        missing_provider_keys,
    )


def _coverage_response(
    *,
    request: ResolveCodeSemanticWorkflowCoverageRequest,
    status: CodeSemanticWorkflowCoverageStatus,
    covered: bool,
    entries: list[CodeSemanticWorkflowCoverageEntry] | None = None,
    diagnostics: list[CodeSemanticWorkflowCoverageDiagnostic] | None = None,
    missing_provider_keys: list[str] | None = None,
    invalid_rule_names: list[str] | None = None,
    provider_count: int = 0,
) -> ResolveCodeSemanticWorkflowCoverageResponse:
    resolved_entries = entries or []
    return ResolveCodeSemanticWorkflowCoverageResponse(
        request_id=request.request_id,
        success=covered,
        status=status,
        covered=covered,
        entries=resolved_entries,
        diagnostics=diagnostics or [],
        missing_provider_keys=missing_provider_keys or [],
        invalid_rule_names=invalid_rule_names or [],
        provider_count=provider_count,
        workflow_count=len(resolved_entries),
        covered_workflow_count=sum(1 for entry in resolved_entries if entry.covered),
    )


def _grammar_rule_evidence(
    *,
    binding: CodeGrammarRuleBinding,
    grammar_profile_key: str,
) -> CodeSemanticWorkflowGrammarRuleEvidence:
    return CodeSemanticWorkflowGrammarRuleEvidence(
        grammar_profile_key=grammar_profile_key,
        rule_name=binding.rule_name,
        provider_key=binding.provider_key,
        lane_key=binding.lane_key,
        semantic_owner=binding.semantic_owner,
        compiler_owner=binding.compiler_owner,
        code_section_type=binding.code_section_type,
        semantic_token_types=list(binding.semantic_token_types),
        semantic_token_modifiers=list(binding.semantic_token_modifiers),
        metadata=JsonObject(
            {
                "source": CODE_SEMANTIC_WORKFLOW_COVERAGE_SOURCE,
                "binding_source": "code.grammar_profile.resolve",
            }
        ),
    )


def _coverage_diagnostic_from_grammar_diagnostic(
    diagnostic: CodeGrammarProfileDiagnostic,
) -> CodeSemanticWorkflowCoverageDiagnostic:
    return CodeSemanticWorkflowCoverageDiagnostic(
        severity=diagnostic.severity,
        reason=f"grammar_profile_{diagnostic.reason}",
        message=diagnostic.message,
        provider_key=diagnostic.provider_key,
        rule_name=diagnostic.rule_name,
        metadata=diagnostic.metadata,
    )


def _workflow_diagnostic(
    *,
    reason: str,
    message: str,
    provider_key: str,
    workflow_key: str,
    ref_kind: str | None = None,
    ref: str | None = None,
    rule_name: str | None = None,
) -> CodeSemanticWorkflowCoverageDiagnostic:
    return CodeSemanticWorkflowCoverageDiagnostic(
        reason=reason,
        message=message,
        provider_key=provider_key,
        workflow_key=workflow_key,
        ref_kind=ref_kind,
        ref=ref,
        rule_name=rule_name,
    )


def _rule_name_from_graph_binding_ref(ref: str) -> str:
    normalized = ref.strip()
    for separator in ("#", "/", "::"):
        if separator in normalized:
            normalized = normalized.rsplit(separator, 1)[-1]
    if "." in normalized:
        normalized = normalized.rsplit(".", 1)[-1]
    return normalized


def _non_empty_tokens(tokens: Sequence[str]) -> tuple[str, ...]:
    return tuple(
        token
        for token in (_normalize_text(token) for token in tokens)
        if token is not None
    )


def _normalized_token_set(tokens: Sequence[str]) -> frozenset[str]:
    return frozenset(
        token
        for token in (_normalize_text(token) for token in tokens)
        if token is not None
    )


def _normalize_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


__all__ = [
    "CODE_SEMANTIC_WORKFLOW_COVERAGE_SOURCE",
    "resolve_code_semantic_workflow_coverage",
]
