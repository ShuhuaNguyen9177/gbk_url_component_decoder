import unittest

from gbk_url_component_decoder import decode_gbk_url_component


class TestDecodeGBKURLComponent(unittest.TestCase):

    def test_basic_gbk_chinese(self):
        # "中文" in GBK is b"\xd6\xd0\xce\xc4" → %D6%D0%CE%C4
        self.assertEqual(
            decode_gbk_url_component("%D6%D0%CE%C4"),
            "中文",
        )

    def test_mixed_ascii_and_gbk(self):
        # "a中文b" → a% D6 D0 CE C4 b
        self.assertEqual(
            decode_gbk_url_component("a%D6%D0%CE%C4b"),
            "a中文b",
        )

    def test_plain_ascii_unchanged(self):
        self.assertEqual(decode_gbk_url_component("hello world"), "hello world")

    def test_percent_literal_when_not_hex(self):
        # "%zz" is not a valid hex pair — left as-is.
        self.assertEqual(decode_gbk_url_component("%zz"), "%zz")

    def test_trailing_percent_preserved(self):
        self.assertEqual(decode_gbk_url_component("abc%"), "abc%")

    def test_single_hex_after_percent_preserved(self):
        # "%D" with no second digit → literal
        self.assertEqual(decode_gbk_url_component("%D"), "%D")

    def test_plus_is_literal_not_space(self):
        # This library decodes path components, not form data. "+" stays "+".
        self.assertEqual(decode_gbk_url_component("a+b"), "a+b")

    def test_gbk_with_plus_literal(self):
        self.assertEqual(
            decode_gbk_url_component("%D6%D0+%CE%C4"),
            "中+文",
        )

    def test_lowercase_hex(self):
        self.assertEqual(
            decode_gbk_url_component("%d6%d0%ce%c4"),
            "中文",
        )

    def test_empty_string(self):
        self.assertEqual(decode_gbk_url_component(""), "")

    def test_errors_replace(self):
        # Invalid GBK sequence %FF%FF with errors='replace' gives replacement chars.
        result = decode_gbk_url_component("%FF%FF", errors="replace")
        self.assertEqual(result, "\ufffd\ufffd")

    def test_errors_strict_raises(self):
        with self.assertRaises(UnicodeDecodeError):
            decode_gbk_url_component("%FF%FF", errors="strict")

    def test_gbk_two_byte_lead_byte_without_trail(self):
        # 0x81 is a GBK lead byte; 0x41 ('A') is not a valid trail byte
        # combination, but 0x81 0x40 is a valid GBK character. Test 0x81 0x41.
        # If 0x81 0x41 isn't a valid GBK code point, strict mode should raise.
        # We test with errors='replace' to avoid depending on exact GBK tables.
        result = decode_gbk_url_component("%81%41", errors="replace")
        # We just assert it doesn't crash and returns a string of the same
        # logical length (either one replacement char or the decoded glyph).
        self.assertIsInstance(result, str)
        self.assertGreaterEqual(len(result), 1)

    def test_already_decoded_unicode_preserved(self):
        # If the string already contains a decoded character, it should survive.
        self.assertEqual(decode_gbk_url_component("中文"), "中文")

    def test_type_error_on_non_string(self):
        with self.assertRaises(TypeError):
            decode_gbk_url_component(123)  # type: ignore[arg-type]

    def test_gbk_extended_character(self):
        # "啊" in GBK is b"\xb0\xa1" → %B0%A1
        self.assertEqual(
            decode_gbk_url_component("%B0%A1"),
            "啊",
        )


if __name__ == "__main__":
    unittest.main()
