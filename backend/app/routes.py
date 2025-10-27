from flask import Blueprint

main = Blueprint('main', __name__)

@main.route('/ping')
def ping():
    return {"message": "pong"}
