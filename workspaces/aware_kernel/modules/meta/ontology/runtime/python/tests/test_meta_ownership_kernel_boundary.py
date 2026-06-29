from __future__ import annotations

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[8]


def _join(*parts: str) -> str:
    return "".join(parts)


def test_meta_kernel_boundary_has_no_product_ownership_rail() -> None:
    repo_root = _repo_root()
    scan_roots = (
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/stable_ids.toml",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/aware",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/stable_ids.toml",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/runtime/python/aware_identity",
    )
    blocked_tokens = (
        _join("root_", "ownership", "_id"),
        _join("ownership", "_id"),
        _join("ownership", ".", "Ownership"),
        _join("Ownership", "Config"),
        _join("Role", "Config", "Ownership", "Config"),
        _join("role_config_", "ownership"),
        _join("ownership", "_owners"),
        _join("stable_", "ownership"),
        _join("stable_role_config_", "ownership"),
        _join("aware_meta", ".", "ownership"),
    )

    hits: list[str] = []
    for scan_root in scan_roots:
        candidates = (
            (scan_root,)
            if scan_root.is_file()
            else tuple(
                path
                for path in scan_root.rglob("*")
                if path.suffix in {".aware", ".py", ".toml"}
                and "/handlers/_generated/" not in path.as_posix()
            )
        )
        for path in candidates:
            text = path.read_text()
            for token in blocked_tokens:
                if token in text:
                    hits.append(f"{path.relative_to(repo_root)}: {token}")

    assert hits == []
