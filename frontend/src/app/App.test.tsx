import { cleanup, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { App } from "./App";

const overview = {
  splits: [
    { name: "train", sample_count: 6_000 },
    { name: "validation", sample_count: 1_000 },
    { name: "test", sample_count: 1_000 },
  ],
  captions: {
    total: 40_000,
    mean_word_count: 10.2,
    top_terms: [{ term: "dog", count: 878 }, { term: "woman", count: 612 }],
  },
  aspect_ratio_bins: [
    { name: "portrait", sample_count: 1_500 },
    { name: "square", sample_count: 500 },
    { name: "landscape", sample_count: 6_000 },
  ],
};

function renderApp() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queryClient}><MemoryRouter><App /></MemoryRouter></QueryClientProvider>);
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => overview }));
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("renders split totals, top terms, and aspect ratio metrics from the overview response", async () => {
  renderApp();

  expect(await screen.findByRole("heading", { level: 1, name: "Flickr8k Explorer" })).toBeVisible();
  expect(await screen.findByText("Train 6,000 samples")).toBeVisible();
  expect(screen.getByText("Validation 1,000 samples")).toBeVisible();
  expect(screen.getByText("40,000 captions")).toBeVisible();
  expect(screen.getByRole("link", { name: "dog 878" })).toHaveAttribute("href", "/gallery?q=dog");
  expect(screen.getByText("Landscape 6,000 samples")).toBeVisible();
  for (const link of screen.getAllByRole("link", { name: /browse samples/i })) {
    expect(link).toHaveAttribute("href", "/gallery");
  }
});

test("turns a missing-dataset response into import guidance", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: false,
    status: 409,
    json: async () => ({ detail: "Dataset is not imported." }),
  }));

  renderApp();

  expect(await screen.findByRole("alert")).toHaveTextContent("Import the dataset before browsing.");
});
