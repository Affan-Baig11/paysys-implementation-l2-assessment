# GUI test automation

Start the application from the repository root:

    docker compose up --build

In another Ubuntu terminal:

    cd tests/ui
    npm install
    node ./node_modules/playwright/cli.js install chromium
    node ./node_modules/playwright/cli.js test

The test suite covers operator sign-in, customer creation, successful test-payment submission, transaction lookup, an unknown-customer error, and an invalid API key. Selectors use stable labels and test IDs rather than timing delays. HTML reports are written to playwright-report/ and are ignored by Git.

For CI, run the short smoke journeys on every pull request and release candidate. Add longer multi-browser and seeded-volume regression runs nightly or before a major release.
