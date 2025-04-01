from flask import Blueprint, jsonify
from app.models import Student, FeeTransaction
from sqlalchemy import func
from app.extensions import db

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/", methods=["GET"])
def get_dashboard_summary():
    try:
        # Calculate total fees collected
        total_fees_collected = db.session.query(
            func.coalesce(func.sum(FeeTransaction.amount), 0)
        ).scalar()

        # Calculate total fees pending
        total_fees_pending = db.session.query(
            func.coalesce(func.sum(Student.expected_fee - Student.total_fee_paid), 0)
        ).scalar()

        # Prepare and return the summary data
        return jsonify({
            "total_fees_collected": float(total_fees_collected),
            "total_fees_pending": float(total_fees_pending),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route("/monthly-fees", methods=["GET"])
def monthly_fees():
    results = db.session.query(
        extract('year', FeeTransaction.timestamp).label('year'),
        extract('month', FeeTransaction.timestamp).label('month'),
        func.coalesce(func.sum(FeeTransaction.amount), 0).label('total_fees_collected')
    ).group_by('year', 'month').order_by('year', 'month').all()

    data = [
        {
            "year": int(row.year),
            "month": int(row.month),
            "total_fees_collected": float(row.total_fees_collected)
        }
        for row in results
    ]

    return jsonify({"monthly_fees": data}), 200
