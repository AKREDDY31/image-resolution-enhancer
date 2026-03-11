# Deployment (Railway)

This project can exceed Render free memory when face restoration is enabled.
Use Railway with a higher-memory service.

## Steps

1. Create a new Railway project from this GitHub repository.
2. Railway will auto-detect `Dockerfile`.
3. In service settings, set memory to at least 4 GB.
4. Deploy.

## Optional Environment Variables

- `LOW_MEMORY_MODE=0` (default, keeps face restoration enabled)
- `MAX_INPUT_DIM=2048`

The app listens on `$PORT` automatically.
