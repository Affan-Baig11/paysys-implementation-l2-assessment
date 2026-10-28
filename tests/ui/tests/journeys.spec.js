const { test, expect } = require("@playwright/test");

const API_KEY = process.env.MINIPAY_API_KEY || "dev-api-key";

test("operator creates a customer, submits a payment, and searches it", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("login-key").fill(API_KEY);
  await page.getByTestId("login-submit").click();
  await expect(page.getByTestId("connection-status")).toHaveText("Connected");

  await page.locator("#customer-ref").fill("UI-" + Date.now());
  await page.locator("#customer-name").fill("Browser Test Customer");
  await page.getByRole("button", { name: "Create customer" }).click();
  await expect(page.locator("#customer-result")).toContainText("Created");
  const customerId = await page.locator("#payment-customer").inputValue();
  expect(Number(customerId)).toBeGreaterThan(0);

  await page.locator("#payment-amount").fill("42.50");
  await page.getByTestId("payment-submit").click();
  await expect(page.locator("#payment-result")).toContainText("SUCCESS");
  await expect(page.locator("#payment-result")).toContainText("42.50");

  const title = await page.locator("#payment-result .result-title").textContent();
  const transactionRef = title.split(" · ")[0];
  await page.locator("#transaction-ref").fill(transactionRef);
  await page.getByRole("button", { name: "Search" }).click();
  await expect(page.locator("#search-result")).toContainText(transactionRef);
  await expect(page.locator("#search-result")).toContainText("Callback attempts: 1");
});

test("operator sees an error for an unknown customer", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("login-key").fill(API_KEY);
  await page.getByTestId("login-submit").click();

  await page.locator("#payment-customer").fill("99999999");
  await page.locator("#payment-amount").fill("10.00");
  await page.getByTestId("payment-submit").click();
  await expect(page.getByTestId("notice")).toContainText("Customer not found");
});

test("invalid API key is rejected", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("login-key").fill("not-a-valid-key");
  await page.getByTestId("login-submit").click();
  await expect(page.getByTestId("notice")).toContainText("Invalid or missing API key");
  await expect(page.getByTestId("connection-status")).toHaveText("Signed out");
});
