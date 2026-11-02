import { useCallback, useState } from "react";

export type Theme = "dark" | "light";

/** Dark by default; the choice is stored so it survives reloads (index.html applies it early). */
export function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>(() =>
    document.documentElement.classList.contains("dark") ? "dark" : "light",
  );
  const toggle = useCallback(() => {
    setTheme((current) => {
      const next: Theme = current === "dark" ? "light" : "dark";
      document.documentElement.classList.toggle("dark", next === "dark");
      localStorage.setItem("theme", next);
      return next;
    });
  }, []);
  return [theme, toggle];
}
