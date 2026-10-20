"""Mechanical namespace-fragment build; never imports customer/runtime code."""

import re
import stat
from pathlib import Path

from hatchling.builders.config import BuilderConfig
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class NamespaceFragmentHook(BuildHookInterface[BuilderConfig]):
    def initialize(self, version, build_data):
        # Hatch otherwise copies a parent repository's VCS exclusions into an
        # sdist. They are not part of this closed, self-contained fragment.
        for original, destination in tuple(build_data["force_include"].items()):
            if destination in {".gitignore", ".hgignore"}:
                del build_data["force_include"][original]
        names = self.config["modules"]
        if (
            type(names) is not list
            or not names
            or len(set(names)) != len(names)
            or any(
                type(name) is not str or re.fullmatch(r"[a-z_]+[.]py", name) is None
                for name in names
            )
        ):
            raise ValueError("closed namespace module inventory required")
        root = Path(self.root)
        embedded = root / "aware_workflow"
        if embedded.exists():
            if embedded.is_symlink() or not embedded.is_dir():
                raise ValueError("regular embedded namespace directory required")
            source = embedded
            if {path.name for path in source.iterdir()} != set(names):
                raise ValueError("embedded namespace inventory differs")
        else:
            source = root / "../../../ontology/runtime/python/aware_workflow"
        for name in names:
            path = source / name
            if not stat.S_ISREG(path.lstat().st_mode):
                raise ValueError("regular original module required")
            build_data["force_include"][str(path)] = "aware_workflow/" + name
