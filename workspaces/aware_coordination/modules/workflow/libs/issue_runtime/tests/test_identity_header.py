import io

import pytest
from aware_issue_runtime import parse_issue_source
from aware_issue_runtime.parser import read_issue_source_header


class BoundedStream(io.BytesIO):
    def __init__(self, source: bytes):
        super().__init__(source)
        self.total = 0

    def read(self, size=-1):
        assert 0 < size <= 4096
        value = super().read(size)
        self.total += len(value)
        return value


@pytest.mark.parametrize(
    "ending", ["\n", "\r", "\r\n", "\v", "\f", "\x85", "\u2028", "\u2029"]
)
def test_large_body_preserves_original_header_grammar_without_loading_body(ending):
    header = ending.join(
        [
            "# Issue: Door",
            "- tAg: `fb/2026-10-13/door`",
            "  continued",
            "- Tag: second",
            "## Body",
            "",
        ]
    )
    source = header + "- Tag: hidden-in-body\n" + "x" * 1_000_000
    stream = BoundedStream(source.encode())
    original = parse_issue_source(source)
    value = read_issue_source_header(stream, byte_limit=262_144)
    assert value.title == original.title
    assert value.headers == original.headers
    assert value.header("Tag") == "fb/2026-10-13/door continued"
    assert value.sections == ()
    assert stream.total == 4096


@pytest.mark.parametrize(
    "source",
    [
        b"",
        b"# Issue: Legacy",
        b"- Tag: first\n  second",
        b"- Tag: first\n- Tag: second",
    ],
)
def test_eof_completes_small_sectionless_headers(source):
    stream = BoundedStream(source)
    value = read_issue_source_header(stream, byte_limit=max(1, len(source)))
    assert value.headers == parse_issue_source(source.decode()).headers
    assert stream.total <= max(1, len(source)) + 1


@pytest.mark.parametrize("duplicate", [False, True])
def test_header_without_boundary_cannot_hide_a_late_identity(duplicate):
    source = b"# Issue: Incomplete\n" + b"x" * 262_144
    if duplicate:
        source += b"\n- Tag: fb/2026-10-13/door\n## Body\n"
    stream = BoundedStream(source)
    with pytest.raises(OSError, match="header limit"):
        read_issue_source_header(stream, byte_limit=262_144)
    assert stream.total == 262_145


@pytest.mark.parametrize("prefix_length", [4094, 4095, 4096])
def test_utf8_and_continuations_cross_chunk_boundaries(prefix_length):
    source = "- Source: " + "x" * (prefix_length - len("- Source: "))
    source += "é\n- Tag: first\n  continuation\n## Body\n" + "x" * 10_000
    stream = BoundedStream(source.encode())
    value = read_issue_source_header(stream, byte_limit=12_000)
    assert value.headers == parse_issue_source(source).headers
    assert value.header("Tag") == "first continuation"
    assert stream.total == 8192


@pytest.mark.parametrize(
    "source",
    [b"- Tag: \xff\n## Body\n", b"- Tag: \xc3", b"\xff\n- Tag: other\n## Body\n"],
)
def test_invalid_header_encoding_refuses(source):
    with pytest.raises(UnicodeError):
        read_issue_source_header(BoundedStream(source), byte_limit=100)


def test_invalid_body_encoding_cannot_hide_an_identity_in_a_complete_header():
    source = b"- Tag: duplicate\n## Body\n\xff"
    assert (
        read_issue_source_header(BoundedStream(source), byte_limit=100).header("Tag")
        == "duplicate"
    )


@pytest.mark.parametrize("limit", [True, 0, -1, 1.5])
def test_invalid_limit_refuses_before_read(limit):
    stream = BoundedStream(b"- Tag: first")
    with pytest.raises(ValueError):
        read_issue_source_header(stream, byte_limit=limit)
    assert stream.total == 0


def test_boundary_must_be_within_the_same_byte_budget():
    source = b"- Tag: first\n## B" + b"x" * 100
    boundary = len(b"- Tag: first\n## B")
    assert (
        read_issue_source_header(BoundedStream(source), byte_limit=boundary).header(
            "Tag"
        )
        == "first"
    )
    with pytest.raises(OSError):
        read_issue_source_header(BoundedStream(source), byte_limit=boundary - 1)
