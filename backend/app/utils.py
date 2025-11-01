import time

import requests
from flask import current_app

# Cache token and expiry time globally
mpesa_token = None
token_expiry = 0


def get_mpesa_token():
    """Fetch and cache M-Pesa access token for 1 hour."""
    global mpesa_token, token_expiry

    # If token exists and is not expired, reuse it
    if mpesa_token and time.time() < token_expiry:
        return mpesa_token

    consumer_key = current_app.config.get("MPESA_CONSUMER_KEY")
    consumer_secret = current_app.config.get("MPESA_CONSUMER_SECRET")

    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    try:
        response = requests.get(url, auth=(consumer_key, consumer_secret))
        response.raise_for_status()
        data = response.json()
        mpesa_token = data.get("access_token")
        token_expiry = time.time() + 3500  # Slightly less than 1 hour to refresh safely

        print(f"✅ New M-Pesa access token fetched: {mpesa_token}")
        return mpesa_token
    except Exception as e:
        print(f"❌ Failed to get M-Pesa token: {str(e)}")
        return None
