import os
from datetime import datetime

from flask import Flask, render_template

from config import Config
from db import db, login_manager


# ==========================================================
# APPLICATION FACTORY
# ==========================================================

def create_app():

    app = Flask(
        __name__,
        instance_relative_config=True
    )

    # ------------------------------------------------------
    # Configuration
    # ------------------------------------------------------

    app.config.from_object(Config)

    # ------------------------------------------------------
    # Create required folders
    # ------------------------------------------------------

    os.makedirs(
        app.instance_path,
        exist_ok=True
    )

    upload_folder = os.path.join(
        app.static_folder,
        "uploads"
    )

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    # ------------------------------------------------------
    # Initialize database
    # ------------------------------------------------------

    db.init_app(app)

    # ------------------------------------------------------
    # Initialize Flask-Login
    # ------------------------------------------------------

    login_manager.init_app(app)

    # ------------------------------------------------------
    # Import models
    # ------------------------------------------------------

    from models import User, Post

    # ------------------------------------------------------
    # Register blueprints
    # ------------------------------------------------------

    from routes import main_bp
    from auth import auth_bp
    from admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # ------------------------------------------------------
    # Context processor
    # ------------------------------------------------------

    @app.context_processor
    def inject_current_year():
        return {
            "now": datetime.now()
        }

    # ------------------------------------------------------
    # Error handlers
    # ------------------------------------------------------

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):

        db.session.rollback()

        return render_template("500.html"), 500

    # ------------------------------------------------------
    # Create database tables
    # ------------------------------------------------------

    with app.app_context():
        db.create_all()

    return app


# ==========================================================
# APPLICATION INSTANCE
# ==========================================================

app = create_app()


# ==========================================================
# LOCAL DEVELOPMENT
# ==========================================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False
    )