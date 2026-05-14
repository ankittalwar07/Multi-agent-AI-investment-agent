"""Streamlit Cloud entry point.

Streamlit Community Cloud looks for `streamlit_app.py` at the repo root by
default. This shim re-execs the real app under `app/streamlit_app.py`. The
sub-pages live in `app/pages/` and Streamlit will auto-discover them.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "app"
SRC = ROOT / "src"

# Make src + app importable on Streamlit Cloud's runner.
for p in (str(SRC), str(APP_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

runpy.run_path(str(APP_DIR / "streamlit_app.py"), run_name="__main__")
