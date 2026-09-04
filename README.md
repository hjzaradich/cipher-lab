# Cipher Lab

A small desktop app for encoding and decoding messages. Ships with Caesar,
ROT13, Atbash, Vigenère, Morse, Base64, hashing and public-key messaging; the structure is built so more ciphers slot
in without touching the interface.

## Running it

Runs on Windows, macOS and Linux.

**Requirements: Python 3.9 or newer, with Tk 8.6.** The Tk version is the part
that catches people out. Check both in one line:

```
python3 -c "import sys, tkinter; print(sys.version); print('Tk', tkinter.TkVersion)"
```

You need `Tk 8.6`. If it prints `Tk 8.5` the app will fail when you select
Caesar, because its shift control is a `ttk.Spinbox` and that widget does not
exist before Tk 8.6.

- **macOS** — the python3 that comes with the Xcode command line tools is
  usually Tk 8.5, so install Python from [python.org](https://www.python.org/downloads/)
  (its installer bundles Tk 8.6). With Homebrew instead: `brew install python
  python-tk`.
- **Windows** — the python.org installer includes Tk 8.6 already.
- **Linux** — `sudo apt install python3-tk` on Debian or Ubuntu.

Then, for public-key messaging only:

```
pip install -r requirements.txt
```

Everything else runs on the standard library. Without PyNaCl the app still
starts and every other cipher works — the **Public key** entry simply does not
appear.

Launching:

- **Windows** — double-click **Cipher Lab.bat**, or run `python main.py`.
- **macOS** — double-click **Cipher Lab.command**. It is stored executable in
  git, so no `chmod` is needed after cloning. Or run `python3 main.py`.
- **Linux** — `python3 main.py`.

## The ciphers

| Cipher | Key | Notes |
| --- | --- | --- |
| **Caesar** | Shift, 0–25 | Every letter moves the same number of places. |
| **ROT13** | none | Caesar fixed at 13. Half the alphabet, so it is its own inverse. |
| **Atbash** | none | Mirrors the alphabet (A↔Z, B↔Y). Also its own inverse. |
| **Vigenère** | Keyword | A Caesar shift per letter, cycling through the keyword. The keyword advances only on letters, so spaces and punctuation never consume it. |
| **Morse** | none | Dots and dashes. Not a substitution cipher, so the two directions really do differ. |
| **Base64** | none | Bytes as printable ASCII. Encoding, not encryption — anyone can undo it. |
| **Hash** | Algorithm | A one-way digest: SHA-256, SHA-512, SHA3-256, BLAKE2b, SHA-1 or MD5. Encode only — see below. |
| **Public key** | Correspondent | Real encryption between you and one named person. Curve25519 + XSalsa20-Poly1305, via PyNaCl. |

The four substitution ciphers keep letter case and pass digits, spaces and
punctuation through untouched.

Morse and Base64 are the exceptions — both are transcodings rather than
substitutions, so their two directions are genuinely different operations.

Morse:

- It has no notion of case, so decoding always comes back uppercase.
- Letters are separated by a space and words by ` / `. Decoding is more
  forgiving than encoding: it also accepts `|` or any run of two or more spaces
  as a word break, and takes `·` `•` for dots and `–` `—` `−` for dashes, so pasted
  Morse usually just works.
- It covers A–Z, 0–9 and common punctuation. Anything with no Morse equivalent
  is dropped when encoding, and a sequence that decodes to nothing shows as `?`
  rather than failing the whole message.

Base64:

- Text is treated as UTF-8, so accents, CJK and emoji round-trip intact.
- Encoding emits the standard alphabet. Decoding also accepts the URL-safe
  alphabet (`-` and `_`), input wrapped across lines, and missing or excess `=`
  padding, which it recomputes — so Base64 copied out of an email or a log
  usually just works.
- Input that cannot be decoded says why in the status bar: unexpected
  characters, a length no amount of padding can fix, or bytes that turn out to
  be binary rather than text.

Base64 is not a cipher and offers no secrecy. It is here because it turns up
constantly alongside them — in tokens, config files and email headers.

### Hashing is one-way

**Hash** is the one entry with no way back. A digest is not an encoding of your
message and does not contain it; nothing can turn `c3abf7a7…` back into
`Attack at dawn!`. The app says so rather than pretending otherwise: selecting
**Hash** disables the Decode direction, labels the output **Digest**, and the
all-keys panel explains there is nothing to reverse.

- The digest covers the text's UTF-8 bytes, and is shown as lowercase hex.
- An empty message gives an empty result, to match the rest of the app. The
  digest of the empty string is a real value, but showing it for an empty box
  would read as though something had been hashed.
- **SHA-1 and MD5 are included for reading old checksums only.** Both are
  broken for security purposes — do not use them to protect anything. SHA-256
  is the default for a reason.
- Hashing is not a way to store passwords. That needs a slow, salted algorithm
  such as bcrypt, scrypt or Argon2; a bare SHA-256 of a password is trivially
  attacked with a wordlist.

## Public-key messaging

This is the one entry that offers actual secrecy, and the only one that keeps
state. It uses PyNaCl's `Box`: Curve25519 key exchange with XSalsa20-Poly1305,
the same construction libsodium gives everyone else.

### Setting it up with someone

1. Select **Public key**, press **Keys…**, and **Create identity**. You choose a
   passphrase; it encrypts your private key on disk.
2. **Copy public key** and send it to the other person. A public key is safe to
   post anywhere — that is the point of it.
3. They do the same, and send you theirs.
4. Each of you adds the other under **Contacts**, with any name you like.
5. Pick them as **Correspondent**. Encode writes a message only they can read;
   decode reads what they send back.

The same correspondent setting covers both directions, because the shared key
is derived from your private key and their public key either way round.

### What it does and does not protect

- Messages are **authenticated** as well as secret. A message that decrypts
  really came from that correspondent and was not altered; a single flipped bit
  makes it fail rather than decrypt to something subtly different.
- Every message gets a **fresh random nonce**, so sending the same text twice
  produces different ciphertext.
- Your private key is stored **encrypted with Argon2id** (moderate parameters)
  under `~/.cipher_lab`, deliberately not beside the app — the program folder
  may sit inside OneDrive or similar, and a private key should not be uploaded
  to a cloud service as a side effect of where you unzipped it.
- **The passphrase cannot be recovered.** Forget it and the identity is gone,
  along with the ability to read anything sent to it.
- **Exchange public keys over a channel you trust.** Nothing here proves a
  public key belongs to who you think. If someone can substitute their own key
  while you are swapping them, they can read everything. Confirm the key with
  the person by some other route — in person, or over a call.
- It protects messages in transit, not your computer. Anyone who can use your
  unlocked session can read your messages.

## Using it

Pick a cipher from the toolbar; its controls appear beside it. Everything
updates as you type — there is no convert button.

| Control | What it does |
| --- | --- |
| **Encode / Decode** | Which direction to run. |
| **Shift** spinbox *(Caesar)* | Type an offset directly, 0–25. |
| ◀ ▶ buttons, `Ctrl`+`←` / `→` | Step the offset one at a time; wraps at both ends. `Cmd` instead of `Ctrl` on macOS, where `Ctrl`+arrow belongs to Mission Control. |
| Slider | Sweep offsets quickly and watch the result change live. |
| **Keyword** *(Vigenère)* | The repeating key. A keyword with no letters in it says so in the status bar rather than failing silently. |
| **All shifts** | A live table of all 26 Caesar decodings. The row matching the current offset is highlighted; double-click any row to adopt that offset. |
| **Send up** | Pushes the result back into the message box, for running a second pass — handy for stacking ciphers. |
| **Copy** / **Paste** | Clipboard, for the result and the message respectively. |
| **Keys…** *(Public key)* | Create or unlock your identity, copy your public key, and manage contacts. |

The all-keys table only makes sense for a cipher with a small, enumerable key
space — in practice, Caesar. ROT13, Atbash, Morse, Base64 and Hash have no key
and
Vigenère has far too many, so for those the panel steps aside and the toggle
explains why. Your preference is remembered, so it returns when you switch back
to Caesar.

## Adding another cipher

1. Write `ciphers/yourcipher.py` with a `Cipher` subclass. Declare its knobs as
   `IntParam` / `TextParam` / `ChoiceParam` in `params`, and implement `encode`
   and `decode`.
2. Add an instance to `REGISTRY` in `ciphers/__init__.py`.
3. Add a suite to `tests/`, copying the shape of `tests/test_base64.py`.

The controls for those params are generated automatically, and the cipher picker
grows a new entry. Two optional touches:

- Set `key_noun` (Caesar uses `"shift"`) and the table column, toggle and hint
  reword themselves.
- If the key space is small enough to enumerate, implement `candidates()` to get
  the same all-keys table Caesar has. Leave it returning `None` and the panel
  hides itself.

Raise `CipherError` for a key the user can fix — it shows as a plain message in
the status bar instead of an exception label.

Set `one_way = True` for anything that cannot be reversed, such as a digest. The
Decode direction is then disabled and the output is labelled **Digest**.

## Platform notes

The app picks its fonts at startup from the first family actually installed —
Consolas, then Menlo, then DejaVu Sans Mono, and so on — falling back to Tk's own
`TkFixedFont`. Tk substitutes silently for a font family it cannot find, which
would otherwise cost the message panes their monospacing on a machine without
Consolas.

Two things are Windows-only and simply do not happen elsewhere: the tinted title
bar, and `Cipher Lab.bat`. The purple theme itself works everywhere, because the
app forces ttk's `clam` theme — the native Windows (`vista`) and macOS (`aqua`)
themes both ignore colour options.

## Theming

The purple look lives entirely in `theme.py`. The palette is a dozen named
constants at the top of that file — change `ACCENT` and the buttons, slider,
selections and highlights all follow. It tints the Windows title bar to match, where
that is available.

## Files

- `main.py` — entry point
- `Cipher Lab.bat` / `Cipher Lab.command` — double-click launchers for Windows
  and macOS
- `app.py` — the Tkinter window
- `keys_dialog.py` — the Keys window: identity and contacts
- `theme.py` — the purple palette and all ttk styling
- `smiley.py` — the face in the corner. Click it.
- `requirements.txt` — the one optional dependency

The engine is `ciphers/`, and nothing in it imports Tkinter — every cipher can
be used from a plain script or a REPL:

- `ciphers/base.py` — `Cipher`, `CipherError`, `IntParam`, `ChoiceParam`,
  `TextParam`
- `ciphers/caesar.py`, `ciphers/rot13.py`, `ciphers/atbash.py`,
  `ciphers/vigenere.py`, `ciphers/morse.py`, `ciphers/b64.py`,
  `ciphers/digest.py`, `ciphers/publickey.py`
- `ciphers/keystore.py` — identities and contacts on disk
- `ciphers/__init__.py` — the registry

## Tests

```
python tests/run_tests.py
```

Nine suites, no test framework required — they drive a real (hidden) window and
assert on what it actually shows. Pass a fragment of a name to run just some of
them, e.g. `python tests/run_tests.py caesar smiley`. They are also plain pytest
tests if you prefer: `python -m pytest tests`.

Each suite runs in its own process, because several build a Tk root and one
rewrites `sys.platform`, neither of which repeats cleanly in one interpreter.
The public-key suites use a throwaway key directory, so they never touch a real
`~/.cipher_lab`; the two that need PyNaCl skip themselves if it is missing.

If you change anything, run these first — they caught a real bug during
development, where the panel toggle was a child of the panel it hides and so
could never be switched back on.
