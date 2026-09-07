import test from 'node:test';
import assert from 'node:assert/strict';
import { AlignmentPipeline, TimedSegment, validateTimeline, normalizeLyric } from '../src/shesasyncer/index.js';

test('normalizes lyric text without changing the source lyric', async () => {
  assert.equal(normalizeLyric('Hello, WORLD!'), 'helloworld');
});

test('aligns trusted lyrics to ordered timed segments', () => {
  const pipeline = new AlignmentPipeline();
  const result = pipeline.run(['Hello world', 'Good night'], [
    new TimedSegment(0, 1.2, 'hello world', 0.95),
    new TimedSegment(1.3, 2.4, 'good night', 0.95)
  ]);
  assert.equal(result.lines[0].start, 0);
  assert.equal(result.lines[1].start, 1.3);
  assert.equal(result.lines[0].text, 'Hello world');
});

test('rejects overlapping timeline evidence', () => {
  const result = validateTimeline([
    { lineIndex: 0, timing: { start: 0, end: 1 } },
    { lineIndex: 1, timing: { start: 0.5, end: 2 } }
  ]);
  assert.equal(result.valid, false);
  assert.equal(result.errors[0].code, 'overlap');
});
