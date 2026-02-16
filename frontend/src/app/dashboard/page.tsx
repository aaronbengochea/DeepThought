"use client";

import { Layers } from "lucide-react";
import { Card } from "@/components/ui/card";
import { PairForm } from "@/components/pairs/pair-form";
import { PairCard } from "@/components/pairs/pair-card";
import { usePairs } from "@/hooks/use-pairs";

export default function DashboardPage() {
  const { data: pairs, isLoading, error } = usePairs();

  const sortedPairs = pairs
    ? [...pairs].sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
    : [];

  return (
    <div className="space-y-10">
      {/* Create Pair */}
      <section>
        <h2 className="font-[family-name:var(--font-display)] text-xl font-bold tracking-tight">
          Create a Pair
        </h2>
        <p className="mt-1 text-sm text-text-secondary">
          Enter two numbers to create a pair for operations.
        </p>
        <Card gradient className="mt-4 max-w-lg">
          <PairForm />
        </Card>
      </section>

      {/* Your Pairs */}
      <section>
        <h2 className="font-[family-name:var(--font-display)] text-xl font-bold tracking-tight">
          Your Pairs
        </h2>
        <p className="mt-1 text-sm text-text-secondary">
          Select a pair to run operations.
        </p>

        {isLoading && (
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="shimmer h-36 rounded-2xl"
              />
            ))}
          </div>
        )}

        {error && (
          <p className="mt-6 text-sm text-danger">
            Failed to load pairs. Please try again.
          </p>
        )}

        {!isLoading && sortedPairs.length === 0 && (
          <div className="mt-6 flex flex-col items-center justify-center rounded-2xl border border-dashed border-border py-12">
            <Layers size={32} className="text-text-muted" />
            <p className="mt-3 text-sm text-text-muted">
              No pairs yet. Create your first one above.
            </p>
          </div>
        )}

        {!isLoading && sortedPairs.length > 0 && (
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {sortedPairs.map((pair) => (
              <PairCard key={pair.pair_id} pair={pair} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
