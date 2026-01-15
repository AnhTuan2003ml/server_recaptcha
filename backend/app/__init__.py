from flask import Flask
from config import Config
from app.extensions import db, cors

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Set application root path
    if hasattr(app.config, 'APPLICATION_ROOT'):
        app.url_map.host_matching = False  # Allow mounting under a path

    # 1. Khởi tạo Extensions
    db.init_app(app)
    # Cấu hình CORS để hỗ trợ credentials (cookie) cho SSE
    cors.init_app(app, supports_credentials=True)

    # 2. Đăng ký các Blueprints (Routes)
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.payment import payment_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(payment_bp, url_prefix='/api/payment')

    # Recaptcha API sẽ được đăng ký riêng khi cần (không import ở đây)

    # 3. Tạo bảng DB nếu chưa có (cho môi trường dev)
    with app.app_context():
        db.create_all()

    return app