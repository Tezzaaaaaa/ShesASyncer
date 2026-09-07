# ShesASyncer

AI-backed lyric alignment engine for accurate synchronisation of trusted lyrics to audio.

## Runtime

ShesASyncer is now a **Node.js / JavaScript ES-module project**. The Python implementation has been removed from this port.

Requirements:

- Node.js 20+
- Optional eSpeak NG for phoneme generation
- Acoustic/model runners are injected as adapters; model weights are not bundled

Install and test:

```bash
npm install
npm test
```

## Purpose

ShesASyncer aligns **trusted lyric text** to the actual timing of an audio recording. It never replaces trusted lyrics with an ASR transcript. Recognition, acoustic phoneme evidence and vocal analysis are timing evidence that can be combined, scored and cross-checked.

## Architecture

```text
AUDIO + TRUSTED LYRICS
          |
     QUICK ANALYSIS
          |
    ┌─────┴───────────┐
    |                 |
 CLEAN ENOUGH      DIFFICULT
    |                 |
 CTC PHONEME       OTHER EVIDENCE
 EVIDENCE              |
    |                 |
    └────────┬────────┘
             |
      SHESASYNCER DECODER
       + EVIDENCE MERGE
             |
      ┌──────┴──────┐
      |             |
    AGREE         CONFLICT
      |             |
    ACCEPT      TARGETED RETRY
                    |
               CONSENSUS
                    |
             FINAL TIMELINE
```

## JavaScript API

```js
import { AlignmentPipeline, CtcSingingEngine, EspeakG2P } from 'shesasyncer';
```

Core exports include `AlignmentPipeline`, `AdaptiveAligner`, trusted lyric models, monotonic matching, consensus/confidence handling, timeline validation, word/character refinement, the native phoneme decoder, and the CTC singing engine.

### CTC path

The CTC path uses an injected acoustic runner plus ShesASyncer's own CTC Viterbi decoder. The decoder explicitly handles CTC blanks and repeated phonemes. `EspeakG2P` can supply IPA phonemes at runtime.

### Trusted text

Trusted lyrics remain canonical. Timing evidence can be uncertain or rejected; the engine does not silently substitute recognised text for the supplied lyrics.

## CLI

```bash
shesasyncer --lyrics lyrics.txt --segments segments.json --output aligned.json
```

`segments.json` contains timed evidence such as:

```json
[{"start":0,"end":1.2,"text":"hello world"}]
```

## Status

**Active development.** The JavaScript port contains the core alignment, adaptive arbitration, consensus, validation, refinement, native phoneme decoding and CTC timing path. Model-specific acoustic runners and production KEFE integration remain adapter-level work.

## License

MIT
