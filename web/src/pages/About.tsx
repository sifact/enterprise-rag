import { ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";
import { api, type Meta, type Results } from "../api";
import * as copy from "../content/about";
import { roleStyle, shortLabel } from "../roles";

const SECTIONS = [
  ["problem", copy.problem.title],
  ["benefits", copy.benefits.title],
  ["how", copy.howItWorks.title],
  ["data", copy.data.title],
  ["results", copy.results.title],
  ["limitations", copy.limitations.title],
  ["your-data", copy.yourData.title],
  ["stack", copy.stack.title],
] as const;

function fmt(key: string, value: number | null | undefined): string {
  if (value === null || value === undefined) return "n/a";
  const info = copy.metricText[key];
  if (key.startsWith("latency")) return value >= 1000 ? `${(value / 1000).toFixed(1)} s` : `${Math.round(value)} ms`;
  if (info?.percent) return `${Math.round(value * 100)}%`;
  return value.toFixed(2);
}

function Section(props: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section id={props.id} aria-labelledby={`${props.id}-h`} className="scroll-mt-20 border-t border-rule pt-10">
      <h2 id={`${props.id}-h`} className="mb-4 font-cond text-[30px] font-semibold leading-tight">
        {props.title}
      </h2>
      {props.children}
    </section>
  );
}

function Metrics(props: { title: string; values: Record<string, number> | null; keys: string[] }) {
  if (!props.values) return null;
  return (
    <div className="mb-8">
      <h3 className="mb-3 font-cond text-[19px] font-semibold">{props.title}</h3>
      <dl className="grid gap-x-8 gap-y-4 sm:grid-cols-2">
        {props.keys
          .filter((k) => props.values?.[k] !== undefined)
          .map((k) => (
            <div key={k} className="border-l-2 border-rule pl-3">
              <dt className="text-[14px] text-muted">{copy.metricText[k]?.label ?? k}</dt>
              <dd className="font-cond text-[30px] font-semibold leading-none">{fmt(k, props.values?.[k])}</dd>
              <dd className="mt-1 text-[13px] leading-snug text-muted">{copy.metricText[k]?.meaning}</dd>
            </div>
          ))}
      </dl>
    </div>
  );
}

function SearchTable({ rows }: { rows: Results["retrieval"] }) {
  if (rows.length === 0) return null;
  return (
    <div className="mb-2">
      <h3 className="mb-1 font-cond text-[19px] font-semibold">{copy.results.searchTitle}</h3>
      <p className="mb-3 max-w-[68ch] text-muted">{copy.results.searchIntro}</p>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] border-collapse text-left text-[14px]">
          <thead>
            <tr className="border-b border-rule text-muted">
              <th className="py-2 pr-4 font-normal">Search method</th>
              <th className="py-2 pr-4 font-normal" title="Share of questions with the right passage in the top 5">Found in top 5</th>
              <th className="py-2 pr-4 font-normal" title="nDCG@10: rewards putting the right passages near the top">Ranking score</th>
              <th className="py-2 font-normal">Slowest 5%</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const used = r.pipeline === copy.SEARCH_USED;
              return (
                <tr key={r.pipeline} className="border-b border-rule">
                  <td className="py-2 pr-4">
                    {copy.searchLabels[r.pipeline] ?? r.pipeline}
                    {used && <span className="ml-2 text-[13px] font-medium text-[var(--r-sales)]">used</span>}
                  </td>
                  <td className="py-2 pr-4">{r["hit@5"] === null ? "n/a" : `${Math.round(r["hit@5"] * 100)}%`}</td>
                  <td className="py-2 pr-4">{r["ndcg@10"]?.toFixed(2) ?? "n/a"}</td>
                  <td className="py-2">{fmt("latency_p95_ms", r.latency_p95_ms)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function About() {
  const [results, setResults] = useState<Results | null>(null);
  const [meta, setMeta] = useState<Meta | null>(null);

  useEffect(() => {
    api.results().then(setResults).catch(() => setResults(null));
    api.meta().then(setMeta).catch(() => setMeta(null));
  }, []);

  return (
    <div className="mx-auto grid max-w-[1240px] grid-cols-1 gap-10 px-4 py-10 sm:px-6 xl:grid-cols-[200px_minmax(0,1fr)]">
      <nav aria-label="On this page" className="hidden xl:block">
        <ul className="sticky top-24 space-y-1.5 text-[14px]">
          {SECTIONS.map(([id, title]) => (
            <li key={id}>
              <a
                href={`#/about`}
                onClick={(e) => {
                  e.preventDefault();
                  document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
                }}
                className="text-muted hover:text-fg"
              >
                {title}
              </a>
            </li>
          ))}
        </ul>
      </nav>

      <article className="min-w-0 space-y-12">
        <header className="max-w-[68ch]">
          <h1 className="font-cond text-[38px] font-semibold leading-[1.1] tracking-tight">{copy.hero.title}</h1>
          <p className="mt-4 text-[17px] leading-relaxed text-muted">{copy.hero.lead}</p>
          <a
            href="#/playground"
            className="mt-6 inline-block rounded-md bg-fg px-4 py-2 font-medium text-ink hover:opacity-90"
          >
            {copy.hero.cta}
          </a>
        </header>

        <Section id="problem" title={copy.problem.title}>
          <div className="max-w-[68ch] space-y-3 text-[16px]">
            {copy.problem.paragraphs.map((p) => (
              <p key={p}>{p}</p>
            ))}
          </div>
        </Section>

        <Section id="benefits" title={copy.benefits.title}>
          <ul className="grid max-w-[900px] gap-x-10 gap-y-5 sm:grid-cols-2">
            {copy.benefits.items.map((b) => (
              <li key={b.title}>
                <p className="font-medium">{b.title}</p>
                <p className="mt-0.5 text-muted">{b.body}</p>
              </li>
            ))}
          </ul>
        </Section>

        <Section id="how" title={copy.howItWorks.title}>
          <p className="mb-6 max-w-[68ch] text-muted">{copy.howItWorks.intro}</p>
          <ol className="grid gap-4 lg:grid-cols-5 lg:gap-0">
            {copy.howItWorks.steps.map((s, i) => (
              <li key={s.title} className="relative lg:pr-5">
                <div className="mb-3 hidden items-center lg:flex" aria-hidden>
                  <span className={`h-3 w-3 rounded-full border-2 ${i < 2 ? "border-muted" : "border-fg bg-fg"}`} />
                  {i < 4 && <span className="h-px flex-1 bg-rule" />}
                </div>
                <p className="font-cond text-[17px] font-semibold">
                  <span className="mr-1.5 text-muted">{i + 1}</span>
                  {s.title}
                </p>
                <p className="mt-1 text-[14px] leading-snug text-muted">{s.body}</p>
              </li>
            ))}
          </ol>
        </Section>

        <Section id="data" title={copy.data.title}>
          <p className="mb-5 max-w-[68ch]">{copy.data.intro}</p>
          {meta && (
            <div className="grid gap-8 lg:grid-cols-2">
              <div>
                <h3 className="mb-2 font-cond text-[19px] font-semibold">Sources ({meta.corpus.documents} documents)</h3>
                <ul className="space-y-1.5">
                  {meta.corpus.sources.map((s) => (
                    <li key={s.label} className="flex justify-between gap-4 border-b border-rule pb-1.5">
                      <span>{s.label}</span>
                      <span className="text-muted">{s.documents}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="mb-2 font-cond text-[19px] font-semibold">Who can read what</h3>
                <ul className="space-y-1.5">
                  {meta.roles.map((r) => (
                    <li key={r.name} style={roleStyle(r.name)} className="flex items-start gap-3 border-b border-rule pb-1.5">
                      <span aria-hidden className="mt-1.5 h-3 w-1.5 shrink-0 rounded-full bg-role" />
                      <span className="min-w-0 flex-1">
                        <span className="font-medium">{shortLabel(r.name)}</span>
                        <span className="text-muted">: {r.description}</span>
                      </span>
                      <span className="text-muted">{r.documents}</span>
                    </li>
                  ))}
                </ul>
                <p className="mt-2 text-[13px] text-muted">
                  Counts include the 30 company-wide pages every team can read.
                </p>
              </div>
            </div>
          )}
        </Section>

        <Section id="results" title={copy.results.title}>
          <p className="mb-8 max-w-[68ch]">{copy.results.intro}</p>
          {!results || (!results.safety && !results.answers && results.retrieval.length === 0) ? (
            <p className="text-muted">{copy.results.pending}</p>
          ) : (
            <>
              <Metrics
                title={copy.results.safetyTitle}
                values={results.safety}
                keys={["leak_rate", "refusal_accuracy", "injection_block_rate"]}
              />
              <Metrics
                title={copy.results.answersTitle}
                values={results.answers}
                keys={[
                  "numeric_match",
                  "faithfulness",
                  "answer_relevancy",
                  "citation_precision",
                  "false_refusal_rate",
                ]}
              />
              <SearchTable rows={results.retrieval} />
              {results.run_dates.length > 0 && (
                <p className="mt-4 text-[13px] text-muted">Measured on {results.run_dates.join(", ")}.</p>
              )}
            </>
          )}
        </Section>

        <Section id="limitations" title={copy.limitations.title}>
          <ul className="max-w-[68ch] list-disc space-y-2 pl-5 marker:text-muted">
            {copy.limitations.items.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        </Section>

        <Section id="your-data" title={copy.yourData.title}>
          <ol className="max-w-[68ch] list-decimal space-y-2 pl-5 marker:text-muted">
            {copy.yourData.steps.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ol>
        </Section>

        <Section id="stack" title={copy.stack.title}>
          <dl className="max-w-[820px] divide-y divide-rule">
            {copy.stack.items.map(([k, v]) => (
              <div key={k} className="grid gap-1 py-2.5 sm:grid-cols-[140px_1fr]">
                <dt className="font-medium">{k}</dt>
                <dd className="text-muted">{v}</dd>
              </div>
            ))}
          </dl>
          <a
            href={copy.REPO_URL}
            target="_blank"
            rel="noreferrer"
            className="mt-5 inline-flex items-center gap-1.5 text-[15px] underline underline-offset-4 hover:text-fg"
          >
            Source code and evaluation runs on GitHub <ExternalLink size={14} aria-hidden />
          </a>
        </Section>
      </article>
    </div>
  );
}
