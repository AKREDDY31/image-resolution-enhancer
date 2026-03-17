# Image Resolution Enhancer

This version uses the Claid.ai API instead of local machine learning models.

## Local setup

1. Create `.env` with `CLAID_API_KEY=...`
2. Install dependencies: `pip install -r requirements.txt`
3. Run locally: `python app.py`

## Vercel

This repo includes:

- `api/index.py` for the Vercel Python runtime
- `vercel.json` to route all traffic to the Flask app
- `.python-version` to keep deployment on a supported Python version

Set `CLAID_API_KEY` in the Vercel project environment variables before deploying.
