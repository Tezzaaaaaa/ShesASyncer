import { anchorLines } from '../alignment/anchor.js';
import { monotonicMatch } from '../alignment/sequence.js';
import { confidence, conflicts } from '../consensus/confidence.js';
import { AlignmentEvidence, AlignmentResult, LyricLine, Timing } from './models.js';

export class AlignmentPipeline {
  constructor(engines = []) { this.engines = [...engines]; }

  run(lyrics, timedSegments) {
    const lines = lyrics.map((x, i) => x instanceof LyricLine ? x : new LyricLine(i, x));
    const evidence = anchorLines(lines, timedSegments, 0.45);
    const matched = new Set(evidence.map(e => e.lineIndex));
    if (matched.size < lines.length && timedSegments.length) {
      const pairs = monotonicMatch(lines.map(x => x.text), timedSegments);
      const existing = new Set(evidence.map(e => e.lineIndex));
      for (const [li, si, score] of pairs) {
        if (existing.has(li) || score < 0.35) continue;
        const seg = timedSegments[si];
        evidence.push(new AlignmentEvidence(li, new Timing(seg.start, seg.end, score, 'asr'), { matchedText: String(seg.text ?? ''), score, source: 'asr', metadata: { matcher: 'monotonic_sequence' } }));
      }
    }
    evidence.sort((a, b) => a.lineIndex - b.lineIndex);
    const conflictLines = conflicts(evidence), byIndex = new Map(evidence.map(e => [e.lineIndex, e]));
    const output = [], warnings = [];
    for (const line of lines) {
      const item = byIndex.get(line.index);
      if (item) output.push({ index: line.index, text: line.text, start: item.timing.start, end: item.timing.end, confidence: item.timing.confidence, source: item.source });
      else { output.push({ index: line.index, text: line.text, start: null, end: null, confidence: 0, source: null }); warnings.push(`No reliable timing evidence for lyric line ${line.index}`); }
    }
    if (conflictLines.length) warnings.push(`Conflicting alignment evidence requires targeted refinement: ${conflictLines.join(', ')}`);
    return new AlignmentResult(output, confidence(evidence), warnings, evidence);
  }
}
