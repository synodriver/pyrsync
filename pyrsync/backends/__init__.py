"""
Copyright (c) 2008-2021 synodriver <synodriver@gmail.com>
"""
import os
import platform

impl = platform.python_implementation()


def _should_use_cffi() -> bool:
    ev = os.getenv("RSYNC_USE_CFFI")
    if ev is not None:
        return True
    if impl == "CPython":
        return False
    else:
        return True


if not _should_use_cffi():
    from pyrsync.backends.cython import delta, get_signature_args, patch, signature
else:
    from pyrsync.backends.cffi import delta, get_signature_args, patch, signature
