import json
import os
import math
from .trajectory import analyze
from .history import history_factor

DEFAULT_WEIGHTS = {'skill_gap': .30, 'grade_importance': .25, 'activity_relevance': .20, 'history': .15, 'career_trajectory': .10}


def weights():
    values = json.loads(os.getenv('RECOMMENDATION_WEIGHTS', 'null'))
    if values is None:
        values = DEFAULT_WEIGHTS
    if not isinstance(values, dict) or set(values) != set(DEFAULT_WEIGHTS) or any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in values.values()) or not math.isfinite(sum(values.values())) or sum(values.values()) <= 0:
        raise ValueError('Recommendation weights must specify all five nonnegative factors with a positive sum')
    return {k: v / sum(values.values()) for k, v in values.items()}


def eligible(employee, event):
    audience = [event.audience] if isinstance(event.audience, str) else event.audience
    return not audience or any(a.casefold() in {'all', '*', 'all employees', employee.role.casefold(), employee.grade.casefold()} for a in audience)


def candidates(employee, data, trajectory):
    completed = {h.event_id for h in data.history if h.employee_id == employee.employee_id and h.status == 'completed'}
    rows = {r['skill_id']: r for r in trajectory['skills']}
    for event in data.events:
        if event.event_id in completed or not eligible(employee, event):
            continue
        effects = []
        for effect in event.skills:
            row = rows.get(effect.skill_id)
            if not row:
                continue
            gain = max(0, min(effect.gain, effect.max_level - row['current']))
            if gain:
                effects.append({**row, 'gain': gain, 'max_level': effect.max_level,
                                'gap_closed': min(gain, row['gap'])})
        if any(e['gap_closed'] for e in effects):
            yield event, effects


def score_candidate(employee, event, effects, data, trajectory, config):
    useful = [e for e in effects if e['gap_closed'] > 0]
    importance_total = sum(r['importance'] for r in trajectory['skills'] if r['gap']) or 1
    history, history_note = history_factor(employee, event, data)
    factors = {
        'skill_gap': sum(e['gap'] / max(e['required'], 1) for e in useful) / len(useful),
        'grade_importance': min(1, sum(e['importance'] for e in useful) / importance_total * 2),
        'activity_relevance': sum(e['gap_closed'] for e in useful) / sum(s.gain for s in event.skills),
        'history': history,
        'career_trajectory': sum(e['gap_closed'] / max(e['gap'], 1) * (1 if e['required'] > e['current_grade_required'] else .6) for e in useful) / len(useful),
    }
    score = sum(config[k] * v for k, v in factors.items())
    reasoning = {
        'grade_requirement': f"Target: {trajectory['target_grade']} {employee.role}. " + '; '.join(f"{e['name']} requires level {e['required']}" for e in useful) + '.',
        'skill_gap': '; '.join(f"{e['name']}: {e['current']}/{e['required']} (gap {e['gap']})" for e in useful) + '.',
        'history': history_note,
        'career_trajectory': f"This activity closes {sum(e['gap_closed'] for e in useful)} required skill level(s) toward {trajectory['target_grade']} readiness.",
        'activity_effect': '; '.join(f"{e['name']} +{e['gain']}, capped at level {e['max_level']}" for e in effects) + '.',
    }
    return {'activity_id': event.event_id, 'activity_name': event.name, 'type': event.type,
            'description': event.description, 'score': round(score, 4), 'factors': factors,
            'weights': config, 'reasoning': reasoning, 'skills': effects}


def recommend(employee, data, limit=3):
    # Filter once; scoring each candidate must not rescan the organization's history.
    data = data.model_copy(update={'history': [h for h in data.history if h.employee_id == employee.employee_id]})
    trajectory = analyze(employee, data)
    config = weights()
    scored = [score_candidate(employee, event, effects, data, trajectory, config)
              for event, effects in candidates(employee, data, trajectory)]
    return sorted(scored, key=lambda r: (-r['score'], r['activity_id']))[:limit]
