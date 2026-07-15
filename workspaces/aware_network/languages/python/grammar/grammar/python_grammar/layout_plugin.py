"""Python-specific layout plugin that handles Python's custom namespace structure."""

from pathlib import Path

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_code.language.layout import (
    CodeLanguagePluginLayout,
    find_namespace_layout_root,
)
from aware_code.language.contracts import CodeNamespaceEntry, CodeNamespaceGroup
from typing_extensions import override


class PythonCodeLanguagePluginLayout(CodeLanguagePluginLayout):
    """Python-specific layout plugin that handles aware_* package structure."""

    @override
    def extract_namespace_groups(
        self,
        file_paths: list[str],
        language: CodeLanguage,
        enforce_namespace_layout: bool = False,
    ) -> list[CodeNamespaceGroup]:
        """Extract namespace groups using Python-specific layout patterns."""
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
        Extract grouped namespace info from Python repository relative path with Python-specific logic.

        Primary rule: Python-specific handling:
        - root/<group>/aware_<group>/<entry>/... (new multilang layout)
        - root/<group>/<entry>/... (classic layout)

        Fallback rule: <group>/<entry>/... when no root folder is found and strict layout is disabled.

        Returns:
            Tuple of (group_name, group_path, entry_name, entry_path) or None
        """
        parts = list(Path(rel_path).parts)
        original_parts = parts.copy()

        # Strip 'python/' prefix if present
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
            return None  # Incomplete path

        group = parts[idx + 1]
        after_group = parts[idx + 2]

        original_root_idx = original_parts.index(root_segment)
        group_path_parts = original_parts[: original_root_idx + 2]
        group_path = "/".join(group_path_parts)

        if after_group == f"aware_{group}":
            if idx + 4 >= len(parts):
                return None
            entry = parts[idx + 3]
            entry_path = f"aware_{group}/{entry}"
        else:
            entry = after_group
            entry_path = entry

        return (
            group,
            group_path,
            self._clean_namespace_entry_name(entry),
            entry_path,
        )

    @override
    def _clean_namespace_entry_name(self, entry_name: str) -> str:
        """Clean namespace entry name by removing trailing underscores."""
        return entry_name.rstrip("_")
