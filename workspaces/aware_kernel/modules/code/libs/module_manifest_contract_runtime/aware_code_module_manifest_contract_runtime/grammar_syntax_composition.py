"""Direct compatibility reexports; the frozen composition home owns the join."""

from .grammar_profile_composition import (
    produce_grammar_source_binding,
    validate_grammar_source_binding_result,
)

__all__ = ["produce_grammar_source_binding", "validate_grammar_source_binding_result"]
