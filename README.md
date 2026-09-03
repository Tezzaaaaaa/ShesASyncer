# ShesASyncer

AI-backed lyric alignment engine for accurate synchronisation of trusted lyrics to audio.

## Purpose

ShesASyncer aligns **trusted lyric text** to the actual timing of an audio recording. It does not replace trusted lyrics with an ASR transcript. ASR, forced alignment, phoneme alignment and vocal analysis are treated as timing evidence that can be combined, scored and cross-checked.

## Design goals

- Trusted lyrics remain canonical.
- Fast paths for clean audio; expensive processing only when needed.
- Singing-aware alignment rather than speech-only assumptions.
- Line, word and character timing where evidence supports it.
- Explicit confidence and uncertainty.
- Conflict detection instead of silently accepting bad timestamps.
- Targeted retries on difficult sections rather than rerunning the whole track.
- Adapter-based external engines so individual models can be replaced without changing the core pipeline.
- Deterministic, machine-readable alignment output suitable for KEFE.

## Planned pipeline

```text
AUDIO + TRUSTED LYRICS
          |
    QUICK ANALYSIS
          |
    +-----+-----+
    |           |
   CLEAN      DIFFICULT
    |           |
 DIRECT      VOCAL / AUDIO
 ALIGN       ANALYSIS
    |           |
    +-----+-----+
          |
   PRIMARY ALIGNMENT
          |
    +-----+-----+
    |           |
 phoneme      timing
 evidence     evidence
    |           |
    +-----+-----+
          |
    EVIDENCE MERGE
          |
    +-----+-----+
    |           |
  AGREE       CONFLICT
    |           |
 ACCEPT     TARGETED RETRY
                |
           CONSENSUS / REVIEW
                |
          FINAL TIMELINE
```

## Architecture

```text
src/shesasyncer/
├── core/
│   ├── pipeline.py
│   ├── models.py
│   ├── timeline.py
│   └── result.py
├── media/
│   ├── ingest.py
│   ├── probe.py
│   └── normalize.py
├── audio/
│   ├── separation.py
│   ├── activity.py
│   └── analysis.py
├── evidence/
│   ├── asr.py
│   ├── phoneme.py
│   └── vocal.py
├── lyrics/
│   ├── parser.py
│   ├── normalize.py
│   └── trusted.py
├── alignment/
│   ├── anchor.py
│   ├── sequence.py
│   ├── forced.py
│   └── refinement.py
├── consensus/
│   ├── scorer.py
│   ├── confidence.py
│   └── conflict.py
├── validation/
│   ├── temporal.py
│   ├── continuity.py
│   └── quality.py
├── output/
│   ├── lrc.py
│   ├── elrc.py
│   └── kefe.py
└── engines/
    ├── whisper.py
    ├── whisperx.py
    ├── sofa.py
    ├── demucs.py
    └── adapters.py
```

## Core principle

When the lyrics are already known, transcription is evidence, not truth. ShesASyncer should use recognition systems to discover **where** words or phonemes occur while preserving the supplied lyric text as the source of truth.

## External techniques

The architecture is designed to take advantage of established approaches such as character-level lyric anchoring, word-level timestamps, forced alignment and singing-oriented phoneme alignment without coupling the project to a single implementation.

## Status

Early implementation. The repository currently contains the architectural foundation and project specification; engine integrations and the production alignment pipeline are being built incrementally.

## License

MIT
