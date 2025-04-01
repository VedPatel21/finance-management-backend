from flask import Blueprint, jsonify, current_app
from app.extensions import db
from app.models import Student, FeeTransactionHistory, Expense
from sqlalchemy import func

reports_bp = Blueprint("reports", __name__)

# 1. Monthly Financial Overview
@reports_bp.route("/monthly-financial", methods=["GET"])
def monthly_financial_overview():
    try:
        fee_results = db.session.query(
            func.strftime("%Y-%m", FeeTransactionHistory.timestamp).label("month"),
            func.coalesce(func.sum(FeeTransactionHistory.amount), 0).label("total_fees")
        ).group_by("month").order_by("month").all()

        expense_results = db.session.query(
            func.strftime("%Y-%m", Expense.date).label("month"),
            func.coalesce(func.sum(Expense.amount), 0).label("total_expenses")
        ).group_by("month").order_by("month").all()

        # If no financial data exists, return placeholder message and data
        if not fee_results and not expense_results:
            return jsonify({
                "message": "No financial data available for the selected period.",
                "labels": ["No Data"],
                "fees": [0],
                "expenses": [0],
                "net_income": [0]
            }), 200

        fee_data = {row.month: float(row.total_fees) for row in fee_results} if fee_results else {}
        expense_data = {row.month: float(row.total_expenses) for row in expense_results} if expense_results else {}

        all_months = sorted(set(fee_data.keys()).union(expense_data.keys()))
        fees_arr = [fee_data.get(month, 0) for month in all_months]
        expenses_arr = [expense_data.get(month, 0) for month in all_months]
        net_income_arr = [fee - expense for fee, expense in zip(fees_arr, expenses_arr)]

        return jsonify({
            "labels": all_months,
            "fees": fees_arr,
            "expenses": expenses_arr,
            "net_income": net_income_arr
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error generating monthly financial overview: {e}")
        return jsonify({"error": "An error occurred while fetching monthly financial data."}), 500


# 2. Class-wise Fee Performance
@reports_bp.route("/class-performance", methods=["GET"])
def class_performance():
    try:
        results = db.session.query(
            Student.class_name,
            func.coalesce(func.sum(Student.expected_fee), 0).label("total_expected"),
            func.coalesce(func.sum(Student.total_fee_paid), 0).label("total_collected")
        ).group_by(Student.class_name).all()

        if not results:
            return jsonify({
                "message": "No class performance data available.",
                "class_performance": []
            }), 200

        data = [{
            "class": row.class_name,
            "total_expected": float(row.total_expected),
            "total_collected": float(row.total_collected),
            "pending": float(row.total_expected) - float(row.total_collected)
        } for row in results]

        return jsonify({"class_performance": data}), 200

    except Exception as e:
        current_app.logger.error(f"Error generating class performance report: {e}")
        return jsonify({"error": "An error occurred while fetching class performance data."}), 500


# 3. Payment Mode Analysis
@reports_bp.route("/payment-mode", methods=["GET"])
def payment_mode_analysis():
    try:
        fee_mode_results = db.session.query(
            FeeTransactionHistory.mode,
            func.count(FeeTransactionHistory.id).label("count"),
            func.coalesce(func.sum(FeeTransactionHistory.amount), 0).label("total_amount")
        ).group_by(FeeTransactionHistory.mode).all()

        expense_mode_results = db.session.query(
            Expense.mode,
            func.count(Expense.id).label("count"),
            func.coalesce(func.sum(Expense.amount), 0).label("total_amount")
        ).group_by(Expense.mode).all()

        if not fee_mode_results and not expense_mode_results:
            return jsonify({
                "message": "No payment mode data available.",
                "fee_payment_modes": [],
                "expense_payment_modes": []
            }), 200

        fee_modes = [{
            "mode": row.mode,
            "count": row.count,
            "total_amount": float(row.total_amount)
        } for row in fee_mode_results]

        expense_modes = [{
            "mode": row.mode,
            "count": row.count,
            "total_amount": float(row.total_amount)
        } for row in expense_mode_results]

        return jsonify({
            "fee_payment_modes": fee_modes,
            "expense_payment_modes": expense_modes
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error generating payment mode analysis: {e}")
        return jsonify({"error": "An error occurred while fetching payment mode data."}), 500


# 4. Expense Categorization
@reports_bp.route("/expense-categories", methods=["GET"])
def expense_categories():
    try:
        results = db.session.query(
            Expense.subject,
            func.coalesce(func.sum(Expense.amount), 0).label("total_expense")
        ).group_by(Expense.subject).all()

        if not results:
            return jsonify({
                "message": "No expense category data available.",
                "expense_categories": []
            }), 200

        data = [{
            "category": row.subject,
            "total_expense": float(row.total_expense)
        } for row in results]

        return jsonify({"expense_categories": data}), 200

    except Exception as e:
        current_app.logger.error(f"Error generating expense categorization report: {e}")
        return jsonify({"error": "An error occurred while fetching expense categories."}), 500


# 5. Year-over-Year Comparison
@reports_bp.route("/yearly", methods=["GET"])
def yearly_comparison():
    try:
        fee_results = db.session.query(
            func.strftime("%Y", FeeTransactionHistory.timestamp).label("year"),
            func.coalesce(func.sum(FeeTransactionHistory.amount), 0).label("total_fees")
        ).group_by("year").order_by("year").all()

        expense_results = db.session.query(
            func.strftime("%Y", Expense.date).label("year"),
            func.coalesce(func.sum(Expense.amount), 0).label("total_expenses")
        ).group_by("year").order_by("year").all()

        if not fee_results and not expense_results:
            return jsonify({
                "message": "No yearly financial data available.",
                "years": [],
                "fees": [],
                "expenses": [],
                "net_income": []
            }), 200

        fee_data = {row.year: float(row.total_fees) for row in fee_results}
        expense_data = {row.year: float(row.total_expenses) for row in expense_results}

        all_years = sorted(set(fee_data.keys()).union(expense_data.keys()))
        fees_arr = [fee_data.get(year, 0) for year in all_years]
        expenses_arr = [expense_data.get(year, 0) for year in all_years]
        net_income_arr = [fee - expense for fee, expense in zip(fees_arr, expenses_arr)]

        return jsonify({
            "years": all_years,
            "fees": fees_arr,
            "expenses": expenses_arr,
            "net_income": net_income_arr
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error generating yearly comparison report: {e}")
        return jsonify({"error": "An error occurred while fetching yearly data."}), 500
