import os
from dotenv import load_dotenv
from flask_migrate import upgrade
from app import create_app, db

# ✅ Load environment variables early
load_dotenv()

app = create_app()

# ✅ Apply pending migrations automatically on startup
with app.app_context():
    try:
        upgrade()
        print("✅ Database migrations applied.")
    except Exception as e:
        print(f"⚠️ Failed to run migrations: {e}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "False") == "True"

    print("🚀 Starting Farmart backend server...")
    print(f"📝 API available at: http://localhost:{port}/api")
    app.run(debug=debug, host="0.0.0.0", port=port)
