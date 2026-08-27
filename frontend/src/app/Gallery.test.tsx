import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { App } from "./App";

const response = { items: [], total: 0, page: 1, page_size: 30 };

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => response }));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test("waits for a pause before searching as the caption query changes", async () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queryClient}><MemoryRouter initialEntries={["/gallery?q=dog"]}><App /></MemoryRouter></QueryClientProvider>);
  const search = screen.getByRole("textbox", { name: "Caption search" });

  fireEvent.change(search, { target: { value: "bicycle" } });
  expect(fetch).toHaveBeenCalledTimes(1);
  await waitFor(() => expect(fetch).toHaveBeenLastCalledWith("/api/samples?q=bicycle"), { timeout: 500 });
});
