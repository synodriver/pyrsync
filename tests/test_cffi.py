
import sys
sys.path.append(".")
from io import BytesIO
from unittest import TestCase
import os
os.environ["RSYNC_USE_CFFI"] = "1"

from pyrsync import delta, get_signature_args, patch, signature


class TestPatch(TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_patch(self):
        s = b"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" * 50
        d = b"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" * 50 + b"2"
        src = BytesIO(s)
        dst = BytesIO(d)
        magic, block_len, strong_len = get_signature_args(len(s))
        sig = BytesIO()
        signature(dst, sig, strong_len, magic, block_len)  # sig由dst产生
        dst.seek(0, 0)
        sig.seek(0, 0)
        self.assertEqual(sig.getvalue(), b'rs\x01G\x00\x00\x01\x00\x00\x00\x00 \xf8\x81\xcb\x01\xea\xe4\xd3\xa7buI\xb3\x83\x17\x9d\xc1\x80I\x96O\x91\xa6\xfe\xd1L\x9f?\xb2g\x05\xed\xa3\xee\xdaUX\xf8\x81\xcb\x01\xea\xe4\xd3\xa7buI\xb3\x83\x17\x9d\xc1\x80I\x96O\x91\xa6\xfe\xd1L\x9f?\xb2g\x05\xed\xa3\xee\xdaUX\xf8\x81\xcb\x01\xea\xe4\xd3\xa7buI\xb3\x83\x17\x9d\xc1\x80I\x96O\x91\xa6\xfe\xd1L\x9f?\xb2g\x05\xed\xa3\xee\xdaUX\xf8\x81\xcb\x01\xea\xe4\xd3\xa7buI\xb3\x83\x17\x9d\xc1\x80I\x96O\x91\xa6\xfe\xd1L\x9f?\xb2g\x05\xed\xa3\xee\xdaUX\xf8\x81\xcb\x01\xea\xe4\xd3\xa7buI\xb3\x83\x17\x9d\xc1\x80I\x96O\x91\xa6\xfe\xd1L\x9f?\xb2g\x05\xed\xa3\xee\xdaUX\xf8\x81\xcb\x01\xea\xe4\xd3\xa7buI\xb3\x83\x17\x9d\xc1\x80I\x96O\x91\xa6\xfe\xd1L\x9f?\xb2g\x05\xed\xa3\xee\xdaUX\xe4g\xcf\x194&\x8b\xdb\x9b\xa9>\xb7\xbb$H\x98\x12\x17\xd1\xb8\xa6\xff\x90\x1a\xc1h\xe2\xde\xbb\xe7\xd7\xfb/;P\xb0')
        sig.seek(0, 0)

        _delta = BytesIO()
        delta(src, sig, _delta)  # src和sig对比产生delta
        src.seek(0, 0)
        _delta.seek(0, 0)
        # print(len_(_delta.getvalue()))
        # _delta.seek(0, 0)
        out = BytesIO()
        patch(dst, _delta, out)
        self.assertEqual(out.getvalue(), src.getvalue())


if __name__ == "__main__":
    import unittest

    unittest.main()