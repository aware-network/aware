from __future__ import annotations

import copy

import pytest

from aware_specification_fs_source_contract import (
    SpecificationFsContractError,
    SpecificationFsParserProfileCoordinate,
    SpecificationFsSourceClosure,
    SpecificationFsSourceMember,
    SpecificationFsSourceRole,
)
from aware_specification_fs_source_contract.values import MAX_MEMBER_BYTES


def profile() -> SpecificationFsParserProfileCoordinate:
    return SpecificationFsParserProfileCoordinate(
        parser_implementation_ref="aware.specification.fs-parser",
        parser_implementation_digest="sha256:" + "1" * 64,
    )


def closure(*members: SpecificationFsSourceMember) -> SpecificationFsSourceClosure:
    return SpecificationFsSourceClosure("specs/example", profile(), tuple(members))


def test_all_roles_and_determinism() -> None:
    members = [
        SpecificationFsSourceMember(
            "aware.spec.toml", SpecificationFsSourceRole.MANIFEST, "aware = 1\n"
        )
    ]
    for index, role in enumerate(tuple(SpecificationFsSourceRole)[1:]):
        members.append(
            SpecificationFsSourceMember(f"docs/{index}.md", role, f"# {role.value}\n")
        )
    value = closure(*members)
    assert copy.copy(value) == value
    assert copy.deepcopy(value) == value
    assert value.total_size_bytes == sum(member.size_bytes for member in members)
    assert value.manifest_member_digest == members[0].member_digest


@pytest.mark.parametrize(
    "path", ["", "/x", "x/", "x//y", "x/./y", "x/../y", "x\\y", "x\x00y"]
)
def test_invalid_paths_reject(path: str) -> None:
    with pytest.raises(SpecificationFsContractError):
        SpecificationFsSourceMember(path, SpecificationFsSourceRole.PHASE, "x\n")


@pytest.mark.parametrize(
    "codepoint", ["\u000b", "\u000c", "\u0085", "\u2028", "\u2029"]
)
@pytest.mark.parametrize("template", ["{}a\n", "a{}b\n", "a{}\n", "a{}"])
def test_alternative_line_breaks_reject_everywhere(
    codepoint: str, template: str
) -> None:
    with pytest.raises(SpecificationFsContractError):
        SpecificationFsSourceMember(
            "x.md", SpecificationFsSourceRole.PHASE, template.format(codepoint)
        )


@pytest.mark.parametrize(
    "body", ["x\r\n", "x\r", "x", "x\n\n", "x \n", "x\t\n", "x\x00\n"]
)
def test_noncanonical_bodies_reject(body: str) -> None:
    with pytest.raises(SpecificationFsContractError):
        SpecificationFsSourceMember("x.md", SpecificationFsSourceRole.PHASE, body)


def test_member_body_size_boundary() -> None:
    accepted = SpecificationFsSourceMember(
        "x.md",
        SpecificationFsSourceRole.PHASE,
        "x" * (MAX_MEMBER_BYTES - 1) + "\n",
    )
    assert accepted.size_bytes == MAX_MEMBER_BYTES
    with pytest.raises(SpecificationFsContractError):
        SpecificationFsSourceMember(
            "x.md",
            SpecificationFsSourceRole.PHASE,
            "x" * MAX_MEMBER_BYTES + "\n",
        )


def test_order_duplicates_manifest_and_restamping_reject() -> None:
    manifest = SpecificationFsSourceMember(
        "aware.spec.toml", SpecificationFsSourceRole.MANIFEST, "x\n"
    )
    phase = SpecificationFsSourceMember(
        "phase.md", SpecificationFsSourceRole.PHASE, "x\n"
    )
    with pytest.raises(SpecificationFsContractError):
        closure(phase, manifest)
    with pytest.raises(SpecificationFsContractError):
        closure(manifest, manifest)
    with pytest.raises(SpecificationFsContractError):
        closure(phase)
    value = closure(manifest, phase)
    object.__setattr__(value, "closure_digest", "sha256:" + "9" * 64)
    from aware_specification_fs_source_contract import (
        encode_specification_fs_source_closure,
    )

    with pytest.raises(SpecificationFsContractError):
        encode_specification_fs_source_closure(value)


def test_incomplete_and_foreign_values_reject() -> None:
    from aware_specification_fs_source_contract import (
        encode_specification_fs_source_closure,
    )

    incomplete = object.__new__(SpecificationFsSourceClosure)
    with pytest.raises(SpecificationFsContractError):
        encode_specification_fs_source_closure(incomplete)

    calls: list[str] = []

    class ForeignMember(SpecificationFsSourceMember):
        def __getattribute__(self, name: str) -> object:
            calls.append(name)
            return super().__getattribute__(name)

    foreign = object.__new__(ForeignMember)
    manifest = SpecificationFsSourceMember(
        "aware.spec.toml", SpecificationFsSourceRole.MANIFEST, "x\n"
    )
    with pytest.raises(SpecificationFsContractError):
        closure(manifest, foreign)
    assert calls == []


def test_foreign_scalar_subclasses_reject_without_behavior() -> None:
    from aware_specification_fs_source_contract import (
        encode_specification_fs_source_closure,
    )

    calls: list[str] = []

    class ForeignStr(str):
        def __eq__(self, other: object) -> bool:
            calls.append("str_eq")
            return super().__eq__(other)

        def __ne__(self, other: object) -> bool:
            calls.append("str_ne")
            return super().__ne__(other)

    class ForeignInt(int):
        def __eq__(self, other: object) -> bool:
            calls.append("int_eq")
            return super().__eq__(other)

        def __ne__(self, other: object) -> bool:
            calls.append("int_ne")
            return super().__ne__(other)

    with pytest.raises(SpecificationFsContractError):
        SpecificationFsParserProfileCoordinate(
            "aware.specification.fs-parser",
            "sha256:" + "1" * 64,
            profile_ref=ForeignStr("specification_fs_v1"),
        )
    with pytest.raises(SpecificationFsContractError):
        SpecificationFsSourceMember(
            ForeignStr("aware.spec.toml"),
            SpecificationFsSourceRole.MANIFEST,
            "x\n",
        )
    with pytest.raises(SpecificationFsContractError):
        SpecificationFsSourceClosure(
            "specs/example",
            profile(),
            (
                SpecificationFsSourceMember(
                    "aware.spec.toml", SpecificationFsSourceRole.MANIFEST, "x\n"
                ),
            ),
            contract=ForeignStr("aware.specification.fs-source-closure.v1"),
        )

    base = closure(
        SpecificationFsSourceMember(
            "aware.spec.toml", SpecificationFsSourceRole.MANIFEST, "x\n"
        )
    )
    mutations: tuple[tuple[object, str, object], ...] = (
        (
            base.profile,
            "parser_implementation_ref",
            ForeignStr(base.profile.parser_implementation_ref),
        ),
        (
            base.profile,
            "parser_implementation_digest",
            ForeignStr(base.profile.parser_implementation_digest),
        ),
        (base.profile, "profile_ref", ForeignStr(base.profile.profile_ref)),
        (
            base.profile,
            "profile_schema_ref",
            ForeignStr(base.profile.profile_schema_ref),
        ),
        (
            base.profile,
            "profile_schema_digest",
            ForeignStr(base.profile.profile_schema_digest),
        ),
        (
            base.profile,
            "profile_coordinate_digest",
            ForeignStr(base.profile.profile_coordinate_digest),
        ),
        (base.members[0], "relative_path", ForeignStr(base.members[0].relative_path)),
        (base.members[0], "canonical_body", ForeignStr(base.members[0].canonical_body)),
        (base.members[0], "size_bytes", ForeignInt(base.members[0].size_bytes)),
        (base.members[0], "body_digest", ForeignStr(base.members[0].body_digest)),
        (base.members[0], "member_digest", ForeignStr(base.members[0].member_digest)),
        (base, "spec_root", ForeignStr(base.spec_root)),
        (base, "contract", ForeignStr(base.contract)),
        (base, "manifest_member_digest", ForeignStr(base.manifest_member_digest)),
        (base, "member_set_digest", ForeignStr(base.member_set_digest)),
        (base, "total_size_bytes", ForeignInt(base.total_size_bytes)),
        (base, "closure_digest", ForeignStr(base.closure_digest)),
    )
    for target, field_name, poisoned in mutations:
        object.__setattr__(target, field_name, poisoned)
        with pytest.raises(SpecificationFsContractError):
            encode_specification_fs_source_closure(base)
        object.__setattr__(
            target,
            field_name,
            str(poisoned) if isinstance(poisoned, str) else int(poisoned),
        )
    assert calls == []
