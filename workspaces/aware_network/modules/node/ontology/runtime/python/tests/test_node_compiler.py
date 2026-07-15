from __future__ import annotations

from pathlib import Path
import sys

import pytest

_REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "aware.repo.toml").is_file()
)
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)
_NODE_RUNTIME_ROOT_STR = str(_REPO_ROOT / "modules" / "node" / "runtime")
if _NODE_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _NODE_RUNTIME_ROOT_STR)

from aware_node.compiler import load_node_ownership_from_sources  # noqa: E402


def _write_node_source(root: Path, *, relpath: str, source: str) -> Path:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(source, encoding="utf-8")
    return Path(relpath)


def test_load_node_ownership_from_sources_parses_node_definition(
    tmp_path: Path,
) -> None:
    relpath = _write_node_source(
        tmp_path,
        relpath="nodes/kernel_node.aware",
        source="""\
node kernel_host {
    include aware.local_agent_kernel;
    environment home-story {
        profile os.default package aware-workspace-environment-profile
    }
    ontology storage-ontology;
    service aware_attention;
    interface aware_workspace;
}
""",
    )

    ownership = load_node_ownership_from_sources(
        package_root=tmp_path,
        source_files=(relpath,),
    )

    assert ownership.name == "kernel_host"
    assert tuple(
        item.included_package_name for item in ownership.included_node_packages
    ) == ("aware.local_agent_kernel",)
    assert tuple(item.include_key for item in ownership.included_node_packages) == (
        "aware.local_agent_kernel",
    )
    assert tuple(item.environment_handle for item in ownership.environment_targets) == (
        "home-story",
    )
    assert tuple(
        (
            mount.package_name,
            mount.profile_key,
            mount.mount_key,
            mount.mode,
            mount.position,
        )
        for item in ownership.environment_targets
        for mount in item.profile_mounts
    ) == (
        (
            "aware-workspace-environment-profile",
            "os.default",
            "aware-workspace-environment-profile:os.default",
            "mounted",
            0,
        ),
    )
    assert tuple(item.service_name for item in ownership.service_targets) == (
        "aware_attention",
    )
    assert ownership.service_targets[0].code_packages == ()
    assert tuple(item.package_name for item in ownership.ontology_targets) == (
        "storage-ontology",
    )
    assert tuple(item.interface_name for item in ownership.interface_targets) == (
        "aware_workspace",
    )


def test_load_node_ownership_from_sources_parses_service_code_package_activation(
    tmp_path: Path,
) -> None:
    relpath = _write_node_source(
        tmp_path,
        relpath="nodes/kernel_node.aware",
        source="""\
node kernel_services_host {
    service aware_experience {
        package experience aware-workspace-experience;
    }
}
""",
    )

    ownership = load_node_ownership_from_sources(
        package_root=tmp_path,
        source_files=(relpath,),
    )

    assert tuple(item.service_name for item in ownership.service_targets) == (
        "aware_experience",
    )
    service_target = ownership.service_targets[0]
    assert tuple(
        (item.slot_key, item.package_name, item.language, item.source_path)
        for item in service_target.code_packages
    ) == (
        (
            "experience",
            "aware-workspace-experience",
            "aware",
            "nodes/kernel_node.aware",
        ),
    )


def test_load_node_ownership_from_sources_parses_multiple_environment_profile_mounts(
    tmp_path: Path,
) -> None:
    relpath = _write_node_source(
        tmp_path,
        relpath="nodes/kernel_node.aware",
        source="""\
node kernel_host {
    environment control {
        profile os.default package aware-control-environment-profile
        profile env.peer.v1 package aware-network-environment-profile
    }
}
""",
    )

    ownership = load_node_ownership_from_sources(
        package_root=tmp_path,
        source_files=(relpath,),
    )

    assert tuple(item.environment_handle for item in ownership.environment_targets) == (
        "control",
    )
    target = ownership.environment_targets[0]
    assert tuple(
        (
            mount.package_name,
            mount.profile_key,
            mount.mount_key,
            mount.mode,
            mount.position,
        )
        for mount in target.profile_mounts
    ) == (
        (
            "aware-control-environment-profile",
            "os.default",
            "aware-control-environment-profile:os.default",
            "mounted",
            0,
        ),
        (
            "aware-network-environment-profile",
            "env.peer.v1",
            "aware-network-environment-profile:env.peer.v1",
            "mounted",
            1,
        ),
    )


def test_load_node_ownership_from_sources_allows_clean_environment_target(
    tmp_path: Path,
) -> None:
    relpath = _write_node_source(
        tmp_path,
        relpath="nodes/kernel_node.aware",
        source="""\
node kernel_host {
    environment control {
    }
}
""",
    )

    ownership = load_node_ownership_from_sources(
        package_root=tmp_path,
        source_files=(relpath,),
    )

    assert tuple(item.environment_handle for item in ownership.environment_targets) == (
        "control",
    )
    target = ownership.environment_targets[0]
    assert target.profile_mounts == ()


def test_load_node_ownership_from_sources_rejects_duplicate_includes(
    tmp_path: Path,
) -> None:
    relpath = _write_node_source(
        tmp_path,
        relpath="nodes/kernel_node.aware",
        source="""\
node kernel_host {
    include aware.local_agent_kernel;
    include aware.local_agent_kernel;
}
""",
    )

    with pytest.raises(ValueError, match="duplicates included Node package"):
        _ = load_node_ownership_from_sources(
            package_root=tmp_path,
            source_files=(relpath,),
        )


def test_load_node_ownership_from_sources_rejects_duplicate_targets(
    tmp_path: Path,
) -> None:
    relpath = _write_node_source(
        tmp_path,
        relpath="nodes/kernel_node.aware",
        source="""\
node kernel_host {
    environment kernel {
        profile os.default package aware-workspace-environment-profile
    }
    environment kernel {
        profile os.default package aware-workspace-environment-profile
    }
}
""",
    )

    with pytest.raises(ValueError, match="duplicates environment target"):
        _ = load_node_ownership_from_sources(
            package_root=tmp_path,
            source_files=(relpath,),
        )


def test_load_node_ownership_from_sources_rejects_duplicate_ontology_targets(
    tmp_path: Path,
) -> None:
    relpath = _write_node_source(
        tmp_path,
        relpath="nodes/kernel_node.aware",
        source="""\
node kernel_host {
    ontology storage-ontology;
    ontology storage-ontology;
}
""",
    )

    with pytest.raises(ValueError, match="duplicates ontology target"):
        _ = load_node_ownership_from_sources(
            package_root=tmp_path,
            source_files=(relpath,),
        )


def test_load_node_ownership_from_sources_rejects_multiple_nodes(
    tmp_path: Path,
) -> None:
    first = _write_node_source(
        tmp_path,
        relpath="nodes/kernel_node.aware",
        source="""\
node kernel_host {
    environment kernel {
        profile os.default package aware-workspace-environment-profile
    }
}
""",
    )
    second = _write_node_source(
        tmp_path,
        relpath="nodes/interface_node.aware",
        source="""\
node interface_host {
    interface aware_workspace;
}
""",
    )

    with pytest.raises(ValueError, match="exactly one node"):
        _ = load_node_ownership_from_sources(
            package_root=tmp_path,
            source_files=(first, second),
        )
