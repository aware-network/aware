"""Python-specific layout plugin that handles Python's custom domain/schema structure."""

from pathlib import Path

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_code.language.layout import CodeLanguagePluginLayout
from aware_code.language.schemas import CodeDomain, CodeSchema
from typing_extensions import override


class PythonCodeLanguagePluginLayout(CodeLanguagePluginLayout):
    """Python-specific layout plugin that handles aware_domain package structure."""

    @override
    def extract_domains_and_schemas(
        self, file_paths: list[str], language: CodeLanguage, enforce_domains_layout: bool = False
    ) -> list[CodeDomain]:
        """Extract domains/schemas using Python-specific layout patterns."""
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
        Extract domain and schema from Python repository relative path with Python-specific logic.

        Primary rule: Python-specific handling:
        • domains/<domain>/aware_<domain>/<schema>/... (new multilang layout)
        • domains/<domain>/<schema>/... (classic layout)

        Fallback rule: <domain>/<schema>/... (when no "domains" folder found and enforce_domains_layout=False)

        Returns:
            Tuple of (domain_name, domain_path, schema_name, schema_path) or None
        """
        parts = list(Path(rel_path).parts)
        original_parts = parts.copy()  # Keep original for domain_path construction

        # Strip 'python/' prefix if present
        if parts and parts[0] == language.value:
            parts = parts[1:]

        # Primary rule: Look for "domains" folder
        try:
            idx = parts.index("domains")

            # Need at least domains/<domain>/<schema>/file pattern (4 parts minimum after domains)
            if idx + 3 >= len(parts):
                return None  # Incomplete path

            domain = parts[idx + 1]
            after_domain = parts[idx + 2]

            # Calculate the actual domain_path from original parts
            # Find the domains index in original parts
            original_domains_idx = original_parts.index("domains")
            # domain_path includes everything up to and including the domain name
            domain_path_parts = original_parts[: original_domains_idx + 2]  # includes domains/<domain>
            domain_path = "/".join(domain_path_parts)

            # Check for Python package structure: domains/<domain>/aware_<domain>/<schema>/...
            if after_domain == f"aware_{domain}":
                if idx + 4 >= len(parts):  # Need at least domains/<domain>/aware_<domain>/<schema>/file
                    return None
                schema = parts[idx + 3]  # New multilang layout
                schema_path = f"aware_{domain}/{schema}"  # Include aware_* package in schema path
            else:
                schema = after_domain  # Classic layout
                schema_path = schema  # Simple schema path

            return (domain, domain_path, self._clean_schema_name(schema), schema_path)

        except ValueError:
            # Fallback rule: only if domains layout is not enforced
            if enforce_domains_layout:
                return None

            return self.extract_domain_schema_from_path_fallback(rel_path, language)

    @override
    def _clean_schema_name(self, schema_name: str) -> str:
        """Clean schema name by removing trailing underscores."""
        return schema_name.rstrip("_")
