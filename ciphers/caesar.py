"""Caesar shift cipher."""

from .base import Cipher, IntParam

ALPHABET_SIZE = 26


def shift_text(text: str, amount: int) -> str:
    """Rotate letters by `amount`, leaving case, digits and punctuation alone."""
    amount %= ALPHABET_SIZE
    if amount == 0:
        return text
    out = []
    for ch in text:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + amount) % ALPHABET_SIZE + 97))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + amount) % ALPHABET_SIZE + 65))
        else:
            out.append(ch)
    return "".join(out)


class CaesarCipher(Cipher):
    name = "Caesar"
    blurb = "Each letter moves a fixed number of places along the alphabet."
    key_noun = "shift"
    params = [
        IntParam(key="shift", label="Shift", minimum=0, maximum=25, default=3),
    ]

    def encode(self, text: str, shift: int = 3, **_) -> str:
        return shift_text(text, shift)

    def decode(self, text: str, shift: int = 3, **_) -> str:
        return shift_text(text, -shift)

    def candidates(self, text: str, **_):
        return [(str(s), shift_text(text, -s)) for s in range(ALPHABET_SIZE)]
