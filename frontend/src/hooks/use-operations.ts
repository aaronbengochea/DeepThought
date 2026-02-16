"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { OperateRequest, OperationLog } from "@/lib/types";

export function useLogs(pairId: string) {
  return useQuery<OperationLog[]>({
    queryKey: ["logs", pairId],
    queryFn: async () => {
      const { data } = await api.get<OperationLog[]>(
        `/pairs/${pairId}/logs`
      );
      return data;
    },
  });
}

export function useOperate(pairId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: OperateRequest) => {
      const { data } = await api.post<OperationLog>(
        `/pairs/${pairId}/operate`,
        request
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["logs", pairId] });
    },
  });
}
