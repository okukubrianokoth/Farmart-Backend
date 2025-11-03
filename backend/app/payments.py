from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Order, OrderStatus, User, PaymentLog
import requests
import base64
from datetime import datetime
import os
import json

payments_bp = Blueprint("payments", __name__, url_prefix="/api/payments")

# --- Environment Variables ---
MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE")
MPESA_BASE_URL = os.getenv("MPESA_BASE_URL", "https://sandbox.safaricom.co.ke")

# Auto-detect callback URL from NGROK_URL if set
NGROK_URL = os.getenv("NGROK_URL")
MPESA_CALLBACK_URL = os.getenv("MPESA_CALLBACK_URL") or "{}/api/payments/mpesa-callback".format(NGROK_URL)

# --- Helper Functions ---
def get_mpesa_access_token():
    try:
        url = "{}/oauth/v1/generate?grant_type=client_credentials".format(MPESA_BASE_URL)
        resp = requests.get(url, auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET))
        resp.raise_for_status()
        token = resp.json().get("access_token")
        current_app.logger.info("🔑 M-Pesa Access Token obtained")
        return token
    except Exception as e:
        current_app.logger.error("❌ Failed to get M-PESA token: {}".format(e))
        return None

def format_phone_number(phone):
    phone = phone.strip().replace("+", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    if not phone.startswith("254"):
        raise ValueError("Invalid phone number. Use format 07XXXXXXXX.")
    return phone

# --- Endpoints ---
@payments_bp.route("/initiate-payment", methods=["POST"])
@jwt_required()
def initiate_payment():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        order_id = data.get("order_id")
        phone_number = data.get("phone_number") or data.get("phone")
        if not order_id or not phone_number:
            return jsonify({"error": "Missing order_id or phone_number"}), 400

        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404

        formatted_phone = format_phone_number(phone_number)
        token = get_mpesa_access_token()
        if not token:
            return jsonify({"error": "Unable to get M-PESA access token"}), 500

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode((MPESA_SHORTCODE + MPESA_PASSKEY + timestamp).encode()).decode()

        payload = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(order.total_amount),
            "PartyA": formatted_phone,
            "PartyB": MPESA_SHORTCODE,
            "PhoneNumber": formatted_phone,
            "CallBackURL": MPESA_CALLBACK_URL,
            "AccountReference": "Order{}".format(order.id),
            "TransactionDesc": "Farmart Order Payment",
        }

        headers = {"Authorization": "Bearer {}".format(token)}
        resp = requests.post(
            "{}/mpesa/stkpush/v1/processrequest".format(MPESA_BASE_URL),
            json=payload,
            headers=headers,
            timeout=30
        )
        resp_data = resp.json()

        # Log INITIATE
        db.session.add(
            PaymentLog(
                order_id=order.id,
                event_type="INITIATE",
                payload={"request": payload, "response": resp_data}
            )
        )
        db.session.commit()

        if resp.status_code != 200 or "errorCode" in resp_data:
            current_app.logger.error("❌ STK Push failed: {}".format(json.dumps(resp_data, indent=4)))
            return jsonify({"error": "Failed to initiate M-PESA payment", "details": resp_data}), 500

        order.checkout_request_id = resp_data.get("CheckoutRequestID")
        order.payment_status = "pending"
        db.session.commit()

        current_app.logger.info("✅ STK Push initiated for Order #{} ({})".format(order.id, formatted_phone))
        return jsonify({"message": "M-PESA STK Push initiated", "checkout_request_id": order.checkout_request_id}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error("🔥 Error initiate_payment: {}".format(e))
        return jsonify({"error": "Internal Server Error"}), 500

@payments_bp.route("/mpesa-callback", methods=["POST"])
def mpesa_callback():
    try:
        data = request.get_json()
        db.session.add(PaymentLog(event_type="CALLBACK", payload=data))
        db.session.commit()

        body = data.get("Body", {}).get("stkCallback", {})
        checkout_request_id = body.get("CheckoutRequestID")
        result_code = body.get("ResultCode")

        order = Order.query.filter_by(checkout_request_id=checkout_request_id).first()
        if not order:
            current_app.logger.warning("⚠️ Order not found for CheckoutRequestID: {}".format(checkout_request_id))
            return jsonify({"error": "Order not found"}), 404

        if result_code == 0:
            order.payment_status = "paid"
            current_app.logger.info("✅ Payment success for Order #{}".format(order.id))
        else:
            order.payment_status = "failed"
            current_app.logger.warning("❌ Payment failed for Order #{}".format(order.id))

        db.session.commit()
        return jsonify({"message": "Callback processed"}), 200
    except Exception as e:
        current_app.logger.error("💥 Error mpesa_callback: {}".format(e))
        return jsonify({"error": "Internal server error"}), 500

@payments_bp.route("/check-payment/<checkout_request_id>", methods=["GET"])
def check_payment_status(checkout_request_id):
    try:
        order = Order.query.filter_by(checkout_request_id=checkout_request_id).first()
        if not order:
            return jsonify({"error": "Order not found"}), 404

        status = order.payment_status
        if status not in ["pending", "paid", "failed"]:
            status = "pending"

        db.session.add(
            PaymentLog(
                order_id=order.id,
                event_type="CHECK_STATUS",
                payload={"checkout_request_id": checkout_request_id, "status": status}
            )
        )
        db.session.commit()

        return jsonify({"order_id": order.id, "payment_status": status}), 200
    except Exception as e:
        current_app.logger.error("💥 Error check_payment_status: {}".format(e))
        return jsonify({"error": "Internal server error"}), 500
