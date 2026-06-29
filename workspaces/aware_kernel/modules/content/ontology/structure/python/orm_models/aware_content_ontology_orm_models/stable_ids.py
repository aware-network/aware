# GENERATED CODE - DO NOT MODIFY BY HAND
# Canonical stable-id derivations (UUIDv5).
from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

NS_CONTENT = uuid5(NAMESPACE_URL, "aware://content/v1")


def stable_content_id(*, key: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip()
    return uuid5(NS_CONTENT, f"aware:content:{key_norm}")


def stable_content_chain_id(*, key: str = "default") -> UUID:
    """Compiler-generated from class-attribute identity keys: key"""

    key_norm = (key or "").casefold().strip() or "default"
    return uuid5(NS_CONTENT, f"aware:content_chain:{key_norm}")


def stable_content_chain_content_id(*, content_chain_id: UUID, position: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: content_chain_id, position"""

    return uuid5(NS_CONTENT, f"aware:content_chain_content:{content_chain_id}:{position}")


def stable_content_chain_section_id(*, content_chain_id: UUID, key: str = "default") -> UUID:
    """Compiler-generated from class-attribute identity keys: content_chain_id, key"""

    key_norm = (key or "").casefold().strip() or "default"
    return uuid5(NS_CONTENT, f"aware:content_chain_section:{content_chain_id}:{key_norm}")


def stable_content_index_id(*, content_id: UUID, key: str = "default") -> UUID:
    """Compiler-generated from class-attribute identity keys: content_id, key"""

    key_norm = (key or "").casefold().strip() or "default"
    return uuid5(NS_CONTENT, f"aware:content_index:{content_id}:{key_norm}")


def stable_content_layout_id(*, content_id: UUID, name: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: content_id, name"""

    name_norm = (name or "").casefold().strip()
    return uuid5(NS_CONTENT, f"aware:content_layout:{content_id}:{name_norm}")


def stable_content_part_id(*, content_part_content_id: UUID, type: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: content_part_content_id, type"""

    type_norm = (type or "").casefold().strip()
    return uuid5(NS_CONTENT, f"aware:content_part:{content_part_content_id}:{type_norm}")


def stable_content_part_content_id(*, content_id: UUID, position: int) -> UUID:
    """Compiler-generated from class-attribute identity keys: content_id, position"""

    return uuid5(NS_CONTENT, f"aware:content_part_content:{content_id}:{position}")


def stable_content_part_content_layout_id(
    *, content_part_content_id: UUID, content_layout_id: UUID, layout_order: int = 0
) -> UUID:
    """Compiler-generated from class-attribute identity keys: content_part_content_id, content_layout_id, layout_order"""

    return uuid5(
        NS_CONTENT, f"aware:content_part_content_layout:{content_part_content_id}:{content_layout_id}:{layout_order}"
    )


def stable_content_part_file_id(*, content_part_id: UUID, modality_type: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: content_part_id, modality_type"""

    modality_type_norm = (modality_type or "").casefold().strip()
    return uuid5(NS_CONTENT, f"aware:content_part_file:{content_part_id}:{modality_type_norm}")


def stable_content_part_multimodal_index_id(*, content_part_id: UUID, key: str = "default") -> UUID:
    """Compiler-generated from class-attribute identity keys: content_part_id, key"""

    key_norm = (key or "").casefold().strip() or "default"
    return uuid5(NS_CONTENT, f"aware:content_part_multimodal_index:{content_part_id}:{key_norm}")


def stable_content_part_text_id(*, content_part_id: UUID, key: str = "default") -> UUID:
    """Compiler-generated from class-attribute identity keys: content_part_id, key"""

    key_norm = (key or "").casefold().strip() or "default"
    return uuid5(NS_CONTENT, f"aware:content_part_text:{content_part_id}:{key_norm}")


def stable_content_part_text_index_id(*, content_part_text_id: UUID, key: str = "default") -> UUID:
    """Compiler-generated from class-attribute identity keys: content_part_text_id, key"""

    key_norm = (key or "").casefold().strip() or "default"
    return uuid5(NS_CONTENT, f"aware:content_part_text_index:{content_part_text_id}:{key_norm}")


def stable_content_part_text_segment_id(*, content_part_text_id: UUID, key: str = "default") -> UUID:
    """Compiler-generated from class-attribute identity keys: content_part_text_id, key"""

    key_norm = (key or "").casefold().strip() or "default"
    return uuid5(NS_CONTENT, f"aware:content_part_text_segment:{content_part_text_id}:{key_norm}")


def stable_content_part_text_segment_translation_id(*, content_part_text_segment_id: UUID, language: str) -> UUID:
    """Compiler-generated from class-attribute identity keys: content_part_text_segment_id, language"""

    language_norm = (language or "").casefold().strip()
    return uuid5(
        NS_CONTENT, f"aware:content_part_text_segment_translation:{content_part_text_segment_id}:{language_norm}"
    )


def stable_content_part_text_style_id(
    *,
    content_part_text_segment_id: UUID,
    background_color: str | None = None,
    block_semantic_type: str | None = None,
    bold: bool = False,
    color: str | None = None,
    font_family: str | None = None,
    font_size: int = 0,
    italic: bool = False,
    underline: bool = False,
) -> UUID:
    """Compiler-generated from class-attribute identity keys: content_part_text_segment_id, background_color, block_semantic_type, bold, color, font_family, font_size, italic, underline"""

    background_color_norm = (background_color or "").casefold().strip()
    block_semantic_type_norm = (block_semantic_type or "").casefold().strip()
    bold_int = int(bold)
    color_norm = (color or "").casefold().strip()
    font_family_norm = (font_family or "").casefold().strip()
    italic_int = int(italic)
    underline_int = int(underline)
    return uuid5(
        NS_CONTENT,
        f"aware:content_part_text_style:{content_part_text_segment_id}:{background_color_norm}:{block_semantic_type_norm}:{bold_int}:{color_norm}:{font_family_norm}:{font_size}:{italic_int}:{underline_int}",
    )


CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID: dict[str, tuple[str, tuple[str, ...]]] = {
    "03b2e8f1-ae21-5b2d-8bcf-8e0ecc92cb58": ("stable_content_chain_content_id", ("content_chain_id", "position")),
    "0f8eded0-c183-57c5-9033-3516cfba14c5": ("stable_content_chain_id", ("key",)),
    "10b11ef0-7b72-519a-9ef2-3cafe22165f6": ("stable_content_id", ("key",)),
    "20cccfaa-af38-5821-86a7-608381982308": ("stable_content_part_file_id", ("content_part_id", "modality_type")),
    "2416f11d-10b3-5732-9021-da4722b0d912": ("stable_content_part_text_segment_id", ("content_part_text_id", "key")),
    "3d9f6e13-2569-5193-adc2-55703f6fde1d": (
        "stable_content_part_content_layout_id",
        ("content_part_content_id", "content_layout_id", "layout_order"),
    ),
    "8cd14d4b-78c4-582b-a15f-bbeaf4175500": ("stable_content_part_id", ("content_part_content_id", "type")),
    "9eb60876-520f-5eb4-a82d-310c69c393f1": (
        "stable_content_part_text_style_id",
        (
            "content_part_text_segment_id",
            "background_color",
            "block_semantic_type",
            "bold",
            "color",
            "font_family",
            "font_size",
            "italic",
            "underline",
        ),
    ),
    "b285b1b6-ca58-5dc8-ba9a-b94fdc7aa0cb": ("stable_content_part_text_index_id", ("content_part_text_id", "key")),
    "cef18a06-8871-5127-bcbb-830eb67b0396": ("stable_content_index_id", ("content_id", "key")),
    "d33cdd96-63f0-529f-86a4-09e75e0c1adc": ("stable_content_layout_id", ("content_id", "name")),
    "d34752f4-de30-5cc3-b7d0-be6a7d0f720d": ("stable_content_part_text_id", ("content_part_id", "key")),
    "e7624595-09eb-5598-a824-78f667bfb7c2": ("stable_content_part_multimodal_index_id", ("content_part_id", "key")),
    "f1acfad3-7a85-5ad9-ac2c-f0da52d2e302": ("stable_content_chain_section_id", ("content_chain_id", "key")),
    "f1bc3d6c-237f-5a2f-b040-d080010b51e0": ("stable_content_part_content_id", ("content_id", "position")),
    "fa4289ed-55f0-597f-926e-08fa512481b8": (
        "stable_content_part_text_segment_translation_id",
        ("content_part_text_segment_id", "language"),
    ),
}

__all__ = [
    "stable_content_id",
    "stable_content_chain_id",
    "stable_content_chain_content_id",
    "stable_content_chain_section_id",
    "stable_content_index_id",
    "stable_content_layout_id",
    "stable_content_part_id",
    "stable_content_part_content_id",
    "stable_content_part_content_layout_id",
    "stable_content_part_file_id",
    "stable_content_part_multimodal_index_id",
    "stable_content_part_text_id",
    "stable_content_part_text_index_id",
    "stable_content_part_text_segment_id",
    "stable_content_part_text_segment_translation_id",
    "stable_content_part_text_style_id",
    "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
]
