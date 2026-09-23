import { test, expect } from "@playwright/test";
import path from "node:path";

test("jury journey: upload, recommendation, completion, refresh and HR", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /Your next chapter/ }),
  ).toBeVisible();
  await page.getByRole("link", { name: "HR Dashboard" }).click();
  await page.getByRole("button", { name: "Open workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Growth, across the team." }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Manage dataset" }).click();
  await page
    .getByLabel("Dataset files")
    .setInputFiles(
      [
        "employees.json",
        "events.json",
        "skills.json",
        "activity_history.csv",
      ].map((n) => path.resolve("../data/sample", n)),
    );
  await page.getByRole("button", { name: "Validate & load dataset" }).click();
  await expect(
    page.getByRole("heading", { name: "Dataset loaded successfully" }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Upload dataset", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Switch workspace/ }).click();
  await page.getByRole("button", { name: "Open workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Recommended for you" }),
  ).toBeVisible();
  await page.locator("summary").first().click();
  await expect(page.locator("details[open]")).toContainText("Target:");
  await page.screenshot({
    path: "test-results/employee-desktop.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "View Details" }).first().click();
  await expect(
    page.getByRole("heading", { name: "Why this recommendation?" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Complete Activity", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Activity completed.");
  await expect(
    page.getByRole("button", { name: "Completed", exact: true }),
  ).toBeDisabled();
  await page.getByRole("link", { name: "Back to overview" }).click();
  await expect(
    page.getByRole("heading", { name: "Recommended for you" }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Career trajectory", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "See the path ahead." }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Activity library", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Available activities" }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("link", { name: "Overview", exact: true }).click();
  await expect(page.getByText("Preparing your workspace…")).toBeHidden();
  await expect(
    page.getByRole("heading", { name: "Recommended for you" }),
  ).toBeVisible();
  await expect(page.locator(".recommendation").first()).toBeVisible();
  await page.waitForLoadState("networkidle");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "test-results/employee-mobile.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: /Switch workspace/ }).click();
  await page.getByRole("button", { name: "HR workspace", exact: true }).click();
  await page.getByRole("button", { name: "Open workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Employee development overview" }),
  ).toBeVisible();
  await page.setViewportSize({ width: 1440, height: 1050 });
  await page.screenshot({
    path: "test-results/hr-desktop.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});

test("jury can add profiles without replacing the catalog", async ({
  page,
}) => {
  await page.goto("/login?role=hr");
  await page.getByRole("button", { name: "Open workspace" }).click();
  await page.getByRole("link", { name: "Manage dataset" }).click();
  await page.getByLabel("Import mode").selectOption("append");
  await page
    .getByLabel("Dataset files")
    .setInputFiles(
      ["employees.json", "activity_history.csv"].map((name) =>
        path.resolve("../data/jury-example", name),
      ),
    );
  await page.getByRole("button", { name: "Validate & load dataset" }).click();
  await expect(
    page.getByRole("heading", { name: "Dataset loaded successfully" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Explore HR dashboard" }).click();
  await expect(
    page.getByRole("cell", { name: "JURY-DESIGN", exact: false }).first(),
  ).toBeVisible();
  await page.getByRole("button", { name: /Switch workspace/ }).click();
  await page
    .getByLabel("Employee", { exact: true })
    .selectOption("JURY-DESIGN");
  await page.getByRole("button", { name: "Open workspace" }).click();
  await expect(page.locator(".recommendation").first()).toContainText(
    "System Design Workshop",
  );
  await expect(page.locator(".recommendation").first()).not.toContainText(
    "Public Speaking Workshop",
  );
});
