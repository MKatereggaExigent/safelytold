import { spawnSync } from 'node:child_process';

const apps = [
  './apps/reporter-web',
  './apps/staff-web',
  './apps/trust-center-web',
];

const pnpm = process.platform === 'win32' ? 'pnpm.cmd' : 'pnpm';
const env = { ...process.env, NEXT_TELEMETRY_DISABLED: '1' };

for (const app of apps) {
  console.log(`\n--- building ${app} ---`);
  const result = spawnSync(pnpm, ['--filter', app, 'build'], {
    stdio: 'inherit',
    env,
  });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}
