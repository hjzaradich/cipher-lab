"""Base64.

Like Morse, this is a transcoding rather than a cipher, so the two directions
differ. Text is treated as UTF-8 on the way in. Encoding always emits the
standard alphabet; decoding is deliberately more forgiving, accepting wrapped
input, the URL-safe alphabet and missing padding.
"""

import base64
import binascii

from .base import Cipher, CipherError

STANDARD = set(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
)
# The URL-safe variant swaps these two characters in; decoding accepts both.
URL_SAFE = {"-": "+", "_": "/"}


def encode(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def decode(text: str) -> str:
    packed = "".join(text.split())          # tolerate wrapped or indented input
    packed = "".join(URL_SAFE.get(ch, ch) for ch in packed)
    packed = packed.rstrip("=")
    if not packed:
        return ""

    unexpected = sorted(set(packed) - STANDARD)
    if unexpected:
        raise CipherError(
            "Not Base64: unexpected %s" % ", ".join(repr(c) for c in unexpected))

    try:
        # Length is restored here, so input with the padding stripped still works.
        raw = base64.b64decode(packed + "=" * (-len(packed) % 4), validate=True)
    except (binascii.Error, ValueError):
        raise CipherError("Not valid Base64 -- the input is the wrong length")

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        raise CipherError(
            "Those Base64 bytes decode to binary data, not text")


class Base64Cipher(Cipher):
    name = "Base64"
    blurb = "Bytes as printable ASCII. Encoding, not encryption -- anyone can undo it."
    params = []

    def encode(self, text: str, **_) -> str:
        return encode(text)

    def decode(self, text: str, **_) -> str:
        return decode(text)
