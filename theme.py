"""Purple theme for Cipher Lab.

All colours live here. `apply(root)` restyles every ttk widget class the app
uses; `TEXT_PANE` and `TEXT_PANE_READONLY` carry the options for the plain
tk.Text widgets, which ttk styling does not reach.
"""

import ctypes
import sys
from tkinter import font as tkfont
from tkinter import ttk

# --- fonts -----------------------------------------------------------------
# Font families are per-platform, so name several and take the first that is
# actually installed. Tk substitutes silently for a missing family, which would
# quietly cost the message panes their monospacing.
MONO_CANDIDATES = ("Consolas", "Menlo", "SF Mono", "DejaVu Sans Mono",
                   "Liberation Mono", "Courier New")
UI_CANDIDATES = ("Segoe UI", "SF Pro Text", "Helvetica Neue", "Ubuntu",
                 "DejaVu Sans", "Arial")

MONO_FAMILY = "Courier"     # both are replaced by apply(), once there is a root
UI_FAMILY = "Helvetica"


def mono(size=11):
    return (MONO_FAMILY, size)


def ui(size=10, weight="normal"):
    return (UI_FAMILY, size, weight)


def _first_installed(root, candidates, fallback_named):
    installed = {name.lower() for name in tkfont.families(root)}
    for family in candidates:
        if family.lower() in installed:
            return family
    # Tk's own named fonts always resolve to something sensible.
    return tkfont.nametofont(fallback_named).actual("family")

# --- palette ---------------------------------------------------------------
BG = "#1b1029"            # window ground, deepest aubergine
SURFACE = "#241638"       # input fields, tables
SURFACE_DIM = "#1f1231"   # read-only surfaces
RAISED = "#33204d"        # buttons, table headings
BORDER = "#4a2f6e"
FG = "#ece6f5"            # primary text
MUTED = "#a892c4"         # secondary text
ACCENT = "#a855f7"        # the purple everything keys off
ACCENT_BRIGHT = "#c795fb"
ACCENT_DEEP = "#6d28d9"   # selections
HIGHLIGHT = "#3b1d63"     # the "this is your current shift" row
DISABLED = "#4b3a63"      # text on controls that cannot be used

TEXT_PANE = dict(
    background=SURFACE, foreground=FG,
    insertbackground=ACCENT_BRIGHT,
    selectbackground=ACCENT_DEEP, selectforeground="#ffffff",
    relief="flat", highlightthickness=1,
    highlightbackground=BORDER, highlightcolor=ACCENT,
)

TEXT_PANE_READONLY = dict(TEXT_PANE, background=SURFACE_DIM, foreground=ACCENT_BRIGHT)


def apply(root):
    global MONO_FAMILY, UI_FAMILY
    MONO_FAMILY = _first_installed(root, MONO_CANDIDATES, "TkFixedFont")
    UI_FAMILY = _first_installed(root, UI_CANDIDATES, "TkDefaultFont")

    root.configure(background=BG)

    style = ttk.Style(root)
    # Both the Windows (vista) and macOS (aqua) native themes ignore colour
    # options, so the palette only lands on clam.
    if "clam" in style.theme_names():
        style.theme_use("clam")

    style.configure(
        ".", background=BG, foreground=FG, fieldbackground=SURFACE,
        bordercolor=BORDER, darkcolor=BG, lightcolor=BG,
        troughcolor=SURFACE_DIM, arrowcolor=ACCENT_BRIGHT,
        focuscolor=ACCENT, insertcolor=FG,
    )
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=FG)
    style.configure("Heading.TLabel", font=ui(10, "bold"),
                    foreground=ACCENT_BRIGHT)
    style.configure("Blurb.TLabel", foreground=MUTED)

    style.configure("TButton", background=RAISED, foreground=FG,
                    bordercolor=BORDER, lightcolor=RAISED, darkcolor=RAISED,
                    relief="flat", padding=(8, 4))
    style.map(
        "TButton",
        background=[("disabled", SURFACE_DIM), ("pressed", ACCENT_DEEP),
                    ("active", ACCENT)],
        foreground=[("disabled", DISABLED), ("pressed", "#ffffff"),
                    ("active", "#ffffff")],
        lightcolor=[("active", ACCENT)], darkcolor=[("active", ACCENT)],
    )

    # clam names these indicatorbackground/indicatorforeground -- not
    # indicatorcolor, which it silently ignores.
    for widget in ("TRadiobutton", "TCheckbutton"):
        style.configure(widget, background=BG, foreground=FG, focuscolor=BG,
                        indicatorbackground=SURFACE, indicatorforeground=FG,
                        indicatorsize=12, indicatormargin=(0, 0, 6, 0),
                        upperbordercolor=BORDER, lowerbordercolor=BORDER,
                        padding=(2, 3))
        style.map(
            widget,
            background=[("active", BG)],
            foreground=[("active", ACCENT_BRIGHT)],
            indicatorbackground=[("selected", ACCENT), ("pressed", ACCENT_DEEP),
                                 ("active", RAISED)],
            indicatorforeground=[("selected", "#ffffff")],
            upperbordercolor=[("selected", ACCENT), ("active", ACCENT)],
            lowerbordercolor=[("selected", ACCENT), ("active", ACCENT)],
        )

    # clam's checked indicator is an X, which reads as "reject". Toggles that
    # light up when on are clearer, so borrow the Toolbutton layout.
    style.layout("Toggle.TCheckbutton", style.layout("Toolbutton"))
    style.configure("Toggle.TCheckbutton", background=RAISED, foreground=MUTED,
                    bordercolor=BORDER, lightcolor=RAISED, darkcolor=RAISED,
                    relief="flat", padding=(10, 4), font=ui(9, "bold"))
    style.map(
        "Toggle.TCheckbutton",
        background=[("disabled", SURFACE_DIM), ("selected", ACCENT_DEEP),
                    ("active", BORDER)],
        foreground=[("disabled", DISABLED), ("selected", "#ffffff"),
                    ("active", FG)],
        lightcolor=[("disabled", SURFACE_DIM), ("selected", ACCENT_DEEP)],
        darkcolor=[("disabled", SURFACE_DIM), ("selected", ACCENT_DEEP)],
    )

    style.configure("TSpinbox", fieldbackground=SURFACE, foreground=FG,
                    background=RAISED, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER,
                    arrowcolor=ACCENT_BRIGHT, insertcolor=FG, padding=(4, 3))
    style.map("TSpinbox", background=[("active", ACCENT)],
              bordercolor=[("focus", ACCENT)])

    style.configure("TEntry", fieldbackground=SURFACE, foreground=FG,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                    insertcolor=FG, padding=(4, 3))
    style.map("TEntry", bordercolor=[("focus", ACCENT)])

    style.configure("TCombobox", fieldbackground=SURFACE, foreground=FG,
                    background=RAISED, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER,
                    arrowcolor=ACCENT_BRIGHT, padding=(4, 3))
    style.map("TCombobox", fieldbackground=[("readonly", SURFACE)],
              bordercolor=[("focus", ACCENT)])
    # The dropdown list is a plain Tk listbox, styled through the option DB.
    root.option_add("*TCombobox*Listbox.background", SURFACE)
    root.option_add("*TCombobox*Listbox.foreground", FG)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT_DEEP)
    root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

    # Both scale elements read one style: the slider takes `background`, the
    # groove takes `troughcolor`. gripcount=0 drops clam's stripes on the grip.
    style.configure("Horizontal.TScale", background=ACCENT,
                    troughcolor=SURFACE_DIM, bordercolor=BORDER,
                    lightcolor=ACCENT_BRIGHT, darkcolor=ACCENT_DEEP,
                    gripcount=0, sliderlength=22, sliderthickness=16)
    style.map("Horizontal.TScale",
              background=[("active", ACCENT_BRIGHT)],
              lightcolor=[("active", ACCENT_BRIGHT)],
              darkcolor=[("active", ACCENT)])

    style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE,
                    foreground=FG, bordercolor=BORDER, borderwidth=1,
                    rowheight=22)
    style.map("Treeview", background=[("selected", ACCENT_DEEP)],
              foreground=[("selected", "#ffffff")])
    style.configure("Treeview.Heading", background=RAISED, foreground=MUTED,
                    relief="flat", padding=(6, 5), font=ui(9, "bold"))
    style.map("Treeview.Heading", background=[("active", BORDER)],
              foreground=[("active", FG)])

    style.configure("Vertical.TScrollbar", background=RAISED, troughcolor=BG,
                    bordercolor=BG, lightcolor=RAISED, darkcolor=RAISED,
                    arrowcolor=MUTED, relief="flat")
    style.map("Vertical.TScrollbar", background=[("active", ACCENT)],
              arrowcolor=[("active", "#ffffff")])

    _paint_title_bar(root)


def _paint_title_bar(root):
    """Colour the Windows title bar to match. No-op anywhere else."""
    if not sys.platform.startswith("win"):
        return
    try:
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        dwm = ctypes.windll.dwmapi.DwmSetWindowAttribute

        def colorref(hex_color):
            r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
            return ctypes.c_int(b << 16 | g << 8 | r)

        for attribute, value in (
            (20, ctypes.c_int(1)),      # use the dark window frame
            (35, colorref(BG)),         # caption background
            (36, colorref(FG)),         # caption text
            (34, colorref(BORDER)),     # frame border
        ):
            dwm(hwnd, ctypes.c_int(attribute), ctypes.byref(value),
                ctypes.sizeof(value))
    except Exception:
        pass  # older Windows, or no DWM -- the app just keeps the stock frame
