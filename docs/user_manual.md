# User Manual

This manual covers the basic usage of the Automated Financial Advisor application for end users and administrators.

Getting started (user)
- Register an account via the frontend UI or `POST /api/auth/register`.
- Log in to receive a JWT access token used for subsequent API requests.

Transactions
- Import transactions using the CSV import: preview then commit. The CSV requires fields: `transaction_date`, `description`, `amount`, `account_id`, `type` (one of `income|expense|transfer`).
- You can review the preview rows and adjust mappings before committing.

Budgets & Goals
- Create budgets to track spending limits per category. Budgets have `start_date` and `end_date` and are evaluated against imported transactions.
- Add financial goals and use the planner to compute feasible schedules.

Admin features
- Admin users can create and manage rules that auto-categorize transactions. Use `POST /api/admin/rules/validate` to validate a rule before saving.

Developer notes
- API endpoints and example payloads are documented in the README and quickstart.
