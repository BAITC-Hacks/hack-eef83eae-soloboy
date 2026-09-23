"""One-command setup/build/run. Uses a project-local virtual environment."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
windows = os.name == 'nt'
python = ROOT / ('.venv/Scripts/python.exe' if windows else '.venv/bin/python')
if not python.exists():
    subprocess.run([sys.executable, '-m', 'venv', str(ROOT / '.venv')], check=True)
node_dirs = list((ROOT / '.tools').glob('node-*-win-x64')) if (ROOT / '.tools').exists() else []
if not shutil.which('node') and node_dirs:
    os.environ['PATH'] = str(node_dirs[0]) + os.pathsep + os.environ['PATH']
npm = shutil.which('npm.cmd' if windows else 'npm')
if not npm:
    sys.exit('Install Node.js 22.12+ and rerun: python run.py')
subprocess.run([str(python), '-m', 'pip', 'install', '-r', 'backend/requirements.lock.txt'], check=True)
subprocess.run([npm, 'ci'], cwd=ROOT / 'frontend', check=True)
subprocess.run([npm, 'run', 'build'], cwd=ROOT / 'frontend', check=True)
print('\nCareer Quest: http://127.0.0.1:8000\nPress Ctrl+C to stop.\n', flush=True)
try:
    subprocess.run([str(python), '-m', 'uvicorn', 'app.main:app', '--app-dir', 'backend', '--host', '127.0.0.1', '--port', '8000'], check=True)
except KeyboardInterrupt:
    pass
