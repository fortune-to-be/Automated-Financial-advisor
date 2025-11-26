# User Manual

Quickstart

1. Start backend and frontend (see `docs/deployment.md` for production).
2. Register a user via POST `/api/auth/register` or use the web UI.
3. Login (`/api/auth/login`) to obtain `access_token` and include `Authorization: Bearer <token>` for protected routes.

Common API flows

- CSV Import: `/api/transactions/import/preview` and `/api/transactions/import/commit` accept multipart `file` field with CSV. Required CSV headers: `transaction_date,description,amount,account_id,type`.
- Admin Rules: `/api/admin/rules` endpoints let admins add/validate rules that auto-categorize transactions.
- Planner: `/api/planner/recommend-budgets` returns budget recommendations based on recent transactions.

Support

If you encounter errors:
- Check server logs for tracebacks.
- Confirm `DATABASE_URL` points to an initialized database and migrations have been applied.
- Use `backend/scripts/seed_direct.py` to create a sample admin user and category for demos.
