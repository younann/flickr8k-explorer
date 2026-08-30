import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { getRadar } from "../../api/client";
import type { RadarResponse } from "../../api/types";

export function useRadar(params: URLSearchParams): UseQueryResult<RadarResponse> {
  const search = params.toString();
  return useQuery({
    queryKey: ["radar", search],
    queryFn: () => getRadar(new URLSearchParams(search)),
    staleTime: 60_000,
  });
}
