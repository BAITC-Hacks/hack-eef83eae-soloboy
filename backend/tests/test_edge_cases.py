import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.data import Store, FILES, parse_dataset
from app.main import create_app
from app.recommender.engine import recommend, weights
from app.ai.explanation_service import ExplanationService

SAMPLE = Path(__file__).resolve().parents[2] / 'data/sample'


def sample():
    return parse_dataset({n: (SAMPLE / n).read_bytes() for n in FILES})


def test_concurrent_completion_only_credits_once(tmp_path):
    store = Store(str(tmp_path / 'state.sqlite'), SAMPLE)
    before = store.snapshot()
    employee = before.employees[0]
    event = recommend(employee, before)[0]['activity_id']
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: store.complete(employee.employee_id, event), range(4)))
    assert sum(not r['already_completed'] for r in results) == 1
    assert len(store.snapshot().history) == len(before.history) + 1
    store.db.close()


def test_upload_new_identity_drives_real_recommendations(tmp_path, monkeypatch):
    monkeypatch.setenv('DEMO_MODE', 'true')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    payload = {
        'employees.json': json.dumps([{'employee_id': 'NEW-901', 'grade': 'Junior', 'role': 'Tester', 'tenure_months': 1, 'skills': {'NEW-SKILL': 1}}]),
        'events.json': json.dumps([{'event_id': 'NEW-EVENT', 'name': 'New Workshop', 'skills': [{'skill_id': 'NEW-SKILL', 'gain': 2, 'max_level': 2}]}]),
        'skills.json': json.dumps([{'skill_id': 'NEW-SKILL', 'name': 'Testing', 'category': 'hard', 'requirements': {'Junior': 1, 'Middle': 3}}]),
        'activity_history.csv': 'employee_id,event_id,date,status\n',
    }
    with TestClient(create_app(str(tmp_path / 'api.sqlite'), SAMPLE)) as client:
        token = client.post('/auth/login', json={'role': 'hr'}).json()['token']
        auth = {'Authorization': f'Bearer {token}'}
        result = client.post('/dataset/upload', headers=auth, files=[('files', (n, content.encode())) for n, content in payload.items()])
        assert result.status_code == 200
        recs = client.get('/employees/NEW-901/recommendations', headers=auth).json()
        assert recs[0]['activity_id'] == 'NEW-EVENT'
        assert recs[0]['skills'][0]['gain'] == 1
        assert recs[0]['explanation_source'] == 'deterministic'
        response = client.post('/employees/NEW-901/activities/NEW-EVENT/complete', headers=auth)
        assert response.json()['changes'][0]['after'] == 2
        assert client.get('/employees/NEW-901/trajectory', headers=auth).json()['progress'] == 66.7
        assert client.get('/employees/NEW-901/recommendations', headers=auth).json() == []
        assert client.get('/hr/dashboard', headers=auth).json()['completion_rate'] == 100


@pytest.mark.parametrize('answer,expected', [
    ('["skill_gap","history","activity_effect"]', 'llm-assisted'),
    ('["you will get promoted", "history", "activity_effect"]', 'deterministic'),
    ('["skill_gap", "skill_gap", "history"]', 'deterministic'),
    ('not json', 'deterministic'),
])
def test_llm_grounding_and_cache(monkeypatch, answer, expected):
    import httpx
    calls = []
    async def post(*args, **kwargs):
        calls.append(1)
        return httpx.Response(200, request=httpx.Request('POST', 'https://example.test'), json={'choices': [{'message': {'content': answer}}]})
    monkeypatch.setattr('httpx.AsyncClient.post', post)
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    data = sample()
    rec = recommend(data.employees[0], data)[0]
    service = ExplanationService()
    result = asyncio.run(service.explain(rec))
    assert result['source'] == expected
    assert 'you will get promoted' not in result['text']
    assert asyncio.run(service.explain(rec)) == result
    assert len(calls) == 1


def test_invalid_weights(monkeypatch):
    monkeypatch.setenv('RECOMMENDATION_WEIGHTS', '{"skill_gap": 1}')
    with pytest.raises(ValueError):
        weights()


def test_200_employee_hr_performance(tmp_path, monkeypatch):
    monkeypatch.setenv('DEMO_MODE', 'true')
    data = sample()
    originals = data.employees
    history = data.history
    data.employees = []
    data.history = []
    for i in range(200):
        employee = originals[i % len(originals)].model_copy(deep=True)
        old_id, employee.employee_id = employee.employee_id, f'PERF{i:04}'
        data.employees.append(employee)
        data.history.extend(h.model_copy(update={'employee_id': employee.employee_id}) for h in history if h.employee_id == old_id)
    with TestClient(create_app(str(tmp_path / 'perf.sqlite'), SAMPLE)) as client:
        client.app.state.store.replace(data)
        token = client.post('/auth/login', json={'role': 'hr'}).json()['token']
        start = time.perf_counter()
        response = client.get('/hr/dashboard', headers={'Authorization': f'Bearer {token}'})
        elapsed = time.perf_counter() - start
        assert response.status_code == 200
        assert response.json()['total_employees'] == 200
        assert elapsed < 2, f'HR dashboard took {elapsed:.2f}s'
        print(f'200-employee HR dashboard: {elapsed:.3f}s')
