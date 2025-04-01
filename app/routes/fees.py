from flask import Blueprint, request, jsonify
from app import db
from app.models import Student, FeeTransaction

fees_bp = Blueprint("fees", __name__)  # ✅ Renamed to 'fees_bp'

@fees_bp.route("/<int:student_id>", methods=["POST"])
def add_fee_transaction(student_id):
    data = request.get_json() or {}
    amount = data.get("amount")
    mode = data.get("mode")
    
    if amount is None or mode not in ["UPI", "Cash"]:
        return jsonify({"error": "Invalid input: 'amount' and 'mode' (UPI or Cash) required."}), 400

    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found."}), 404

    try:
        transaction = FeeTransaction(student_id=student_id, amount=amount, mode=mode)
        db.session.add(transaction)
        student.total_fee_paid += amount
        db.session.commit()
        return jsonify({"message": "Fee transaction recorded successfully."}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@fees_bp.route("/<int:student_id>", methods=["GET"])
def get_fee_transactions(student_id):
    transactions = FeeTransaction.query.filter_by(student_id=student_id).all()
    data = [
        {
            "id": t.id,
            "amount": float(t.amount),
            "mode": t.mode,
            "timestamp": t.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        } 
        for t in transactions
    ]
    return jsonify({"fee_transactions": data}), 200
