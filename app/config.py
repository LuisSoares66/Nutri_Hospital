import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")

    ADMIN_USER = os.environ.get("ADMIN_USER", "luis")
    ADMIN_PASS = os.environ.get("ADMIN_PASS", "8mVS1v8dUxzZkWGm35ag2hYU5V5Ixfy0")
