import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  gradient?: boolean;
}

export function Card({ children, gradient = false, className = "", ...props }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-border-subtle bg-surface-elevated
        p-6 backdrop-blur-sm transition-all duration-300
        ${gradient ? "gradient-border" : ""}
        ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
