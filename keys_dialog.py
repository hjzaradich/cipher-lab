"""The Keys window: your identity, and the people you exchange messages with."""

import tkinter as tk
from tkinter import ttk

import theme
from ciphers.keystore import KeyStoreError


class PassphrasePrompt(tk.Toplevel):
    """Modal passphrase entry. Asks twice when setting a new one."""

    def __init__(self, parent, title, prompt, confirm=False):
        super().__init__(parent)
        self.title(title)
        self.configure(background=theme.BG)
        self.resizable(False, False)
        self.transient(parent)
        self.result = None

        body = ttk.Frame(self, padding=16)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text=prompt, style="Blurb.TLabel",
                  wraplength=360).grid(row=0, column=0, columnspan=2,
                                       sticky="w", pady=(0, 12))

        ttk.Label(body, text="Passphrase").grid(row=1, column=0, sticky="w",
                                                padx=(0, 8), pady=4)
        self.first = ttk.Entry(body, show="•", width=32, font=theme.mono(11))
        self.first.grid(row=1, column=1, sticky="ew", pady=4)

        self.second = None
        if confirm:
            ttk.Label(body, text="Again").grid(row=2, column=0, sticky="w",
                                               padx=(0, 8), pady=4)
            self.second = ttk.Entry(body, show="•", width=32,
                                    font=theme.mono(11))
            self.second.grid(row=2, column=1, sticky="ew", pady=4)

        self.message = ttk.Label(body, text="", style="Blurb.TLabel",
                                 wraplength=360)
        self.message.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        buttons = ttk.Frame(body)
        buttons.grid(row=4, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="OK", command=self._accept).pack(
            side="right", padx=(0, 6))

        self.bind("<Return>", lambda e: self._accept())
        self.bind("<Escape>", lambda e: self.destroy())
        self.first.focus_set()
        self.grab_set()
        self.wait_window(self)

    def _accept(self):
        value = self.first.get()
        if not value:
            self.message.configure(text="Enter a passphrase")
            return
        if self.second is not None and value != self.second.get():
            self.message.configure(text="Those two do not match")
            return
        self.result = value
        self.destroy()


class KeysDialog(tk.Toplevel):
    def __init__(self, parent, store, on_change=None):
        super().__init__(parent)
        self.store = store
        self.on_change = on_change
        self.title("Keys")
        self.configure(background=theme.BG)
        self.geometry("620x560")
        self.minsize(520, 480)
        self.transient(parent)

        self.status = tk.StringVar()
        self._build()
        self._refresh()
        self.grab_set()

    # ---------- layout ----------

    def _build(self):
        outer = ttk.Frame(self, padding=14)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(3, weight=1)

        # --- identity ---
        ttk.Label(outer, text="Your identity",
                  style="Heading.TLabel").grid(row=0, column=0, sticky="w")

        ident = ttk.Frame(outer, padding=(0, 6, 0, 12))
        ident.grid(row=1, column=0, sticky="ew")
        ident.columnconfigure(0, weight=1)

        self.identity_state = ttk.Label(ident, text="", style="Blurb.TLabel",
                                        wraplength=560)
        self.identity_state.grid(row=0, column=0, columnspan=3, sticky="w",
                                 pady=(0, 8))

        ttk.Label(ident, text="Public key — give this to the other person",
                  style="Blurb.TLabel").grid(row=1, column=0, columnspan=3,
                                             sticky="w")
        self.public_key = tk.Text(ident, height=2, wrap="char", borderwidth=0,
                                  padx=8, pady=6, font=theme.mono(10),
                                  **theme.TEXT_PANE_READONLY)
        self.public_key.grid(row=2, column=0, columnspan=3, sticky="ew",
                             pady=(4, 8))
        self.public_key.configure(state="disabled")

        self.create_button = ttk.Button(ident, text="Create identity",
                                        command=self._create)
        self.create_button.grid(row=3, column=0, sticky="w")
        self.unlock_button = ttk.Button(ident, text="Unlock",
                                        command=self._unlock)
        self.unlock_button.grid(row=3, column=1, padx=6)
        self.copy_button = ttk.Button(ident, text="Copy public key",
                                      command=self._copy_public)
        self.copy_button.grid(row=3, column=2, sticky="w")

        # --- contacts ---
        ttk.Label(outer, text="Contacts",
                  style="Heading.TLabel").grid(row=2, column=0, sticky="w")

        contacts = ttk.Frame(outer, padding=(0, 6, 0, 0))
        contacts.grid(row=3, column=0, sticky="nsew")
        contacts.columnconfigure(0, weight=1)
        contacts.rowconfigure(0, weight=1)

        self.contact_list = ttk.Treeview(contacts, columns=("name", "key"),
                                         show="headings", selectmode="browse")
        self.contact_list.heading("name", text="Name", anchor="w")
        self.contact_list.heading("key", text="Public key", anchor="w")
        self.contact_list.column("name", width=140, stretch=False)
        self.contact_list.column("key", anchor="w")
        self.contact_list.grid(row=0, column=0, columnspan=3, sticky="nsew")
        scroll = ttk.Scrollbar(contacts, orient="vertical",
                               command=self.contact_list.yview)
        self.contact_list.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=3, sticky="ns")

        form = ttk.Frame(contacts, padding=(0, 10, 0, 0))
        form.grid(row=1, column=0, columnspan=4, sticky="ew")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Name").grid(row=0, column=0, sticky="w",
                                          padx=(0, 8), pady=3)
        self.contact_name = ttk.Entry(form)
        self.contact_name.grid(row=0, column=1, sticky="ew", pady=3)

        ttk.Label(form, text="Their public key").grid(row=1, column=0,
                                                      sticky="w", padx=(0, 8),
                                                      pady=3)
        self.contact_key = ttk.Entry(form, font=theme.mono(10))
        self.contact_key.grid(row=1, column=1, sticky="ew", pady=3)

        buttons = ttk.Frame(form)
        buttons.grid(row=2, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(buttons, text="Remove selected",
                   command=self._remove).pack(side="right", padx=(6, 0))
        ttk.Button(buttons, text="Add contact",
                   command=self._add).pack(side="right")

        ttk.Label(outer, textvariable=self.status, style="Blurb.TLabel",
                  wraplength=580).grid(row=4, column=0, sticky="w", pady=(10, 0))

        ttk.Button(outer, text="Close", command=self.destroy).grid(
            row=5, column=0, sticky="e", pady=(10, 0))
        self.bind("<Escape>", lambda e: self.destroy())

    # ---------- state ----------

    def _refresh(self):
        if not self.store.has_identity:
            self.identity_state.configure(
                text="No identity yet. Create one, then send your public key to "
                     "the person you want to exchange messages with.")
            self._set_public("")
            self.create_button.configure(text="Create identity", state="normal")
            self.unlock_button.configure(state="disabled")
            self.copy_button.configure(state="disabled")
        else:
            unlocked = self.store.is_unlocked
            self.identity_state.configure(
                text="Identity ready and unlocked for this session."
                     if unlocked else
                     "Identity found, but locked. Unlock it to read or write "
                     "messages.")
            try:
                self._set_public(self.store.public_key_b64)
            except KeyStoreError as exc:
                self._set_public("")
                self.status.set(str(exc))
            self.create_button.configure(text="Replace identity", state="normal")
            self.unlock_button.configure(
                state="disabled" if unlocked else "normal")
            self.copy_button.configure(state="normal")

        self.contact_list.delete(*self.contact_list.get_children())
        for name, key in sorted(self.store.contacts().items()):
            self.contact_list.insert("", "end", values=(name, key))

        if self.on_change:
            self.on_change()

    def _set_public(self, value):
        self.public_key.configure(state="normal")
        self.public_key.delete("1.0", "end")
        self.public_key.insert("1.0", value)
        self.public_key.configure(state="disabled")

    # ---------- actions ----------

    def _create(self):
        replacing = self.store.has_identity
        note = ("This replaces your current identity. Every message already "
                "sent to your old public key becomes unreadable, and your "
                "contacts will need your new key."
                if replacing else
                "This passphrase encrypts your private key on disk. There is "
                "no way to recover it if you forget it.")
        prompt = PassphrasePrompt(self, "New identity", note, confirm=True)
        if prompt.result is None:
            return
        try:
            self.store.create_identity(prompt.result, overwrite=replacing)
        except KeyStoreError as exc:
            self.status.set(str(exc))
        else:
            self.status.set("Identity created. Send your public key to your "
                            "correspondent, over a channel you trust.")
        self._refresh()

    def _unlock(self):
        prompt = PassphrasePrompt(
            self, "Unlock", "Enter the passphrase for your identity.")
        if prompt.result is None:
            return
        try:
            self.store.unlock(prompt.result)
        except KeyStoreError as exc:
            self.status.set(str(exc))
        else:
            self.status.set("Unlocked for this session.")
        self._refresh()

    def _copy_public(self):
        value = self.public_key.get("1.0", "end-1c")
        if value:
            self.clipboard_clear()
            self.clipboard_append(value)
            self.status.set("Public key copied. It is safe to share.")

    def _add(self):
        try:
            self.store.add_contact(self.contact_name.get(),
                                   self.contact_key.get())
        except KeyStoreError as exc:
            self.status.set(str(exc))
        else:
            self.status.set("Added %s." % self.contact_name.get().strip())
            self.contact_name.delete(0, "end")
            self.contact_key.delete(0, "end")
        self._refresh()

    def _remove(self):
        selected = self.contact_list.selection()
        if not selected:
            self.status.set("Select a contact to remove")
            return
        name = self.contact_list.item(selected[0], "values")[0]
        try:
            self.store.remove_contact(name)
        except KeyStoreError as exc:
            self.status.set(str(exc))
        else:
            self.status.set("Removed %s." % name)
        self._refresh()
