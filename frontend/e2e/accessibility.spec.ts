import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function expectNoSeriousOrCriticalViolations(page: Page) {
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations.filter(({ impact }) => impact === "serious" || impact === "critical")).toEqual([]);
}

for (const path of ["/", "/gallery?q=dog&sort=disagreement", "/radar"]) {
  test(`has no serious or critical accessibility violations on ${path}`, async ({ page }) => {
    await page.goto(path);
    await expect(path === "/radar" ? page.getByRole("heading", { name: "Research Radar" }) : page.getByText(path === "/" ? "155 captions" : "31 samples")).toBeVisible();
    await expectNoSeriousOrCriticalViolations(page);
  });
}

test("has no serious or critical accessibility violations on sample detail", async ({ page }) => {
  await page.goto("/gallery?q=dog");
  await page.locator(".sample-card").first().click();
  await expect(page.locator("main")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Read the annotation set" })).toBeVisible();
  await expectNoSeriousOrCriticalViolations(page);
});

test("keeps gallery controls keyboard reachable", async ({ page }) => {
  await page.goto("/gallery?q=dog");
  const sort = page.getByRole("combobox", { name: "Sort samples" });
  await sort.focus();
  await expect(sort).toBeFocused();
  await sort.selectOption("disagreement");
  await expect(page).toHaveURL("/gallery?q=dog&sort=disagreement");
});

test("keeps primary navigation usable at a mobile width", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile", "This regression covers the mobile header layout.");
  await page.setViewportSize({ width: 320, height: 720 });
  await page.goto("/");

  const header = page.locator(".masthead");
  await expect(header).toBeVisible();
  await expect(header.getByRole("link", { name: "Overview" })).toBeVisible();
  await expect(header.getByRole("link", { name: "Browse samples" })).toBeVisible();
  await expect(header.getByRole("link", { name: "Research Radar" })).toBeVisible();
  expect(await header.evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
});
