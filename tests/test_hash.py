"""Hashing: digests that match hashlib, and the one-way contract in the UI."""

import hashlib

from _harness import Driver, make_app


def main():
    app = make_app()
    d = Driver(app)

    from ciphers import REGISTRY

    assert "Hash" in [c.name for c in REGISTRY]

    # --- the one-way contract ----------------------------------------------
    d.pick("Hash")
    assert app.mode.get() == "encode", app.mode.get()
    assert str(app.decode_radio.cget("state")) == "disabled", "Decode must be off"
    assert str(app.encode_radio.cget("state")) == "normal"
    assert app.out_label.cget("text") == "Digest", app.out_label.cget("text")
    print("one-way: Decode disabled, output labelled 'Digest'")

    # arriving from a cipher that was mid-decode must not leave it decoding
    d.pick("Caesar")
    d.mode("decode")
    d.pick("Hash")
    assert app.mode.get() == "encode", "switching to Hash left it decoding"
    print("switching in while decoding flips to encode")

    # --- digests match hashlib exactly -------------------------------------
    d.set("Attack at dawn!")
    raw = "Attack at dawn!".encode("utf-8")
    assert d.out() == hashlib.sha256(raw).hexdigest(), d.out()
    print("sha256:", d.out())
    assert len(d.out()) == 64

    for label, fn in (("SHA-512", hashlib.sha512), ("SHA3-256", hashlib.sha3_256),
                      ("BLAKE2b", hashlib.blake2b), ("SHA-1", hashlib.sha1),
                      ("MD5", hashlib.md5)):
        app.param_vars["algorithm"].set(label)
        app.update()
        assert d.out() == fn(raw).hexdigest(), label
        print("  %-9s -> %s... (%d hex chars)" % (label, d.out()[:16], len(d.out())))

    app.param_vars["algorithm"].set("SHA-256")
    app.update()

    # UTF-8 bytes are what get hashed
    d.set("café")
    assert d.out() == hashlib.sha256("café".encode("utf-8")).hexdigest()
    print("utf-8 hashed as utf-8 bytes")

    # a one-character change must change the digest completely
    d.set("Attack at dawn!")
    a = d.out()
    d.set("Attack at dawn?")
    b = d.out()
    differing = sum(x != y for x, y in zip(a, b))
    assert a != b and differing > 40, "digest barely changed"
    print("one character changed -> %d of 64 hex digits differ" % differing)

    # blank in, blank out -- not the digest of the empty string
    d.set("")
    assert d.out() == "", d.out()
    assert d.out() != hashlib.sha256(b"").hexdigest()
    print("empty input stays empty")

    # the backstop still refuses if decode is reached directly
    from ciphers import CipherError

    try:
        app.cipher.decode("anything")
        raise AssertionError("decode should have refused")
    except CipherError as exc:
        print("decode backstop:", exc)

    # --- no key table ------------------------------------------------------
    assert d.toggle_state() == "disabled"
    assert not d.panel_shown()

    # --- leaving Hash restores both directions -----------------------------
    d.pick("Caesar")
    assert str(app.decode_radio.cget("state")) == "normal", "Decode stayed disabled"
    d.mode("decode")
    app.param_vars["shift"].set(3)
    d.set("Dwwdfn dw gdzq!")
    assert d.out() == "Attack at dawn!", d.out()
    assert app.out_label.cget("text") == "Decoded"
    print("leaving Hash restores Decode")

    app.destroy()
    print("\nAll checks passed.")


def test_hash():
    main()


if __name__ == "__main__":
    main()
