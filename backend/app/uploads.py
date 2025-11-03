# backend/app/uploads.py
from flask import Blueprint, request, jsonify
import cloudinary
import cloudinary.uploader
import os

upload_bp = Blueprint("upload", __name__)

# ✅ Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

@upload_bp.route("/upload", methods=["POST"])
def upload_image():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]

    try:
        result = cloudinary.uploader.upload(file)
        image_url = result.get("secure_url")
        return jsonify({"image_url": image_url}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
