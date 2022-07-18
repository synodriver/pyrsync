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
    from pyrsync.backends.cython import (
        RS_BLAKE2_SIG_MAGIC,
        RS_DELTA_MAGIC,
        RS_MD4_SIG_MAGIC,
        RS_RK_BLAKE2_SIG_MAGIC,
        RS_RK_MD4_SIG_MAGIC,
        delta,
        get_signature_args,
        patch,
        signature,
    )
else:
    from pyrsync.backends.cffi import (
        RS_BLAKE2_SIG_MAGIC,
        RS_DELTA_MAGIC,
        RS_MD4_SIG_MAGIC,
        RS_RK_BLAKE2_SIG_MAGIC,
        RS_RK_MD4_SIG_MAGIC,
        delta,
        get_signature_args,
        patch,
        signature,
    )
