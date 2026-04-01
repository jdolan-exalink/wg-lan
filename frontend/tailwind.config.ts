import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // NetLoom Design System v2 — Ubiquiti/Netbird inspired
        // All colors use CSS variables → automatic light/dark switching
        "surface-dim":                "rgb(var(--c-base) / <alpha-value>)",
        "surface-container-lowest":   "rgb(var(--c-surface-low) / <alpha-value>)",
        "surface-container-low":      "rgb(var(--c-surface) / <alpha-value>)",
        "surface-container":          "rgb(var(--c-card) / <alpha-value>)",
        "surface-container-high":     "rgb(var(--c-elevated) / <alpha-value>)",
        "surface-container-highest":  "rgb(var(--c-high) / <alpha-value>)",
        "surface-bright":             "rgb(var(--c-bright) / <alpha-value>)",
        "surface-variant":            "rgb(var(--c-elevated) / <alpha-value>)",
        "surface-tint":               "rgb(var(--c-primary) / <alpha-value>)",
        "background":                 "rgb(var(--c-base) / <alpha-value>)",
        "on-background":              "rgb(var(--c-text) / <alpha-value>)",
        "on-surface":                 "rgb(var(--c-text) / <alpha-value>)",
        "on-surface-variant":         "rgb(var(--c-text-muted) / <alpha-value>)",
        "primary":                    "rgb(var(--c-primary) / <alpha-value>)",
        "primary-container":          "rgb(var(--c-accent) / <alpha-value>)",
        "primary-fixed":              "rgb(var(--c-primary) / <alpha-value>)",
        "primary-fixed-dim":          "rgb(var(--c-primary) / <alpha-value>)",
        "on-primary":                 "rgb(var(--c-on-accent) / <alpha-value>)",
        "on-primary-container":       "rgb(var(--c-on-accent) / <alpha-value>)",
        "on-primary-fixed":           "rgb(var(--c-on-accent) / <alpha-value>)",
        "on-primary-fixed-variant":   "rgb(var(--c-accent) / <alpha-value>)",
        "secondary":                  "rgb(var(--c-text-muted) / <alpha-value>)",
        "secondary-container":        "rgb(var(--c-elevated) / <alpha-value>)",
        "secondary-fixed":            "rgb(var(--c-text-muted) / <alpha-value>)",
        "secondary-fixed-dim":        "rgb(var(--c-text-muted) / <alpha-value>)",
        "on-secondary":               "rgb(var(--c-text) / <alpha-value>)",
        "on-secondary-container":     "rgb(var(--c-text-muted) / <alpha-value>)",
        "on-secondary-fixed":         "rgb(var(--c-text) / <alpha-value>)",
        "on-secondary-fixed-variant": "rgb(var(--c-muted) / <alpha-value>)",
        "tertiary":                   "rgb(var(--c-success) / <alpha-value>)",
        "tertiary-container":         "rgb(var(--c-success-bg) / <alpha-value>)",
        "tertiary-fixed":             "rgb(var(--c-success-text) / <alpha-value>)",
        "tertiary-fixed-dim":         "rgb(var(--c-success) / <alpha-value>)",
        "on-tertiary":                "rgb(var(--c-success-bg) / <alpha-value>)",
        "on-tertiary-container":      "rgb(var(--c-success-text) / <alpha-value>)",
        "on-tertiary-fixed":          "rgb(var(--c-success-bg) / <alpha-value>)",
        "on-tertiary-fixed-variant":  "rgb(var(--c-success) / <alpha-value>)",
        "error":                      "rgb(var(--c-error) / <alpha-value>)",
        "error-container":            "rgb(var(--c-error-bg) / <alpha-value>)",
        "on-error":                   "rgb(var(--c-error-bg) / <alpha-value>)",
        "on-error-container":         "rgb(var(--c-error-text) / <alpha-value>)",
        "outline":                    "rgb(var(--c-muted) / <alpha-value>)",
        "outline-variant":            "rgb(var(--c-border) / <alpha-value>)",
        "inverse-surface":            "rgb(var(--c-text) / <alpha-value>)",
        "inverse-on-surface":         "rgb(var(--c-base) / <alpha-value>)",
        "inverse-primary":            "rgb(var(--c-accent) / <alpha-value>)",
        // shadcn compatibility (still needed for Radix component theming)
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        foreground: "hsl(var(--foreground))",
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      fontFamily: {
        headline: ["Inter", "sans-serif"],
        body: ["Inter", "sans-serif"],
        label: ["Space Grotesk", "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "0.375rem",
        lg: "0.5rem",
        xl: "0.75rem",
        "2xl": "1rem",
        full: "9999px",
      },
      transitionDuration: {
        DEFAULT: "200ms",
      },
    },
  },
  plugins: [],
};

export default config;
