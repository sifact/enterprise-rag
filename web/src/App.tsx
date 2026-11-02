import { useEffect, useState } from "react";
import TopBar from "./components/TopBar";
import About from "./pages/About";
import Playground from "./pages/Playground";
import { useTheme } from "./theme";

export type Route = "playground" | "about";

function readRoute(): Route {
  return window.location.hash.startsWith("#/about") ? "about" : "playground";
}

export default function App() {
  const [route, setRoute] = useState<Route>(readRoute);
  const [theme, toggleTheme] = useTheme();

  useEffect(() => {
    const onHash = () => {
      setRoute(readRoute());
      window.scrollTo({ top: 0 });
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => {
    document.title =
      route === "about"
        ? "About: Enterprise RAG"
        : "Enterprise RAG: answers that respect who can see what";
  }, [route]);

  return (
    <div className="min-h-dvh">
      <TopBar route={route} theme={theme} onToggleTheme={toggleTheme} />
      <main id="main">{route === "about" ? <About /> : <Playground />}</main>
    </div>
  );
}
