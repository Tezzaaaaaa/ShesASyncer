export class TimedSegment {
  constructor(start, end, text, confidence = 0, words = [], phonemes = []) { Object.assign(this, { start: Number(start), end: Number(end), text: String(text), confidence: Number(confidence), words: [...words], phonemes: [...phonemes] }); }
}

export class NullEngine {
  name = 'none';
  available() { return false; }
  align() { return []; }
}
