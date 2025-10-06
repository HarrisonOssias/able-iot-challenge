# Analytics Service (Next.js)

## Overview
Next.js app exposing API routes that query Postgres metrics/views and a simple React dashboard to visualize results. Runs separately from ingest.

## API Routes
- `/api/metrics/avg-extension-mm` – average platform extension in mm per device.
- `/api/metrics/extension-vs-retraction` – counts of extension vs retraction.
- `/api/metrics/battery-summary` – min/max/avg battery % and last seen.
- `/api/metrics/platform-height` – summary of platform height values.

## UI
- `/` – dashboard that polls the routes every few seconds and renders tables.

## Config
- Environment: `DATABASE_URL` pointing at the same Postgres used by ingest.
- Source: `analytics_service/src/*`

## Local Dev
- Compose target `analytics` runs `next dev` on port 8001.
- Open `http://localhost:3000`.
