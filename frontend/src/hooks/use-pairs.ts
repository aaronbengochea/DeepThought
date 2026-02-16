"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Pair, PairCreate } from "@/lib/types";

export function usePairs() {
  return useQuery<Pair[]>({
    queryKey: ["pairs"],
    queryFn: async () => {
      const { data } = await api.get<Pair[]>("/pairs");
      return data;
    },
  });
}

export function useCreatePair() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (pair: PairCreate) => {
      const { data } = await api.post<Pair>("/pairs", pair);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pairs"] });
    },
  });
}
