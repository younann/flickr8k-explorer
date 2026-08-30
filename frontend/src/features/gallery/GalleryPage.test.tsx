import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { App } from "../../app/App";

const pageOneResponse = {
  items: [{ id: "sample-one", split: "train", width: 4, height: 3, caption_preview: "Page one sample", image_url: "/api/samples/sample-one/image" }],
  total: 90,
  page: 1,
  page_size: 30,
};
const pageTwoResponse = {
  items: [{ id: "sample-two", split: "train", width: 6, height: 4, caption_preview: "Page two sample", image_url: "/api/samples/sample-two/image" }],
  total: 90,
  page: 2,
  page_size: 30,
};

function LocationDisplay() {
  const location = useLocation();
  return <output>{`${location.pathname}${location.search}`}</output>;
}

function renderGallery(initialEntry: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queryClient}><MemoryRouter initialEntries={[initialEntry]}><App /><LocationDisplay /></MemoryRouter></QueryClientProvider>);
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn((url: string) => Promise.resolve({
    ok: true,
    json: async () => new URL(url, "http://localhost").searchParams.get("page") === "2" ? pageTwoResponse : pageOneResponse,
  })));
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
  expect(await screen.findByText("Page two sample")).toBeVisible();
  expect(screen.queryByText("Page one sample")).not.toBeInTheDocument();
  fireEvent.click(await screen.findByRole("button", { name: "Next page" }));

  expect(screen.getByText("/gallery?q=dog&split=train&page=3")).toBeVisible();
});

test("keeps disagreement sorting while changing gallery page", async () => {
  renderGallery("/gallery?sort=disagreement");

  expect(await screen.findByRole("combobox", { name: "Sort samples" })).toHaveValue("disagreement");
  await screen.findByText("Page one sample");
  fireEvent.click(screen.getByRole("button", { name: "Next page" }));

  expect(screen.getByText("/gallery?sort=disagreement&page=2")).toBeVisible();
});

test("shows a debounce indicator before requesting a new caption query", async () => {
  renderGallery("/gallery?q=dog");
  const search = await screen.findByRole("textbox", { name: "Caption search" });
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));

  fireEvent.change(search, { target: { value: "bicycle" } });

  expect(screen.getByText("Waiting to update search…")).toBeVisible();
  expect(fetch).toHaveBeenCalledTimes(1);
});
