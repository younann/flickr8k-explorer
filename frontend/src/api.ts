export type Sample = { id: string; split: string; width: number; height: number; caption_preview: string; image_url: string };
export type SampleDetail = Sample & { aspect_ratio: number; captions: string[] };

export async function getSamples(params: URLSearchParams): Promise<{ items: Sample[]; total: number; page: number; page_size: number }> {
  const response = await fetch(`/api/samples?${params}`);
  if (!response.ok) throw new Error(response.status === 409 ? "Import the dataset before browsing." : "Could not load samples.");
  return response.json();
}

export async function getSample(id: string): Promise<SampleDetail> {
  const response = await fetch(`/api/samples/${id}`);
  if (!response.ok) throw new Error("Could not load this sample.");
  const payload = await response.json();
  return payload.sample;
}
