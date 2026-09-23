from datetime import date
from math import exp, log


def history_factor(employee, event, data, today=None):
    today = today or date.today()
    ids = {s.skill_id for s in event.skills}
    events = {e.event_id: e for e in data.events}
    evidence, completed, skipped, rejected = [], 0, 0, 0
    for h in data.history:
        if h.employee_id != employee.employee_id:
            continue
        related = events[h.event_id]
        overlap = len(ids & {s.skill_id for s in related.skills}) / len(ids)
        if not overlap:
            continue
        decay = exp(-log(2) * max(0, (today - h.date).days) / 180)
        weight = overlap * decay
        value = {'completed': 1, 'skipped': -0.8, 'rejected': -0.6}[h.status]
        evidence.append((weight, value))
        completed += h.status == 'completed'
        skipped += h.status == 'skipped'
        rejected += h.status == 'rejected'
    score = 0.5 + 0.5 * sum(w * v for w, v in evidence) / (1 + sum(w for w, _ in evidence))
    note = (f'Related history: {completed} completed, {skipped} skipped, {rejected} rejected. '
            'Older activity has less influence (180-day half-life).') if evidence else 'No related history yet; a neutral history signal is used.'
    return score, note
