"""Optional SOFA singing-oriented forced-alignment adapter boundary.

SOFA is deliberately isolated because its model/runtime requirements differ
from the lightweight core. The core owns routing and consensus.
"""


class SofaEngine:
    name = "sofa"

    def available(self) -> bool:
        return False

    def align(self, audio_path: str, lyrics: list[str], language: str | None = None):
        if not self.available():
            return ()
        raise NotImplementedError
