from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models import Student, FeeTransactionHistory
from sqlalchemy.sql import func  # Import SQLAlchemy functions
from datetime import datetime

students_bp = Blueprint("students", __name__)

# Route to fetch student data
@students_bp.route("/", methods=["GET"])
def get_students():
    query = Student.query
    search = request.args.get("search")
    sort = request.args.get("sort")

    # Filter by search query
    if search:
        query = query.filter(Student.full_name.ilike(f"%{search}%"))

    # Sorting options
    if sort == "pending_asc":
        query = query.order_by((Student.expected_fee - Student.total_fee_paid).asc())
    elif sort == "pending_desc":
        query = query.order_by((Student.expected_fee - Student.total_fee_paid).desc())

    students = query.all()
    data = [
        {
            "id": s.id,
            "full_name": s.full_name,
            "class": s.class_name,  # Mapping model field class_name to JSON key "class"
            "expected_fee": float(s.expected_fee),
            "total_fee_paid": float(s.total_fee_paid),
            "fee_balance": float(s.expected_fee - s.total_fee_paid)
        }
        for s in students
    ]

    # Group data by class for class summary
    summary_by_class = {}
    for student in students:
        cls = student.class_name
        if cls not in summary_by_class:
            summary_by_class[cls] = 0
        summary_by_class[cls] += float(student.expected_fee - student.total_fee_paid)

    class_summary = [
        {"class": cls, "total_fee_pending": total_pending}
        for cls, total_pending in summary_by_class.items()
    ]

    return jsonify({"students": data, "class_summary": class_summary}), 200

# Route to add a new student
@students_bp.route("/", methods=["POST"])
def add_student():
    data = request.get_json() or {}
    full_name = data.get("full_name")
    class_name = data.get("class")  # Frontend sends key "class"
    expected_fee = data.get("expected_fee")

    if not full_name or not class_name or expected_fee is None:
        return jsonify({"error": "Missing required fields: full_name, class, expected_fee"}), 400

    try:
        student = Student(
            full_name=full_name,
            class_name=class_name,
            expected_fee=expected_fee
        )
        db.session.add(student)
        db.session.commit()
        return jsonify({"message": "Student added successfully", "student_id": student.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Route to update a student's data and log a transaction
@students_bp.route("/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    data = request.get_json() or {}
    student = Student.query.get(student_id)

    if not student:
        return jsonify({"error": "Student not found."}), 404

    try:
        previous_fee_paid = float(student.total_fee_paid)
        student.full_name = data.get("full_name", student.full_name)
        student.class_name = data.get("class", student.class_name)  # Maps "class" from frontend to model's class_name
        student.expected_fee = data.get("expected_fee", student.expected_fee)
        new_fee_paid = float(data.get("total_fee_paid", previous_fee_paid))

        # Calculate the additional amount paid
        amount_paid = new_fee_paid - previous_fee_paid

        # Retrieve mode and timestamp from the request
        mode = data.get("mode", "Cash")
        timestamp = data.get("timestamp", datetime.utcnow())
        # If timestamp is a string, expect "YYYY-MM-DD" format
        if not isinstance(timestamp, datetime):
            timestamp = datetime.strptime(timestamp, "%Y-%m-%d")

        # Update student's fee paid
        student.total_fee_paid = new_fee_paid

        fee_transaction = FeeTransactionHistory(
            student_id=student.id,
            student_name=student.full_name,
            class_name=student.class_name,
            amount=amount_paid,
            mode=mode,
            fee_remaining=(student.expected_fee - new_fee_paid),
            timestamp=timestamp
        )
        db.session.add(fee_transaction)

        db.session.commit()
        return jsonify({"message": "Student updated successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Route to fetch a student's fee transaction history
@students_bp.route("/history/<int:student_id>", methods=["GET"])
def get_fee_transaction_history(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found."}), 404

    transactions = FeeTransactionHistory.query.filter_by(
        student_id=student_id
    ).order_by(FeeTransactionHistory.timestamp.desc()).all()

    history_data = [
        {
            "id": t.id,
            "student_name": t.student_name,
            "class_name": t.class_name,
            "amount": float(t.amount),
            "mode": t.mode,
            "fee_remaining": float(t.fee_remaining),
            "timestamp": t.timestamp.strftime("%d-%m-%Y")
        }
        for t in transactions
    ]

    return jsonify({
        "student_id": student.id,
        "full_name": student.full_name,
        "class_name": student.class_name,
        "history": history_data
    }), 200

# Route to delete a specific transaction
@students_bp.route("/transactions/<int:transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):
    try:
        # Query the transaction by its ID
        transaction = FeeTransactionHistory.query.get(transaction_id)
        if not transaction:
            return jsonify({"error": "Transaction not found."}), 404

        # Delete the transaction from the database
        db.session.delete(transaction)
        db.session.commit()

        return jsonify({"message": "Transaction deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# New Route: Get Monthly Fee Collection Report
@students_bp.route("/fees/monthly", methods=["GET"])
def get_monthly_fee_collection():
    try:
        results = db.session.query(
            func.strftime("%Y-%m", FeeTransactionHistory.timestamp).label("month"),
            func.sum(FeeTransactionHistory.amount).label("total_amount")
        ).group_by("month").order_by("month").all()

        labels = [row.month for row in results]
        data = [float(row.total_amount) for row in results]

        return jsonify({"labels": labels, "data": data}), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching monthly fee collection: {e}")
        return jsonify({"error": "Error fetching monthly fee collection. Please try again later."}), 500
    
@students_bp.route("/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found."}), 404
    try:
        # Delete associated fee transactions
        for transaction in student.fee_transactions:
            db.session.delete(transaction)
        
        # Delete associated fee history records
        for history in student.fee_history:
            db.session.delete(history)
        
        # Now delete the student
        db.session.delete(student)
        db.session.commit()
        return jsonify({"message": "Student deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
