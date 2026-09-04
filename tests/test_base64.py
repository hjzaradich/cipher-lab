"""Base64: round trips, forgiving input, and errors that read as sentences."""

from _harness import Driver, make_app


def main():
    app = make_app()
    d = Driver(app)

    d.pick("Base64")
    assert app.param_vars == {}

    # --- round trip --------------------------------------------------------
    d.mode("encode")
    d.set("Attack at dawn!")
    assert d.out() == "QXR0YWNrIGF0IGRhd24h", d.out()
    print("encode:", d.out())
    app.send_up()
    d.mode("decode")
    assert d.out() == "Attack at dawn!", d.out()
    print("decode:", d.out())

    # non-ASCII survives as UTF-8
    d.mode("encode")
    d.set("café — 日本語")
    app.send_up()
    d.mode("decode")
    assert d.out() == "café — 日本語", d.out()
    print("utf-8 round trip ok")

    # --- forgiving decoding ------------------------------------------------
    d.mode("decode")
    for variant, label in (
        ("QXR0YWNrIGF0IGRhd24h", "canonical"),
        ("QXR0YWNr\nIGF0IGRh\nd24h", "wrapped across lines"),
        ("  QXR0YWNrIGF0IGRhd24h  ", "padded with spaces"),
        ("QXR0YWNrIGF0IGRhd24", "padding stripped"),
    ):
        d.set(variant)
        assert d.out().startswith("Attack at daw"), (label, d.out())
    print("decode tolerates wrapping, whitespace and missing padding")

    # --- failures read as plain sentences, not tracebacks ------------------
    for bad, expect in (("not base64!!", "unexpected"),
                        ("QQQQQ", "wrong length"),
                        ("//79", "binary data")):
        d.set(bad)
        assert d.out() == "", (bad, d.out())
        status = d.status()
        assert expect in status, (bad, status)
        assert "Error:" not in status and "Exception" not in status, status
        print("  %-14s -> %s" % (bad, status))

    # recovering from an error restores normal output
    d.set("QXR0YWNrIGF0IGRhd24h")
    assert d.out() == "Attack at dawn!"
    assert "chars" in d.status(), d.status()
    print("recovers after an error")

    # --- no key, so no panel -----------------------------------------------
    assert d.toggle_state() == "disabled"
    assert not d.panel_shown()
    assert "no key to choose" in d.hint()

    # --- Caesar is unaffected ----------------------------------------------
    d.pick("Caesar")
    assert d.toggle_state() == "normal"
    assert d.panel_shown()
    d.mode("decode")
    app.param_vars["shift"].set(3)
    d.set("Dwwdfn dw gdzq!")
    assert d.out() == "Attack at dawn!", d.out()
    print("caesar unaffected")

    app.destroy()
    print("\nAll checks passed.")


def test_base64():
    main()


if __name__ == "__main__":
    main()
