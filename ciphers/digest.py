"""Cryptographic hashes.

The odd one out in this collection: a hash is one-way. It is not a cipher and
carries no message -- you cannot get the text back from a digest, at any price.
It sits here because it turns up in the same work as the ciphers do: checking a
download, comparing two files, recognising a known value.
"""

import hashlib

from .base import Cipher, ChoiceParam, CipherError

# Display name -> hashlib name. SHA-256 leads because it is the usual default.
ALGORITHMS = {
    "SHA-256": "sha256",
    "SHA-512": "sha512",
    "SHA3-256": "sha3_256",
    "BLAKE2b": "blake2b",
    "SHA-1": "sha1",
    "MD5": "md5",
}
DEFAULT = "SHA-256"


def digest(text: str, algorithm: str = DEFAULT) -> str:
    """Hex digest of the text's UTF-8 bytes."""
    try:
        name = ALGORITHMS[algorithm]
    except KeyError:
        raise CipherError("Unknown algorithm %r" % algorithm)
    return hashlib.new(name, text.encode("utf-8")).hexdigest()


class HashCipher(Cipher):
    name = "Hash"
    blurb = "A one-way digest. SHA-1 and MD5 are here for old checksums only."
    one_way = True
    params = [
        ChoiceParam(key="algorithm", label="Algorithm",
                    choices=tuple(ALGORITHMS), default=DEFAULT),
    ]

    def encode(self, text: str, algorithm: str = DEFAULT, **_) -> str:
        # Blank in, blank out, to match every other entry. The digest of the
        # empty string is a real value, but showing it for an empty box reads
        # as though something was hashed.
        if not text:
            return ""
        return digest(text, algorithm)

    def decode(self, text: str, **_) -> str:
        # The UI disables the Decode direction for one-way entries; this is the
        # backstop if anything calls it anyway.
        raise CipherError(
            "A hash is one-way -- a digest cannot be turned back into text")
