export class LyricLine {
  constructor(index, text) { this.index = index; this.text = String(text); Object.freeze(this); }
}

export class Timing {
  constructor(start, end, confidence = 0, source = 'consensus') {
    this.start = Number(start); this.end = Number(end); this.confidence = Number(confidence); this.source = source; Object.freeze(this);
  }
}

export class AlignmentEvidence {
  constructor(lineIndex, timing, { matchedText = '', score = 0, source = 'asr', metadata = {} } = {}) {
    this.lineIndex = lineIndex; this.timing = timing; this.matchedText = matchedText; this.score = score; this.source = source; this.metadata = metadata;
  }
}

export class AlignmentResult {
  constructor(lines, confidence, warnings = [], evidence = []) {
    this.lines = lines; this.confidence = confidence; this.warnings = warnings; this.evidence = evidence;
  }
}
