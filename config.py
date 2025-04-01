import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///school.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Additional configuration for logging if needed:
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
