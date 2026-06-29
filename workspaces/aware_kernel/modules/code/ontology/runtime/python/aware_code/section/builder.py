"""Build a code section from a code node."""

import hashlib
from typing import cast
from uuid import UUID

# Code
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_section_enums import CodeSectionType

# Content
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

# Code Section Builder Index
from aware_code.section.builder_index import CodeSectionBuilderIndex

from aware_code.node.node import CodeNode, T_Node
from aware_code.node.adapter import CodeNodeAdapter
from aware_code.types.json import Json

# Aware Core
from aware_utils.logging import logger


def build_section_from_bytes(
    code_section_type: CodeSectionType,
    code: Code,
    section_index: CodeSectionBuilderIndex,
    qualname: str,
    body_bytes: bytes,
    byte_start: int,
    byte_end: int,
    parent_id: UUID | None = None,
    reference: str | None = None,
    metadata: Json | None = None,
) -> CodeSection:
    """
    Create a new base CodeSection with identity hash.

    This is a helper method for all builders to use when creating
    a new CodeSection. It handles:
    1. Creating the identity hash
    2. Checking for existing section
    3. Creating the base CodeSection only if needed
    4. Adding it to the section_index

    Args:
        code_section_type: The type of code section to create
        code: The code object
        section_index: Shared index of sections to add the section to
        qualname: The qualname of the section
        body_bytes: The body bytes of the section
        byte_start: The start byte position of the section
        byte_end: The end byte position of the section
        parent_id: Optional ID of the parent section
        reference: Optional reference string for lookup
        metadata: Optional metadata dict for surgical editing support
    Returns:
        The created CodeSection
    """
    section_key = make_section_key(
        code_section_type=code_section_type,
        qualname=qualname,
        reference=reference,
    )
    identity_hash = make_identity_hash(
        code_section_type=code_section_type,
        code_id=code.id,
        qualname=qualname,
        body_bytes=body_bytes,
    )

    existing = section_index.get_by_hash(code_section_type, identity_hash)
    if existing:
        code_section = existing
        logger.warning(
            f"Reusing existing {code_section_type.name} section for {qualname} (identity_hash={identity_hash[:8]}...)",
        )
    else:
        code_section = CodeSection(
            code_id=code.id,
            section_key=section_key,
            type=code_section_type,
            identity_hash=identity_hash,
            qualname=qualname,
            content_part_text_segment=ContentPartTextSegment(
                content_part_text=code.content_part_text,
                byte_start=byte_start,
                byte_end=byte_end,
                parent_id=parent_id,
            ),
            metadata=metadata,
        )
        section_index.add(code_section=code_section)

    if reference:
        section_index.add_reference(code_section_type, reference, code_section)

    return code_section


def make_section_key(
    *,
    code_section_type: CodeSectionType,
    qualname: str,
    reference: str | None,
) -> str:
    qualname_clean = qualname.strip()
    if qualname_clean:
        return qualname_clean
    reference_clean = (reference or "").strip()
    if reference_clean:
        return reference_clean
    raise ValueError(
        "CodeSection builder requires a canonical descriptive key: "
        f"section_type={code_section_type.value}"
    )


def build_section_from_code(
    adapter: CodeNodeAdapter[T_Node],
    code_section_type: CodeSectionType,
    source: bytes,
    code: Code,
    node: CodeNode[T_Node],
    section_index: CodeSectionBuilderIndex,
    parent: str | None = None,
    parent_id: UUID | None = None,
    metadata: Json | None = None,
) -> CodeSection:
    # Get the qualname, body bytes and reference string
    qualname, body_bytes, reference = get_code_identity_info(adapter, source, node, parent)

    return build_section_from_code_by_identity(
        code_section_type=code_section_type,
        code=code,
        node=node,
        section_index=section_index,
        qualname=qualname,
        body_bytes=body_bytes,
        reference=reference,
        parent_id=parent_id,
        metadata=metadata,
    )


def build_section_from_code_by_identity(
    code_section_type: CodeSectionType,
    code: Code,
    node: CodeNode[T_Node],
    section_index: CodeSectionBuilderIndex,
    qualname: str,
    body_bytes: bytes,
    reference: str | None = None,
    parent_id: UUID | None = None,
    metadata: Json | None = None,
) -> CodeSection:
    """
    Create a new CodeSection from a code node by identity.

    Args:
        code_section_type: The type of code section to create
        code: The code object
        node: The node to create a section
        section_index: Shared index of sections to add the section to
        qualname: The qualname of the section
        body_bytes: The body bytes of the section
        reference: Optional reference string for lookup
        parent_id: Optional ID of the parent section
        metadata: Optional metadata dict for surgical editing support
    Returns:
        The created CodeSection
    """
    code_section = build_section_from_bytes(
        code_section_type=code_section_type,
        code=code,
        qualname=qualname,
        body_bytes=body_bytes,
        byte_start=node.byte_start,
        byte_end=node.byte_end,
        section_index=section_index,
        parent_id=parent_id,
        reference=reference,
        metadata=metadata,
    )

    # Link the code node to the code section
    section_index.add_section_node(
        code_section_id=code_section.id,
        code_node=cast(CodeNode[object], node),
    )

    return code_section


def make_identity_hash(code_section_type: CodeSectionType, code_id: UUID, qualname: str, body_bytes: bytes) -> str:
    """
    Generate a deterministic hash for a code section.

    This hash is used to uniquely identify a section across runs,
    even if the exact position or formatting changes.

    Args:
        code_section_type: Type of section (CLASS, FUNCTION, etc.)
        code_id: ID of the containing code object
        qualname: Fully qualified name (e.g., namespace.class.method)
        body_bytes: Normalized content bytes for hashing

    Returns:
        SHA-1 hash as a hex string
    """
    # Create a consistent hash from the key pieces of identity.
    #
    # IMPORTANT:
    # `Code.id` is currently runtime-generated (uuid4) and is therefore not stable across
    # processes/machines. Including it here would make `identity_hash` non-deterministic,
    # which breaks compiler-owned commit rails (OCG/OIG determinism) when any meta entities
    # reference code section identities.
    _ = code_id
    body_hash = hashlib.sha1(body_bytes).hexdigest()
    combined = f"{code_section_type.name}:{qualname}:{body_hash}".encode()
    return hashlib.sha1(combined).hexdigest()


def get_code_identity_info(
    adapter: CodeNodeAdapter[T_Node], source: bytes, node: CodeNode[T_Node], parent: str | None = None
) -> tuple[str, bytes, str | None]:
    # Get the qualname
    qualname = adapter.qualname(node, parent)

    # Get the body bytes
    body_bytes = adapter.body_bytes(node, source)

    # Get optional reference string for lookup
    reference = adapter.reference_string(node, parent)

    return qualname, body_bytes, reference
