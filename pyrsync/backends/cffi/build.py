import os

from cffi import FFI

ffibuilder = FFI()

ffibuilder.cdef(
    r"""
extern char const rs_librsync_version[];

typedef uint8_t rs_byte_t;
typedef intmax_t rs_long_t;

                          /*=
                           | "The IETF already has more than enough
                           | RFCs that codify the obvious, make
                           | stupidity illegal, support truth,
                           | justice, and the IETF way, and generally
                           | demonstrate the author is a brilliant and
                           | valuable Contributor to The Standards
                           | Process."
                           |     -- Vernon Schryver
                           */

/** A uint32 magic number, emitted in bigendian/network order at the start of
 * librsync files. */
typedef enum {
    /** A delta file.
     *
     * At present, there's only one delta format.
     *
     * The four-byte literal \c "rs\x026". */
    RS_DELTA_MAGIC = 0x72730236,

    /** A signature file with MD4 signatures.
     *
     * Backward compatible with librsync < 1.0, but strongly deprecated because
     * it creates a security vulnerability on files containing partly untrusted
     * data. See <https://github.com/librsync/librsync/issues/5>.
     *
     * The four-byte literal \c "rs\x016".
     *
     * \sa rs_sig_begin() */
    RS_MD4_SIG_MAGIC = 0x72730136,

    /** A signature file using the BLAKE2 hash. Supported from librsync 1.0.
     *
     * The four-byte literal \c "rs\x017".
     *
     * \sa rs_sig_begin() */
    RS_BLAKE2_SIG_MAGIC = 0x72730137,

    /** A signature file with RabinKarp rollsum and MD4 hash.
     *
     * Uses a faster/safer rollsum, but still strongly discouraged because of
     * MD4's security vulnerability. Supported since librsync 2.2.0.
     *
     * The four-byte literal \c "rs\x01F".
     *
     * \sa rs_sig_begin() */
    RS_RK_MD4_SIG_MAGIC = 0x72730146,

    /** A signature file with RabinKarp rollsum and BLAKE2 hash.
     *
     * Uses a faster/safer rollsum together with the safer BLAKE2 hash. This is
     * the recommended default supported since librsync 2.2.0.
     *
     * The four-byte literal \c "rs\x01G".
     *
     * \sa rs_sig_begin() */
    RS_RK_BLAKE2_SIG_MAGIC = 0x72730147,

} rs_magic_number;

/** Log severity levels.
 *
 * These are the same as syslog, at least in glibc.
 *
 * \sa rs_trace_set_level() \sa \ref api_trace */
typedef enum {
    RS_LOG_EMERG = 0,           /**< System is unusable */
    RS_LOG_ALERT = 1,           /**< Action must be taken immediately */
    RS_LOG_CRIT = 2,            /**< Critical conditions */
    RS_LOG_ERR = 3,             /**< Error conditions */
    RS_LOG_WARNING = 4,         /**< Warning conditions */
    RS_LOG_NOTICE = 5,          /**< Normal but significant condition */
    RS_LOG_INFO = 6,            /**< Informational */
    RS_LOG_DEBUG = 7            /**< Debug-level messages */
} rs_loglevel;

/** Callback to write out log messages.
 *
 * \param level a syslog level.
 *
 * \param msg message to be logged.
 *
 * \sa \ref api_trace */
typedef void rs_trace_fn_t(rs_loglevel level, char const *msg);

/** Set the least important message severity that will be output.
 *
 * \sa \ref api_trace */
void rs_trace_set_level(rs_loglevel level);

/** Set trace callback.
 *
 * \sa \ref api_trace */
void rs_trace_to(rs_trace_fn_t *);

/** Default trace callback that writes to stderr.
 *
 * Implements ::rs_trace_fn_t, and may be passed to rs_trace_to().
 *
 * \sa \ref api_trace */
void rs_trace_stderr(rs_loglevel level, char const *msg);

/** Check whether the library was compiled with debugging trace.
 *
 * \returns True if the library contains trace code; otherwise false.
 *
 * If this returns false, then trying to turn trace on will achieve nothing.
 *
 * \sa \ref api_trace */
int rs_supports_trace(void);

/** Convert \p from_len bytes at \p from_buf into a hex representation in \p
 * to_buf, which must be twice as long plus one byte for the null terminator. */
void rs_hexify(char *to_buf, void const *from_buf,
                               int from_len);

/** Decode a base64 buffer in place.
 *
 * \returns The number of binary bytes. */
size_t rs_unbase64(char *s);

/** Encode a buffer as base64. */
void rs_base64(unsigned char const *buf, int n, char *out);

/** Return codes from nonblocking rsync operations.
 *
 * \sa rs_strerror() \sa api_callbacks */
typedef enum rs_result {
    RS_DONE = 0,                /**< Completed successfully. */
    RS_BLOCKED = 1,             /**< Blocked waiting for more data. */
    RS_RUNNING = 2,             /**< The job is still running, and not yet
                                 * finished or blocked. (This value should
                                 * never be seen by the application.) */
    RS_TEST_SKIPPED = 77,       /**< Test neither passed or failed. */
    RS_IO_ERROR = 100,          /**< Error in file or network IO. */
    RS_SYNTAX_ERROR = 101,      /**< Command line syntax error. */
    RS_MEM_ERROR = 102,         /**< Out of memory. */
    RS_INPUT_ENDED = 103,       /**< Unexpected end of input file, perhaps due
                                 * to a truncated file or dropped network
                                 * connection. */
    RS_BAD_MAGIC = 104,         /**< Bad magic number at start of stream.
                                 * Probably not a librsync file, or possibly
                                 * the wrong kind of file or from an
                                 * incompatible library version. */
    RS_UNIMPLEMENTED = 105,     /**< Author is lazy. */
    RS_CORRUPT = 106,           /**< Unbelievable value in stream. */
    RS_INTERNAL_ERROR = 107,    /**< Probably a library bug. */
    RS_PARAM_ERROR = 108        /**< Bad value passed in to library, probably
                                 * an application bug. */
} rs_result;

/** Return an English description of a ::rs_result value. */
char const *rs_strerror(rs_result r);

/** Performance statistics from a librsync encoding or decoding operation.
 *
 * \sa api_stats \sa rs_format_stats() \sa rs_log_stats() */
typedef struct rs_stats {
    char const *op;             /**< Human-readable name of current operation.
                                 * For example, "delta". */
    int lit_cmds;               /**< Number of literal commands. */
    rs_long_t lit_bytes;        /**< Number of literal bytes. */
    rs_long_t lit_cmdbytes;     /**< Number of bytes used in literal command
                                 * headers. */

    rs_long_t copy_cmds, copy_bytes, copy_cmdbytes;
    rs_long_t sig_cmds, sig_bytes;
    int false_matches;

    rs_long_t sig_blocks;       /**< Number of blocks described by the
                                 * signature. */

    size_t block_len;

    rs_long_t in_bytes;         /**< Total bytes read from input. */
    rs_long_t out_bytes;        /**< Total bytes written to output. */

    long start, end;
} rs_stats_t;

/** MD4 message-digest accumulator.
 *
 * \sa rs_mdfour(), rs_mdfour_begin(), rs_mdfour_update(), rs_mdfour_result() */
 struct rs_mdfour {
    unsigned int A, B, C, D;
    uint64_t totalN;
    int tail_len;
    unsigned char tail[64];
};
typedef struct rs_mdfour rs_mdfour_t;

extern const int RS_MD4_SUM_LENGTH, RS_BLAKE2_SUM_LENGTH;

#  define RS_MAX_STRONG_SUM_LENGTH 32

typedef uint32_t rs_weak_sum_t;
typedef unsigned char rs_strong_sum_t[RS_MAX_STRONG_SUM_LENGTH];

void rs_mdfour(unsigned char *out, void const *in, size_t);
void rs_mdfour_begin( /* @out@ */ rs_mdfour_t *md);

/** Feed some data into the MD4 accumulator.
 *
 * \param md MD4 accumulator.
 *
 * \param in_void Data to add.
 *
 * \param n Number of bytes fed in. */
void rs_mdfour_update(rs_mdfour_t *md, void const *in_void,
                                      size_t n);
void rs_mdfour_result(rs_mdfour_t *md, unsigned char *out);

/** Return a human-readable representation of statistics.
 *
 * The string is truncated if it does not fit. 100 characters should be
 * sufficient space.
 *
 * \param stats Statistics from an encoding or decoding operation.
 *
 * \param buf Buffer to receive result.
 *
 * \param size Size of buffer.
 *
 * \return \p buf.
 *
 * \sa \ref api_stats */
char *rs_format_stats(rs_stats_t const *stats, char *buf,
                                      size_t size);

/** Write statistics into the current log as text.
 *
 * \sa \ref api_stats \sa \ref api_trace */
int rs_log_stats(rs_stats_t const *stats);

/** The signature datastructure type. */
typedef struct rs_signature rs_signature_t;

/** Log the rs_signature_delta match stats. */
void rs_signature_log_stats(rs_signature_t const *sig);

/** Deep deallocation of checksums. */
void rs_free_sumset(rs_signature_t *);

/** Dump signatures to the log. */
void rs_sumset_dump(rs_signature_t const *);

/** Description of input and output buffers.
 *
 * On each call to ::rs_job_iter(), the caller can make available
 *
 * - #avail_in bytes of input data at #next_in
 *
 * - #avail_out bytes of output space at #next_out
 *
 * - or some of both
 *
 * Buffers must be allocated and passed in by the caller.
 *
 * On input, the buffers structure must contain the address and length of the
 * input and output buffers. The library updates these values to indicate the
 * amount of \b remaining buffer. So, on return, #avail_out is not the amount
 * of output data produced, but rather the amount of output buffer space still
 * available.
 *
 * This means that the values on return are consistent with the values on
 * entry, and suitable to be passed in on a second call, but they don't
 * directly tell you how much output data was produced.
 *
 * If the input buffer was large enough, it will be processed directly,
 * otherwise the data can be copied and accumulated into an internal buffer for
 * processing. This means using larger buffers can be much more efficient.
 *
 * Note also that if #avail_in is nonzero on return, then not all of the input
 * data has been consumed. This can happen either because it ran out of output
 * buffer space, or because it processed as much data as possible directly from
 * the input buffer and needs more input to proceed without copying into
 * internal buffers. The caller should provide more output buffer space and/or
 * pack the remaining input data into another buffer with more input before
 * calling rs_job_iter() again.
 *
 * \sa rs_job_iter() */
struct rs_buffers_s {
    /** Next input byte.
     *
     * References a pointer which on entry should point to the start of the
     * data to be encoded. Updated to point to the byte after the last one
     * consumed. */
    char *next_in;

    /** Number of bytes available at next_in.
     *
     * References the length of available input. Updated to be the number of
     * unused data bytes, which will be zero if all the input was consumed. May
     * be zero if there is no new input, but the caller just wants to drain
     * output. */
    size_t avail_in;

    /** True if there is no more data after this. */
    int eof_in;

    /** Next output byte should be put there.
     *
     * References a pointer which on entry points to the start of the output
     * buffer. Updated to point to the byte after the last one filled. */
    char *next_out;

    /** Remaining free space at next_out.
     *
     * References the size of available output buffer. Updated to the size of
     * unused output buffer. */
    size_t avail_out;
};

/** \sa ::rs_buffers_s */
typedef struct rs_buffers_s rs_buffers_t;

/** Default block length, if not determined by any other factors.
 *
 * The 2K default assumes a typical file is about 4MB and should be OK for
 * files up to 32G with more than 1GB ram. */
#  define RS_DEFAULT_BLOCK_LEN 2048

/** Default minimum strong sum length, if the filesize is unknown.
 *
 * This is conservative, and should be safe for files less than 45TB with a 2KB
 * block_len, assuming no collision attack with crafted data. */
#  define RS_DEFAULT_MIN_STRONG_LEN 12

/** Job of work to be done.
 *
 * Created by functions such as rs_sig_begin(), and then iterated over by
 * rs_job_iter().
 *
 * The contents are opaque to the application, and instances are always
 * allocated by the library.
 *
 * \sa \ref api_streaming \sa rs_job */
typedef enum {
    RS_ROLLSUM,
    RS_RABINKARP,
} weaksum_kind_t;

/** Strongsum implementations. */
typedef enum {
    RS_MD4,
    RS_BLAKE2,
} strongsum_kind_t;

/** Abstract wrapper around weaksum implementations.
 *
 * This is a polymorphic interface to the different rollsum implementations.
 *
 * Historically rollsum methods were implemented as static inline functions
 * because they were small and needed to be fast. Now that we need to call
 * different methods for different rollsum implementations, they are getting
 * more complicated. Is it better to delegate calls to the right implementation
 * using static inline switch statements, or stop inlining them and use virtual
 * method pointers? Tests suggest inlined switch statements is faster. */
 typedef struct Rollsum {
    size_t count;               /**< count of bytes included in sum */
    uint_fast16_t s1;           /**< s1 part of sum */
    uint_fast16_t s2;           /**< s2 part of sum */
} Rollsum;
typedef struct rabinkarp {
    size_t count;               /**< Count of bytes included in sum. */
    uint32_t hash;              /**< The accumulated hash value. */
    uint32_t mult;              /**< The value of RABINKARP_MULT^count. */
} rabinkarp_t;
typedef struct weaksum {
    weaksum_kind_t kind;
    union {
        Rollsum rs;
        rabinkarp_t rk;
    } sum;
} weaksum_t;
typedef rs_result rs_copy_cb(void *opaque, rs_long_t pos, size_t *len_,
                             void **buf);
struct rs_job {
    int dogtag;

    /** Human-readable job operation name. */
    const char *job_name;

    rs_buffers_t *stream;

    /** Callback for each processing step. */
    rs_result (*statefn)(struct rs_job *);

    /** Final result of processing job. Used by rs_job_s_failed(). */
    rs_result final_result;

    /* Arguments for initializing the signature used by mksum.c and readsums.c.
     */
    int sig_magic;
    int sig_block_len;
    int sig_strong_len;

    /** The size of the signature file if available. Used by loadsums.c when
     * initializing the signature to preallocate memory. */
    rs_long_t sig_fsize;

    /** Pointer to the signature that's being used by the operation. */
    rs_signature_t *signature;

    /** Flag indicating signature should be destroyed with the job. */
    int job_owns_sig;

    /** Command byte currently being processed, if any. */
    unsigned char op;

    /** The weak signature digest used by readsums.c */
    rs_weak_sum_t weak_sig;

    /** The rollsum weak signature accumulator used by delta.c */
    weaksum_t weak_sum;

    /** Lengths of expected parameters. */
    rs_long_t param1, param2;

    struct rs_prototab_ent const *cmd;
    rs_mdfour_t output_md4;

    /** Encoding statistics. */
    rs_stats_t stats;

    /** Buffer of data in the scoop. Allocation is scoop_buf[0..scoop_alloc],
     * and scoop_next[0..scoop_avail] contains data yet to be processed. */
    rs_byte_t *scoop_buf;       /**< The buffer allocation pointer. */
    rs_byte_t *scoop_next;      /**< The next data pointer. */
    size_t scoop_alloc;         /**< The buffer allocation size. */
    size_t scoop_avail;         /**< The amount of data available. */

    /** The delta scan buffer, where scan_buf[scan_pos..scan_len] is the data
     * yet to be scanned. */
    rs_byte_t *scan_buf;        /**< The delta scan buffer pointer. */
    size_t scan_len;            /**< The delta scan buffer length. */
    size_t scan_pos;            /**< The delta scan position. */

    /** If USED is >0, then buf contains that much write data to be sent out. */
    rs_byte_t write_buf[36];
    size_t write_len;

    /** If \p copy_len is >0, then that much data should be copied through
     * from the input. */
    size_t copy_len;

    /** Copy from the basis position. */
    rs_long_t basis_pos, basis_len;

    /** Callback used to copy data from the basis into the output. */
    rs_copy_cb *copy_cb;
    void *copy_arg;
};
 
 
typedef struct rs_job  rs_job_t;

/** Run a ::rs_job state machine until it blocks (::RS_BLOCKED), returns an
 * error, or completes (::RS_DONE).
 *
 * \param job Description of job state.
 *
 * \param buffers Pointer to structure describing input and output buffers.
 *
 * \return The ::rs_result that caused iteration to stop.
 *
 * \c buffers->eof_in should be true if there is no more data after what's in
 * the input buffer. The final block checksum will run across whatever's in
 * there, without trying to accumulate anything else.
 *
 * \sa \ref api_streaming */
rs_result rs_job_iter(rs_job_t *job, rs_buffers_t *buffers);

/** Type of application-supplied function for rs_job_drive().
 *
 * \sa \ref api_pull */
typedef rs_result rs_driven_cb(rs_job_t *job, rs_buffers_t *buf,
                               void *opaque);

/** Actively process a job, by making callbacks to fill and empty the buffers
 * until the job is done. */
rs_result rs_job_drive(rs_job_t *job, rs_buffers_t *buf,
                                       rs_driven_cb in_cb, void *in_opaque,
                                       rs_driven_cb out_cb, void *out_opaque);

/** Return a pointer to the statistics in a job. */
const rs_stats_t *rs_job_statistics(rs_job_t *job);

/** Deallocate job state. */
rs_result rs_job_free(rs_job_t *);

/** Get or check signature arguments for a given file size.
 *
 * This can be used to get the recommended arguments for generating a
 * signature. On calling, old_fsize should be set to the old file size or -1
 * for "unknown". The magic and block_len arguments should be set to a valid
 * value or 0 for "recommended". The strong_len input should be set to a valid
 * value, 0 for "maximum", or -1 for "miniumum". Use strong_len=0 for the best
 * protection against active hash collision attacks for the given magic type.
 * Use strong_len=-1 for the smallest signature size that is safe against
 * random hash collisions for the block_len and old_fsize. Use strong_len=20
 * for something probably good enough against attacks with smaller signatures.
 * On return the 0 or -1 input args will be set to recommended values and the
 * returned result will indicate if any inputs were invalid.
 *
 * \param old_fsize - the original file size (-1 for "unknown").
 *
 * \param *magic - the magic type to use (0 for "recommended").
 *
 * \param *block_len - the block length to use (0 for "recommended").
 *
 * \param *strong_len - the strongsum length to use (0 for "maximum", -1 for
 * "minimum").
 *
 * \return RS_DONE if all arguments are valid, otherwise an error code. */
rs_result rs_sig_args(rs_long_t old_fsize,
                                      rs_magic_number * magic,
                                      size_t *block_len, size_t *strong_len);

/** Start generating a signature.
 *
 * It's recommended you use rs_sig_args() to get the recommended arguments for
 * this based on the original file size.
 *
 * \return A new rs_job_t into which the old file data can be passed.
 *
 * \param sig_magic Signature file format to generate (0 for "recommended").
 * See ::rs_magic_number.
 *
 * \param block_len Checksum block size to use (0 for "recommended"). Larger
 * values make the signature shorter, and the delta longer.
 *
 * \param strong_len Strongsum length in bytes to use (0 for "maximum", -1 for
 * "minimum"). Smaller values make the signature shorter but increase the risk
 * of corruption from hash collisions.
 *
 * \sa rs_sig_file() */
rs_job_t *rs_sig_begin(size_t block_len, size_t strong_len,
                                       rs_magic_number sig_magic);

/** Prepare to compute a streaming delta.
 *
 * \todo Add a version of this that takes a ::rs_magic_number controlling the
 * delta format. */
rs_job_t *rs_delta_begin(rs_signature_t *);

/** Read a signature from a file into an ::rs_signature structure in memory.
 *
 * Once there, it can be used to generate a delta to a newer version of the
 * file.
 *
 * \note After loading the signatures, you must call \ref rs_build_hash_table()
 * before you can use them. */
rs_job_t *rs_loadsig_begin(rs_signature_t **);

/** Call this after loading a signature to index it.
 *
 * Use rs_free_sumset() to release it after use. */
rs_result rs_build_hash_table(rs_signature_t *sums);

/** Callback used to retrieve parts of the basis file.
 *
 * \param opaque The opaque object to execute the callback with. Often the file
 * to read from.
 *
 * \param pos Position where copying should begin.
 *
 * \param len_ On input, the amount of data that should be retrieved. Updated to
 * show how much is actually available, but should not be greater than the
 * input value.
 *
 * \param buf On input, a buffer of at least \p *len_ bytes. May be updated to
 * point to a buffer allocated by the callback if it prefers. */


/** Apply a \a delta to a \a basis file to recreate the \a new file.
 *
 * This gives you back a ::rs_job_t object, which can be cranked by calling
 * rs_job_iter() and updating the stream pointers. When finished, call
 * rs_job_free() to dispose of it.
 *
 * \param copy_cb Callback used to retrieve content from the basis file.
 *
 * \param copy_arg Opaque environment pointer passed through to the callback.
 *
 * \todo As output is produced, accumulate the MD4 checksum of the output. Then
 * if we find a CHECKSUM command we can check it's contents against the output.
 *
 * \todo Implement COPY commands.
 *
 * \sa rs_patch_file() \sa \ref api_streaming */
rs_job_t *rs_patch_begin(rs_copy_cb * copy_cb, void *copy_arg);


/** Open a file with special handling for stdin or stdout.
 *
 * This provides a platform independent way to open large binary files. A
 * filename "" or "-" means use stdin for reading, or stdout for writing.
 *
 * \param filename - The filename to open.
 *
 * \param mode - fopen style mode string.
 *
 * \param force - bool to force overwriting of existing files. */
FILE *rs_file_open(char const *filename, char const *mode,
                                   int force);

/** Close a file with special handling for stdin or stdout.
 *
 * This will not actually close the file if it is stdin or stdout.
 *
 * \param file - the stdio file to close. */
int rs_file_close(FILE *file);

/** Get the size of a file.
 *
 * This provides a platform independent way to get the size of large files. It
 * will return -1 if the size cannot be determined because it is not a regular
 * file.
 *
 * \param file - the stdio file to get the size of. */
rs_long_t rs_file_size(FILE *file);

/** ::rs_copy_cb that reads from a stdio file. */
rs_result rs_file_copy_cb(void *arg, rs_long_t pos, size_t *len_,
                                          void **buf);

/** Buffer sizes for file IO.
 *
 * The default 0 means use the recommended buffer size for the operation being
 * performed, any other value will override the recommended sizes. You probably
 * only need to change these in testing. */
extern int rs_inbuflen, rs_outbuflen;

/** Generate the signature of a basis file, and write it out to another.
 *
 * It's recommended you use rs_sig_args() to get the recommended arguments for
 * this based on the original file size.
 *
 * \param old_file Stdio readable file whose signature will be generated.
 *
 * \param sig_file Writable stdio file to which the signature will be written./
 *
 * \param block_len Checksum block size to use (0 for "recommended"). Larger
 * values make the signature shorter, and the delta longer.
 *
 * \param strong_len Strongsum length in bytes to use (0 for "maximum", -1 for
 * "minimum"). Smaller values make the signature shorter but increase the risk
 * of corruption from hash collisions.
 *
 * \param sig_magic Signature file format to generate (0 for "recommended").
 * See ::rs_magic_number.
 *
 * \param stats Optional pointer to receive statistics.
 *
 * \sa \ref api_whole */
rs_result rs_sig_file(FILE *old_file, FILE *sig_file,
                                      size_t block_len, size_t strong_len,
                                      rs_magic_number sig_magic,
                                      rs_stats_t *stats);

/** Load signatures from a signature file into memory.
 *
 * \param sig_file Readable stdio file from which the signature will be read.
 *
 * \param sumset on return points to the newly allocated structure.
 *
 * \param stats Optional pointer to receive statistics.
 *
 * \sa \ref api_whole */
rs_result rs_loadsig_file(FILE *sig_file,
                                          rs_signature_t **sumset,
                                          rs_stats_t *stats);

/** Generate a delta between a signature and a new file into a delta file.
 *
 * \sa \ref api_whole */
rs_result rs_delta_file(rs_signature_t *, FILE *new_file,
                                        FILE *delta_file, rs_stats_t *);

/** Apply a patch, relative to a basis, into a new file.
 *
 * \sa \ref api_whole */
rs_result rs_patch_file(FILE *basis_file, FILE *delta_file,
                                        FILE *new_file, rs_stats_t *);
                                        
void* malloc(size_t n);
void free(void *p);
void* realloc(void *p, size_t n);

// my event callback
typedef struct {
    void *file;
    char* buffer;
    size_t len_;
} input_args;
                       
extern "Python" rs_result read_cb(void *opaque, rs_long_t pos, size_t *len_, void ** buf);
"""
)

c_src = []
for root, dirs, files in os.walk("./dep/src"):
    for file in files:
        if file.endswith(".c") and "rdiff" not in file:
            c_src.append(os.path.join(root, file))
source = """
#include <stdlib.h>
#include <time.h>
#include "job.h"
#include "librsync.h"
#include "cbarg.h"
"""
ffibuilder.set_source(
    "pyrsync.backends.cffi._rsync",
    source,
    sources=c_src,
    include_dirs=["./dep/src", "./dep/src/blake2", "./pyrsync/backends/cffi"],
    define_macros=[("rsync_EXPORTS", None)],
)

if __name__ == "__main__":
    ffibuilder.compile()
