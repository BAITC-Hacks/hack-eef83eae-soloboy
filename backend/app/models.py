"""Validated interchange schema. Unknown metadata is preserved on import."""
from datetime import date
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Level = Annotated[int, Field(strict=True, ge=0, le=5)]
Identifier = Annotated[str, Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9_.-]+$')]


class Record(BaseModel):
    model_config = ConfigDict(extra='allow')


class Employee(Record):
    employee_id: Identifier
    name: str | None = None
    role: str = Field(min_length=1)
    grade: str = Field(min_length=1)
    tenure_months: int = Field(ge=0)
    skills: dict[str, Level]


class Effect(Record):
    skill_id: Identifier
    gain: int = Field(strict=True, ge=1, le=5)
    max_level: Level


class Event(Record):
    event_id: Identifier
    name: str = Field(min_length=1)
    type: str = 'training'
    audience: list[str] | str = Field(default_factory=list)
    skills: list[Effect] = Field(min_length=1)
    description: str = ''

    @model_validator(mode='after')
    def unique_skills(self):
        if len({s.skill_id for s in self.skills}) != len(self.skills):
            raise ValueError('An activity must not repeat a skill')
        return self


class Skill(Record):
    skill_id: Identifier
    name: str = Field(min_length=1)
    category: str
    requirements: dict[str, Level]
    roles: list[str] = Field(default_factory=list)
    importance: float = Field(default=1, gt=0, le=5)


class History(Record):
    employee_id: Identifier
    event_id: Identifier
    date: date
    status: Literal['completed', 'skipped', 'rejected']


class Dataset(BaseModel):
    employees: list[Employee] = Field(min_length=1)
    events: list[Event] = Field(min_length=1)
    skills: list[Skill] = Field(min_length=1)
    history: list[History]

    @model_validator(mode='after')
    def references(self):
        for records, key in [(self.employees, 'employee_id'), (self.events, 'event_id'), (self.skills, 'skill_id')]:
            ids = [getattr(r, key) for r in records]
            if len(ids) != len(set(ids)):
                raise ValueError(f'Duplicate {key}')
        employees = {e.employee_id for e in self.employees}
        events = {e.event_id for e in self.events}
        skills = {s.skill_id for s in self.skills}
        for e in self.employees:
            if set(e.skills) - skills:
                raise ValueError(f'Unknown skill on employee {e.employee_id}')
        for event in self.events:
            if {s.skill_id for s in event.skills} - skills:
                raise ValueError(f'Unknown skill on activity {event.event_id}')
        for h in self.history:
            if h.employee_id not in employees or h.event_id not in events:
                raise ValueError('History references an unknown employee or activity')
            if h.date > date.today():
                raise ValueError('History cannot contain future dates')
        return self
