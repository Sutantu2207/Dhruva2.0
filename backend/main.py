"""Dhruva.AI V2 — Root ASGI Entrypoint for Vercel Serverless & Local Execution."""

import os
import sys

# Ensure backend root and src directory are on sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

src_dir = os.path.join(backend_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from src.main import app  # noqa: F401

