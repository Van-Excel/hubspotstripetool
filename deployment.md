# Deployment

## One Repo, Two Platforms

Push to GitHub. Vercel sees only `frontend/`, GCP sees the root via Docker.

### Vercel (Frontend)

1. Import GitHub repo into Vercel
2. Configure:
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Framework Preset:** Vite
3. Add environment variables:
   - `VITE_API_URL` = your GCP Cloud Run URL (e.g. `https://api-tool-abc.a.run.app`)
4. Deploy

### GCP Cloud Run (Backend)

1. Update `Dockerfile` for production:
   ```dockerfile
   CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8080", "--workers=2"]
   ```
2. Push secrets to GCP or use Secret Manager
3. Deploy:
   ```bash
   gcloud run deploy recon-api \
     --source . \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars DJANGO_DEBUG=False
   ```
4. Use **Cloud SQL** for PostgreSQL instead of local Docker

### Production Checklist

- `DEBUG=False`
- `ALLOWED_HOSTS=your-gcp-url.a.run.app`
- `USE_SQLITE=0` (remove from `.env`, use PostgreSQL)
- Set `VITE_API_URL` in Vercel to point to Cloud Run URL
- Update `vite.config.ts` proxy to use `VITE_API_URL` env var instead of hardcoded `localhost:8000` for production builds
