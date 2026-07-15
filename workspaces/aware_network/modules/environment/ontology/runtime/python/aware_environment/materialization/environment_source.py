from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


class EnvironmentSourceError(ValueError):
    """Raised when environment-owned profile/session source is unsupported."""


@dataclass(frozen=True, slots=True)
class EnvironmentThreadSource:
    key: str
    title: str | None = None
    description: str | None = None
    narrative: str | None = None
    intent: str | None = None
    workspace_view_key: str | None = None
    is_default: bool = False


@dataclass(frozen=True, slots=True)
class EnvironmentProcessSource:
    key: str
    type: str
    title: str | None = None
    description: str | None = None
    narrative: str | None = None
    intent: str | None = None
    is_default: bool = False
    threads: tuple[EnvironmentThreadSource, ...] = ()


@dataclass(frozen=True, slots=True)
class EnvironmentSessionSource:
    key: str
    title: str | None = None
    description: str | None = None
    purpose: str | None = None
    status: str = "active"
    default_profile_key: str | None = None
    default_process_key: str | None = None
    default_thread_key: str | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentProfileSource:
    key: str
    title: str | None = None
    description: str | None = None
    narrative: str | None = None
    is_default: bool = False
    processes: tuple[EnvironmentProcessSource, ...] = ()
    sessions: tuple[EnvironmentSessionSource, ...] = ()
    source_path: str | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentSourceBundle:
    profiles: tuple[EnvironmentProfileSource, ...] = ()


@dataclass(slots=True)
class _MutableProfile:
    key: str
    title: str | None = None
    description: str | None = None
    narrative: str | None = None
    is_default: bool = False
    processes: list[EnvironmentProcessSource] = field(default_factory=list)
    sessions: list[EnvironmentSessionSource] = field(default_factory=list)
    source_path: str | None = None


@dataclass(slots=True)
class _MutableProcess:
    key: str
    type: str
    title: str | None = None
    description: str | None = None
    narrative: str | None = None
    intent: str | None = None
    is_default: bool = False
    threads: list[EnvironmentThreadSource] = field(default_factory=list)


class _TokenStream:
    def __init__(self, tokens: list[str], *, source_label: str) -> None:
        self._tokens = tokens
        self._source_label = source_label
        self._index = 0

    def peek(self) -> str | None:
        if self._index >= len(self._tokens):
            return None
        return self._tokens[self._index]

    def pop(self) -> str:
        token = self.peek()
        if token is None:
            raise EnvironmentSourceError(
                f"Unexpected end of environment source in {self._source_label}"
            )
        self._index += 1
        return token

    def expect(self, expected: str) -> None:
        token = self.pop()
        if token != expected:
            raise EnvironmentSourceError(
                f"Expected {expected!r} in {self._source_label}, found {token!r}"
            )

    def at_end(self) -> bool:
        return self.peek() is None


def parse_environment_source_text(
    *,
    source_text: str,
    source_path: str | Path | None = None,
) -> EnvironmentSourceBundle:
    """Parse the Environment-owned profile/session subset from `.aware` source."""

    source_label = str(source_path or "<environment-source>")
    stream = _TokenStream(_lex(source_text, source_label=source_label), source_label=source_label)
    profiles: list[EnvironmentProfileSource] = []
    while not stream.at_end():
        token = stream.peek()
        if token not in {"profile", "environment_profile"}:
            raise EnvironmentSourceError(
                f"Unsupported top-level token {token!r} in {source_label}; "
                "expected `profile`"
            )
        profiles.append(_parse_profile(stream, source_label=source_label))
    return EnvironmentSourceBundle(profiles=tuple(profiles))


def merge_environment_source_bundles(
    bundles: list[EnvironmentSourceBundle],
) -> EnvironmentSourceBundle:
    profiles: list[EnvironmentProfileSource] = []
    seen: set[str] = set()
    for bundle in bundles:
        for profile in bundle.profiles:
            key = profile.key.casefold().strip()
            if key in seen:
                raise EnvironmentSourceError(
                    f"Duplicate environment profile key {profile.key!r}"
                )
            seen.add(key)
            profiles.append(profile)
    return EnvironmentSourceBundle(profiles=tuple(profiles))


def _parse_profile(
    stream: _TokenStream,
    *,
    source_label: str,
) -> EnvironmentProfileSource:
    _ = stream.pop()
    key = _symbol(stream.pop(), ctx="profile key", source_label=source_label)
    is_default = _consume_default_flag(stream)
    stream.expect("{")
    profile = _MutableProfile(key=key, is_default=is_default, source_path=source_label)
    while stream.peek() != "}":
        token = stream.peek()
        if token is None:
            raise EnvironmentSourceError(f"Unclosed profile {key!r} in {source_label}")
        if token == "process":
            profile.processes.append(_parse_process(stream, source_label=source_label))
            continue
        if token == "session":
            profile.sessions.append(
                _parse_session(
                    stream,
                    default_profile_key=key,
                    source_label=source_label,
                )
            )
            continue
        _parse_profile_property(profile, stream, source_label=source_label)
    stream.expect("}")
    _assert_unique([process.key for process in profile.processes], "process", source_label)
    _assert_unique([session.key for session in profile.sessions], "session", source_label)
    return EnvironmentProfileSource(
        key=profile.key,
        title=profile.title,
        description=profile.description,
        narrative=profile.narrative,
        is_default=profile.is_default,
        processes=tuple(profile.processes),
        sessions=tuple(profile.sessions),
        source_path=profile.source_path,
    )


def _parse_process(
    stream: _TokenStream,
    *,
    source_label: str,
) -> EnvironmentProcessSource:
    stream.expect("process")
    process_type = _symbol(stream.pop(), ctx="process type", source_label=source_label)
    key = _symbol(stream.pop(), ctx="process key", source_label=source_label)
    is_default = _consume_default_flag(stream)
    stream.expect("{")
    process = _MutableProcess(key=key, type=process_type, is_default=is_default)
    while stream.peek() != "}":
        token = stream.peek()
        if token is None:
            raise EnvironmentSourceError(f"Unclosed process {key!r} in {source_label}")
        if token == "thread":
            process.threads.append(_parse_thread(stream, source_label=source_label))
            continue
        _parse_process_property(process, stream, source_label=source_label)
    stream.expect("}")
    _assert_unique([thread.key for thread in process.threads], "thread", source_label)
    return EnvironmentProcessSource(
        key=process.key,
        type=process.type,
        title=process.title,
        description=process.description,
        narrative=process.narrative,
        intent=process.intent,
        is_default=process.is_default,
        threads=tuple(process.threads),
    )


def _parse_thread(
    stream: _TokenStream,
    *,
    source_label: str,
) -> EnvironmentThreadSource:
    stream.expect("thread")
    key = _symbol(stream.pop(), ctx="thread key", source_label=source_label)
    is_default = _consume_default_flag(stream)
    stream.expect("{")
    values: dict[str, str | None] = {
        "title": None,
        "description": None,
        "narrative": None,
        "intent": None,
        "workspace_view_key": None,
    }
    while stream.peek() != "}":
        token = stream.pop()
        if token is None:
            raise EnvironmentSourceError(f"Unclosed thread {key!r} in {source_label}")
        if token == "title":
            values["title"] = stream.pop()
        elif token == "description":
            values["description"] = stream.pop()
        elif token == "narrative":
            values["narrative"] = stream.pop()
        elif token == "intent":
            values["intent"] = stream.pop()
        elif token == "workspace_view":
            values["workspace_view_key"] = stream.pop()
        else:
            raise EnvironmentSourceError(
                f"Unsupported thread token {token!r} in {source_label}"
            )
    stream.expect("}")
    return EnvironmentThreadSource(
        key=key,
        title=values["title"],
        description=values["description"],
        narrative=values["narrative"],
        intent=values["intent"],
        workspace_view_key=values["workspace_view_key"],
        is_default=is_default,
    )


def _parse_session(
    stream: _TokenStream,
    *,
    default_profile_key: str,
    source_label: str,
) -> EnvironmentSessionSource:
    stream.expect("session")
    key = _symbol(stream.pop(), ctx="session key", source_label=source_label)
    _ = _consume_default_flag(stream)
    stream.expect("{")
    title: str | None = None
    description: str | None = None
    purpose: str | None = None
    status = "active"
    default_process_key: str | None = None
    default_thread_key: str | None = None
    while stream.peek() != "}":
        token = stream.pop()
        if token == "title":
            title = stream.pop()
        elif token == "description":
            description = stream.pop()
        elif token == "purpose":
            purpose = stream.pop()
        elif token == "status":
            status = stream.pop()
        elif token == "default":
            stream.expect("process")
            default_process_key = _symbol(
                stream.pop(),
                ctx="session default process key",
                source_label=source_label,
            )
            stream.expect("thread")
            default_thread_key = _symbol(
                stream.pop(),
                ctx="session default thread key",
                source_label=source_label,
            )
        else:
            raise EnvironmentSourceError(
                f"Unsupported session token {token!r} in {source_label}"
            )
    stream.expect("}")
    return EnvironmentSessionSource(
        key=key,
        title=title,
        description=description,
        purpose=purpose,
        status=status,
        default_profile_key=default_profile_key,
        default_process_key=default_process_key,
        default_thread_key=default_thread_key,
    )


def _parse_profile_property(
    profile: _MutableProfile,
    stream: _TokenStream,
    *,
    source_label: str,
) -> None:
    token = stream.pop()
    if token == "title":
        profile.title = stream.pop()
    elif token == "description":
        profile.description = stream.pop()
    elif token == "narrative":
        profile.narrative = stream.pop()
    else:
        raise EnvironmentSourceError(
            f"Unsupported profile token {token!r} in {source_label}"
        )


def _parse_process_property(
    process: _MutableProcess,
    stream: _TokenStream,
    *,
    source_label: str,
) -> None:
    token = stream.pop()
    if token == "title":
        process.title = stream.pop()
    elif token == "description":
        process.description = stream.pop()
    elif token == "narrative":
        process.narrative = stream.pop()
    elif token == "intent":
        process.intent = stream.pop()
    else:
        raise EnvironmentSourceError(
            f"Unsupported process token {token!r} in {source_label}"
        )


def _consume_default_flag(stream: _TokenStream) -> bool:
    if stream.peek() == "default":
        stream.pop()
        return True
    return False


def _symbol(value: str, *, ctx: str, source_label: str) -> str:
    token = (value or "").strip()
    if not token or token in {"{", "}"}:
        raise EnvironmentSourceError(f"Expected {ctx} in {source_label}")
    return token


def _assert_unique(values: list[str], kind: str, source_label: str) -> None:
    seen: set[str] = set()
    for value in values:
        key = value.casefold().strip()
        if key in seen:
            raise EnvironmentSourceError(
                f"Duplicate {kind} key {value!r} in {source_label}"
            )
        seen.add(key)


def _lex(source_text: str, *, source_label: str) -> list[str]:
    tokens: list[str] = []
    i = 0
    while i < len(source_text):
        char = source_text[i]
        if char.isspace():
            i += 1
            continue
        if char == "/" and i + 1 < len(source_text) and source_text[i + 1] == "/":
            newline = source_text.find("\n", i + 2)
            if newline == -1:
                break
            i = newline + 1
            continue
        if char in "{}":
            tokens.append(char)
            i += 1
            continue
        if char == '"':
            value, i = _consume_quoted(source_text, i, source_label=source_label)
            tokens.append(value)
            continue
        start = i
        while i < len(source_text):
            if source_text[i].isspace() or source_text[i] in '{}"':
                break
            if (
                source_text[i] == "/"
                and i + 1 < len(source_text)
                and source_text[i + 1] == "/"
            ):
                break
            i += 1
        token = source_text[start:i].strip()
        if token:
            tokens.append(token)
    return tokens


def _consume_quoted(
    source_text: str,
    start_index: int,
    *,
    source_label: str,
) -> tuple[str, int]:
    chars: list[str] = []
    i = start_index + 1
    while i < len(source_text):
        char = source_text[i]
        if char == "\\":
            if i + 1 >= len(source_text):
                raise EnvironmentSourceError(
                    f"Unclosed escape sequence in quoted string at {source_label}"
                )
            chars.append(source_text[i + 1])
            i += 2
            continue
        if char == '"':
            return "".join(chars), i + 1
        chars.append(char)
        i += 1
    raise EnvironmentSourceError(f"Unclosed quoted string in {source_label}")


__all__ = [
    "EnvironmentProcessSource",
    "EnvironmentProfileSource",
    "EnvironmentSessionSource",
    "EnvironmentSourceBundle",
    "EnvironmentSourceError",
    "EnvironmentThreadSource",
    "merge_environment_source_bundles",
    "parse_environment_source_text",
]
