import type { Collection, CollectionListResponse, CreateCollection, CreateFinding, Finding, FindingsResponse, OverviewResponse, RadarResponse, SampleAnalysis, SampleDetail, SampleDetailResponse, SamplePage, SimilarSamplesResponse } from "./types";

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = init ? await fetch(path, init) : await fetch(path);
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

function getJson<T>(path: string): Promise<T> { return requestJson<T>(path); }

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

export function getSampleAnalysis(id: string): Promise<SampleAnalysis> { return getJson<SampleAnalysis>(`/api/samples/${id}/analysis`); }
export function getSimilarSamples(id: string): Promise<SimilarSamplesResponse> { return getJson<SimilarSamplesResponse>(`/api/samples/${id}/similar`); }
export function getCollections(): Promise<CollectionListResponse> { return getJson<CollectionListResponse>("/api/collections"); }
export function createCollection(collection: CreateCollection): Promise<Collection> {
  return requestJson<Collection>("/api/collections", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(collection) });
}
export function getFindings(collectionId: number): Promise<FindingsResponse> { return getJson<FindingsResponse>(`/api/collections/${collectionId}/findings`); }

export function createFinding(collectionId: number, finding: CreateFinding): Promise<Finding> {
  return requestJson<Finding>(`/api/collections/${collectionId}/findings`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(finding) });
}

export async function deleteFinding(findingId: number): Promise<void> {
  const response = await fetch(`/api/findings/${findingId}`, { method: "DELETE" });
  if (!response.ok) throw new ApiError(response.status, "Could not delete finding.");
}
