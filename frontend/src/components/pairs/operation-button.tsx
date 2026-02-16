"use client";

import type { ReactNode } from "react";

interface OperationButtonProps {
  icon: ReactNode;
  label: string;
  color: "blue" | "green" | "violet" | "amber";
  onClick: () => void;
  isLoading: boolean;
  disabled: boolean;
}

const colorMap = {
  blue: {
    bg: "from-sky-500 to-blue-600",
    hover: "hover:from-sky-400 hover:to-blue-500",
    shadow: "shadow-sky-500/20 hover:shadow-sky-500/30",
    ring: "focus-visible:ring-sky-400",
  },
  green: {
    bg: "from-emerald-500 to-green-600",
    hover: "hover:from-emerald-400 hover:to-green-500",
    shadow: "shadow-emerald-500/20 hover:shadow-emerald-500/30",
    ring: "focus-visible:ring-emerald-400",
  },
  violet: {
    bg: "from-violet-500 to-purple-600",
    hover: "hover:from-violet-400 hover:to-purple-500",
    shadow: "shadow-violet-500/20 hover:shadow-violet-500/30",
    ring: "focus-visible:ring-violet-400",
  },
  amber: {
    bg: "from-amber-500 to-orange-600",
    hover: "hover:from-amber-400 hover:to-orange-500",
    shadow: "shadow-amber-500/20 hover:shadow-amber-500/30",
    ring: "focus-visible:ring-amber-400",
  },
};

export function OperationButton({
  icon,
  label,
  color,
  onClick,
  isLoading,
  disabled,
}: OperationButtonProps) {
  const c = colorMap[color];

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`group flex flex-col items-center gap-2 rounded-2xl bg-gradient-to-br
        ${c.bg} ${c.hover} ${c.shadow} ${c.ring}
        px-5 py-4 text-white shadow-lg transition-all duration-200
        active:scale-[0.96] disabled:opacity-50 disabled:pointer-events-none`}
    >
      {isLoading ? (
        <svg className="h-6 w-6 animate-spin" viewBox="0 0 24 24" fill="none">
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
      ) : (
        <span className="text-2xl">{icon}</span>
      )}
      <span className="text-xs font-semibold uppercase tracking-wider">
        {label}
      </span>
    </button>
  );
}
