#  Farmart Backend

## Overview
Farmart is a backend API built with **Flask** that connects farmers directly to buyers, eliminating middlemen who reduce farmers’ profits. The API enables farmers to list animals for sale, while users can browse, search, filter, order, and pay for animals — all within a secure and scalable platform.

Repository Name: **Farmart-Backend**  
Frontend Repository: **Farmart-Frontend**  
GitHub Username: **okukubrianokoth**

---

##  Table of Contents
1. Project Description  
2. Features  
3. Tech Stack  
4. Project Structure  
5. Getting Started  
6. Environment Variables  
7. Database Setup  
8. Running the App  
9. Testing  
10. Deployment  
11. API Documentation  
12. Contributors  
13. License

---

##  Project Description
Farmart empowers farmers to directly list and sell their farm animals while buyers can easily discover and purchase animals online.  
The backend handles authentication, authorization, payments, and communication with third-party services like **Cloudinary**, **SendGrid**, and **M-Pesa**.

---

##  Features

###  Farmer
- Secure registration and login  
- Add new animals for sale (with Cloudinary image uploads)  
- Edit and update animal details  
- Approve or reject orders  
- View analytics of sales  

###  Buyer
- Register and log in securely  
- View all listed animals  
- Search and filter by type, breed, or age  
- Add animals to cart and checkout  
- Make payments through integrated M-Pesa gateway  

### ⚙️ System Features
- Pagination for large datasets  
- Image uploads and resizing via Cloudinary  
- Two-step authentication with email verification  
- Email notifications using SendGrid  
- JWT-based authentication and authorization  
- Human-readable date formatting  
- CI/CD pipeline with GitHub Actions and Render  
- Swagger UI for documentation  
- Unit and integration testing  

---

##  Tech Stack

| Layer | Technology |
|-------|-------------|
| Backend Framework | Flask (Python) |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Authentication | JWT Authentication |
| Email Service | SendGrid |
| Image Uploads | Cloudinary |
| Payments | M-Pesa Daraja API |
| Testing | Pytest / Unittest |
| CI/CD | GitHub Actions + Render |
| Documentation | Swagger UI |
| Frontend (linked) | React + Redux Toolkit |

---
---

##  Running the App

###  Prerequisites
- Python 3.10+  
- PostgreSQL installed and running  
- A virtual environment (recommended)  
- M-Pesa Daraja API credentials  
- SendGrid API key  
- Cloudinary account for image uploads  

###  Steps to Run Locally
```bash
# 1️ Clone the repository
git clone https://github.com/okukubrianokoth/Farmart-Backend.git
cd Farmart-Backend/backend

# 2️ Create a virtual environment and activate it
python3 -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows

# 3️ Install dependencies
pip install -r requirements.txt

# 4️ Set up your environment variables
cp .env.example .env
# Edit .env and update credentials (DB, Cloudinary, SendGrid, M-Pesa)

# 5️ Run database migrations
flask db upgrade

# 6️ Start the Flask development server
flask run
```

###  Access
Visit: **http://127.0.0.1:5000/**

---

##  Testing

Farmart uses **pytest** for testing.

```bash
# Run all tests
pytest

# Run specific test file
pytest backend/tests/test_auth.py -v

# Run with coverage report
pytest --cov=app
```

---

## 👥 Contributors

| Name | Role | GitHub |
|------|------|--------|
| **Brian Okuku** | Backend Developer / Lead | [@okukubrianokoth](https://github.com/okukubrianokoth) |
| **Edward Karogo** | Developer | — |
| **Ezra Radai** | Developer | — |
| **Hussein Chegu** | Developer | — |

---

##  Location & Contact

 **Location:** Ngong Road, Nairobi, Kenya  
 **Phone:** 0793459226  
 **Email:** okukubrian743@gmail.com  

---

##  License

```
MIT License

Copyright (c) 2025
Brian Okuku, Edward Karogo, Ezra Radai, and Hussein Chegu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

---





##  Project Structure
##  Project Structure

```
Farmart-Backend/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py               # Initializes the Flask app, database, and extensions
│   │   ├── models.py                 # Defines database models (User, Animal, Order, etc.)
│   │   ├── routes/                   # Contains all route blueprints
│   │   │   ├── auth.py               # Handles user registration, login, and JWT authentication
│   │   │   ├── animals.py            # Routes for CRUD operations on animal listings
│   │   │   ├── orders.py             # Routes for placing, viewing, and updating orders
│   │   │   ├── payments.py           # M-Pesa integration routes and callback handling
│   │   │   └── users.py              # Routes for managing user profiles and data
│   │   ├── utils/                    # Helper and utility modules
│   │   │   ├── email_service.py      # Handles sending verification and notification emails via SendGrid
│   │   │   ├── mpesa.py              # Contains helper functions for M-Pesa Daraja API integration
│   │   │   ├── cloudinary_upload.py  # Manages Cloudinary uploads and image transformations
│   │   │   └── decorators.py         # Custom decorators for authorization and role-based access
│   │   ├── config.py                 # App configuration file (development, testing, production)
│   │   ├── extensions.py             # Initializes database, JWT manager, and other extensions
│   │   └── __init__.py               # Makes the folder a package
│   │
│   ├── tests/                        # Test suite for unit and integration testing
│   │   ├── test_auth.py              # Tests authentication endpoints
│   │   ├── test_animals.py           # Tests CRUD for animal listings
│   │   ├── test_orders.py            # Tests order management logic
│   │   ├── test_payments.py          # Tests M-Pesa API endpoints
│   │   └── conftest.py               # Pytest fixtures and setup
│   │
│   ├── migrations/                   # Auto-generated Alembic migration files
│   ├── wsgi.py                       # WSGI entry point for deployment
│   └── manage.py                     # Command-line interface for managing the app (migrations, etc.)
│
├── .github/
│   └── workflows/
│       └── ci.yml                    # CI/CD pipeline for GitHub Actions (linting, testing)
│
├── .env.example                      # Example environment variable configuration
├── requirements.txt                  # Python dependencies list
├── Dockerfile                        # Docker configuration for containerized deployment
├── render.yaml                       # Render platform deployment configuration
└── README.md                         # Project documentation (this file)
```

├── render.yaml                      # Render platform deployment configuration
└── README.md                        # Project documentation (this file)




