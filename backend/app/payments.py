# from flask import Blueprint, request, jsonify, current_app
# from flask_jwt_extended import jwt_required, get_jwt_identity
# from app import db
# from app.models import Order, OrderStatus, User, PaymentLog
# import requests
# import base64
# from datetime import datetime
# import os
# import json

# # ✅ Blueprint prefix ensures all endpoints start with /api/payments/
# payments_bp = Blueprint("payments", __name__, url_prefix="/api/payments")

# # --- ⚙️ Load environment variables ---
# MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
# MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
# MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
# MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE")
# MPESA_BASE_URL = os.getenv("MPESA_BASE_URL", "https://sandbox.safaricom.co.ke")
# MPESA_CALLBACK_URL = os.getenv(
#     "MPESA_CALLBACK_URL",
#     "https://your-backend.onrender.com/api/payments/mpesa-callback"
# )

# # --- 🔐 Helper functions ---
# def get_mpesa_access_token():
#     """Request OAuth token from M-PESA API"""
#     try:
#         url = f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
#         resp = requests.get(url, auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET))
#         resp.raise_for_status()
#         token = resp.json().get("access_token")
#         return token
#     except Exception as e:
#         # Use current_app.logger only inside function
#         current_app.logger.error(f"❌ Failed to get M-Pesa access token: {e}")
#         return None


# def format_phone_number(phone):
#     """Ensure phone is in Safaricom 2547XXXXXXXX format"""
#     phone = phone.strip().replace("+", "")
#     if phone.startswith("0"):
#         phone = "254" + phone[1:]
#     if not phone.startswith("254"):
#         raise ValueError("Invalid phone number. Use format 07XXXXXXXX.")
#     return phone


# # --- 🚀 Initiate M-PESA STK Push ---
# @payments_bp.route("/initiate-payment", methods=["POST"])
# @jwt_required()
# def initiate_payment():
#     try:
#         data = request.get_json()
#         current_app.logger.info(f"🧾 Incoming Payment Data: {data}")

#         user_id = get_jwt_identity()
#         user = User.query.get(user_id)
#         if not user:
#             return jsonify({"error": "User not found"}), 404

#         order_id = data.get("order_id")
#         phone_number = data.get("phone_number") or data.get("phone")

#         if not order_id or not phone_number:
#             current_app.logger.warning(f"⚠️ Missing data -> order_id: {order_id}, phone_number: {phone_number}")
#             return jsonify({"error": "Missing order_id or phone_number"}), 400

#         order = Order.query.get(order_id)
#         if not order:
#             return jsonify({"error": "Order not found"}), 404

#         formatted_phone = format_phone_number(phone_number)
#         access_token = get_mpesa_access_token()
#         if not access_token:
#             return jsonify({"error": "Unable to get M-PESA access token"}), 500

#         timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
#         password = base64.b64encode(
#             (MPESA_SHORTCODE + MPESA_PASSKEY + timestamp).encode()
#         ).decode()

#         payload = {
#             "BusinessShortCode": MPESA_SHORTCODE,
#             "Password": password,
#             "Timestamp": timestamp,
#             "TransactionType": "CustomerPayBillOnline",
#             "Amount": int(order.total_amount),
#             "PartyA": formatted_phone,
#             "PartyB": MPESA_SHORTCODE,
#             "PhoneNumber": formatted_phone,
#             "CallBackURL": MPESA_CALLBACK_URL,
#             "AccountReference": f"Order{order.id}",
#             "TransactionDesc": "Farmart Order Payment",
#         }

#         headers = {"Authorization": f"Bearer {access_token}"}

#         stk_url = f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
#         response = requests.post(stk_url, json=payload, headers=headers)
#         response_data = response.json()

#         # 🧾 Log payment initiation attempt
#         db.session.add(PaymentLog(
#             order_id=order.id,
#             event_type="INITIATE",
#             payload={"request": payload, "response": response_data}
#         ))
#         db.session.commit()

#         if response.status_code != 200 or "errorCode" in response_data:
#             current_app.logger.error(f"❌ M-PESA STK Push failed: {json.dumps(response_data, indent=4)}")
#             return jsonify({
#                 "error": "Failed to initiate M-PESA payment",
#                 "details": response_data
#             }), 500

#         checkout_request_id = response_data.get("CheckoutRequestID")
#         order.checkout_request_id = checkout_request_id
#         order.payment_status = OrderStatus.PENDING.value
#         db.session.commit()

#         current_app.logger.info(f"✅ M-PESA STK Push initiated for Order #{order.id} ({formatted_phone})")

#         return jsonify({
#             "message": "M-PESA STK Push initiated successfully",
#             "checkout_request_id": checkout_request_id
#         }), 200

#     except ValueError as e:
#         return jsonify({"error": str(e)}), 400
#     except Exception as e:
#         current_app.logger.error(f"🔥 Unexpected error during payment initiation: {e}")
#         return jsonify({"error": "Internal Server Error"}), 500


# # --- 📥 Handle M-PESA Callback ---
# @payments_bp.route("/mpesa-callback", methods=["POST"])
# def mpesa_callback():
#     try:
#         data = request.get_json()
#         current_app.logger.info(f"📬 M-PESA Callback received: {json.dumps(data, indent=4)}")

#         # 🧾 Log callback
#         db.session.add(PaymentLog(event_type="CALLBACK", payload=data))
#         db.session.commit()

#         body = data.get("Body", {}).get("stkCallback", {})
#         checkout_request_id = body.get("CheckoutRequestID")
#         result_code = body.get("ResultCode")
#         result_desc = body.get("ResultDesc")

#         order = Order.query.filter_by(checkout_request_id=checkout_request_id).first()
#         if not order:
#             current_app.logger.warning(f"⚠️ Order not found for CheckoutRequestID: {checkout_request_id}")
#             return jsonify({"error": "Order not found"}), 404

#         if result_code == 0:
#             order.payment_status = OrderStatus.PAID.value
#             current_app.logger.info(f"✅ Payment success for Order #{order.id}")
#         else:
#             order.payment_status = OrderStatus.FAILED.value
#             current_app.logger.warning(f"❌ Payment failed for Order #{order.id}: {result_desc}")

#         db.session.commit()
#         return jsonify({"message": "Callback processed successfully"}), 200

#     except Exception as e:
#         current_app.logger.error(f"💥 Error in M-PESA callback: {e}")
#         return jsonify({"error": "Internal server error"}), 500


# # --- 🔎 Check Payment Status (frontend polling) ---
# @payments_bp.route("/check-payment/<checkout_request_id>", methods=["GET"])
# def check_payment_status(checkout_request_id):
#     try:
#         order = Order.query.filter_by(checkout_request_id=checkout_request_id).first()
#         if not order:
#             return jsonify({"error": "Order not found"}), 404

#         # 🧾 Log status check
#         db.session.add(PaymentLog(
#             order_id=order.id,
#             event_type="CHECK_STATUS",
#             payload={"checkout_request_id": checkout_request_id, "status": order.payment_status}
#         ))
#         db.session.commit()

#         return jsonify({
#             "order_id": order.id,
#             "payment_status": order.payment_status
#         }), 200

#     except Exception as e:
#         current_app.logger.error(f"💥 Error checking payment status: {e}")
#         return jsonify({"error": "Internal server error"}), 500

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

# Environment Variables
MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE")
MPESA_BASE_URL = os.getenv("MPESA_BASE_URL", "https://sandbox.safaricom.co.ke")
MPESA_CALLBACK_URL = os.getenv("MPESA_CALLBACK_URL")

# --- Helpers ---
def get_mpesa_access_token():
    try:
        url = f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
        resp = requests.get(url, auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET))
        resp.raise_for_status()
        return resp.json().get("access_token")
    except Exception as e:
        current_app.logger.error(f"❌ Failed to get M-PESA token: {e}")
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
            "AccountReference": f"Order{order.id}",
            "TransactionDesc": "Farmart Order Payment",
        }

        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.post(f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest", json=payload, headers=headers)
        resp_data = resp.json()

        # Log INITIATE
        db.session.add(PaymentLog(order_id=order.id, event_type="INITIATE", payload={"request": payload, "response": resp_data}))
        db.session.commit()

        if resp.status_code != 200 or "errorCode" in resp_data:
            return jsonify({"error": "Failed to initiate M-PESA payment", "details": resp_data}), 500

        order.checkout_request_id = resp_data.get("CheckoutRequestID")
        order.payment_status = "pending"
        db.session.commit()

        return jsonify({"message": "M-PESA STK Push initiated", "checkout_request_id": order.checkout_request_id}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"🔥 Error initiate_payment: {e}")
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
            return jsonify({"error": "Order not found"}), 404

        if result_code == 0:
            order.payment_status = "paid"
        else:
            order.payment_status = "failed"

        db.session.commit()
        return jsonify({"message": "Callback processed"}), 200
    except Exception as e:
        current_app.logger.error(f"💥 Error mpesa_callback: {e}")
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

        db.session.add(PaymentLog(order_id=order.id, event_type="CHECK_STATUS", payload={"checkout_request_id": checkout_request_id, "status": status}))
        db.session.commit()

        return jsonify({"order_id": order.id, "payment_status": status}), 200
    except Exception as e:
        current_app.logger.error(f"💥 Error check_payment_status: {e}")
        return jsonify({"error": "Internal server error"}), 500
