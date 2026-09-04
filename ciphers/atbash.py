"""Atbash: the alphabet mirrored, A<->Z, B<->Y, and so on."""

from .base import Cipher

# 'a' + 'z' == 219 and 'A' + 'Z' == 155, so mirroring is one subtraction.
_LOWER_PIVOT = ord("a") + ord("z")
_UPPER_PIVOT = ord("A") + ord("Z")


def mirror(text: str) -> str:
    out = []
    for ch in text:
        if "a" <= ch <= "z":
            out.append(chr(_LOWER_PIVOT - ord(ch)))
        elif "A" <= ch <= "Z":
            out.append(chr(_UPPER_PIVOT - ord(ch)))
        else:
            out.append(ch)
    return "".join(out)


class AtbashCipher(Cipher):
    name = "Atbash"
    blurb = "Mirrors the alphabet. It has no key, and is its own inverse."
    params = []

    # Applying it twice returns the original, so both directions are the same.
    def encode(self, text: str, **_) -> str:
        return mirror(text)

    def decode(self, text: str, **_) -> str:
        return mirror(text)
