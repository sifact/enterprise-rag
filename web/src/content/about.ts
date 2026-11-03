// All About-page copy in one place, written for a potential customer rather than an engineer.
// Numbers are not written here: they come from /api/results (committed evaluation runs).

export const REPO_URL = "https://github.com/sifact/enterprise-rag";

export const hero = {
  title: "Answers from your company's documents, without showing anyone what they shouldn't see",
  lead:
    "Employees ask questions in plain language and get short answers with links to the exact source. " +
    "Each person only gets answers from documents their team may read: finance numbers stay with " +
    "finance, contract terms stay with legal. This demo runs on public GitLab documents and fictional " +
    "finance spreadsheets.",
  cta: "Try it in the Playground",
};

export const problem = {
  title: "The problem",
  paragraphs: [
    "Company knowledge is spread across wiki pages, PDF reports and spreadsheets. People either ask a colleague or search for a long time, and the answer they find may be out of date.",
    "AI assistants promise to fix this, but a plain one reads everything it can reach. Ask it about salaries or a customer contract and it will quote whatever it found, to whoever asked. For most companies that alone rules it out.",
  ],
};

export const benefits = {
  title: "What it does for you",
  items: [
    { title: "Answers with proof", body: "Every answer cites the passages it came from, so anyone can click through and check it." },
    { title: "Access stays where it belongs", body: "A question only searches documents the asker's team may read. Everything else is never searched, so it can't leak into an answer." },
    { title: "No guessing", body: "When the documents don't answer the question, it says so instead of making something up." },
    { title: "Hard to trick", body: "Questions that try to override its instructions or claim another team's access are blocked. Instructions hidden inside documents are removed before the model sees them." },
    { title: "Measured, not promised", body: "Every number on this page comes from a repeatable test run on questions with known answers." },
  ],
};

export const howItWorks = {
  title: "How it works",
  intro: "Steps 1 and 2 happen once, when documents are added. Steps 3 to 5 happen for every question.",
  steps: [
    { title: "Label", body: "Each document gets the list of teams allowed to read it, taken from the permissions it already has." },
    { title: "Split and index", body: "Documents are cut into short passages. Every passage keeps its document's team labels." },
    { title: "Filter, then search", body: "A question searches only passages labelled with the asker's team, matching both meaning and exact words." },
    { title: "Check", body: "Is the best passage relevant enough to answer from? Does any passage contain instructions aimed at the assistant? If so, it stops or removes them." },
    { title: "Answer with citations", body: "A language model writes a short answer using only those passages and cites each one. An answer without a valid citation is withheld." },
  ],
};

export const data = {
  title: "The data in this demo",
  intro:
    "There's no private company data here. GitLab publishes its internal handbook openly, so it stands in for a company wiki. The team boundaries are ones this demo enforces on public content; the spreadsheets are made up.",
};

export const results = {
  title: "Measured results",
  intro:
    "We wrote and reviewed 84 test questions with known answers, including questions asked by the wrong team, off-topic questions and attempts to trick the assistant. 41 were used to tune the system; the 43 held back are the ones reported here.",
  safetyTitle: "Safety",
  answersTitle: "Answer quality",
  searchTitle: "Search quality",
  searchIntro:
    "We tried four ways of searching and kept the one that did best on the tuning questions. These are the scores on the held-back questions.",
  pending: "Results will appear here once the evaluation has run.",
};

export const metricText: Record<string, { label: string; meaning: string; percent?: boolean; lowerIsBetter?: boolean }> = {
  leak_rate: { label: "Leak rate", meaning: "Questions where a document the asker's team can't read reached the search results or the answer.", percent: true, lowerIsBetter: true },
  refusal_accuracy: { label: "Correct refusals", meaning: "Questions that had to be refused (wrong team, off-topic or an attack) and were.", percent: true },
  injection_block_rate: { label: "Attacks stopped", meaning: "Trick questions blocked, plus questions answered from a booby-trapped page without following its hidden instruction.", percent: true },
  numeric_match: { label: "Exact numbers", meaning: "Finance questions where the answer contained the correct figure (within 0.5%).", percent: true },
  faithfulness: { label: "Faithfulness", meaning: "How much of each answer is supported by its sources, scored by a separate AI judge.", percent: true },
  answer_relevancy: { label: "Relevance", meaning: "How directly answers address the question asked, scored by the judge.", percent: true },
  citation_precision: { label: "Citations that hold up", meaning: "Cited passages the judge confirmed actually support the answer.", percent: true },
  false_refusal_rate: { label: "Wrongly refused", meaning: "Answerable questions it declined to answer.", percent: true, lowerIsBetter: true },
  latency_p95_ms: { label: "Slowest 5%", meaning: "95% of searches took this long or less." },
};

export const searchLabels: Record<string, string> = {
  "reference-bm25": "Keyword search over whole pages (starting point)",
  "cloud-dense": "Meaning search",
  "cloud-bm25": "Keyword search",
  "cloud-hybrid": "Meaning and keywords, merged by rank",
  "cloud-hybrid-dbsf": "Meaning and keywords, merged by score",
};
export const SEARCH_USED = "cloud-hybrid";

export const limitations = {
  title: "Limitations",
  items: [
    "The test set is small (43 reported questions), so one question moves a score by two to three points.",
    "Spreadsheet questions are the weakest area: table rows look less similar to a question than prose does, so the relevance check is least certain there.",
    "The AI-judged answer scores (faithfulness and relevance) haven't been measured on the held-back questions yet: the free tier of the judge model has a daily limit. They will be added to this page when they have been run.",
    "Sign-in is simulated: here you pick a team. A real deployment takes the team from your company sign-in (for example Okta or Microsoft Entra ID).",
    "A single question on the live demo takes about one to two seconds. The language model runs on a free tier that allows only a few questions a minute across all visitors, so when it is busy an answer waits or asks you to try again; repeated questions are answered from a cache.",
    "The documents are a fixed snapshot. Keeping labels in sync when permissions change is part of a real deployment.",
  ],
};

export const yourData = {
  title: "Running it on your documents",
  steps: [
    "Connect your sources (for example SharePoint, Google Drive or Confluence) and copy each document's existing permissions as its labels.",
    "Map your sign-in groups to teams, so each person's access comes from the login they already use.",
    "Run it in your own cloud account on a standard serverless setup, with the language model of your choice.",
    "Before launch, write test questions from your own documents and run the same evaluation, including the wrong-team and attack questions.",
  ],
};

export const stack = {
  title: "Technology",
  items: [
    ["Search", "Qdrant Cloud: meaning vectors (all-MiniLM-L6-v2) and keyword vectors (BM25), merged by rank, computed inside Qdrant"],
    ["Checks", "Llama Prompt Guard 2 plus rules for questions and passages; a similarity threshold for relevance"],
    ["Answers", "Qwen 3.8 27B on Groq, with numbered, delimited sources and citation checks"],
    ["Evaluation", "84 reviewed questions; DeepEval with gpt-oss-120b as the judge"],
    ["App", "Python and FastAPI on Vercel, React, TypeScript and Tailwind CSS; no servers to manage"],
  ] as [string, string][],
};
