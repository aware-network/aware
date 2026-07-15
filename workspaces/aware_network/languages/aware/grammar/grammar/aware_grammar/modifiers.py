"""Typed definitions for Aware language modifiers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TypeModifier:
    """Type-level modifiers (topology only)."""

    # Inline-value types are serialized as inline payloads (not graph refs).
    inline_value: bool = False

    def merge_with(self, other: "TypeModifier") -> None:
        """Merge another TypeModifier into this one."""
        self.inline_value = self.inline_value or other.inline_value

    @classmethod
    def from_strings(cls, modifiers: list[str]) -> "TypeModifier":
        """Create a TypeModifier from string modifiers."""
        result = cls()

        for mod_str in modifiers:
            if mod_str == "inline_value":
                result.inline_value = True
            elif mod_str:
                raise ValueError(f"Unknown type modifier: {mod_str}")

        return result
