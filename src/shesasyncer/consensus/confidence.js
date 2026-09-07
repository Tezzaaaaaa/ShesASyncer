export function confidence(evidence) {
  if (!evidence.length) return 0;
  return Number((evidence.reduce((s, e) => s + Math.max(0, Math.min(1, e.timing.confidence)), 0) / evidence.length).toFixed(4));
}

export function conflicts(evidence, tolerance = 0.75) {
  const byLine = new Map();
  for (const item of evidence) { if (!byLine.has(item.lineIndex)) byLine.set(item.lineIndex, []); byLine.get(item.lineIndex).push(item); }
  const result = [];
  for (const [index, items] of byLine) {
    const starts = items.map(x => x.timing.start), ends = items.map(x => x.timing.end);
    if (items.length > 1 && (Math.max(...starts) - Math.min(...starts) > tolerance || Math.max(...ends) - Math.min(...ends) > tolerance)) result.push(index);
  }
  return result;
}
