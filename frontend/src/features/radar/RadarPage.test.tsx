import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { App } from "../../app/App";

const radar = {
  distribution: [
    { name: "0-19", sample_count: 2 },
    { name: "20-39", sample_count: 4 },
    { name: "40-59", sample_count: 6 },
    { name: "60-79", sample_count: 8 },
    { name: "80-100", sample_count: 10 },
  ],
  summary: {
    sample_count: 30,
    mean_disagreement_score: 54.2,
    mean_token_disagreement: 0.46,
    mean_vocabulary_diversity: 0.61,
  },
  outliers: [{
    id: "fixture-dog-1",
    split: "train",
    width: 500,
    height: 375,
    caption_preview: "Fixture dog 1",
    image_url: "/api/samples/fixture-dog-1/image",
    disagreement_score: 92,
    token_disagreement: 0.84,
    vocabulary_diversity: 0.78,
  }],
};

const sample = {
  id: "fixture-dog-1",
  split: "train",
  width: 500,
  height: 375,
  caption_preview: "Fixture dog 1",
  image_url: "/api/samples/fixture-dog-1/image",
  aspect_ratio: 1.33,
  captions: ["Fixture dog 1", "A dog in a fixture"],
};

function routerAt(path: string) {
  return function RouterAt({ children }: { children: React.ReactNode }) {
    window.history.replaceState({}, "", path);
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    return <QueryClientProvider client={queryClient}><BrowserRouter>{children}</BrowserRouter></QueryClientProvider>;
  };
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn((url: string) => Promise.resolve({
    ok: true,
    json: async () => url.includes("/api/samples/") ? { sample } : radar,
  })));
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.history.replaceState({}, "", "/");
});

test("links a Radar outlier to a disagreement-filtered gallery", async () => {
  render(<App />, { wrapper: routerAt("/radar") });

  fireEvent.click(await screen.findByRole("link", { name: /Fixture dog 1/i }));

  expect(window.location.pathname).toBe("/samples/fixture-dog-1");
  expect(window.location.search).toContain("sort=disagreement");
});
