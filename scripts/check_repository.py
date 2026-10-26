"""Check tracked source for accidentally committed credentials or local data."""
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
files = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
problems = []
for name in filter(None, files):
    path = Path(name)
    if (path.name.startswith('.env') and not path.name.endswith('.example')) or path.suffix in {'.db', '.sqlite', '.sqlite3'} or any(part in {'.run', '.venv', 'node_modules', '.vercel'} for part in path.parts):
        problems.append(name + ': private/generated file')
        continue
    if path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.ico', '.woff', '.woff2'}:
        continue
    content = (root / name).read_text(encoding='utf-8', errors='replace')
    for pattern in [r'AIza[0-9A-Za-z_-]{35}', r'gh[pousr]_[A-Za-z0-9]{30,}', r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']:
        if re.search(pattern, content):
            problems.append(name + ': possible credential')
if problems:
    raise SystemExit('\n'.join(problems))
print('Tracked files: no detected API keys, private keys, local databases or environment files.')
