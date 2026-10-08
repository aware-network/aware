import os

from aware_file_system.filters.base import Filter


class Size(Filter):
    max_size: int

    def should_include(self, file_path: str) -> bool:
        file_size = os.path.getsize(file_path)
        return file_size > 0 and file_size <= self.max_size


class Depth(Filter):
    max_depth: int
    root_path: str

    def should_include(self, file_path: str) -> bool:
        relative_path = os.path.relpath(file_path, self.root_path)
        return relative_path.count(os.sep) <= self.max_depth
