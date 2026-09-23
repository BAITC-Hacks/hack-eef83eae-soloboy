import asyncio
import os
from collections import Counter, defaultdict
from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from .data import Store, parse_dataset, FILES
from .auth import Login, create_session, demo_mode, principal, require_hr, require_employee
from .recommender.engine import recommend, eligible, weights
from .recommender.trajectory import analyze
from .ai.explanation_service import ExplanationService

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / '.env')


def create_app(db=None, dataset_dir=None):
    @asynccontextmanager
    async def lifespan(app):
        weights()
        app.state.store = Store(db or os.getenv('STATE_DB', str(ROOT / 'runtime/career_quest.sqlite')),
                               Path(dataset_dir or os.getenv('DATASET_DIR') or ROOT / 'data/sample'))
        app.state.sessions = {}
        app.state.explanations = ExplanationService()
        yield
        app.state.store.db.close()

    app = FastAPI(title='Career Quest', lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
                       allow_methods=['GET', 'POST', 'DELETE'], allow_headers=['Authorization', 'Content-Type'])

    def employee_data(request, employee_id):
        require_employee(request, employee_id)
        data = request.app.state.store.snapshot()
        employee = next((e for e in data.employees if e.employee_id == employee_id), None)
        if employee is None:
            raise HTTPException(404, 'Employee not found')
        return employee, data

    @app.get('/health')
    def health():
        return {'status': 'ok', 'demo_mode': demo_mode(), 'dataset_source': app.state.store.source}

    @app.get('/demo/employees')
    def demo_employees():
        if not demo_mode():
            raise HTTPException(403, 'Demo is disabled')
        return [{'employee_id': e.employee_id, 'name': e.name, 'role': e.role, 'grade': e.grade} for e in app.state.store.snapshot().employees]

    @app.post('/auth/login')
    def login(request: Request, body: Login):
        return create_session(request, body)

    @app.delete('/auth/session')
    def logout(request: Request):
        app.state.sessions.pop(request.headers.get('authorization', '').removeprefix('Bearer '), None)
        return {'ok': True}

    @app.get('/employees')
    def employees(request: Request):
        session = principal(request)
        return [e for e in app.state.store.snapshot().employees if session['role'] == 'hr' or e.employee_id == session['employee_id']]

    @app.get('/employees/{employee_id}')
    def profile(request: Request, employee_id: str):
        return employee_data(request, employee_id)[0]

    @app.get('/employees/{employee_id}/skills')
    def skills(request: Request, employee_id: str):
        return analyze(*employee_data(request, employee_id))['skills']

    @app.get('/employees/{employee_id}/trajectory')
    def trajectory(request: Request, employee_id: str):
        return analyze(*employee_data(request, employee_id))

    @app.get('/employees/{employee_id}/recommendations')
    async def recommendations(request: Request, employee_id: str):
        results = recommend(*employee_data(request, employee_id))
        explanations = await asyncio.gather(*(app.state.explanations.explain(r) for r in results))
        return [{**r, 'explanation': e['text'], 'explanation_source': e['source']} for r, e in zip(results, explanations)]

    @app.get('/employees/{employee_id}/history')
    def history(request: Request, employee_id: str):
        _, data = employee_data(request, employee_id)
        events = {e.event_id: e for e in data.events}
        return [{**h.model_dump(mode='json'), 'activity_name': events[h.event_id].name} for h in sorted(data.history, key=lambda h: h.date, reverse=True) if h.employee_id == employee_id]

    @app.get('/employees/{employee_id}/activities')
    def activities(request: Request, employee_id: str):
        employee, data = employee_data(request, employee_id)
        completed = {h.event_id for h in data.history if h.employee_id == employee_id and h.status == 'completed'}
        names = {s.skill_id: s.name for s in data.skills}
        return [{**e.model_dump(), 'completed': e.event_id in completed,
                 'skills': [{**s.model_dump(), 'name': names[s.skill_id]} for s in e.skills]} for e in data.events if eligible(employee, e)]

    @app.post('/employees/{employee_id}/activities/{event_id}/complete')
    def complete(request: Request, employee_id: str, event_id: str):
        require_employee(request, employee_id)
        try:
            return app.state.store.complete(employee_id, event_id)
        except KeyError:
            raise HTTPException(404, 'Employee or activity not found')
        except ValueError as error:
            raise HTTPException(422, str(error))

    @app.get('/hr/dashboard')
    def hr(request: Request):
        require_hr(request)
        data = app.state.store.snapshot()
        gaps, overview = Counter(), []
        history_by_employee, history_by_event = defaultdict(list), defaultdict(list)
        for record in data.history:
            history_by_employee[record.employee_id].append(record)
            history_by_event[record.event_id].append(record)
        for employee in data.employees:
            trajectory = analyze(employee, data)
            missing = sorted((s for s in trajectory['skills'] if s['gap']), key=lambda s: -s['gap'])
            gaps.update(s['name'] for s in missing)
            employee_history = history_by_employee[employee.employee_id]
            recs = recommend(employee, data.model_copy(update={'history': employee_history}))
            completed_dates = [h.date for h in employee_history if h.status == 'completed']
            last_completed = max(completed_dates, default=None)
            overview.append({'employee_id': employee.employee_id, 'name': employee.name, 'role': employee.role,
                             'grade': employee.grade, 'main_gap': missing[0]['name'] if missing else None,
                             'progress': trajectory['progress'], 'recommendation_count': len(recs),
                             'last_completed': last_completed.isoformat() if last_completed else None,
                             'active_development': last_completed is not None and last_completed >= date.today() - timedelta(days=90)})
        statuses = Counter(h.status for h in data.history)
        cutoff = date.today() - timedelta(days=90)
        active = {h.employee_id for h in data.history if h.status == 'completed' and h.date >= cutoff}
        participation = []
        for event in data.events:
            records = history_by_event[event.event_id]
            participation.append({'event_id': event.event_id, 'name': event.name, 'participants': len({h.employee_id for h in records}),
                                  'completed': sum(h.status == 'completed' for h in records),
                                  'skipped': sum(h.status == 'skipped' for h in records), 'rejected': sum(h.status == 'rejected' for h in records)})
        total = len(data.history)
        return {'total_employees': len(data.employees), 'active_development': len(active),
                'without_recommendations': sum(not e['recommendation_count'] for e in overview),
                'completion_rate': round(100 * statuses['completed'] / total, 1) if total else 0,
                'skip_rate': round(100 * statuses['skipped'] / total, 1) if total else 0,
                'history_count': total, 'skill_gaps': [{'name': k, 'employees': v} for k, v in gaps.most_common(8)],
                'participation': participation, 'employees': overview}

    @app.get('/dataset/status')
    def dataset_status(request: Request):
        require_hr(request)
        data = app.state.store.snapshot()
        return {'source': app.state.store.source, **{k: len(getattr(data, k)) for k in ('employees', 'events', 'skills', 'history')}}

    @app.post('/dataset/upload')
    async def upload(request: Request, files: list[UploadFile] = File(...)):
        require_hr(request)
        if len(files) != 4 or {f.filename for f in files} != set(FILES):
            raise HTTPException(422, 'Upload the four files with their exact names')
        payloads = {}
        for file in files:
            content = await file.read(10 * 1024 * 1024 + 1)
            if len(content) > 10 * 1024 * 1024:
                raise HTTPException(413, 'Each file must be under 10 MB')
            payloads[file.filename] = content
        try:
            data = parse_dataset(payloads)
        except (ValueError, UnicodeError, TypeError) as error:
            raise HTTPException(422, str(error))
        app.state.store.replace(data)
        app.state.explanations.cache.clear()
        # Retain HR sessions; employee identities must be reselected after a dataset replacement.
        app.state.sessions = {k: v for k, v in app.state.sessions.items() if v['role'] == 'hr'}
        return {'source': 'uploaded', **{k: len(getattr(data, k)) for k in ('employees', 'events', 'skills', 'history')}}

    @app.post('/dataset/profiles')
    async def add_profiles(request: Request, files: list[UploadFile] = File(...)):
        require_hr(request)
        if len(files) != 2 or {f.filename for f in files} != {'employees.json', 'activity_history.csv'}:
            raise HTTPException(422, 'Upload employees.json and activity_history.csv')
        payloads = {}
        for file in files:
            content = await file.read(10 * 1024 * 1024 + 1)
            if len(content) > 10 * 1024 * 1024:
                raise HTTPException(413, 'Each file must be under 10 MB')
            payloads[file.filename] = content
        try:
            data = app.state.store.import_profiles(payloads)
        except (ValueError, UnicodeError, TypeError) as error:
            raise HTTPException(422, str(error))
        app.state.explanations.cache.clear()
        return {'source': 'extended', **{k: len(getattr(data, k)) for k in ('employees', 'events', 'skills', 'history')}}

    dist = ROOT / 'frontend/dist'
    if dist.exists():
        app.mount('/assets', StaticFiles(directory=dist / 'assets'), name='assets')

        @app.get('/{path:path}', include_in_schema=False)
        def frontend(path: str):
            if path.split('/')[0] not in ('', 'login', 'dashboard', 'employee', 'hr', 'dataset'):
                raise HTTPException(404, 'Not found')
            return FileResponse(dist / 'index.html')
    return app


app = create_app()
