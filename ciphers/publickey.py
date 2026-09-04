"""Public-key messaging between two people.

Curve25519 + XSalsa20-Poly1305, via PyNaCl's Box. Encrypting uses your private
key and the other person's public key; decrypting uses the same pair, so one
"Correspondent" setting covers both directions of a conversation.

Box is authenticated as well as secret: a message that decrypts is one that
really came from that correspondent and has not been altered in transit.
"""

import base64
import binascii

from nacl.exceptions import CryptoError
from nacl.public import Box

from .base import Cipher, ChoiceParam, CipherError
from .keystore import KeyStore, KeyStoreError

NO_CONTACTS = "(no contacts yet)"


class PublicKeyCipher(Cipher):
    name = "Public key"
    blurb = "Messages only you and one named correspondent can read."
    uses_keystore = True

    def __init__(self, store=None):
        self.store = store or KeyStore()
        # Built per instance rather than on the class: refresh_params rewrites
        # the choices in place, and a shared class attribute would leak one
        # instance's contact list into another's.
        self.params = [
            ChoiceParam(key="correspondent", label="Correspondent",
                        choices=(NO_CONTACTS,), default=NO_CONTACTS)
        ]

    def refresh_params(self):
        """Contacts change while the app runs, so re-read them on selection."""
        names = tuple(sorted(self.store.contacts()))
        spec = self.params[0]
        spec.choices = names or (NO_CONTACTS,)
        spec.default = names[0] if names else NO_CONTACTS

    # ---------- the work ----------

    def _box(self, correspondent: str) -> Box:
        if not self.store.has_identity:
            raise CipherError(
                "No identity yet -- open Keys to create your keypair")
        if not correspondent or correspondent == NO_CONTACTS:
            raise CipherError(
                "No correspondent yet -- open Keys to add their public key")
        try:
            return Box(self.store.private_key,
                       self.store.public_key_for(correspondent))
        except KeyStoreError as exc:
            raise CipherError(str(exc))

    def encode(self, text: str, correspondent: str = "", **_) -> str:
        box = self._box(correspondent)
        if not text:
            return ""
        # PyNaCl generates a fresh random nonce per message and prepends it.
        return base64.b64encode(box.encrypt(text.encode("utf-8"))).decode("ascii")

    def decode(self, text: str, correspondent: str = "", **_) -> str:
        box = self._box(correspondent)
        packed = "".join(text.split())
        if not packed:
            return ""
        try:
            raw = base64.b64decode(packed, validate=True)
        except (binascii.Error, ValueError):
            raise CipherError("That is not a Base64 message from this app")
        try:
            return box.decrypt(raw).decode("utf-8")
        except CryptoError:
            raise CipherError(
                "Could not decrypt: wrong correspondent, or the message was "
                "altered or truncated")
        except UnicodeDecodeError:
            raise CipherError("Decrypted, but the contents are not text")
