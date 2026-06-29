from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Content Ontology
from aware_content_ontology.part.content_part_text_style import ContentPartTextStyle

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
import json

from uuid import NAMESPACE_URL, uuid5

from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_orm.session.change_collector import current_change_collector

# --- AWARE: USER_IMPORTS END


async def create_or_get_style(
    font_family: str | None = None,
    font_size: int | None = None,
    bold: bool | None = False,
    italic: bool | None = False,
    underline: bool | None = False,
    color: str | None = None,
    background_color: str | None = None,
    block_semantic_type: str | None = None,
) -> ContentPartTextStyle:
    """
    Creates or retrieves a text style.
    Parameters: font_family: The font family.
    font_size: The font size.
    bold: Whether the text is bold.
    italic: Whether the text is italic.
    underline: Whether the text is underlined.
    color: The text color.
    background_color: The background color.
    block_semantic_type: Optional block semantic type tag (e.g. header/list/task/table).
    """

    # --- AWARE: LOGIC START create_or_get_style
    # Canonical v1:
    # - Styles are content-addressed (stable id derived from the style tuple).
    # - No DB reads in write mode: reuse identity-map when present; otherwise create.

    bold_v = bool(bold) if bold is not None else False
    italic_v = bool(italic) if italic is not None else False
    underline_v = bool(underline) if underline is not None else False

    spec = {
        "background_color": background_color,
        "block_semantic_type": block_semantic_type,
        "bold": bold_v,
        "color": color,
        "font_family": font_family,
        "font_size": font_size,
        "italic": italic_v,
        "underline": underline_v,
    }
    spec_key = json.dumps(
        spec,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    style_id = uuid5(NAMESPACE_URL, f"aware:content:text-style:v1:{spec_key}")

    existing = ContentPartTextStyle.get_by_id_sync(style_id)
    if existing is None:
        return ContentPartTextStyle(
            id=style_id,
            background_color=background_color,
            block_semantic_type=block_semantic_type,
            bold=bold_v,
            color=color,
            font_family=font_family,
            font_size=font_size,
            italic=italic_v,
            underline=underline_v,
        )

    if existing.background_color != background_color:
        existing.background_color = background_color
    if existing.block_semantic_type != block_semantic_type:
        existing.block_semantic_type = block_semantic_type
    if bool(existing.bold) != bold_v:
        existing.bold = bold_v
    if existing.color != color:
        existing.color = color
    if existing.font_family != font_family:
        existing.font_family = font_family
    if existing.font_size != font_size:
        existing.font_size = font_size
    if bool(existing.italic) != italic_v:
        existing.italic = italic_v
    if bool(existing.underline) != underline_v:
        existing.underline = underline_v

    return existing
    # --- AWARE: LOGIC END create_or_get_style


async def delete_if_unreferenced(content_part_text_style: ContentPartTextStyle) -> None:
    """
    Deletes this text style when no text segment in the current lane references it.
    """

    # --- AWARE: LOGIC START delete_if_unreferenced
    style_id = content_part_text_style.id
    bound_session = content_part_text_style.bound_session
    if bound_session is None:
        raise RuntimeError(
            "ContentPartTextStyle.delete_if_unreferenced requires a bound session"
        )

    for obj in bound_session.imap_all_objects():
        if not isinstance(obj, ContentPartTextSegment):
            continue
        if getattr(obj, "style_id", None) == style_id:
            return
        linked_style = getattr(obj, "style", None)
        if getattr(linked_style, "id", None) == style_id:
            return

    collector = current_change_collector()
    if collector is None:
        raise RuntimeError(
            "ContentPartTextStyle.delete_if_unreferenced requires an active runtime change collector"
        )

    collector.record_delete(content_part_text_style)
    bound_session.imap_remove(type(content_part_text_style), style_id)
    # --- AWARE: LOGIC END delete_if_unreferenced
