// Typed client for the FastAPI backend. Shapes mirror src/enterprise_rag/serving/.

export type Role = { name: string; label: string; description: string; documents: number };

export type Attack = { question: string; role: string; kind: string };

export type Meta = {
  roles: Role[];
  examples: {
    by_role: Record<string, { own_team: string[]; other_team: string[] }>;
    attacks: Attack[];
  };
  corpus: { documents: number; sources: { label: string; documents: number }[] };
  limits: { max_question_chars: number; per_minute: number; per_day: number };
};

export type Citation = {
  n: number;
  chunk_id: string;
  doc_id: string;
  title: string | null;
  section: string | null;
  page: number | null;
  source_url: string | null;
  snippet: string;
};

export type Passage = {
  chunk_id: string;
  doc_id: string;
  title: string | null;
  section: string | null;
  page: number | null;
  allowed_roles: string[];
  score: number;
  cited: boolean;
  used: boolean;
  removed_reason: string | null;
  cleaned_reason: string | null;
  snippet: string;
};

export type Answer = {
  role: string;
  question: string;
  answer: string;
  refused: boolean;
  refusal_reason: string | null;
  citations: Citation[];
  retrieved: Passage[];
  removed: { chunk_id: string; doc_id: string; reason: string }[];
  cleaned: { chunk_id: string; doc_id: string; reason: string }[];
  guard: { flagged: boolean; score: number; reason: string } | null;
  timings: Record<string, number>;
  top_score: number | null;
  model: string | null;
  usage: { prompt_tokens: number; completion_tokens: number } | null;
  latency_ms: number;
  cached: boolean;
};

export type RetrievalRow = {
  pipeline: string;
  "hit@5": number | null;
  "hit@10": number | null;
  "mrr@10": number | null;
  "ndcg@10": number | null;
  "evidence_recall@10": number | null;
  latency_p95_ms: number | null;
};

export type Results = {
  split: string;
  retrieval: RetrievalRow[];
  answers: Record<string, number> | null;
  safety: Record<string, number> | null;
  run_dates: string[];
};

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError(0, "Can't reach the server. Check your connection and try again.");
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status}).`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* keep the generic message */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  meta: () => request<Meta>("/api/meta"),
  results: () => request<Results>("/api/results"),
  signIn: (role: string) =>
    request<{ role: string }>("/api/session", { method: "POST", body: JSON.stringify({ role }) }),
  ask: (question: string) =>
    request<Answer>("/api/ask", { method: "POST", body: JSON.stringify({ question }) }),
};
