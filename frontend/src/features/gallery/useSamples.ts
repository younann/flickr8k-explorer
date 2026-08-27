import { keepPreviousData, useQuery, type UseQueryResult } from "@tanstack/react-query";
import { getSamples } from "../../api/client";
import type { SamplePage } from "../../api/types";

export function useSamples(query: URLSearchParams): UseQueryResult<SamplePage> {
  const search = query.toString();
  return useQuery({
    queryKey: ["samples", search],
    queryFn: () => getSamples(new URLSearchParams(search)),
    staleTime: 60_000,
    placeholderData: keepPreviousData,
  });
}
