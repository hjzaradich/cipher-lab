"""ROT13: a Caesar shift fixed at 13."""

from .base import Cipher
from .caesar import shift_text

ROTATION = 13


class Rot13Cipher(Cipher):
    name = "ROT13"
    blurb = "A Caesar shift of 13 -- half the alphabet, so it is its own inverse."
    params = []

    # 13 + 13 == 26, a full turn, so both directions are the same operation.
    def encode(self, text: str, **_) -> str:
        return shift_text(text, ROTATION)

    def decode(self, text: str, **_) -> str:
        return shift_text(text, ROTATION)
