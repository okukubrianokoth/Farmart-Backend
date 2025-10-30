from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Order, OrderStatus, User
import requests
import base64
from datetime import datetime
import json

payments_bp = Blueprint("payments", __name__)

# M-PESA EXPRESS SANDBOX CREDENTIALS
MPESA_CONSUMER_KEY = "ELffJ1IIfOR2LrBHXG7UH3xfCzQylGV1ucU0glmP9BBhZ8LR"
MPESA_CONSUMER_SECRET = (
    "87BCDfPwRbllkz1ITk2CiNGk3IaMjUcAryhQoFEsqZADz7q2wXA4Tb4sXIO8vbQA"
)
MPESA_SHORTCODE = "174379"
MPESA_PASSKEY = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
MPESA_CALLBACK_URL = "http://localhost:5000/api/payments/mpesa/callback"


def get_mpesa_access_token():
    """Get M-Pesa OAuth access token"""
    try:
        # Encode consumer key and secret
        credentials = f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {"Authorization": f"Basic {encoded_credentials}"}

        response = requests.get(
            "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
            headers=headers,
        )

        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"🔑 M-Pesa Access Token: {token}")
            return token
        else:
            print(f"❌ M-Pesa token error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ M-Pesa token exception: {str(e)}")
        return None


def generate_mpesa_password():
    """Generate M-Pesa API password"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    data_to_encode = MPESA_SHORTCODE + MPESA_PASSKEY + timestamp
    password = base64.b64encode(data_to_encode.encode()).decode()
    return password, timestamp


@payments_bp.route("/payments/mpesa/stk-push", methods=["POST"])
@jwt_required()
def initiate_mpesa_payment():
    """Initiate M-Pesa STK Push payment"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        order_id = data.get("order_id")
        phone_number = data.get("phone_number")

        if not order_id or not phone_number:
            return jsonify({"message": "Order ID and phone number are required"}), 400

        # Get order
        order = Order.query.get_or_404(order_id)

        # Verify user owns the order
        if order.user_id != current_user_id:
            return jsonify({"message": "Not authorized"}), 403

        # Format phone number (2547...)
        if phone_number.startswith("0"):
            phone_number = "254" + phone_number[1:]
        elif phone_number.startswith("+"):
            phone_number = phone_number[1:]
        elif not phone_number.startswith("254"):
            phone_number = "254" + phone_number

        print(f"📱 Processing payment for phone: {phone_number}")
        print(f"💰 Order amount: ${order.total_amount}")

        # Get access token
        access_token = get_mpesa_access_token()
        if not access_token:
            return jsonify({"message": "Failed to get M-Pesa access token"}), 500

        # Generate password
        password, timestamp = generate_mpesa_password()

        # STK Push request
        stk_push_data = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": 1,  # Use 1 KES for testing in sandbox
            "PartyA": phone_number,
            "PartyB": MPESA_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": MPESA_CALLBACK_URL,
            "AccountReference": f"Farmart{order.id}",
            "TransactionDesc": f"Payment for Order #{order.id}",
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        print("🚀 Sending STK Push to M-Pesa Sandbox...")

        print(f"📦 Request data: {json.dumps(stk_push_data, indent=2)}")

        response = requests.post(
            "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
            json=stk_push_data,
            headers=headers,
            timeout=30,
        )

        print(f"📡 M-Pesa Response Status: {response.status_code}")
        print(f"📡 M-Pesa Response: {response.text}")

        if response.status_code == 200:
            response_data = response.json()

            if response_data.get("ResponseCode") == "0":
                # Update order with payment reference
                order.payment_intent_id = response_data.get("CheckoutRequestID")
                order.payment_status = "pending"
                db.session.commit()

                return jsonify(
                    {
                        "message": "Payment initiated successfully! Check your phone for STK Push.",
                        "checkout_request_id": response_data.get("CheckoutRequestID"),
                        "customer_message": response_data.get("CustomerMessage"),
                    }
                )
            else:
                error_msg = response_data.get(
                    "ResponseDescription", "Payment initiation failed"
                )
                print(f"❌ M-Pesa Error: {error_msg}")
                return (
                    jsonify(
                        {"message": "Payment initiation failed", "error": error_msg}
                    ),
                    400,
                )
        else:
            print(f"❌ HTTP Error: {response.status_code} - {response.text}")
            return (
                jsonify(
                    {"message": "M-Pesa service unavailable", "error": response.text}
                ),
                500,
            )

    except Exception as e:
        print(f"❌ Payment error: {str(e)}")
        return jsonify({"message": "Payment failed", "error": str(e)}), 500


@payments_bp.route("/payments/mpesa/callback", methods=["POST"])
def mpesa_callback():
    """Handle M-Pesa payment callback"""
    try:
        callback_data = request.get_json()
        print("📞 M-Pesa Callback Received:", json.dumps(callback_data, indent=2))

        # Extract callback data
        result_code = (
            callback_data.get("Body", {}).get("stkCallback", {}).get("ResultCode")
        )
        checkout_request_id = (
            callback_data.get("Body", {})
            .get("stkCallback", {})
            .get("CheckoutRequestID")
        )
        result_desc = (
            callback_data.get("Body", {}).get("stkCallback", {}).get("ResultDesc")
        )

        print(f"🔍 Callback ResultCode: {result_code}")
        print(f"🔍 Callback CheckoutRequestID: {checkout_request_id}")

        if result_code == 0:
            # Payment successful
            print(f"✅ Payment successful for CheckoutRequestID: {checkout_request_id}")
            # Find order and update status
            order = Order.query.filter_by(payment_intent_id=checkout_request_id).first()
            if order:
                order.payment_status = "completed"
                order.status = OrderStatus.CONFIRMED
                db.session.commit()
                print(f"✅ Updated order #{order.id} payment status to completed")
        else:
            # Payment failed
            print(f"❌ Payment failed for CheckoutRequestID: {checkout_request_id}")
            print(f"❌ Error: {result_desc}")
            order = Order.query.filter_by(payment_intent_id=checkout_request_id).first()
            if order:
                order.payment_status = "failed"
                db.session.commit()
                print(f"❌ Updated order #{order.id} payment status to failed")

        return jsonify({"ResultCode": 0, "ResultDesc": "Success"})

    except Exception as e:
        print(f"❌ Callback error: {str(e)}")
        return jsonify({"ResultCode": 1, "ResultDesc": "Failed"})


@payments_bp.route(
    "/payments/check-payment/<string:checkout_request_id>", methods=["GET"]
)
@jwt_required()
def check_payment_status(checkout_request_id):
    """Check payment status"""
    try:
        access_token = get_mpesa_access_token()
        if not access_token:
            return jsonify({"message": "Service unavailable"}), 500

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        password, timestamp = generate_mpesa_password()

        query_data = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id,
        }

        response = requests.post(
            "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query",
            json=query_data,
            headers=headers,
        )

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"message": "Failed to check status"}), 500

    except Exception as e:
        return jsonify({"message": "Status check failed", "error": str(e)}), 500
