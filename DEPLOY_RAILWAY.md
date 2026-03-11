# Deployment (Railway)

Use Railway with at least 4 GB RAM for face restoration.
This repo is configured for Railway Nixpacks (not Docker).

## Steps

1. In Railway service settings, ensure Builder is Nixpacks.
2. Redeploy latest commit.
3. Set service memory to at least 4 GB.

## Optional Environment Variables

- `LOW_MEMORY_MODE=0` (default, face restoration enabled)
- `MAX_INPUT_DIM=2048`

The app start command is defined in `railway.json`.
