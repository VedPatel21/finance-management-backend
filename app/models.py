from .extensions import db
from datetime import datetime

# Student Model
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    expected_fee = db.Column(db.Numeric(10, 2), nullable=False)
    total_fee_paid = db.Column(db.Numeric(10, 2), default=0)
    
    fee_transactions = db.relationship('FeeTransaction', backref='student', lazy=True)
    fee_history = db.relationship('FeeTransactionHistory', backref='student', lazy=True)

    @property
    def fee_balance(self):
        return float(self.expected_fee) - float(self.total_fee_paid)

    def update_fee_balance(self, amount):
        self.total_fee_paid += float(amount)
        db.session.commit()

# FeeTransaction Model
class FeeTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    mode = db.Column(db.String(20), nullable=False)  # 'UPI' or 'Cash'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# FeeTransactionHistory Model
class FeeTransactionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    student_name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    mode = db.Column(db.String(20), nullable=False)  # 'UPI' or 'Cash'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    fee_remaining = db.Column(db.Numeric(10, 2), nullable=False)

# Expense Category Model
class ExpenseCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

# Expense Model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    mode = db.Column(db.String(20), nullable=False)  # 'UPI' or 'Cash'
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    subject = db.Column(db.String(50), nullable=False)