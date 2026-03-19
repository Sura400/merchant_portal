from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# Merchant table
class Merchant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))          # Merchant name
    account_number = db.Column(db.String(50)) # Merchant account number
    city = db.Column(db.String(50))           # Merchant city
    country_code = db.Column(db.String(2))    # Country code (ISO 3166, e.g. ET)
    category_code = db.Column(db.String(10))  # Merchant Category Code (MCC)
    channel = db.Column(db.String(20))        # Channel type (QRCP, POS, etc.)

# Transaction table
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id'))
    amount = db.Column(db.Float)              # Transaction amount
    currency = db.Column(db.String(3))        # Currency (ISO 4217, e.g. ETB)
    purpose = db.Column(db.String(50))        # Transaction purpose
    bill_number = db.Column(db.String(50))    # Bill or invoice number
    mobile_number = db.Column(db.String(20))  # Customer mobile number
    timestamp = db.Column(db.DateTime)        # Transaction date/time
