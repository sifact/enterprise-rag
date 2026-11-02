import { useCallback, useEffect, useRef, useState } from "react";
import { type Answer, api, ApiError, type Meta } from "../api";
import AnswerView from "../components/AnswerView";
import Examples, { type Pick } from "../components/Examples";
import HowItAnswered from "../components/HowItAnswered";
import QuestionBox from "../components/QuestionBox";
import RoleSwitcher from "../components/RoleSwitcher";
import { roleStyle, shortLabel } from "../roles";

const DEFAULT_ROLE = "finance";
const PROGRESS = [
  "Checking the question",
  "Searching your team's documents",
  "Checking the passages",
  "Writing a cited answer",
];

type Status =
  | { kind: "idle" }
  | { kind: "loading"; question: string; role: string }
  | { kind: "done"; answer: Answer }
  | { kind: "error"; message: string; question: string };

function savedRole(): string {
  return localStorage.getItem("role") ?? DEFAULT_ROLE;
}

export default function Playground() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [metaError, setMetaError] = useState<string | null>(null);
  const [role, setRole] = useState<string>(savedRole);
  const [question, setQuestion] = useState("");
  const [status, setStatus] = useState<Status>({ kind: "idle" });
  const [progress, setProgress] = useState(0);
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api
      .meta()
      .then((m) => {
        setMeta(m);
        const r = m.roles.some((x) => x.name === savedRole()) ? savedRole() : DEFAULT_ROLE;
        setRole(r);
        return api.signIn(r);
      })
      .catch((e: ApiError) => setMetaError(e.message));
  }, []);

  useEffect(() => {
    if (status.kind !== "loading") return;
    setProgress(0);
    const timer = window.setInterval(() => setProgress((p) => Math.min(p + 1, PROGRESS.length - 1)), 900);
    return () => window.clearInterval(timer);
  }, [status.kind]);

  const switchRole = useCallback(async (next: string) => {
    await api.signIn(next);
    localStorage.setItem("role", next);
    setRole(next);
  }, []);

  const ask = useCallback(
    async (q: string, asRole?: string) => {
      const r = asRole ?? role;
      setStatus({ kind: "loading", question: q, role: r });
      requestAnimationFrame(() => resultRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" }));
      try {
        if (r !== role) await switchRole(r);
        let answer: Answer;
        try {
          answer = await api.ask(q);
        } catch (e) {
          if (!(e instanceof ApiError) || e.status !== 401) throw e;
          await api.signIn(r); // the session expired or the server restarted
          answer = await api.ask(q);
        }
        setStatus({ kind: "done", answer });
      } catch (e) {
        setStatus({ kind: "error", message: (e as Error).message, question: q });
      }
    },
    [role, switchRole],
  );

  const onPick = (p: Pick) => {
    setQuestion(p.question);
    void ask(p.question, p.role);
  };

  if (metaError) {
    return (
      <div className="mx-auto max-w-[1240px] px-4 py-16 sm:px-6">
        <p className="font-medium">The demo server isn't responding.</p>
        <p className="mt-1 text-muted">{metaError}</p>
      </div>
    );
  }

  return (
    <div className="mx-auto grid max-w-[1240px] gap-8 px-4 py-6 sm:px-6 lg:grid-cols-[250px_minmax(0,1fr)] lg:py-10">
      <aside className="lg:sticky lg:top-20 lg:self-start">
        {meta ? (
          <RoleSwitcher
            roles={meta.roles}
            role={role}
            onChange={(r) => {
              void switchRole(r);
              setStatus({ kind: "idle" });
            }}
            disabled={status.kind === "loading"}
          />
        ) : (
          <div className="h-40 animate-pulse rounded-md bg-panel" aria-label="Loading teams" />
        )}
        <p className="mt-4 hidden text-[13px] leading-snug text-muted lg:block">
          In a real deployment your team comes from the company sign-in. Here you choose it, and the
          server signs that choice into your session so it can't be changed from the browser.
        </p>
      </aside>

      <div className="min-w-0 space-y-8" style={roleStyle(role)}>
        <QuestionBox
          value={question}
          onChange={setQuestion}
          onSubmit={() => void ask(question.trim())}
          max={meta?.limits.max_question_chars ?? 500}
          busy={status.kind === "loading"}
          teamLabel={shortLabel(role)}
        />

        {meta && (status.kind === "idle" || status.kind === "error") && (
          <Examples meta={meta} role={role} onPick={onPick} />
        )}

        <div ref={resultRef} className="scroll-mt-20">
          {status.kind === "loading" && (
            <div aria-live="polite" className="space-y-3">
              <p className="text-muted">
                {PROGRESS[progress]} for <span className="text-role">{shortLabel(status.role)}</span>…
              </p>
              <div className="h-4 w-3/4 animate-pulse rounded bg-panel" />
              <div className="h-4 w-1/2 animate-pulse rounded bg-panel" />
            </div>
          )}

          {status.kind === "error" && (
            <div role="alert" className="max-w-[68ch] rounded-md border border-rule bg-panel p-4">
              <p className="font-medium">No answer this time</p>
              <p className="mt-1 text-muted">{status.message}</p>
              <button
                type="button"
                onClick={() => void ask(status.question)}
                className="mt-3 rounded-md border border-rule px-3 py-1.5 text-[14px] hover:border-fg"
              >
                Try again
              </button>
            </div>
          )}

          {status.kind === "done" && meta && (
            <div className="grid gap-10 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
              <AnswerView answer={status.answer} roles={meta.roles} onAskAs={(r) => void ask(status.answer.question, r)} />
              <HowItAnswered answer={status.answer} />
            </div>
          )}
        </div>

        {status.kind === "done" && meta && (
          <details className="border-t border-rule pt-4">
            <summary className="cursor-pointer text-[14px] text-muted hover:text-fg">More questions to try</summary>
            <div className="mt-4">
              <Examples meta={meta} role={role} onPick={onPick} />
            </div>
          </details>
        )}
      </div>
    </div>
  );
}
