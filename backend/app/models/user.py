from app.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    key = db.Column(db.String(18), unique=True, nullable=False)  # Key ngẫu nhiên 18 ký tự, unique
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable để hỗ trợ cả OTP và password
    credit = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Quan hệ
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    sessions = db.relationship('Session', backref='user', lazy=True)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

class Session(db.Model):
    __tablename__ = 'sessions'
    
    token = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    expires_at = db.Column(db.Float, nullable=False)

class OTP(db.Model):
    __tablename__ = 'otps'
    
    email = db.Column(db.String(120), primary_key=True)
    otp_code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.Float, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # Lưu password tạm khi đăng ký