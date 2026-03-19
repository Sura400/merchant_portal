from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Merchant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    account_number = db.Column(db.String(50))
    city = db.Column(db.String(50))
    country_code = db.Column(db.String(2))
    category_code = db.Column(db.String(10))
    channel = db.Column(db.String(20))

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id'))
    amount = db.Column(db.Float)
    currency = db.Column(db.String(3))
    purpose = db.Column(db.String(50))
    bill_number = db.Column(db.String(50))
    mobile_number = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime)
