const { execSync } = require('child_process');

function run(cmd) {
  try {
    const out = execSync(cmd, { encoding: 'utf8', shell: true });
    console.log(`[keepalive] ${cmd}\n${out.trim()}`);
  } catch (e) {
    console.error(`[keepalive] FAILED: ${cmd}\n${e.message}`);
  }
}

console.log(`[keepalive] Running at ${new Date().toISOString()}`);

// Re-auth devtunnel using integrated Windows auth (silent, no browser needed)
run('devtunnel user login -w');

// Restart tunnel processes so they pick up fresh auth token
run('pm2 restart lumina-tunnel-backend lumina-tunnel-ui');

console.log('[keepalive] Done.');
