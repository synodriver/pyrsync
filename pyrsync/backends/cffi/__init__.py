"""
Copyright (c) 2008-2021 synodriver <synodriver@gmail.com>
"""
from pyrsync.backends.cffi._rsync import ffi, lib


class LibrsyncError(Exception):
    def __init__(self, result):
        self.code = result

    def __str__(self):
        if self.code == lib.RS_RUNNING:
            return "RS_RUNNING"
        elif self.code == lib.RS_TEST_SKIPPED:
            return "RS_TEST_SKIPPED"
        elif self.code == lib.RS_IO_ERROR:
            return "RS_IO_ERROR"
        elif self.code == lib.RS_SYNTAX_ERROR:
            return "RS_SYNTAX_ERROR"
        elif self.code == lib.RS_MEM_ERROR:
            return "RS_MEM_ERROR"
        elif self.code == lib.RS_INPUT_ENDED:
            return "RS_INPUT_ENDED"
        elif self.code == lib.RS_BAD_MAGIC:
            return "RS_BAD_MAGIC"
        elif self.code == lib.RS_UNIMPLEMENTED:
            return "RS_UNIMPLEMENTED"
        elif self.code == lib.RS_CORRUPT:
            return "RS_CORRUPT"
        elif self.code == lib.RS_INTERNAL_ERROR:
            return "RS_INTERNAL_ERROR"
        elif self.code == lib.RS_PARAM_ERROR:
            return "RS_PARAM_ERROR"


RS_JOB_BLOCKSIZE = 65535

RS_DELTA_MAGIC = lib.RS_DELTA_MAGIC
RS_MD4_SIG_MAGIC = lib.RS_MD4_SIG_MAGIC
RS_BLAKE2_SIG_MAGIC = lib.RS_BLAKE2_SIG_MAGIC
RS_RK_MD4_SIG_MAGIC = lib.RS_RK_MD4_SIG_MAGIC
RS_RK_BLAKE2_SIG_MAGIC = lib.RS_RK_BLAKE2_SIG_MAGIC


def PyFile_Check(file) -> bool:
    if hasattr(file, "read") and hasattr(file, "write") and hasattr(file, "seek"):
        return True
    return False


class Stats:
    @staticmethod
    def from_ptr(state):
        self = Stats.__new__(Stats)
        self.state = state
        return self

    @property
    def op(self):
        return ffi.string(self.state.op).decode()

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
    def sig_blocks(self):
        return self.state.sig_blocks

    @property
    def block_len(self):
        return self.state.block_len

    @property
    def in_bytes(self):
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


class Job:
    # cdef  rs_job_t * job

    @staticmethod
    def from_ptr(job):
        self = Job.__new__(Job)
        self.job = job
        return self

    def iter(self, buffer):
        result = lib.rs_job_iter(self.job, buffer)
        return result

    def statistics(self):
        state = lib.rs_job_statistics(self.job)
        return Stats.from_ptr(state)

    def execute(self, input, output=None) -> None:
        if not PyFile_Check(input):
            raise TypeError(
                "input except a file-like object, got %s" % type(input).__name__
            )
        if output is not None and not PyFile_Check(output):
            raise TypeError(
                "sigfile except a file-like object, got %s" % type(output).__name__
            )
        # cdef:
        #     rs_buffers_t buffer
        #     void * out  # sigfile buffer
        #     bytes block
        #     rs_result result
        buffer = ffi.new("rs_buffers_t*")
        out = ffi.new("char[]", RS_JOB_BLOCKSIZE)
        if not out:
            raise MemoryError
        while True:
            block = input.read(RS_JOB_BLOCKSIZE)  # type: bytes
            buffer.next_in = ffi.from_buffer(block)
            buffer.avail_in = len(block)
            buffer.eof_in = not block
            buffer.next_out = out
            buffer.avail_out = RS_JOB_BLOCKSIZE
            result = self.iter(buffer)
            if output is not None:
                output.write(
                    ffi.unpack(
                        out, RS_JOB_BLOCKSIZE - buffer.avail_out
                    )
                )
            if result == lib.RS_DONE:
                break
            elif result != lib.RS_BLOCKED:
                raise LibrsyncError(result)
            if buffer.avail_in > 0:
                # There is data left in the input buffer, librsync did not consume
                # all of it. Rewind the file a bit so we include that data in our
                # next read. It would be better to simply tack data to the end of
                # this buffer, but that is very difficult in Python.
                input.seek(input.tell() - buffer.avail_in)

    def __del__(self):
        if self.job:
            lib.rs_job_free(self.job)
        self.job = ffi.NULL


def get_signature_args(
    old_fsize: int, magic: int = 0, block_len: int = 0, strong_len: int = 0
) -> tuple:
    c_magic = ffi.new("rs_magic_number*")
    c_magic[0] = magic
    c_block_len = ffi.new("size_t*")
    c_block_len[0] = block_len
    c_strong_len = ffi.new("size_t*")
    c_strong_len[0] = strong_len
    result = lib.rs_sig_args(old_fsize, c_magic, c_block_len, c_strong_len)
    if result != lib.RS_DONE:
        raise LibrsyncError(result)
    return c_magic[0], c_block_len[0], c_strong_len[0]


def signature(
    input,
    output,
    strong_len: int,
    sig_magic: int,
    block_size: int = lib.RS_DEFAULT_BLOCK_LEN,
) -> None:
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
    # cdef rs_job_t * c_job
    # with nogil:
    c_job = lib.rs_sig_begin(block_size, strong_len, sig_magic)
    job = Job.from_ptr(c_job)
    job.execute(input, output)


def delta(input, sigfile, output) -> None:
    """
    Create a delta for the file input using the signature read from sigfile. The delta
    will be written to  output.
    :param input:
    :param sigfile:
    :param output: delta file
    :return:
    """
    # cdef:
    #     rs_signature_t* sig
    #     rs_job_t * c_job = rs_loadsig_begin(&sig)
    #     Job job
    #     rs_result result
    sig = ffi.new("rs_signature_t**")
    c_job = lib.rs_loadsig_begin(sig)
    try:
        job = Job.from_ptr(c_job)
        job.execute(sigfile)
        result = lib.rs_build_hash_table(sig[0])
        if result != lib.RS_DONE:
            raise LibrsyncError(result)
        c_job = lib.rs_delta_begin(sig[0])
        job = Job.from_ptr(c_job)
        return job.execute(input, output)
    finally:
        lib.rs_free_sumset(sig[0])


@ffi.def_extern()
def read_cb(opaque, pos, len_, buf):
    args = ffi.cast("input_args*", opaque)
    input = ffi.from_handle(args.file)
    input.seek(pos)
    block = input.read(len_[0])  # type: bytes
    block_size: int = len(block)  # fixme: why block is bytes but can't len_
    if block_size > args.len_:
        temp = lib.realloc(args.buffer, block_size)
        if temp == ffi.NULL:
            raise MemoryError
        args.buffer = ffi.cast("char*", temp)
        args.len_ = block_size

    len_[0] = block_size
    ffi.memmove(args.buffer, block, block_size)
    ffi.cast("char**", buf)[0] = args.buffer
    return lib.RS_DONE


def patch(input, delta, output):
    """
    Patch the file  input using the delta . The patched file will be written to
    output.
    :param input:
    :param delta:
    :param output:
    :return:
    """
    # cdef input_args args
    args = ffi.new("input_args*")
    handle = ffi.new_handle(input)  # catch you! keep cdata alive
    args.file = handle
    args.buffer = ffi.NULL
    args.len_ = 0
    # cdef rs_job_t * c_job
    c_job = lib.rs_patch_begin(lib.read_cb, ffi.cast("void*", args))
    job = Job.from_ptr(c_job)
    try:
        job.execute(delta, output)
    finally:
        lib.free(args.buffer)
