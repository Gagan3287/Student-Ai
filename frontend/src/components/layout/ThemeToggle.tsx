"use client";

import { useTheme } from "next-themes";
import { Sun, Moon } from "lucide-react";
import { useEffect, useState } from "react";

interface ThemeToggleProps {
  /** Compact variant (icon only) for sidebar; default renders a pill */
  compact?: boolean;
}

export default function ThemeToggle({ compact = false }: ThemeToggleProps) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Avoid hydration mismatch — render nothing until client is ready
  useEffect(() => setMounted(true), []);
  if (!mounted) return null;

  const isDark = theme === "dark";
  const toggle = () => setTheme(isDark ? "light" : "dark");

  if (compact) {
    return (
      <button
        id="theme-toggle-compact"
        onClick={toggle}
        aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
        className="w-full flex items-center gap-3 px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent rounded-xl transition-all duration-200"
      >
        {isDark ? (
          <>
            <Sun className="h-4 w-4 text-amber-400" />
            Light Mode
          </>
        ) : (
          <>
            <Moon className="h-4 w-4 text-indigo-400" />
            Dark Mode
          </>
        )}
      </button>
    );
  }

  return (
    <button
      id="theme-toggle-navbar"
      onClick={toggle}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className="relative h-9 w-9 rounded-xl border border-border/60 bg-card/60 hover:bg-accent flex items-center justify-center transition-all duration-200 hover:scale-105"
    >
      <Sun
        className={`h-4 w-4 text-amber-500 absolute transition-all duration-300 ${
          isDark ? "opacity-0 rotate-90 scale-50" : "opacity-100 rotate-0 scale-100"
        }`}
      />
      <Moon
        className={`h-4 w-4 text-indigo-400 absolute transition-all duration-300 ${
          isDark ? "opacity-100 rotate-0 scale-100" : "opacity-0 -rotate-90 scale-50"
        }`}
      />
    </button>
  );
}
