# ShesASyncer

AI-backed lyric alignment engine for accurate synchronisation of trusted lyrics to audio.

## Purpose

ShesASyncer aligns **trusted lyric text** to the actual timing of an audio recording. It never replaces trusted lyrics with an ASR transcript. Recognition, acoustic phoneme evidence and vocal analysis are timing evidence that can be combined, scored and cross-checked.

## Design goals

- Trusted lyrics remain canonical.
- Fast paths for clean audio; expensive processing only when needed.
- Singing-aware alignment without copying a third-party aligner's architecture.
- Line, word and phoneme timing where evidence supports it.
- Explicit confidence and uncertainty.
- Conflict detection instead of silently averaging contradictory timestamps.
- Targeted retries on difficult sections.
- Replaceable model adapters with ShesASyncer-owned decoding and consensus.
- Deterministic output suitable for KEFE.

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
 CTC PHONEME       VOCAL / OTHER
 EVIDENCE          EVIDENCE
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

The core alignment logic owns the temporal decoding, matching, confidence, conflict handling and output. Acoustic models are interchangeable evidence providers.

## Native CTC path

The native path is a **Wav2Vec2-style acoustic encoder + phoneme CTC posterior + ShesASyncer CTC decoder**. This is deliberately different from SOFA's singing-aligner architecture.

The repository provides:

- `G2PEngine` for an injectable grapheme-to-phoneme boundary.
- `EspeakG2P` for runtime eSpeak NG IPA conversion.
- `AcousticFrame` for model-independent frame/posterior data.
- CTC Viterbi decoding with explicit blank handling and repeated-phoneme support.
- `CtcSingingEngine` for reconstructing trusted lyric-line timings.
- `OnnxCtcRunner` for local ONNX Runtime inference.
- Optional NumPy/ONNX dependencies; model weights remain external.

A suitable external reference model is the Apache-2.0 `wav2vec2-espeak-ctc` ONNX export, which accepts mono 16 kHz audio and emits 392 IPA CTC classes at approximately 50 frames/second. Model assets are intentionally not bundled into this repository. citeturn0search0turn0search3

## External engines

WhisperX remains optional timing evidence. Its recognized text is matched back to trusted lyrics rather than becoming the source of truth.

SOFA remains an isolated optional singing-specific evidence adapter. It is not required by the native CTC path.

The project does **not** vendor large model weights or copy third-party implementations. External engines stay behind adapters and can be replaced without changing the core timeline model.

## Installation

Core package:

```bash
python -m pip install -e .
```

Tests:

```bash
python -m pip install -e '.[test]'
python -m pytest -q
```

ONNX CTC runtime:

```bash
python -m pip install -e '.[onnx]'
```

Install eSpeak NG separately when using `EspeakG2P`. The adapter discovers `espeak-ng` or `espeak` at runtime.

## Status

**Active development.** The repository now has the core adaptive alignment foundation plus a native CTC phoneme-alignment path. The remaining production work is model validation on representative singing audio, vocal-isolation routing for difficult mixes, objective timing benchmarks and KEFE integration.

## License

MIT
