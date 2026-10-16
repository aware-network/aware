"""Actual selected-source custody is local, not a Storage worker grant.

Use the original Workspace reader, Code registration/executor/retained-result
verifier and Meta source assembler. These are disposable source conformance
fixtures, not installed producer qualification. No full compiler, evaluator,
Storage worker, database, graph publisher or domain store is invoked.
"""

from __future__ import annotations

import json
import os
import select
from dataclasses import replace
from pathlib import Path
from typing import Protocol, cast

import pytest
from aware_code_semantic_contract_runtime import ContractViolation
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_code_semantic_contract_runtime.source_origin import SemanticInputSourceOrigin
from aware_meta_contract_runtime_provider.codec import (
    decode_meta_package_source_closure,
)
from test_original_engine_input_join import (  # pyright: ignore[reportImplicitRelativeImport] -- original pytest fixture, not a library input
    _original_assembly,  # pyright: ignore[reportPrivateUsage] -- borrow actual supplier fixture without a replacement owner
)


class _OriginalSupplier(Protocol):
    host: inputs.SemanticInputProducerHost
    selected: object


class _JoinedSupplier(Protocol):
    original: _OriginalSupplier
    registration: inputs.AdmittedSemanticInputProducerRegistration
    expected: inputs.SemanticInputProductionExpectation
    result: SemanticBody
    source_origin: SemanticInputSourceOrigin


def _fixture_view(raw: object) -> _JoinedSupplier:
    # The legacy fixture returns a dynamic namespace. This typing view neither
    # creates a wrapper nor changes any original identity/registry field.
    return cast(_JoinedSupplier, raw)


def _verify(joined: _JoinedSupplier) -> None:
    # The original fixture yields an invocation, not an authority we construct.
    inputs.validate_registered_semantic_input_result(
        joined.original.host,
        joined.registration,
        source_admission=joined.original.selected,
        expected=joined.expected,
        result=joined.result,
    )


async def test_original_supplier_is_live_only_in_its_parent_scope(
    tmp_path: Path,
) -> None:
    async with _original_assembly(tmp_path) as raw:
        joined = _fixture_view(raw)
        _verify(joined)
        source = decode_meta_package_source_closure(joined.result.canonical_body)
        assert joined.result.coordinate.role == "source_closure"
        assert (
            source.source_epoch_ref == joined.source_origin.source_identity_digest.value
        )
        assert joined.expected.source_identity is joined.original.selected
        # The supplier produces a source closure, not the complete compiled
        # snapshot required by Storage configuration admission.
        assert (
            joined.result.coordinate.contract.key
            == "aware.meta.package-source-closure.v1"
        )
        retained_body = joined.result.canonical_body
    assert joined.result.canonical_body == retained_body
    with pytest.raises(ContractViolation):
        _verify(joined)


async def test_equal_source_body_cannot_recreate_retained_invocation(
    tmp_path: Path,
) -> None:
    async with _original_assembly(tmp_path) as raw:
        joined = _fixture_view(raw)
        _verify(joined)
        copied = replace(joined.result)
        assert copied is not joined.result
        assert copied.canonical_body == joined.result.canonical_body
        assert copied.coordinate == joined.result.coordinate
        # Exact bytes and a lawful exact SemanticBody are structural evidence,
        # not the originally returned object registered by Code.
        with (
            inputs.original_result_verification_work_scope(
                result_visits=0,
                source_calls=0,
                context_calls=0,
            ),
            pytest.raises(
                ContractViolation,
                match="original returned semantic input result required",
            ),
        ):
            inputs.validate_registered_semantic_input_result(
                joined.original.host,
                joined.registration,
                source_admission=joined.original.selected,
                expected=joined.expected,
                result=copied,
            )
        _verify(joined)


async def test_new_receiver_host_has_no_original_source_result_registry(
    tmp_path: Path,
) -> None:
    async with _original_assembly(tmp_path) as raw:
        joined = _fixture_view(raw)
        _verify(joined)
        receiver = inputs.SemanticInputProducerHost()
        try:
            with (
                inputs.original_result_verification_work_scope(
                    result_visits=0,
                    source_calls=0,
                    context_calls=0,
                ),
                pytest.raises(
                    ContractViolation,
                    match="original returned semantic input result required",
                ),
            ):
                inputs.validate_registered_semantic_input_result(
                    receiver,
                    joined.registration,
                    source_admission=joined.original.selected,
                    expected=joined.expected,
                    result=joined.result,
                )
        finally:
            receiver.close()
        _verify(joined)


@pytest.mark.parametrize("field", ["source_admission", "source_production"])
async def test_worker_host_has_no_serialized_supplier_custody_entrance(
    tmp_path: Path,
    field: str,
) -> None:
    from aware_ontology_meta_object_provider.storage_worker_host import (
        decode_storage_worker_host,
    )

    async with _original_assembly(tmp_path) as raw:
        joined = _fixture_view(raw)
        _verify(joined)
        digest = joined.result.coordinate.digest.value
        # Comparison data only. The real host decoder runs, but no host bind,
        # path read, journal, worker or publisher is called. A valid structural
        # host input is not a selected store or source capability.
        host: dict[str, object] = {
            "contract": "aware.ontology.storage.worker.host.v1",
            "provider": ["provider:storage", "generation:storage", "authority:storage"],
            "operation": [
                "branch:storage",
                "actor:storage",
                "projection:storage",
                "attempt:storage",
                "key:storage",
                "blob:42",
            ],
            "application": ["application:storage", digest],
            "store": ["/inert-domain", "store:storage", 1, 2, digest],
            "lane": ["oig:storage", "branch:storage", "lane:storage"],
            "mapping": ["source:storage", digest, digest, digest],
            "configurations": [b"inert OCG".hex(), b"inert OPG".hex()],
            "journals": [
                "/inert-service",
                1,
                3,
                "/inert-attempt",
                1,
                4,
                digest,
                digest,
            ],
        }

        def encode() -> bytes:
            return json.dumps(
                host,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode()

        _ = decode_storage_worker_host(encode())
        # Even the complete genuine parent result/body/coordinate cannot add a
        # new receiving authority to the existing closed worker ABI.
        host[field] = {
            "coordinate": joined.result.coordinate.to_wire(),
            "canonical_body": joined.result.canonical_body.hex(),
            "input_digest": joined.expected.input_digest.value,
        }
        with pytest.raises(ValueError, match="Storage host fields differ"):
            _ = decode_storage_worker_host(encode())
        _verify(joined)


@pytest.mark.skipif(not hasattr(os, "fork"), reason="real POSIX process-boundary proof")
async def test_inherited_original_supplier_rejects_before_owner_calls(
    tmp_path: Path,
) -> None:
    async with _original_assembly(tmp_path) as raw:
        joined = _fixture_view(raw)
        _verify(joined)
        read_fd, write_fd = os.pipe()
        child = os.fork()
        if child == 0:
            os.close(read_fd)
            status = 1
            try:
                # A budget of zero proves rejection precedes retained-source
                # or context verification, without replacing owner methods or
                # simulating a PID change. Fork inherits all original objects.
                with inputs.original_result_verification_work_scope(
                    result_visits=0,
                    source_calls=0,
                    context_calls=0,
                ):
                    _verify(joined)
                payload = {"accepted": True}
            except ContractViolation as error:
                payload = {"accepted": False, "reason": str(error)}
                status = 0
            except BaseException as error:  # noqa: BLE001 -- child must report then exit, never resume the parent's pytest
                payload = {"unexpected": type(error).__name__, "reason": str(error)}
            try:
                body = json.dumps(payload, sort_keys=True).encode()
                if os.write(write_fd, body) != len(body):
                    status = 1
            finally:
                os.close(write_fd)
                os._exit(status)
        os.close(write_fd)
        try:
            ready, _, _ = select.select([read_fd], [], [], 10.0)
            if not ready:
                os.kill(child, 9)
            _, status = os.waitpid(child, 0)  # noqa: ASYNC222 -- bounded isolated fork proof, no owner coroutine/thread transfer
            assert ready, "source verification child did not complete"
            assert os.waitstatus_to_exitcode(status) == 0
            payload = cast(dict[str, object], json.loads(os.read(read_fd, 4096)))
            assert payload == {
                "accepted": False,
                "reason": "semantic input host belongs to another process",
            }
        finally:
            os.close(read_fd)
        # Child refusal must not expire the parent's live original custody.
        _verify(joined)
