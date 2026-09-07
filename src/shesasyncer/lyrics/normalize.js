export function normalizeLyric(text) {
  return String(text).normalize('NFKC').toLocaleLowerCase().replace(/[^\p{L}\p{N}_]+/gu, '');
}

export function lyricTokens(text) {
  return String(text).normalize('NFKC').toLocaleLowerCase().match(/[\p{L}\p{N}_]+/gu) ?? [];
}
