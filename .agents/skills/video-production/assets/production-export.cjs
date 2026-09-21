// Normal exports always check the recorded review gate before invoking Remotion.
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
const check = spawnSync('uv', ['run', '--no-project', '--python',
  process.env.VIDEO_PRODUCTION_PYTHON || config.python, 'python',
  path.join(__dirname, 'production/09_check_production.py'), '--project-dir', root,
  '--production-state', config.state, '--stage', 'render'], {cwd: root, stdio: 'inherit'});
if (check.error || check.status !== 0) {
  if (check.error) console.error(check.error.message);
  process.exit(check.status || 1);
}
const cli = path.join(path.dirname(require.resolve('@remotion/cli/package.json', {paths: [root]})), 'remotion-cli.js');
const args = mode === 'render'
  ? ['render', 'src/index.ts', 'VideoFull', 'out/video.mp4', '--codec=h264', '--pixel-format=yuv420p']
  : ['still', 'src/index.ts', 'VideoFull', 'out/video-hero.png', `--frame=${config.lastFrame}`];
const result = spawnSync(process.execPath, [cli, ...args], {cwd: root, stdio: 'inherit'});
if (result.error) console.error(result.error.message);
process.exit(result.status === null ? 1 : result.status);
