import { ctcViterbiAlignment } from '../evidence/ctc.js';
import { G2PEngine } from '../lyrics/g2p.js';
import { TimedSegment } from './adapters.js';

export class CtcSingingEngine {
  name = 'shesasyncer-ctc';
  constructor(g2p, acousticRunner = null, { blankToken = null } = {}) { this.g2p = g2p; this.acousticRunner = acousticRunner; this.blankToken = blankToken || acousticRunner?.blankToken || '<blank>'; }
  available() { return this.g2p?.available?.() && typeof this.acousticRunner === 'function'; }
  async align(audioPath, lyrics = [], language = null) {
    if (!this.available()) return [];
    const lines = [...lyrics], linePhonemes = lines.map(line => this.g2p.convert(line, language)), flat = linePhonemes.flat(); if (!flat.length) return [];
    const frames = [...await this.acousticRunner(audioPath, flat, language)], spans = ctcViterbiAlignment(flat, frames, this.blankToken); if (!spans.length) return [];
    const byIndex = new Map(spans.map(x => [x.tokenIndex, x])), result = []; let offset = 0;
    for (let i = 0; i < lines.length; i++) { const phonemes = linePhonemes[i], lineSpans = Array.from({ length: phonemes.length }, (_, j) => byIndex.get(offset + j)).filter(Boolean); offset += phonemes.length; if (!lineSpans.length) continue; result.push(new TimedSegment(lineSpans[0].start, lineSpans.at(-1).end, lines[i], lineSpans.reduce((s, x) => s + x.confidence, 0) / lineSpans.length, [], lineSpans.map(({ tokenIndex, ...x }) => x))); }
    if (result.length) result[0].start = Math.min(result[0].start, frames[0].time);
    for (let i = 1; i < result.length; i++) if (result[i - 1].end < result[i].start) result[i - 1].end = result[i].start;
    return result;
  }
}
