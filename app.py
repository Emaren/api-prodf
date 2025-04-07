import os
import logging
from flask import Flask
from flask_cors import CORS
from db import db, init_db

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # DB Setup
    raw_db_url = os.getenv("DATABASE_URL")
    if not raw_db_url:
        user = os.getenv("PGUSER", "postgres")
        pw = os.getenv("PGPASSWORD", "postgres")
        host = os.getenv("PGHOST", "localhost")
        port = os.getenv("PGPORT", "5432")
        dbname = os.getenv("PGDATABASE", "aoe2")
        raw_db_url = f"postgresql://{user}:{pw}@{host}:{port}/{dbname}"
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = raw_db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if "RENDER" in os.environ or "render.com" in raw_db_url:
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"sslmode": "require"}}

    init_db(app)

    # Register routes
    from routes.replay_routes import replay_bp
    from routes.user_routes import user_bp
    from routes.debug_routes import debug_bp

    app.register_blueprint(replay_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(debug_bp)

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)  # 🔍 Max debug logging
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=8002)
