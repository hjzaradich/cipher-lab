"""Vigenère: a Caesar shift per letter, cycling through a keyword."""

from .base import Cipher, CipherError, TextParam


def _offsets(keyword: str) -> list[int]:
    offsets = [
        ord(ch.lower()) - 97
        for ch in keyword
        if "a" <= ch <= "z" or "A" <= ch <= "Z"
    ]
    if not offsets:
        raise CipherError("Vigenère needs a keyword containing at least one letter")
    return offsets


def apply_key(text: str, keyword: str, direction: int) -> str:
    """Shift each letter by the next keyword letter; +1 encodes, -1 decodes."""
    offsets = _offsets(keyword)
    out = []
    position = 0  # advances only on letters, so spacing never consumes the key
    for ch in text:
        if "a" <= ch <= "z":
            base = 97
        elif "A" <= ch <= "Z":
            base = 65
        else:
            out.append(ch)
            continue
        shift = offsets[position % len(offsets)] * direction
        out.append(chr((ord(ch) - base + shift) % 26 + base))
        position += 1
    return "".join(out)


class VigenereCipher(Cipher):
    name = "Vigenère"
    blurb = "Each letter is shifted by the matching letter of a repeating keyword."
    params = [
        TextParam(key="keyword", label="Keyword", default="LEMON"),
    ]

    def encode(self, text: str, keyword: str = "", **_) -> str:
        return apply_key(text, keyword, 1)

    def decode(self, text: str, keyword: str = "", **_) -> str:
        return apply_key(text, keyword, -1)

    # The key space is unbounded, so there is no table of every decoding.
