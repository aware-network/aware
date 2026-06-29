from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Code Ontology
from aware_code_ontology.package.code_package_delta_producer_code import CodePackageDeltaProducerCode

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.stable_ids import stable_code_package_delta_producer_code_id
from aware_code_ontology.package.code_package_code import CodePackageCode
from aware_code_ontology.package.code_package_delta_producer import CodePackageDeltaProducer
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_code_package_delta_producer(
    code_package_delta_producer_id: UUID,
    code_package_code_id: UUID,
    input_code_package_id: UUID | None = None,
    input_object_instance_graph_commit_id: UUID | None = None,
    input_digest: str | None = None,
    output_digest: str | None = None,
    emission_payload: JsonObject | None = None,
) -> CodePackageDeltaProducerCode:
    """
    Attach one producer emission to package-owned Code.
    """

    # --- AWARE: LOGIC START build_via_code_package_delta_producer
    session = current_handler_session()
    producer = session.imap_get(CodePackageDeltaProducer, code_package_delta_producer_id)
    if producer is None:
        raise RuntimeError(
            "CodePackageDeltaProducerCode.build_via_code_package_delta_producer requires existing producer: "
            + f"code_package_delta_producer_id={code_package_delta_producer_id}"
        )
    code_package_code = session.imap_get(CodePackageCode, code_package_code_id)
    if code_package_code is None:
        raise RuntimeError(
            "CodePackageDeltaProducerCode.build_via_code_package_delta_producer requires existing CodePackageCode: "
            + f"code_package_code_id={code_package_code_id}"
        )

    link_id = stable_code_package_delta_producer_code_id(
        code_package_delta_producer_id=code_package_delta_producer_id,
        code_package_code_id=code_package_code_id,
    )
    existing = session.imap_get(CodePackageDeltaProducerCode, link_id)
    if existing is not None:
        if (
            existing.code_package_delta_producer_id != code_package_delta_producer_id
            or existing.code_package_code_id != code_package_code_id
        ):
            raise RuntimeError(
                "CodePackageDeltaProducerCode.build_via_code_package_delta_producer payload mismatch "
                + f"for existing link: code_package_delta_producer_code_id={link_id}"
            )
        existing.code_package_code = code_package_code
        existing.input_code_package_id = input_code_package_id
        existing.input_object_instance_graph_commit_id = input_object_instance_graph_commit_id
        existing.input_digest = input_digest
        existing.output_digest = output_digest
        existing.emission_payload = emission_payload
        return existing

    return CodePackageDeltaProducerCode(
        id=link_id,
        code_package_delta_producer_id=code_package_delta_producer_id,
        code_package_code_id=code_package_code_id,
        code_package_code=code_package_code,
        input_code_package_id=input_code_package_id,
        input_object_instance_graph_commit_id=input_object_instance_graph_commit_id,
        input_digest=input_digest,
        output_digest=output_digest,
        emission_payload=emission_payload,
    )
    # --- AWARE: LOGIC END build_via_code_package_delta_producer
