# Demo script and shot list

This document describes a 3–5 minute demo video with three scenarios and timed actions. Use the `scripts/demo.sh` to seed the DB and start the backend. The frontend can be run via `npm run dev` or using the built `dist` assets.

Goal: show registration/login, import transactions, budget recommendations and rule auto-categorization.

Scenario overview (3 scenarios, ~4 minutes total)

1) Quick intro & login (0:00–0:40)
- 0:00–0:05: Title slide (App name + purpose)
- 0:05–0:20: Show dashboard logged in as `demo_user` (use seeded demo user). Mention monthly income = 150000 PKR.
- 0:20–0:40: Show account balances and recent transactions list.

2) CSV import & rule application (0:40–2:10)
- 0:40–0:50: Open CSV import modal, select `sample-data/transactions_6mo.csv`.
- 0:50–1:20: Preview rows, show auto-categorized rows (Groceries, Utilities), adjust one row category manually and commit.
- 1:20–1:40: Show audit/log that import created transactions and rules applied.
- 1:40–2:10: Create / validate an admin rule that auto-categorizes 'Supermarket' as `Groceries` and apply to recent transactions. Show results.

3) Planner & budgets (2:10–4:00)
- 2:10–2:30: Open Planner -> Recommend Budgets; explain 50/30/20 baseline and show generated budgets.
- 2:30–3:00: Create a budget for `Groceries` with monthly limit and show budget screen (spent vs limit).
- 3:00–3:30: Show goal planner (create small goal) and compute schedule.
- 3:30–4:00: Close: show logs, mention tests and CI, link to docs in repo.

Expected screenshots (capture during recording)
- Dashboard with transactions visible and demo user email.
- CSV import preview window with sample rows and applied rules.
- Planner recommendations screen showing recommended budgets and monthly income.

Recording tips
- Use a stable terminal or the `scripts/demo.sh` to start a seeded instance so the demo is deterministic.
- Keep actions short and narrate the key benefits (auto-categorization, budget recommendations, planner).
