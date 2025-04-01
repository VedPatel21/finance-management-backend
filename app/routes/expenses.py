from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models import Expense, ExpenseCategory
from sqlalchemy.sql import func
from datetime import datetime

expenses_bp = Blueprint("expenses", __name__)

def initialize_categories():
    categories = ["Staff Salary", "Land Rent", "House Loan", "Car Loan", "School Maintenance", "House Expense"]
    for cat in categories:
        if not ExpenseCategory.query.filter_by(name=cat).first():
            db.session.add(ExpenseCategory(name=cat))
    db.session.commit()

@expenses_bp.route("/monthly", methods=["GET"])
def monthly_expenses():
    """
    Returns the total expenses grouped by year and month using SQLite's strftime.
    Example response:
    [
      {"year": 2025, "month": 1, "total_expense": 5000.0},
      {"year": 2025, "month": 2, "total_expense": 7500.0},
      ...
    ]
    """
    try:
        results = db.session.query(
            func.strftime('%Y', Expense.date).label('year'),
            func.strftime('%m', Expense.date).label('month'),
            func.coalesce(func.sum(Expense.amount), 0).label('total_expense')
        ).group_by(func.strftime('%Y-%m', Expense.date)).order_by('year', 'month').all()

        data = []
        for row in results:
            if row.year and row.month:
                data.append({
                    "year": int(row.year),
                    "month": int(row.month),
                    "total_expense": float(row.total_expense)
                })

        return jsonify({"monthly_expenses": data}), 200
    except Exception as e:
        current_app.logger.error(f"Error aggregating monthly expenses: {e}")
        return jsonify({"error": "Error aggregating monthly expenses. Please try again later."}), 500
    

@expenses_bp.route("/category", methods=["POST"])
def add_expense_category():
    data = request.get_json() or {}
    name = data.get("name")
    if not name:
        return jsonify({"error": "Category name is required."}), 400
    if ExpenseCategory.query.filter_by(name=name).first():
        return jsonify({"error": "Category already exists."}), 400
    try:
        category = ExpenseCategory(name=name)
        db.session.add(category)
        db.session.commit()
        return jsonify({"message": "Category added successfully.", "category_id": category.id}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding expense category: {e}")
        return jsonify({"error": str(e)}), 500

@expenses_bp.route("/", methods=["POST"])
def add_expense():
    data = request.get_json() or {}
    amount = data.get("amount")
    mode = data.get("mode")
    date_str = data.get("date")
    description = data.get("description", "")
    subject = data.get("subject")
    
    if None in [amount, mode, date_str, subject] or mode not in ["UPI", "Cash"]:
        return jsonify({"error": "Missing or invalid fields."}), 400
    
    try:
        expense_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    if not ExpenseCategory.query.filter_by(name=subject).first():
        return jsonify({"error": "Expense category does not exist."}), 400

    try:
        expense = Expense(
            amount=amount,
            mode=mode,
            date=expense_date,
            description=description,
            subject=subject
        )
        db.session.add(expense)
        db.session.commit()
        return jsonify({"message": "Expense recorded successfully.", "expense_id": expense.id}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding expense: {e}")
        return jsonify({"error": str(e)}), 500

@expenses_bp.route("/", methods=["GET"])
def get_expenses():
    try:
        expenses = Expense.query.all()
        data = [{
            "id": exp.id,
            "amount": float(exp.amount),
            "mode": exp.mode,
            "date": exp.date.strftime("%Y-%m-%d"),
            "description": exp.description,
            "subject": exp.subject
        } for exp in expenses]
        return jsonify({"expenses": data}), 200
    except Exception as e:
        current_app.logger.error(f"Error retrieving expenses: {e}")
        return jsonify({"error": "Error retrieving expenses. Please try again later."}), 500

# New Route: Update an expense
@expenses_bp.route("/<int:expense_id>", methods=["PUT"])
def update_expense(expense_id):
    data = request.get_json() or {}
    expense = Expense.query.get(expense_id)
    if not expense:
        return jsonify({"error": "Expense not found."}), 404

    # Update allowed fields if provided
    try:
        if "amount" in data:
            expense.amount = data["amount"]
        if "mode" in data:
            if data["mode"] not in ["UPI", "Cash"]:
                return jsonify({"error": "Invalid payment mode."}), 400
            expense.mode = data["mode"]
        if "date" in data:
            try:
                expense.date = datetime.strptime(data["date"], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
        if "description" in data:
            expense.description = data["description"]
        if "subject" in data:
            if not ExpenseCategory.query.filter_by(name=data["subject"]).first():
                return jsonify({"error": "Expense category does not exist."}), 400
            expense.subject = data["subject"]

        db.session.commit()
        return jsonify({"message": "Expense updated successfully."}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating expense: {e}")
        return jsonify({"error": str(e)}), 500

# New Route: Delete an expense
@expenses_bp.route("/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    expense = Expense.query.get(expense_id)
    if not expense:
        return jsonify({"error": "Expense not found."}), 404
    try:
        db.session.delete(expense)
        db.session.commit()
        return jsonify({"message": "Expense deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting expense: {e}")
        return jsonify({"error": str(e)}), 500
