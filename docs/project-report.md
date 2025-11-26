# Project Report — Automated Financial Advisor

This report includes the Software Requirements Specification (SRS), architecture, algorithms (with formulas), tests summary, and notes for future work (including an optional ML branch).

1. Software Requirements Specification (SRS)

1.1 Purpose
The Automated Financial Advisor provides personal finance automation: import transactions, auto-categorization rules, budgeting recommendations, goal planning, and reports.

1.2 Functional Requirements
- User registration and authentication (JWT)
- CRUD for accounts, categories, budgets, goals
- CSV import preview and commit
- Admin rule editor to define conditions and actions for auto-categorization
- Planner to recommend budgets (50/30/20 baseline) and schedule goals

1.3 Non-functional Requirements
- Production deployment via Docker
- Tests (unit and integration) with CI
- Reasonable performance for single-user budgets (milliseconds to seconds)

2. Architecture
- See `docs/architecture.md` for a high-level overview. The app uses a Flask backend (app factory) with SQLAlchemy and a Vite React frontend.

3. Algorithms and formulas

3.1 Budget Recommender (50/30/20 baseline)

Inputs:
- Transactions T over analysis window (e.g., last N months)
- Monthly income I (calculated from income transactions)

Steps:
1. Calculate analysis window: start_date = now - N months; end_date = now.
2. Filter transactions in T where transaction_date ∈ [start, end].
3. Monthly income I = (sum of income transaction amounts over window) / months_in_window

Formulas:
- months_in_window = max(1, (end_date - start_date).days / 30)
- I = (Σ_{t ∈ T, t.type='income'} t.amount) / months_in_window

Baseline budgets:
- Needs = 0.50 * I
- Wants = 0.30 * I * (1 - debt_ratio)
- Savings = 0.20 * I * (1 - debt_ratio)

Debt ratio estimation:
- debt_ratio = min(1.0, total_debt / I)
- total_debt = Σ max(0, -account.balance) over user accounts

Per-category recommendation (for category c):
- avg_spend_c = average monthly spending for category c (from T)
- recommended_c = clamp(avg_spend_c * buffer_factor, upper_bound)
  where buffer_factor typically 1.05–1.1 and upper_bound is (needs or wants)/k depending on category type.

3.2 Rule Engine
- Rules are evaluated in priority order. Each rule has:
  - condition: simple operators like `merchant_contains`, `amount_gt`, `merchant_regex`.
  - action: `set_category`, `set_tags`.

Evaluation:
- For transaction tx, evaluate condition(tx) -> boolean. If true, perform action(tx).

Examples:
- merchant_contains: condition(tx) := lower(tx.description) contains lower(value)

3.3 Transaction Import
- CSV parsed with required fields: `transaction_date`, `description`, `amount`, `account_id` or `account_name`, `type`.
- Rows are previewed with rule application (non-persistent). On commit, transactions are persisted and audit logs created.

4. Tests
- Backend: pytest suite (unit and integration) — currently ~112 passing, 10 skipped.
- Frontend: Vitest component tests — basic coverage for core components.
- E2E: in-process Flask client smoke test `backend/test_e2e.py` covers auth, import, budgets, planner.

5. Future Work
- ML-driven auto-categorization: train a classifier on labeled transactions (features: merchant, description tokens, amount, time-of-day). Use lightweight models (logistic regression or tree-based) and offer model explainability.
- Expand planner with Monte Carlo cashflow projections and risk-aware allocation.
- Add background workers (Celery/RQ) for heavy imports and schedule tasks.

Appendix: expected screenshots and test outputs
- See `docs/demo_script.md` for expected screenshots in the demo.
