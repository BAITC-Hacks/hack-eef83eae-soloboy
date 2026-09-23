"""Reproducible synthetic fixtures, never presented as the hackathon dataset."""
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
target = Path(__file__).resolve().parents[1] / 'data/sample'
target.mkdir(parents=True, exist_ok=True)
definitions = [('PYTHON', 'Python', 'hard', ['Backend Engineer'], 2, 3, 4),
               ('SYSTEM_DESIGN', 'System Design', 'hard', ['Backend Engineer'], 1, 2, 4),
               ('SQL', 'SQL & Data Modeling', 'hard', ['Backend Engineer', 'Data Analyst'], 2, 3, 4),
               ('ANALYTICS', 'Data Analysis', 'hard', ['Data Analyst'], 2, 3, 5),
               ('PRODUCT', 'Product Discovery', 'hard', ['Product Manager'], 1, 3, 4),
               ('STRATEGY', 'Product Strategy', 'hard', ['Product Manager'], 1, 2, 4),
               ('PUBLIC_SPEAKING', 'Public Speaking', 'soft', [], 1, 2, 3),
               ('LEADERSHIP', 'Leadership', 'soft', [], 1, 2, 3),
               ('COLLABORATION', 'Collaboration', 'soft', [], 2, 3, 4),
               ('SECURITY', 'Security Awareness', 'hard', [], 2, 3, 4),
               ('CLOUD', 'Cloud Architecture', 'hard', ['Backend Engineer'], 1, 2, 4),
               ('VISUALIZATION', 'Data Visualization', 'hard', ['Data Analyst'], 2, 3, 4)]
skills = [{'skill_id': 'SK_' + key, 'name': name, 'category': category, 'roles': roles,
           'requirements': {'Junior': junior, 'Middle': middle, 'Senior': senior},
           'importance': 2 if key in ('SYSTEM_DESIGN', 'ANALYTICS', 'STRATEGY') else 1}
          for key, name, category, roles, junior, middle, senior in definitions]
events = []
for i, skill in enumerate(skills):
    for j, kind in enumerate(['workshop', 'mentoring']):
        events.append({'event_id': f'EV{i * 2 + j + 1:03}', 'name': skill['name'] + (' Workshop' if j == 0 else ' Practice Lab'),
                       'type': kind, 'audience': skill['roles'],
                       'skills': [{'skill_id': skill['skill_id'], 'gain': 1, 'max_level': 4 if j == 0 else 5}],
                       'description': f"Build {skill['name'].lower()} through guided exercises and practical workplace scenarios."})
names = ['Aigerim Sadykova', 'Daniyar Karimov', 'Amina Nur', 'Timur Saken', 'Dana Omarova', 'Alikhan Bek',
         'Madina Zhan', 'Arman Toleu', 'Asel Murat', 'Nursultan Ali', 'Kamila Serik', 'Dias Askar']
employees = []
for i, name in enumerate(names):
    role = ['Backend Engineer', 'Data Analyst', 'Product Manager'][i % 3]
    grade = ['Middle', 'Junior', 'Senior'][i % 3 if i > 2 else 0]
    employees.append({'employee_id': f'E{i + 1:04}', 'name': name, 'role': role, 'grade': grade,
                      'tenure_months': random.randint(8, 70),
                      'skills': {s['skill_id']: random.randint(1, 3) for s in skills if not s['roles'] or role in s['roles']}})
employees[0]['skills'].update(SK_PYTHON=3, SK_SYSTEM_DESIGN=2, SK_PUBLIC_SPEAKING=1)
history = []
for employee in employees:
    choices = [e for e in events if not e['audience'] or employee['role'] in e['audience']]
    for _ in range(10):
        event = random.choice(choices)
        # Keep the first employee's system design options open for the demo.
        if employee == employees[0] and event['event_id'] in ('EV003', 'EV004'):
            continue
        history.append({'employee_id': employee['employee_id'], 'event_id': event['event_id'],
                        'date': (date.today() - timedelta(days=random.randint(1, 730))).isoformat(),
                        'status': random.choice(['completed', 'completed', 'skipped', 'rejected'])})
for days in [8, 30, 60]:
    history.append({'employee_id': employees[0]['employee_id'], 'event_id': 'EV013',
                    'date': (date.today() - timedelta(days=days)).isoformat(), 'status': 'skipped'})
for name, records in [('employees', employees), ('events', events), ('skills', skills)]:
    (target / f'{name}.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
with (target / 'activity_history.csv').open('w', newline='', encoding='utf-8') as output:
    writer = csv.DictWriter(output, fieldnames=['employee_id', 'event_id', 'date', 'status'])
    writer.writeheader()
    writer.writerows(history)
print(f'Synthetic sample written to {target}')
