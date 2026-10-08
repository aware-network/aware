from __future__ import annotations

import statistics
import time
from collections.abc import Callable

from aware_specification_fs_source_contract import (
    SpecificationFsParserProfileCoordinate,
    SpecificationFsSourceClosure,
    SpecificationFsSourceMember,
    SpecificationFsSourceRole,
    decode_specification_fs_source_closure,
    encode_specification_fs_source_closure,
)


def fixture(member_count: int, total_bytes: int) -> SpecificationFsSourceClosure:
    return SpecificationFsSourceClosure(
        "specs/performance",
        performance_profile(),
        fixture_members(member_count, total_bytes),
    )


def performance_profile() -> SpecificationFsParserProfileCoordinate:
    return SpecificationFsParserProfileCoordinate(
        "aware.specification.fs-parser", "sha256:" + "1" * 64
    )


def fixture_members(
    member_count: int, total_bytes: int
) -> tuple[SpecificationFsSourceMember, ...]:
    body_size = total_bytes // member_count
    members = [
        SpecificationFsSourceMember(
            "aware.spec.toml",
            SpecificationFsSourceRole.MANIFEST,
            "x" * (body_size - 1) + "\n",
        )
    ]
    for index in range(1, member_count):
        members.append(
            SpecificationFsSourceMember(
                f"members/{index:04d}.md",
                SpecificationFsSourceRole.PHASE,
                "x" * (body_size - 1) + "\n",
            )
        )
    return tuple(members)


def samples(
    operation: Callable[[], object], *, warmups: int = 5, count: int = 30
) -> tuple[float, float]:
    call = operation
    for _ in range(warmups):
        call()
    measured: list[float] = []
    for _ in range(count):
        start = time.perf_counter()
        call()
        measured.append((time.perf_counter() - start) * 1000)
    return statistics.median(measured), sorted(measured)[int(count * 0.95) - 1]


def test_representative_and_doubled_performance() -> None:
    representative = fixture(256, 1_048_576)
    doubled = fixture(512, 2_097_152)
    representative_members = representative.members
    doubled_members = doubled.members
    profile = representative.profile
    encoded = encode_specification_fs_source_closure(representative)
    doubled_encoded = encode_specification_fs_source_closure(doubled)
    derive = samples(
        lambda: SpecificationFsSourceClosure(
            "specs/performance", profile, representative_members
        )
    )
    encode = samples(lambda: encode_specification_fs_source_closure(representative))
    decode = samples(lambda: decode_specification_fs_source_closure(encoded))
    doubled_derive = samples(
        lambda: SpecificationFsSourceClosure(
            "specs/performance", profile, doubled_members
        )
    )
    doubled_encode = samples(lambda: encode_specification_fs_source_closure(doubled))
    doubled_decode = samples(
        lambda: decode_specification_fs_source_closure(doubled_encoded)
    )
    assert derive[0] < 75 and derive[1] < 110
    assert encode[0] < 100 and encode[1] < 150
    assert decode[0] < 200 and decode[1] < 300
    assert len(encoded) < 4_500_000
    assert doubled_derive[0] <= derive[0] * 2.5
    assert doubled_encode[0] <= encode[0] * 2.5
    assert doubled_decode[0] <= decode[0] * 2.5
