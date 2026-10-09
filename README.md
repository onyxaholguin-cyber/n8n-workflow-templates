# Free n8n workflow templates for landlords, freelancers and self-hosters

Six importable [n8n](https://n8n.io) workflows that solve one boring job each, with **no paid APIs and no AI keys**. Every template has a setup note on the canvas, and every one was run end to end in a real n8n 2.40.6 before it was published here (how, below).

| # | Template | What it does | Needs |
|---|---|---|---|
| 1 | [Weekly workflow audit](workflows/01-weekly-workflow-audit.json) | Every Monday, reads all your workflows through the n8n API and reports pasted secrets (redacted), webhooks without auth, missing error workflows, swallowed errors and pinned data to Slack/Discord/Google Chat. Silent when clean. | n8n API key, chat webhook |
| 2 | [Error alert to chat](workflows/02-error-alert-to-chat.json) | When any watched workflow fails, posts the workflow, failing node, error and execution link to your chat. | chat webhook |
| 3 | [Bank CSV → Schedule C / E categories](workflows/03-bank-csv-tax-categorizer.json) | A private n8n form: upload a bank or card CSV, get it back categorized into Schedule C (freelancer) or Schedule E (landlord) lines with totals. Runs inside your n8n only. | nothing |
| 4 | [Late rent and late fee alerts](workflows/04-late-rent-and-late-fee-alerts.json) | Every morning, reads your rent ledger (Google Sheet published as CSV) and posts who is LATE, who still owes a late fee, and how much, using your grace period, flat/percent/daily fee and cap. | sheet CSV link, chat webhook |
| 5 | [Lease renewal notice reminders](workflows/05-lease-renewal-notice-reminders.json) | Every Monday, works out each lease's notice send-by date (lease end − notice days − mailing buffer) and warns you before it passes, with the proposed new rent. | sheet CSV link, chat webhook |
| 6 | [New n8n release alert](workflows/06-n8n-new-release-alert.json) | Daily check of n8n's GitHub releases against the version you run; one message per new stable release, with a warning on major version jumps. | chat webhook |

Chat = any incoming webhook: Slack, Discord, Google Chat, Mattermost or Rocket.Chat (one HTTP node sends both `text` and `content`).

## Import

1. Open the JSON file above, click **Raw**, copy everything.
2. In n8n, open a new workflow and paste (Ctrl/Cmd+V), or use **⋯ > Import from file**.
3. Follow the yellow setup note on the canvas (2–5 minutes), click **Execute workflow** to test, then **Publish**.

No file contains credentials or webhook URLs; you add your own.

## How these were tested

- **Live runs in n8n 2.40.6** (official image / official npm package) with a mock chat endpoint and local CSV fixtures: each template was triggered for real and the posted message was checked word for word. Clean paths (nothing late, already up to date) post nothing; a missing chat webhook or CSV link stops with a clear "Paste your … into the Settings node" error (tested on templates 2 and 4).
- **The logic in templates 4–6 lives in [`src/`](src/)** and is unit-tested against an independent Python model: `python3 test/test_logic.py` (1,000 randomized rent charges, 242 lease reminders, release edge cases). The late fee rule matches this [rent late fee spreadsheet walkthrough](https://onyxaholguin-cyber.github.io/sheet-and-flow/tutorials/rent-late-fee-calculator-spreadsheet/), including the one-day-wide grace boundary.
- `python3 test/validate_workflows.py` checks every file: importable shape, connections point at real nodes, no credential ids, no pinned data, nothing secret-looking. CI runs both on every push.

Template 1 uses the rules from [n8n-workflow-audit](https://github.com/onyxaholguin-cyber/n8n-workflow-audit) and template 3 the categorizer from [bank-csv-categorizer](https://github.com/onyxaholguin-cyber/bank-csv-categorizer) (both MIT, also from Sheet & Flow).

## Want the bigger versions?

These are free and stay free. If they save you time, the paid kits go further (one-time price, instant download, from [Sheet & Flow](https://onyxaholguin-cyber.github.io/sheet-and-flow/)):

- **[n8n Production Self-Hosting Kit](https://sheetandflow.gumroad.com/l/n8n-self-hosting-kit)** ($29): Docker Compose + Postgres + Caddy HTTPS, backup/restore scripts, restore drill and a safe upgrade script.
- **[n8n Reliability Pack](https://sheetandflow.gumroad.com/l/n8n-reliability-pack)** ($19): error alert *router* (by workflow/severity), workflow backups to GitHub and disk, weekly failed-executions report, uptime/keyword/SSL monitor.
- **[Invoice Chaser for n8n + Google Sheets](https://sheetandflow.gumroad.com/l/invoice-chaser)** ($12): polite, escalating overdue-invoice reminders from a sheet.
- **[n8n Production Bundle](https://sheetandflow.gumroad.com/l/n8n-production-bundle)** ($49): all three.
- Landlords: the **[Landlord Tenant Toolkit](https://sheetandflow.gumroad.com/l/landlord-tenant-toolkit)** ($39) is the spreadsheet behind templates 4–5 (rent ledger with late fees, move-out deposit itemization, screening, turnover vs renewal), and the **[Lease Renewal Tracker](https://sheetandflow.gumroad.com/l/lease-renewal-tracker)** ($12) tracks 30/60/90-day windows and rent bumps.

Free browser tools and tutorials: [https://onyxaholguin-cyber.github.io/sheet-and-flow/](https://onyxaholguin-cyber.github.io/sheet-and-flow/)

## Notes

Not legal or tax advice. Late fee caps, grace periods and notice periods depend on your state, city and lease; set the template to match yours.

Issues and pull requests with fixes are welcome. License: MIT.
