"""A small face in the corner. He blinks on his own, and winks when clicked."""

import random
import tkinter as tk

import theme

SIZE = 30

WINK_MS = 320          # one eye, held long enough to read as deliberate
BLINK_MS = 130         # both eyes, quick enough to look involuntary
DOUBLE_BLINK_MS = 150  # gap before the second blink of a pair
DOUBLE_BLINK_CHANCE = 0.25
BLINK_GAP_MS = (2600, 7000)


class Smiley(tk.Canvas):
    def __init__(self, parent, size=SIZE):
        super().__init__(parent, width=size, height=size,
                         background=theme.BG, highlightthickness=0,
                         borderwidth=0, cursor="hand2")
        self.size = size
        self._blink_job = None
        self._wink_job = None
        self._draw()

        self.bind("<Button-1>", self.wink)
        self.bind("<Enter>", lambda _e: self._tint(theme.ACCENT_BRIGHT))
        self.bind("<Leave>", lambda _e: self._tint(theme.ACCENT))
        self.bind("<Destroy>", self._stop)   # no timers firing after teardown

        self._schedule_blink()

    # ---------- drawing ----------

    def _dot(self, cx, cy, radius, **options):
        return self.create_oval(cx - radius, cy - radius,
                                cx + radius, cy + radius, **options)

    def _draw(self):
        s = self.size
        self.face = self.create_oval(2, 2, s - 2, s - 2,
                                     outline=theme.ACCENT, width=2)

        eye_y = s * 0.36
        eye_r = s * 0.06
        reach = s * 0.10
        self.eyes, self.lids = {}, {}
        for side, cx in (("left", s * 0.34), ("right", s * 0.66)):
            self.eyes[side] = self._dot(cx, eye_y, eye_r,
                                        fill=theme.ACCENT, outline="")
            # the closed eye, kept hidden until it is needed
            self.lids[side] = self.create_line(
                cx - reach, eye_y, cx + reach, eye_y, fill=theme.ACCENT,
                width=2, capstyle="round", state="hidden")

        # 200 deg to 340 deg traces the lower half of the ellipse: a smile.
        self.mouth = self.create_arc(s * 0.22, s * 0.20, s * 0.78, s * 0.80,
                                     start=200, extent=140, style="arc",
                                     outline=theme.ACCENT, width=2)

    def _tint(self, colour):
        for item in (self.face, self.mouth):
            self.itemconfigure(item, outline=colour)
        for side in self.eyes:
            self.itemconfigure(self.eyes[side], fill=colour)
            self.itemconfigure(self.lids[side], fill=colour)

    def _set_eye(self, side, closed):
        self.itemconfigure(self.eyes[side], state="hidden" if closed else "normal")
        self.itemconfigure(self.lids[side], state="normal" if closed else "hidden")

    # ---------- timers ----------

    def _cancel(self, job):
        if job is not None:
            try:
                self.after_cancel(job)
            except tk.TclError:      # already fired, or the widget is going away
                pass

    def _stop(self, _event=None):
        self._cancel(self._blink_job)
        self._cancel(self._wink_job)
        self._blink_job = self._wink_job = None

    def _next_gap(self) -> int:
        return random.randint(*BLINK_GAP_MS)

    def _schedule_blink(self):
        self._cancel(self._blink_job)
        self._blink_job = self.after(self._next_gap(), self.blink)

    # ---------- blinking ----------

    def blink(self, double=None):
        """Both eyes, briefly. Skipped while a wink is showing."""
        self._blink_job = None
        if self.is_winking:
            self._schedule_blink()
            return
        if double is None:
            double = random.random() < DOUBLE_BLINK_CHANCE
        for side in self.eyes:
            self._set_eye(side, closed=True)
        self._blink_job = self.after(BLINK_MS, lambda: self._end_blink(double))

    def _end_blink(self, double):
        self._blink_job = None
        for side in self.eyes:
            self._set_eye(side, closed=False)
        if double:
            self._blink_job = self.after(DOUBLE_BLINK_MS,
                                         lambda: self.blink(double=False))
        else:
            self._schedule_blink()

    # ---------- winking ----------

    def wink(self, _event=None):
        """One eye, on click. Takes precedence over a blink in progress."""
        self._cancel(self._blink_job)
        self._blink_job = None
        self._cancel(self._wink_job)
        self._set_eye("left", closed=False)   # in case a blink had shut it
        self._set_eye("right", closed=True)
        self._wink_job = self.after(WINK_MS, self._end_wink)

    def _end_wink(self):
        self._wink_job = None
        self._set_eye("right", closed=False)
        self._schedule_blink()

    @property
    def is_winking(self) -> bool:
        return self._wink_job is not None

    @property
    def is_blinking(self) -> bool:
        return self.itemcget(self.lids["left"], "state") == "normal"
