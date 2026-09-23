export type Employee = {
  employee_id: string;
  name?: string;
  role: string;
  grade: string;
  tenure_months: number;
  skills: Record<string, number>;
};
export type Skill = {
  skill_id: string;
  name: string;
  category: string;
  current: number;
  required: number;
  gap: number;
  gain?: number;
  max_level?: number;
};
export type Trajectory = {
  current_grade: string;
  next_grade: string | null;
  target_grade: string;
  progress: number | null;
  skills: Skill[];
  note: string;
};
export type Recommendation = {
  activity_id: string;
  activity_name: string;
  type: string;
  description: string;
  score: number;
  reasoning: Record<string, string>;
  explanation: string;
  explanation_source: string;
  skills: Skill[];
  factors: Record<string, number>;
};
export type Activity = {
  event_id: string;
  name: string;
  type: string;
  description: string;
  completed: boolean;
  skills: { skill_id: string; name: string; gain: number; max_level: number }[];
};
export type History = {
  event_id: string;
  activity_name: string;
  date: string;
  status: string;
};
export type Session = {
  token: string;
  role: string;
  employee_id: string | null;
};
export type Dataset = {
  source: string;
  employees: number;
  events: number;
  skills: number;
  history: number;
};
export type HR = {
  total_employees: number;
  active_development: number;
  without_recommendations: number;
  completion_rate: number;
  skip_rate: number;
  history_count: number;
  skill_gaps: { name: string; employees: number }[];
  participation: {
    event_id: string;
    name: string;
    participants: number;
    completed: number;
    skipped: number;
    rejected: number;
  }[];
  employees: {
    employee_id: string;
    name?: string;
    role: string;
    grade: string;
    main_gap: string | null;
    progress: number | null;
    recommendation_count: number;
    last_completed: string | null;
    active_development: boolean;
  }[];
};
const base =
  (import.meta as unknown as { env: Record<string, string> }).env
    .VITE_API_URL || "";
export function readSession(): Session | null {
  try {
    return JSON.parse(sessionStorage.getItem("cq-session") || "null");
  } catch {
    return null;
  }
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const session = readSession();
  const response = await fetch(base + path, {
    ...options,
    headers: {
      ...(session ? { Authorization: `Bearer ${session.token}` } : {}),
      ...(options.body && !(options.body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => ({ detail: response.statusText }));
    if (response.status === 401 && session) {
      sessionStorage.removeItem("cq-session");
      window.dispatchEvent(new Event("session-expired"));
    }
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : JSON.stringify(body.detail),
    );
  }
  return response.json();
}
