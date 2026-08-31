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
  split_composition: [{ name: "train", sample_count: 24 }, { name: "validation", sample_count: 6 }],
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

test("keeps Radar split, score, and near-duplicate filters in the URL", async () => {
  render(<App />, { wrapper: routerAt("/radar?split=train&min_score=40&max_score=90&near_duplicates_only=true") });

  expect(await screen.findByRole("combobox", { name: "Split" })).toHaveValue("train");
  expect(screen.getByRole("spinbutton", { name: "Minimum disagreement" })).toHaveValue(40);
  expect(screen.getByRole("spinbutton", { name: "Maximum disagreement" })).toHaveValue(90);
  expect(screen.getByRole("checkbox", { name: "Near-duplicate signal only" })).toBeChecked();
  fireEvent.change(screen.getByRole("combobox", { name: "Split" }), { target: { value: "validation" } });

  expect(window.location.search).toBe("?split=validation&min_score=40&max_score=90&near_duplicates_only=true");
});

test("normalizes malformed Radar URL filters before requesting data", async () => {
  render(<App />, { wrapper: routerAt("/radar?split=archive&min_score=not-a-score&max_score=101&near_duplicates_only=1") });

  expect(await screen.findByRole("combobox", { name: "Split" })).toHaveValue("");
  expect(screen.getByRole("spinbutton", { name: "Minimum disagreement" })).toHaveValue(0);
  expect(screen.getByRole("spinbutton", { name: "Maximum disagreement" })).toHaveValue(100);
  expect(screen.getByRole("checkbox", { name: "Near-duplicate signal only" })).not.toBeChecked();
  expect(fetch).toHaveBeenCalledWith("/api/radar");
  expect(window.location.search).toBe("");
});

test("orders valid Radar score bounds from the URL before requesting data", async () => {
  render(<App />, { wrapper: routerAt("/radar?min_score=90&max_score=10") });

  expect(await screen.findByRole("spinbutton", { name: "Minimum disagreement" })).toHaveValue(10);
  expect(screen.getByRole("spinbutton", { name: "Maximum disagreement" })).toHaveValue(90);
  expect(fetch).toHaveBeenCalledWith("/api/radar?min_score=10&max_score=90");
});
