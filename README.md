# Playwright Java POC

![CI](https://github.com/krishhsubash/PlayWrightJava/actions/workflows/playwright.yml/badge.svg)
<!-- Replace <your-username> after first successful Pages publish if desired -->
[Trends & Flaky History](https://krishhsubash.github.io/PlayWrightJava/extra/trends.html)
[![Flaky Tests](https://img.shields.io/endpoint?url=https%3A%2F%2Fkrishhsubash.github.io%2FPlayWrightJava%2Fbadges%2Fflaky-badge.json)](https://krishhsubash.github.io/PlayWrightJava/extra/trends.html)
[![Failure Rate](https://img.shields.io/endpoint?url=https%3A%2F%2Fkrishhsubash.github.io%2FPlayWrightJava%2Fbadges%2Ffailure-badge.json)](https://krishhsubash.github.io/PlayWrightJava/extra/trends.html)
[![Stability](https://img.shields.io/endpoint?url=https%3A%2F%2Fkrishhsubash.github.io%2FPlayWrightJava%2Fbadges%2Fstability-badge.json)](https://krishhsubash.github.io/PlayWrightJava/extra/trends.html)

Minimal Proof of Concept project using Microsoft Playwright with Java (JUnit 5 + AssertJ) for cross-browser functional UI testing.

## Prerequisites
- Java 17+ (`java -version` to verify)
- Maven 3.8+ (`mvn -version` to verify)
- Internet access (first run downloads browsers)

## Project Structure
```
pom.xml
src
 └── test
     └── java
         └── com.example.tests
             ├── BaseTest.java
             └── ExampleTest.java
```

## Install Playwright Browsers
Playwright downloads browser binaries on first use. You can explicitly install them:
```
mvn -q exec:java -Dexec.classpathScope=test -Dexec.mainClass=com.microsoft.playwright.CLI -Dexec.args="install"
```
If that fails you can rely on first test run (it will auto-download).

## Run Tests
Headless Chromium (default):
```
mvn test
```

Run headed (visible browser window):
```
mvn test -Dheaded=true
```

Choose browser (chromium | firefox | webkit | chrome channel):
```
mvn test -Dbrowser=firefox
mvn test -Dbrowser=webkit
mvn test -Dbrowser=chrome -Dheaded=true
```

Parallel execution (classes level, 4 threads default when enabled):
```
mvn test -Dparallel.tests=classes -Dparallel.threads=4
```

## Example Assertion
`ExampleTest` navigates to https://playwright.dev and asserts the page title contains "Playwright".

## System Properties Summary
| Property | Default   | Description |
|----------|-----------|-------------|
| `browser`| `chromium`| Browser engine (`chromium`, `firefox`, `webkit`, `chrome`) |
| `headed` | `false`   | Set `true` to disable headless mode |
| `trace`  | `false`   | Capture Playwright trace (`playwright-report/traces/*.zip`) |
| `recordVideo` | `false` | Record videos (`playwright-report/videos/`) when true |
| `screenshotOnFail` | `true` | Capture screenshots per test (`playwright-report/screenshots/`) |

## Extending
Create new test classes ending in `Test.java` under `com.example.tests` and extend `BaseTest` if you need a shared page instance.

You can also create separate contexts or pages inside individual tests if isolation is required:
```java
try (BrowserContext ctx = browser.newContext()) {
    Page localPage = ctx.newPage();
    localPage.navigate("https://example.com");
}
```

## Reports / Artifacts
You can enable tracing, videos or screenshots by adjusting context creation in `BaseTest`:
```java
context = browser.newContext(new Browser.NewContextOptions()
    .setRecordVideoDir(Paths.get("playwright-report/videos")));
```
Or simply pass system properties when running tests:
```
mvn test -Dtrace=true -DrecordVideo=true
```
Traces: `playwright show-trace playwright-report/traces/<trace-file>.zip` (install Playwright CLI on local machine if needed).

### Allure Reporting
Allure results are written to `target/allure-results` when tests run.
To generate a local report (after a run):
```
allure serve target/allure-results
```
Or generate static files:
```
allure generate target/allure-results -o target/allure-report --clean
```
Each failed test screenshot is attached automatically (if `screenshotOnFail=true`).

### Test Summary & Flaky Detection
After CI runs, a machine-readable JSON summary is printed and `target/test-summary.md` (uploaded as artifact) lists flaky candidates (tests that both passed and failed in same run across matrix). Script: `scripts/surefire_summary.py`.

## Troubleshooting
- Browser download blocked: set `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` and copy browsers from a machine where they are installed.
- Proxy / corporate SSL: export `NODE_EXTRA_CA_CERTS` pointing to your root CA if downloads fail.
- Clean and retry: `mvn -U clean test -Dbrowser=firefox`.

## CI Browser Caching
GitHub Actions workflow caches downloaded browsers to speed up runs.
- Cache path: `.cache/ms-playwright` (controlled by `PLAYWRIGHT_BROWSERS_PATH` env var)
- Cache key factors: OS + `pom.xml` hash. Updating Playwright version in `pom.xml` naturally busts the cache.
- Local use (optional): set before first test run to reuse between projects:
```
export PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/ms-playwright
mvn test
```
This keeps browsers outside `target` so subsequent clean builds are faster.

## CI Schedule
Weekly scheduled run (Monday 03:00 UTC) refreshes cache and validates browsers with tracing & video enabled.

## Published Report (GitHub Pages)
Main branch publishes merged Allure report + aggregated test summaries to GitHub Pages (after first successful main build). Published URL:
```
https://krishhsubash.github.io/PlayWrightJava/
```
Contains:
- Quality dashboard (`index.html`) linking to charts & badges
- Allure interactive HTML report (now under `/allure/`):
    - https://krishhsubash.github.io/PlayWrightJava/allure/
- `test-summary.md` aggregated across matrix

## Flaky History Persistence
`target/flaky-history.json` accumulates per-run flaky candidate data. CI merges histories and can surface trends over time.
You can download artifacts and inspect:
```
jq '.' target/flaky-history.json
```

## CI Headed / Headless Matrix
The GitHub Actions workflow executes each test run across:
- Browsers: `chromium`, `firefox`, `webkit`
- Head mode: `headed=false` and `headed=true`

Videos are only recorded when `-DrecordVideo=true` (in CI this is aligned with headed mode). This gives coverage for both rendering paths while keeping runtime parallelized.

## Trend Charts
Historical flaky candidate count, failed test count, and failure rate (%) trends are rendered into an HTML page during the `deploy-report` job using `scripts/generate_trends.py`.

After Pages publish you can view (replace `<your-username>`):
```
https://krishhsubash.github.io/PlayWrightJava/extra/trends.html
```
Artifacts included:
- `trends.html` (Chart.js line charts)
- `flaky-history.json` (raw merged data)

## Slack Notifications (Optional)
The pipeline can notify a Slack channel when the number of flaky candidates increases between the last two main branch runs.

Steps to enable:
1. Create an Incoming Webhook in your Slack workspace (Workspace Settings → Apps → Incoming Webhooks).
2. Copy the webhook URL.
3. In your GitHub repo settings add a Repository Secret named `SLACK_WEBHOOK_URL` with that value.
4. Next main branch run will execute the notification step; it only posts when `current_flaky > previous_flaky`.

Message format example:
```
Flaky tests increased: 2 -> 5
```

If the secret is absent or no increase is detected the step logs and exits silently.

### Flaky History Retention
History arrays can grow indefinitely. A pruning mechanism keeps only the most recent N entries (default 200) controlled by env var `FLAKY_HISTORY_MAX`.

Override in CI (example keep last 100):
```
env:
    FLAKY_HISTORY_MAX: 100
```
Both generation (`scripts/surefire_summary.py`) and merge (`scripts/merge_flaky_histories.py`) honor this variable.

### Badge Color Thresholds
Current logic (CI workflow) sets colors:
- Flaky count: 0=green, 1-3=yellow, >3=red
- Failure rate (% of total tests latest run): 0-2%=green, 3-10%=yellow, >10%=red
 - Stability score (100 - failure rate): >=98=green, 90-97=yellow, <90=red
Adjust in `.github/workflows/playwright.yml` within the badge steps as needed.

### Additional Caching
`~/.npm` is cached in the deploy job to speed up repeated global install of Allure CLI.

## License
POC code – adapt freely within your organization.
