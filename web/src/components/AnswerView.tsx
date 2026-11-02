import { ExternalLink, ShieldAlert } from "lucide-react";
import { Fragment } from "react";
import type { Answer, Citation, Role } from "../api";
import { refusalMessage, roleStyle, shortLabel } from "../roles";

/** Answer text with its [n] markers turned into links to the sources listed below it. */
function AnswerText({ text, citations }: { text: string; citations: Citation[] }) {
  const known = new Set(citations.map((c) => c.n));
  const parts = text.split(/(\[\d+\])/g);
  return (
    <p className="max-w-[68ch] text-[17px] leading-relaxed">
      {parts.map((part, i) => {
        const m = part.match(/^\[(\d+)\]$/);
        if (!m || !known.has(Number(m[1]))) return <Fragment key={i}>{part}</Fragment>;
        return (
          <a
            key={i}
            href={`#source-${m[1]}`}
            onClick={(e) => {
              e.preventDefault();
              document.getElementById(`source-${m[1]}`)?.scrollIntoView({ block: "nearest", behavior: "smooth" });
            }}
            className="mx-0.5 inline-flex h-5 min-w-5 items-center justify-center rounded border border-rule px-1 align-[2px] text-[12px] font-medium text-muted no-underline hover:border-fg hover:text-fg"
            aria-label={`Source ${m[1]}`}
          >
            {m[1]}
          </a>
        );
      })}
    </p>
  );
}

function where(c: { section: string | null; page: number | null; doc_id: string }) {
  if (c.page && c.doc_id.startsWith("sec:")) return `page ${c.page}`;
  return c.section || "";
}

export default function AnswerView(props: {
  answer: Answer;
  roles: Role[];
  onAskAs: (role: string) => void;
}) {
  const { answer, roles, onAskAs } = props;
  const others = roles.filter((r) => r.name !== answer.role);
  const refusal = answer.refused ? refusalMessage(answer.refusal_reason, answer.role) : null;
  return (
    <section aria-live="polite" className="fade-in" style={roleStyle(answer.role)}>
      <div className="mb-3 flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h2 className="font-cond text-[19px] font-semibold">Answer</h2>
        <span className="text-[13px] text-muted">
          for <span className="font-medium text-role">{shortLabel(answer.role)}</span>, in{" "}
          {(answer.latency_ms / 1000).toFixed(1)} s{answer.cached ? " (from cache)" : ""}
        </span>
      </div>

      {refusal ? (
        <div className="flex max-w-[68ch] gap-3 rounded-md border border-role/60 bg-panel p-4">
          <ShieldAlert size={20} className="mt-0.5 shrink-0 text-role" aria-hidden />
          <div>
            <p className="font-medium">{refusal.title}</p>
            <p className="mt-1 text-muted">{refusal.body}</p>
          </div>
        </div>
      ) : (
        <AnswerText text={answer.answer} citations={answer.citations} />
      )}

      {answer.citations.length > 0 && (
        <div className="mt-5">
          <h3 className="mb-2 text-[13px] text-muted">Sources</h3>
          <ol className="space-y-2">
            {[...answer.citations]
              .sort((a, b) => a.n - b.n)
              .map((c) => (
                <li key={c.chunk_id} id={`source-${c.n}`} className="flex gap-3 scroll-mt-20">
                  <span className="mt-0.5 inline-flex h-5 min-w-5 items-center justify-center rounded border border-rule px-1 text-[12px] text-muted">
                    {c.n}
                  </span>
                  <div className="min-w-0">
                    <p className="text-[14px]">
                      <span className="font-medium">{c.title ?? c.doc_id}</span>
                      {where(c) && <span className="text-muted">, {where(c)}</span>}
                      {c.source_url && (
                        <a
                          href={c.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="ml-1.5 inline-flex items-center gap-0.5 text-[13px] text-muted underline-offset-2 hover:text-fg hover:underline"
                        >
                          original <ExternalLink size={12} aria-hidden />
                        </a>
                      )}
                    </p>
                    <p className="mt-0.5 line-clamp-2 max-w-[68ch] text-[13px] text-muted">{c.snippet}</p>
                  </div>
                </li>
              ))}
          </ol>
        </div>
      )}

      <div className="mt-6">
        <p className="mb-2 text-[13px] text-muted">Ask the same question as another team</p>
        <div className="flex flex-wrap gap-1.5">
          {others.map((r) => (
            <button
              key={r.name}
              type="button"
              style={roleStyle(r.name)}
              onClick={() => onAskAs(r.name)}
              className="flex items-center gap-1.5 rounded-md border border-rule px-2.5 py-1 text-[13px] hover:border-role"
            >
              <span aria-hidden className="h-2.5 w-2.5 rounded-full bg-role" />
              {shortLabel(r.name)}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
