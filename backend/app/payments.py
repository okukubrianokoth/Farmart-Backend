# import base64
# import json
# from datetime import datetime

# import requests
# from flask import Blueprint, jsonify, request
# from flask_jwt_extended import get_jwt_identity, jwt_required

# from app import db
# from app.models import Order, OrderStatus, User
# from app.utils import get_mpesa_token


# payments_bp = Blueprint("payments", __name__)

# # M-PESA DARAJA API CREDENTIALS (move to config in production)
# MPESA_CONSUMER_KEY = "0MGI4OURcyORSUN0BjmvzDW77r6dGyjRYcZdRYdbHLC20Xjl"
# MPESA_CONSUMER_SECRET = (
#     "4UVbzIvUBoV5HxNFHDs3ZCSwsVuSFSDXRsWbSyiOEqB9NYtYZu60MZnpRC56rlZ8"
# )

# # SHORTCODE / PASSKEY
# MPESA_SHORTCODE = "174379"
# MPESA_PASSKEY = (
#     "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
# )

# # CALLBACK URL — must be publicly reachable (ngrok used here)
# MPESA_CALLBACK_URL = (
#     "https://coral-salamanderlike-ilona.ngrok-free.dev/api/payments/mpesa/callback"
# )


# def generate_mpesa_password():
#     """Generate M-Pesa API password."""
#     timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
#     data_to_encode = MPESA_SHORTCODE + MPESA_PASSKEY + timestamp
#     password = base64.b64encode(data_to_encode.encode()).decode()
#     return password, timestamp


# @payments_bp.route("/payments/mpesa/stk-push", methods=["POST"])
# @jwt_required()
# def initiate_mpesa_payment():
#     """Initiate M-Pesa STK Push payment."""
#     try:
#         current_user_id = get_jwt_identity()
#         data = request.get_json() or {}

#         order_id = data.get("order_id")
#         phone_number = data.get("phone_number")

#         if not order_id or not phone_number:
#             return jsonify({"message": "Order ID and phone number are required"}), 400

#         order = Order.query.get_or_404(order_id)
#         if order.user_id != current_user_id:
#             return jsonify({"message": "Not authorized"}), 403

#         # Format phone number to 254...
#         if phone_number.startswith("0"):
#             phone_number = "254" + phone_number[1:]
#         elif phone_number.startswith("+"):
#             phone_number = phone_number[1:]
#         elif not phone_number.startswith("254"):
#             phone_number = "254" + phone_number

#         # Get access token (cached in app.utils.get_mpesa_token)
#         access_token = get_mpesa_token()
#         if not access_token:
#             return jsonify({"message": "Failed to get M-Pesa access token"}), 503

#         password, timestamp = generate_mpesa_password()
#         amount = int(order.total_amount) if order.total_amount else 1

#         stk_push_data = {
#             "BusinessShortCode": MPESA_SHORTCODE,
#             "Password": password,
#             "Timestamp": timestamp,
#             "TransactionType": "CustomerPayBillOnline",
#             "Amount": amount,
#             "PartyA": phone_number,
#             "PartyB": MPESA_SHORTCODE,
#             "PhoneNumber": phone_number,
#             "CallBackURL": MPESA_CALLBACK_URL,
#             "AccountReference": f"Farmart{order.id}",
#             "TransactionDesc": f"Payment for Order #{order.id}",
#         }

#         headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

#         response = requests.post(
#             "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
#             json=stk_push_data,
#             headers=headers,
#             timeout=30,
#         )

#         if response.status_code == 200:
#             try:
#                 response_data = response.json()
#             except ValueError:
#                 return jsonify({"message": "Invalid response from M-Pesa"}), 502

#             if response_data.get("ResponseCode") == "0":
#                 order.payment_intent_id = response_data.get("CheckoutRequestID")
#                 order.payment_status = "pending"
#                 db.session.commit()
#                 return (
#                     jsonify(
#                         {
#                             "message": "Payment initiated successfully",
#                             "checkout_request_id": response_data.get("CheckoutRequestID"),
#                             "customer_message": response_data.get("CustomerMessage"),
#                         }
#                     ),
#                     200,
#                 )
#             else:
#                 return (
#                     jsonify(
#                         {
#                             "message": "Payment initiation failed",
#                             "error": response_data.get("ResponseDescription", response.text),
#                         }
#                     ),
#                     400,
#                 )

#         if response.status_code == 429:
#             retry_after = response.headers.get("Retry-After")
#             return (
#                 jsonify(
#                     {
#                         "message": "Rate limited by M-Pesa API",
#                         "retry_after": retry_after,
#                         "details": response.text,
#                     }
#                 ),
#                 429,
#             )

#         return (
#             jsonify(
#                 {
#                     "message": "Failed to connect to M-Pesa API",
#                     "status_code": response.status_code,
#                     "error": response.text,
#                 }
#             ),
#             502,
#         )

#     except requests.Timeout:
#         return jsonify({"message": "M-Pesa request timed out"}), 504
#     except requests.ConnectionError:
#         return jsonify({"message": "Connection error to M-Pesa API"}), 502
#     except Exception as e:
#         print("initiate_mpesa_payment error:", str(e))
#         return jsonify({"message": "Payment initiation failed", "error": str(e)}), 500


# @payments_bp.route("/payments/mpesa/callback", methods=["POST"])
# def mpesa_callback():
#     """Handle M-Pesa callback."""
#     try:
#         callback_data = request.get_json() or {}
#         print("Callback received:", json.dumps(callback_data, indent=2))

#         stk = callback_data.get("Body", {}).get("stkCallback", {})
#         result_code = stk.get("ResultCode")
#         checkout_request_id = stk.get("CheckoutRequestID")
#         result_desc = stk.get("ResultDesc")

#         order = None
#         if checkout_request_id:
#             order = Order.query.filter_by(payment_intent_id=checkout_request_id).first()

#         if result_code == 0:
#             if order:
#                 order.payment_status = "completed"
#                 order.status = OrderStatus.CONFIRMED
#                 db.session.commit()
#         else:
#             if order:
#                 order.payment_status = "failed"
#                 db.session.commit()
#             print(f"Payment failed/cancelled: {checkout_request_id} - {result_desc}")

#         return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200

#     except Exception as e:
#         print("mpesa_callback error:", str(e))
#         return jsonify({"ResultCode": 1, "ResultDesc": "Failed"}), 500


# @payments_bp.route("/payments/check-payment/<string:checkout_request_id>", methods=["GET"])
# @jwt_required()
# def check_payment_status(checkout_request_id):
#     """Check M-Pesa payment status with defensive handling and DB-first lookup."""
#     try:
#         order = Order.query.filter_by(payment_intent_id=checkout_request_id).first()
#         if order and order.payment_status in ("completed", "failed"):
#             return (
#                 jsonify(
#                     {
#                         "checkout_request_id": checkout_request_id,
#                         "payment_status": order.payment_status,
#                         "order_id": order.id,
#                         "message": "Status retrieved from server records",
#                     }
#                 ),
#                 200,
#             )

#         access_token = get_mpesa_token()
#         if not access_token:
#             return jsonify({"message": "Failed to get access token"}), 503

#         headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

#         password, timestamp = generate_mpesa_password()
#         query_data = {
#             "BusinessShortCode": MPESA_SHORTCODE,
#             "Password": password,
#             "Timestamp": timestamp,
#             "CheckoutRequestID": checkout_request_id,
#         }

#         response = requests.post(
#             "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query",
#             json=query_data,
#             headers=headers,
#             timeout=30,
#         )

#         if response.status_code == 429:
#             retry_after = response.headers.get("Retry-After")
#             return (
#                 jsonify({"message": "Rate limited by M-Pesa API", "retry_after": retry_after}),
#                 429,
#             )

#         if response.status_code != 200:
#             return (
#                 jsonify(
#                     {
#                         "message": "Failed to check payment status",
#                         "status_code": response.status_code,
#                         "error": response.text,
#                     }
#                 ),
#                 502,
#             )

#         try:
#             resp_json = response.json()
#         except ValueError:
#             return jsonify({"message": "Invalid JSON response from M-Pesa"}), 502

#         result_code = resp_json.get("ResultCode") or resp_json.get("resultCode") or resp_json.get("ResponseCode")

#         if order:
#             if str(result_code) == "0":
#                 order.payment_status = "completed"
#                 order.status = OrderStatus.CONFIRMED
#                 db.session.commit()
#             elif result_code is not None:
#                 order.payment_status = "failed"
#                 db.session.commit()

#         return jsonify({"checkout_request_id": checkout_request_id, "m_pesa_response": resp_json}), 200

#     except requests.Timeout:
#         return jsonify({"message": "Status check request timed out"}), 504
#     except requests.ConnectionError:
#         return jsonify({"message": "Connection error while checking payment"}), 502
#     except Exception as e:
#         print("check_payment_status error:", str(e))
#         return jsonify({"message": "Status check failed", "error": str(e)}), 500

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Order, OrderStatus, User, PaymentLog
import requests
import base64
from datetime import datetime
import os
import json

payments_bp = Blueprint("payments", __name__)

# --- ⚙️ Load environment variables ---
MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE")
MPESA_BASE_URL = os.getenv("MPESA_BASE_URL", "https://sandbox.safaricom.co.ke")
MPESA_CALLBACK_URL = os.getenv(
    "MPESA_CALLBACK_URL",
    "https://your-backend.onrender.com/api/payments/mpesa-callback"
)


# --- 🔐 Helper functions ---
def get_mpesa_access_token():
    """Request OAuth token from M-PESA API"""
    try:
        url = f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
        resp = requests.get(url, auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET))
        resp.raise_for_status()
        token = resp.json().get("access_token")
        return token
    except Exception as e:
        current_app.logger.error(f"❌ Failed to get access token: {e}")
        return None


def format_phone_number(phone):
    """Ensure phone is in Safaricom 2547XXXXXXXX format"""
    phone = phone.strip().replace("+", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    if not phone.startswith("254"):
        raise ValueError("Invalid phone number. Use format 07XXXXXXXX.")
    return phone


# --- 🚀 Initiate M-PESA STK Push ---
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
        phone_number = data.get("phone_number")

        if not order_id or not phone_number:
            return jsonify({"error": "Missing order_id or phone_number"}), 400

        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404

        formatted_phone = format_phone_number(phone_number)
        access_token = get_mpesa_access_token()
        if not access_token:
            return jsonify({"error": "Unable to get M-PESA access token"}), 500

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(
            (MPESA_SHORTCODE + MPESA_PASSKEY + timestamp).encode()
        ).decode()

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
            "TransactionDesc": "Farmart Order Payment"
        }

        headers = {"Authorization": f"Bearer {access_token}"}

        stk_url = f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
        response = requests.post(stk_url, json=payload, headers=headers)
        response_data = response.json()

        # 🧾 Log the attempt (✅ NEW)
        db.session.add(PaymentLog(
            order_id=order.id,
            event_type="INITIATE",
            payload={"request": payload, "response": response_data}
        ))
        db.session.commit()

        if response.status_code != 200 or "errorCode" in response_data:
            current_app.logger.error(f"❌ M-PESA STK Push failed: {json.dumps(response_data, indent=4)}")
            return jsonify({
                "error": "Failed to initiate M-PESA payment",
                "details": response_data
            }), 500

        checkout_request_id = response_data.get("CheckoutRequestID")
        order.checkout_request_id = checkout_request_id
        order.payment_status = OrderStatus.PENDING.value
        db.session.commit()

        current_app.logger.info(f"✅ M-PESA STK Push initiated for Order #{order.id} ({formatted_phone})")

        return jsonify({
            "message": "M-PESA STK Push initiated successfully",
            "checkout_request_id": checkout_request_id
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"🔥 Unexpected error during payment initiation: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


# --- 📥 Handle M-PESA Callback ---
@payments_bp.route("/mpesa-callback", methods=["POST"])
def mpesa_callback():
    try:
        data = request.get_json()
        current_app.logger.info(f"📬 M-PESA Callback received: {json.dumps(data, indent=4)}")

        # 🧾 Log callback (✅ NEW)
        db.session.add(PaymentLog(
            event_type="CALLBACK",
            payload=data
        ))
        db.session.commit()

        body = data.get("Body", {}).get("stkCallback", {})
        checkout_request_id = body.get("CheckoutRequestID")
        result_code = body.get("ResultCode")
        result_desc = body.get("ResultDesc")

        order = Order.query.filter_by(checkout_request_id=checkout_request_id).first()
        if not order:
            current_app.logger.warning(f"⚠️ Order not found for CheckoutRequestID: {checkout_request_id}")
            return jsonify({"error": "Order not found"}), 404

        if result_code == 0:
            order.payment_status = OrderStatus.PAID.value
            current_app.logger.info(f"✅ Payment success for Order #{order.id}")
        else:
            order.payment_status = OrderStatus.FAILED.value
            current_app.logger.warning(f"❌ Payment failed for Order #{order.id}: {result_desc}")

        db.session.commit()
        return jsonify({"message": "Callback processed successfully"}), 200

    except Exception as e:
        current_app.logger.error(f"💥 Error in M-PESA callback: {e}")
        return jsonify({"error": "Internal server error"}), 500


# --- 🔎 Check Payment Status (frontend polling) ---
@payments_bp.route("/check-payment/<checkout_request_id>", methods=["GET"])
def check_payment_status(checkout_request_id):
    try:
        order = Order.query.filter_by(checkout_request_id=checkout_request_id).first()
        if not order:
            return jsonify({"error": "Order not found"}), 404

        # 🧾 Log check request (✅ NEW)
        db.session.add(PaymentLog(
            order_id=order.id,
            event_type="CHECK_STATUS",
            payload={"checkout_request_id": checkout_request_id, "status": order.payment_status}
        ))
        db.session.commit()

        return jsonify({
            "order_id": order.id,
            "payment_status": order.payment_status
        }), 200

    except Exception as e:
        current_app.logger.error(f"💥 Error checking payment status: {e}")
        return jsonify({"error": "Internal server error"}), 500
