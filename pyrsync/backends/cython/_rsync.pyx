# cython: language_level=3
# cython: cdivision=True
cimport cython
from cpython.bytes cimport (PyBytes_AS_STRING, PyBytes_FromStringAndSize,
                            PyBytes_GET_SIZE)
from cpython.mem cimport PyMem_Free, PyMem_Malloc, PyMem_Realloc
from cpython.object cimport PyObject, PyObject_HasAttrString
from libc.stdint cimport uint8_t
from libc.string cimport memcpy

from pyrsync.backends.cython.rsync cimport RS_BAD_MAGIC
from pyrsync.backends.cython.\
    rsync cimport RS_BLAKE2_SIG_MAGIC as C_RS_BLAKE2_SIG_MAGIC
from pyrsync.backends.cython.rsync cimport (RS_BLOCKED, RS_CORRUPT,
                                            RS_DEFAULT_BLOCK_LEN)
from pyrsync.backends.cython.rsync cimport RS_DELTA_MAGIC as C_RS_DELTA_MAGIC
from pyrsync.backends.cython.rsync cimport (RS_DONE, RS_INPUT_ENDED,
                                            RS_INTERNAL_ERROR, RS_IO_ERROR)
from pyrsync.backends.cython.\
    rsync cimport RS_MD4_SIG_MAGIC as C_RS_MD4_SIG_MAGIC
from pyrsync.backends.cython.rsync cimport RS_MEM_ERROR, RS_PARAM_ERROR
from pyrsync.backends.cython.\
    rsync cimport RS_RK_BLAKE2_SIG_MAGIC as C_RS_RK_BLAKE2_SIG_MAGIC
from pyrsync.backends.cython.\
    rsync cimport RS_RK_MD4_SIG_MAGIC as C_RS_RK_MD4_SIG_MAGIC
from pyrsync.backends.cython.rsync cimport (RS_RUNNING, RS_SYNTAX_ERROR,
                                            RS_TEST_SKIPPED, RS_UNIMPLEMENTED,
                                            rs_buffers_t, rs_build_hash_table,
                                            rs_delta_begin, rs_free_sumset,
                                            rs_job_free, rs_job_iter,
                                            rs_job_statistics, rs_job_t,
                                            rs_loadsig_begin, rs_long_t,
                                            rs_magic_number, rs_patch_begin,
                                            rs_result, rs_sig_args,
                                            rs_sig_begin, rs_signature_t,
                                            rs_stats_t)


class LibrsyncError(Exception):
    def __init__(self, result):
        self.code = result

    def __str__(self):
        if self.code == RS_RUNNING:
            return "RS_RUNNING"
        elif self.code == RS_TEST_SKIPPED:
            return "RS_TEST_SKIPPED"
        elif self.code == RS_IO_ERROR:
            return "RS_IO_ERROR"
        elif self.code == RS_SYNTAX_ERROR:
            return "RS_SYNTAX_ERROR"
        elif self.code == RS_MEM_ERROR:
            return "RS_MEM_ERROR"
        elif self.code == RS_INPUT_ENDED:
            return "RS_INPUT_ENDED"
        elif self.code == RS_BAD_MAGIC:
            return "RS_BAD_MAGIC"
        elif self.code == RS_UNIMPLEMENTED:
            return "RS_UNIMPLEMENTED"
        elif self.code == RS_CORRUPT:
            return "RS_CORRUPT"
        elif self.code == RS_INTERNAL_ERROR:
            return "RS_INTERNAL_ERROR"
        elif self.code == RS_PARAM_ERROR:
            return "RS_PARAM_ERROR"


RS_JOB_BLOCKSIZE = 65535

RS_DELTA_MAGIC = C_RS_DELTA_MAGIC
RS_MD4_SIG_MAGIC = C_RS_MD4_SIG_MAGIC
RS_BLAKE2_SIG_MAGIC = C_RS_BLAKE2_SIG_MAGIC
RS_RK_MD4_SIG_MAGIC = C_RS_RK_MD4_SIG_MAGIC
RS_RK_BLAKE2_SIG_MAGIC= C_RS_RK_BLAKE2_SIG_MAGIC

cdef inline uint8_t PyFile_Check(object file):
    if PyObject_HasAttrString(file, "read") and PyObject_HasAttrString(file, "write") and PyObject_HasAttrString(file,
                                                                                                                 "seek"):
        return 1
    return 0
# copyed sthing from https://github.com/smartfile/python-librsync/blob/master/librsync/__init__.py
@cython.freelist(8)
@cython.final
@cython.no_gc
cdef class Stats:
    cdef rs_stats_t * state

    @staticmethod
    cdef inline Stats from_ptr(rs_stats_t * state):
        cdef Stats self = Stats.__new__(Stats)
        self.state = state
        return self

    @property
    def op(self):
        return (<bytes>self.state.op).decode()

    @property
    def lit_cmds(self):
        return self.state.lit_cmds
    @property
    def lit_bytes(self):
        return self.state.lit_bytes

    @property
    def lit_cmdbytes(self):
        return self.state.lit_cmdbytes

    @property
    def copy_cmds(self):
        return self.state.copy_cmds

    @property
    def copy_bytes(self):
        return self.state.copy_bytes
    @property
    def copy_cmdbytes(self):
        return self.state.copy_cmdbytes
    @property
    def sig_cmds(self):
        return self.state.sig_cmds
    @property
    def sig_bytes(self):
        return self.state.sig_bytes
    @property
    def false_matches(self):
        return self.state.false_matches
    @property
    def sig_blocks (self):
        return self.state.sig_blocks
    @property
    def block_len(self):
        return self.state.block_len
    @property
    def in_bytes  (self):
        return self.state.in_bytes
    @property
    def out_bytes(self):
        return self.state.out_bytes
    @property
    def start(self):
        return self.state.start

    @property
    def end(self):
        return self.state.end

@cython.freelist(8)
@cython.final
@cython.no_gc
@cython.internal
cdef class Job:
    cdef  rs_job_t * job

    @staticmethod
    cdef inline Job from_ptr(rs_job_t * job):
        cdef Job self = Job.__new__(Job)
        self.job = job
        return self

    cdef inline rs_result iter(self, rs_buffers_t * buffer):
        cdef rs_result result
        with nogil:
            result = rs_job_iter(self.job, buffer)
        return result

    cpdef inline Stats statistics(self):
        cdef rs_stats_t * state = <rs_stats_t *>rs_job_statistics(self.job)
        return Stats.from_ptr(state)

    cpdef inline int execute(self, object input, object output = None) except -1:
        if not PyFile_Check(input):
            raise TypeError("input except a file-like object, got %s" % type(input).__name__)
        if output is not None and not PyFile_Check(output):
            raise TypeError("sigfile except a file-like object, got %s" % type(output).__name__)
        cdef:
            rs_buffers_t buffer
            void * out  # sigfile buffer
            bytes block
            rs_result result

        out = PyMem_Malloc(RS_JOB_BLOCKSIZE)
        if not out:
            raise MemoryError
        try:
            while True:
                block = input.read(RS_JOB_BLOCKSIZE)  # type: bytes
                buffer.next_in = PyBytes_AS_STRING(block)
                buffer.avail_in = <size_t> PyBytes_GET_SIZE(block)
                buffer.eof_in = not block
                buffer.next_out = <char *> out
                buffer.avail_out = <size_t> RS_JOB_BLOCKSIZE
                result = self.iter(&buffer)
                if output is not None:
                    output.write(
                        PyBytes_FromStringAndSize(<char *> out, <Py_ssize_t> (RS_JOB_BLOCKSIZE - buffer.avail_out)))
                if result == RS_DONE:
                    break
                elif result != RS_BLOCKED:
                    raise LibrsyncError(result)
                if buffer.avail_in > 0:
                    # There is data left in the input buffer, librsync did not consume
                    # all of it. Rewind the file a bit so we include that data in our
                    # next read. It would be better to simply tack data to the end of
                    # this buffer, but that is very difficult in Python.
                    input.seek(input.tell() - buffer.avail_in)
        finally:
            PyMem_Free(out)
        return 0

    def __dealloc__(self):
        if self.job:
            rs_job_free(self.job)
        self.job = NULL

cpdef inline tuple get_signature_args(rs_long_t old_fsize, int magic = 0, size_t block_len = 0, size_t strong_len= 0):
    cdef:
        rs_result result
        rs_magic_number c_magic = <rs_magic_number>magic
        # size_t cblock_len, strong_len
    with nogil:
        result = rs_sig_args(old_fsize, &c_magic, &block_len, &strong_len)
    if result != RS_DONE:
        raise LibrsyncError(result)
    return c_magic, block_len, strong_len

cpdef inline signature(object input, object output, size_t strong_len, rs_magic_number sig_magic,
                           size_t block_size=RS_DEFAULT_BLOCK_LEN):
    """
     Generate a signature for the file input. The signature will be written to output.
    You can specify the size of the blocks using the optional `block_size` parameter.
    :param input: 
    :param output: 
    :param strong_len: 
    :param sig_magic: 
    :param block_size: 
    :return: 
    """
    cdef rs_job_t * c_job
    with nogil:
        c_job = rs_sig_begin(block_size, strong_len, sig_magic)
    cdef Job job = Job.from_ptr(c_job)
    job.execute(input, output)

cpdef inline delta(object input, object sigfile, object output):
    """
    Create a delta for the file input using the signature read from sigfile. The delta
    will be written to  output.
    :param input: 
    :param sigfile: 
    :param output: delta file
    :return: 
    """
    cdef:
        rs_signature_t* sig
        rs_job_t * c_job = rs_loadsig_begin(&sig)
        Job job
        rs_result result
    try:
        job = Job.from_ptr(c_job)
        job.execute(sigfile)
        with nogil:
            result = rs_build_hash_table(sig)
        if result != RS_DONE:
            raise LibrsyncError(result)
        with nogil:
            c_job = rs_delta_begin(sig)
        job = Job.from_ptr(c_job)
        return job.execute(input, output)
    finally:
        rs_free_sumset(sig)

cdef struct input_args:
    PyObject *file
    char* buffer
    Py_ssize_t len

cdef rs_result read_cb(void *opaque, rs_long_t pos, size_t *len, void ** buf) except * with gil:
    cdef  input_args* args = <input_args*>opaque
    input = <object>args.file
    input.seek(pos)
    block = input.read(len[0]) # type: bytes
    cdef Py_ssize_t block_size = PyBytes_GET_SIZE(block)
    cdef void* temp
    if block_size > args.len:
        temp = PyMem_Realloc(<void*>args.buffer, <size_t>block_size)
        if temp==NULL:
            raise MemoryError
        args.buffer = <char*>temp
        args.len = block_size

    len[0] = <size_t>block_size
    memcpy(args.buffer, PyBytes_AS_STRING(block), <size_t>block_size)
    (<char**> buf)[0] = args.buffer
    return RS_DONE


cpdef inline patch(object input, object delta, object output):
    """
    Patch the file  input using the delta . The patched file will be written to
    output.
    :param input: 
    :param delta: 
    :param output: 
    :return: 
    """
    cdef input_args args
    args.file= <PyObject *>input
    args.buffer = NULL
    args.len = 0
    cdef rs_job_t * c_job
    with nogil:
        c_job = rs_patch_begin(read_cb, <void*>&args)
    cdef Job job = Job.from_ptr(c_job)
    try:
        job.execute(delta, output)
    finally:
        PyMem_Free(args.buffer)
