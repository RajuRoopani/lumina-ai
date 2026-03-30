const { spawn } = require('child_process');

const proc = spawn('npm', ['run', 'dev'], {
  cwd: 'C:\\Work6\\lumina-ai\\frontend',
  stdio: 'inherit',
  shell: true,
});

proc.on('exit', (code) => process.exit(code ?? 0));
proc.on('error', (err) => { console.error(err); process.exit(1); });
