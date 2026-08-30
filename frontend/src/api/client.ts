import type { OverviewResponse, RadarResponse, SampleDetail, SampleDetailResponse, SamplePage } from "./types";

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    let message = "Could not load data.";
    try {
      const payload: unknown = await response.json();
      if (typeof payload === "object" && payload !== null && "detail" in payload && typeof payload.detail === "string") {
        message = payload.detail;
      }
    } catch {
      // Responses without a JSON error body retain the generic message.
    }
    throw new ApiError(response.status, message);
  }
  return response.json() as Promise<T>;
}

export function getOverview(): Promise<OverviewResponse> {
  return getJson<OverviewResponse>("/api/overview");
}

export function getRadar(params: URLSearchParams): Promise<RadarResponse> {
  const query = params.toString();
  return getJson<RadarResponse>(`/api/radar${query ? `?${query}` : ""}`);
}

export function getSamples(params: URLSearchParams): Promise<SamplePage> {
  return getJson<SamplePage>(`/api/samples?${params}`);
}

export async function getSample(id: string): Promise<SampleDetail> {
  const payload = await getJson<SampleDetailResponse>(`/api/samples/${id}`);
  return payload.sample;
}
