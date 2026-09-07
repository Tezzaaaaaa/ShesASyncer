export function ctcViterbiAlignment(phonemes, frames, blankToken = '<blank>') {
  const tokens = phonemes.map(String).map(x => x.trim()).filter(Boolean); if (!tokens.length || !frames.length) return [];
  const labels = [blankToken]; for (const token of tokens) labels.push(token, blankToken);
  const states = labels.length, neg = -Infinity, dp = Array.from({ length: frames.length }, () => Array(states).fill(neg)), back = Array.from({ length: frames.length }, () => Array(states).fill(-1));
  dp[0][0] = Number(frames[0].scores[blankToken] ?? neg); if (states > 1) dp[0][1] = Number(frames[0].scores[tokens[0]] ?? neg);
  for (let t = 1; t < frames.length; t++) for (let s = 0; s < states; s++) {
    const emit = Number(frames[t].scores[labels[s]] ?? neg); if (emit === neg) continue;
    let best = dp[t - 1][s], prev = s;
    if (s > 0 && dp[t - 1][s - 1] > best) { best = dp[t - 1][s - 1]; prev = s - 1; }
    if (s > 1 && labels[s] !== blankToken && labels[s] !== labels[s - 2] && dp[t - 1][s - 2] > best) { best = dp[t - 1][s - 2]; prev = s - 2; }
    if (best !== neg) { dp[t][s] = best + emit; back[t][s] = prev; }
  }
  const finals = [states - 1, ...(states > 1 ? [states - 2] : [])], final = finals.reduce((a, b) => dp.at(-1)[b] > dp.at(-1)[a] ? b : a);
  if (dp.at(-1)[final] === neg) return [];
  const path = [final]; for (let t = frames.length - 1; t > 0; t--) { const p = back[t][path.at(-1)]; if (p < 0) return []; path.push(p); } path.reverse();
  const deltas = frames.slice(1).map((f, i) => Math.max(0, f.time - frames[i].time)).sort((a, b) => a - b), hop = deltas.length ? deltas[Math.floor(deltas.length / 2)] || 0.01 : 0.01;
  const spans = []; let start = null, current = null;
  for (let i = 0; i <= path.length; i++) { const state = i < path.length ? path[i] : -1, label = current == null ? null : labels[current];
    if (state !== current) {
      if (current != null && label !== blankToken && start != null) {
        const scores = frames.slice(start, i).map(f => Number(f.scores[label] ?? neg)).filter(Number.isFinite);
        if (scores.length) { const mean = scores.reduce((a, b) => a + b, 0) / scores.length; const conf = mean <= 0 ? Math.exp(mean) : 1 - Math.exp(-mean); spans.push({ tokenIndex: Math.floor(current / 2), phoneme: label, start: frames[start].time, end: i < frames.length ? frames[i].time : frames.at(-1).time + hop, confidence: Math.max(0, Math.min(1, conf)) }); }
      }
      start = state >= 0 ? i : null; current = state >= 0 ? state : null;
    }
  }
  return spans;
}
