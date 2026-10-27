"""Decode percent-encoded URL components that were encoded with GBK.

The standard library's ``urllib.parse.unquote`` is hardcoded to treat
percent-encoded bytes as UTF-8 (or Latin-1 via ``errors="replace"``).
For legacy Chinese web URLs that were encoded with GBK this produces
mojibake. The only correct way to handle these is to take the raw
percent-encoded bytes and pass them through Python's built-in GBK codec.

This module exposes a single function, ``decode_gbk_url_component``,
which does exactly that and nothing else.
"""

from __future__ import annotations


def decode_gbk_url_component(
    value: str,
    *,
    errors: str = "strict",
) -> str:
    """Decode a percent-encoded URL component from GBK bytes.

    :param value:   The percent-encoded string. The plus character ``+``
                    is treated as a literal plus, *not* as a space — this
                    function decodes *path components* where ``+`` is a
                    literal character. Use ``urllib.parse.unquote_plus``
    :param errors:  Codec error-handling scheme passed straight through to
                    Python's built-in GBK codec. ``strict`` (default) raises
                    ``UnicodeDecodeError`` on malformed byte sequences.
                    ``replace`` and ``ignore`` behave as the codec defines them.
    :return:        The decoded Python ``str``.

    The design decision here is to **only decode percent sequences** and leave
every other character alone. This matches the behaviour of
``urllib.parse.unquote`` and avoids surprises where an already-decoded
string containing percent signs gets mangled on a second pass.

    Malformed percent sequences — ``%`` not followed by two hex digits — are
left as-is rather than raising, matching the lenient behaviour of most
browsers for path segments.
    """
    if not isinstance(value, str):
        raise TypeError(f"expected str, got {type(value).__name__}")

    # Walk the string, decoding percent-encoded byte sequences with GBK.
    # Already-decoded characters outside Latin-1 (e.g. raw Chinese) are
    # appended to the output directly, after flushing any pending bytes
    # through the GBK codec, so they survive untouched.
    result = []
    decoded_bytes = bytearray()
    i = 0
    length = len(value)

    def _flush() -> None:
        if decoded_bytes:
            result.append(decoded_bytes.decode("gbk", errors=errors))
            decoded_bytes.clear()

    while i < length:
        ch = value[i]
        if ch == "%":
            if i + 2 < length:
                hi = value[i + 1]
                lo = value[i + 2]
                if _is_hex_char(hi) and _is_hex_char(lo):
                    decoded_bytes.append((_hex_val_char(hi) << 4) | _hex_val_char(lo))
                    i += 3
                    continue
            # Malformed percent sequence — emit it literally.
            decoded_bytes.extend(ch.encode("latin-1", errors="replace"))
            i += 1
        elif ord(ch) <= 0xFF:
            decoded_bytes.append(ord(ch))
            i += 1
        else:
            # Already-decoded character outside Latin-1 (e.g. raw Chinese).
            # Flush any pending bytes, then append the character literally.
            _flush()
            result.append(ch)
            i += 1

    _flush()
    return "".join(result)


_HEX_DIGITS = b"0123456789ABCDEFabcdef"


def _is_hex(byte: int) -> bool:
    return byte in _HEX_DIGITS


def _hex_val(byte: int) -> int:
    if 0x30 <= byte <= 0x39:  # '0'-'9'
        return byte - 0x30
    if 0x41 <= byte <= 0x46:  # 'A'-'F'
        return byte - 0x41 + 10
    if 0x61 <= byte <= 0x66:  # 'a'-'f'
        return byte - 0x61 + 10
    raise ValueError(f"not a hex digit: {byte!r}")


def _is_hex_char(ch: str) -> bool:
    return len(ch) == 1 and ord(ch) in _HEX_DIGITS


def _hex_val_char(ch: str) -> int:
    return _hex_val(ord(ch))
