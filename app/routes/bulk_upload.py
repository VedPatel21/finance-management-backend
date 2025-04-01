from flask import Blueprint, request, jsonify
import os
from werkzeug.utils import secure_filename
from app.models import Student
from app.extensions import db

bulk_upload_bp = Blueprint("bulk_upload", __name__)
ALLOWED_EXTENSIONS = {'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bulk_upload_bp.route("/", methods=["POST"])
def bulk_upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    filename = secure_filename(file.filename)
    upload_path = os.path.join("uploads", filename)
    file.save(upload_path)

    try:
        os.remove(upload_path)
        return jsonify({"message": "File processed successfully."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
