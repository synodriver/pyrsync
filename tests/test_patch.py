import sys
sys.path.append(".")
from io import BytesIO
from unittest import TestCase

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