from collections.abc import Callable
from typing import Sequence


class G2PEngine:
    """Small dependency-free boundary for lyric-to-phoneme conversion."""

    def __init__(self, converter: Callable[[str, str | None], Sequence[str]] | None = None):
        self.converter = converter

    def available(self) -> bool:
        return callable(self.converter)

    def convert(self, text: str, language: str | None = None) -> tuple[str, ...]:
        if not self.available():
            return ()
        return tuple(str(x).strip() for x in self.converter(text, language) if str(x).strip())
