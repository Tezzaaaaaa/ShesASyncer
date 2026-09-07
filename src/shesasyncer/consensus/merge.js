export class Candidate {
  constructor(start, end, confidence, source) { this.start = start; this.end = end; this.confidence = confidence; this.source = source; }
}

export function mergeCandidates(candidates, tolerance = 0.45) {
  if (!candidates.length) return null;
  const ranked = [...candidates].sort((a, b) => b.confidence - a.confidence);
  const best = ranked[0];
  const agreeing = ranked.filter(c => Math.abs(c.start - best.start) <= tolerance && Math.abs(c.end - best.end) <= tolerance);
  if (agreeing.length === 1 && ranked.length > 1) return null;
  const weight = agreeing.reduce((s, c) => s + Math.max(c.confidence, 0.01), 0);
  const start = agreeing.reduce((s, c) => s + c.start * Math.max(c.confidence, 0.01), 0) / weight;
  const end = agreeing.reduce((s, c) => s + c.end * Math.max(c.confidence, 0.01), 0) / weight;
  const confidence = Math.min(1, agreeing.reduce((s, c) => s + c.confidence, 0) / agreeing.length + 0.05 * (agreeing.length - 1));
  return new Candidate(start, end, confidence, agreeing.length > 1 ? 'consensus' : best.source);
}
