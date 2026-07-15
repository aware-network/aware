from platform import system
from setuptools import setup, Extension
import sys

# Define the extension module
binding_module = Extension(
    name="_binding",
    sources=[
        "tree_sitter_python/binding.c",
        "tree_sitter_python/src/parser.c",
        "tree_sitter_python/src/scanner.c",
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
    include_dirs=["tree_sitter_python/src"],
    py_limited_api=True,
)

# If no arguments are provided (which happens with Poetry),
# inject the build_ext --inplace command
if len(sys.argv) == 1:
    sys.argv.extend(["build_ext", "--inplace"])

setup(
    name="tree-sitter-python",
    version="0.23.6",
    packages=["tree_sitter_python"],
    package_data={
        "tree_sitter_python": ["*.pyi", "py.typed", "queries/*.scm"],
    },
    ext_modules=[binding_module],
    ext_package="tree_sitter_python",
    python_requires=">=3.12",
    zip_safe=False,
)
