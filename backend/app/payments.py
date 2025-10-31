from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Order, OrderStatus, User
from app.utils import get_mpesa_token
import requests
import base64
from datetime import datetime
import json
import time

payments_bp = Blueprint('payments', __name__)

# M-PESA DARAJA API CREDENTIALS (move to config in production)
MPESA_CONSUMER_KEY = '0MGI4OURcyORSUN0BjmvzDW77r6dGyjRYcZdRYdbHLC20Xjl'
MPESA_CONSUMER_SECRET = '4UVbzIvUBoV5HxNFHDs3ZCSwsVuSFSDXRsWbSyiOEqB9NYtYZu60MZnpRC56rlZ8'

# SHORTCODE / PASSKEY
MPESA_SHORTCODE = '174379'
MPESA_PASSKEY = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'

# CALLBACK URL — must be publicly reachable (ngrok used here)
MPESA_CALLBACK_URL = "https://coral-salamanderlike-ilona.ngrok-free.dev/api/payments/mpesa/callback"


def generate_mpesa_password():
    """Generate M-Pesa API password."""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = MPESA_SHORTCODE + MPESA_PASSKEY + timestamp
    password = base64.b64encode(data_to_encode.encode()).decode()
    return password, timestamp


@payments_bp.route('/payments/mpesa/stk-push', methods=['POST'])
@jwt_required()
def initiate_mpesa_payment():
    """Initiate M-Pesa STK Push payment."""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}

        order_id = data.get('order_id')
        phone_number = data.get('phone_number')

        if not order_id or not phone_number:
            return jsonify({'message': 'Order ID and phone number are required'}), 400

        order = Order.query.get_or_404(order_id)
        if order.user_id != current_user_id:
            return jsonify({'message': 'Not authorized'}), 403

        # Format phone number to 254...
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+'):
            phone_number = phone_number[1:]
        elif not phone_number.startswith('254'):
            phone_number = '254' + phone_number

        # Get access token (cached in app.utils.get_mpesa_token)
        access_token = get_mpesa_token()
        if not access_token:
            return jsonify({'message': 'Failed to get M-Pesa access token'}), 503

        password, timestamp = generate_mpesa_password()
        amount = int(order.total_amount) if order.total_amount else 1

        stk_push_data = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": MPESA_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": MPESA_CALLBACK_URL,
            "AccountReference": f"Farmart{order.id}",
            "TransactionDesc": f"Payment for Order #{order.id}"
        }

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        response = requests.post(
            'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
            json=stk_push_data,
            headers=headers,
            timeout=30
        )

        # If Safaricom accepted the request (not yet payment completed)
        if response.status_code == 200:
            try:
                response_data = response.json()
            except ValueError:
                return jsonify({'message': 'Invalid response from M-Pesa'}), 502

            if response_data.get('ResponseCode') == '0':
                order.payment_intent_id = response_data.get('CheckoutRequestID')
                order.payment_status = 'pending'
                db.session.commit()
                return jsonify({
                    'message': 'Payment initiated successfully',
                    'checkout_request_id': response_data.get('CheckoutRequestID'),
                    'customer_message': response_data.get('CustomerMessage')
                }), 200
            else:
                # M-Pesa returned an error response (e.g., invalid details)
                return jsonify({
                    'message': 'Payment initiation failed',
                    'error': response_data.get('ResponseDescription', response.text)
                }), 400

        # handle specific status codes
        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After')
            body = response.text
            return jsonify({
                'message': 'Rate limited by M-Pesa API',
                'retry_after': retry_after,
                'details': body
            }), 429

        return jsonify({
            'message': 'Failed to connect to M-Pesa API',
            'status_code': response.status_code,
            'error': response.text
        }), 502

    except requests.Timeout:
        return jsonify({'message': 'M-Pesa request timed out'}), 504
    except requests.ConnectionError:
        return jsonify({'message': 'Connection error to M-Pesa API'}), 502
    except Exception as e:
        print("initiate_mpesa_payment error:", str(e))
        return jsonify({'message': 'Payment initiation failed', 'error': str(e)}), 500


@payments_bp.route('/payments/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """Handle M-Pesa callback."""
    try:
        callback_data = request.get_json() or {}
        print("Callback received:", json.dumps(callback_data, indent=2))

        stk = callback_data.get('Body', {}).get('stkCallback', {})
        result_code = stk.get('ResultCode')
        checkout_request_id = stk.get('CheckoutRequestID')
        result_desc = stk.get('ResultDesc')

        order = None
        if checkout_request_id:
            order = Order.query.filter_by(payment_intent_id=checkout_request_id).first()

        if result_code == 0:
            # successful
            if order:
                order.payment_status = 'completed'
                order.status = OrderStatus.CONFIRMED
                db.session.commit()
        else:
            # failed / cancelled
            if order:
                order.payment_status = 'failed'
                db.session.commit()
            print(f"Payment failed/cancelled: {checkout_request_id} - {result_desc}")

        return jsonify({'ResultCode': 0, 'ResultDesc': 'Success'}), 200

    except Exception as e:
        print("mpesa_callback error:", str(e))
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Failed'}), 500


@payments_bp.route('/payments/check-payment/<string:checkout_request_id>', methods=['GET'])
@jwt_required()
def check_payment_status(checkout_request_id):
    """Check M-Pesa payment status with defensive handling and DB-first lookup."""
    try:
        # 1) If we already recorded payment status in DB, return it
        order = Order.query.filter_by(payment_intent_id=checkout_request_id).first()
        if order and order.payment_status in ('completed', 'failed'):
            return jsonify({
                'checkout_request_id': checkout_request_id,
                'payment_status': order.payment_status,
                'order_id': order.id,
                'message': 'Status retrieved from server records'
            }), 200

        # 2) If not in DB (or pending), query Safaricom
        access_token = get_mpesa_token()
        if not access_token:
            return jsonify({'message': 'Failed to get access token'}), 503

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        password, timestamp = generate_mpesa_password()
        query_data = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }

        response = requests.post(
            'https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query',
            json=query_data,
            headers=headers,
            timeout=30
        )

        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After')
            return jsonify({
                'message': 'Rate limited by M-Pesa API',
                'retry_after': retry_after
            }), 429

        if response.status_code != 200:
            return jsonify({
                'message': 'Failed to check payment status',
                'status_code': response.status_code,
                'error': response.text
            }), 502

        try:
            resp_json = response.json()
        except ValueError:
            return jsonify({'message': 'Invalid JSON response from M-Pesa'}), 502

        # Fix W504: operator at start of line
        result_code = (resp_json.get('ResultCode')
                       or resp_json.get('resultCode')
                       or resp_json.get('ResponseCode'))

        if order:
            if str(result_code) in ('0', '0'):
                order.payment_status = 'completed'
                order.status = OrderStatus.CONFIRMED
                db.session.commit()
            elif result_code is not None:
                order.payment_status = 'failed'
                db.session.commit()

        return jsonify({
            'checkout_request_id': checkout_request_id,
            'm_pesa_response': resp_json
        }), 200

    except requests.Timeout:
        return jsonify({'message': 'Status check request timed out'}), 504
    except requests.ConnectionError:
        return jsonify({'message': 'Connection error while checking payment'}), 502
    except Exception as e:
        print("check_payment_status error:", str(e))
        return jsonify({'message': 'Status check failed', 'error': str(e)}), 500
