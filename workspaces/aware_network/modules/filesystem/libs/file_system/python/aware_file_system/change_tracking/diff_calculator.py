from typing import Optional
from difflib import unified_diff

from aware_file_system.models import (
    ChangeType,
    Changes,
    Diff,
    FileType,
    FileMetadata,
)


class DiffCalculator:
    @staticmethod
    def calculate_diff(previous_file: Optional[FileMetadata], current_file: FileMetadata) -> Diff:
        if previous_file is None:
            # This is a new file
            return Diff(
                file_path=current_file.path,
                file_type=current_file.file_type,
                change_type=ChangeType.create,
                diff_content=f"New file: {current_file.path}",
                new_content=current_file.content,
            )

        if current_file.file_type == FileType.TEXT:
            diff_content = DiffCalculator._calculate_text_diff(previous_file.content, current_file.content)
        elif current_file.file_type in [
            FileType.IMAGE,
            FileType.AUDIO,
            FileType.VIDEO,
        ]:
            diff_content = f"Binary file {current_file.path} has changed"
        else:
            diff_content = f"File {current_file.path} has changed"

        return Diff(
            file_path=current_file.path,
            file_type=current_file.file_type,
            change_type=ChangeType.update,
            diff_content=diff_content,
        )

    @staticmethod
    def _calculate_text_diff(previous_content: bytes, current_content: bytes) -> str:
        prev_lines = previous_content.decode("utf-8", errors="replace").splitlines(keepends=True)
        curr_lines = current_content.decode("utf-8", errors="replace").splitlines(keepends=True)

        diff = list(unified_diff(prev_lines, curr_lines, fromfile="previous", tofile="current"))
        return "".join(diff) if diff else ""

    @staticmethod
    def summarize_changes(
        changes: Changes, current_files: dict[str, FileMetadata]
    ) -> dict[ChangeType, dict[FileType, int]]:
        summary = {ct: {ft: 0 for ft in FileType} for ct in ChangeType}

        for change_type in ChangeType:
            for file_path in changes.changes[change_type]:
                file_type = current_files[file_path].file_type if file_path in current_files else FileType.OTHER
                summary[change_type][file_type] += 1

        return summary
