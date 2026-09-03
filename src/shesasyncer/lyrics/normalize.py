import re
import unicodedata


def normalize_lyric(text: str) -> str:
    """Normalize text for matching without changing the trusted lyric itself."""
    text = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"[^\w\u00C0-\uFFFF]+", "", text, flags=re.UNICODE)


def lyric_tokens(text: str) -> list[str]:
    return re.findall(r"\w+", unicodedata.normalize("NFKC", text).casefold(), flags=re.UNICODE)
