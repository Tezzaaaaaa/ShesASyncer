import { similarity } from './sequence.js';
import { AlignmentEvidence, Timing, LyricLine } from '../core/models.js';

export function anchorLines(lyrics, segments, minScore = 0.45) {
  const lines = lyrics.map((x, i) => x instanceof LyricLine ? x : new LyricLine(i, x));
  const evidence = []; let cursor = 0;
  for (const line of lines) {
    let best = null, bestScore = 0;
    for (let i = cursor; i < segments.length; i++) {
      const score = similarity(line.text, String(segments[i]?.text ?? ''));
      if (score > bestScore) { bestScore = score; best = [i, segments[i]]; }
      if (score >= 0.9) break;
    }
    if (best && bestScore >= minScore) {
      const [i, seg] = best;
      evidence.push(new AlignmentEvidence(line.index, new Timing(Number(seg.start), Number(seg.end), Math.min(1, bestScore), 'asr'), { matchedText: String(seg.text ?? ''), score: bestScore, source: 'asr' }));
      cursor = i + 1;
    }
  }
  return evidence;
}
