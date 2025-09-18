# simple-commerce-platform-18605-18616

## Backend API base and frontend configuration

The backend serves all API routes under `/api` (e.g., `/api/categories/`, `/api/products/`, etc.).
For local development, the backend typically runs on `http://localhost:3001`.

The frontend axios client is configured to read the base URL from the `REACT_APP_API_BASE` environment variable and falls back to `/api`:
- If the frontend is served by the same origin and the backend is reverse-proxied under `/api`, you can keep the default `REACT_APP_API_BASE=/api`.
- If the frontend runs on a different origin/port in development (e.g., React dev server at `http://localhost:3000` and backend at `http://localhost:3001`), set:
  REACT_APP_API_BASE=http://localhost:3001/api

Ensure this variable is present in the frontend `.env` file so requests reach the backend correctly.
