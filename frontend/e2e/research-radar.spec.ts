import { expect, test } from "@playwright/test";

test("keeps Radar filter controls shareable", async ({ page }) => {
  await page.goto("/radar");

  await page.getByRole("spinbutton", { name: "Minimum disagreement" }).fill("1");
  await expect(page).toHaveURL("/radar?min_score=1");
  await page.getByRole("checkbox", { name: "Near-duplicate signal only" }).click();
  await expect(page).toHaveURL("/radar?min_score=1&near_duplicates_only=true");
});

test("fresh researcher creates, saves, and exports an ambiguity finding", async ({ page }, testInfo) => {
  const collectionName = `Radar workflow ${testInfo.project.name} ${Date.now()}`;

  await page.goto("/radar");
  await page.getByRole("link", { name: /Fixture dog/i }).first().click();
  await expect(page).toHaveURL(/\/samples\/.*\?sort=disagreement/);
  await page.getByRole("link", { name: "← Back to results" }).click();
  await expect(page).toHaveURL("/gallery?sort=disagreement");
  await page.locator(".sample-card").first().click();
  await page.getByRole("textbox", { name: "New collection name" }).fill(collectionName);
  await page.getByRole("button", { name: "Create collection" }).click();
  await page.getByRole("combobox", { name: "Collection" }).selectOption({ label: collectionName });
  await page.getByRole("button", { name: "Save finding" }).click();
  await expect(page.getByText(/Saved to/i)).toBeVisible();
  await page.getByRole("link", { name: "Collections" }).click();
  await expect(page.getByRole("region", { name: collectionName }).getByRole("link", { name: "Export CSV" })).toBeVisible();
});
