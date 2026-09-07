export function refineEvidence(evidence) {
  return evidence.map(item => {
    const words = cleanWords(item.metadata?.words);
    if (!words.length) return item;
    const mapped = mapWords(item.matchedText, words);
    if (!mapped.length) return item;
    const metadata = { ...item.metadata, words: mapped, characters: characterTimings(item.matchedText, mapped), refinement: 'word-to-character' };
    return { ...item, metadata };
  });
}

function cleanWords(words) {
  if (!Array.isArray(words)) return [];
  return words.flatMap(word => {
    if (!word || typeof word !== 'object') return [];
    const start = Number(word.start), end = Number(word.end), text = String(word.word ?? word.text ?? '').trim();
    if (!text || !Number.isFinite(start) || !Number.isFinite(end) || !(end > start) || start < 0) return [];
    return [{ text, start, end, confidence: Number(word.confidence ?? 0) || 0 }];
  });
}

function mapWords(lyric, words) {
  const tokens = [...String(lyric).matchAll(/\S+/g)].map(m => ({ start: m.index, end: m.index + m[0].length, text: m[0] }));
  const mapped = []; let offset = 0;
  for (const token of tokens) {
    let found = -1;
    for (let i = offset; i < words.length; i++) if (token.text.localeCompare(words[i].text, undefined, { sensitivity: 'base' }) === 0) { found = i; break; }
    if (found >= 0) { const word = words[found]; mapped.push({ text: token.text, start: word.start, end: word.end, confidence: word.confidence, lyricStart: token.start, lyricEnd: token.end }); offset = found + 1; }
  }
  return mapped;
}

function characterTimings(lyric, words) {
  const result = [];
  for (const word of words) {
    const chars = [...String(lyric).slice(word.lyricStart, word.lyricEnd)].filter(c => !/\s/.test(c));
    if (!chars.length) continue;
    const step = (word.end - word.start) / chars.length;
    chars.forEach((char, index) => result.push({ char, start: word.start + step * index, end: index === chars.length - 1 ? word.end : word.start + step * (index + 1), confidence: word.confidence }));
  }
  return result;
}
