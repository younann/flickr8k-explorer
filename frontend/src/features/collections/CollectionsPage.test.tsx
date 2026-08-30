import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { App } from "../../app/App";
import { DetailPage } from "../detail/DetailPage";

const sample = {
  id: "fixture-dog-1",
  split: "train",
  width: 500,
  height: 375,
  caption_preview: "A dog runs through grass",
  image_url: "/api/samples/fixture-dog-1/image",
  aspect_ratio: 1.33,
  captions: [
    "A dog runs through grass",
    "A brown dog runs",
    "A dog is outside",
    "The animal runs over grass",
    "A puppy sprints on a field",
  ],
};

const analysis = {
  sample_id: sample.id,
  disagreement_score: 82,
  token_disagreement: 0.71,
  vocabulary_diversity: 0.68,
  mean_caption_length: 5.2,
  caption_length_spread: 2.4,
  differing_tokens: ["brown", "outside", "puppy", "sprints"],
};

const collections = [{
  id: 1,
  name: "Action ambiguity examples",
  finding_count: 1,
  created_at: "2026-08-29T10:00:00Z",
  updated_at: "2026-08-29T10:00:00Z",
}];

const findings = [{
  id: 4,
  collection_id: 1,
  sample_id: sample.id,
  tags: ["action", "ambiguity"],
  note: "Captions disagree about motion.",
  created_at: "2026-08-29T10:00:00Z",
  updated_at: "2026-08-29T10:00:00Z",
}];

function routerAt(path: string) {
  return function RouterAt({ children }: { children: React.ReactNode }) {
    window.history.replaceState({}, "", path);
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    return <QueryClientProvider client={queryClient}><BrowserRouter>{children}</BrowserRouter></QueryClientProvider>;
  };
}

function response(payload: unknown, status = 200) {
  return { ok: status >= 200 && status < 300, status, json: async () => payload };
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
    if (url === `/api/samples/${sample.id}`) return Promise.resolve(response({ sample }));
    if (url.endsWith("/analysis")) return Promise.resolve(response(analysis));
    if (url.endsWith("/similar")) return Promise.resolve(response({ items: [] }));
    if (url === "/api/collections") return Promise.resolve(response({ items: collections }));
    if (url === "/api/collections/1/findings" && init?.method === "POST") return Promise.resolve(response(findings[0], 201));
    if (url === "/api/collections/1/findings") return Promise.resolve(response({ items: findings }));
    if (url === "/api/findings/4" && init?.method === "DELETE") return Promise.resolve({ ok: true, status: 204, json: async () => undefined });
    return Promise.resolve(response({ detail: "Not found" }, 404));
  }));
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.history.replaceState({}, "", "/");
});

test("saves a tagged finding from evidence triage", async () => {
  render(<Routes><Route path="/samples/:id" element={<DetailPage />} /></Routes>, { wrapper: routerAt(`/samples/${sample.id}`) });

  fireEvent.change(await screen.findByLabelText("Collection"), { target: { value: "1" } });
  fireEvent.change(screen.getByLabelText("Tags"), { target: { value: "action, ambiguity" } });
  fireEvent.change(screen.getByLabelText("Note"), { target: { value: "Different wording for the action." } });
  fireEvent.click(screen.getByRole("button", { name: "Save finding" }));

  expect(await screen.findByRole("status")).toHaveTextContent("Saved to Action ambiguity examples");
  expect(fetch).toHaveBeenCalledWith("/api/collections/1/findings", expect.objectContaining({
    method: "POST",
    body: JSON.stringify({
      sample_id: sample.id,
      tags: ["action", "ambiguity"],
      note: "Different wording for the action.",
    }),
  }));
});

test("explains local evidence without overstating visual-neighbour or token signals", async () => {
  render(<Routes><Route path="/samples/:id" element={<DetailPage />} /></Routes>, { wrapper: routerAt(`/samples/${sample.id}`) });

  expect(await screen.findByText("Caption-length standard deviation")).toBeVisible();
  expect(screen.getByText(/strict subset of these captions/i)).toBeVisible();
  expect(screen.getByText(/not semantic similarity/i)).toBeVisible();
  expect(screen.getByText("brown", { selector: "mark" })).toBeVisible();
  expect(screen.queryByText("dog", { selector: "mark" })).not.toBeInTheDocument();
});

test("lists findings with deletion controls and direct export links", async () => {
  render(<App />, { wrapper: routerAt("/collections") });

  expect(await screen.findByRole("heading", { name: "Collections" })).toBeVisible();
  expect(await screen.findByText("Captions disagree about motion.")).toBeVisible();
  expect(screen.getByRole("link", { name: "Export CSV" })).toHaveAttribute("href", "/api/collections/1/export?format=csv");
  expect(screen.getByRole("link", { name: "Export JSON" })).toHaveAttribute("href", "/api/collections/1/export?format=json");

  fireEvent.click(screen.getByRole("button", { name: "Delete finding 4" }));

  expect(await screen.findByRole("status")).toHaveTextContent("Finding deleted");
});

test("creates a local collection from the empty collections page", async () => {
  vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
    if (url === "/api/collections" && init?.method === "POST") return Promise.resolve(response({ ...collections[0], name: "Fresh review", finding_count: 0 }, 201));
    if (url === "/api/collections") return Promise.resolve(response({ items: [] }));
    return Promise.resolve(response({ detail: "Not found" }, 404));
  }));
  render(<App />, { wrapper: routerAt("/collections") });

  fireEvent.change(await screen.findByRole("textbox", { name: "New collection name" }), { target: { value: "Fresh review" } });
  fireEvent.click(screen.getByRole("button", { name: "Create collection" }));

  expect(await screen.findByRole("heading", { name: "Fresh review" })).toBeVisible();
  expect(screen.getByRole("status")).toHaveTextContent("Created Fresh review");
});
