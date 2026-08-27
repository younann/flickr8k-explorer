import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { App } from "../../app/App";

const response = { items: [], total: 90, page: 2, page_size: 30 };

function LocationDisplay() {
  const location = useLocation();
  return <output>{`${location.pathname}${location.search}`}</output>;
}

function renderGallery(initialEntry: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queryClient}><MemoryRouter initialEntries={[initialEntry]}><App /><LocationDisplay /></MemoryRouter></QueryClientProvider>);
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => response }));
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("clearing filters removes the caption query and split from the URL", async () => {
  renderGallery("/gallery?q=dog&split=train&page=2");

  await screen.findByRole("button", { name: "Clear" });
  fireEvent.click(screen.getByRole("button", { name: "Clear" }));

  expect(screen.getByRole("textbox", { name: "Caption search" })).toHaveValue("");
  expect(screen.getByRole("combobox", { name: "Split" })).toHaveValue("");
  expect(screen.getByText("/gallery")).toBeVisible();
});

test("next page preserves filters and updates only the page", async () => {
  renderGallery("/gallery?q=dog&split=train&page=2");

  await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/samples?q=dog&split=train&page=2"));
  fireEvent.click(await screen.findByRole("button", { name: "Next page" }));

  expect(screen.getByText("/gallery?q=dog&split=train&page=3")).toBeVisible();
});

test("shows a debounce indicator before requesting a new caption query", async () => {
  renderGallery("/gallery?q=dog");
  const search = await screen.findByRole("textbox", { name: "Caption search" });
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));

  fireEvent.change(search, { target: { value: "bicycle" } });

  expect(screen.getByText("Waiting to update search…")).toBeVisible();
  expect(fetch).toHaveBeenCalledTimes(1);
});
