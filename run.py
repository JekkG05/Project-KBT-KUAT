"""
KUAT. - Keep Up Adaptive Training
Entry point of the application.

Run with:
    python run.py
"""
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=debug_mode)
