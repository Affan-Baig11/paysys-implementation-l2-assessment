# Browser UI test evidence

Date: 2026-10-28
Application: Docker Compose API and PostgreSQL; browser UI at http://127.0.0.1:8080
Runner: Playwright 1.64.1 with Ubuntu Chromium

Command:

    cd tests/ui
    node ./node_modules/playwright/cli.js test

Result:

    Running 3 tests using 1 worker
      PASS operator creates a customer, submits a payment, and searches it
      PASS operator sees an error for an unknown customer
      PASS invalid API key is rejected
    3 passed (4.4s)

The primary journey signs in, creates a customer, submits a successful mock payment, and searches the generated transaction reference. The other tests verify an unknown-customer error and rejection of an invalid API key. No real payment is sent.
