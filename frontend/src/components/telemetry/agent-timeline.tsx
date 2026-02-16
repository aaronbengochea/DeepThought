"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { StepDetail } from "./step-detail";
import type { AgentStepOutput } from "@/lib/types";

const AGENT_META: Record<string, { label: string; description: string }> = {
  orchestrator: {
    label: "Orchestrator",
    description: "Plans the operation and determines execution strategy",
  },
  execution: {
    label: "Execution",
    description: "Runs the mathematical operation with tool calls",
  },
  verification: {
    label: "Verification",
    description: "Validates the result matches expected output",
  },
  response: {
    label: "Response",
    description: "Formats the final result for display",
  },
};

function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

interface AgentTimelineProps {
  steps: AgentStepOutput[];
  success: boolean;
}

export function AgentTimeline({ steps, success }: AgentTimelineProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const toggle = (i: number) =>
    setExpandedIndex(expandedIndex === i ? null : i);

  return (
    <div className="relative pl-6">
      {/* Vertical line */}
      <div
        className="absolute left-[11px] top-3 bottom-3 w-px"
        style={{
          background: success
            ? "linear-gradient(to bottom, #34d399, #38bdf8)"
            : "linear-gradient(to bottom, #f87171, #fb923c)",
        }}
      />

      <div className="space-y-1">
        {steps.map((step, i) => {
          const meta = AGENT_META[step.agent_name] ?? {
            label: step.agent_name,
            description: "",
          };
          const isExpanded = expandedIndex === i;
          const isLast = i === steps.length - 1;

          return (
            <div key={i}>
              <button
                onClick={() => toggle(i)}
                className="group relative flex w-full items-start gap-3 rounded-xl px-2 py-2.5
                           text-left transition-colors hover:bg-surface-elevated"
              >
                {/* Node circle */}
                <div
                  className={`relative z-10 mt-0.5 flex h-[22px] w-[22px] shrink-0 items-center
                    justify-center rounded-full border-2 -ml-8
                    ${
                      isLast && success
                        ? "border-success bg-success/20"
                        : isLast && !success
                          ? "border-danger bg-danger/20"
                          : "border-accent bg-accent/10"
                    }`}
                >
                  <div
                    className={`h-2 w-2 rounded-full ${
                      isLast && success
                        ? "bg-success"
                        : isLast && !success
                          ? "bg-danger"
                          : "bg-accent"
                    }`}
                  />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-text-primary">
                      {meta.label}
                    </span>
                    <span className="rounded-md bg-surface px-2 py-0.5 text-[10px] font-mono text-text-muted border border-border-subtle">
                      {formatDuration(step.duration_ms)}
                    </span>
                  </div>
                  <p className="mt-0.5 text-xs text-text-muted">
                    {meta.description}
                  </p>
                </div>

                {/* Expand icon */}
                <div className="mt-1 text-text-muted transition-colors group-hover:text-text-secondary">
                  {isExpanded ? (
                    <ChevronDown size={14} />
                  ) : (
                    <ChevronRight size={14} />
                  )}
                </div>
              </button>

              {/* Expanded detail */}
              {isExpanded && (
                <div className="ml-0 pb-2">
                  <StepDetail output={step.output} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
