import asyncio
import sys
from pathlib import Path
from typing import Awaitable, Callable

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from aware_file_system.config import Config, FileSystemConfig, FilterConfig
from aware_file_system.models import ChangeType
from aware_file_system.watcher import (
    FileChangeEvent,
    FileSystemWatcher,
    RepositoryFileSystemWatcher,
)


async def _run_and_collect(
    watcher: FileSystemWatcher,
    action: Callable[[], Awaitable[None] | None],
    *,
    ensure_mtime: bool = False,
) -> tuple[list[FileChangeEvent], dict[ChangeType, list]]:
    events: list[FileChangeEvent] = []

    async def handler(event: FileChangeEvent) -> None:
        events.append(event)

    watcher.add_event_handler(handler)
    try:
        result = action()
        if asyncio.iscoroutine(result):
            await result
        if ensure_mtime:
            await asyncio.sleep(0.02)
        changes = await watcher.poll_once()
        return events, changes
    finally:
        watcher.remove_event_handler(handler)


def _build_watcher(
    root: Path,
    *,
    poll_interval: float = 0.05,
    use_executor: bool = False,
    filter_config: FilterConfig | None = None,
) -> FileSystemWatcher:
    config = Config(
        file_system=FileSystemConfig(root_path=str(root), generate_tree=False, export_json=False),
        filter=filter_config or FilterConfig(),
    )
    return FileSystemWatcher(config, poll_interval=poll_interval, use_executor=use_executor)


def _run(coro: Awaitable[None]) -> None:
    asyncio.run(coro)


class TestFileSystemWatcher:
    def test_poll_once_detects_create_update_delete(self, tmp_path: Path) -> None:
        async def scenario() -> None:
            watcher = _build_watcher(tmp_path)
            await watcher.initialize()
            target = tmp_path / "track.txt"

            create_events, create_changes = await _run_and_collect(watcher, lambda: target.write_text("alpha"))
            assert set(create_changes[ChangeType.create]) == {"track.txt"}
            assert [event.change_type for event in create_events] == [ChangeType.create]

            update_events, update_changes = await _run_and_collect(
                watcher, lambda: target.write_text("beta"), ensure_mtime=True
            )
            assert set(update_changes[ChangeType.update]) == {"track.txt"}
            assert [event.change_type for event in update_events] == [ChangeType.update]

            delete_events, delete_changes = await _run_and_collect(watcher, lambda: target.unlink())
            assert set(delete_changes[ChangeType.delete]) == {"track.txt"}
            assert [event.change_type for event in delete_events] == [ChangeType.delete]

        _run(scenario())

    def test_nested_creation_is_reported(self, tmp_path: Path) -> None:
        async def scenario() -> None:
            watcher = _build_watcher(tmp_path)
            await watcher.initialize()
            nested_file = tmp_path / "nested" / "deep.txt"

            def create_nested() -> None:
                nested_file.parent.mkdir(parents=True)
                nested_file.write_text("payload")

            events, changes = await _run_and_collect(watcher, create_nested)
            assert set(changes[ChangeType.create]) == {"nested/deep.txt"}
            assert [event.path for event in events] == ["nested/deep.txt"]

        _run(scenario())

    def test_ignore_rules_filter_expected_paths(self, tmp_path: Path) -> None:
        async def scenario() -> None:
            watcher = _build_watcher(tmp_path)
            await watcher.initialize()

            def generate_files() -> None:
                (tmp_path / ".aware").mkdir()
                (tmp_path / ".aware" / "blob.dat").write_bytes(b"blob")
                (tmp_path / "__pycache__").mkdir()
                (tmp_path / "__pycache__" / "ignored.pyc").write_bytes(b"pyc")
                (tmp_path / "keep.py").write_text("print('visible')")

            events, changes = await _run_and_collect(watcher, generate_files)
            assert set(changes[ChangeType.create]) == {"keep.py"}
            assert [event.path for event in events] == ["keep.py"]

        _run(scenario())

    def test_custom_ignore_configuration(self, tmp_path: Path) -> None:
        async def scenario() -> None:
            filter_config = FilterConfig(
                ignored_extensions=[".tmp"],
                ignored_dirs=["ignored"],
                inherit_ignore_defaults=False,
            )
            watcher = _build_watcher(tmp_path, filter_config=filter_config)
            await watcher.initialize()

            def create_files() -> None:
                (tmp_path / "ignored").mkdir()
                (tmp_path / "ignored" / "skip.txt").write_text("hidden")
                (tmp_path / "keep").mkdir()
                (tmp_path / "keep" / "visible.txt").write_text("visible")
                (tmp_path / "keep" / "logs.tmp").write_text("temp")

            events, changes = await _run_and_collect(watcher, create_files)
            assert set(changes[ChangeType.create]) == {"keep/visible.txt"}
            assert [event.path for event in events] == ["keep/visible.txt"]

        _run(scenario())

    def test_multiple_handlers_receive_events(self, tmp_path: Path) -> None:
        async def scenario() -> None:
            watcher = _build_watcher(tmp_path)
            await watcher.initialize()
            handler_one_events: list[FileChangeEvent] = []
            handler_two_events: list[FileChangeEvent] = []

            async def handler_one(event: FileChangeEvent) -> None:
                handler_one_events.append(event)

            async def handler_two(event: FileChangeEvent) -> None:
                handler_two_events.append(event)

            watcher.add_event_handler(handler_one)
            watcher.add_event_handler(handler_two)

            try:
                events, _ = await _run_and_collect(watcher, lambda: (tmp_path / "shared.txt").write_text("ok"))
            finally:
                watcher.remove_event_handler(handler_one)
                watcher.remove_event_handler(handler_two)

            assert events
            assert handler_one_events
            assert handler_two_events

        _run(scenario())

    def test_watch_loop_emits_events_with_executor(self, tmp_path: Path) -> None:
        async def scenario() -> None:
            watcher = _build_watcher(tmp_path, poll_interval=0.02, use_executor=True)
            events: list[FileChangeEvent] = []

            async def capture(event: FileChangeEvent) -> None:
                events.append(event)

            watcher.add_event_handler(capture)
            await watcher.start()

            try:
                await asyncio.sleep(0.05)
                (tmp_path / "loop.txt").write_text("data")
                await asyncio.sleep(0.1)
            finally:
                await watcher.stop()

            assert any(event.path == "loop.txt" for event in events)
            assert not watcher.get_stats()["is_running"]

        _run(scenario())

    def test_start_stop_is_idempotent(self, tmp_path: Path) -> None:
        async def scenario() -> None:
            watcher = _build_watcher(tmp_path)

            await watcher.start()
            await watcher.start()
            assert watcher.get_stats()["is_running"]

            await watcher.stop()
            await watcher.stop()
            assert not watcher.get_stats()["is_running"]

        _run(scenario())

    def test_repository_watcher_exposes_stats_and_events(self, tmp_path: Path) -> None:
        async def scenario() -> None:
            class DummyRepository:
                def __init__(self, workspace: Path) -> None:
                    self.name = "repo"
                    self.workspace_root = str(workspace)
                    self.events: list[FileChangeEvent] = []

                async def apply_event(self, event: FileChangeEvent) -> None:
                    self.events.append(event)

            repo = DummyRepository(tmp_path)
            repo_watcher = RepositoryFileSystemWatcher(repo, poll_interval=0.05, use_executor=False)
            await repo_watcher.watcher.initialize()

            repo_watcher.watcher.add_event_handler(repo.apply_event)

            file_path = tmp_path / "repo_file.txt"
            events_collected, changes = await _run_and_collect(
                repo_watcher.watcher, lambda: file_path.write_text("data")
            )

            assert set(changes[ChangeType.create]) == {"repo_file.txt"}
            assert events_collected
            assert repo.events

            stats = repo_watcher.get_stats()
            assert stats["repository_name"] == repo.name
            assert stats["repository_workspace"] == repo.workspace_root

            if repo_watcher.watcher.get_stats()["is_running"]:
                await repo_watcher.stop()

        _run(scenario())
