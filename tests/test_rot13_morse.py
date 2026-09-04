"""ROT13 and Morse, plus every cipher surviving a switch with text present."""

from _harness import Driver, make_app

VIGENERE = "Vigenère"


def main():
    app = make_app()
    d = Driver(app)

    from ciphers import REGISTRY

    names = [c.name for c in REGISTRY]
    for required in ("Caesar", "ROT13", "Atbash", VIGENERE, "Morse"):
        assert required in names, (required, names)
    print("registry:", names)

    # every cipher must survive being selected with the previous one's text
    d.set("Attack at dawn!")
    for name in names:
        d.pick(name)
        assert "Error" not in d.status(), (name, d.status())
    print("all of them select cleanly with text in the box")

    # --- ROT13 -------------------------------------------------------------
    d.pick("ROT13")
    assert app.param_vars == {}
    d.set("Attack at dawn!")
    d.mode("encode")
    assert d.out() == "Nggnpx ng qnja!", d.out()
    print("rot13 encode:", d.out())
    d.mode("decode")
    assert d.out() == "Nggnpx ng qnja!", d.out()    # self-inverse
    app.send_up()
    app.update()
    assert d.out() == "Attack at dawn!", d.out()    # twice returns the original
    assert d.toggle_state() == "disabled"
    assert not d.panel_shown()
    assert "no key to choose" in d.hint()

    # --- Morse -------------------------------------------------------------
    d.pick("Morse")
    assert app.param_vars == {}
    d.mode("encode")
    d.set("SOS Attack at dawn!")
    expected = "... --- ... / .- - - .- -.-. -.- / .- - / -.. .- .-- -. -.-.--"
    assert d.out() == expected, d.out()
    print("morse encode:", d.out())

    # send the dots and dashes back up and decode them
    app.send_up()
    d.mode("decode")
    assert d.out() == "SOS ATTACK AT DAWN!", d.out()
    print("morse decode:", d.out())

    # decoding is forgiving about separators
    for variant in (
        ".... ..   .-- --- .-. .-.. -..",
        ".... .. | .-- --- .-. .-.. -..",
        "•••• •• / •—— ——— "
        "•—• •—•• —••",
    ):
        d.set(variant)
        assert d.out() == "HI WORLD", (variant, d.out())
    print("morse tolerates spacing, pipes, bullets and dashes")

    # an unreadable token shows as ? rather than throwing
    d.set(".... ..---.-.-.-.-... ..")
    assert d.out() == "H?I", d.out()
    assert "Error" not in d.status()

    # blank input is not an error
    d.set("")
    assert d.out() == ""
    assert d.toggle_state() == "disabled"
    assert "no key to choose" in d.hint()

    # --- Caesar's table still returns intact -------------------------------
    d.pick("Caesar")
    assert d.toggle_state() == "normal"
    assert d.panel_shown()
    d.mode("decode")
    app.param_vars["shift"].set(3)
    d.set("Dwwdfn dw gdzq!")
    assert d.out() == "Attack at dawn!", d.out()
    assert len(app.brute.get_children()) == 26
    print("caesar table intact after the other ciphers")

    app.destroy()
    print("\nAll checks passed.")


def test_rot13_morse():
    main()


if __name__ == "__main__":
    main()
