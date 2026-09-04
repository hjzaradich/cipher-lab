"""Cipher registry.

To add a cipher: write a module here with a Cipher subclass, then append an
instance to REGISTRY. The UI picks it up automatically -- a cipher picker
appears as soon as there is more than one.
"""

from .atbash import AtbashCipher
from .b64 import Base64Cipher
from .base import Cipher, ChoiceParam, CipherError, IntParam, TextParam
from .caesar import CaesarCipher
from .digest import HashCipher
from .morse import MorseCipher
from .rot13 import Rot13Cipher
from .vigenere import VigenereCipher

# Public-key messaging needs PyNaCl. Without it the entry simply does not
# appear, rather than the whole app failing to start.
try:
    from .publickey import PublicKeyCipher
except ImportError:  # pragma: no cover - depends on the install
    PublicKeyCipher = None

REGISTRY: list[Cipher] = [
    CaesarCipher(),
    Rot13Cipher(),
    AtbashCipher(),
    VigenereCipher(),
    MorseCipher(),
    Base64Cipher(),
    HashCipher(),
]

if PublicKeyCipher is not None:
    REGISTRY.append(PublicKeyCipher())

__all__ = ["Cipher", "ChoiceParam", "CipherError", "IntParam",
           "TextParam", "REGISTRY"]
