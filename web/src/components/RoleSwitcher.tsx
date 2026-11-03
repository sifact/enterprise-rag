import { useEffect, useRef } from "react";
import type { Role } from "../api";
import { roleStyle, shortLabel } from "../roles";

/** The team list. Picking a team signs the visitor in as that team (a signed server session). */
export default function RoleSwitcher(props: {
  roles: Role[];
  role: string;
  onChange: (role: string) => void;
  disabled?: boolean;
}) {
  const { roles, role, onChange, disabled } = props;
  const row = useRef<HTMLDivElement>(null);
  // On a phone the team chips scroll sideways: keep the signed-in team in view.
  useEffect(() => {
    const active = row.current?.querySelector<HTMLElement>('[data-active="true"]');
    if (active && row.current) {
      row.current.scrollTo({ left: active.offsetLeft - 16, behavior: "smooth" });
    }
  }, [role, roles]);
  return (
    <fieldset disabled={disabled} className="min-w-0">
      <legend className="mb-3 text-[13px] text-muted">You are signed in as</legend>
      <div ref={row} className="flex gap-2 overflow-x-auto pb-1 lg:flex-col lg:gap-1 lg:overflow-visible">
        {roles.map((r) => {
          const active = r.name === role;
          return (
            <label
              key={r.name}
              data-active={active}
              style={roleStyle(r.name)}
              className={`group relative flex shrink-0 cursor-pointer items-center gap-3 rounded-md border px-3 py-2 transition-colors lg:py-2.5 ${
                active ? "border-role bg-panel" : "border-transparent hover:bg-panel"
              }`}
            >
              <input
                type="radio"
                name="role"
                value={r.name}
                checked={active}
                onChange={() => onChange(r.name)}
                className="sr-only"
              />
              <span
                aria-hidden
                className={`h-8 w-1.5 shrink-0 rounded-full bg-role transition-opacity ${active ? "" : "opacity-45"}`}
              />
              <span className="min-w-0">
                <span className={`block font-cond text-[17px] leading-tight ${active ? "font-semibold text-fg" : "text-fg"}`}>
                  {shortLabel(r.name)}
                </span>
                <span className="hidden text-[13px] leading-snug text-muted lg:block">
                  {r.description} ({r.documents})
                </span>
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
