"""Core cipher interface.

Every cipher declares its parameters; the UI builds its controls from that
declaration, so adding a cipher never means touching the interface code.
"""

from dataclasses import dataclass


class CipherError(ValueError):
    """A key the user can fix -- shown plainly, without a traceback label."""


@dataclass
class IntParam:
    """An integer knob, rendered as a slider + spinbox + nudge buttons."""

    key: str
    label: str
    minimum: int
    maximum: int
    default: int = 0
    wrap: bool = True


@dataclass
class ChoiceParam:
    """A fixed set of options, rendered as a dropdown."""

    key: str
    label: str
    choices: tuple
    default: str = ""


@dataclass
class TextParam:
    """A free-text knob (keywords, alphabets), rendered as an entry box."""

    key: str
    label: str
    default: str = ""


class Cipher:
    """Base class. Subclasses set `name`, `params`, and implement encode/decode."""

    name = "Unnamed"
    blurb = ""
    params: list = []
    key_noun = "key"  # labels the brute-force column, toggle and hint
    one_way = False  # set True for digests: encode only, no way back

    uses_keystore = False  # True adds a Keys button beside the controls

    def refresh_params(self):
        """Hook for params whose choices change while the app is running."""

    def defaults(self) -> dict:
        return {p.key: p.default for p in self.params}

    def encode(self, text: str, **params) -> str:
        raise NotImplementedError

    def decode(self, text: str, **params) -> str:
        raise NotImplementedError

    def candidates(self, text: str, **params):
        """Every plausible decoding, as (label, text) pairs.

        Returning None means the key space is too large to enumerate and the
        brute-force panel stays hidden.
        """
        return None
