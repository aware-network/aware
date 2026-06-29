"""Layout interface for code language plugins to extract domains and schemas from file paths.

This module provides the interface and default implementation for extracting domain/schema
information from file paths at the primitive level, without importing structure domain.
Language-specific plugins can override this behavior.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import override

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_code.language.schemas import CodeDomain, CodeSchema


class CodeLanguagePluginLayout(ABC):
    """Abstract interface for domain/schema extraction from file paths."""

    @abstractmethod
    def extract_domains_and_schemas(
        self,
        file_paths: list[str],
        language: CodeLanguage,
        enforce_domains_layout: bool = False,
    ) -> list[CodeDomain]:
        """
        Extract domains and schemas from file paths.

        Args:
            file_paths: List of relative file paths from repository root
            language: Language being processed
            enforce_domains_layout: If True, only allow strict domains structure

        Returns:
            List of CodeDomain objects with their associated schemas
        """
        pass

    def extract_domain_schema_from_path_fallback(
        self, rel_path: str, language: CodeLanguage
    ) -> tuple[str, str, str, str] | None:
        """
        Shared fallback method to extract domain/schema info when domains layout is not enforced.

        Returns:
            Tuple of (domain_name, domain_path, schema_name, schema_path) or None
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
            domain = parts[0]
            schema = parts[1]
            domain_path = original_parts[0] if len(original_parts) > 0 else ""
            schema_path = original_parts[1] if len(original_parts) > 1 else ""
        elif len(parts) == 2:
            domain = "default"
            schema = parts[0]
            domain_path = ""
            schema_path = original_parts[0] if len(original_parts) > 0 else ""
        elif len(parts) == 1:
            domain = "default"
            schema = "default"
            if language_found:
                # Language was stripped
                domain_path = ""
                schema_path = original_parts[0] if len(original_parts) > 0 else ""
            else:
                domain_path = ""
                schema_path = ""
        else:
            return None

        return (domain, domain_path, self._clean_schema_name(schema), schema_path)

    def _clean_schema_name(self, schema_name: str) -> str:
        """Clean schema name by removing trailing underscores."""
        return schema_name.rstrip("_")


class DefaultCodeLanguagePluginLayout(CodeLanguagePluginLayout):
    """Default implementation of domain/schema extraction using standard aware layout."""

    @override
    def extract_domains_and_schemas(
        self,
        file_paths: list[str],
        language: CodeLanguage,
        enforce_domains_layout: bool = False,
    ) -> list[CodeDomain]:
        """Extract domains/schemas using default aware layout patterns."""
        domains_map: dict[str, dict[str, set[str]]] = {}  # domain_name -> {schema_name -> {schema_paths}}
        domain_paths_map: dict[str, str] = {}  # domain_name -> domain_path

        # Process all files and group by domain/schema
        for file_path in file_paths:
            domain_schema_info = self._extract_domain_schema_from_path(file_path, language, enforce_domains_layout)
            if not domain_schema_info:
                continue

            domain_name, domain_path, schema_name, schema_path = domain_schema_info

            # Track domain path
            domain_paths_map[domain_name] = domain_path

            # Group schemas within domain
            if domain_name not in domains_map:
                domains_map[domain_name] = {}

            if schema_name not in domains_map[domain_name]:
                domains_map[domain_name][schema_name] = set()

            domains_map[domain_name][schema_name].add(schema_path)

        # Convert to CodeDomain objects
        result: list[CodeDomain] = []
        for domain_name, schemas_map in domains_map.items():
            domain_path = domain_paths_map[domain_name]

            schemas: list[CodeSchema] = []
            for schema_name, schema_paths in schemas_map.items():
                # Use the first schema path (they should all be the same for a given schema)
                schema_path = next(iter(schema_paths))
                schemas.append(CodeSchema(name=schema_name, path=schema_path))

            result.append(CodeDomain(name=domain_name, path=domain_path, schemas=schemas))

        return result

    def _extract_domain_schema_from_path(
        self, rel_path: str, language: CodeLanguage, enforce_domains_layout: bool
    ) -> tuple[str, str, str, str] | None:
        """
        Extract domain/schema info from a single file path.

        Returns:
            Tuple of (domain_name, domain_path, schema_name, schema_path) or None
        """
        parts = list(Path(rel_path).parts)
        original_parts = parts.copy()

        # Strip language prefix if present
        if parts and parts[0] == language.value:
            parts = parts[1:]

        # Primary rule: Look for "domains" folder
        try:
            idx = parts.index("domains")

            # Need at least domains/<domain>/<schema>/file pattern
            if idx + 3 >= len(parts):
                return None

            domain = parts[idx + 1]
            schema = parts[idx + 2]

            # Calculate actual paths
            original_domains_idx = original_parts.index("domains")
            domain_path_parts = original_parts[: original_domains_idx + 2]
            domain_path = "/".join(domain_path_parts)

            return (domain, domain_path, self._clean_schema_name(schema), schema)

        except ValueError:
            # Fallback rule: only if domains layout is not enforced
            if enforce_domains_layout:
                return None

            return self.extract_domain_schema_from_path_fallback(rel_path, language)
