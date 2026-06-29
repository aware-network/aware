from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from uuid import UUID

from aware_code.builder import build_code_from_content
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.setup_language_plugins import setup_code_plugins
from aware_code.symbol_table import CodeSymbolTable
from aware_code_ontology.code.code import Code
from aware_code_ontology.package.code_package import CodePackage
from aware_code_ontology.package.code_package_code import CodePackageCode
from aware_meta.manifest.spec import AwareTomlNamespaceMappingSpec
from aware_meta.manifest.namespace_match import namespace_for_source_path
from aware_meta.fqn_resolver import NamespacePath


def build_namespace_by_code_id_for_code_package(
    *,
    repository_name: str,
    workspace_root: str,
    code_package: CodePackage,
    fqn_prefix: str,
    namespace_mappings: Sequence[AwareTomlNamespaceMappingSpec] | None = None,
) -> dict[UUID, NamespacePath]:
    _ = workspace_root
    if code_package.id is None:
        raise ValueError("CodePackage id is required for namespace discovery")

    setup_code_plugins()

    package_file_codes = sorted(
        [
            (edge.relative_path, edge.code)
            for edge in code_package.code_package_codes
            if edge.code is not None and edge.relative_path
        ],
        key=lambda item: item[0],
    )
    if not package_file_codes:
        return {}

    return _build_namespace_by_code_id_for_sources(
        repository_name=repository_name,
        code_package=code_package,
        package_file_codes=package_file_codes,
        fqn_prefix=fqn_prefix,
        namespace_mappings=tuple(namespace_mappings or ()),
    )


def build_parsed_file_codes_for_code_package_sources(
    *,
    code_package: CodePackage,
    sources_root: Path,
    code_package_codes: Sequence[CodePackageCode] | None = None,
) -> tuple[list[tuple[str, Code]], CodePackage]:
    setup_code_plugins()
    package_codes = tuple(code_package_codes or code_package.code_package_codes)
    if not package_codes:
        return [], code_package

    parsed_edges: list[CodePackageCode] = []
    file_codes: list[tuple[str, Code]] = []
    resolved_sources_root = sources_root.resolve()

    for edge in sorted(package_codes, key=lambda item: item.relative_path):
        relative_path = edge.relative_path
        if not relative_path:
            continue
        absolute_path = (resolved_sources_root / relative_path).resolve()
        if not absolute_path.is_file():
            raise RuntimeError(
                "CodePackage source parse requires an existing source file: "
                + f"package={code_package.package_name!r} relative_path={relative_path!r} "
                + f"sources_root={resolved_sources_root}"
            )
        parsed_code = build_code_from_content(
            sections_index=CodeSectionBuilderIndex(),
            content=absolute_path.read_text(encoding="utf-8"),
            code_key=relative_path,
            language=code_package.language,
            symbol_table=CodeSymbolTable(),
        )
        parsed_edges.append(
            edge.model_copy(
                update={
                    "code": parsed_code,
                }
            )
        )
        file_codes.append((relative_path, parsed_code))

    parsed_code_package = code_package.model_copy(
        update={
            "code_package_codes": parsed_edges,
        }
    )
    return file_codes, parsed_code_package


def _build_namespace_by_code_id_for_sources(
    *,
    repository_name: str,
    code_package: CodePackage,
    package_file_codes: Sequence[tuple[str, Code]],
    fqn_prefix: str,
    namespace_mappings: Sequence[AwareTomlNamespaceMappingSpec],
) -> dict[UUID, NamespacePath]:
    namespace_by_code_id: dict[UUID, NamespacePath] = {}
    for relative_path, code in package_file_codes:
        if code.id is None:
            raise ValueError(
                "Code id is required for namespace discovery: "
                + f"{repository_name}:{code_package.package_name}:{relative_path}"
            )
        namespace = namespace_for_source_path(
            source_path=relative_path,
            namespace_mappings=tuple(namespace_mappings),
        )
        namespace_by_code_id[code.id] = NamespacePath(
            package=fqn_prefix,
            namespace=namespace,
        )
    return namespace_by_code_id
