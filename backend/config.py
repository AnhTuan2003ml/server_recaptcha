import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key-cua-sep'
    # Sử dụng SQLite cho hiện tại
    SQLALCHEMY_DATABASE_URI = 'sqlite:///payment.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session cookie configuration (for SSE)
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access (XSS protection)
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'  # Only HTTPS in production
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # Cấu hình SePay & Mail
    BANK_ID = "MB"
    ACCOUNT_NO = "0966549624"
    TEMPLATE = "compact"
    # Webhook secret key để verify webhook requests
    WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET') or 'webhook-secret-key-change-in-production'

    # Application root path for serving under /api
    APPLICATION_ROOT = '/api'