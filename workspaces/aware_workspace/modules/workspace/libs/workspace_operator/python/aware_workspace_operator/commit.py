"""Compatibility import of the one original writer, now owned by Workspace FS.

Keep legacy callers and monkeypatch points on the same module object during
semantic caller migration. No writer body or foreign authority lives here.
"""

import sys

from aware_workspace_fs_adapter import git_writer

sys.modules[__name__] = git_writer
