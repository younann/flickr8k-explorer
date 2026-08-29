import { expect, test } from "@playwright/test";

test("presents pagination as a styled control bar", async ({ page }) => {
  await page.goto("/gallery");

  const pagination = page.getByRole("navigation", { name: "Pagination" });
  await expect(pagination).toHaveCSS("display", "flex");
  await expect(page.getByRole("button", { name: "Next page" })).toHaveCSS("background-color", "rgb(23, 32, 58)");
});

test("searches fixture samples, returns from detail, paginates, and shows an empty state", async ({ page }) => {
  await page.goto("/gallery");

  const search = page.getByRole("textbox", { name: "Caption search" });
  await search.fill("dog");
  await expect(page).toHaveURL("/gallery?q=dog");
  await expect(page.getByText("31 samples")).toBeVisible();

  const firstResult = page.locator(".sample-card").first();
  await expect(firstResult).toContainText("Fixture dog 1 runs.");
  await firstResult.click();
  await expect(page).toHaveURL(/\/samples\/.*\?q=dog/);

  await page.getByRole("link", { name: "← Back to results" }).click();
  await expect(page).toHaveURL("/gallery?q=dog");
  await expect(search).toHaveValue("dog");

  await page.getByRole("button", { name: "Next page" }).click();
  await expect(page).toHaveURL("/gallery?q=dog&page=2");
  await expect(page.getByText("Page 2")).toBeVisible();

  await search.fill("unfindable");
  await expect(page.getByText("No local samples match this query. Try fewer words or clear the split.")).toBeVisible();
});
