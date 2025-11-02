# from app import create_app

# app = create_app('default')

# if __name__ == '__main__':
#     print("🚀 Starting Farmart backend server...")
#     print("📝 API available at: http://localhost:5000/api")
#     print("🔑 Sample accounts:")
#     print("   Farmer: farmer@example.com / password123")
#     print("   User: user@example.com / password123")
#     app.run(debug=True, host='0.0.0.0', port=5000)
from app import create_app, db
from flask_migrate import upgrade
import os

app = create_app()

# ✅ Ensure DB is migrated automatically on Render startup
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
