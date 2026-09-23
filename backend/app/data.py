import csv
import io
import json
import sqlite3
import threading
from pathlib import Path
from datetime import date
from .models import Dataset, Employee, History

FILES = ('employees.json', 'events.json', 'skills.json', 'activity_history.csv')


def parse_json_records(content: bytes, key: str):
    payload = json.loads(content.decode('utf-8-sig'))
    records = payload.get(key) if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ValueError(f'{key}.json must contain an array of records')
    return records


def parse_history(content: bytes):
    reader = csv.DictReader(io.StringIO(content.decode('utf-8-sig')), strict=True)
    fields = reader.fieldnames or []
    if not {'employee_id', 'event_id', 'date', 'status'} <= set(fields) or len(fields) != len(set(fields)):
        raise ValueError('History CSV needs unique employee_id,event_id,date,status columns')
    try:
        records = list(reader)
    except csv.Error as error:
        raise ValueError(f'Invalid history CSV: {error}') from error
    if any(None in row or any(value is None for value in row.values()) for row in records):
        raise ValueError('History CSV rows must have the same number of fields as the header')
    return records


def parse_dataset(files: dict[str, bytes]) -> Dataset:
    if set(files) != set(FILES):
        raise ValueError('Provide exactly employees.json, events.json, skills.json and activity_history.csv')
    result = {}
    for name in FILES[:3]:
        key = name.removesuffix('.json')
        result[key] = parse_json_records(files[name], key)
    result['history'] = parse_history(files[FILES[3]])
    return Dataset.model_validate(result)


class Store:
    """One transactional snapshot; lock protects read-modify-write across requests."""
    def __init__(self, db: str, dataset_dir: Path):
        Path(db).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(db, check_same_thread=False)
        self.db.execute('CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL, source TEXT NOT NULL)')
        row = self.db.execute('SELECT payload, source FROM state WHERE id=1').fetchone()
        if row:
            self.dataset, self.source = Dataset.model_validate_json(row[0]), row[1]
        else:
            self.replace(parse_dataset({n: (dataset_dir / n).read_bytes() for n in FILES}),
                         'sample' if dataset_dir.name == 'sample' else 'configured')

    def replace(self, dataset: Dataset, source='uploaded'):
        with self.lock:
            # Publish memory only after SQLite has committed successfully.
            with self.db:
                self.db.execute('INSERT OR REPLACE INTO state VALUES (1, ?, ?)', (dataset.model_dump_json(), source))
            self.dataset, self.source = dataset, source

    def import_profiles(self, files: dict[str, bytes]):
        if set(files) != {'employees.json', 'activity_history.csv'}:
            raise ValueError('Provide employees.json and activity_history.csv for additional profiles')
        employees = [Employee.model_validate(e) for e in parse_json_records(files['employees.json'], 'employees')]
        history = [History.model_validate(h) for h in parse_history(files['activity_history.csv'])]
        ids = {e.employee_id for e in employees}
        if not employees or len(ids) != len(employees):
            raise ValueError('Provide at least one profile with unique employee IDs')
        if any(h.employee_id not in ids for h in history):
            raise ValueError('Additional history must belong to the supplied profiles')
        with self.lock:
            data = self.snapshot()
            if ids & {e.employee_id for e in data.employees}:
                raise ValueError('Employee IDs already exist; use new IDs or replace the full dataset')
            merged = Dataset.model_validate({**data.model_dump(),
                'employees': [*data.employees, *employees], 'history': [*data.history, *history]})
            self.replace(merged, 'extended')
            return merged

    def snapshot(self):
        with self.lock:
            return self.dataset.model_copy(deep=True)

    def complete(self, employee_id: str, event_id: str):
        from .recommender.engine import eligible
        with self.lock:
            data = self.snapshot()
            employee = next((e for e in data.employees if e.employee_id == employee_id), None)
            event = next((e for e in data.events if e.event_id == event_id), None)
            if employee is None or event is None:
                raise KeyError('Employee or activity not found')
            if not eligible(employee, event):
                raise ValueError('This activity is not available for this role or grade')
            if any(h.employee_id == employee_id and h.event_id == event_id and h.status == 'completed' for h in data.history):
                return {'already_completed': True, 'changes': []}
            changes = []
            for effect in event.skills:
                before = employee.skills.get(effect.skill_id, 0)
                after = max(before, min(before + effect.gain, effect.max_level))
                employee.skills[effect.skill_id] = after
                changes.append({'skill_id': effect.skill_id, 'before': before, 'after': after})
            data.history.append(History(employee_id=employee_id, event_id=event_id, date=date.today(), status='completed'))
            self.replace(data, self.source)
            return {'already_completed': False, 'changes': changes}
