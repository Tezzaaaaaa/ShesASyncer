from dataclasses import dataclass

from ..core.models import AlignmentEvidence


@dataclass(frozen=True)
class TimelineIssue:
    line_index: int
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class TimelineValidation:
    issues: tuple[TimelineIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.errors

    @property
    def errors(self) -> tuple[TimelineIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "error")

    @property
    def warnings(self) -> tuple[TimelineIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "warning")

    @property
    def affected_lines(self) -> tuple[int, ...]:
        return tuple(sorted({issue.line_index for issue in self.issues}))


def validate_timeline(
    evidence: list[AlignmentEvidence],
    *,
    duration: float | None = None,
    min_duration: float = 0.03,
    max_duration: float = 20.0,
    max_gap: float = 30.0,
) -> TimelineValidation:
    """Reject impossible timings without silently repairing them."""
    issues: list[TimelineIssue] = []
    ordered = sorted(evidence, key=lambda item: (item.timing.start, item.line_index))

    previous_end: float | None = None
    previous_index: int | None = None
    for item in ordered:
        start = item.timing.start
        end = item.timing.end
        index = item.line_index
        span = end - start

        if start < 0 or end < 0:
            issues.append(TimelineIssue(index, "negative-time", "error", "Timing contains a negative timestamp."))
        if end <= start:
            issues.append(TimelineIssue(index, "non-positive-duration", "error", "End time must be after start time."))
        elif span < min_duration:
            issues.append(TimelineIssue(index, "too-short", "warning", f"Line duration is only {span:.3f}s."))
        elif span > max_duration:
            issues.append(TimelineIssue(index, "too-long", "warning", f"Line duration is {span:.3f}s."))

        if previous_end is not None:
            if start < previous_end - 0.02:
                issues.append(TimelineIssue(index, "overlap", "error", f"Line overlaps previous line {previous_index}."))
            elif start - previous_end > max_gap:
                issues.append(TimelineIssue(index, "large-gap", "warning", f"Gap before line is {start - previous_end:.3f}s."))

        if duration is not None and end > duration + 0.05:
            issues.append(TimelineIssue(index, "past-duration", "error", "Timing extends beyond the audio duration."))

        previous_end = max(previous_end, end) if previous_end is not None else end
        previous_index = index

    return TimelineValidation(tuple(issues))
