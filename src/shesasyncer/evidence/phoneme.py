from dataclasses import dataclass


@dataclass(frozen=True)
class PhonemeBoundary:
    """A single phoneme boundary produced by a singing aligner."""

    symbol: str
    start: float
    end: float
    confidence: float = 0.0

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


def normalize_phonemes(items: object) -> tuple[PhonemeBoundary, ...]:
    """Normalize engine-specific phoneme dictionaries into a stable schema."""
    if not isinstance(items, (list, tuple)):
        return ()

    result: list[PhonemeBoundary] = []
    for item in items:
        if isinstance(item, PhonemeBoundary):
            boundary = item
        elif isinstance(item, dict):
            try:
                boundary = PhonemeBoundary(
                    symbol=str(item.get("phoneme", item.get("symbol", ""))).strip(),
                    start=float(item["start"]),
                    end=float(item["end"]),
                    confidence=float(item.get("confidence", 0.0) or 0.0),
                )
            except (KeyError, TypeError, ValueError):
                continue
        else:
            continue

        if boundary.symbol and boundary.start >= 0 and boundary.end > boundary.start:
            result.append(boundary)

    return tuple(sorted(result, key=lambda item: (item.start, item.end)))
