"""Bound synchronous projection reuse without weakening original currentness."""

import asyncio
from contextlib import closing
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    PACKAGE_CONTEXT_INPUT_REF,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputContextContract,
    SemanticInputProducerHost,
    execute_registered_semantic_input,
)
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime.declaration_scope_admission import (
    WorkspaceDeclarationScopeRuntime,
)
from test_v3_source_admission import (
    _original_selection,
    _pre_request_source,
    _register_pre_request_producer,
)


async def test_recursive_original_results_rebuild_closure_only_at_window_edges(
    tmp_path, monkeypatch,
):
    async with _original_selection(tmp_path, ontology=True) as original:
        with original.issuer.original_selected_source_input(
            original.selected, use_ref="bounded-validation", stage="selected",
            **original.arguments,
        ) as expected:
            calls = []
            genuine = WorkspaceDeclarationScopeRuntime._closure

            def counted(self, *args, **kwargs):
                calls.append(self)
                return genuine(self, *args, **kwargs)

            monkeypatch.setattr(WorkspaceDeclarationScopeRuntime, "_closure", counted)
            original.issuer.validate_semantic_input_source(original.selected, expected=expected)
            # Entry binding, entry closure and final full binding. Recursive
            # Code result validation still executes inside these full checks.
            assert len(calls) == 3
            assert original.issuer._semantic_source_window is None
            calls.clear()
            original.issuer.validate_semantic_input_context(original.selected, expected=expected)
            assert len(calls) == 3  # A new callback never inherits reuse.


@pytest.mark.parametrize("change", ["source", "declaration", "added_source"])
async def test_mutation_after_nested_validation_rejects_before_return_and_cannot_resume(
    tmp_path, monkeypatch, change,
):
    async with _pre_request_source(tmp_path) as (root, _, issuer, selected, sources):
        with pytest.raises(SourceObservationUnavailable), issuer.original_pre_request_input(
            selected, use_ref="final-currentness", stage="source", source_coordinates=sources,
        ) as expected:
            target = root / (
                "workspaces/kernel/modules/main/aware.module.toml" if change == "declaration"
                else "workspaces/network/modules/main/package/"
                + ("new.bin" if change == "added_source" else "a.bin")
            )
            before = target.read_bytes() if target.exists() else None
            genuine = WorkspaceDeclarationScopeRuntime._validate_semantic_input_source

            def changed(self, source_admission, *, expected):
                genuine(self, source_admission, expected=expected)
                target.write_bytes(b"changed after the nested validation")

            monkeypatch.setattr(WorkspaceDeclarationScopeRuntime, "_validate_semantic_input_source", changed)
            try:
                with pytest.raises(SourceObservationUnavailable):
                    issuer.validate_semantic_input_source(selected, expected=expected)
                assert issuer._semantic_source_window is None
            finally:
                if before is None:
                    target.unlink()
                else:
                    target.write_bytes(before)
                monkeypatch.setattr(WorkspaceDeclarationScopeRuntime, "_validate_semantic_input_source", genuine)
            issuer.validate_semantic_input_source(selected, expected=expected)
        assert not issuer._pre_request_inputs


async def test_private_projection_returns_are_detached_and_window_does_not_escape(tmp_path):
    async with _pre_request_source(tmp_path) as (_, _, issuer, selected, sources):
        with issuer.original_pre_request_input(
            selected, use_ref="detached-validation", stage="source", source_coordinates=sources,
        ) as expected:
            record = issuer._selected_record(selected)
            with issuer._original_semantic_source_window(selected, expected):
                first = issuer.read_selected_package_source(selected)
                second = issuer.read_selected_package_source(selected)
                assert first == second and first is not second
                assert first.candidates is not second.candidates
                closure = issuer.read_declaration_scope(record.declaration)
                window = issuer._semantic_source_window
                assert window is not None
                assert closure is not window.closure
                assert closure == issuer.read_declaration_scope(record.declaration)
            assert issuer._semantic_source_window is None
            issuer.validate_semantic_input_source(selected, expected=expected)


async def test_copied_expectation_does_not_revoke_original_family(tmp_path):
    async with _pre_request_source(tmp_path) as (_, _, issuer, selected, sources):
        with issuer.original_pre_request_input(
            selected, use_ref="foreign-validation", stage="source", source_coordinates=sources,
        ) as expected:
            with pytest.raises((ContractViolation, SourceObservationUnavailable)):
                issuer.validate_semantic_input_source(selected, expected=replace(expected))
            assert issuer._semantic_source_window is None
            issuer.validate_semantic_input_source(selected, expected=expected)


async def test_exception_clears_projection_window_and_retires_original_use(tmp_path, monkeypatch):
    async with _pre_request_source(tmp_path) as (_, _, issuer, selected, sources):
        with pytest.raises(SourceObservationUnavailable), issuer.original_pre_request_input(
            selected, use_ref="failed-validation", stage="source", source_coordinates=sources,
        ) as expected:
            genuine = WorkspaceDeclarationScopeRuntime._validate_semantic_input_source

            def interrupted(self, source_admission, *, expected):
                raise KeyboardInterrupt("interrupted synchronous source check")

            monkeypatch.setattr(WorkspaceDeclarationScopeRuntime, "_validate_semantic_input_source", interrupted)
            with pytest.raises(KeyboardInterrupt):
                issuer.validate_semantic_input_source(selected, expected=expected)
            assert issuer._semantic_source_window is None
            monkeypatch.setattr(WorkspaceDeclarationScopeRuntime, "_validate_semantic_input_source", genuine)
            issuer.validate_semantic_input_source(selected, expected=expected)
        assert not issuer._pre_request_inputs


async def test_reuse_is_absent_during_and_after_awaited_owner_execution(tmp_path):
    async with _pre_request_source(tmp_path) as (_, _, issuer, selected, sources):
        with issuer.original_pre_request_input(
            selected, use_ref="owner-boundary", stage="source", source_coordinates=sources,
            context_contracts=(SemanticInputContextContract("package_context", PACKAGE_CONTEXT_INPUT_REF),),
        ) as expected:
            output = SemanticBody(SemanticValueCoordinate(
                "prepared", sources[0].coordinate.contract, "prepared:owner-boundary",
                ContentDigest.of_bytes(b"original owner output"), len(b"original owner output"),
            ), b"original owner output")
            seen = []

            async def produce(value):
                assert issuer._semantic_source_window is None
                await asyncio.sleep(0)
                assert issuer._semantic_source_window is None
                seen.append(value)
                return output

            with closing(SemanticInputProducerHost()) as host:
                registration = _register_pre_request_producer(host, issuer, expected, produce, output)
                result = await execute_registered_semantic_input(
                    host, registration, source_admission=selected, expected=expected,
                )
                assert result.canonical_body == output.canonical_body
            assert len(seen) == 1
            assert issuer._semantic_source_window is None
