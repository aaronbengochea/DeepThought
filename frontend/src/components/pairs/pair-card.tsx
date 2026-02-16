"use client";

import { useRouter } from "next/navigation";
import { ChevronRight } from "lucide-react";
import type { Pair } from "@/lib/types";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function PairCard({ pair }: { pair: Pair }) {
  const router = useRouter();

  return (
    <button
      onClick={() => router.push(`/pairs/${pair.pair_id}`)}
      className="gradient-border group w-full rounded-2xl border border-border-subtle
                 bg-surface-elevated p-5 text-left transition-all duration-300
                 hover:scale-[1.02] hover:shadow-lg hover:shadow-accent/5
                 active:scale-[0.99]"
    >
      {/* Numbers */}
      <div className="mb-4 flex items-center gap-3">
        <div className="flex-1">
          <span className="block text-xs font-medium uppercase tracking-wider text-text-muted">
            Val 1
          </span>
          <span className="font-[family-name:var(--font-display)] text-2xl font-bold text-text-primary">
            {pair.val1}
          </span>
        </div>

        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-muted">
          <span className="text-sm font-bold text-accent">&</span>
        </div>

        <div className="flex-1 text-right">
          <span className="block text-xs font-medium uppercase tracking-wider text-text-muted">
            Val 2
          </span>
          <span className="font-[family-name:var(--font-display)] text-2xl font-bold text-text-primary">
            {pair.val2}
          </span>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between border-t border-border-subtle pt-3">
        <span className="text-xs text-text-muted">{formatDate(pair.created_at)}</span>
        <ChevronRight
          size={14}
          className="text-text-muted transition-transform duration-200 group-hover:translate-x-0.5 group-hover:text-accent"
        />
      </div>
    </button>
  );
}
