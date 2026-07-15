from __future__ import annotations

from aware_code_ontology.package.code_package_code import CodePackageCode
from aware_orm.session.change_collector import current_change_collector


def delete_package_code_edge_instance(code_package_code: CodePackageCode) -> None:
    collector = current_change_collector()
    if collector is None:
        raise RuntimeError("CodePackageCode deletion requires an active runtime change collector")

    collector.record_delete(code_package_code)
    if code_package_code.bound_session is not None:
        code_package_code.bound_session.imap_remove(type(code_package_code), code_package_code.id)
