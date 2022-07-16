# cython: language_level=3
# cython: cdivision=True
cimport cython
from cpython.bytes cimport (PyBytes_AS_STRING, PyBytes_FromStringAndSize,
                            PyBytes_GET_SIZE)
from cpython.mem cimport PyMem_Malloc

from pyrsync.backends.cython.rsync cimport *


class LibrsyncError(Exception):
    def __init__(self, result):
        self.code = result

RS_JOB_BLOCKSIZE = 65535

# copyed sthing from https://github.com/smartfile/python-librsync/blob/master/librsync/__init__.py

@cython.freelist(8)
@cython.final
@cython.no_gc
cdef class Job:
    cdef  rs_job_t* job

    @staticmethod
    cdef inline Job from_ptr(rs_job_t* job):
        cdef Job self = Job.__new__(Job)
        self.job = job
        return self

    cdef inline rs_result iter(self, rs_buffers_t* buffer):
        cdef rs_result result = rs_job_iter(self.job, buffer)
        return result

    cpdef inline int execute(self, object input, object output):
        cdef:
            rs_buffers_t buffer
            void* out  # output buffer
            bytes block
            rs_result result

        out = PyMem_Malloc(RS_JOB_BLOCKSIZE)
        if not out:
            raise
        while True:
            block = input.read(RS_JOB_BLOCKSIZE) # type: bytes
            buffer.next_in = PyBytes_AS_STRING(block)
            buffer.avail_in = <size_t>PyBytes_GET_SIZE(block)
            buffer.eof_in = bool(block)
            buffer.next_out = <char*>out
            buffer.avail_out = <size_t>RS_JOB_BLOCKSIZE
            result = self.iter(&buffer)
            output.write(PyBytes_FromStringAndSize(<char*>out, <Py_ssize_t>(RS_JOB_BLOCKSIZE - buffer.avail_out)))
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
        return 0

    def __dealloc__(self):
        if self.job:
            rs_job_free(self.job)
        self.job = NULL

