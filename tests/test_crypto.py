"""Two people, two key directories: does the round trip work, and does it
actually exclude everyone else?

No Tkinter here -- this drives the crypto and the keystore directly.
"""

import base64
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

from _harness import PROJECT_ROOT  # noqa: F401  (puts the project on sys.path)


def main():
    try:
        import nacl.pwhash
    except ImportError:
        print("PyNaCl not installed -- skipping the crypto suite")
        return

    from ciphers.base import CipherError
    from ciphers.keystore import KeyStore, KeyStoreError
    from ciphers.publickey import PublicKeyCipher

    root = Path(tempfile.mkdtemp(prefix="cipherlab_test_"))
    print("sandbox:", root)

    def person(name, passphrase):
        store = KeyStore(root / name)
        started = time.time()
        store.create_identity(passphrase)
        print("  %-5s identity created in %.2fs" % (name, time.time() - started))
        return store, PublicKeyCipher(store)

    try:
        alice_store, alice = person("alice", "correct horse battery staple")
        bob_store, bob = person("bob", "hunter2 but longer")
        eve_store, eve = person("eve", "eve's passphrase")

        # --- exchange public keys (the out-of-band step) -------------------
        alice_store.add_contact("Bob", bob_store.public_key_b64)
        bob_store.add_contact("Alice", alice_store.public_key_b64)
        print("\npublic keys exchanged")
        print("  alice sees contacts:", list(alice_store.contacts()))
        print("  bob   sees contacts:", list(bob_store.contacts()))

        # --- Alice -> Bob --------------------------------------------------
        secret = "Meet at the pier at nine. Bring the maps. — A"
        wire = alice.encode(secret, correspondent="Bob")
        print("\nAlice sends (%d chars of base64):" % len(wire))
        print("  " + wire[:64] + "...")
        assert secret not in wire
        got = bob.decode(wire, correspondent="Alice")
        assert got == secret, got
        print("Bob reads:", got)

        # --- Bob -> Alice --------------------------------------------------
        reply = "Understood. Nine it is."
        back = bob.encode(reply, correspondent="Alice")
        assert alice.decode(back, correspondent="Bob") == reply
        print("Alice reads reply:", alice.decode(back, correspondent="Bob"))

        # --- Eve cannot read it, even holding both public keys -------------
        eve_store.add_contact("Alice", alice_store.public_key_b64)
        eve_store.add_contact("Bob", bob_store.public_key_b64)
        for who in ("Alice", "Bob"):
            try:
                eve.decode(wire, correspondent=who)
                raise AssertionError("Eve decrypted the message as %s!" % who)
            except CipherError as exc:
                print("Eve as %-5s -> %s" % (who, str(exc)[:52]))

        # --- tampering is detected (Box is authenticated) ------------------
        raw = bytearray(base64.b64decode(wire))
        raw[-1] ^= 0x01                      # flip one bit of the ciphertext
        tampered = base64.b64encode(bytes(raw)).decode()
        try:
            bob.decode(tampered, correspondent="Alice")
            raise AssertionError("tampered message was accepted")
        except CipherError as exc:
            print("one flipped bit ->", str(exc)[:52])

        # --- a fresh nonce per message -------------------------------------
        first = alice.encode("same text", correspondent="Bob")
        second = alice.encode("same text", correspondent="Bob")
        assert first != second, "identical ciphertext twice: nonce reuse"
        assert (bob.decode(first, correspondent="Alice")
                == bob.decode(second, correspondent="Alice"))
        print("same plaintext twice -> different ciphertext (fresh nonce)")

        # --- locking, wrong passphrase, persistence ------------------------
        alice_store.lock()
        try:
            alice.encode("anything", correspondent="Bob")
            raise AssertionError("locked store still encrypted")
        except CipherError as exc:
            print("locked ->", exc)

        reopened = KeyStore(root / "alice")          # as if the app restarted
        assert not reopened.is_unlocked
        try:
            reopened.unlock("wrong passphrase")
            raise AssertionError("wrong passphrase accepted")
        except KeyStoreError as exc:
            print("wrong passphrase ->", exc)

        started = time.time()
        reopened.unlock("correct horse battery staple")
        print("unlock after restart: %.2fs" % (time.time() - started))
        assert PublicKeyCipher(reopened).decode(back, correspondent="Bob") == reply
        print("message from before the restart still readable")

        # --- the private key is not sitting in the file in the clear -------
        blob = (root / "alice" / "identity.json").read_bytes()
        raw_private = bytes(reopened.private_key)
        assert raw_private not in blob, "PRIVATE KEY STORED IN CLEAR"
        assert base64.b64encode(raw_private) not in blob, "PRIVATE KEY AS BASE64"
        record = json.loads(blob)
        print("\nidentity.json holds only:", sorted(record))
        print("  argon2id opslimit=%s memlimit=%s (%d MiB)"
              % (record["opslimit"], record["memlimit"],
                 record["memlimit"] // (1024 * 1024)))
        assert record["opslimit"] == nacl.pwhash.argon2id.OPSLIMIT_MODERATE
        assert record["memlimit"] == nacl.pwhash.argon2id.MEMLIMIT_MODERATE
        print("  matches argon2id MODERATE, as intended")
        print("  raw private key absent from the file: confirmed")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print("\nAll crypto checks passed.")


def test_crypto():
    main()


if __name__ == "__main__":
    main()
