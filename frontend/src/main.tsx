import React, { useEffect, useState, type ReactNode } from "react";
import ReactDOM from "react-dom/client";
import {
  BrowserRouter,
  Link,
  NavLink,
  Navigate,
  Route,
  Routes,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronRight,
  Compass,
  Database,
  LayoutDashboard,
  LogOut,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  Users,
  Upload,
  Layers,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import {
  api,
  readSession,
  type Employee,
  type Trajectory,
  type Recommendation,
  type Activity,
  type History,
  type Session,
  type Dataset,
  type HR,
} from "./api";
import "./style.css";

function useLoad<T>(load: () => Promise<T>, deps: unknown[]) {
  const key = JSON.stringify(deps);
  const [result, setResult] = useState<{ key: string; value: T }>();
  const [error, setError] = useState("");
  useEffect(() => {
    let alive = true;
    setError("");
    load()
      .then((value) => {
        if (alive) setResult({ key, value });
      })
      .catch((e) => {
        if (alive) setError(e.message);
      });
    return () => {
      alive = false;
    };
  }, deps);
  return { data: result?.key === key ? result.value : undefined, error };
}
function Alert({ children }: { children: ReactNode }) {
  return (
    <div className="alert" role="alert">
      {children}
    </div>
  );
}
function Loading() {
  return (
    <div className="loading" role="status">
      <Compass size={30} />
      <p>Preparing your workspace…</p>
    </div>
  );
}
function Brand() {
  return (
    <Link to="/" className="brand">
      <span className="brand-icon">
        <Compass size={24} />
      </span>
      <span>
        Career Quest<small>AI NAVIGATOR</small>
      </span>
    </Link>
  );
}
function Progress({ value }: { value: number | null }) {
  return (
    <div
      className="progress"
      role="progressbar"
      aria-label="Skill readiness"
      aria-valuenow={value ?? 0}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <span style={{ width: `${value ?? 0}%` }} />
    </div>
  );
}
function Stat({
  label,
  value,
  note,
  icon,
}: {
  label: string;
  value: ReactNode;
  note: string;
  icon: ReactNode;
}) {
  return (
    <div className="stat card">
      <div className="stat-label">
        {label}
        {icon}
      </div>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

function Landing() {
  return (
    <div className="landing">
      <header>
        <Brand />
        <Link className="button secondary" to="/login">
          Sign in <ArrowUpRight size={16} />
        </Link>
      </header>
      <main>
        <div className="eyebrow">
          <span className="dot" /> HALYK BANK · EMPLOYEE DEVELOPMENT
        </div>
        <h1>
          Your next chapter.
          <br />
          <em>A clearer path.</em>
        </h1>
        <p className="hero-copy">
          AI-powered career development navigation.
          <br />
          Understand where you are. See where you can go.
          <br />
          Know what to do next.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link className="button" to="/login">
            Try Demo <ArrowRight size={18} />
          </Link>
          <Link className="button secondary" to="/login?role=hr">
            HR Dashboard <Users size={18} />
          </Link>
        </div>
        <div className="hero-note">
          <ShieldCheck size={16} /> Explainable recommendations. Your
          development, your pace.
        </div>
        <section className="how">
          <div className="section-heading">
            <h2>A little direction goes a long way.</h2>
            <span className="eyebrow">HOW IT WORKS</span>
          </div>
          <div className="steps">
            {[
              [
                "Understand profile",
                "Start with your skills, experience, and development history.",
              ],
              [
                "Analyze skill gaps",
                "See what the next career level actually requires.",
              ],
              [
                "Recommend next step",
                "Find an activity that fits your goals and learning history.",
              ],
              [
                "Track progress",
                "Complete an activity and watch your skill readiness grow.",
              ],
            ].map(([title, text], i) => (
              <div key={title}>
                <span className="step-number">0{i + 1}</span>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
            ))}
          </div>
        </section>
      </main>
      <footer>
        Career Quest{" "}
        <span>AI Navigator for Employee Development · HackAlem</span>
      </footer>
    </div>
  );
}

function Login({ onLogin }: { onLogin: (s: Session) => void }) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [role, setRole] = useState(
    params.get("role") === "hr" ? "hr" : "employee",
  );
  const { data: health, error } = useLoad(
    () => api<{ demo_mode: boolean; dataset_source: string }>("/health"),
    [],
  );
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [id, setId] = useState("");
  const [key, setKey] = useState("");
  const [failure, setFailure] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (health?.demo_mode)
      api<Employee[]>("/demo/employees")
        .then((e) => {
          setEmployees(e);
          setId(e[0]?.employee_id || "");
        })
        .catch((e) => setFailure(e.message));
  }, [health]);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setFailure("");
    try {
      const session = await api<Session>("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          role,
          employee_id: id || null,
          access_key: key,
        }),
      });
      onLogin(session);
      navigate(role === "hr" ? "/hr" : `/employee/${id}`);
    } catch (e) {
      setFailure((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="login-page">
      <Brand />
      <form className="card login-card" onSubmit={submit}>
        <span className="eyebrow">YOUR DEVELOPMENT WORKSPACE</span>
        <h1>
          {health?.demo_mode ? "Explore your next step." : "Welcome back."}
        </h1>
        <p className="muted">
          {health?.demo_mode
            ? `Demo mode · ${health.dataset_source === "sample" ? "synthetic sample data" : "loaded dataset"}. Choose a perspective to begin.`
            : "Enter your provisioned access credentials."}
        </p>
        <div className="segmented">
          <button
            type="button"
            className={role === "employee" ? "selected" : ""}
            onClick={() => setRole("employee")}
          >
            Employee
          </button>
          <button
            type="button"
            className={role === "hr" ? "selected" : ""}
            onClick={() => setRole("hr")}
          >
            HR workspace
          </button>
        </div>
        {role === "employee" && health && (
          <label>
            Employee
            {health?.demo_mode ? (
              <select aria-label="Employee" value={id} onChange={(e) => setId(e.target.value)}>
                {employees.map((e) => (
                  <option key={e.employee_id} value={e.employee_id}>
                    {e.name || e.employee_id} · {e.role} · {e.grade}
                  </option>
                ))}
              </select>
            ) : (
              <input
                required
                value={id}
                onChange={(e) => setId(e.target.value)}
                placeholder="Employee ID"
              />
            )}
          </label>
        )}
        {health && !health.demo_mode && (
          <label>
            Access key
            <input
              required
              type="password"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              autoComplete="current-password"
            />
          </label>
        )}
        {(failure || error) && <Alert>{failure || error}</Alert>}
        <button
          className="button full"
          disabled={busy || !health || (role === "employee" && !id)}
        >
          {busy ? "Opening workspace…" : "Open workspace"}
          <ArrowRight size={18} />
        </button>
        <small className="muted">
          {health?.demo_mode
            ? "Demo selection is intentionally open for the jury. Production mode requires credentials."
            : "Employee profiles are private. HR access is role restricted."}
        </small>
      </form>
    </div>
  );
}

function Shell({
  session,
  logout,
  children,
}: {
  session: Session;
  logout: () => void;
  children: ReactNode;
}) {
  const path = `/employee/${session.employee_id}`;
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Brand />
        <div className="workspace-label">
          {session.role === "hr" ? "PEOPLE & DEVELOPMENT" : "MY WORKSPACE"}
        </div>
        <nav>
          {session.role === "employee" ? (
            <>
              <NavLink end to={path}>
                <LayoutDashboard size={19} /> Overview
              </NavLink>
              <NavLink to={`${path}/trajectory`}>
                <TrendingUp size={19} /> Career trajectory
              </NavLink>
              <NavLink to={`${path}/activities`}>
                <BookOpen size={19} /> Activity library
              </NavLink>
            </>
          ) : (
            <>
              <NavLink to="/hr">
                <Users size={19} /> HR overview
              </NavLink>
              <NavLink to="/dataset">
                <Database size={19} /> Dataset manager
              </NavLink>
            </>
          )}
        </nav>
        <div className="sidebar-note">
          <Sparkles size={20} />
          <h3>Growth with direction.</h3>
          <p>Small, meaningful steps toward your next chapter.</p>
        </div>
        <button className="signout" onClick={logout}>
          <LogOut size={17} /> Switch workspace / sign out
        </button>
        <div className="sidebar-bottom">
          <span className="avatar">{session.role === "hr" ? "HR" : "CQ"}</span>
          <div>
            {session.role === "hr" ? "HR workspace" : session.employee_id}
            <small>Career Quest</small>
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span>
            Workspace <ChevronRight size={14} />{" "}
            <strong>
              {session.role === "hr"
                ? "People & development"
                : "Personal development"}
            </strong>
          </span>
          <span className="privacy">
            <ShieldCheck size={15} /> Private workspace
          </span>
        </header>
        <main className="page">{children}</main>
        <footer className="workspace-footer">
          Career Quest <span>Every next step starts with clarity.</span>
        </footer>
      </div>
    </div>
  );
}

function RecommendationCard({
  rec,
  id,
  index,
}: {
  rec: Recommendation;
  id: string;
  index: number;
}) {
  return (
    <article
      className={`recommendation card ${index === 0 ? "primary-rec" : ""}`}
    >
      <div className="flex justify-between items-center">
        <span className="pill">
          {index === 0 ? (
            <>
              <Sparkles size={13} /> NEXT BEST STEP
            </>
          ) : (
            `RECOMMENDATION 0${index + 1}`
          )}
        </span>
        <span className="match">{Math.round(rec.score * 100)}% match</span>
      </div>
      <div className="activity-icon">
        <Layers size={23} />
      </div>
      <span className="eyebrow">{rec.type}</span>
      <h3>{rec.activity_name}</h3>
      <p>{rec.description}</p>
      <p className="rec-summary">{rec.reasoning.career_trajectory}</p>
      <div className="skill-chips">
        {rec.skills.map((s) => (
          <span key={s.skill_id}>
            {s.name} <b>+{s.gain}</b>
            <small>
              {s.current} → {s.current + (s.gain || 0)} · target{" "}
              {s.required || "—"}
            </small>
          </span>
        ))}
      </div>
      <details>
        <summary>Why this recommendation?</summary>
        <ul>
          {Object.values(rec.reasoning).map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ul>
        <small>Match is a weighted fit score, not a probability.</small>
      </details>
      <Link
        className={`button ${index ? "secondary" : ""}`}
        to={`/employee/${id}/activity/${rec.activity_id}`}
      >
        View Details <ArrowUpRight size={17} />
      </Link>
    </article>
  );
}

function EmployeePage({ mode = "overview" }: { mode?: string }) {
  const { id = "" } = useParams();
  const { data, error } = useLoad(async () => {
    const [employee, trajectory, recommendations, history, activities] =
      await Promise.all([
        api<Employee>(`/employees/${id}`),
        api<Trajectory>(`/employees/${id}/trajectory`),
        api<Recommendation[]>(`/employees/${id}/recommendations`),
        api<History[]>(`/employees/${id}/history`),
        api<Activity[]>(`/employees/${id}/activities`),
      ]);
    return { employee, trajectory, recommendations, history, activities };
  }, [id, mode]);
  if (error) return <Alert>{error}</Alert>;
  if (!data) return <Loading />;
  const { employee, trajectory, recommendations, history, activities } = data;
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">YOUR CAREER, IN FOCUS</div>
          <h1>
            {mode === "trajectory"
              ? "See the path ahead."
              : mode === "activities"
                ? "Make room for growth."
                : `Hello, ${employee.name?.split(" ")[0] || employee.employee_id}.`}
          </h1>
          <p>A clear view of where you are, and what comes next.</p>
        </div>
        <div className="profile-tag">
          <span className="avatar">
            {(employee.name || employee.employee_id).slice(0, 2).toUpperCase()}
          </span>
          <div>
            {employee.name || employee.employee_id}
            <small>
              {employee.grade} {employee.role} · {employee.tenure_months} months
            </small>
          </div>
        </div>
      </div>
      <div className="stats-grid">
        <Stat
          label="Career readiness"
          value={`${trajectory.progress ?? "—"}${trajectory.progress === null ? "" : "%"}`}
          note={`Toward ${trajectory.target_grade}`}
          icon={<TrendingUp size={18} />}
        />
        <Stat
          label="Skills to develop"
          value={trajectory.skills.filter((s) => s.gap > 0).length}
          note="Based on grade requirements"
          icon={<Target size={18} />}
        />
        <Stat
          label="Activities completed"
          value={history.filter((h) => h.status === "completed").length}
          note="Recorded development history"
          icon={<CheckCircle2 size={18} />}
        />
        <Stat
          label="Your next steps"
          value={recommendations.length}
          note="Personalized recommendations"
          icon={<Compass size={18} />}
        />
      </div>
      {mode === "overview" && (
        <>
          <div className="section-heading">
            <div>
              <h2>
                <Sparkles size={21} /> Recommended for you
              </h2>
              <p>
                Built around your skills, career path, and learning history.
              </p>
            </div>
            <span className="pill neutral">EXPLAINABLE AI</span>
          </div>
          {recommendations.length ? (
            <div className="recommendations">
              {recommendations.map((rec, i) => (
                <RecommendationCard
                  key={rec.activity_id}
                  rec={rec}
                  id={id}
                  index={i}
                />
              ))}
            </div>
          ) : (
            <div className="card empty">
              <CheckCircle2 />
              <h3>No suitable next activity in this dataset.</h3>
              <p>
                You may have met the defined requirements or completed the
                available activities. HR can add more options.
              </p>
            </div>
          )}
        </>
      )}
      {mode !== "activities" && (
        <div className="lower-grid">
          <section className="card skills-panel">
            <div className="section-heading">
              <h2>Skill snapshot</h2>
              <span className="muted">Current / target</span>
            </div>
            {trajectory.skills.map((skill) => (
              <div className="skill-row" key={skill.skill_id}>
                <div>
                  <span>
                    {skill.name}
                    <small>{skill.category}</small>
                  </span>
                  <b>
                    {skill.current}
                    <span className="muted"> / {skill.required || "—"}</span>
                  </b>
                </div>
                <Progress
                  value={
                    skill.required
                      ? Math.min(100, (100 * skill.current) / skill.required)
                      : 100
                  }
                />
                {skill.gap > 0 && (
                  <small className="gap-label">
                    {skill.gap} level{skill.gap > 1 ? "s" : ""} to target
                  </small>
                )}
              </div>
            ))}
          </section>
          <section className="card career-panel">
            <span className="eyebrow">THE BIGGER PICTURE</span>
            <h2>Your career trajectory</h2>
            <div className="career-stop">
              <span className="stop-dot filled" />
              <div>
                <small>YOU ARE HERE</small>
                <h3>{trajectory.current_grade}</h3>
                <p>{employee.role}</p>
              </div>
            </div>
            <div className="career-connector" />
            <div className="career-stop">
              <span className="stop-dot" />
              <div>
                <small>
                  {trajectory.next_grade
                    ? "YOUR NEXT CHAPTER"
                    : "CURRENT TARGET"}
                </small>
                <h3>{trajectory.target_grade}</h3>
                <p>{employee.role}</p>
              </div>
            </div>
            <div className="readiness">
              <div>
                <strong>{trajectory.progress === null ? "—" : `${trajectory.progress}%`}</strong>
                <span>skill readiness</span>
              </div>
              <Progress value={trajectory.progress} />
              <p>{trajectory.note}</p>
            </div>
            {mode !== "trajectory" && (
              <Link className="text-link" to={`/employee/${id}/trajectory`}>
                Explore your trajectory <ArrowRight size={16} />
              </Link>
            )}
          </section>
        </div>
      )}
      {mode === "activities" && (
        <section>
          <div className="section-heading">
            <h2>Available activities</h2>
            <span className="muted">
              {activities.length} activities for your role
            </span>
          </div>
          <div className="activity-grid">
            {activities.map((a) => (
              <article className="card activity-card" key={a.event_id}>
                <span className="pill neutral">{a.type}</span>
                <h3>{a.name}</h3>
                <p>{a.description}</p>
                <div className="skill-chips">
                  {a.skills.map((s) => (
                    <span key={s.skill_id}>
                      {s.name} +{s.gain}
                    </span>
                  ))}
                </div>
                <Link
                  className="button secondary"
                  to={`/employee/${id}/activity/${a.event_id}`}
                >
                  {a.completed ? "View completed activity" : "View Details"}
                  <ArrowRight size={16} />
                </Link>
              </article>
            ))}
          </div>
        </section>
      )}
      {mode === "overview" && (
        <section className="card history-panel">
          <div className="section-heading">
            <h2>Development history</h2>
            <Link className="text-link" to={`/employee/${id}/activities`}>
              Browse activities <ArrowRight size={16} />
            </Link>
          </div>
          {history.length ? (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Activity</th>
                    <th>Date</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h, i) => (
                    <tr key={i}>
                      <td>{h.activity_name}</td>
                      <td>{h.date}</td>
                      <td>
                        <span className={`status ${h.status}`}>{h.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="muted">
              Your first completed activity will appear here.
            </p>
          )}
        </section>
      )}
    </>
  );
}

function ActivityPage() {
  const { id = "", activityId = "" } = useParams();
  const [version, setVersion] = useState(0);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [failure, setFailure] = useState("");
  const { data, error } = useLoad(async () => {
    const [activities, recommendations, trajectory] = await Promise.all([
      api<Activity[]>(`/employees/${id}/activities`),
      api<Recommendation[]>(`/employees/${id}/recommendations`),
      api<Trajectory>(`/employees/${id}/trajectory`),
    ]);
    return {
      activity: activities.find((a) => a.event_id === activityId),
      recommendation: recommendations.find((r) => r.activity_id === activityId),
      trajectory,
    };
  }, [id, activityId, version]);
  async function complete() {
    setBusy(true);
    setFailure("");
    try {
      const result = await api<{
        already_completed: boolean;
        changes: { skill_id: string; before: number; after: number }[];
      }>(`/employees/${id}/activities/${activityId}/complete`, {
        method: "POST",
      });
      setNotice(
        result.already_completed
          ? "This activity was already recorded. No duplicate credit was added."
          : `Activity completed. ${result.changes.map((c) => `${data?.activity?.skills.find((s) => s.skill_id === c.skill_id)?.name || c.skill_id}: ${c.before} → ${c.after}`).join(" · ")}. Your career readiness and recommendations have been recalculated.`,
      );
      setVersion((v) => v + 1);
    } catch (e) {
      setFailure((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (error) return <Alert>{error}</Alert>;
  if (!data) return <Loading />;
  if (!data.activity)
    return <Alert>Activity not found or unavailable for this employee.</Alert>;
  const { activity, recommendation, trajectory } = data;
  return (
    <>
      <Link className="text-link" to={`/employee/${id}`}>
        ← Back to overview
      </Link>
      <div className="page-heading">
        <div>
          <span className="eyebrow">YOUR DEVELOPMENT ACTIVITY</span>
          <h1>{activity.name}</h1>
          <p>{activity.description}</p>
        </div>
        <span className="pill">{activity.type}</span>
      </div>
      {notice && (
        <div className="success" role="status">
          {notice}
        </div>
      )}
      {failure && <Alert>{failure}</Alert>}
      <div className="lower-grid">
        <section className="card detail-panel">
          <h2>What you’ll develop</h2>
          {activity.skills.map((s) => {
            const current = trajectory.skills.find(
              (x) => x.skill_id === s.skill_id,
            );
            const gain = Math.max(
              0,
              Math.min(s.gain, s.max_level - (current?.current || 0)),
            );
            return (
              <div className="effect-row" key={s.skill_id}>
                <div>
                  <h3>{s.name}</h3>
                  <p>
                    Current {current?.current || 0} · Target{" "}
                    {current?.required || "not specified"} · Activity cap{" "}
                    {s.max_level}
                  </p>
                </div>
                <span className="gain">
                  {activity.completed ? <Check size={20} /> : `+${gain}`}
                </span>
              </div>
            );
          })}
          <p className="muted">
            Record completion after finishing the activity. Skill gains are
            limited by the activity’s level cap.
          </p>
          <button
            className="button"
            disabled={busy || activity.completed}
            onClick={complete}
          >
            {activity.completed ? (
              <>
                <CheckCircle2 size={18} /> Completed
              </>
            ) : busy ? (
              "Saving progress…"
            ) : (
              "Complete Activity"
            )}
          </button>
        </section>
        <section className="card detail-panel">
          <h2>
            <Sparkles size={20} /> Why this recommendation?
          </h2>
          {recommendation ? (
            <>
              <p>{recommendation.explanation}</p>
              <ul className="reason-list">
                {Object.entries(recommendation.reasoning).map(([key, text]) => (
                  <li key={key}>
                    <CheckCircle2 size={16} />
                    <span>{text}</span>
                  </li>
                ))}
              </ul>
              <small className="muted">
                {Math.round(recommendation.score * 100)}% weighted match ·{" "}
                {recommendation.explanation_source === "llm-assisted"
                  ? "AI-assisted evidence selection"
                  : "Evidence-based explanation"}
              </small>
            </>
          ) : (
            <p className="muted">
              {activity.completed
                ? "Completion recorded. Return to your overview to explore your updated next steps."
                : "This activity is in your library but is not among your current top recommendations."}
            </p>
          )}
        </section>
      </div>
    </>
  );
}

function HRPage() {
  const { data, error } = useLoad(() => api<HR>("/hr/dashboard"), []);
  const [search, setSearch] = useState("");
  if (error) return <Alert>{error}</Alert>;
  if (!data) return <Loading />;
  return (
    <>
      <div className="page-heading">
        <div>
          <span className="eyebrow">PEOPLE & DEVELOPMENT</span>
          <h1>Growth, across the team.</h1>
          <p>
            Understand development needs and help people take their next step.
          </p>
        </div>
        <Link className="button secondary" to="/dataset">
          <Database size={17} /> Manage dataset
        </Link>
      </div>
      <div className="stats-grid">
        <Stat
          label="Total employees"
          value={data.total_employees}
          note="In the loaded dataset"
          icon={<Users size={18} />}
        />
        <Stat
          label="Active development"
          value={data.active_development}
          note="Completed activity in last 90 days"
          icon={<TrendingUp size={18} />}
        />
        <Stat
          label="Completion rate"
          value={`${data.completion_rate}%`}
          note={`${data.history_count} history records · ${data.skip_rate}% skipped`}
          icon={<CheckCircle2 size={18} />}
        />
        <Stat
          label="Need more options"
          value={data.without_recommendations}
          note="Employees without recommendations"
          icon={<Compass size={18} />}
        />
      </div>
      <div className="lower-grid equal">
        <section className="card chart-panel">
          <h2>Most common skill gaps</h2>
          <p>Employees below their target grade requirements</p>
          {data.skill_gaps.length ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={data.skill_gaps}
                layout="vertical"
                margin={{ left: 10, right: 25 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" allowDecimals={false} />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={140}
                  tick={{ fontSize: 11 }}
                />
                <Tooltip />
                <Bar
                  dataKey="employees"
                  fill="#267861"
                  radius={[0, 5, 5, 0]}
                  maxBarSize={22}
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty">
              No skill gaps in the defined requirements.
            </div>
          )}
        </section>
        <section className="card chart-panel">
          <h2>Activity participation</h2>
          <p>Recorded outcomes · first eight activities</p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={data.participation.slice(0, 8)}
              margin={{ bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="name"
                angle={-30}
                textAnchor="end"
                interval={0}
                tick={{ fontSize: 9 }}
              />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="completed" stackId="a" fill="#267861" />
              <Bar dataKey="skipped" stackId="a" fill="#e7b76c" />
              <Bar dataKey="rejected" stackId="a" fill="#c7d0d2" />
            </BarChart>
          </ResponsiveContainer>
          <div className="legend">
            <span>● Completed</span>
            <span>● Skipped</span>
            <span>● Rejected</span>
          </div>
        </section>
      </div>
      <section className="card history-panel">
        <div className="section-heading">
          <div>
            <h2>Employee development overview</h2>
            <p>Development support, without performance rankings.</p>
          </div>
          <input
            aria-label="Search employees"
            placeholder="Search name, role or ID…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Role / grade</th>
                <th>Main skill gap</th>
                <th>Development activity</th>
                <th>Next steps</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {data.employees
                .filter((e) =>
                  `${e.name} ${e.employee_id} ${e.role}`
                    .toLowerCase()
                    .includes(search.toLowerCase()),
                )
                .map((e) => (
                  <tr key={e.employee_id}>
                    <td>
                      <strong>{e.name || e.employee_id}</strong>
                      <small>{e.employee_id}</small>
                    </td>
                    <td>
                      {e.role}
                      <small>{e.grade}</small>
                    </td>
                    <td>{e.main_gap || "Requirements met"}</td>
                    <td>
                      <span
                        className={`status ${e.active_development ? "completed" : "skipped"}`}
                      >
                        {e.active_development
                          ? "Active in last 90 days"
                          : "No recent completion"}
                      </span>
                      <small>
                        {e.last_completed
                          ? `Last completed: ${e.last_completed}`
                          : "No recorded completion"}
                      </small>
                    </td>
                    <td>
                      <span
                        className={`status ${e.recommendation_count ? "completed" : "skipped"}`}
                      >
                        {e.recommendation_count
                          ? `${e.recommendation_count} available`
                          : "No suitable activity"}
                      </span>
                    </td>
                    <td>
                      <Link
                        className="text-link"
                        to={`/employee/${e.employee_id}`}
                      >
                        View <ArrowUpRight size={14} />
                      </Link>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="card history-panel">
        <h2>Participation detail</h2>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Activity</th>
                <th>Unique participants</th>
                <th>Completed</th>
                <th>Skipped</th>
                <th>Rejected</th>
              </tr>
            </thead>
            <tbody>
              {data.participation.map((e) => (
                <tr key={e.event_id}>
                  <td>{e.name}</td>
                  <td>{e.participants}</td>
                  <td>{e.completed}</td>
                  <td>{e.skipped}</td>
                  <td>{e.rejected}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function DatasetPage() {
  const [version, setVersion] = useState(0);
  const { data, error } = useLoad(
    () => api<Dataset>("/dataset/status"),
    [version],
  );
  const [files, setFiles] = useState<File[]>([]);
  const [mode, setMode] = useState("replace");
  const requiredFiles =
    mode === "append"
      ? ["employees.json", "activity_history.csv"]
      : [
          "employees.json",
          "events.json",
          "skills.json",
          "activity_history.csv",
        ];
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  const [success, setSuccess] = useState(false);
  async function upload(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setFailure("");
    setSuccess(false);
    const body = new FormData();
    files.forEach((f) => body.append("files", f));
    try {
      await api(mode === "append" ? "/dataset/profiles" : "/dataset/upload", {
        method: "POST",
        body,
      });
      setSuccess(true);
      setVersion((v) => v + 1);
    } catch (e) {
      setFailure((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <span className="eyebrow">DATASET MANAGER</span>
          <h1>Real data. Relevant next steps.</h1>
          <p>
            Load your employee development dataset to power the entire
            workspace.
          </p>
        </div>
      </div>
      {error && <Alert>{error}</Alert>}
      {data && (
        <div className="dataset-banner">
          <Database size={23} />
          <div>
            <strong>
              {data.source === "sample"
                ? "Synthetic sample dataset"
                : "Your loaded dataset"}
            </strong>
            <p>
              {data.source === "sample"
                ? "No official hackathon files were supplied. This sample demonstrates the working engine."
                : "Recommendations and HR insights are calculated from these records."}
            </p>
          </div>
          <span className="pill">ACTIVE</span>
        </div>
      )}
      <div className="lower-grid">
        <form className="card detail-panel" onSubmit={upload}>
          <h2>Upload dataset</h2>
          <label>
            Import mode
            <select
              value={mode}
              onChange={(e) => {
                setMode(e.target.value);
                setFiles([]);
                setSuccess(false);
                setFailure("");
              }}
            >
              <option value="replace">Replace all data · 4 files</option>
              <option value="append">Add jury profiles · 2 files</option>
            </select>
          </label>
          <p className="muted">
            {mode === "append"
              ? "Add profiles and their history using the existing activities and skill requirements. Employee IDs must be new; existing progress is preserved."
              : "Choose all four files together. Schemas, identifiers, skill references, and history are validated before replacing the active dataset."}
          </p>
          <label className="upload-zone">
            <Upload size={30} />
            <strong>Select JSON and CSV files</strong>
            <span>{requiredFiles.length} files · up to 10 MB each · UTF-8</span>
            <input
              key={mode}
              aria-label="Dataset files"
              type="file"
              accept=".json,.csv"
              multiple
              onChange={(e) => {
                setFiles(Array.from(e.target.files || []));
                setSuccess(false);
              }}
            />
          </label>
          <ul className="file-list">
            {requiredFiles.map((name) => (
              <li key={name}>
                {files.some((f) => f.name === name) ? (
                  <CheckCircle2 size={17} />
                ) : (
                  <Database size={17} />
                )}{" "}
                {name}
              </li>
            ))}
          </ul>
          <p className="muted">
            {mode === "append"
              ? "Only the supplied profiles and history are added. Existing employees, activities, skills, and sessions are preserved."
              : "Import replaces the active dataset and its saved completions. Keep your source files. Employee sessions will need to sign in again."}
          </p>
          {failure && <Alert>{failure}</Alert>}
          <button
            className="button"
            disabled={
              busy ||
              files.length !== requiredFiles.length ||
              !requiredFiles.every((name) => files.some((f) => f.name === name))
            }
          >
            {busy ? "Validating and loading…" : "Validate & load dataset"}
            <ArrowRight size={17} />
          </button>
        </form>
        <section className="card detail-panel">
          <h2>{success ? "Dataset loaded successfully" : "Active dataset"}</h2>
          {success && (
            <div className="success" role="status">
              All files validated. The engine now uses your uploaded data.
            </div>
          )}
          {data &&
            [
              ["Employees", data.employees],
              ["Activities", data.events],
              ["Skills", data.skills],
              ["History", data.history],
            ].map(([label, count]) => (
              <div className="dataset-count" key={label}>
                <CheckCircle2 size={19} />
                <span>{label} loaded</span>
                <strong>{count}</strong>
              </div>
            ))}
          <p className="muted">
            JSON uses arrays of records; history uses employee_id, event_id,
            date, status columns. See README and data/sample for full schema
            examples.
          </p>
          <Link className="text-link" to="/hr">
            Explore HR dashboard <ArrowRight size={16} />
          </Link>
        </section>
      </div>
    </>
  );
}

function App() {
  const [session, setSession] = useState<Session | null>(readSession());
  useEffect(() => {
    const expired = () => setSession(null);
    window.addEventListener("session-expired", expired);
    return () => window.removeEventListener("session-expired", expired);
  }, []);
  function login(s: Session) {
    sessionStorage.setItem("cq-session", JSON.stringify(s));
    setSession(s);
  }
  function logout() {
    void api("/auth/session", { method: "DELETE" }).catch(() => {});
    sessionStorage.removeItem("cq-session");
    setSession(null);
  }
  function protectedPage(node: ReactNode, hr = false) {
    return !session ? (
      <Navigate to="/login" replace />
    ) : hr && session.role !== "hr" ? (
      <Alert>HR access is required for this workspace.</Alert>
    ) : (
      <Shell session={session} logout={logout}>
        {node}
      </Shell>
    );
  }
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login onLogin={login} />} />
      <Route
        path="/dashboard"
        element={
          <Navigate
            to={
              session
                ? session.role === "hr"
                  ? "/hr"
                  : `/employee/${session.employee_id}`
                : "/login"
            }
            replace
          />
        }
      />
      <Route path="/employee/:id" element={protectedPage(<EmployeePage />)} />
      <Route
        path="/employee/:id/trajectory"
        element={protectedPage(<EmployeePage mode="trajectory" />)}
      />
      <Route
        path="/employee/:id/activities"
        element={protectedPage(<EmployeePage mode="activities" />)}
      />
      <Route
        path="/employee/:id/activity/:activityId"
        element={protectedPage(<ActivityPage />)}
      />
      <Route path="/hr" element={protectedPage(<HRPage />, true)} />
      <Route path="/dataset" element={protectedPage(<DatasetPage />, true)} />
      <Route
        path="*"
        element={
          <div className="empty">
            <h1>Page not found</h1>
            <Link to="/">Return home</Link>
          </div>
        }
      />
    </Routes>
  );
}
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
