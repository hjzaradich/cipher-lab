"""Caesar: the shift controls, the round trip, and the all-shifts table."""

from _harness import Driver, make_app


def main():
    app = make_app()
    d = Driver(app)

    # type a message, encode it
    d.mode("encode")
    d.set("Attack at dawn!")
    app.param_vars["shift"].set(3)
    app.update()
    assert d.out() == "Dwwdfn dw gdzq!", d.out()
    print("encode shift 3 ->", d.out())

    # change the offset via the spinbox variable
    app.param_vars["shift"].set(13)
    app.update()
    assert d.out() == "Nggnpx ng qnja!", d.out()
    print("encode shift 13 ->", d.out())

    # nudge buttons wrap around the alphabet
    app.param_vars["shift"].set(25)
    app._nudge(1)
    app.update()
    assert app.param_vars["shift"].get() == 0, app.param_vars["shift"].get()
    app._nudge(-1)
    assert app.param_vars["shift"].get() == 25

    # decode mode round-trips
    app.param_vars["shift"].set(3)
    d.mode("decode")
    d.set("Dwwdfn dw gdzq!")
    assert d.out() == "Attack at dawn!", d.out()
    print("decode shift 3 ->", d.out())

    # the table lists all 26 and highlights the live shift
    rows = app.brute.get_children()
    assert len(rows) == 26, len(rows)
    assert app.brute.item(rows[3], "values")[1].startswith("Attack at dawn!")
    assert "current" in app.brute.item(rows[3], "tags")
    print("brute row 3 ->", app.brute.item(rows[3], "values"))

    # double-clicking a row adopts that shift
    app.param_vars["shift"].set(0)
    app.update()
    rows = app.brute.get_children()   # the panel rebuilt, so the ids are new
    app.brute.selection_set(rows[3])
    app._adopt_row()
    app.update()
    assert app.param_vars["shift"].get() == 3
    assert app.mode.get() == "decode"
    assert d.out() == "Attack at dawn!", d.out()

    # the slider drives the value, and refresh syncs it back
    app._on_slide("17.4", app._first_int_spec())
    app.update()
    assert app.param_vars["shift"].get() == 17
    assert abs(app.param_scales["shift"].get() - 17) < 0.01

    # send-up feeds the result back into the input
    app.param_vars["shift"].set(3)
    app.update()
    app.send_up()
    app.update()
    assert d.source() == "Attack at dawn!"

    # an empty spinbox mid-edit must not crash the refresh
    app.param_vars["shift"].set(5)
    d.set("")
    assert d.out() == ""

    # toggling the panel off and on again
    app.show_brute.set(False)
    app._toggle_brute()
    app.update()
    app.show_brute.set(True)
    app._toggle_brute()
    app.update()
    assert len(app.brute.get_children()) == 26

    app.destroy()
    print("\nAll checks passed.")


def test_caesar():
    main()


if __name__ == "__main__":
    main()
