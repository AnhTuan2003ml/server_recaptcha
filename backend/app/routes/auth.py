from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user import User, OTP, Session
from app.services.email_service import get_email_service
import random, string, time, uuid

auth_bp = Blueprint('auth', __name__)

# ========== ĐĂNG KÝ ==========
@auth_bp.route('/register', methods=['POST'])
def register():
    """Đăng ký tài khoản mới - chỉ gửi OTP, chưa tạo user vào DB"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email:
        return jsonify({"error": "Thiếu email"}), 400
    
    if not password:
        return jsonify({"error": "Thiếu mật khẩu"}), 400
    
    if len(password) < 6:
        return jsonify({"error": "Mật khẩu phải có ít nhất 6 ký tự"}), 400
    
    # Kiểm tra email đã tồn tại chưa
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email đã được sử dụng"}), 400
    
    # Hash password để lưu tạm trong OTP
    from werkzeug.security import generate_password_hash
    password_hash = generate_password_hash(password)
    
    # Tạo OTP để xác thực email
    otp_code = ''.join(random.choices(string.digits, k=6))
    expires = time.time() + 300  # 5 phút
    
    # Lưu OTP kèm password_hash tạm thời
    otp_entry = OTP.query.filter_by(email=email).first()
    if otp_entry:
        otp_entry.otp_code = otp_code
        otp_entry.expires_at = expires
        otp_entry.password_hash = password_hash  # Lưu password tạm
    else:
        new_otp = OTP(email=email, otp_code=otp_code, expires_at=expires, password_hash=password_hash)
        db.session.add(new_otp)
    
    db.session.commit()
    
    # Gửi email OTP
    email_service = get_email_service()
    email_sent = email_service.send_otp(email, otp_code, purpose="đăng ký")
    
    if email_sent:
        print(f"📧 Đã gửi email OTP đăng ký đến {email}")
    else:
        # Vẫn in ra console để debug nếu gửi email thất bại
        print(f"⚠️ Không gửi được email, OTP code: {otp_code}")
        print(f"   [DEBUG] Registration OTP for {email}: {otp_code}")
    
    return jsonify({"success": True, "message": "Mã OTP đã được gửi để xác thực email."})

@auth_bp.route('/register/verify', methods=['POST'])
def verify_register():
    """Xác thực OTP sau khi đăng ký - TẠO USER vào DB và tự động đăng nhập"""
    data = request.get_json()
    email = data.get('email')
    otp_input = data.get('otp')
    
    if not email or not otp_input:
        return jsonify({"error": "Thiếu email hoặc OTP"}), 400
    
    otp_record = OTP.query.filter_by(email=email).first()
    
    if otp_record and otp_record.otp_code == otp_input:
        if time.time() > otp_record.expires_at:
            return jsonify({"error": "OTP đã hết hạn"}), 400
        
        # Kiểm tra lại email đã tồn tại chưa (phòng trường hợp đăng ký song song)
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            # Xóa OTP cũ
            db.session.delete(otp_record)
            db.session.commit()
            return jsonify({"error": "Email đã được sử dụng"}), 400
        
        # Tạo key ngẫu nhiên 18 ký tự (unique)
        max_attempts = 10
        user_key = None
        for _ in range(max_attempts):
            # Sử dụng chữ cái và số để tạo key
            candidate_key = ''.join(random.choices(string.ascii_letters + string.digits, k=18))
            # Kiểm tra key đã tồn tại chưa
            if not User.query.filter_by(key=candidate_key).first():
                user_key = candidate_key
                break
        
        if not user_key:
            return jsonify({"error": "Không thể tạo key, vui lòng thử lại"}), 500
        
        # Xác thực OTP thành công -> TẠO USER mới vào database
        new_user = User(email=email, key=user_key, password_hash=otp_record.password_hash)
        db.session.add(new_user)
        db.session.flush()  # Để lấy ID của user
        
        print(f"✅ Đã tạo user mới: {email} (ID: {new_user.id}, Key: {user_key})")
        
        # Tạo Session và đăng nhập
        token = str(uuid.uuid4())
        expires = time.time() + (86400 * 2)  # 2 ngày
        
        new_session = Session(token=token, user_id=new_user.id, expires_at=expires)
        db.session.add(new_session)
        
        # Xóa OTP cũ
        db.session.delete(otp_record)
        db.session.commit()
        
        return jsonify({"success": True, "token": token, "message": "Đăng ký và đăng nhập thành công"})
    
    return jsonify({"error": "Mã OTP không đúng"}), 400

# ========== ĐĂNG NHẬP ==========
@auth_bp.route('/login/otp', methods=['POST'])
def login_otp():
    """Gửi OTP cho đăng nhập - chỉ cho user đã tồn tại"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({"error": "Thiếu email"}), 400
    
    # Kiểm tra user đã tồn tại chưa
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Email chưa được đăng ký. Vui lòng đăng ký trước."}), 400
    
    # Tạo OTP
    otp_code = ''.join(random.choices(string.digits, k=6))
    expires = time.time() + 300  # 5 phút
    
    # Lưu OTP (Update nếu đã tồn tại)
    otp_entry = OTP.query.filter_by(email=email).first()
    if otp_entry:
        otp_entry.otp_code = otp_code
        otp_entry.expires_at = expires
    else:
        new_otp = OTP(email=email, otp_code=otp_code, expires_at=expires)
        db.session.add(new_otp)
    
    db.session.commit()
    
    # Gửi email OTP
    email_service = get_email_service()
    email_sent = email_service.send_otp(email, otp_code, purpose="đăng nhập")
    
    if email_sent:
        print(f"📧 Đã gửi email OTP đăng nhập đến {email}")
    else:
        # Vẫn in ra console để debug nếu gửi email thất bại
        print(f"⚠️ Không gửi được email, OTP code: {otp_code}")
        print(f"   [DEBUG] Login OTP for {email}: {otp_code}")
    
    return jsonify({"success": True, "message": "Mã OTP đã được gửi"})

@auth_bp.route('/login', methods=['POST'])
def login():
    """Đăng nhập bằng mật khẩu hoặc OTP"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    otp_input = data.get('otp')
    
    if not email:
        return jsonify({"error": "Thiếu email"}), 400
    
    # Phải có mật khẩu HOẶC OTP
    if not password and not otp_input:
        return jsonify({"error": "Thiếu mật khẩu hoặc OTP"}), 400
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Email chưa được đăng ký"}), 400
    
    # Kiểm tra mật khẩu
    if password:
        if not user.check_password(password):
            return jsonify({"error": "Mật khẩu không đúng"}), 400
    # Hoặc kiểm tra OTP
    elif otp_input:
        otp_record = OTP.query.filter_by(email=email).first()
        if not otp_record or otp_record.otp_code != otp_input:
            return jsonify({"error": "Mã OTP không đúng"}), 400
        if time.time() > otp_record.expires_at:
            return jsonify({"error": "OTP đã hết hạn"}), 400
        # Xóa OTP sau khi dùng
        db.session.delete(otp_record)
    
    # Login thành công -> Tạo Session
    remember = data.get('remember', False)
    token = str(uuid.uuid4())
    
    if remember:
        # Ghi nhớ: 5 ngày
        expires = time.time() + (86400 * 5)
    else:
        # Không ghi nhớ: 1 ngày
        expires = time.time() + (86400 * 1)
    
    # Luôn lưu session vào database
    new_session = Session(token=token, user_id=user.id, expires_at=expires)
    db.session.add(new_session)
    db.session.commit()
    
    print(f"✅ User {email} đăng nhập thành công (ID: {user.id}, Remember: {remember})")
    
    return jsonify({"success": True, "token": token, "remember": remember})

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Gửi mật khẩu mới qua email khi quên mật khẩu"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({"error": "Thiếu email"}), 400
    
    # Kiểm tra user có tồn tại không
    user = User.query.filter_by(email=email).first()
    if not user:
        # Không trả về lỗi chi tiết để bảo mật (tránh user enumeration)
        return jsonify({"success": True, "message": "Nếu email tồn tại, mật khẩu mới đã được gửi."})
    
    # Tạo mật khẩu mới ngẫu nhiên (8-12 ký tự)
    new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    
    # Cập nhật mật khẩu mới vào database
    user.set_password(new_password)
    db.session.commit()
    
    print(f"✅ Đã tạo mật khẩu mới cho user: {email}")
    
    # Gửi email mật khẩu mới
    email_service = get_email_service()
    email_sent = email_service.send_new_password(email, new_password)
    
    if email_sent:
        print(f"📧 Đã gửi email mật khẩu mới đến {email}")
    else:
        print(f"⚠️ Không gửi được email, mật khẩu mới: {new_password}")
        print(f"   [DEBUG] New password for {email}: {new_password}")
    
    # Trả về success (không tiết lộ thông tin)
    return jsonify({"success": True, "message": "Nếu email tồn tại, mật khẩu mới đã được gửi."})

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """Đổi mật khẩu - yêu cầu đăng nhập"""
    # Lấy user từ token
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Chưa đăng nhập"}), 401
    
    session = Session.query.filter_by(token=token).first()
    if not session or session.expires_at <= time.time():
        return jsonify({"error": "Phiên đăng nhập đã hết hạn"}), 401
    
    user = User.query.get(session.user_id)
    if not user:
        return jsonify({"error": "User không tồn tại"}), 404
    
    # Lấy dữ liệu
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password:
        return jsonify({"error": "Thiếu mật khẩu cũ"}), 400
    
    if not new_password:
        return jsonify({"error": "Thiếu mật khẩu mới"}), 400
    
    if len(new_password) < 6:
        return jsonify({"error": "Mật khẩu mới phải có ít nhất 6 ký tự"}), 400
    
    # Kiểm tra mật khẩu cũ
    if not user.check_password(old_password):
        return jsonify({"error": "Mật khẩu cũ không đúng"}), 400
    
    # Cập nhật mật khẩu mới
    user.set_password(new_password)
    db.session.commit()
    
    print(f"✅ User {user.email} đã đổi mật khẩu thành công (ID: {user.id})")
    
    return jsonify({"success": True, "message": "Đổi mật khẩu thành công"})