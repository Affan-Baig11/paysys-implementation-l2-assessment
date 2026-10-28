const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./tests",
  timeout: 30000,
  expect: { timeout: 5000 },
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  use: {
    baseURL: process.env.MINIPAY_BASE_URL || "http://127.0.0.1:8080",
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
});
