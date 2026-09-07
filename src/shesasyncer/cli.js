#!/usr/bin/env node
import fs from 'node:fs/promises';
import { AlignmentPipeline } from './core/pipeline.js';

function usage() {
  console.error('Usage: shesasyncer --lyrics lyrics.txt --segments segments.json [--output output.json]');
  console.error('segments.json must contain [{"start":0,"end":1,"text":"..."}]');
}

const args = process.argv.slice(2);
const value = flag => { const i = args.indexOf(flag); return i >= 0 ? args[i + 1] : null; };
const lyricsPath = value('--lyrics'), segmentsPath = value('--segments'), outputPath = value('--output');
if (!lyricsPath || !segmentsPath) { usage(); process.exit(1); }

const lyrics = (await fs.readFile(lyricsPath, 'utf8')).split(/\r?\n/).map(x => x.trim()).filter(Boolean);
const segments = JSON.parse(await fs.readFile(segmentsPath, 'utf8'));
const result = new AlignmentPipeline().run(lyrics, segments);
const json = JSON.stringify(result, null, 2) + '\n';
if (outputPath) await fs.writeFile(outputPath, json); else process.stdout.write(json);
