"""Run browser tests against a disposable database, never the user's workspace."""
import os
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'backend'))
os.environ['DEMO_MODE'] = 'true'
os.environ['OPENAI_API_KEY'] = ''
os.environ['DATASET_DIR'] = str(root / 'data/sample')
with tempfile.TemporaryDirectory(prefix='career-quest-e2e-') as directory:
    os.environ['STATE_DB'] = str(Path(directory) / 'test.sqlite')
    import uvicorn
    uvicorn.run('app.main:app', host='127.0.0.1', port=8001)
