import os


class Config:

    # ==========================================================
    # FLASK CONFIGURATION
    # ==========================================================

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "multiuserblog-secret-key-change-this"
    )

    # ==========================================================
    # DATABASE CONFIGURATION
    # ==========================================================

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:Beth%40321@localhost:5432/multiuserblog"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ==========================================================
    # FILE UPLOAD CONFIGURATION
    # ==========================================================

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    ALLOWED_EXTENSIONS = {
        "jpg",
        "jpeg",
        "png",
        "gif",
        "webp"
    }