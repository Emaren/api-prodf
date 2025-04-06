from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    from sqlalchemy import text
    import time, logging

    db.init_app(app)

    with app.app_context():
        # Wait for DB to be ready
        for attempt in range(10):
            try:
                db.session.execute(text("SELECT 1"))
                break
            except Exception:
                logging.warning(f"⏳ DB not ready (attempt {attempt+1}/10), retrying in 3s...")
                time.sleep(3)
        else:
            logging.error("❌ Database did not become ready in time.")
            exit(1)

        db.create_all()
        logging.info("✅ Tables created or verified existing.")
