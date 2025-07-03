import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root regardless of where the script runs
ROOT = Path(__file__).resolve().parent.parent
env_path = ROOT / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)