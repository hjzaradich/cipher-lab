"""The face in the corner: where it sits, the wink, the blink, and the
collisions between the two.

This one needs a window that is actually on screen, because Tk only delivers
generated mouse events to a mapped window.
"""

from _harness import Driver, make_app


def main():
    import smiley as smiley_module
    import theme

    app = make_app(withdraw=False)
    d = Driver(app)
    face = app.smiley

    def eye_open(side):
        return face.itemcget(face.eyes[side], "state") in ("", "normal")

    def lid_shown(side):
        return face.itemcget(face.lids[side], "state") == "normal"

    # --- placement ---------------------------------------------------------
    assert face.master.grid_info()["row"] == 4, face.master.grid_info()
    assert face.grid_info()["sticky"] == "e", face.grid_info()
    assert face.bind("<Button-1>"), "nothing bound to a click"
    assert str(face.cget("cursor")) == "hand2"
    print("footer row 4, right-aligned, click bound, hand cursor")

    # --- a blink is scheduled from the start -------------------------------
    assert face._blink_job is not None, "no blink scheduled"
    low, high = smiley_module.BLINK_GAP_MS
    gaps = [face._next_gap() for _ in range(300)]
    assert all(low <= gap <= high for gap in gaps), (min(gaps), max(gaps))
    assert max(gaps) - min(gaps) > (high - low) * 0.5, "gaps barely vary"
    print("blink gaps random in %.1f-%.1fs (sampled %.1f-%.1f)"
          % (low / 1000, high / 1000, min(gaps) / 1000, max(gaps) / 1000))

    # --- a real click winks one eye ----------------------------------------
    assert eye_open("right") and not lid_shown("right")
    face.event_generate("<Button-1>", x=15, y=15, when="now")
    app.update()
    assert lid_shown("right") and not lid_shown("left"), "wink closed both eyes"
    assert face.is_winking
    print("click -> right eye closes, left stays open")

    d.wait(500)
    assert eye_open("right"), "the eye stayed shut"
    assert not face.is_winking

    # --- a blink closes both -----------------------------------------------
    face.blink(double=False)
    app.update()
    assert lid_shown("left") and lid_shown("right"), "blink did not close both"
    print("blink -> both eyes closed")
    d.wait(400)
    assert eye_open("left") and eye_open("right"), "eyes stayed shut"
    print("blink -> both reopen")

    # --- clicking mid-blink takes over cleanly -----------------------------
    face.blink(double=False)
    app.update()
    assert lid_shown("left") and lid_shown("right")
    face.wink()                    # click while both eyes are closed
    app.update()
    assert lid_shown("right") and not lid_shown("left"), \
        "left eye stuck shut after a wink"
    d.wait(500)
    assert eye_open("left") and eye_open("right"), "an eye stayed closed"
    assert face._blink_job is not None, "blinking did not resume after the wink"
    print("click during a blink -> becomes a wink, both recover, blinking resumes")

    # --- a blink during a wink is deferred, not dropped --------------------
    face.wink()
    app.update()
    face.blink(double=False)       # the timer fires mid-wink
    app.update()
    assert not lid_shown("left"), "the blink overrode the wink"
    assert lid_shown("right")
    assert face._blink_job is not None, "the blink was dropped, not rescheduled"
    print("blink during a wink -> deferred, wink undisturbed")
    d.wait(500)

    # --- double blinks come back to a resting face -------------------------
    face.blink(double=True)
    app.update()
    assert lid_shown("left") and lid_shown("right")
    d.wait(600)
    assert eye_open("left") and eye_open("right"), "a double blink left an eye shut"
    assert face._blink_job is not None
    print("double blink -> resolves and reschedules")

    # --- rapid clicks recover ----------------------------------------------
    for _ in range(5):
        face.wink()
    app.update()
    assert lid_shown("right")
    d.wait(500)
    assert eye_open("right"), "stuck winking"
    print("rapid clicks recover cleanly")

    # --- hover brightens and restores --------------------------------------
    face.event_generate("<Enter>", when="now")
    app.update()
    assert face.itemcget(face.face, "outline").lower() == theme.ACCENT_BRIGHT.lower()
    face.event_generate("<Leave>", when="now")
    app.update()
    assert face.itemcget(face.face, "outline").lower() == theme.ACCENT.lower()
    print("hover brightens and restores")

    # --- teardown cancels timers -------------------------------------------
    face._stop()
    assert face._blink_job is None and face._wink_job is None
    app.destroy()

    # destroying with animations in flight must not raise into stderr
    for _ in range(3):
        again = make_app()
        again.smiley.blink(double=True)
        again.smiley.wink()
        again.destroy()
    print("destroy with timers pending: clean")

    print("\nAll checks passed.")


def test_smiley():
    main()


if __name__ == "__main__":
    main()
