import type { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export function Input({ label, error, className = "", id, ...props }: InputProps) {
  const inputId = id || label.toLowerCase().replace(/\s+/g, "-");

  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={inputId}
        className="text-sm font-medium text-text-secondary"
      >
        {label}
      </label>
      <input
        id={inputId}
        className={`h-11 w-full rounded-xl border border-border bg-surface-elevated
          px-4 text-sm text-text-primary placeholder:text-text-muted
          transition-all duration-200
          focus:border-accent/50 focus:outline-none focus:ring-2 focus:ring-accent/20
          hover:border-border
          ${error ? "border-danger/50 focus:border-danger/50 focus:ring-danger/20" : ""}
          ${className}`}
        {...props}
      />
      {error && <p className="text-xs text-danger">{error}</p>}
    </div>
  );
}
