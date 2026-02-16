"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";

interface StepDetailProps {
  output: Record<string, unknown>;
}

export function StepDetail({ output }: StepDetailProps) {
  const [copied, setCopied] = useState(false);
  const json = JSON.stringify(output, null, 2);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(json);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative mt-3 rounded-xl border border-border-subtle bg-surface p-4">
      <button
        onClick={handleCopy}
        className="absolute right-3 top-3 flex h-7 w-7 items-center justify-center rounded-md
                   border border-border-subtle bg-surface-elevated text-text-muted
                   transition-all hover:border-border hover:text-text-secondary
                   active:scale-95"
        aria-label="Copy JSON"
      >
        {copied ? <Check size={12} className="text-success" /> : <Copy size={12} />}
      </button>
      <pre className="overflow-x-auto text-xs leading-relaxed text-text-secondary font-[family-name:var(--font-mono)]">
        {json}
      </pre>
    </div>
  );
}
