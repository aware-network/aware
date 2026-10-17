"""Original Workspace expectation owns the source/context join, not a copy."""
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import product_input_context as contexts
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputContextContract,
)
from aware_workspace_runtime.source_observation import SourceObservationUnavailable
from test_product_input_context import original as code_context
from test_v3_source_admission import _pre_request_source


@pytest.mark.asyncio
async def test_original_expectation_joins_pending_then_bound_provider_context(tmp_path):
    async with _pre_request_source(tmp_path, with_local_provider=True) as (_, _, issuer, selected, coordinates):
        package = issuer.inspect_inputs(selected)[0].package
        with code_context(source=selected, operation=issuer._exclusion._parent,
                          coordinates=coordinates, package=package) as (supplier, receipt, *_):
            body = supplier.supplied.body
            rows = ((body.coordinate.role, body.coordinate.contract, receipt),)
            contracts = (SemanticInputContextContract(body.coordinate.role, body.coordinate.contract),)
            with issuer.original_pre_request_input(selected, use_ref="original-provider-context", stage="input",
                    source_coordinates=coordinates, context_contracts=contracts, context_receipts=rows) as expected:
                assert expected.context_bodies[0] is body
                issuer.validate_semantic_input_source(selected, expected=expected)
                contexts._bind(receipt, expected)
                issuer.validate_semantic_input_source(selected, expected=expected)
                with pytest.raises(SourceObservationUnavailable):
                    issuer.validate_semantic_input_source(selected, expected=replace(expected))
                issuer.validate_semantic_input_source(selected, expected=expected)
            with pytest.raises(SourceObservationUnavailable):
                issuer.validate_semantic_input_source(selected, expected=expected)


@pytest.mark.asyncio
async def test_provider_context_mutation_terminally_retires_original_expectation(tmp_path):
    async with _pre_request_source(tmp_path, with_local_provider=True) as (_, _, issuer, selected, coordinates):
        package = issuer.inspect_inputs(selected)[0].package
        with code_context(source=selected, operation=issuer._exclusion._parent,
                          coordinates=coordinates, package=package) as (supplier, receipt, *_):
            body = supplier.supplied.body
            rows = ((body.coordinate.role, body.coordinate.contract, receipt),)
            contracts = (SemanticInputContextContract(body.coordinate.role, body.coordinate.contract),)
            with (
                pytest.raises((SourceObservationUnavailable, ContractViolation)),
                issuer.original_pre_request_input(selected, use_ref="terminal-provider-context", stage="input",
                    source_coordinates=coordinates, context_contracts=contracts, context_receipts=rows) as expected,
            ):
                contexts._bind(receipt, expected)
                original = body.canonical_body
                object.__setattr__(body, "canonical_body", b"{}")
                with pytest.raises(ContractViolation):
                    issuer.validate_semantic_input_source(selected, expected=expected)
                object.__setattr__(body, "canonical_body", original)
                issuer.validate_semantic_input_source(selected, expected=expected)
            assert supplier.closed == 1


@pytest.mark.asyncio
async def test_context_verifier_substitution_never_dispatches_foreign_helper(tmp_path, monkeypatch):
    async with _pre_request_source(tmp_path, with_local_provider=True) as (_, _, issuer, selected, coordinates):
        package = issuer.inspect_inputs(selected)[0].package
        with code_context(source=selected, operation=issuer._exclusion._parent,
                          coordinates=coordinates, package=package) as (supplier, receipt, *_):
            body = supplier.supplied.body
            calls = []
            monkeypatch.setattr(contexts, "require_product_input_context_receipt", lambda *a, **k: calls.append(True))
            with (
                pytest.raises(ContractViolation),
                issuer.original_pre_request_input(selected, use_ref="foreign-context-verifier", stage="input",
                    source_coordinates=coordinates,
                    context_contracts=(SemanticInputContextContract(body.coordinate.role, body.coordinate.contract),),
                    context_receipts=((body.coordinate.role, body.coordinate.contract, receipt),)),
            ):
                pytest.fail("substituted verifier admitted context")
            assert calls == []
