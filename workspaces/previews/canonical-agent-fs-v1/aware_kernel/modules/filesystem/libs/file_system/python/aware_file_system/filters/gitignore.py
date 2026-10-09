from __future__ import annotations

import logging
import os
import posixpath
import subprocess
from collections.abc import Iterable
from pathlib import Path

from pathspec import GitIgnoreSpec

from aware_file_system.filters.base import Filter

logger = logging.getLogger(__name__)

_ScopedSpec = tuple[str, GitIgnoreSpec]


class GitIgnore(Filter):
    """Lazy, nested Git ignore matching over repository-relative paths."""

    _root_path: str
    _spec_cache: dict[str, GitIgnoreSpec | None]
    _chain_cache: dict[str, tuple[_ScopedSpec, ...]]

    def setup(self, root_path: str) -> None:
        """Bind the root without performing a second repository traversal."""
        self._root_path = os.path.abspath(root_path)
        self._spec_cache = {}
        self._chain_cache = {}
        logger.debug("Initialized lazy GitIgnore specs for %s", root_path)

    def should_include(self, file_path: str) -> bool:
        relative_path = self._relative_posix_path(file_path)
        if relative_path is None:
            return False
        return not self._is_ignored(relative_path)

    def should_include_directory(self, directory_path: str) -> bool:
        """Return whether Git permits traversal into one directory.

        Git cannot re-include a file once an ancestor directory is excluded, so
        pruning a directory that matches the effective parent rules preserves
        ordered negation semantics while avoiding per-file work below it.
        """
        relative_path = self._relative_posix_path(directory_path)
        if relative_path is None:
            return False
        return not self._is_ignored(f"{relative_path}/")

    def included_files(self, file_paths: Iterable[str]) -> set[str]:
        """Apply ordered nested ignore semantics to a bounded file batch."""

        candidates = tuple(file_paths)
        accelerated = self._git_included_files(candidates)
        if accelerated is not None:
            return accelerated

        grouped: dict[
            tuple[tuple[str, int], ...],
            tuple[tuple[_ScopedSpec, ...], list[tuple[str, str]]],
        ] = {}
        excluded: set[str] = set()
        for original in candidates:
            relative = self._relative_posix_path(original)
            if relative is None:
                excluded.add(original)
                continue
            directory = posixpath.dirname(relative) or "."
            chain = self._spec_chain(directory)
            key = tuple((scope, id(spec)) for scope, spec in chain)
            if key not in grouped:
                grouped[key] = (chain, [])
            grouped[key][1].append((original, relative))

        included: set[str] = set()
        for chain, values in grouped.values():
            ignored = [False] * len(values)
            for scope, spec in chain:
                scoped_paths = [
                    relative if scope == "." else relative[len(scope) + 1 :]
                    for _original, relative in values
                ]
                for index, decision in enumerate(spec.check_files(scoped_paths)):
                    if decision.include is not None:
                        ignored[index] = decision.include
            included.update(
                original
                for index, (original, _relative) in enumerate(values)
                if not ignored[index]
            )
        return included - excluded

    def _git_included_files(self, file_paths: tuple[str, ...]) -> set[str] | None:
        """Use Git's bounded batch matcher when available; fall back to pathspec."""

        if not file_paths:
            return set()
        relative_to_original: dict[str, str] = {}
        root_prefix = self._root_path.rstrip(os.sep) + os.sep
        for original in file_paths:
            relative = (
                original[len(root_prefix) :].replace(os.sep, "/")
                if original.startswith(root_prefix)
                else self._relative_posix_path(original)
            )
            if relative is None:
                continue
            relative_to_original[relative] = original
        stdin = (
            b"\0".join(os.fsencode(relative) for relative in relative_to_original)
            + b"\0"
        )
        try:
            result = subprocess.run(
                (
                    "git",
                    "-c",
                    "core.fsmonitor=false",
                    "-C",
                    self._root_path,
                    "check-ignore",
                    "--no-index",
                    "-z",
                    "--stdin",
                ),
                input=stdin,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=2.0,
                env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if result.returncode not in {0, 1}:
            return None
        ignored = {os.fsdecode(value) for value in result.stdout.split(b"\0") if value}
        return {
            original
            for relative, original in relative_to_original.items()
            if relative not in ignored
        }

    def _relative_posix_path(self, file_path: str) -> str | None:
        relative = os.path.relpath(os.path.abspath(file_path), self._root_path)
        if relative == os.pardir or relative.startswith(f"{os.pardir}{os.sep}"):
            return None
        return relative.replace(os.sep, "/")

    def _is_ignored(self, relative_path: str) -> bool:
        directory = posixpath.dirname(relative_path.rstrip("/")) or "."
        ignored = False
        for scope, spec in self._spec_chain(directory):
            scoped_path = (
                relative_path if scope == "." else relative_path[len(scope) + 1 :]
            )
            decision = spec.check_file(scoped_path).include
            if decision is not None:
                ignored = decision
        return ignored

    def _spec_chain(self, relative_directory: str) -> tuple[_ScopedSpec, ...]:
        normalized = posixpath.normpath(relative_directory)
        cached = self._chain_cache.get(normalized)
        if cached is not None:
            return cached

        if normalized == ".":
            chain: tuple[_ScopedSpec, ...] = ()
        else:
            parent = posixpath.dirname(normalized) or "."
            chain = self._spec_chain(parent)

        spec = self._local_spec(normalized)
        if spec is not None:
            chain = (*chain, (normalized, spec))
        self._chain_cache[normalized] = chain
        return chain

    def _local_spec(self, relative_directory: str) -> GitIgnoreSpec | None:
        if relative_directory in self._spec_cache:
            return self._spec_cache[relative_directory]
        directory = (
            Path(self._root_path)
            if relative_directory == "."
            else Path(self._root_path, *relative_directory.split("/"))
        )
        ignore_path = directory / ".gitignore"
        try:
            if not ignore_path.is_file():
                spec = None
            else:
                with ignore_path.open(encoding="utf-8") as stream:
                    spec = GitIgnoreSpec.from_lines(stream)
        except (OSError, UnicodeError) as error:
            logger.warning(
                "Unable to read Git ignore rules from %s: %s", ignore_path, error
            )
            spec = None
        self._spec_cache[relative_directory] = spec
        return spec
