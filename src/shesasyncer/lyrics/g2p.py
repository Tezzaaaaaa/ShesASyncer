from collections.abc import Callable
from typing import Sequence
import os
import re
import shutil
import subprocess


class G2PEngine:
    """Small boundary for lyric-to-phoneme conversion."""

    def __init__(self, converter: Callable[[str, str | None], Sequence[str]] | None = None):
        self.converter = converter

    def available(self) -> bool:
        return callable(self.converter)

    def convert(self, text: str, language: str | None = None) -> tuple[str, ...]:
        if not self.available():
            return ()
        return tuple(str(x).strip() for x in self.converter(text, language) if str(x).strip())


class EspeakG2P(G2PEngine):
    """eSpeak NG backed IPA G2P adapter.

    eSpeak NG is used only to produce the trusted lyric phoneme sequence;
    acoustic timing remains entirely in ShesASyncer. The executable is
    discovered at runtime so the core package stays dependency-light.
    """

    def __init__(self, executable: str | None = None, *, strip_stress: bool = True):
        self.executable = executable or shutil.which("espeak-ng") or shutil.which("espeak")
        self.strip_stress = strip_stress
        super().__init__(self._convert)

    def available(self) -> bool:
        if not self.executable:
            return False
        if os.path.isabs(self.executable) or os.path.sep in self.executable:
            return os.path.isfile(self.executable) and os.access(self.executable, os.X_OK)
        return shutil.which(self.executable) is not None

    def _convert(self, text: str, language: str | None = None) -> tuple[str, ...]:
        if not self.executable or not text.strip():
            return ()
        voice = language or "en"
        process = subprocess.run(
            [self.executable, "-q", "--ipa", "--sep", " ", "-v", voice],
            input=text,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
        if process.returncode != 0:
            return ()
        return _tokenize_ipa(process.stdout, strip_stress=self.strip_stress)


def _tokenize_ipa(value: str, *, strip_stress: bool = True) -> tuple[str, ...]:
    """Convert eSpeak's separated IPA into model-friendly phoneme tokens."""
    tokens: list[str] = []
    for chunk in re.split(r"\s+", value.strip()):
        if not chunk:
            continue
        if strip_stress:
            chunk = chunk.replace("ˈ", "").replace("ˌ", "")
        chunk = chunk.replace("\u0361", "").replace("\u200d", "")
        if chunk:
            tokens.append(chunk)
    return tuple(tokens)
