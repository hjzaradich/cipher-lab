"""Cipher Lab -- a desktop workbench for encoding and decoding messages."""

import sys
import tkinter as tk
from tkinter import ttk

import theme
from smiley import Smiley
from ciphers import ChoiceParam, REGISTRY, CipherError, IntParam, TextParam

PREVIEW_CHARS = 72

# Ctrl+arrow is Mission Control on macOS, so the OS would swallow it there.
MODIFIER = "Command" if sys.platform == "darwin" else "Control"
MODIFIER_LABEL = "Cmd" if sys.platform == "darwin" else "Ctrl"


class CipherLab(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cipher Lab")
        self.geometry("1020x700")
        self.minsize(780, 540)

        self.cipher = REGISTRY[0]
        self.mode = tk.StringVar(value="decode")
        self.status = tk.StringVar(value="")
        self.show_brute = tk.BooleanVar(value=True)
        self.param_vars: dict[str, tk.Variable] = {}
        self.param_scales: dict[str, ttk.Scale] = {}
        self._syncing = False

        self._build_style()
        self._build_layout()
        self._build_params()
        self._sync_direction()
        self._sync_brute_chrome()
        self.refresh()

    # ---------- construction ----------

    def _build_style(self):
        theme.apply(self)

    def _build_layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=2)
        self.rowconfigure(3, weight=3)

        # --- control bar -------------------------------------------------
        bar = ttk.Frame(self, padding=(12, 10, 12, 6))
        bar.grid(row=0, column=0, sticky="ew")
        bar.columnconfigure(9, weight=1)

        col = 0
        if len(REGISTRY) > 1:
            ttk.Label(bar, text="Cipher").grid(row=0, column=col, padx=(0, 6))
            picker = ttk.Combobox(
                bar, state="readonly", width=16,
                values=[c.name for c in REGISTRY],
            )
            picker.set(self.cipher.name)
            picker.bind("<<ComboboxSelected>>", self._on_cipher_change)
            picker.grid(row=0, column=col + 1, padx=(0, 16))
            self.picker = picker
            col += 2

        self.params_frame = ttk.Frame(bar)
        self.params_frame.grid(row=0, column=col, sticky="w")

        modes = ttk.Frame(bar)
        modes.grid(row=0, column=col + 1, padx=(20, 0), sticky="w")
        self.encode_radio = ttk.Radiobutton(
            modes, text="Encode", value="encode",
            variable=self.mode, command=self.refresh)
        self.encode_radio.pack(side="left")
        self.decode_radio = ttk.Radiobutton(
            modes, text="Decode", value="decode",
            variable=self.mode, command=self.refresh)
        self.decode_radio.pack(side="left", padx=(8, 0))

        ttk.Label(bar, textvariable=self.status, style="Blurb.TLabel").grid(
            row=0, column=9, sticky="e")

        # --- text panes --------------------------------------------------
        panes = ttk.Frame(self, padding=(12, 0, 12, 6))
        panes.grid(row=1, column=0, sticky="nsew")
        panes.columnconfigure(0, weight=1, uniform="pane")
        panes.columnconfigure(1, weight=1, uniform="pane")
        panes.rowconfigure(1, weight=1)

        in_head = ttk.Frame(panes)
        in_head.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Label(in_head, text="Message", style="Heading.TLabel").pack(side="left")
        ttk.Button(in_head, text="Clear", width=7,
                   command=self.clear_input).pack(side="right")
        ttk.Button(in_head, text="Paste", width=7,
                   command=self.paste_input).pack(side="right", padx=(0, 4))

        out_head = ttk.Frame(panes)
        out_head.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.out_label = ttk.Label(out_head, text="Result", style="Heading.TLabel")
        self.out_label.pack(side="left")
        ttk.Button(out_head, text="Copy", width=7,
                   command=self.copy_output).pack(side="right")
        ttk.Button(out_head, text="Send up", width=9,
                   command=self.send_up).pack(side="right", padx=(0, 4))

        self.input = self._text_pane(panes, 0, (0, 6))
        self.output = self._text_pane(panes, 1, (6, 0))
        self.output.configure(state="disabled", **theme.TEXT_PANE_READONLY)
        self.input.bind("<<Modified>>", self._on_input_modified)

        # --- brute force -------------------------------------------------
        # The toggle sits in its own always-visible strip: inside the panel it
        # hides, switching it off would take the control away with it.
        strip = ttk.Frame(self, padding=(12, 6, 12, 4))
        strip.grid(row=2, column=0, sticky="ew")
        self.brute_toggle = ttk.Checkbutton(
            strip, text="All shifts", variable=self.show_brute,
            style="Toggle.TCheckbutton", command=self._toggle_brute)
        self.brute_toggle.pack(side="left")
        self.brute_hint = ttk.Label(strip, text="", style="Blurb.TLabel")
        self.brute_hint.pack(side="left", padx=(12, 0))

        self.brute_frame = ttk.Frame(self, padding=(12, 0, 12, 10))
        self.brute_frame.grid(row=3, column=0, sticky="nsew")
        self.brute_frame.columnconfigure(0, weight=1)
        self.brute_frame.rowconfigure(0, weight=1)

        self.brute = ttk.Treeview(
            self.brute_frame, columns=("shift", "text"), show="headings",
            selectmode="browse", height=12,
        )
        self.brute.heading("shift", text="Shift")
        self.brute.heading("text", text="Decoded with that shift", anchor="w")
        self.brute.column("shift", width=60, anchor="center", stretch=False)
        self.brute.column("text", anchor="w")
        self.brute.tag_configure("current", background=theme.HIGHLIGHT,
                                 foreground=theme.ACCENT_BRIGHT)
        self.brute.grid(row=0, column=0, sticky="nsew")
        bscroll = ttk.Scrollbar(self.brute_frame, orient="vertical",
                                command=self.brute.yview)
        self.brute.configure(yscrollcommand=bscroll.set)
        bscroll.grid(row=0, column=1, sticky="ns")
        self.brute.bind("<Double-1>", self._adopt_row)
        self.brute.bind("<Return>", self._adopt_row)

        # --- footer ------------------------------------------------------
        footer = ttk.Frame(self, padding=(12, 0, 10, 8))
        footer.grid(row=4, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        self.smiley = Smiley(footer)
        self.smiley.grid(row=0, column=1, sticky="e")

        # --- keyboard ----------------------------------------------------
        self.bind_all("<%s-Left>" % MODIFIER, lambda e: self._nudge(-1))
        self.bind_all("<%s-Right>" % MODIFIER, lambda e: self._nudge(1))
        self.input.focus_set()

    def _text_pane(self, parent, column, padx):
        wrap = ttk.Frame(parent)
        wrap.grid(row=1, column=column, sticky="nsew", padx=padx, pady=(4, 0))
        wrap.columnconfigure(0, weight=1)
        wrap.rowconfigure(0, weight=1)
        # A small requested height keeps the Text from claiming the window;
        # the grid row weights decide the real split.
        text = tk.Text(wrap, wrap="word", font=theme.mono(11), undo=True, height=6,
                       borderwidth=0, padx=8, pady=6, **theme.TEXT_PANE)
        text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(wrap, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")
        return text

    def _build_params(self):
        """Render one control group per parameter the current cipher declares."""
        for child in self.params_frame.winfo_children():
            child.destroy()
        self.param_vars.clear()
        self.param_scales.clear()
        self.cipher.refresh_params()   # contacts and the like change at runtime

        for spec in self.cipher.params:
            group = ttk.Frame(self.params_frame)
            group.pack(side="left", padx=(0, 18))
            ttk.Label(group, text=spec.label).pack(side="left", padx=(0, 6))

            if isinstance(spec, IntParam):
                var = tk.IntVar(value=spec.default)
                ttk.Button(group, text="◀", width=3,
                           command=lambda s=spec: self._nudge(-1, s)).pack(side="left")
                ttk.Spinbox(
                    group, from_=spec.minimum, to=spec.maximum, width=4,
                    textvariable=var, font=theme.mono(12), justify="center",
                    command=self.refresh, wrap=spec.wrap,
                ).pack(side="left", padx=4)
                ttk.Button(group, text="▶", width=3,
                           command=lambda s=spec: self._nudge(1, s)).pack(side="left")
                scale = ttk.Scale(
                    group, from_=spec.minimum, to=spec.maximum, length=200,
                    command=lambda v, s=spec: self._on_slide(v, s),
                )
                scale.pack(side="left", padx=(10, 0))
                self.param_scales[spec.key] = scale
                var.trace_add("write", lambda *_: self.refresh())
            elif isinstance(spec, ChoiceParam):
                var = tk.StringVar(value=spec.default or spec.choices[0])
                width = max(len(choice) for choice in spec.choices) + 2
                ttk.Combobox(group, textvariable=var, values=list(spec.choices),
                             state="readonly", width=width).pack(side="left")
                var.trace_add("write", lambda *_: self.refresh())
            elif isinstance(spec, TextParam):
                var = tk.StringVar(value=spec.default)
                ttk.Entry(group, textvariable=var, width=18,
                          font=theme.mono(11)).pack(side="left")
                var.trace_add("write", lambda *_: self.refresh())
            else:
                continue
            self.param_vars[spec.key] = var

        if self.cipher.uses_keystore:
            ttk.Button(self.params_frame, text="Keys…",
                       command=self._open_keys).pack(side="left", padx=(4, 0))

        for spec in self.cipher.params:
            if isinstance(spec, IntParam):
                self._sync_scale(spec)

    def _open_keys(self):
        from keys_dialog import KeysDialog
        dialog = KeysDialog(self, self.cipher.store, on_change=self._keys_changed)
        self.wait_window(dialog)
        self._keys_changed()

    def _keys_changed(self):
        """Contacts or lock state moved, so rebuild the controls and reconvert.

        Rebuilding replaces every widget, so any dropdown selection still on
        offer is carried across -- otherwise adding a contact could silently
        change who you are writing to.
        """
        remembered = {}
        for key, var in self.param_vars.items():
            try:
                remembered[key] = var.get()
            except tk.TclError:      # a control mid-edit; let it fall back
                pass

        self._build_params()

        for spec in self.cipher.params:
            if not isinstance(spec, ChoiceParam):
                continue
            previous = remembered.get(spec.key)
            if previous in spec.choices and spec.key in self.param_vars:
                self.param_vars[spec.key].set(previous)
        self.refresh()

    # ---------- parameter plumbing ----------

    def _values(self) -> dict:
        out = self.cipher.defaults()
        for key, var in self.param_vars.items():
            try:
                out[key] = var.get()
            except tk.TclError:  # spinbox is mid-edit or empty
                pass
        return out

    def _first_int_spec(self):
        for spec in self.cipher.params:
            if isinstance(spec, IntParam):
                return spec
        return None

    def _nudge(self, delta: int, spec=None):
        spec = spec or self._first_int_spec()
        if spec is None:
            return
        var = self.param_vars[spec.key]
        try:
            value = var.get() + delta
        except tk.TclError:
            value = spec.default
        span = spec.maximum - spec.minimum + 1
        if spec.wrap:
            value = (value - spec.minimum) % span + spec.minimum
        else:
            value = max(spec.minimum, min(spec.maximum, value))
        var.set(value)

    def _on_slide(self, raw, spec):
        if self._syncing:
            return
        value = int(round(float(raw)))
        var = self.param_vars[spec.key]
        try:
            unchanged = var.get() == value
        except tk.TclError:
            unchanged = False
        if not unchanged:
            var.set(value)

    def _sync_scale(self, spec):
        """Push the authoritative integer value back into the slider."""
        scale = self.param_scales.get(spec.key)
        if scale is None:
            return
        self._syncing = True
        try:
            scale.set(self.param_vars[spec.key].get())
        except tk.TclError:
            pass
        finally:
            self._syncing = False

    def _on_cipher_change(self, _event=None):
        self.cipher = REGISTRY[self.picker.current()]
        self._build_params()
        self._sync_direction()
        self._sync_brute_chrome()
        self.refresh()

    # ---------- the actual work ----------

    def _on_input_modified(self, _event):
        if self.input.edit_modified():
            self.input.edit_modified(False)
            self.refresh()

    def refresh(self):
        source = self.input.get("1.0", "end-1c")
        values = self._values()
        decoding = self.mode.get() == "decode"

        transform = self.cipher.decode if decoding else self.cipher.encode
        try:
            result = transform(source, **values)
        except CipherError as exc:  # the user can fix this one; say it plainly
            result = ""
            self.status.set(str(exc))
        except Exception as exc:  # anything else should not take the window down
            result = ""
            self.status.set("%s: %s" % (type(exc).__name__, exc))
        else:
            verb = "Hashed" if self.cipher.one_way else (
                "Decoded" if decoding else "Encoded")
            self.status.set("%s · %d chars" % (verb, len(source)))

        self.out_label.configure(text="Digest" if self.cipher.one_way else (
            "Decoded" if decoding else "Encoded"))
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", result)
        self.output.configure(state="disabled")

        spec = self._first_int_spec()
        if spec is not None:
            self._sync_scale(spec)

        self._refresh_brute(source, values)

    def _refresh_brute(self, source, values):
        if not (self.show_brute.get() and self._supports_brute()):
            return
        rows = self.cipher.candidates(source, **values)
        if rows is None:
            return

        spec = self._first_int_spec()
        current = str(values.get(spec.key, "")) if spec else ""
        selected = None
        self.brute.delete(*self.brute.get_children())
        for label, text in rows:
            preview = text[:PREVIEW_CHARS].replace("\n", " ↵ ")
            if len(text) > PREVIEW_CHARS:
                preview += " …"
            tags = ("current",) if label == current else ()
            item = self.brute.insert("", "end", values=(label, preview), tags=tags)
            if label == current:
                selected = item
        if selected:
            self.brute.selection_set(selected)
            self.brute.see(selected)

    def _adopt_row(self, _event=None):
        selection = self.brute.selection()
        spec = self._first_int_spec()
        if not selection or spec is None:
            return
        label = self.brute.item(selection[0], "values")[0]
        self.mode.set("decode")
        self.param_vars[spec.key].set(int(label))

    def _toggle_brute(self):
        self._sync_brute_chrome()
        self.refresh()

    def _sync_direction(self):
        """One-way ciphers can only encode, so do not offer Decode at all."""
        if self.cipher.one_way:
            self.mode.set("encode")
            self.decode_radio.configure(state="disabled")
        else:
            self.decode_radio.configure(state="normal")

    def _supports_brute(self) -> bool:
        """Whether this cipher can enumerate every decoding of a message."""
        try:
            return self.cipher.candidates("", **self.cipher.defaults()) is not None
        except Exception:
            return False

    def _sync_brute_chrome(self):
        """Label and show the panel to suit the current cipher."""
        noun = self.cipher.key_noun
        supported = self._supports_brute()
        showing = supported and self.show_brute.get()

        self.brute_toggle.configure(
            text="All %ss" % noun, state="normal" if supported else "disabled")
        self.brute.heading("shift", text=noun.capitalize())
        self.brute.heading("text", text="Decoded with that %s" % noun, anchor="w")

        if not supported:
            if self.cipher.one_way:
                reason = "one-way, nothing to reverse"
            elif not self.cipher.params:
                reason = "no key to choose"
            else:
                reason = "too many keys to list"
            self.brute_hint.configure(text="%s — %s" % (self.cipher.name, reason))
        elif showing:
            self.brute_hint.configure(
                text="double-click a row to adopt that %s" % noun)
        else:
            self.brute_hint.configure(text="")

        if showing:
            self.brute_frame.grid()
            self.rowconfigure(3, weight=3)
        else:
            self.brute_frame.grid_remove()
            self.rowconfigure(3, weight=0)

    # ---------- buttons ----------

    def clear_input(self):
        self.input.delete("1.0", "end")
        self.input.focus_set()

    def paste_input(self):
        try:
            clip = self.clipboard_get()
        except tk.TclError:
            return
        self.input.delete("1.0", "end")
        self.input.insert("1.0", clip)

    def copy_output(self):
        text = self.output.get("1.0", "end-1c")
        if not text:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status.set("Result copied to clipboard")

    def send_up(self):
        """Feed the result back in as the new message, for chaining passes."""
        text = self.output.get("1.0", "end-1c")
        self.input.delete("1.0", "end")
        self.input.insert("1.0", text)


def main():
    CipherLab().mainloop()


if __name__ == "__main__":
    main()
