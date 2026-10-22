import os

from dotenv import load_dotenv

load_dotenv()

# EURI API Key (set in .env, see .env.example)
EURI_API_KEY = os.getenv("EURI_API_KEY")
