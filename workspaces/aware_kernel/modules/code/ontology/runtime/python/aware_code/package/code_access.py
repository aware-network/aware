from __future__ import annotations

from aware_orm.session.current_session_ctx import current_session
from aware_orm.session.session import Session

from aware_code.stable_ids import stable_code_package_code_id
from aware_code_ontology.code.code import Code
from aware_code_ontology.package.code_package import CodePackage
from aware_code_ontology.package.code_package_code import CodePackageCode
from aware_meta.runtime.handler_context import current_handler_session


def normalize_package_relative_path(relative_path: str) -> str:
    normalized_relative_path = (relative_path or "").strip()
    if not normalized_relative_path:
        raise RuntimeError("CodePackage code path requires non-empty relative_path")
    return normalized_relative_path


def current_package_access_session() -> Session:
    try:
        return current_handler_session()
    except RuntimeError:
        session = current_session()
        if session is None:
            raise RuntimeError("CodePackage access requires an active handler session or local ORM session") from None
        return session


def find_package_code_edge(code_package: CodePackage, relative_path: str) -> CodePackageCode | None:
    normalized_relative_path = normalize_package_relative_path(relative_path)
    for existing in code_package.code_package_codes:
        if (existing.relative_path or "").strip() == normalized_relative_path:
            return existing

    edge_id = stable_code_package_code_id(
        code_package_id=code_package.id,
        relative_path=normalized_relative_path,
    )
    session = current_package_access_session()
    return session.imap_get(CodePackageCode, edge_id)


def resolve_edge_code(edge: CodePackageCode) -> Code:
    code = edge.code
    if code is None:
        raise RuntimeError(
            "CodePackageCode.code must be available on the package-owned rail: "
            f"code_package_code_id={edge.id}"
        )
    return code
