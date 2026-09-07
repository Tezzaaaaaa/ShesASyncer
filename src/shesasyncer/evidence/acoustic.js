export class AcousticFrame {
  constructor(time, scores = {}) { this.time = Number(time); this.scores = scores; }
}

export function viterbiPhonemeAlignment(phonemes, frames, { stayBonus = 0.15, skipPenalty = 2 } = {}) {
  const tokens = phonemes.map(String).map(x => x.trim()).filter(Boolean);
  if (!tokens.length || !frames.length) return [];
  const n = tokens.length, m = frames.length, negInf = -Infinity;
  const dp = Array.from({ length: m }, () => Array(n).fill(negInf));
  const back = Array.from({ length: m }, () => Array(n).fill(-1));
  for (let j = 0; j < Math.min(n, m); j++) dp[0][j] = frames[0].scores[tokens[j]] ?? -skipPenalty * j;
  for (let i = 1; i < m; i++) for (let j = 0; j < n; j++) {
    const emit = frames[i].scores[tokens[j]] ?? -skipPenalty;
    let best = dp[i - 1][j] + stayBonus, prev = j;
    if (j > 0 && dp[i - 1][j - 1] > best) { best = dp[i - 1][j - 1]; prev = j - 1; }
    dp[i][j] = best + emit; back[i][j] = prev;
  }
  if (dp[m - 1][n - 1] === negInf) return [];
  const states = [n - 1];
  for (let i = m - 1; i > 0; i--) states.push(back[i][states.at(-1)]);
  states.reverse();
  const deltas = frames.slice(1).map((f, i) => Math.max(0, f.time - frames[i].time)).sort((a, b) => a - b);
  const hop = deltas.length ? deltas[Math.floor(deltas.length / 2)] || 0.01 : 0.01;
  const spans = []; let start = 0, current = states[0];
  for (let i = 1; i <= m; i++) if (i === m || states[i] !== current) {
    const scores = frames.slice(start, i).map(f => f.scores[tokens[current]] ?? -skipPenalty);
    const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
    const conf = 1 / (1 + Math.exp(-mean));
    spans.push({ tokenIndex: current, phoneme: tokens[current], start: frames[start].time, end: frames[i - 1].time + hop, confidence: Math.max(0, Math.min(1, conf)) });
    if (i < m) { start = i; current = states[i]; }
  }
  return spans;
}
