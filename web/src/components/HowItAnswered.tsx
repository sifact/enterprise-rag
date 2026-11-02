import { Check, ChevronDown, CircleSlash, X } from "lucide-react";
import { useState } from "react";
import type { Answer, Passage } from "../api";
import { roleStyle, shortLabel } from "../roles";

const REMOVED_REASON: Record<string, string> = {
  classifier: "looked like instructions to the assistant",
  instruction_override: "tells the assistant to ignore its instructions",
  prompt_extraction: "asks for the system prompt",
  role_play: "tries to change the assistant's role",
};

type Step = { label: string; ok: boolean | null; detail: string; ms?: number };

function steps(a: Answer): Step[] {
  const blocked = a.refusal_reason === "blocked_input";
  const t = a.timings;
  const out: Step[] = [
    {
      label: "Question check",
      ok: !blocked,
      detail: blocked
        ? `Blocked: ${a.guard?.reason.replaceAll("_", " ") || "looks like an injection attempt"}`
        : `Passed (injection score ${(a.guard?.score ?? 0).toFixed(3)})`,
      ms: t.input_guard,
    },
  ];
  if (blocked) return out;
  out.push({
    label: "Search",
    ok: a.retrieved.length > 0,
    detail: `${a.retrieved.length} passages found, only among documents ${shortLabel(a.role)} may read`,
    ms: t.search,
  });
  const noEvidence = a.refusal_reason === "no_evidence";
  out.push({
    label: "Relevance check",
    ok: !noEvidence,
    detail: noEvidence
      ? `Best passage scored ${a.top_score?.toFixed(2) ?? "n/a"}: too weak to answer from`
      : `Best passage scored ${a.top_score?.toFixed(2) ?? "n/a"}: strong enough to answer from`,
    ms: t.evidence_check,
  });
  if (noEvidence) return out;
  out.push({
    label: "Passage check",
    ok: true,
    detail:
      a.removed.length + a.cleaned.length === 0
        ? "No passage contained instructions"
        : [
            a.cleaned.length > 0 &&
              `${a.cleaned.length} passage${a.cleaned.length > 1 ? "s" : ""} had a planted instruction cut out`,
            a.removed.length > 0 &&
              `${a.removed.length} passage${a.removed.length > 1 ? "s" : ""} removed for containing instructions`,
          ]
            .filter(Boolean)
            .join("; "),
    ms: t.context_guard,
  });
  out.push({
    label: "Answer",
    ok: !a.refused,
    detail: a.refused
      ? "The model found no answer in the passages and said so"
      : `${a.model ?? "Model"} wrote the answer with ${a.citations.length} citation${a.citations.length === 1 ? "" : "s"}`,
    ms: t.generate,
  });
  return out;
}

function StepIcon({ ok }: { ok: boolean | null }) {
  if (ok === null) return <CircleSlash size={16} className="text-muted" aria-hidden />;
  return ok ? (
    <Check size={16} className="text-[var(--r-sales)]" aria-label="passed" />
  ) : (
    <X size={16} className="text-[var(--r-hr)]" aria-label="stopped here" />
  );
}

function PassageRow({ p, rank }: { p: Passage; rank: number }) {
  const [open, setOpen] = useState(false);
  const status = p.removed_reason
    ? `Removed: ${REMOVED_REASON[p.removed_reason] ?? p.removed_reason}`
    : p.cleaned_reason
      ? `Cleaned: a sentence that ${REMOVED_REASON[p.cleaned_reason] ?? "addressed the assistant"} was cut out${p.cited ? ", then cited" : ""}`
      : p.cited
      ? "Cited in the answer"
      : p.used
        ? "Given to the model, not cited"
        : "Found, not used";
  return (
    <li className="border-t border-rule py-2.5 first:border-t-0">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-start gap-3 text-left"
      >
        <span className="w-5 shrink-0 pt-0.5 text-[13px] text-muted">{rank}</span>
        <span className="min-w-0 flex-1">
          <span className="block text-[14px] font-medium leading-snug">
            {p.title ?? p.doc_id}
            {p.page && p.doc_id.startsWith("sec:") ? (
              <span className="font-normal text-muted">, page {p.page}</span>
            ) : p.section ? (
              <span className="font-normal text-muted">, {p.section}</span>
            ) : null}
          </span>
          <span
            className={`block text-[13px] ${p.removed_reason || p.cleaned_reason ? "text-[var(--r-hr)]" : "text-muted"}`}
          >
            {status}
          </span>
          <span className="mt-1.5 flex flex-wrap gap-1" aria-label="Teams that may read this passage">
            {p.allowed_roles.map((r) => (
              <span
                key={r}
                style={roleStyle(r)}
                className="rounded-sm border border-role/50 px-1.5 text-[12px] leading-5 text-role"
              >
                {shortLabel(r)}
              </span>
            ))}
          </span>
        </span>
        <ChevronDown
          size={16}
          aria-hidden
          className={`mt-1 shrink-0 text-muted transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && <p className="mt-2 ml-8 whitespace-pre-line text-[13px] text-muted">{p.snippet}</p>}
    </li>
  );
}

export default function HowItAnswered({ answer }: { answer: Answer }) {
  const list = steps(answer);
  return (
    <section aria-label="How it answered" className="fade-in">
      <h2 className="mb-3 font-cond text-[19px] font-semibold">How it answered</h2>
      <ol className="mb-6 space-y-2">
        {list.map((s, i) => (
          <li key={s.label} className="flex items-start gap-3">
            <span className="w-5 shrink-0 pt-0.5 text-[13px] text-muted">{i + 1}</span>
            <span className="pt-1">
              <StepIcon ok={s.ok} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="font-medium">{s.label}</span>
              <span className="block text-[13px] text-muted">{s.detail}</span>
            </span>
            {s.ms !== undefined && <span className="pt-0.5 text-[13px] text-muted">{Math.round(s.ms)} ms</span>}
          </li>
        ))}
      </ol>
      {answer.retrieved.length > 0 && (
        <>
          <h3 className="mb-1 font-cond text-[15px] font-semibold">Passages searched</h3>
          <p className="mb-2 text-[13px] text-muted">
            Coloured tags show which teams may read each passage. Every one includes{" "}
            {shortLabel(answer.role)}: other teams' documents are filtered out before the search ranks anything.
          </p>
          <ol>
            {answer.retrieved.map((p, i) => (
              <PassageRow key={p.chunk_id} p={p} rank={i + 1} />
            ))}
          </ol>
        </>
      )}
    </section>
  );
}
