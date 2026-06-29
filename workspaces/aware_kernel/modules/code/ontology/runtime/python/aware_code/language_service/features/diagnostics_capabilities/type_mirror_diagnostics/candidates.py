from __future__ import annotations

from aware_workspace.compiler.workspace import WorkspaceSnapshot


def build_quickfix_candidates(
    *,
    snapshot: WorkspaceSnapshot | None,
    common_primitive_tokens: tuple[str, ...],
) -> list[str]:
    candidates: set[str] = set(common_primitive_tokens)
    if snapshot is None:
        return sorted(candidates)

    for fqn in snapshot.fqn_resolver.classes_by_fqn.keys():
        candidates.add(fqn)
        parts = [part for part in fqn.split(".") if part]
        if len(parts) == 4:
            candidates.add(parts[3])
            candidates.add(f"{parts[2]}.{parts[3]}")

    for fqn in snapshot.fqn_resolver.enums_by_fqn.keys():
        candidates.add(fqn)
        parts = [part for part in fqn.split(".") if part]
        if len(parts) == 4:
            candidates.add(parts[3])
            candidates.add(f"{parts[2]}.{parts[3]}")

    return sorted(candidates)
