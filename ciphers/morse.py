"""Morse code.

Unlike the substitution ciphers, this one changes alphabet entirely, so the two
directions are genuinely different operations: encode turns text into dots and
dashes, decode parses them back.
"""

import re

from .base import Cipher

LETTER_GAP = " "
WORD_GAP = " / "
UNKNOWN = "?"

TABLE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".",
    "F": "..-.", "G": "--.", "H": "....", "I": "..", "J": ".---",
    "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---",
    "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-",
    "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--",
    "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
    ".": ".-.-.-", ",": "--..--", "?": "..--..", "'": ".----.",
    "!": "-.-.--", "/": "-..-.", "(": "-.--.", ")": "-.--.-",
    "&": ".-...", ":": "---...", ";": "-.-.-.", "=": "-...-",
    "+": ".-.-.", "-": "-....-", "_": "..--.-", '"': ".-..-.",
    "$": "...-..-", "@": ".--.-.",
}

FROM_CODE = {code: char for char, code in TABLE.items()}

# Accept the typographic variants people paste in alongside . and -
ALIASES = {
    "·": ".", "•": ".", "∙": ".",   # middle dot, bullet
    "−": "-", "–": "-", "—": "-",   # minus, en dash, em dash
}


def encode(text: str) -> str:
    """Text to dots and dashes. Characters with no code are dropped."""
    lines = []
    for line in text.split("\n"):
        words = []
        for word in line.split():
            codes = [TABLE[ch] for ch in word.upper() if ch in TABLE]
            if codes:
                words.append(LETTER_GAP.join(codes))
        lines.append(WORD_GAP.join(words))
    return "\n".join(lines)


def decode(text: str) -> str:
    """Dots and dashes back to text, forgiving about how words are separated."""
    lines = []
    for line in text.split("\n"):
        symbols = "".join(ALIASES.get(ch, ch) for ch in line)
        symbols = symbols.replace("|", "/")
        symbols = re.sub(r"[ \t]*/[ \t]*", "/", symbols)  # explicit word breaks
        symbols = re.sub(r"[ \t]{2,}", "/", symbols)      # a wide gap is one too
        words = [word for word in symbols.split("/") if word.strip()]
        lines.append(" ".join(
            "".join(FROM_CODE.get(code, UNKNOWN) for code in word.split())
            for word in words
        ))
    return "\n".join(lines)


class MorseCipher(Cipher):
    name = "Morse"
    blurb = "Letters, digits and punctuation as dots and dashes."
    params = []

    def encode(self, text: str, **_) -> str:
        return encode(text)

    def decode(self, text: str, **_) -> str:
        return decode(text)
