from platform import system
from setuptools import setup, Extension
import sys

# Define the extension module
binding_module = Extension(
    name="_binding",
    sources=[
        "tree_sitter_dart/binding.c",
        "tree_sitter_dart/src/parser.c",
        "tree_sitter_dart/src/scanner.c",
    ],
    extra_compile_args=(
        [
            "-std=c11",
        ]
        if system() != "Windows"
        else [
            "/std:c11",
            "/utf-8",
        ]
    ),
    define_macros=[("Py_LIMITED_API", "0x03080000"), ("PY_SSIZE_T_CLEAN", None)],
    include_dirs=["tree_sitter_dart/src"],
    py_limited_api=True,
)

# If no arguments are provided (which happens with Poetry),
# inject the build_ext --inplace command
if len(sys.argv) == 1:
    sys.argv.extend(["build_ext", "--inplace"])

setup(
    name="tree-sitter-dart",
    version="0.0.1",
    packages=["tree_sitter_dart"],
    package_data={
        "tree_sitter_dart": ["*.pyi", "py.typed", "queries/*.scm"],
    },
    ext_package="tree_sitter_dart",
    ext_modules=[binding_module],
    python_requires=">=3.12",
    zip_safe=False,
)
