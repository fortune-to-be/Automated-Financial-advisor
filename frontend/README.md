# Frontend (React + TypeScript)

This is a minimal Vite + React + TypeScript scaffold for the Automated Financial Advisor frontend.

Quick start:

```powershell
cd frontend
npm install
npm run dev
```

Notes:
- Uses Tailwind for styling.
- `src/services/api.ts` provides an `api` axios instance and keeps the access token in memory. Refresh endpoint `/api/auth/refresh` is expected to use an httpOnly cookie for the refresh token.
