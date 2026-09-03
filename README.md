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

## Current pipeline

```text
AUDIO + TRUSTED LYRICS
          |
    QUICK ANALYSIS
          |
    AVAILABLE ENGINES
          |
   PRIMARY EVIDENCE
          |
   GLOBAL MONOTONIC
      MATCHING
          |
    EVIDENCE MERGE
          |
    +-----+-----+
    |           |
  AGREE       CONFLICT
    |           |
 ACCEPT      TARGETED RETRY
                |
           CONSENSUS / REVIEW
                |
          FINAL TIMELINE
```

The public `AlignmentPipeline.run_audio()` path now executes configured timing engines through a common adapter interface. `AdaptiveAligner` keeps engine execution, lyric matching and evidence merging separate so heavy models can be added without changing the core data model.

## Architecture

```text
src/shesasyncer/
├── core/
│   ├── adaptive.py
│   ├── pipeline.py
│   └── models.py
├── media/
├── audio/
│   └── analysis.py
├── evidence/
├── lyrics/
├── alignment/
│   ├── anchor.py
│   └── sequence.py
├── consensus/
│   ├── confidence.py
│   └── merge.py
├── validation/
├── output/
└── engines/
    ├── adapters.py
    ├── whisperx.py
    ├── sofa.py
    └── demucs.py
```

## Engine strategy

WhisperX is integrated as an optional timing-evidence engine. It provides ASR and forced-alignment word timestamps; its recognised text is matched back to the trusted lyrics rather than replacing them. WhisperX's forced-alignment architecture is specifically intended to improve timestamp precision over raw Whisper segment timestamps. citeturn0search0turn0search2

SOFA remains an isolated singing-specific adapter. SOFA is designed for singing voice forced alignment and supports confidence output, making it suitable for the phoneme evidence layer rather than as the sole authority. citeturn1search0

The project intentionally does **not** vendor large model weights or copy entire third-party implementations. External engines stay behind adapters and can be installed/configured separately.

## Core principle

When the lyrics are already known, transcription is evidence, not truth. ShesASyncer should use recognition systems to discover **where** words or phonemes occur while preserving the supplied lyric text as the source of truth.

## Status

**Early working foundation.** The repository now has:

- dependency-free trusted lyric models
- global monotonic lyric-to-timing matching
- adaptive multi-engine orchestration
- confidence-weighted consensus
- disagreement protection
- targeted retry hooks
- optional WhisperX timing integration
- isolated SOFA integration boundary
- test coverage for consensus, conflicts and retries

Next production layer: vocal isolation and a real SOFA execution adapter, followed by word/character timeline refinement and objective alignment-quality metrics.

## License

MIT
