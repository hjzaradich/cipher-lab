"""Public-key messaging driven through the window.

Runs against a throwaway key directory, so a real ~/.cipher_lab is never
touched, read or overwritten.
"""

import os
import shutil
import tempfile

SANDBOX = tempfile.mkdtemp(prefix="cipherlab_ui_")
os.environ["CIPHER_LAB_HOME"] = SANDBOX   # set before anything reads it

from _harness import Driver, make_app   # noqa: E402


def main():
    app = make_app()
    d = Driver(app)

    from ciphers import REGISTRY

    if "Public key" not in [c.name for c in REGISTRY]:
        print("PyNaCl not installed -- public-key entry absent, skipping")
        app.destroy()
        return

    from ciphers.keystore import KeyStore
    from ciphers.publickey import PublicKeyCipher

    d.pick("Public key")
    store = app.cipher.store
    assert str(store.directory) == SANDBOX, store.directory

    # --- before setup, it says what to do rather than failing obscurely ----
    d.set("hello")
    assert d.out() == ""
    assert "No identity" in d.status(), d.status()
    print("no identity ->", d.status())

    # the Keys button is there for this cipher only
    def key_buttons():
        return [w for w in app.params_frame.winfo_children()
                if w.winfo_class() == "TButton"]

    assert key_buttons(), "no Keys button"
    d.pick("Caesar")
    assert not key_buttons(), "Keys button leaked to Caesar"
    d.pick("Public key")
    print("Keys button appears only for the public-key cipher")

    # --- set up an identity and a correspondent ----------------------------
    store.create_identity("a test passphrase")
    friend = KeyStore(os.path.join(SANDBOX, "friend"))
    friend.create_identity("their passphrase")
    store.add_contact("Friend", friend.public_key_b64)
    friend.add_contact("Me", store.public_key_b64)

    app._keys_changed()          # what closing the Keys dialog does
    app.update()
    assert app.cipher.params[0].choices == ("Friend",), app.cipher.params[0].choices
    assert app.param_vars["correspondent"].get() == "Friend"
    print("correspondent dropdown picked up the new contact")

    # --- round trip through the window -------------------------------------
    d.mode("encode")
    message = "Meet at the pier at nine. — me"
    d.set(message)
    wire = d.out()
    assert wire and message not in wire
    print("encrypted:", wire[:48] + "...")

    # the friend, with their own keystore, reads it
    assert PublicKeyCipher(friend).decode(wire, correspondent="Me") == message
    print("friend decrypts it with their own key")

    # and the window decrypts what the friend sends back
    reply = PublicKeyCipher(friend).encode("See you there.", correspondent="Me")
    d.mode("decode")
    d.set(reply)
    assert d.out() == "See you there.", d.out()
    print("window decrypts the reply:", d.out())

    # --- a selected correspondent survives a keystore change ---------------
    # "Anna" sorts before "Friend", so a naive rebuild would snap the dropdown
    # back to the first entry and silently change who you are writing to.
    third = KeyStore(os.path.join(SANDBOX, "third"))
    third.create_identity("a third passphrase")
    store.add_contact("Anna", third.public_key_b64)
    app._keys_changed()
    app.update()
    assert app.cipher.params[0].choices == ("Anna", "Friend")
    assert app.param_vars["correspondent"].get() == "Friend", \
        "adding a contact moved the selection"
    print("selected correspondent survives a contact being added")

    store.remove_contact("Anna")
    app._keys_changed()
    app.update()
    assert app.param_vars["correspondent"].get() == "Friend"

    # --- locking mid-session reports plainly -------------------------------
    store.lock()
    app.refresh()
    app.update()
    assert d.out() == ""
    assert "Locked" in d.status(), d.status()
    print("locked ->", d.status())

    store.unlock("a test passphrase")
    d.set(reply)
    assert d.out() == "See you there."
    print("unlocked again, message readable")

    # --- a corrupted message says so ---------------------------------------
    d.set(reply[:-6] + "AAAAAA")
    assert d.out() == ""
    assert "Could not decrypt" in d.status(), d.status()
    print("corrupted ->", d.status()[:60])

    # --- no key table for this one -----------------------------------------
    assert d.toggle_state() == "disabled"
    assert "too many keys" in d.hint()

    # --- other ciphers unaffected ------------------------------------------
    d.pick("Caesar")
    d.mode("decode")
    app.param_vars["shift"].set(3)
    d.set("Dwwdfn dw gdzq!")
    assert d.out() == "Attack at dawn!", d.out()
    print("caesar unaffected")

    app.destroy()
    print("\nAll checks passed.")


def test_publickey_ui():
    main()


if __name__ == "__main__":
    try:
        main()
    finally:
        shutil.rmtree(SANDBOX, ignore_errors=True)
