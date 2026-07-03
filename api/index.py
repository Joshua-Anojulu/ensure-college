"""Vercel serverless entrypoint. Vercel's @vercel/python runtime serves the
FastAPI ASGI `app` exported here for every route (see vercel.json)."""
from app.main import app  # noqa: F401
