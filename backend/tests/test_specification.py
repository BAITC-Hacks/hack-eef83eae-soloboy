import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.data import Store, FILES, parse_dataset
from app.main import create_app
from app.models import Dataset
from app.recommender.engine import recommend, weights

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / 'data/sample'
JURY = ROOT / 'data/jury-example'


def test_additional_jury_profiles_preserve_existing_data(tmp_path):
    store = Store(str(tmp_path / 'jury.sqlite'), SAMPLE)
    before = store.snapshot()
    incoming = {n: (JURY / n).read_bytes() for n in ('employees.json', 'activity_history.csv')}
    merged = store.import_profiles(incoming)
    assert len(merged.employees) == len(before.employees) + 3
    assert merged.events == before.events
    assert merged.skills == before.skills
    assert merged.history[:len(before.history)] == before.history
    expected = {'JURY-DESIGN': 'EV003', 'JURY-CLOUD': 'EV021', 'JURY-ANALYTICS': 'EV008'}
    for employee_id, event_id in expected.items():
        employee = next(e for e in merged.employees if e.employee_id == employee_id)
        assert recommend(employee, merged)[0]['activity_id'] == event_id
    with pytest.raises(ValueError, match='already exist'):
        store.import_profiles(incoming)
    assert len(store.snapshot().employees) == len(merged.employees)
    store.db.close()


def test_additional_profiles_validate_atomically(tmp_path):
    store = Store(str(tmp_path / 'jury.sqlite'), SAMPLE)
    before = store.snapshot()
    incoming = {n: (JURY / n).read_bytes() for n in ('employees.json', 'activity_history.csv')}
    profiles = json.loads(incoming['employees.json'])
    profiles[0]['skills']['UNKNOWN'] = 2
    incoming['employees.json'] = json.dumps(profiles).encode()
    with pytest.raises(ValueError, match='Unknown skill'):
        store.import_profiles(incoming)
    assert store.snapshot() == before
    store.db.close()


@pytest.mark.parametrize('level', [-1, 6, 2.5, True])
def test_official_zero_to_five_scale(level):
    files = {n: (SAMPLE / n).read_bytes() for n in FILES}
    profiles = json.loads(files['employees.json'])
    profiles[0]['skills']['SK_PYTHON'] = level
    files['employees.json'] = json.dumps(profiles).encode()
    with pytest.raises(ValueError):
        parse_dataset(files)


@pytest.mark.parametrize('raw', ['{}', '[]', '1', 'false', '{"skill_gap": 1}'])
def test_invalid_weight_shapes_fail_clearly(monkeypatch, raw):
    monkeypatch.setenv('RECOMMENDATION_WEIGHTS', raw)
    with pytest.raises(ValueError):
        weights()


def test_malformed_csv_rejected():
    files = {n: (SAMPLE / n).read_bytes() for n in FILES}
    files['activity_history.csv'] = b'employee_id,event_id,date,status\nE0001,EV001,2026-01-01,skipped,unexpected\n'
    with pytest.raises(ValueError, match='same number'):
        parse_dataset(files)


def test_jury_import_authorization_and_hr_inactivity(tmp_path, monkeypatch):
    monkeypatch.setenv('DEMO_MODE', 'true')
    with TestClient(create_app(str(tmp_path / 'api.sqlite'), SAMPLE)) as client:
        employee = client.post('/auth/login', json={'role': 'employee', 'employee_id': 'E0001'}).json()['token']
        employee_auth = {'Authorization': f'Bearer {employee}'}
        files = [('files', (n, (JURY / n).read_bytes())) for n in ('employees.json', 'activity_history.csv')]
        assert client.post('/dataset/profiles', files=files, headers=employee_auth).status_code == 403
        token = client.post('/auth/login', json={'role': 'hr'}).json()['token']
        auth = {'Authorization': f'Bearer {token}'}
        assert client.post('/dataset/profiles', files=files, headers=auth).json()['employees'] == 15
        # Adding new identities does not invalidate an existing employee session.
        assert client.get('/employees/E0001', headers=employee_auth).status_code == 200
        dashboard = client.get('/hr/dashboard', headers=auth).json()
        cloud = next(e for e in dashboard['employees'] if e['employee_id'] == 'JURY-CLOUD')
        assert cloud['last_completed'] is None
        assert cloud['active_development'] is False


def test_non_ascii_access_key_and_bad_credentials_configuration(tmp_path, monkeypatch):
    monkeypatch.setenv('DEMO_MODE', 'false')
    monkeypatch.setenv('HR_ACCESS_KEY', 'test-key')
    monkeypatch.setenv('EMPLOYEE_CREDENTIALS_FILE', str(tmp_path / 'missing.json'))
    with TestClient(create_app(str(tmp_path / 'auth.sqlite'), SAMPLE)) as client:
        assert client.post('/auth/login', json={'role': 'hr', 'access_key': 'неверный'}).status_code == 401
        assert client.post('/auth/login', json={'role': 'employee', 'employee_id': 'E0001'}).status_code == 503
