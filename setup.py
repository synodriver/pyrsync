# -*- coding: utf-8 -*-
import os
import re
import sys
from collections import defaultdict

try:
    from Cython.Build import cythonize
    from Cython.Compiler.Version import version as cython_version
    from packaging.version import Version
except ImportError:
    Cython = None
from setuptools import Extension, find_packages, setup
from setuptools.command.build_ext import build_ext

BUILD_ARGS = defaultdict(lambda: ["-O3", "-g0"])

for compiler, args in [
    ("msvc", ["/EHsc", "/DHUNSPELL_STATIC", "/Oi", "/O2", "/Ot"]),
    ("gcc", ["-O3", "-g0"]),
]:
    BUILD_ARGS[compiler] = args


def has_option(name: str) -> bool:
    if name in sys.argv[1:]:
        sys.argv.remove(name)
        return True
    name = name.strip("-").upper()
    if os.environ.get(name, None) is not None:
        return True
    return False


class build_ext_compiler_check(build_ext):
    def build_extensions(self):
        compiler = self.compiler.compiler_type
        args = BUILD_ARGS[compiler]
        for ext in self.extensions:
            ext.extra_compile_args = args
            if os.name == "nt":
                ext.libraries.append("ws2_32")
        super().build_extensions()


c_src = ["pyrsync/backends/cython/_rsync.pyx"]
include_dirs = []
libraries = []
extra_objects = []

if has_option("--use-lib"):
    include_dirs.extend(["./dep/src", "./dep/src/blake2"])
    libraries.append("rsync")
    extra_objects.append(r"./dep/librsync.so")
else:
    include_dirs.extend(["./dep/src", "./dep/src/blake2"])
    for root, dirs, files in os.walk("./dep/src"):
        for file in files:
            if file.endswith(".c") and "rdiff" not in file:
                c_src.append(os.path.join(root, file))

defined_macros = [("rsync_EXPORTS", None)]
if (
    sys.version_info > (3, 13, 0)
    and hasattr(sys, "_is_gil_enabled")
    and not sys._is_gil_enabled()
):
    print("build nogil")
    defined_macros.append(
        ("Py_GIL_DISABLED", "1"),
    )  # ("CYTHON_METH_FASTCALL", "1"), ("CYTHON_VECTORCALL",  1)]

extensions = [
    Extension(
        "pyrsync.backends.cython._rsync",
        c_src,
        include_dirs=include_dirs,
        # library_dirs=[r"F:\pyproject\pyrsync\dep\Debug"],
        # libraries=libraries,
        define_macros=defined_macros,
        extra_objects=extra_objects,
    ),
]
cffi_modules = ["pyrsync/backends/cffi/build.py:ffibuilder"]


def get_dis():
    with open("README.markdown", "r", encoding="utf-8") as f:
        return f.read()


def get_version() -> str:
    path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "pyrsync", "__init__.py"
    )
    with open(path, "r", encoding="utf-8") as f:
        data = f.read()
    result = re.findall(r"(?<=__version__ = \")\S+(?=\")", data)
    return result[0]


packages = find_packages(exclude=("test", "tests.*", "test*"))

compiler_directives = {
    "cdivision": True,
    "embedsignature": True,
    "boundscheck": False,
    "wraparound": False,
}


if Version(cython_version) >= Version("3.1.0a0"):
    compiler_directives["freethreading_compatible"] = True

setup_requires = []
install_requires = []
setup_kw = {}
if has_option("--use-cython"):
    print("building cython")
    setup_requires.append("cython")
    setup_kw["ext_modules"] = cythonize(
        extensions,
        compiler_directives=compiler_directives,
    )
if has_option("--use-cffi"):
    print("building cffi")
    setup_requires.append("cffi>=1.0.0")
    install_requires.append("cffi>=1.0.0")
    setup_kw["cffi_modules"] = cffi_modules


def main():
    version: str = get_version()

    dis = get_dis()
    setup(
        name="python-rsync",
        version=version,
        url="https://github.com/synodriver/pyrsync",
        packages=packages,
        keywords=["compress", "decompress"],
        description="python binding for librsync",
        long_description_content_type="text/markdown",
        long_description=dis,
        author="synodriver",
        author_email="diguohuangjiajinweijun@gmail.com",
        python_requires=">=3.6",
        setup_requires=setup_requires,
        install_requires=install_requires,
        license="BSD",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Operating System :: OS Independent",
            "License :: OSI Approved :: BSD License",
            "Programming Language :: C",
            "Programming Language :: Cython",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: Implementation :: CPython",
            "Programming Language :: Python :: Implementation :: PyPy",
        ],
        include_package_data=True,
        zip_safe=False,
        cmdclass={"build_ext": build_ext_compiler_check},
        **setup_kw
    )


if __name__ == "__main__":
    main()
