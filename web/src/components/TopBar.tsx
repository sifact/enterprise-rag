import { Moon, Sun } from "lucide-react";
import type { Route } from "../App";
import type { Theme } from "../theme";

const TABS: { route: Route; label: string }[] = [
  { route: "playground", label: "Playground" },
  { route: "about", label: "About" },
];

export default function TopBar(props: { route: Route; theme: Theme; onToggleTheme: () => void }) {
  const { route, theme, onToggleTheme } = props;
  return (
    <header className="sticky top-0 z-20 border-b border-rule bg-ink/95 backdrop-blur">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:rounded-md focus:bg-panel focus:px-3 focus:py-2"
      >
        Skip to content
      </a>
      <div className="mx-auto flex h-14 max-w-[1240px] items-center gap-6 px-4 sm:px-6">
        <a href="#/playground" className="flex items-center gap-2.5 font-cond text-[19px] font-semibold tracking-tight">
          <Mark />
          <span>Enterprise RAG</span>
        </a>
        <nav aria-label="Sections" className="flex h-full items-stretch gap-1">
          {TABS.map((t) => {
            const active = route === t.route;
            return (
              <a
                key={t.route}
                href={`#/${t.route}`}
                aria-current={active ? "page" : undefined}
                className={`flex items-center border-b-2 px-3 text-[15px] transition-colors ${
                  active ? "border-fg font-medium text-fg" : "border-transparent text-muted hover:text-fg"
                }`}
              >
                {t.label}
              </a>
            );
          })}
        </nav>
        <button
          type="button"
          onClick={onToggleTheme}
          className="ml-auto flex h-9 w-9 items-center justify-center rounded-md border border-rule text-muted hover:text-fg"
          aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
          title={theme === "dark" ? "Light theme" : "Dark theme"}
        >
          {theme === "dark" ? <Sun size={17} aria-hidden /> : <Moon size={17} aria-hidden />}
        </button>
      </div>
    </header>
  );
}

/** Three bars in team colours: documents filtered by who may read them. */
function Mark() {
  return (
    <svg width="22" height="22" viewBox="0 0 32 32" aria-hidden>
      <rect x="4" y="7" width="22" height="4" rx="2" fill="var(--r-engineering)" />
      <rect x="4" y="14" width="14" height="4" rx="2" fill="var(--r-sales)" />
      <rect x="4" y="21" width="18" height="4" rx="2" fill="var(--r-marketing)" />
    </svg>
  );
}
