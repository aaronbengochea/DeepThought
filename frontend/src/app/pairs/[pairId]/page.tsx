"use client";

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  CheckCircle2,
  Divide,
  Minus,
  Plus,
  X,
  XCircle,
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { useLogs, useOperate } from "@/hooks/use-operations";
import { OperationButton } from "@/components/pairs/operation-button";
import { AgentTimeline } from "@/components/telemetry/agent-timeline";
import type { OperationLog } from "@/lib/types";

const OPERATIONS = [
  { key: "add", label: "Add", icon: <Plus size={20} />, color: "blue" as const },
  { key: "subtract", label: "Subtract", icon: <Minus size={20} />, color: "green" as const },
  { key: "multiply", label: "Multiply", icon: <X size={20} />, color: "violet" as const },
  { key: "divide", label: "Divide", icon: <Divide size={20} />, color: "amber" as const },
];

const OP_SYMBOLS: Record<string, string> = {
  add: "+",
  subtract: "−",
  multiply: "×",
  divide: "÷",
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function PairOperationsPage({
  params,
}: {
  params: Promise<{ pairId: string }>;
}) {
  const { pairId } = use(params);
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const { data: logs, isLoading: logsLoading } = useLogs(pairId);
  const operate = useOperate(pairId);
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);
  const [activeOp, setActiveOp] = useState<string | null>(null);

  if (authLoading) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
      </div>
    );
  }

  if (!user) {
    router.replace("/auth");
    return null;
  }

  const handleOperate = (operation: string) => {
    setActiveOp(operation);
    operate.mutate(
      { operation },
      {
        onSettled: () => setActiveOp(null),
      }
    );
  };

  const sortedLogs = logs
    ? [...logs].sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
    : [];

  // Extract pair values from the most recent log or show pairId
  const latestLog = sortedLogs[0];

  return (
    <div className="min-h-dvh bg-[var(--gradient-surface)]">
      {/* Nav */}
      <div className="mx-auto max-w-4xl px-6 py-8">
        {/* Back button */}
        <button
          onClick={() => router.push("/dashboard")}
          className="mb-6 flex items-center gap-2 text-sm text-text-secondary
                     transition-colors hover:text-text-primary"
        >
          <ArrowLeft size={16} />
          Back to Dashboard
        </button>

        {/* Pair header */}
        <div className="mb-8">
          <h1 className="font-[family-name:var(--font-display)] text-2xl font-bold tracking-tight">
            Pair Operations
          </h1>
          <p className="mt-1 text-sm text-text-secondary">
            Pair ID: {pairId}
          </p>
        </div>

        {/* Operation buttons */}
        <div className="mb-10 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {OPERATIONS.map((op) => (
            <OperationButton
              key={op.key}
              icon={op.icon}
              label={op.label}
              color={op.color}
              onClick={() => handleOperate(op.key)}
              isLoading={activeOp === op.key}
              disabled={activeOp !== null}
            />
          ))}
        </div>

        {/* Operation history */}
        <div>
          <h2 className="font-[family-name:var(--font-display)] text-xl font-bold tracking-tight">
            Operation History
          </h2>
          <p className="mt-1 text-sm text-text-secondary">
            Click an entry to view the agent telemetry timeline.
          </p>

          {logsLoading && (
            <div className="mt-6 space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="shimmer h-20 rounded-2xl" />
              ))}
            </div>
          )}

          {!logsLoading && sortedLogs.length === 0 && (
            <div className="mt-6 flex flex-col items-center justify-center rounded-2xl border border-dashed border-border py-12">
              <p className="text-sm text-text-muted">
                No operations yet. Click a button above to run one.
              </p>
            </div>
          )}

          {!logsLoading && sortedLogs.length > 0 && (
            <div className="mt-6 space-y-3">
              {sortedLogs.map((log) => (
                <LogEntry
                  key={log.log_id}
                  log={log}
                  isExpanded={expandedLogId === log.log_id}
                  onToggle={() =>
                    setExpandedLogId(
                      expandedLogId === log.log_id ? null : log.log_id
                    )
                  }
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function LogEntry({
  log,
  isExpanded,
  onToggle,
}: {
  log: OperationLog;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const symbol = OP_SYMBOLS[log.operation] ?? log.operation;

  return (
    <div
      className={`rounded-2xl border transition-all duration-200 ${
        isExpanded
          ? "border-accent/30 bg-surface-elevated"
          : "border-border-subtle bg-surface-elevated/50 hover:border-border"
      }`}
    >
      {/* Summary row */}
      <button
        onClick={onToggle}
        className="flex w-full items-center gap-4 p-4 text-left"
      >
        {/* Operation icon */}
        <div
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-lg font-bold ${
            log.success
              ? "bg-success/10 text-success"
              : "bg-danger/10 text-danger"
          }`}
        >
          {symbol}
        </div>

        {/* Info */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-text-primary capitalize">
              {log.operation}
            </span>
            {log.success ? (
              <CheckCircle2 size={14} className="text-success" />
            ) : (
              <XCircle size={14} className="text-danger" />
            )}
          </div>
          <p className="mt-0.5 text-xs text-text-muted">
            {formatDate(log.created_at)}
          </p>
        </div>

        {/* Result */}
        <span className="font-[family-name:var(--font-mono)] text-sm font-medium text-text-primary">
          {log.result}
        </span>
      </button>

      {/* Expanded timeline */}
      {isExpanded && log.agent_steps.length > 0 && (
        <div className="border-t border-border-subtle px-4 py-4">
          <AgentTimeline steps={log.agent_steps} success={log.success} />
        </div>
      )}
    </div>
  );
}
