# simple-commerce-platform-18605-18616

Deployment notes for unified backend + frontend:

- This Django backend is configured to serve a built React SPA for all non-API routes.
- API is mounted under `/api/` and docs under `/docs` and `/redoc`.
- To avoid 404s on direct navigation (e.g. `/products/1`, `/cart`, etc.), ensure the React build is placed at:
  `ecommerce_backend/frontend_build`
  containing at least `index.html` and a `static/` directory.

Steps:
1. Build the React app (from the frontend project):
   - In simple-commerce-platform-18605-18617/ecommerce_frontend run: `npm run build`
2. Copy the build output into the backend project:
   - Copy the contents of `ecommerce_frontend/build/` to `simple-commerce-platform-18605-18616/ecommerce_backend/frontend_build/`
3. Run Django server. Django will:
   - Serve API under `/api/`
   - Serve React SPA for all other routes via a catch-all view.
4. If using collectstatic in production:
   - STATIC_ROOT is set to `ecommerce_backend/staticfiles`
   - React build static files are referenced via STATICFILES_DIRS and do not require collectstatic.

Environment:
- CORS is open for simplicity (CORS_ALLOW_ALL_ORIGINS=True). Adjust per your security needs.

Troubleshooting:
- If you see "Frontend build not found" on non-API routes, ensure step 2 is completed and `index.html` exists under `frontend_build`.
- If API requests 404, confirm you are calling paths prefixed with `/api/` (e.g., `/api/health/`, `/api/products/`).