"""Run Robin with one command: `python robin_single.py`

All the code now lives in the `app/` package (this file used to contain a
second, out-of-date copy of everything). This is just a shortcut that starts
the same app Docker runs.
"""

import uvicorn

from app.main import app  # noqa: F401

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
