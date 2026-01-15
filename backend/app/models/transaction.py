from app.extensions import db
from datetime import datetime

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.String(20), primary_key=True) # Mã giao dịch (A1B2...)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, success
    content = db.Column(db.String(200)) # Nội dung chuyển khoản
    created_at = db.Column(db.DateTime, default=datetime.utcnow)