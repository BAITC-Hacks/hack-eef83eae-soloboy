"""Three additional synthetic profiles; no official starter-kit data is used."""
import csv
import json
from datetime import date, timedelta
from pathlib import Path

root = Path(__file__).resolve().parents[1]
skills = json.loads((root / 'data/sample/skills.json').read_text(encoding='utf-8'))
profiles = []
for employee_id, role, gaps in [
    ('JURY-DESIGN', 'Backend Engineer', {'SK_SYSTEM_DESIGN': 2, 'SK_PUBLIC_SPEAKING': 1}),
    ('JURY-CLOUD', 'Backend Engineer', {'SK_CLOUD': 1}),
    ('JURY-ANALYTICS', 'Data Analyst', {'SK_ANALYTICS': 2, 'SK_PUBLIC_SPEAKING': 1}),
]:
    levels = {s['skill_id']: s['requirements']['Senior'] for s in skills if not s['roles'] or role in s['roles']}
    levels.update(gaps)
    profiles.append({'employee_id': employee_id, 'role': role, 'grade': 'Middle', 'tenure_months': 30, 'skills': levels})
folder = root / 'data/jury-example'
folder.mkdir(parents=True, exist_ok=True)
(folder / 'employees.json').write_text(json.dumps(profiles, indent=2), encoding='utf-8')
with (folder / 'activity_history.csv').open('w', newline='', encoding='utf-8') as output:
    writer = csv.DictWriter(output, fieldnames=['employee_id', 'event_id', 'date', 'status'])
    writer.writeheader()
    for employee_id in ('JURY-DESIGN', 'JURY-ANALYTICS'):
        for days in (7, 20, 45):
            writer.writerow({'employee_id': employee_id, 'event_id': 'EV013', 'date': (date.today() - timedelta(days=days)).isoformat(), 'status': 'skipped'})
    writer.writerow({'employee_id': 'JURY-ANALYTICS', 'event_id': 'EV007', 'date': (date.today() - timedelta(days=10)).isoformat(), 'status': 'completed'})
print('Created three synthetic jury examples using the sample catalog.')
