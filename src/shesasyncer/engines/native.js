import { viterbiPhonemeAlignment } from '../evidence/acoustic.js';
import { G2PEngine } from '../lyrics/g2p.js';
import { TimedSegment } from './adapters.js';

export class NativeSingingEngine {
  name = 'shesasyncer-native';
  constructor(g2p, acousticRunner = null) { this.g2p = g2p; this.acousticRunner = acousticRunner; }
  available() { return this.g2p instanceof G2PEngine ? this.g2p.available() && typeof this.acousticRunner === 'function' : typeof this.acousticRunner === 'function' && this.g2p?.available?.(); }
  async align(audioPath, lyrics = [], language = null) {
    if (!this.available()) return [];
    const lines = [...lyrics], linePhonemes = lines.map(line => this.g2p.convert(line, language));
    const flat = linePhonemes.flat(); if (!flat.length) return [];
    const frames = await this.acousticRunner(audioPath, flat, language);
    const spans = viterbiPhonemeAlignment(flat, frames); if (!spans.length) return [];
    const result = []; let offset = 0;
    for (let i = 0; i < lines.length; i++) {
      const phonemes = linePhonemes[i], indices = new Set(Array.from({ length: phonemes.length }, (_, j) => offset + j));
      const lineSpans = spans.filter(span => indices.has(span.tokenIndex)); offset += phonemes.length;
      if (!lineSpans.length) continue;
      result.push(new TimedSegment(lineSpans[0].start, lineSpans.at(-1).end, lines[i], lineSpans.reduce((s, x) => s + x.confidence, 0) / lineSpans.length, [], lineSpans.map(({ tokenIndex, ...x }) => x)));
    }
    return result;
  }
}
