const fs = require('node:fs');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
const config = JSON.parse(fs.readFileSync(path.join(__dirname, 'production/export-config.json'), 'utf8'));
const mode = process.argv[2];
if (!['render', 'hero'].includes(mode) || process.argv.length !== 3) {
  console.error('Usage: production-export.cjs render|hero');
  process.exit(1);
}
const runPython = (args) => {
  let result = spawnSync('uv', ['run', '--no-project', '--python', config.python, 'python', ...args], {cwd: root, stdio: 'inherit'});
  if (result.error && result.error.code === 'ENOENT') {
    console.error('WARNING: uv is unavailable; using the project-local configured Python interpreter directly.');
    result = spawnSync(config.python, args, {cwd: root, stdio: 'inherit'});
  }
  return result;
};
const review = runPython([path.join(__dirname, 'production/check_production_v1.py'), '--project-dir', root,
  '--project', config.project, '--state', config.state]);
if (review.error || review.status !== 0) process.exit(review.status || 1);
const qc = runPython([path.join(__dirname, 'production/run_qc.py'), '--timeline', path.join(root, 'src/timeline-data.json'),
  '--out', path.join(root, 'qc/render-timeline.json')]);
if (qc.error || qc.status !== 0) process.exit(qc.status || 1);
const timeline = JSON.parse(fs.readFileSync(path.join(root, 'src/timeline-data.json'), 'utf8'));
const lastFrame = timeline.totalFrames - 1;
if (!Number.isSafeInteger(lastFrame) || lastFrame < 0) {
  console.error('Invalid final frame. Recompile the editorial timeline.');
  process.exit(1);
}
const cli = path.join(path.dirname(require.resolve('@remotion/cli/package.json', {paths: [root]})), 'remotion-cli.js');
const args = mode === 'render'
  ? ['render', 'src/index.ts', 'VideoFull', 'out/video.mp4', '--codec=h264', '--pixel-format=yuv420p']
  : ['still', 'src/index.ts', 'VideoFull', 'out/video-hero.png', `--frame=${lastFrame}`];
const result = spawnSync(process.execPath, [cli, ...args], {cwd: root, stdio: 'inherit'});
process.exit(result.status === null ? 1 : result.status);
