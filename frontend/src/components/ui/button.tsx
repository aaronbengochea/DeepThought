import type { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
  children: ReactNode;
}

export function Button({
  variant = "primary",
  size = "md",
  isLoading = false,
  children,
  className = "",
  disabled,
  ...props
}: ButtonProps) {
  const base = `relative inline-flex items-center justify-center font-medium
    rounded-xl transition-all duration-200 active:scale-[0.97]
    disabled:opacity-50 disabled:pointer-events-none`;

  const variants = {
    primary: `bg-accent text-white hover:bg-accent-hover
      shadow-[0_0_20px_rgba(56,189,248,0.15)]
      hover:shadow-[0_0_30px_rgba(56,189,248,0.25)]`,
    secondary: `border border-border bg-surface-elevated text-text-primary
      hover:border-accent/30 hover:bg-accent-muted`,
    ghost: `text-text-secondary hover:text-text-primary hover:bg-surface-elevated`,
  };

  const sizes = {
    sm: "h-8 px-3 text-sm gap-1.5",
    md: "h-10 px-5 text-sm gap-2",
    lg: "h-12 px-7 text-base gap-2.5",
  };

  return (
    <button
      className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <svg
          className="h-4 w-4 animate-spin"
          viewBox="0 0 24 24"
          fill="none"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="3"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      )}
      {children}
    </button>
  );
}
