# ShesASyncer real-song test kit

This is the shortest path to testing the native CTC aligner on an actual song.

## 1. Install

```bash
python -m pip install -e '.[onnx,test]'
```

Install eSpeak NG separately and make sure `espeak-ng --version` works.

For MP3/M4A/FLAC input, install ffmpeg. A 16-bit PCM WAV at 16 kHz is accepted without ffmpeg.

## 2. Get the reference acoustic model

```bash
python -m shesasyncer model setup
```

This downloads the Apache-2.0 `sadda-speech/wav2vec2-espeak-ctc` ONNX acoustic model and its vocabulary into `~/.cache/shesasyncer/model/`.

The model is approximately 635 MB. It expects mono 16 kHz audio and emits 392 IPA CTC classes at about 50 frames/second.

## 3. Align a song

Put trusted lyrics in `lyrics.txt` (one lyric line per line), or provide an LRC file.

```bash
python -m shesasyncer align song.mp3 lyrics.txt
```

The command produces three files beside the audio:

- `song.shesasyncer.json` — machine-readable result, confidence, warnings and timings
- `song.shesasyncer.lrc` — generated line timings
- `song.shesasyncer.html` — visual timing report for inspection

The installed console command is also available:

```bash
shesasyncer align song.mp3 lyrics.lrc
```

## 4. What to test

Use several real songs, not just one. Keep the supplied lyrics authoritative.

### A — clean lead vocal

Expected: most lines receive high-confidence timings with boundaries close to the sung words.

### B — dense production

Test a normal commercial mix with drums, synths and other instruments.

Expected: alignment should remain stable without replacing lyrics with an ASR transcript.

### C — harmonies / backing vocals

Expected: the main lyric timing should follow the intended lead vocal rather than an earlier/later backing vocal.

### D — reverb / live recording

Expected: confidence may fall, but timings should not silently jump to unrelated vocal echoes.

### E — stretched syllables / melisma

Expected: a lyric line can span a long sung syllable without being compressed to speech-like timing.

### F — repeated words / phonemes

Expected: repeated lyric tokens remain in the correct order and are not collapsed together.

### G — accent / slang

Expected: trusted lyric text remains unchanged even when acoustic pronunciation differs from written spelling.

## 5. What counts as a failure

Report a failure when any of these happen:

- a line is consistently early or late by a noticeable amount;
- a line locks onto backing vocals instead of the intended vocal;
- repeated words are assigned to the wrong occurrence;
- a long held syllable is given an implausibly short duration;
- a lyric is silently changed to match recognition output;
- confidence is high despite visibly incorrect timing;
- difficult sections produce plausible-looking but wrong timestamps instead of uncertainty.

The HTML report is the first thing to inspect. The JSON is the machine-readable artifact for later benchmarking and KEFE integration.

## 6. Important limitation

The reference acoustic model is a phoneme-recognition model trained primarily for speech. The ShesASyncer decoder is singing-aware, but real singing accuracy still has to be demonstrated experimentally. Do not treat a successful command or high confidence as proof of production accuracy.
