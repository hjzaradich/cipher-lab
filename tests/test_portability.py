"""The cross-platform branches, checked by faking sys.platform before import.

Each platform runs in its own subprocess, because MODIFIER is decided at import
time and a module cannot be un-imported cleanly.
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
PLATFORMS = ("darwin", "linux", "win32")


def check(fake):
    """Run inside the subprocess, with sys.platform already rewritten."""
    sys.platform = fake
    sys.path.insert(0, str(HERE.parent))          # for _harness
    import _harness  # noqa: F401  (puts the project root on sys.path)

    import tkinter as tk
    import theme
    from app import MODIFIER, MODIFIER_LABEL, CipherLab

    expected = ("Command", "Cmd") if fake == "darwin" else ("Control", "Ctrl")
    assert (MODIFIER, MODIFIER_LABEL) == expected, (MODIFIER, MODIFIER_LABEL)
    print("%-7s modifier  -> %s (%s)" % (fake, MODIFIER, MODIFIER_LABEL))

    app = CipherLab()
    app.withdraw()

    sequence = "<%s-Left>" % MODIFIER
    assert app.bind_all(sequence), "no handler bound for " + sequence
    print("%-7s bound     -> %s" % (fake, sequence))

    # the Windows-only title bar call must be skipped without raising elsewhere
    theme._paint_title_bar(app)
    print("%-7s title bar -> %s"
          % (fake, "tinted" if fake == "win32" else "skipped cleanly"))

    # font selection must degrade to a real installed family, never to nothing
    picked = theme._first_installed(app, ("NoSuchFontXYZ", "Courier New"),
                                    "TkFixedFont")
    assert picked == "Courier New", picked
    fallback = theme._first_installed(app, ("NoSuchFontXYZ",), "TkFixedFont")
    installed = {name.lower() for name in tk.font.families(app)}
    assert fallback.lower() in installed, fallback
    print("%-7s fonts     -> skips missing, falls back to %r" % (fake, fallback))

    # and the app still converts correctly under the faked platform
    app.input.insert("1.0", "Attack at dawn!")
    app.mode.set("encode")
    app.param_vars["shift"].set(3)
    app.update()
    assert app.output.get("1.0", "end-1c") == "Dwwdfn dw gdzq!"
    print("%-7s cipher    -> works" % fake)

    app.destroy()


def main():
    for platform in PLATFORMS:
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(HERE), platform],
            capture_output=True, text=True)
        print(result.stdout.rstrip())
        if result.returncode:
            print(result.stderr.rstrip(), file=sys.stderr)
            raise AssertionError("portability check failed for " + platform)
    print("\nAll checks passed.")


def test_portability():
    main()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        check(sys.argv[1])
    else:
        main()
