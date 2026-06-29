from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.expression.code_section_expression_enums import CodeSectionExpressionType
from aware_code_ontology.expression.code_section_expression import CodeSectionExpression

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_code_section(code_section_id: UUID, type: CodeSectionExpressionType) -> CodeSectionExpression:
    """
    Build the expression payload under a CodeSection.
    """

    # --- AWARE: LOGIC START build_via_code_section
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_code_section
