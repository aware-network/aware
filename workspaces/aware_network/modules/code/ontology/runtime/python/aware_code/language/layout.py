"""Layout interface for code language plugins to extract namespace groups from file paths.

This module provides the interface and default implementation for extracting
namespace group information from file paths at the primitive level. Language-specific
plugins can override this behavior.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import override

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_code.language.contracts import CodeNamespaceEntry, CodeNamespaceGroup


NAMESPACE_LAYOUT_ROOT_SEGMENT = "namespaces"


def find_namespace_layout_root(parts: Sequence[str]) -> tuple[int, str] | None:
    try:
        return (
            parts.index(NAMESPACE_LAYOUT_ROOT_SEGMENT),
            NAMESPACE_LAYOUT_ROOT_SEGMENT,
        )
    except ValueError:
        return None


class CodeLanguagePluginLayout(ABC):
    """Abstract interface for namespace group extraction from file paths."""

    @abstractmethod
    def extract_namespace_groups(
        self,
        file_paths: list[str],
        language: CodeLanguage,
        enforce_namespace_layout: bool = False,
    ) -> list[CodeNamespaceGroup]:
        """
        Extract namespace groups from file paths.

        Args:
            file_paths: List of relative file paths from repository root
            language: Language being processed
            enforce_namespace_layout: If True, only allow the strict namespace layout

        Returns:
            List of CodeNamespaceGroup objects with their associated entries
        """
        pass

    def extract_namespace_group_from_path_fallback(
        self, rel_path: str, language: CodeLanguage
    ) -> tuple[str, str, str, str] | None:
        """
        Shared fallback method to extract namespace group info when strict layout is not enforced.

        Returns:
            Tuple of (group_name, group_path, entry_name, entry_path) or None
        """
        parts = list(Path(rel_path).parts)
        original_parts = parts.copy()

        # Initial condition: iterate over parts and find language, then crop all parts to start right after language
        language_found = False
        for i, part in enumerate(parts):
            if part == language.value:
                parts = parts[i + 1 :]
                language_found = True
                break

        # Handle permissive cases
        if len(parts) >= 3:
            group = parts[0]
            entry = parts[1]
            group_path = original_parts[0] if len(original_parts) > 0 else ""
            entry_path = original_parts[1] if len(original_parts) > 1 else ""
        elif len(parts) == 2:
            group = "default"
            entry = parts[0]
            group_path = ""
            entry_path = original_parts[0] if len(original_parts) > 0 else ""
        elif len(parts) == 1:
            group = "default"
            entry = "default"
            if language_found:
                # Language was stripped
                group_path = ""
                entry_path = original_parts[0] if len(original_parts) > 0 else ""
            else:
                group_path = ""
                entry_path = ""
        else:
            return None

        return (group, group_path, self._clean_namespace_entry_name(entry), entry_path)

    def _clean_namespace_entry_name(self, entry_name: str) -> str:
        """Clean namespace entry name by removing trailing underscores."""
        return entry_name.rstrip("_")


class DefaultCodeLanguagePluginLayout(CodeLanguagePluginLayout):
    """Default implementation of namespace group extraction using standard aware layout."""

    @override
    def extract_namespace_groups(
        self,
        file_paths: list[str],
        language: CodeLanguage,
        enforce_namespace_layout: bool = False,
    ) -> list[CodeNamespaceGroup]:
        """Extract namespace groups using default aware layout patterns."""
        groups_map: dict[str, dict[str, set[str]]] = {}
        group_paths_map: dict[str, str] = {}

        # Process all files and group by namespace.
        for file_path in file_paths:
            namespace_info = self._extract_namespace_group_from_path(
                file_path, language, enforce_namespace_layout
            )
            if not namespace_info:
                continue

            group_name, group_path, entry_name, entry_path = namespace_info

            group_paths_map[group_name] = group_path

            if group_name not in groups_map:
                groups_map[group_name] = {}

            if entry_name not in groups_map[group_name]:
                groups_map[group_name][entry_name] = set()

            groups_map[group_name][entry_name].add(entry_path)

        result: list[CodeNamespaceGroup] = []
        for group_name, entries_map in groups_map.items():
            group_path = group_paths_map[group_name]

            entries: list[CodeNamespaceEntry] = []
            for entry_name, entry_paths in entries_map.items():
                entry_path = next(iter(entry_paths))
                entries.append(CodeNamespaceEntry(name=entry_name, path=entry_path))

            result.append(
                CodeNamespaceGroup(name=group_name, path=group_path, entries=entries)
            )

        return result

    def _extract_namespace_group_from_path(
        self, rel_path: str, language: CodeLanguage, enforce_namespace_layout: bool
    ) -> tuple[str, str, str, str] | None:
        """
        Extract namespace group info from a single file path.

        Returns:
            Tuple of (group_name, group_path, entry_name, entry_path) or None
        """
        parts = list(Path(rel_path).parts)
        original_parts = parts.copy()

        # Strip language prefix if present
        if parts and parts[0] == language.value:
            parts = parts[1:]

        root = find_namespace_layout_root(parts)
        if root is None:
            if enforce_namespace_layout:
                return None

            return self.extract_namespace_group_from_path_fallback(rel_path, language)

        idx, root_segment = root

        # Need at least root/<group>/<entry>/file pattern.
        if idx + 3 >= len(parts):
            return None

        group = parts[idx + 1]
        entry = parts[idx + 2]

        original_root_idx = original_parts.index(root_segment)
        group_path_parts = original_parts[: original_root_idx + 2]
        group_path = "/".join(group_path_parts)

        return (group, group_path, self._clean_namespace_entry_name(entry), entry)
