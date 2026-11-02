import type { CSSProperties } from "react";

/** CSS variable carrying a team's clearance colour (defined per theme in index.css). */
export function roleStyle(role: string): CSSProperties {
  return { "--role": `var(--r-${role})` } as CSSProperties;
}

export const SHORT_LABEL: Record<string, string> = {
  engineering: "Engineering",
  hr: "People",
  marketing: "Marketing",
  legal: "Legal",
  sales: "Sales",
  finance: "Finance",
  c_level: "Executive",
};

export function shortLabel(role: string): string {
  return SHORT_LABEL[role] ?? role;
}

/** Plain-language explanation for each refusal reason the pipeline records. */
export function refusalMessage(reason: string | null, role: string): { title: string; body: string } {
  const team = shortLabel(role);
  switch (reason) {
    case "blocked_input":
      return {
        title: "Question blocked before searching",
        body: "It looks like an attempt to change the assistant's instructions or to claim another team's access, so nothing was searched.",
      };
    case "no_evidence":
      return {
        title: `Nothing ${team} can read answers this`,
        body: "The answer may sit in another team's documents, or it isn't in the company documents at all. Documents your team can't read were never searched.",
      };
    case "not_in_sources":
      return {
        title: `The ${team} documents don't contain the answer`,
        body: "The assistant read the closest passages your team can see and found no answer, so it didn't guess.",
      };
    case "no_support":
      return {
        title: "Answer withheld: no source backed it",
        body: "The draft answer didn't cite any of the passages it was given, so it wasn't shown.",
      };
    default:
      return { title: "No answer", body: "The assistant couldn't answer this from your team's documents." };
  }
}
