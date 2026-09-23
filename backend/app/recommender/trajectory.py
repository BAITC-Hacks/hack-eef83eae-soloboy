import os
from ..models import Dataset, Employee


def analyze(employee: Employee, data: Dataset):
    order = [g.strip() for g in os.getenv('GRADE_ORDER', 'Junior,Middle,Senior,Lead').split(',')]
    available = {g for s in data.skills if not s.roles or employee.role in s.roles for g in s.requirements}
    if employee.grade not in order:
        next_grade = None
    else:
        next_grade = next((g for g in order[order.index(employee.grade) + 1:] if g in available), None)
    target = next_grade or employee.grade
    rows = []
    for skill in data.skills:
        relevant = not skill.roles or employee.role in skill.roles
        required = skill.requirements.get(target, 0) if relevant else 0
        current = employee.skills.get(skill.skill_id, 0)
        if required or skill.skill_id in employee.skills:
            rows.append({'skill_id': skill.skill_id, 'name': skill.name, 'category': skill.category,
                         'current': current, 'required': required, 'gap': max(0, required - current),
                         'importance': skill.importance,
                         'current_grade_required': skill.requirements.get(employee.grade, 0) if relevant else 0})
    total = sum(r['required'] for r in rows)
    progress = round(100 * sum(min(r['current'], r['required']) for r in rows) / total, 1) if total else None
    return {'current_grade': employee.grade, 'next_grade': next_grade, 'target_grade': target,
            'progress': progress, 'skills': rows,
            'note': 'Skill readiness, not a promotion guarantee.' if next_grade else 'No next-grade mapping is available; showing current-grade requirements where defined.'}
