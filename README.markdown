<h1 align="center"><i>✨ pyrsync ✨ </i></h1>

<h3 align="center">The python binding for <a href="https://github.com/librsync/librsync">librsync</a> </h3>

[![pypi](https://img.shields.io/pypi/v/python-rsync.svg)](https://pypi.org/project/python-rsync/)
![python](https://img.shields.io/pypi/pyversions/python-rsync)
![implementation](https://img.shields.io/pypi/implementation/python-rsync)
![wheel](https://img.shields.io/pypi/wheel/python-rsync)
![license](https://img.shields.io/github/license/synodriver/pyrsync.svg)
![action](https://img.shields.io/github/workflow/status/synodriver/pyrsync/build%20wheel)

## Install
```bash
pip install python-rsync
```


## Usage
```python
from io import BytesIO
from pyrsync import delta, get_signature_args, signature, patch

s = b"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" * 50
d = b"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" * 50 + b"2"
src = BytesIO(s)
dst = BytesIO(d)
magic, block_len, strong_len = get_signature_args(len(s))
sig = BytesIO()
signature(dst, sig, strong_len, magic, block_len)  # sig由dst产生
dst.seek(0, 0)
sig.seek(0, 0)
_delta = BytesIO()
delta(src, sig, _delta)  # src和sig对比产生delta
src.seek(0, 0)
_delta.seek(0, 0)
out = BytesIO()
patch(dst, _delta, out)
assert out.getvalue() ==  src.getvalue()
```

## Public functions
```python
from typing import IO

class LibrsyncError(Exception):
    code: Any
    def __init__(self, result) -> None: ...

RS_JOB_BLOCKSIZE: int
RS_DELTA_MAGIC: int
RS_MD4_SIG_MAGIC: int
RS_BLAKE2_SIG_MAGIC: int
RS_RK_MD4_SIG_MAGIC: int
RS_RK_BLAKE2_SIG_MAGIC: int

def get_signature_args(old_fsize: int, magic: int = 0, block_len: int = 0, strong_len: int = 0) -> tuple: ...
def signature(input:IO, output:IO, strong_len: int, sig_magic: int, block_size: int = ...) -> None: ...
def delta(input:IO, sigfile:IO, output) -> None: ...
def patch(input:IO, delta:IO, output) -> None: ...
```


### Compile
```
python -m pip install setuptools wheel cython cffi
git clone https://github.com/synodriver/pyrsync
cd pyrsync
git submodule update --init --recursive
python setup.py bdist_wheel --use-cython --use-cffi
```

### Backend Choose
Use ```RSYNC_USE_CFFI``` env var to use cffi backend, otherwise it's depend on your python implementation.
