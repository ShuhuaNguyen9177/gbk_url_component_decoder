# gbk_url_component_decoder

Decodes percent-encoded URL components that were encoded using GBK, the legacy encoding common in older Chinese web URLs. Python's `urllib.parse.unquote` assumes UTF-8 and produces mojibake on these strings; this library uses the GBK codec instead.

```python
from gbk_url_component_decoder import decode_gbk_url_component

decoded = decode_gbk_url_component("%D6%D0%CE%C4")
# → "中文"

decoded = decode_gbk_url_component("%B0%A1")
# → "啊"
```

## Why this exists

Older Chinese websites encoded URL path segments with GBK, not UTF-8. When you fetch or log these URLs today, `urllib.parse.unquote` interprets the percent-encoded bytes as UTF-8, yielding garbled text. This library extracts the percent-encoded byte sequences and decodes them with Python's built-in GBK codec, leaving literal characters untouched.

## Design decisions

- **`+` is a literal plus, not a space.** This decodes *path components*, where `+` has no special meaning. If you need form-data semantics, convert `+` to space yourself before calling.
- **Malformed percent sequences are left as-is.** `%zz` or a trailing `%` is preserved literally rather than raising, matching browser leniency for path segments.
- **`errors="strict"` is the default.** Invalid GBK byte sequences raise `UnicodeDecodeError`. Pass `errors="replace"` for lenient handling.

## Edge cases

- Strings containing already-decoded characters outside Latin-1 (e.g. raw Chinese) are preserved as-is; only percent sequences are decoded.
- The function accepts `str` only and raises `TypeError` on other types.

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

