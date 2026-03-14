"use client";

import { createContext, useCallback, useContext, useEffect, useSyncExternalStore } from "react";

type Theme = "light" | "dark";

interface ThemeContextValue {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: "light",
  toggleTheme: () => {},
});

export function useTheme(): ThemeContextValue {
  return useContext(ThemeContext);
}

let currentTheme: Theme = "light";
const listeners = new Set<() => void>();

function getThemeSnapshot(): Theme {
  return currentTheme;
}

function getServerSnapshot(): Theme {
  return "light";
}

function subscribeToTheme(callback: () => void): () => void {
  listeners.add(callback);
  return () => listeners.delete(callback);
}

function setThemeValue(next: Theme) {
  currentTheme = next;
  document.documentElement.classList.toggle("dark", next === "dark");
  localStorage.setItem("chartora-theme", next);
  for (const listener of listeners) listener();
}

function initTheme() {
  const stored = localStorage.getItem("chartora-theme");
  if (stored === "dark" || stored === "light") {
    currentTheme = stored;
  } else if (
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  ) {
    currentTheme = "dark";
  }
  document.documentElement.classList.toggle("dark", currentTheme === "dark");
}

let initialized = false;

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    if (!initialized) {
      initialized = true;
      initTheme();
      for (const listener of listeners) listener();
    }
  }, []);

  const theme = useSyncExternalStore(subscribeToTheme, getThemeSnapshot, getServerSnapshot);

  const toggleTheme = useCallback(() => {
    setThemeValue(theme === "light" ? "dark" : "light");
  }, [theme]);

  return <ThemeContext.Provider value={{ theme, toggleTheme }}>{children}</ThemeContext.Provider>;
}
