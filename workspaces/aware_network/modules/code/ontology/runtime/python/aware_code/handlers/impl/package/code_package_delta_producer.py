from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Code Ontology
from aware_code_ontology.package.code_package_delta_producer import CodePackageDeltaProducer
from aware_code_ontology.package.code_package_delta_producer_code import CodePackageDeltaProducerCode

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.handlers.impl.package import code_package_delta_producer_code as producer_code_handler
from aware_code.stable_ids import stable_code_package_delta_producer_id
from aware_code_ontology.package.code_package import CodePackage
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def link_code(
    code_package_delta_producer: CodePackageDeltaProducer,
    code_package_code_id: UUID,
    input_code_package_id: UUID | None = None,
    input_object_instance_graph_commit_id: UUID | None = None,
    input_digest: str | None = None,
    output_digest: str | None = None,
    emission_payload: JsonObject | None = None,
) -> CodePackageDeltaProducerCode:
    """
    Link one producer emission to package-owned Code.
    """

    # --- AWARE: LOGIC START link_code
    linked = await producer_code_handler.build_via_code_package_delta_producer(
        code_package_delta_producer_id=code_package_delta_producer.id,
        code_package_code_id=code_package_code_id,
        input_code_package_id=input_code_package_id,
        input_object_instance_graph_commit_id=input_object_instance_graph_commit_id,
        input_digest=input_digest,
        output_digest=output_digest,
        emission_payload=emission_payload,
    )
    for existing in code_package_delta_producer.code_package_delta_producer_codes:
        if existing.id == linked.id:
            return existing
    code_package_delta_producer.code_package_delta_producer_codes.append(linked)
    return linked
    # --- AWARE: LOGIC END link_code


async def build_via_code_package(
    code_package_id: UUID,
    provider_key: str,
    producer_key: str,
    producer_kind: str | None = None,
    provider_payload: JsonObject | None = None,
) -> CodePackageDeltaProducer:
    """
    Create one package-local raw delta producer identity.
    """

    # --- AWARE: LOGIC START build_via_code_package
    normalized_provider_key = (provider_key or "").strip()
    normalized_producer_key = (producer_key or "").strip()
    if not normalized_provider_key:
        raise RuntimeError("CodePackageDeltaProducer.build_via_code_package requires non-empty provider_key")
    if not normalized_producer_key:
        raise RuntimeError("CodePackageDeltaProducer.build_via_code_package requires non-empty producer_key")

    session = current_handler_session()
    code_package = session.imap_get(CodePackage, code_package_id)
    if code_package is None:
        raise RuntimeError(
            "CodePackageDeltaProducer.build_via_code_package requires existing CodePackage: "
            + f"code_package_id={code_package_id}"
        )

    producer_id = stable_code_package_delta_producer_id(
        code_package_id=code_package_id,
        provider_key=normalized_provider_key,
        producer_key=normalized_producer_key,
    )
    existing = session.imap_get(CodePackageDeltaProducer, producer_id)
    if existing is not None:
        if (
            existing.code_package_id != code_package_id
            or (existing.provider_key or "").strip() != normalized_provider_key
            or (existing.producer_key or "").strip() != normalized_producer_key
        ):
            raise RuntimeError(
                "CodePackageDeltaProducer.build_via_code_package payload mismatch for existing producer: "
                + f"code_package_delta_producer_id={producer_id}"
            )
        existing.producer_kind = (producer_kind or "").strip() or None
        existing.provider_payload = provider_payload
        return existing

    return CodePackageDeltaProducer(
        id=producer_id,
        code_package_id=code_package_id,
        provider_key=normalized_provider_key,
        producer_key=normalized_producer_key,
        producer_kind=(producer_kind or "").strip() or None,
        provider_payload=provider_payload,
    )
    # --- AWARE: LOGIC END build_via_code_package
