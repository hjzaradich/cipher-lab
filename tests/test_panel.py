"""Atbash, Vigenere, and the all-keys panel's behaviour across ciphers."""

from _harness import Driver, make_app

VIGENERE = "Vigenère"


def main():
    app = make_app()
    d = Driver(app)

    from ciphers import REGISTRY

    names = [c.name for c in REGISTRY]
    for required in ("Caesar", "Atbash", VIGENERE):
        assert required in names, (required, names)
    print("registry:", names)

    # --- Caesar still behaves ----------------------------------------------
    d.pick("Caesar")
    d.mode("encode")
    d.set("Attack at dawn!")
    app.param_vars["shift"].set(3)
    app.update()
    assert d.out() == "Dwwdfn dw gdzq!", d.out()
    assert app.brute_toggle.cget("text") == "All shifts"
    assert d.toggle_state() == "normal"
    assert len(app.brute.get_children()) == 26
    print("caesar:", d.out())

    # --- the toggle survives being switched off ----------------------------
    app.show_brute.set(False)
    app._toggle_brute()
    app.update()
    assert not d.panel_shown()
    # the real guarantee: the toggle is not a child of the panel it hides
    assert not str(app.brute_toggle).startswith(str(app.brute_frame) + "."), \
        "toggle lives inside the panel it hides"
    assert app.brute_toggle.master.grid_info(), "the toggle's strip was unmapped"
    app.show_brute.set(True)
    app._toggle_brute()
    app.update()
    assert d.panel_shown()
    print("toggle stays reachable while the panel is hidden")

    # --- Atbash: no params, self-inverse, no panel -------------------------
    d.pick("Atbash")
    assert app.param_vars == {}, app.param_vars
    d.set("Attack at dawn!")
    d.mode("encode")
    assert d.out() == "Zggzxp zg wzdm!", d.out()
    d.mode("decode")
    assert d.out() == "Zggzxp zg wzdm!", d.out()   # its own inverse
    print("atbash:", d.out())
    assert d.toggle_state() == "disabled"
    assert not d.panel_shown()
    assert "no key to choose" in d.hint()

    # --- Vigenere ----------------------------------------------------------
    d.pick(VIGENERE)
    assert "keyword" in app.param_vars
    app.param_vars["keyword"].set("LEMON")
    d.mode("encode")
    d.set("ATTACKATDAWN")
    assert d.out() == "LXFOPVEFRNHR", d.out()      # the canonical textbook case
    print("vigenere:", d.out())

    d.mode("decode")
    d.set("LXFOPVEFRNHR")
    assert d.out() == "ATTACKATDAWN", d.out()

    # case and punctuation survive a round trip
    d.mode("encode")
    d.set("Meet me at the docks, 9pm!")
    app.send_up()
    d.mode("decode")
    assert d.out() == "Meet me at the docks, 9pm!", d.out()
    print("vigenere round trip through punctuation ok")

    # a keyword with no letters reports plainly rather than crashing
    app.param_vars["keyword"].set("123")
    app.update()
    assert d.out() == ""
    assert d.status().startswith("Vigen"), d.status()
    assert "Error" not in d.status(), d.status()
    print("empty-key message:", d.status())

    app.param_vars["keyword"].set("LEMON")
    app.update()
    assert d.toggle_state() == "disabled"
    assert "too many keys" in d.hint()

    # --- back to Caesar: the panel and the preference come back ------------
    d.pick("Caesar")
    assert d.toggle_state() == "normal"
    assert d.panel_shown()
    assert app.brute.heading("shift")["text"] == "Shift"
    d.mode("decode")
    app.param_vars["shift"].set(3)
    d.set("Dwwdfn dw gdzq!")
    assert d.out() == "Attack at dawn!", d.out()
    assert len(app.brute.get_children()) == 26
    print("returned to caesar cleanly")

    app.destroy()
    print("\nAll checks passed.")


def test_panel():
    main()


if __name__ == "__main__":
    main()
