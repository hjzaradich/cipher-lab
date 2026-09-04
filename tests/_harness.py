"""Shared setup for the test suites.

Importing this puts the project root on sys.path, so the suites run from
anywhere -- `python tests/test_caesar.py`, `python -m pytest`, or the runner in
`run_tests.py` -- without knowing where the project lives.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def make_app(withdraw=True):
    """A real CipherLab window, hidden unless a test needs events delivered."""
    from app import CipherLab

    app = CipherLab()
    if withdraw:
        app.withdraw()
    else:
        # Mapped but parked off to the side: Tk only delivers generated events
        # to a window that is actually on screen.
        app.geometry("+2000+2000")
    app.update()
    return app


class Driver:
    """The handful of moves every UI suite makes."""

    def __init__(self, app):
        self.app = app

    def out(self) -> str:
        return self.app.output.get("1.0", "end-1c")

    def source(self) -> str:
        return self.app.input.get("1.0", "end-1c")

    def status(self) -> str:
        return self.app.status.get()

    def set(self, text: str):
        self.app.input.delete("1.0", "end")
        self.app.input.insert("1.0", text)
        self.app.update()

    def pick(self, name: str):
        from ciphers import REGISTRY

        self.app.picker.current([c.name for c in REGISTRY].index(name))
        self.app._on_cipher_change()
        self.app.update()

    def mode(self, direction: str):
        self.app.mode.set(direction)
        self.app.refresh()
        self.app.update()

    def panel_shown(self) -> bool:
        # winfo_ismapped is always false on a withdrawn window, so ask the
        # geometry manager instead of the screen.
        return bool(self.app.brute_frame.grid_info())

    def toggle_state(self) -> str:
        return str(self.app.brute_toggle.cget("state"))

    def hint(self) -> str:
        return self.app.brute_hint.cget("text")

    def wait(self, ms: int):
        """Let Tk's event loop run for a while, for timed animations."""
        self.app.after(ms, self.app.quit)
        self.app.mainloop()
