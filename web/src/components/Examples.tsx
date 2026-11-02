import type { Meta } from "../api";
import { roleStyle, shortLabel } from "../roles";

export type Pick = { question: string; role?: string };

/** Suggested questions with known outcomes, taken from the reviewed evaluation set. */
export default function Examples(props: { meta: Meta; role: string; onPick: (p: Pick) => void }) {
  const { meta, role, onPick } = props;
  const mine = meta.examples.by_role[role] ?? { own_team: [], other_team: [] };
  const groups: { title: string; hint: string; items: Pick[] }[] = [
    {
      title: `From ${shortLabel(role)} documents`,
      hint: "Answered with sources.",
      items: mine.own_team.map((q) => ({ question: q })),
    },
    {
      title: "From another team's documents",
      hint: "Refused: your team can't read the source.",
      items: mine.other_team.map((q) => ({ question: q })),
    },
    {
      title: "Try to break it",
      hint: "Instruction tricks, planted instructions and off-topic questions.",
      items: meta.examples.attacks.map((a) => ({ question: a.question, role: a.role })),
    },
  ];
  return (
    <div className="grid gap-5 md:grid-cols-3">
      {groups
        .filter((g) => g.items.length > 0)
        .map((g) => (
          <section key={g.title} aria-label={g.title}>
            <h3 className="font-cond text-[15px] font-semibold">{g.title}</h3>
            <p className="mb-2 text-[13px] text-muted">{g.hint}</p>
            <ul className="space-y-1">
              {g.items.map((item) => (
                <li key={item.question + (item.role ?? "")}>
                  <button
                    type="button"
                    onClick={() => onPick(item)}
                    className="w-full rounded-md px-2 py-1.5 text-left text-[14px] leading-snug text-fg hover:bg-panel"
                  >
                    {item.question}
                    {item.role && item.role !== role && (
                      <span style={roleStyle(item.role)} className="ml-1.5 whitespace-nowrap text-[12px] text-role">
                        as {shortLabel(item.role)}
                      </span>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          </section>
        ))}
    </div>
  );
}
