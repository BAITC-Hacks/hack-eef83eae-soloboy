import json
import os
import secrets
import time
from pathlib import Path
from fastapi import HTTPException, Request
from pydantic import BaseModel


def demo_mode():
    return os.getenv('DEMO_MODE', 'true').lower() == 'true'


class Login(BaseModel):
    role: str
    employee_id: str | None = None
    access_key: str = ''


def create_session(request: Request, body: Login):
    if body.role not in ('hr', 'employee'):
        raise HTTPException(422, 'Choose employee or hr')
    if not demo_mode():
        if body.role == 'hr':
            expected = os.getenv('HR_ACCESS_KEY', '')
        else:
            path = os.getenv('EMPLOYEE_CREDENTIALS_FILE', '')
            try:
                credentials = json.loads(Path(path).read_text(encoding='utf-8')) if path else {}
                if not isinstance(credentials, dict):
                    raise ValueError('Invalid credential configuration')
                expected = credentials.get(body.employee_id, '')
            except (OSError, ValueError):
                raise HTTPException(503, 'Employee sign-in is not configured correctly')
        if not isinstance(expected, str) or not expected or not secrets.compare_digest(expected.encode('utf-8'), body.access_key.encode('utf-8')):
            raise HTTPException(401, 'Invalid credentials')
    if body.role == 'employee' and not any(e.employee_id == body.employee_id for e in request.app.state.store.snapshot().employees):
        raise HTTPException(404, 'Employee not found')
    sessions = request.app.state.sessions
    for key in list(sessions):
        if sessions[key]['expires'] < time.time():
            del sessions[key]
    token = secrets.token_urlsafe(32)
    session = {'role': body.role, 'employee_id': body.employee_id if body.role == 'employee' else None, 'expires': time.time() + 8 * 3600}
    sessions[token] = session
    return {'token': token, **session}


def principal(request: Request):
    token = request.headers.get('authorization', '').removeprefix('Bearer ')
    session = request.app.state.sessions.get(token)
    if not session or session['expires'] < time.time():
        raise HTTPException(401, 'Please sign in')
    return session


def require_hr(request: Request):
    session = principal(request)
    if session['role'] != 'hr':
        raise HTTPException(403, 'HR access required')
    return session


def require_employee(request: Request, employee_id: str):
    session = principal(request)
    if session['role'] != 'hr' and session['employee_id'] != employee_id:
        raise HTTPException(403, 'You can only access your own profile')
    return session
