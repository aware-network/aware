from aware_content_ontology.part.content_part_text import ContentPartText
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_storage_ontology.bucket.storage_bucket import StorageBucket

from aware_storage.blob_handlers import lazy_text, create_blob_from_content
from aware_storage.blob_store import BlobStore


def get_segment_text(
    content_part_text_segment: ContentPartTextSegment,
    blob_store: BlobStore | None = None,
) -> str:
    """Get the text of the content part text segment."""
    return get_segment_bytes(content_part_text_segment, blob_store=blob_store).decode("utf-8")


def get_segment_bytes(
    content_part_text_segment: ContentPartTextSegment,
    blob_store: BlobStore | None = None,
) -> bytes:
    """
    Get the source of the content part text segment.
    """
    content_part_text = content_part_text_segment.content_part_text
    text = get_text(content_part_text, blob_store=blob_store)
    text_bytes = text.encode("utf-8")
    # Get the specific byte range from source_bytes
    return text_bytes[content_part_text_segment.byte_start : content_part_text_segment.byte_end]


def get_text(content_part_text: ContentPartText, blob_store: BlobStore | None = None) -> str:
    """Get the text of the content part text."""
    if content_part_text.inline_text is not None:
        return content_part_text.inline_text
    if content_part_text.blob:
        if not blob_store:
            raise ValueError("Blob store is required to get text from blob")
        # Force immediate loading by converting LazyBlobContent to string
        lazy_content = lazy_text(content_part_text.blob, blob_store=blob_store)
        return str(lazy_content)  # This triggers _ensure_loaded()
    return ""


def build_content_part_text_inline(
    inline_text: str,
) -> ContentPartText:
    """Build a content part text from an inline text."""
    return ContentPartText(inline_text=inline_text)


def build_content_part_text_blob(content: bytes | str, bucket: StorageBucket, blob_store: BlobStore) -> ContentPartText:
    """Build a content part text from a blob."""
    blob = create_blob_from_content(content=content, bucket=bucket, blob_store=blob_store)
    return ContentPartText(blob=blob, blob_id=blob.id)
