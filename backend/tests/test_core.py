import asyncio
import json
from datetime import date, timedelta
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.data import FILES, Store, parse_dataset
from app.main import create_app
from app.models import Dataset, Employee, Event, Skill, History
from app.recommender.engine import recommend
from app.recommender.trajectory import analyze
from app.recommender.history import history_factor
from app.ai.explanation_service import ExplanationService

SAMPLE = Path(__file__).resolve().parents[2] / 'data/sample'


@pytest.fixture
def data():
    return Dataset(employees=[Employee(employee_id='A', role='Engineer', grade='Middle', tenure_months=24,
                                     skills={'DESIGN': 2, 'SPEAK': 1})],
                   skills=[Skill(skill_id='DESIGN', name='System Design', category='hard', importance=2,
                                 requirements={'Middle': 2, 'Senior': 4}),
                           Skill(skill_id='SPEAK', name='Public Speaking', category='soft', requirements={'Middle': 2, 'Senior': 3})],
                   events=[Event(event_id='D', name='Design workshop', skills=[{'skill_id': 'DESIGN', 'gain': 3, 'max_level': 4}]),
                           Event(event_id='S', name='Speaking workshop', skills=[{'skill_id': 'SPEAK', 'gain': 1, 'max_level': 4}]),
                           Event(event_id='OLD', name='Design primer', skills=[{'skill_id': 'DESIGN', 'gain': 1, 'max_level': 2}])],
                   history=[History(employee_id='A', event_id='S', date=date.today() - timedelta(days=i), status='skipped') for i in (1, 7, 30)] +
                           [History(employee_id='A', event_id='OLD', date=date.today(), status='completed')])


def test_gap_next_grade_and_progress(data):
    result = analyze(data.employees[0], data)
    assert result['next_grade'] == 'Senior'
    assert [s['gap'] for s in result['skills']] == [2, 2]
    assert result['progress'] == 42.9


def test_difficult_profile_lowest_skill_is_not_recommendation(data):
    results = recommend(data.employees[0], data)
    assert min(data.employees[0].skills, key=data.employees[0].skills.get) == 'SPEAK'
    assert results[0]['activity_id'] == 'D'
    assert len(results[0]['reasoning']) == 5
    assert 0 <= results[0]['score'] <= 1
    assert results[0]['score'] == round(sum(results[0]['factors'][k] * w for k, w in results[0]['weights'].items()), 4)


def test_history_influence_decays(data):
    employee, event = data.employees[0], data.events[1]
    recent, _ = history_factor(employee, event, data)
    old, _ = history_factor(employee, event, data, today=date.today() + timedelta(days=1500))
    assert recent < old < .5
    assert any(r['activity_id'] == 'S' for r in recommend(employee, data))


def test_completion_cap_persistence_and_idempotence(tmp_path, data):
    db = str(tmp_path / 'state.sqlite')
    store = Store(db, SAMPLE)
    store.replace(data)
    assert store.complete('A', 'D')['changes'][0] == {'skill_id': 'DESIGN', 'before': 2, 'after': 4}
    assert store.complete('A', 'D')['already_completed']
    assert len(store.snapshot().history) == 5
    assert all(r['activity_id'] != 'D' for r in recommend(store.snapshot().employees[0], store.snapshot()))
    store.db.close()
    restarted = Store(db, SAMPLE)
    assert restarted.snapshot().employees[0].skills['DESIGN'] == 4
    restarted.db.close()


def test_cap_never_reduces_existing_level(tmp_path, data):
    data.employees[0].skills['DESIGN'] = 5
    store = Store(str(tmp_path / 'state.sqlite'), SAMPLE)
    store.replace(data)
    assert store.complete('A', 'D')['changes'][0]['after'] == 5
    store.db.close()


def test_validation_references_and_duplicates(data):
    raw = data.model_dump(mode='json')
    raw['employees'][0]['skills']['MISSING'] = 1
    with pytest.raises(ValueError):
        Dataset.model_validate(raw)
    raw = data.model_dump(mode='json')
    raw['employees'].append(raw['employees'][0])
    with pytest.raises(ValueError):
        Dataset.model_validate(raw)


def test_no_llm_and_failure_fallback(data, monkeypatch):
    rec = recommend(data.employees[0], data)[0]
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    assert asyncio.run(ExplanationService().explain(rec))['source'] == 'deterministic'
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    async def fail(*args, **kwargs):
        raise RuntimeError('offline')
    monkeypatch.setattr('httpx.AsyncClient.post', fail)
    assert asyncio.run(ExplanationService().explain(rec))['source'] == 'deterministic'


def test_api_roles_upload_and_invalid_employee(tmp_path, monkeypatch):
    monkeypatch.setenv('DEMO_MODE', 'true')
    with TestClient(create_app(str(tmp_path / 'api.sqlite'), SAMPLE)) as client:
        assert client.get('/health').json()['status'] == 'ok'
        employee_id = client.get('/demo/employees').json()[0]['employee_id']
        token = client.post('/auth/login', json={'role': 'employee', 'employee_id': employee_id}).json()['token']
        auth = {'Authorization': f'Bearer {token}'}
        assert client.get('/hr/dashboard', headers=auth).status_code == 403
        assert client.get('/employees/E0002', headers=auth).status_code == 403
        assert len(client.get('/employees', headers=auth).json()) == 1
        for path in ('', '/skills', '/trajectory', '/recommendations', '/history', '/activities'):
            assert client.get(f'/employees/{employee_id}{path}', headers=auth).status_code == 200
        hr = client.post('/auth/login', json={'role': 'hr'}).json()['token']
        auth = {'Authorization': f'Bearer {hr}'}
        assert client.get('/employees/MISSING', headers=auth).status_code == 404
        assert client.get('/hr/dashboard', headers=auth).status_code == 200
        files = [('files', (name, (SAMPLE / name).read_bytes())) for name in FILES]
        assert client.post('/dataset/upload', headers=auth, files=files).json()['employees'] == 12
        assert client.get('/employees', headers={'Authorization': f'Bearer {token}'}).status_code == 401
        files[0] = ('files', ('employees.json', b'[]'))
        assert client.post('/dataset/upload', headers=auth, files=files).status_code == 422
        assert client.get('/dataset/status', headers=auth).json()['employees'] == 12


def test_production_requires_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv('DEMO_MODE', 'false')
    monkeypatch.setenv('HR_ACCESS_KEY', 'private-test-key')
    with TestClient(create_app(str(tmp_path / 'prod.sqlite'), SAMPLE)) as client:
        assert client.get('/demo/employees').status_code == 403
        assert client.get('/employees').status_code == 401
        assert client.post('/auth/login', json={'role': 'hr'}).status_code == 401
        assert client.post('/auth/login', json={'role': 'hr', 'access_key': 'private-test-key'}).status_code == 200


def test_empty_history_and_top_grade(data):
    data.history = []
    data.employees[0].grade = 'Senior'
    assert analyze(data.employees[0], data)['next_grade'] is None
    assert recommend(data.employees[0], data)
