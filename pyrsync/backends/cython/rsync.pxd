# cython: language_level=3
# cython: cdivision=True
from libc.stdint cimport intmax_t, uint8_t, uint32_t
from libc.stdio cimport FILE
from libc.time cimport time_t


cdef extern from "librsync.h" nogil:
    extern char rs_librsync_version[]
    ctypedef uint8_t rs_byte_t
    ctypedef intmax_t rs_long_t
    ctypedef enum rs_magic_number:
        RS_DELTA_MAGIC
        RS_MD4_SIG_MAGIC
        RS_BLAKE2_SIG_MAGIC
        RS_RK_MD4_SIG_MAGIC
        RS_RK_BLAKE2_SIG_MAGIC
    ctypedef enum rs_loglevel:
        RS_LOG_EMERG      #     /**< System is unusable */
        RS_LOG_ALERT      #     /**< Action must be taken immediately */
        RS_LOG_CRIT      #     /**< Critical conditions */
        RS_LOG_ERR        #     /**< Error conditions */
        RS_LOG_WARNING    #     /**< Warning conditions */
        RS_LOG_NOTICE    #     /**< Normal but significant condition */
        RS_LOG_INFO      #     /**< Informational */
        RS_LOG_DEBUG      #     /**< Debug-level messages */
    ctypedef void rs_trace_fn_t(rs_loglevel level, char *msg)
    void rs_trace_set_level(rs_loglevel level)
    void rs_trace_to(rs_trace_fn_t *)
    void rs_trace_stderr(rs_loglevel level, char * msg)
    int rs_supports_trace()
    void rs_hexify(char *to_buf, void * from_buf, int from_len)
    size_t rs_unbase64(char *s)
    void rs_base64(unsigned char * buf, int n, char * out)
    ctypedef enum rs_result:
        RS_DONE          #   /**< Completed successfully. */
        RS_BLOCKED        #   /**< Blocked waiting for more data. */
        RS_RUNNING        #   /**< The job is still running, and not yet
                               #    * finished or blocked. (This value should
                               #    * never be seen by the application.) */
        RS_TEST_SKIPPED    #   /**< Test neither passed or failed. */
        RS_IO_ERROR      #   /**< Error in input or network IO. */
        RS_SYNTAX_ERROR   #   /**< Command line syntax error. */
        RS_MEM_ERROR      #   /**< Out of memory. */
        RS_INPUT_ENDED    #   /**< Unexpected end of input input, perhaps due
                               #    * to a truncated input or dropped network
                               #    * connection. */
        RS_BAD_MAGIC     #   /**< Bad magic number at start of stream.
                               #    * Probably not a librsync input, or possibly
                               #    * the wrong kind of input or from an
                               #    * incompatible library version. */
        RS_UNIMPLEMENTED  #   /**< Author is lazy. */
        RS_CORRUPT     #   /**< Unbelievable value in stream. */
        RS_INTERNAL_ERROR  #   /**< Probably a library bug. */
        RS_PARAM_ERROR   #   /**< Bad value passed in to library, probably
                               #* an application bug. */
    char *rs_strerror(rs_result r)

    ctypedef struct rs_stats_t:
        char  *op           #  /**< Human-readable name of current operation.
                                  #   * For example, "delta". */
        int lit_cmds             #  /**< Number of literal commands. */
        rs_long_t lit_bytes      #  /**< Number of literal bytes. */
        rs_long_t lit_cmdbytes   #  /**< Number of bytes used in literal command
                                  #   * headers. */

        rs_long_t copy_cmds, copy_bytes, copy_cmdbytes
        rs_long_t sig_cmds, sig_bytes
        int false_matches

        rs_long_t sig_blocks   #    /**< Number of blocks described by the * signature. */

        size_t block_len

        rs_long_t in_bytes        #   /**< Total bytes read from input. */
        rs_long_t out_bytes     #     /**< Total bytes written to sigfile. */

        time_t start, end
    ctypedef struct rs_mdfour_t
    extern const int RS_MD4_SUM_LENGTH, RS_BLAKE2_SUM_LENGTH
    int  RS_MAX_STRONG_SUM_LENGTH
    ctypedef uint32_t rs_weak_sum_t
    ctypedef unsigned char* rs_strong_sum_t
    void rs_mdfour(unsigned char *out, void *in_, size_t n)
    void rs_mdfour_begin(rs_mdfour_t *md)
    void rs_mdfour_update(rs_mdfour_t *md, void * in_void, size_t  n)
    void rs_mdfour_result(rs_mdfour_t *md, unsigned char *out)
    char *rs_format_stats(rs_stats_t * stats, char * buf, size_t size )
    int rs_log_stats(rs_stats_t * stats)
    ctypedef struct rs_signature_t

    void rs_signature_log_stats(rs_signature_t *sig)
    void rs_free_sumset(rs_signature_t *sig)
    void rs_sumset_dump(rs_signature_t *sig)
    ctypedef struct rs_buffers_t:
        char *next_in
        size_t avail_in
        int eof_in
        char *next_out
        size_t avail_out
    int RS_DEFAULT_BLOCK_LEN
    int RS_DEFAULT_MIN_STRONG_LEN
    ctypedef struct rs_job_t

    rs_result rs_job_iter(rs_job_t *job, rs_buffers_t *buffers)
    ctypedef rs_result rs_driven_cb(rs_job_t *job, rs_buffers_t *buf,
                 void *opaque)

    rs_result rs_job_drive(rs_job_t *job, rs_buffers_t *buf,
                                           rs_driven_cb in_cb, void *in_opaque,
                                           rs_driven_cb out_cb, void *out_opaque)
    rs_stats_t *rs_job_statistics(rs_job_t *job)
    rs_result rs_job_free(rs_job_t *)
    rs_result rs_sig_args(rs_long_t old_fsize,
                          rs_magic_number * magic,
                          size_t *block_len, size_t *strong_len)

    rs_job_t *rs_sig_begin(size_t block_len, size_t strong_len,
                           rs_magic_number sig_magic)

    rs_job_t *rs_delta_begin(rs_signature_t *)
    rs_job_t *rs_loadsig_begin(rs_signature_t **)
    rs_result rs_build_hash_table(rs_signature_t *sums)
    ctypedef rs_result rs_copy_cb(void *opaque, rs_long_t pos, size_t *len,
                         void ** buf)  except * with gil
    rs_job_t *rs_patch_begin(rs_copy_cb * copy_cb, void *copy_arg)
    FILE *rs_file_open(char * filename, char  * mode, int force )
    int rs_file_close(FILE *file)
    rs_long_t rs_file_size(FILE *file)
    rs_result rs_file_copy_cb(void *arg, rs_long_t pos, size_t *len,
                              void ** buf)
    extern int rs_inbuflen, rs_outbuflen
    rs_result rs_sig_file(FILE *old_file, FILE *sig_file,
                                          size_t block_len, size_t strong_len,
                                          rs_magic_number sig_magic,
                                          rs_stats_t *stats)
    rs_result rs_loadsig_file(FILE *sig_file,
                              rs_signature_t ** sumset,
                              rs_stats_t *stats)
    rs_result rs_delta_file(rs_signature_t *, FILE *new_file,
                  FILE *delta_file, rs_stats_t *)
    rs_result rs_patch_file(FILE *basis_file, FILE *delta_file,
                            FILE *new_file, rs_stats_t *)

cdef extern from "job.h" nogil:
    rs_job_t *rs_job_new(const char *, rs_result (*statefn)(rs_job_t *))