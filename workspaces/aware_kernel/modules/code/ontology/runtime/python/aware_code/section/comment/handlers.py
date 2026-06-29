# Kernel Graph Ontology
from aware_code_ontology.comment.code_section_comment import CodeSectionComment
from aware_code_ontology.comment.code_section_comment_enums import (
    CodeSectionCommentType,
)
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment

# Aware Content
from aware_content.builder import get_segment_text

# Aware Storage
from aware_storage.blob_store import BlobStore


def get_first_doc_comment_segment(
    comments: list[CodeSectionComment],
) -> ContentPartTextSegment | None:
    """Return the first durable text segment for a doc comment."""
    for comment in sorted(
        comments,
        key=lambda item: 0 if item.type == CodeSectionCommentType.doc else 1,
    ):
        if comment.type != CodeSectionCommentType.doc:
            continue
        contents = sorted(
            comment.code_section_comment_contents,
            key=lambda item: item.position,
        )
        for content in contents:
            return content.content_part_text_segment
    return None


def get_content(comment: CodeSectionComment, blob_store: BlobStore | None = None) -> str:
    """
    Get the content of the comment.
    """
    content_texts = [
        get_segment_text(content.content_part_text_segment, blob_store=blob_store)
        for content in comment.code_section_comment_contents
    ]

    # For single segments (like triple-quoted docstrings), return as-is
    # For multiple segments (like /// comments), join with newlines to preserve line structure
    if len(content_texts) <= 1:
        return "".join(content_texts)
    else:
        return "\n".join(content_texts)


def get_docstring(comments: list[CodeSectionComment], blob_store: BlobStore | None = None) -> str | None:
    """
    Get the docstring for the attribute.

    Prioritizes DOC type comments first, then others.
    """
    # Get all comments with content
    doc_comments: list[CodeSectionComment] = []
    for comment in comments:
        content = get_content(comment, blob_store=blob_store)
        if content and content.strip():
            doc_comments.append(comment)

    if not doc_comments:
        return None

    # Sort DOC comments first, then others
    sorted_comments = sorted(doc_comments, key=lambda c: 0 if c.type == CodeSectionCommentType.doc else 1)

    # Return the content of the first comment, stripped
    content = get_content(sorted_comments[0], blob_store=blob_store)
    return content.strip() if content else None


def get_segment(comment: CodeSectionComment, kind: object) -> ContentPartTextSegment | None:
    """
    Get a segment by its enum type.

    Args:
        kind: The segment enum value (e.g., CodeSectionAttributeSegment.NAME)

    Returns:
        The ContentPartTextSegment if found, None otherwise
    """
    # TODO: Legacy stub retained for compatibility with older callers.
    # CodeSectionComment currently stores segments as a list of content parts.
    _ = comment, kind
    return None
