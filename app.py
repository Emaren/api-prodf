import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate, upgrade
from db import db, init_db

migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # ✅ CORS setup for local dev
    CORS(app, origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002"
    ], supports_credentials=True)

    # Build DB connection string
    raw_db_url = os.getenv("DATABASE_URL")
    if not raw_db_url:
        user = os.getenv("PGUSER", "aoe2user")
        pw = os.getenv("PGPASSWORD", "secretpassword")
        host = os.getenv("PGHOST", "db")  # <--- matches your Compose service name for Postgres
        port = os.getenv("PGPORT", "5432")
        dbname = os.getenv("PGDATABASE", "aoe2db")
        raw_db_url = f"postgresql://{user}:{pw}@{host}:{port}/{dbname}"

    # Fix any old postgres:// URLs that need to be postgresql://
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = raw_db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # If running on Render or a DB that needs SSL
    if "RENDER" in os.environ or "render.com" in raw_db_url:
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"sslmode": "require"}}

    # Init DB and migrations
    init_db(app)
    migrate.init_app(app, db)

    # ───────────────────────────────────────────────────────────────────
    # AUTOMATIC MIGRATIONS on container startup
    # ───────────────────────────────────────────────────────────────────
    with app.app_context():
        try:
            upgrade()  # Alembic "flask db upgrade"
        except Exception as e:
            logging.warning(f"Auto-migrate failed: {e}")

    # Register blueprints
    from routes.replay_routes import replay_bp
    from routes.user_routes import user_bp
    from routes.debug_routes import debug_bp
    from routes.admin_routes import admin_bp

    app.register_blueprint(replay_bp)  # /api/parse_replay, /api/game_stats
    app.register_blueprint(user_bp)    # /api/user/*
    app.register_blueprint(debug_bp)   # /debug/*
    app.register_blueprint(admin_bp)   # /api/admin/*

    # Optional alias route => /me is the same as /api/user/me
    @app.route("/me", methods=["GET", "POST"])
    def me_alias():
        from routes.user_routes import get_user_by_uid
        return get_user_by_uid()

    return app

app = create_app()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True, host="0.0.0.0", port=8002)
