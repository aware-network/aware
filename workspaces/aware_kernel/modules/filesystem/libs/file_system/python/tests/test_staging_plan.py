"""Detached plan validation is not worker or backend qualification."""

import hashlib
import json
from dataclasses import FrozenInstanceError, replace

import pytest
from aware_file_system.staging_plan import (
    StagingDirectory,
    StagingFile,
    StagingPlan,
    StagingPlanLimits,
    validate_staging_plan,
)


def digest(content=b"x"):
    return "sha256:" + hashlib.sha256(content).hexdigest()


def limits(**changes):
    return replace(StagingPlanLimits(100, 1024, 4096, 1024, 8, 8192), **changes)


def file(path="dir/file", **changes):
    return replace(StagingFile(path, 0o644, 1, digest()), **changes)


def plan(*members, bound=None):
    return StagingPlan(bound or limits(), members)


def test_nested_plan_exact_encoding_and_digest():
    source = plan(StagingDirectory("dir", 0o700), file())
    result = validate_staging_plan(source)
    encoded = json.dumps(
        [
            "aware.filesystem.staging-plan.v1",
            [100, 1024, 4096, 1024, 8, 8192],
            [["directory", "dir", 448], ["file", "dir/file", 420, 1, digest()]],
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode()
    assert result.plan_digest == digest(encoded)
    assert result.member_count == 2
    assert result.total_file_bytes == 1
    assert result.encoded_bytes == len(encoded)
    assert validate_staging_plan(source) == result


def test_plan_is_detached_and_frozen():
    source = plan(file("leaf"))
    assert validate_staging_plan(replace(source)) == validate_staging_plan(source)
    with pytest.raises(FrozenInstanceError):
        source.members = ()
    with pytest.raises(FrozenInstanceError):
        source.members[0].mode = 0o755


@pytest.mark.parametrize(
    "field",
    [
        "member_count",
        "file_bytes",
        "total_file_bytes",
        "path_bytes",
        "path_components",
        "encoded_bytes",
    ],
)
@pytest.mark.parametrize("value", [True, False, 0, -1, 1.5, "1", 2**64])
def test_invalid_limits(field, value):
    with pytest.raises(ValueError, match="invalid_staging_limit"):
        validate_staging_plan(plan(bound=limits(**{field: value})))


@pytest.mark.parametrize(
    "path",
    [
        "",
        ".",
        "..",
        "../x",
        "/x",
        "a//b",
        "a/./b",
        "a/../b",
        "a/",
        "a\\b",
        "a\x00b",
        "a\nb",
        "e\u0301",
        "\ud800",
    ],
)
def test_noncanonical_paths(path):
    with pytest.raises((ValueError, UnicodeError)):
        validate_staging_plan(plan(file(path)))


def test_unicode_byte_limit_and_depth():
    with pytest.raises(ValueError):
        validate_staging_plan(plan(file("éé"), bound=limits(path_bytes=3)))
    validate_staging_plan(plan(file("éé"), bound=limits(path_bytes=4)))
    with pytest.raises(ValueError, match="staging_path_depth_limit"):
        validate_staging_plan(
            plan(
                StagingDirectory("d", 0o700),
                file("d/x"),
                bound=limits(path_components=1),
            )
        )


@pytest.mark.parametrize(
    "members",
    [
        (file(),),
        (file("parent"), file("parent/child")),
        (file(), StagingDirectory("dir", 0o700)),
        (StagingDirectory("dir", 0o700), file("dir")),
        (file("leaf"), file("leaf")),
        (StagingDirectory("dir", 0o700), StagingDirectory("dir", 0o700)),
    ],
)
def test_parent_and_collision_refusals(members):
    with pytest.raises(ValueError):
        validate_staging_plan(plan(*members))


@pytest.mark.parametrize("mode", [True, 0, 0o777, 0o4755, 0o1755, "644"])
@pytest.mark.parametrize("directory", [True, False])
def test_unsupported_modes(mode, directory):
    member = StagingDirectory("d", mode) if directory else file("f", mode=mode)
    with pytest.raises(ValueError, match="staging_mode_unsupported"):
        validate_staging_plan(plan(member))


@pytest.mark.parametrize("mode", [0o444, 0o555])
def test_verified_artifact_final_mode_is_preserved_and_digest_bound(mode):
    # Original public archive verifier admits these final regular-file modes.
    # They are not temporary write modes and must not be rewritten to 0644/0755.
    member = file("artifact", mode=mode)
    source = plan(member)
    result = validate_staging_plan(source)
    encoded = json.dumps(
        [
            "aware.filesystem.staging-plan.v1",
            [100, 1024, 4096, 1024, 8, 8192],
            [["file", "artifact", mode, 1, digest()]],
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode()
    assert source.members[0].mode == mode
    assert result.plan_digest == digest(encoded)
    rewritten = plan(replace(member, mode=mode | 0o200))
    assert validate_staging_plan(rewritten).plan_digest != result.plan_digest


@pytest.mark.parametrize("mode", [0o444, 0o555])
def test_readonly_artifact_modes_do_not_expand_directory_admission(mode):
    with pytest.raises(ValueError, match="staging_mode_unsupported"):
        validate_staging_plan(plan(StagingDirectory("dir", mode)))


@pytest.mark.parametrize("value", [True, -1, 1025, "1", 1.0])
def test_file_length(value):
    with pytest.raises(ValueError, match="staging_file_limit"):
        validate_staging_plan(plan(file("f", size_bytes=value)))


@pytest.mark.parametrize(
    "value",
    [
        "SHA256:" + "a" * 64,
        "sha256:" + "A" * 64,
        "sha256:" + "z" * 64,
        "sha256:" + "a" * 63,
        None,
    ],
)
def test_bad_digest(value):
    with pytest.raises(ValueError, match="staging_digest_invalid"):
        validate_staging_plan(plan(file("f", content_digest=value)))


def test_empty_file_digest():
    with pytest.raises(ValueError, match="staging_empty_digest_mismatch"):
        validate_staging_plan(plan(file("f", size_bytes=0)))
    validate_staging_plan(plan(file("f", size_bytes=0, content_digest=digest(b""))))


def test_aggregate_and_exact_boundaries():
    source = plan(
        file("a"), file("b"), bound=limits(member_count=2, total_file_bytes=2)
    )
    result = validate_staging_plan(source)
    assert result.total_file_bytes == 2
    with pytest.raises(ValueError, match="staging_member_limit"):
        validate_staging_plan(replace(source, limits=limits(member_count=1)))
    with pytest.raises(ValueError, match="staging_total_file_limit"):
        validate_staging_plan(replace(source, limits=limits(total_file_bytes=1)))
    bounded = replace(
        source, limits=replace(source.limits, encoded_bytes=result.encoded_bytes)
    )
    # Changing a limit changes its encoded width; find the exact new boundary.
    new_size = validate_staging_plan(bounded).encoded_bytes
    bounded = replace(bounded, limits=replace(bounded.limits, encoded_bytes=new_size))
    assert validate_staging_plan(bounded).encoded_bytes == new_size
    with pytest.raises(ValueError, match="staging_metadata_limit"):
        validate_staging_plan(
            replace(bounded, limits=replace(bounded.limits, encoded_bytes=new_size - 1))
        )


def test_metadata_path_budget_precedes_encoding(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("encoding oversized paths")

    monkeypatch.setattr("aware_file_system.staging_plan.json.dumps", forbidden)
    with pytest.raises(ValueError, match="staging_metadata_limit"):
        validate_staging_plan(plan(file("long-name"), bound=limits(encoded_bytes=8)))


def test_digest_binds_order_modes_content_and_limits():
    source = plan(file("a"), file("b"))
    original = validate_staging_plan(source).plan_digest
    alternatives = (
        replace(source, members=source.members[::-1]),
        plan(file("a", mode=0o755), file("b")),
        plan(file("a", content_digest=digest(b"y")), file("b")),
        replace(source, limits=limits(file_bytes=100)),
    )
    assert all(
        validate_staging_plan(other).plan_digest != original for other in alternatives
    )


def test_exact_types_required():
    class ForeignFile(StagingFile):
        pass

    invalid = (
        {},
        StagingPlan({}, ()),
        StagingPlan(limits(), []),
        plan(ForeignFile("f", 0o644, 1, digest())),
        plan(file(123)),
    )
    for value in invalid:
        with pytest.raises(TypeError):
            validate_staging_plan(value)


def test_revalidates_constructed_values():
    source = plan(file("f"))
    object.__setattr__(source.members[0], "size_bytes", -1)
    with pytest.raises(ValueError, match="staging_file_limit"):
        validate_staging_plan(source)


@pytest.mark.parametrize(
    ("field", "ceiling"),
    [
        ("member_count", 10_000),
        ("file_bytes", 256 * 1024 * 1024),
        ("total_file_bytes", 256 * 1024 * 1024),
        ("path_bytes", 1024),
        ("path_components", 64),
        ("encoded_bytes", 4 * 1024 * 1024),
    ],
)
def test_exact_candidate_ceiling(field, ceiling):
    validate_staging_plan(plan(bound=limits(**{field: ceiling})))
    with pytest.raises(ValueError, match="invalid_staging_limit"):
        validate_staging_plan(plan(bound=limits(**{field: ceiling + 1})))


def test_oversized_path_before_unicode_work(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("normalizing an oversized scalar")

    monkeypatch.setattr("aware_file_system.staging_plan._read_text", forbidden)
    with pytest.raises(ValueError, match="staging_path_byte_limit"):
        validate_staging_plan(plan(file("x" * 1025)))


def test_no_filesystem_or_upper_layer_dependency():
    import ast
    from pathlib import Path

    import aware_file_system.staging_plan as module

    tree = ast.parse(Path(module.__file__).read_text())
    imports = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    names = {
        node.module if isinstance(node, ast.ImportFrom) else alias.name
        for node in imports
        for alias in (node.names if isinstance(node, ast.Import) else [None])
    }
    assert names == {
        "__future__",
        "hashlib",
        "json",
        "dataclasses",
        "confined_mutation",
    }
