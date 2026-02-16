"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCreatePair } from "@/hooks/use-pairs";

export function PairForm() {
  const [val1, setVal1] = useState("");
  const [val2, setVal2] = useState("");
  const [showSuccess, setShowSuccess] = useState(false);
  const createPair = useCreatePair();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    const v1 = parseFloat(val1);
    const v2 = parseFloat(val2);
    if (isNaN(v1) || isNaN(v2)) return;

    createPair.mutate(
      { val1: v1, val2: v2 },
      {
        onSuccess: () => {
          setVal1("");
          setVal2("");
          setShowSuccess(true);
          setTimeout(() => setShowSuccess(false), 2000);
        },
      }
    );
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Value 1"
          type="number"
          step="any"
          placeholder="0"
          value={val1}
          onChange={(e) => setVal1(e.target.value)}
          required
        />
        <Input
          label="Value 2"
          type="number"
          step="any"
          placeholder="0"
          value={val2}
          onChange={(e) => setVal2(e.target.value)}
          required
        />
      </div>

      <Button
        type="submit"
        isLoading={createPair.isPending}
        className="w-full"
      >
        <Plus size={16} />
        Create Pair
      </Button>

      {showSuccess && (
        <p className="text-center text-sm text-success animate-in fade-in">
          Pair created successfully
        </p>
      )}
    </form>
  );
}
