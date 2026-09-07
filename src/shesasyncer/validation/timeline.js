export function validateTimeline(evidence, { duration = null, minDuration = 0.03, maxDuration = 20, maxGap = 30 } = {}) {
  const issues = [], ordered = [...evidence].sort((a, b) => a.timing.start - b.timing.start || a.lineIndex - b.lineIndex);
  let previousEnd = null, previousIndex = null;
  for (const item of ordered) {
    const { start, end } = item.timing, index = item.lineIndex, span = end - start;
    const issue = (code, severity, message) => issues.push({ lineIndex: index, code, severity, message });
    if (start < 0 || end < 0) issue('negative-time', 'error', 'Timing contains a negative timestamp.');
    if (end <= start) issue('non-positive-duration', 'error', 'End time must be after start time.');
    else if (span < minDuration) issue('too-short', 'warning', `Line duration is only ${span.toFixed(3)}s.`);
    else if (span > maxDuration) issue('too-long', 'warning', `Line duration is ${span.toFixed(3)}s.`);
    if (previousEnd !== null) {
      if (start < previousEnd - 0.02) issue('overlap', 'error', `Line overlaps previous line ${previousIndex}.`);
      else if (start - previousEnd > maxGap) issue('large-gap', 'warning', `Gap before line is ${(start - previousEnd).toFixed(3)}s.`);
    }
    if (duration !== null && end > duration + 0.05) issue('past-duration', 'error', 'Timing extends beyond the audio duration.');
    previousEnd = previousEnd === null ? end : Math.max(previousEnd, end); previousIndex = index;
  }
  return { issues, valid: !issues.some(x => x.severity === 'error'), errors: issues.filter(x => x.severity === 'error'), warnings: issues.filter(x => x.severity === 'warning') };
}
