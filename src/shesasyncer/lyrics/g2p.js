import { execFileSync } from 'node:child_process';
import { existsSync, accessSync, constants } from 'node:fs';
import { which } from 'node:child_process';

export class G2PEngine {
  constructor(converter = null) { this.converter = converter; }
  available() { return typeof this.converter === 'function'; }
  convert(text, language = null) { return this.available() ? this.converter(text, language).map(String).map(x => x.trim()).filter(Boolean) : []; }
}

export class EspeakG2P extends G2PEngine {
  constructor(executable = null, { stripStress = true } = {}) {
    const resolved = executable || which('espeak-ng') || which('espeak');
    super((text, language) => this._convert(text, language));
    this.executable = resolved; this.stripStress = stripStress;
  }
  available() {
    if (!this.executable) return false;
    try { accessSync(this.executable, constants.X_OK); return true; } catch { return false; }
  }
  _convert(text, language = null) {
    if (!this.executable || !String(text).trim()) return [];
    try {
      const out = execFileSync(this.executable, ['-q', '--ipa', '--sep', ' ', '-v', language || 'en'], { input: text, encoding: 'utf8', timeout: 10000 });
      return tokenizeIpa(out, this.stripStress);
    } catch { return []; }
  }
}

export function tokenizeIpa(value, stripStress = true) {
  return String(value).trim().split(/\s+/).filter(Boolean).map(chunk => {
    if (stripStress) chunk = chunk.replace(/[ˈˌ]/g, '');
    return chunk.replace(/[͡‍]/g, '');
  }).filter(Boolean);
}
