import { expect, test } from "@playwright/test";

test("researcher saves and exports an ambiguity finding", async ({ page, request }, testInfo) => {
  const collectionName = `Radar workflow ${testInfo.project.name} ${Date.now()}`;
  const collection = await request.post("/api/collections", { data: { name: collectionName } });
  await expect(collection).toBeOK();

  await page.goto("/radar");
  await page.getByRole("link", { name: /Fixture dog/i }).first().click();
  await expect(page).toHaveURL(/\/samples\/.*\?sort=disagreement/);
  await page.getByRole("link", { name: "← Back to results" }).click();
  await expect(page).toHaveURL("/gallery?sort=disagreement");
  await page.locator(".sample-card").first().click();
  await page.getByRole("combobox", { name: "Collection" }).selectOption({ label: collectionName });
  await page.getByRole("button", { name: "Save finding" }).click();
  await expect(page.getByText(/Saved to/i)).toBeVisible();
  await page.getByRole("link", { name: "Collections" }).click();
  await expect(page.getByRole("region", { name: collectionName }).getByRole("link", { name: "Export CSV" })).toBeVisible();
});
