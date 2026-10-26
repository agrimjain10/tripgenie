# Deployment and continuous updates

**Live app:** https://tripgenie-escape.vercel.app

**Backend health:** https://tripgenie-api.vercel.app/api/health

## Target layout

| Resource | Configuration |
| --- | --- |
| GitHub | `agrimjain10/tripgenie`, private; production branch `main` |
| Frontend | Vercel, root `frontend`, Next.js, Node 22 |
| Backend | Vercel, root `backend`, FastAPI, Python 3.12 |
| Database | Persistent Neon PostgreSQL, Free plan |
| AI | Gemini key stored only in backend environment settings |

This is a personal-project setup within free-tier limits. No paid plan is required. Provider quotas and terms can change; verify the selected plan and avoid enabling usage-based billing unintentionally.

## Database

Create Neon from backend project → Storage → Create Database. Select Free, a nearby supported region, and connect to the backend. Ensure the backend receives the pooled PostgreSQL connection URL as `DATABASE_URL`, with TLS enabled (`sslmode=require`). The integration may also provide `POSTGRES_URL`; the app reads `DATABASE_URL`.

Use separate preview and production databases/branches for testing migrations. Connecting previews to production means their writes affect real data too.

## Backend settings

Root directory: **backend**. Framework: **FastAPI**. Python: **3.12**. Install from `requirements.txt`.

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Persistent pooled PostgreSQL connection URL |
| `JWT_SECRET` | Random secret, at least 32 characters |
| `GEMINI_API_KEY` | Sensitive backend-only Gemini key |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` or another supported configured model |
| `GEMINI_FALLBACK_MODELS` | Optional comma-separated model IDs |
| `FRONTEND_URL` | Exact final frontend HTTPS origin; comma-separated origins supported |

Tables are created on startup and small additive compatibility migrations are applied. Local SQLite accounts/trips are not uploaded. Never use local or `/tmp` SQLite as cloud persistence.

The backend production URL must accept requests from the frontend. Preview deployment protection can remain enabled.

## Frontend settings

Root: **frontend**. Framework: **Next.js**. Node: **22.x**. Install: `npm ci`. Build: `npm run build`.

Set `NEXT_PUBLIC_API_URL=/` and `BACKEND_API_URL=https://tripgenie-api.vercel.app`. Next.js proxies `/api/*` to the backend so browser calls stay on the application origin. These settings affect the build; redeploy after changing them. Direct cross-origin API URLs remain supported for local development. A free `vercel.app` domain is included. Buying a custom domain is optional and outside this zero-cost setup.

## Verify the complete flow

1. Open backend `/api/health`.
2. Register a fresh cloud account and sign in.
3. Create a trip and generate a plan. Confirm generation finishes and reload preserves it.
4. Refine with the assistant, edit an activity, add an expense, and reload again.
5. Export PDF and ICS.
6. Open a share link while signed out, confirm private data is excluded, and verify revocation.

Generation uses bounded FastAPI background tasks. Verify completion on the deployed Python runtime. A host restart can interrupt in-process tasks; stale-job recovery allows retry. A durable queue is recommended for stronger guarantees at scale.

## Push updates

```powershell
git pull --ff-only
# Make and verify changes.
git add .
python scripts/check_repository.py
git commit -m "Describe the change"
git push origin main
```

Vercel builds and deploys pushes automatically. Run the documented tests before pushing. An optional GitHub Actions workflow is included at `docs/quality-checks.yml.example`; enable it at `.github/workflows/ci.yml` after granting the GitHub publishing credential `workflow` scope. The current publishing token can push app code but cannot upload workflow files. Use pull requests and review checks before merging.

Revert a bad commit and push, or promote a previously verified deployment. Code rollback does not roll back database changes. Keep database backups outside Git.

## Free-tier boundaries

- [Vercel Hobby](https://vercel.com/docs/plans/hobby) is for personal, non-commercial use, with usage caps.
- [Neon Free](https://neon.com/pricing) has storage/compute limits; idle compute can suspend.
- [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing) and quotas depend on the model and Google project. Free hosting does not make inference unlimited.
- [Render Free](https://render.com/docs/free) is an alternative compute host, but sleeps on inactivity and has an ephemeral filesystem. Its free PostgreSQL expires, so it is not this project's persistent database default.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Login cannot connect | API URL, backend deployment and database connection |
| CORS rejection | Exact frontend origin in `FRONTEND_URL`, then redeploy backend |
| Trips vanish on redeploy | Use PostgreSQL, never cloud SQLite |
| Starter plan instead of Gemini | Key, model access, quotas and provider availability |
| Generation stays pending | Wait for stale-job recovery, retry, inspect backend logs |
| API URL change ignored | Rebuild frontend; public variables are build-time values |
| Preview modifies live trips | Isolate its database / Neon branch |
