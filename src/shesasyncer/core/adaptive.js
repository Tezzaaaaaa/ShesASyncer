import { monotonicMatch } from '../alignment/sequence.js';
import { refineEvidence } from '../alignment/refinement.js';
import { mergeCandidates, Candidate } from '../consensus/merge.js';
import { AlignmentEvidence, AlignmentResult, LyricLine, Timing } from './models.js';
import { validateTimeline } from '../validation/timeline.js';

export class AdaptiveAligner {
  constructor(engines = []) { this.engines = [...engines]; }
  async collect(audioPath, lyrics, language = null) {
    const lines = lyrics.map((x, i) => x instanceof LyricLine ? x : new LyricLine(i, x)), collected = [];
    for (const engine of this.engines) {
      if (!engine.available?.()) continue;
      try { const segments = await engine.align(audioPath, lines.map(x => x.text), language); if (segments?.length) collected.push({ engine: engine.name, segments: [...segments] }); } catch { /* optional engine failure is isolated */ }
    }
    return collected;
  }
  async run(audioPath, lyrics, { language = null, retry = null, duration = null } = {}) {
    const lines = lyrics.map((x, i) => x instanceof LyricLine ? x : new LyricLine(i, x));
    let runs = await this.collect(audioPath, lines, language), evidence = this.#match(lines, runs);
    let unresolved = this.#unresolved(lines, evidence);
    if (unresolved.length && retry) { runs = runs.concat(await this.#targetedRetry(audioPath, unresolved, retry)); evidence = this.#match(lines, runs); unresolved = this.#unresolved(lines, evidence); }
    let validation = validateTimeline(evidence, { duration });
    const invalid = new Set(validation.errors.map(x => x.lineIndex));
    evidence = refineEvidence(evidence.filter(x => !invalid.has(x.lineIndex)));
    unresolved = this.#unresolved(lines, evidence);
    const byLine = new Map(evidence.map(x => [x.lineIndex, x])), output = [], warnings = validation.issues.map(x => `Timeline ${x.severity}: line ${x.lineIndex}: ${x.message}`);
    for (const line of lines) {
      const item = byLine.get(line.index);
      if (!item) { output.push({ index: line.index, text: line.text, start: null, end: null, confidence: 0, source: null, words: [], characters: [], phonemes: [] }); if (!invalid.has(line.index)) warnings.push(`No reliable timing evidence for lyric line ${line.index}`); }
      else output.push({ index: line.index, text: line.text, start: item.timing.start, end: item.timing.end, confidence: item.timing.confidence, source: item.source, words: item.metadata?.words ?? [], characters: item.metadata?.characters ?? [], phonemes: item.metadata?.phonemes ?? [] });
    }
    if (unresolved.length) warnings.push(`Unresolved lines remain after validation: ${unresolved.join(', ')}`);
    return new AlignmentResult(output, this.#confidence(evidence), warnings, evidence);
  }
  #match(lines, runs) {
    const candidates = new Map(lines.map(x => [x.index, []])), metadata = new Map();
    for (const run of runs) {
      const segments = run.segments.map(s => ({ start: s.start, end: s.end, text: s.text, confidence: s.confidence }));
      for (const [lineIndex, segmentIndex, sim] of monotonicMatch(lines.map(x => x.text), segments)) {
        const segment = run.segments[segmentIndex], score = Math.max(0, Math.min(1, sim * Math.max(segment.confidence ?? 0, 0.01)));
        candidates.get(lineIndex).push(new Candidate(segment.start, segment.end, score, run.engine));
        metadata.set(`${lineIndex}:${run.engine}`, { words: segment.words ?? [], phonemes: segment.phonemes ?? [], similarity: sim, engineConfidence: segment.confidence ?? 0 });
      }
    }
    return lines.flatMap(line => { const list = candidates.get(line.index), merged = mergeCandidates(list); if (!merged) return []; const agreeing = list.filter(c => Math.abs(c.start - merged.start) <= 0.45 && Math.abs(c.end - merged.end) <= 0.45); const sources = agreeing.map(c => c.source); const meta = { sources, agreement: sources.length > 1 }; for (const source of sources) { const sm = metadata.get(`${line.index}:${source}`); if (sm?.words?.length) { meta.words = sm.words; } if (sm?.phonemes?.length) { meta.phonemes = sm.phonemes; } if (sm?.similarity != null) meta.similarity = sm.similarity; if (sm?.engineConfidence != null) meta.engineConfidence = sm.engineConfidence; } return [new AlignmentEvidence(line.index, new Timing(merged.start, merged.end, merged.confidence, sources.length > 1 ? 'consensus' : sources[0]), { matchedText: line.text, score: merged.confidence, source: sources.length > 1 ? 'consensus' : sources[0], metadata: meta })]; });
  }
  async #targetedRetry(audioPath, indices, retry) { const out = []; for (const index of indices) { try { const runs = await retry(audioPath, [index]); if (runs) out.push(...runs); } catch {} } return out; }
  #unresolved(lines, evidence) { const matched = new Set(evidence.map(x => x.lineIndex)); return lines.map(x => x.index).filter(i => !matched.has(i)); }
  #confidence(evidence) { return evidence.length ? evidence.reduce((s, e) => s + e.timing.confidence, 0) / evidence.length : 0; }
}
