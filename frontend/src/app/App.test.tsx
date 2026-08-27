import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { expect, test } from "vitest";

import { App } from "./App";

test("shows the explorer title and a direct path to browsing samples", () => {
  render(<MemoryRouter><App /></MemoryRouter>);

  expect(screen.getByRole("heading", { level: 1, name: "Flickr8k Explorer" })).toBeVisible();
  for (const link of screen.getAllByRole("link", { name: /browse samples/i })) {
    expect(link).toHaveAttribute("href", "/gallery");
  }
});
