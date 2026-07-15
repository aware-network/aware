from typing import Dict

from aware_file_system.models import FileMetadata, Changes, ChangeType


class Detector:
    @staticmethod
    def detect_changes(previous_state: Dict[str, FileMetadata], current_state: Dict[str, FileMetadata]) -> Changes:
        changes = Changes()
        current_files = set(current_state.keys())
        previous_files = set(previous_state.keys())

        changes.changes[ChangeType.create] = list(current_files - previous_files)
        changes.changes[ChangeType.delete] = list(previous_files - current_files)
        changes.changes[ChangeType.update] = [
            file_path
            for file_path in current_files & previous_files
            if current_state[file_path].is_modified(previous_state[file_path])
        ]

        return changes
