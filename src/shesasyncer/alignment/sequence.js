import { normalizeLyric } from '../lyrics/normalize.js';

export function similarity(a, b) {
  const x = normalizeLyric(a), y = normalizeLyric(b);
  if (x === y) return x ? 1 : 0;
  if (!x || !y) return 0;
  const prev = Array(y.length + 1).fill(0).map((_, i) => i);
  for (let i = 1; i <= x.length; i++) {
    let left = i;
    for (let j = 1; j <= y.length; j++) {
      const old = prev[j];
      const cost = x[i - 1] === y[j - 1] ? 0 : 1;
      prev[j] = Math.min(prev[j] + 1, left + 1, prev[j - 1] + cost);
      left = prev[j];
    }
  }
  const distance = prev[y.length];
  return 1 - distance / Math.max(x.length, y.length);
}

export function monotonicMatch(lyrics, segments, { skipPenalty = 0.18 } = {}) {
  const n = lyrics.length, m = segments.length;
  if (!n || !m) return [];
  const dp = Array.from({ length: n + 1 }, () => Array(m + 1).fill(0));
  const move = Array.from({ length: n + 1 }, () => Array(m + 1).fill(null));
  for (let i = 1; i <= n; i++) for (let j = 1; j <= m; j++) {
    const s = similarity(lyrics[i - 1], segments[j - 1]?.text ?? '');
    const choices = [[dp[i - 1][j - 1] + s, 'diag'], [dp[i - 1][j] - skipPenalty, 'up'], [dp[i][j - 1] - skipPenalty, 'left']];
    choices.sort((a, b) => b[0] - a[0]);
    [dp[i][j], move[i][j]] = choices[0];
  }
  const out = []; let i = n, j = m;
  while (i && j) {
    if (move[i][j] === 'diag') { const s = similarity(lyrics[i - 1], segments[j - 1]?.text ?? ''); if (s > 0) out.push([i - 1, j - 1, s]); i--; j--; }
    else if (move[i][j] === 'up') i--; else j--;
  }
  return out.reverse();
}
