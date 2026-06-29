from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Code Ontology
from aware_code_ontology.code.code_test_framework import CodeTestFramework

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.stable_ids import stable_code_test_framework_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build(name: str, title: str | None = None) -> CodeTestFramework:
    """
    Create deterministic test framework identity by canonical framework name.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("CodeTestFramework.build requires non-empty name")

    normalized_title = (title or "").strip() or None
    framework_id = stable_code_test_framework_id(name=normalized_name)
    session = current_handler_session()
    existing = session.imap_get(CodeTestFramework, framework_id)
    if existing is not None:
        if (existing.name or "").strip() != normalized_name:
            raise RuntimeError(
                "CodeTestFramework.build payload mismatch for existing framework: "
                + f"code_test_framework_id={framework_id}"
            )
        existing.title = normalized_title
        return existing

    return CodeTestFramework(
        id=framework_id,
        name=normalized_name,
        title=normalized_title,
    )
    # --- AWARE: LOGIC END build
