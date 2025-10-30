from app import create_app

app = create_app('default')

if __name__ == '__main__':
    print("🚀 Starting Farmart backend server...")
    print("📝 API available at: http://localhost:5000/api")
    print("🔑 Sample accounts:")
    print("   Farmer: farmer@example.com / password123")
    print("   User: user@example.com / password123")
    app.run(debug=True, host='0.0.0.0', port=5000)