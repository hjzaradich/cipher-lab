"""Key storage for the public-key cipher.

Holds one identity (your Curve25519 keypair) and a list of contacts (their
public keys). The private key is encrypted at rest with a passphrase, using
Argon2id to derive the key and a SecretBox to hold it.

Files live in ~/.cipher_lab, deliberately NOT beside the app: the app folder may
sit inside OneDrive or another sync client, and a private key should not be
copied to a cloud service as a side effect of where the program was unzipped.
"""

import base64
import json
import os
from pathlib import Path

import nacl.pwhash
import nacl.secret
import nacl.utils
from nacl.exceptions import CryptoError
from nacl.public import PrivateKey, PublicKey

FORMAT_VERSION = 1
KDF = nacl.pwhash.argon2id
# Moderate rather than interactive: this guards a key at rest, and the cost is
# paid once per session.
OPSLIMIT = KDF.OPSLIMIT_MODERATE
MEMLIMIT = KDF.MEMLIMIT_MODERATE


class KeyStoreError(Exception):
    """Something the user can act on: wrong passphrase, missing contact, ..."""


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _unb64(text: str, what: str) -> bytes:
    try:
        return base64.b64decode(text.strip(), validate=True)
    except Exception:
        raise KeyStoreError("That %s is not valid Base64" % what)


def default_directory() -> Path:
    override = os.environ.get("CIPHER_LAB_HOME")
    return Path(override) if override else Path.home() / ".cipher_lab"


class KeyStore:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory else default_directory()
        self._private = None            # unlocked PrivateKey, or None

    # ---------- paths ----------

    @property
    def identity_path(self) -> Path:
        return self.directory / "identity.json"

    @property
    def contacts_path(self) -> Path:
        return self.directory / "contacts.json"

    # ---------- identity ----------

    @property
    def has_identity(self) -> bool:
        return self.identity_path.exists()

    @property
    def is_unlocked(self) -> bool:
        return self._private is not None

    def create_identity(self, passphrase: str, overwrite: bool = False):
        """Generate a keypair and save it, encrypted under `passphrase`."""
        if self.has_identity and not overwrite:
            raise KeyStoreError(
                "An identity already exists. Replacing it makes every message "
                "ever sent to your current key unreadable.")
        if not passphrase:
            raise KeyStoreError("Choose a passphrase -- it protects your key on disk")

        private = PrivateKey.generate()
        salt = nacl.utils.random(KDF.SALTBYTES)
        box = nacl.secret.SecretBox(self._derive(passphrase, salt))
        record = {
            "version": FORMAT_VERSION,
            "public": _b64(bytes(private.public_key)),
            "salt": _b64(salt),
            "opslimit": OPSLIMIT,
            "memlimit": MEMLIMIT,
            "secret": _b64(box.encrypt(bytes(private))),
        }
        self._write(self.identity_path, record)
        self._private = private

    def unlock(self, passphrase: str):
        record = self._read(self.identity_path)
        if record is None:
            raise KeyStoreError("There is no identity yet -- create one first")
        try:
            key = self._derive(passphrase, _unb64(record["salt"], "salt"),
                               record.get("opslimit", OPSLIMIT),
                               record.get("memlimit", MEMLIMIT))
            raw = nacl.secret.SecretBox(key).decrypt(
                _unb64(record["secret"], "stored key"))
        except CryptoError:
            raise KeyStoreError("Wrong passphrase")
        except KeyError:
            raise KeyStoreError("The identity file is damaged or incomplete")
        self._private = PrivateKey(raw)

    def lock(self):
        self._private = None

    @property
    def private_key(self) -> PrivateKey:
        if self._private is None:
            raise KeyStoreError("Locked -- open Keys to unlock your identity")
        return self._private

    @property
    def public_key_b64(self) -> str:
        """Your public key, to hand to the other person."""
        record = self._read(self.identity_path)
        if record is None:
            raise KeyStoreError("There is no identity yet -- create one first")
        return record["public"]

    # ---------- contacts ----------

    def contacts(self) -> dict:
        return self._read(self.contacts_path) or {}

    def add_contact(self, name: str, public_b64: str):
        name = name.strip()
        if not name:
            raise KeyStoreError("Give the contact a name")
        raw = _unb64(public_b64, "public key")
        if len(raw) != 32:
            raise KeyStoreError(
                "A public key is 32 bytes; that one is %d" % len(raw))
        PublicKey(raw)  # rejects anything structurally wrong
        contacts = self.contacts()
        contacts[name] = _b64(raw)
        self._write(self.contacts_path, contacts)

    def remove_contact(self, name: str):
        contacts = self.contacts()
        if contacts.pop(name, None) is None:
            raise KeyStoreError("No contact called %r" % name)
        self._write(self.contacts_path, contacts)

    def public_key_for(self, name: str) -> PublicKey:
        contacts = self.contacts()
        if name not in contacts:
            raise KeyStoreError("No contact called %r" % name)
        return PublicKey(_unb64(contacts[name], "stored public key"))

    # ---------- plumbing ----------

    def _derive(self, passphrase, salt, ops=OPSLIMIT, mem=MEMLIMIT) -> bytes:
        return KDF.kdf(nacl.secret.SecretBox.KEY_SIZE,
                       passphrase.encode("utf-8"), salt,
                       opslimit=ops, memlimit=mem)

    def _read(self, path: Path):
        if not path.exists():
            return None
        try:
            with path.open(encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, ValueError):
            raise KeyStoreError("Could not read %s" % path.name)

    def _write(self, path: Path, payload):
        self.directory.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        os.replace(temporary, path)     # atomic, so a crash cannot truncate it
        try:
            os.chmod(path, 0o600)       # no-op on Windows, matters elsewhere
        except OSError:
            pass
