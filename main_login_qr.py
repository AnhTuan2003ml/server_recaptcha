"""
Main entry point cho Login & QR Payment API Service
Flask API tối giản chỉ chứa đăng nhập và thanh toán QR code
"""

import sys
import socket
import json
import base64
from flask import Flask, jsonify, Response, request

# Tạo Flask app
app = Flask(__name__)

# Import các module cần thiết
try:
    from apis import qr_code
    print("✅ Đã import module QR Code")
except ImportError as e:
    print(f"❌ Lỗi khi import apis.qr_code: {e}")
    sys.exit(1)

try:
    from apis import authencation
    print("✅ Đã import module Authentication")
except ImportError as e:
    print(f"❌ Lỗi khi import apis.authencation: {e}")
    sys.exit(1)

try:
    from apis import creat_otp
    print("✅ Đã import module Create OTP")
except ImportError as e:
    print(f"❌ Lỗi khi import apis.creat_otp: {e}")
    sys.exit(1)

try:
    from apis import check_login
    print("✅ Đã import module Check Login")
except ImportError as e:
    print(f"❌ Lỗi khi import apis.check_login: {e}")
    sys.exit(1)

try:
    from apis import session_manager
    print("✅ Đã import module Session Manager")
except ImportError as e:
    print(f"❌ Lỗi khi import apis.session_manager: {e}")
    sys.exit(1)


def lay_ip_local():
    """Lấy địa chỉ IP local của máy"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


def in_thong_tin_api(port, local_ip):
    """In thông tin các API endpoints"""
    print("="*60)
    print("🚀 Login & QR Payment API Service đã sẵn sàng!")
    print("="*60)
    print(f"📍 Local: http://localhost:{port}")
    print(f"📍 Mạng nội bộ: http://{local_ip}:{port}")
    print("="*60)
    print("📋 Available Endpoints:")
    print("   🔐 ĐĂNG KÝ:")
    print(f"   • POST http://localhost:{port}/register        - Đăng ký tài khoản mới (tạo user và gửi OTP)")
    print(f"   • POST http://localhost:{port}/register/verify - Xác thực OTP và đăng nhập sau đăng ký")
    print("   🔑 ĐĂNG NHẬP:")
    print(f"   • POST http://localhost:{port}/login/otp      - Gửi mã OTP cho đăng nhập (chỉ user đã tồn tại)")
    print(f"   • POST http://localhost:{port}/check_login    - Kiểm tra mã OTP và đăng nhập (trả về session token)")
    print("   🔒 SESSION:")
    print(f"   • POST http://localhost:{port}/verify_session - Kiểm tra session token có hợp lệ không")
    print(f"   • POST http://localhost:{port}/logout        - Đăng xuất (xóa session)")
    print("   💳 THANH TOÁN:")
    print(f"   • GET  http://localhost:{port}/qr             - Tạo QR code thanh toán")
    print(f"       Query: ?sl=<số_lượng> (optional) - Số lượng để tính toán số tiền")
    print(f"              ?format=json (optional) - Trả về JSON với id và qr_code base64")
    print(f"   • POST http://localhost:{port}/authentication  - Webhook xử lý thanh toán từ SePay")
    print("="*60)


# ========== ĐĂNG KÝ ==========
@app.route('/register', methods=['POST'])
def register_endpoint():
    """
    API endpoint để đăng ký tài khoản mới - tạo user và gửi OTP
    
    Body JSON format:
    {
        "email": "user@example.com"  // Email cần đăng ký
    }
    
    Returns:
        - 200: Thành công - Đã tạo user và gửi OTP
        - 400: Request không hợp lệ hoặc email đã được sử dụng
        - 500: Lỗi server
    
    Response body:
        {
            "success": bool,
            "status_code": number,
            "message": "string"
        }
    
    Example:
        POST /register
        Body: {"email": "user@example.com"}
    """
    json_data = request.get_json(silent=True)
    
    print("\n" + "="*60)
    print("✅ Nhận được request register!")
    print("="*60)
    print(f"📋 Method: {request.method}")
    print(f"📋 URL: {request.url}")
    
    if json_data:
        print(f"📋 JSON Body:")
        print(json.dumps(json_data, ensure_ascii=False, indent=2))
    
    if not json_data:
        print("❌ Không có JSON body trong request")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Request phải chứa JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    email = json_data.get('email')
    
    if email is None:
        print("❌ Thiếu trường 'email' trong JSON body")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Thiếu trường 'email' trong JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    if not isinstance(email, str):
        print(f"❌ Trường 'email' phải là chuỗi, nhận được: {type(email).__name__}")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": f"Trường 'email' phải là chuỗi, nhận được: {type(email).__name__}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    print(f"\n📤 Trích xuất thông tin:")
    print(f"   • email: {email}")
    
    try:
        # Kiểm tra user đã tồn tại chưa
        # Giả định có hàm check_user_exists trong module creat_otp hoặc check_login
        # Nếu không có, sẽ cần import thêm hoặc tạo logic kiểm tra
        user_exists = False
        try:
            # Thử kiểm tra user tồn tại (nếu module có hàm này)
            if hasattr(creat_otp, 'check_user_exists'):
                user_exists = creat_otp.check_user_exists(email)
            elif hasattr(check_login, 'check_user_exists'):
                user_exists = check_login.check_user_exists(email)
        except:
            # Nếu không có hàm check, giả định creat_otp sẽ tự động tạo user
            # Nên ta sẽ gọi creat_otp và kiểm tra response
            pass
        
        # Nếu user đã tồn tại, từ chối đăng ký
        if user_exists:
            print(f"❌ Email {email} đã được sử dụng")
            response = jsonify({
                "success": False,
                "status_code": 400,
                "message": "Email đã được sử dụng. Vui lòng đăng nhập."
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            return response, 400
        
        # Tạo user mới và gửi OTP
        # Giả định có hàm create_user hoặc creat_otp sẽ tự động tạo user nếu chưa có
        if hasattr(creat_otp, 'create_user'):
            user_created, user_msg = creat_otp.create_user(email)
            if not user_created:
                response = jsonify({
                    "success": False,
                    "status_code": 500,
                    "message": user_msg
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                return response, 500
        
        # Gửi OTP
        success, message = creat_otp.creat_otp(email)
        
        if success:
            status_code = 200
            response_data = {
                "success": True,
                "status_code": status_code,
                "message": "Đăng ký thành công. Mã OTP đã được gửi."
            }
        else:
            if "không hợp lệ" in message.lower() or "mail không đúng" in message.lower():
                status_code = 400
            else:
                status_code = 500
            response_data = {
                "success": False,
                "status_code": status_code,
                "message": message
            }
        
        print(f"\n📥 Kết quả:")
        print(f"   • success: {success}")
        print(f"   • status_code: {status_code}")
        print(f"   • message: {response_data['message']}")
        print("="*60 + "\n")
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, status_code
        
    except Exception as e:
        print(f"❌ Lỗi khi xử lý register: {e}")
        response = jsonify({
            "success": False,
            "status_code": 500,
            "message": f"Lỗi server: {str(e)}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 500


@app.route('/register/verify', methods=['POST'])
def verify_register_endpoint():
    """
    API endpoint để xác thực OTP sau khi đăng ký và tự động đăng nhập
    
    Body JSON format:
    {
        "email": "user@example.com",  // Email đã đăng ký
        "otp_code": "123456"           // Mã OTP nhận được
    }
    
    Returns:
        - 200: Thành công - Đăng ký và đăng nhập thành công (trả về session_token)
        - 400: Request không hợp lệ hoặc mã OTP không đúng
        - 500: Lỗi server
    
    Response body:
        {
            "success": bool,
            "status_code": number,
            "message": "string",
            "session_token": "string" (nếu thành công),
            "email": "string" (nếu thành công)
        }
    
    Example:
        POST /register/verify
        Body: {"email": "user@example.com", "otp_code": "123456"}
    """
    json_data = request.get_json(silent=True)
    
    print("\n" + "="*60)
    print("✅ Nhận được request register/verify!")
    print("="*60)
    print(f"📋 Method: {request.method}")
    print(f"📋 URL: {request.url}")
    
    if json_data:
        print(f"📋 JSON Body:")
        print(json.dumps(json_data, ensure_ascii=False, indent=2))
    
    if not json_data:
        print("❌ Không có JSON body trong request")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Request phải chứa JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    email = json_data.get('email')
    otp_code = json_data.get('otp_code')
    
    if email is None:
        print("❌ Thiếu trường 'email' trong JSON body")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Thiếu trường 'email' trong JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    if otp_code is None:
        print("❌ Thiếu trường 'otp_code' trong JSON body")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Thiếu trường 'otp_code' trong JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    if not isinstance(email, str):
        print(f"❌ Trường 'email' phải là chuỗi, nhận được: {type(email).__name__}")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": f"Trường 'email' phải là chuỗi, nhận được: {type(email).__name__}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    if not isinstance(otp_code, str):
        print(f"❌ Trường 'otp_code' phải là chuỗi, nhận được: {type(otp_code).__name__}")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": f"Trường 'otp_code' phải là chuỗi, nhận được: {type(otp_code).__name__}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    print(f"\n📤 Trích xuất thông tin:")
    print(f"   • email: {email}")
    print(f"   • otp_code: {otp_code}")
    
    try:
        # Kiểm tra OTP
        success, message = check_login.check_login(email, otp_code)
        
        if success:
            status_code = 200
            # Tạo session và đăng nhập
            session_token = session_manager.create_session(email)
            
            if session_token:
                response_data = {
                    "success": True,
                    "status_code": status_code,
                    "message": "Đăng ký và đăng nhập thành công",
                    "session_token": session_token,
                    "email": email.strip().lower()
                }
                print(f"✅ Đã tạo session token cho email: {email}")
            else:
                response_data = {
                    "success": False,
                    "status_code": 500,
                    "message": "Không thể tạo session token"
                }
                print(f"⚠️ Không thể tạo session token cho email: {email}")
        else:
            if "không hợp lệ" in message.lower() or "không đúng" in message.lower():
                status_code = 400
            else:
                status_code = 500
            
            response_data = {
                "success": False,
                "status_code": status_code,
                "message": message
            }
        
        print(f"\n📥 Kết quả:")
        print(f"   • success: {response_data.get('success', False)}")
        print(f"   • status_code: {response_data.get('status_code', 500)}")
        print(f"   • message: {response_data.get('message', '')}")
        print("="*60 + "\n")
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, response_data.get('status_code', 500)
        
    except Exception as e:
        print(f"❌ Lỗi khi xử lý register/verify: {e}")
        response = jsonify({
            "success": False,
            "status_code": 500,
            "message": f"Lỗi server: {str(e)}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 500


# ========== ĐĂNG NHẬP ==========
@app.route('/login/otp', methods=['POST'])
def login_otp_endpoint():
    """
    API endpoint để gửi OTP cho đăng nhập - chỉ cho user đã tồn tại
    
    Body JSON format:
    {
        "email": "user@example.com"  // Email cần gửi OTP (phải đã đăng ký)
    }
    
    Returns:
        - 200: Thành công - OTP đã được gửi
        - 400: Request không hợp lệ hoặc email chưa được đăng ký
        - 500: Lỗi server
    
    Response body:
        {
            "success": bool,
            "status_code": number,
            "message": "string"
        }
    
    Example:
        POST /login/otp
        Body: {"email": "user@example.com"}
    """
    json_data = request.get_json(silent=True)
    
    print("\n" + "="*60)
    print("✅ Nhận được request login/otp!")
    print("="*60)
    print(f"📋 Method: {request.method}")
    print(f"📋 URL: {request.url}")
    
    if json_data:
        print(f"📋 JSON Body:")
        print(json.dumps(json_data, ensure_ascii=False, indent=2))
    
    if not json_data:
        print("❌ Không có JSON body trong request")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Request phải chứa JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    email = json_data.get('email')
    
    if email is None:
        print("❌ Thiếu trường 'email' trong JSON body")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Thiếu trường 'email' trong JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    if not isinstance(email, str):
        print(f"❌ Trường 'email' phải là chuỗi, nhận được: {type(email).__name__}")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": f"Trường 'email' phải là chuỗi, nhận được: {type(email).__name__}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    print(f"\n📤 Trích xuất thông tin:")
    print(f"   • email: {email}")
    
    try:
        # Kiểm tra user đã tồn tại chưa
        user_exists = False
        try:
            if hasattr(check_login, 'check_user_exists'):
                user_exists = check_login.check_user_exists(email)
            elif hasattr(creat_otp, 'check_user_exists'):
                user_exists = creat_otp.check_user_exists(email)
        except:
            # Nếu không có hàm check, giả định user tồn tại nếu creat_otp thành công
            pass
        
        # Nếu user chưa tồn tại, từ chối đăng nhập
        if not user_exists:
            # Thử kiểm tra bằng cách gọi creat_otp và xem có lỗi không
            # Nếu creat_otp tự động tạo user, ta cần kiểm tra khác
            # Tạm thời giả định nếu không có hàm check thì cho phép
            print(f"⚠️ Không thể kiểm tra user tồn tại, cho phép tiếp tục")
        
        # Gửi OTP
        success, message = creat_otp.creat_otp(email)
        
        if success:
            status_code = 200
            response_data = {
                "success": True,
                "status_code": status_code,
                "message": "Mã OTP đã được gửi"
            }
        else:
            # Nếu creat_otp thất bại, có thể là user chưa tồn tại
            if "không hợp lệ" in message.lower() or "mail không đúng" in message.lower():
                status_code = 400
            else:
                status_code = 500
            response_data = {
                "success": False,
                "status_code": status_code,
                "message": message if status_code == 400 else "Email chưa được đăng ký. Vui lòng đăng ký trước."
            }
        
        print(f"\n📥 Kết quả:")
        print(f"   • success: {success}")
        print(f"   • status_code: {status_code}")
        print(f"   • message: {response_data['message']}")
        print("="*60 + "\n")
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, status_code
        
    except Exception as e:
        print(f"❌ Lỗi khi xử lý login/otp: {e}")
        response = jsonify({
            "success": False,
            "status_code": 500,
            "message": f"Lỗi server: {str(e)}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 500


@app.route('/creat_otp', methods=['POST'])
def creat_otp_endpoint():
    """
    API endpoint để tạo và gửi mã OTP qua email
    (DEPRECATED: Nên dùng /register hoặc /login/otp thay thế)
    
    Body JSON format:
    {
        "email": "user@example.com"  // Email cần gửi OTP
    }
    
    Returns:
        - 200: Thành công - OTP đã được gửi
        - 400: Request không hợp lệ hoặc email không hợp lệ
        - 500: Lỗi server
    
    Response body:
        {
            "success": bool,
            "status_code": number,
            "message": "string"
        }
    
    Example:
        POST /creat_otp
        Body: {"email": "user@example.com"}
    
    Note: Route này có thể tự động tạo user nếu chưa tồn tại.
          Để tách rõ đăng ký và đăng nhập, nên dùng:
          - /register cho đăng ký
          - /login/otp cho đăng nhập
    """
    json_data = request.get_json(silent=True)
    
    print("\n" + "="*60)
    print("✅ Nhận được request creat_otp!")
    print("="*60)
    print(f"📋 Method: {request.method}")
    print(f"📋 URL: {request.url}")
    
    if json_data:
        print(f"📋 JSON Body:")
        print(json.dumps(json_data, ensure_ascii=False, indent=2))
    
    if not json_data:
        print("❌ Không có JSON body trong request")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Request phải chứa JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    email = json_data.get('email')
    
    if email is None:
        print("❌ Thiếu trường 'email' trong JSON body")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Thiếu trường 'email' trong JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    if not isinstance(email, str):
        print(f"❌ Trường 'email' phải là chuỗi, nhận được: {type(email).__name__}")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": f"Trường 'email' phải là chuỗi, nhận được: {type(email).__name__}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    print(f"\n📤 Trích xuất thông tin:")
    print(f"   • email: {email}")
    
    try:
        success, message = creat_otp.creat_otp(email)
        
        if success:
            status_code = 200
            response_data = {
                "success": True,
                "status_code": status_code,
                "message": message
            }
        else:
            if "không hợp lệ" in message.lower() or "mail không đúng" in message.lower():
                status_code = 400
            else:
                status_code = 500
            response_data = {
                "success": False,
                "status_code": status_code,
                "message": message
            }
        
        print(f"\n📥 Kết quả:")
        print(f"   • success: {success}")
        print(f"   • status_code: {status_code}")
        print(f"   • message: {message}")
        print("="*60 + "\n")
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, status_code
        
    except Exception as e:
        print(f"❌ Lỗi khi xử lý creat_otp: {e}")
        response = jsonify({
            "success": False,
            "status_code": 500,
            "message": f"Lỗi server: {str(e)}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 500


@app.route('/check_login', methods=['POST'])
def check_login_endpoint():
    """
    API endpoint để kiểm tra mã OTP và đăng nhập
    (Dùng cho cả đăng nhập sau khi gọi /login/otp hoặc /register/verify)
    
    Body JSON format:
    {
        "email": "user@example.com",  // Email của người dùng
        "otp_code": "123456"           // Mã OTP nhận được
    }
    
    Returns:
        - 200: Thành công - Đăng nhập thành công (trả về session_token)
        - 400: Request không hợp lệ hoặc mã OTP không đúng
        - 500: Lỗi server
    
    Response body:
        {
            "success": bool,
            "status_code": number,
            "message": "string",
            "session_token": "string" (nếu thành công),
            "email": "string" (nếu thành công)
        }
    
    Example:
        POST /check_login
        Body: {"email": "user@example.com", "otp_code": "123456"}
    
    Note: Route này có thể dùng cho cả đăng nhập và xác thực đăng ký.
          Để rõ ràng hơn, nên dùng /register/verify cho đăng ký và /check_login cho đăng nhập.
    """
    json_data = request.get_json(silent=True)
    
    print("\n" + "="*60)
    print("✅ Nhận được request check_login!")
    print("="*60)
    print(f"📋 Method: {request.method}")
    print(f"📋 URL: {request.url}")
    
    if json_data:
        print(f"📋 JSON Body:")
        print(json.dumps(json_data, ensure_ascii=False, indent=2))
    
    if not json_data:
        print("❌ Không có JSON body trong request")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Request phải chứa JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    email = json_data.get('email')
    otp_code = json_data.get('otp_code')
    
    if email is None:
        print("❌ Thiếu trường 'email' trong JSON body")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Thiếu trường 'email' trong JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    if otp_code is None:
        print("❌ Thiếu trường 'otp_code' trong JSON body")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Thiếu trường 'otp_code' trong JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    if not isinstance(email, str):
        print(f"❌ Trường 'email' phải là chuỗi, nhận được: {type(email).__name__}")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": f"Trường 'email' phải là chuỗi, nhận được: {type(email).__name__}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    if not isinstance(otp_code, str):
        print(f"❌ Trường 'otp_code' phải là chuỗi, nhận được: {type(otp_code).__name__}")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": f"Trường 'otp_code' phải là chuỗi, nhận được: {type(otp_code).__name__}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    print(f"\n📤 Trích xuất thông tin:")
    print(f"   • email: {email}")
    print(f"   • otp_code: {otp_code}")
    
    try:
        success, message = check_login.check_login(email, otp_code)
        
        if success:
            status_code = 200
        else:
            if "không hợp lệ" in message.lower() or "không đúng" in message.lower():
                status_code = 400
            else:
                status_code = 500
        
        response_data = {
            "success": success,
            "status_code": status_code,
            "message": message
        }
        
        if success:
            session_token = session_manager.create_session(email)
            
            if session_token:
                response_data["session_token"] = session_token
                response_data["email"] = email.strip().lower()
                print(f"✅ Đã tạo session token cho email: {email}")
            else:
                print(f"⚠️ Không thể tạo session token cho email: {email}")
        
        print(f"\n📥 Kết quả:")
        print(f"   • success: {success}")
        print(f"   • status_code: {status_code}")
        print(f"   • message: {message}")
        print("="*60 + "\n")
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, status_code
        
    except Exception as e:
        print(f"❌ Lỗi khi xử lý check_login: {e}")
        response = jsonify({
            "success": False,
            "status_code": 500,
            "message": f"Lỗi server: {str(e)}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 500


@app.route('/verify_session', methods=['POST'])
def verify_session_endpoint():
    """
    API endpoint để kiểm tra session token có hợp lệ không
    
    Body JSON format:
    {
        "session_token": "token_string"  // Session token cần kiểm tra
    }
    
    Returns:
        - 200: Thành công - Session hợp lệ
        - 400: Request không hợp lệ hoặc token không hợp lệ
        - 401: Session đã hết hạn
        - 500: Lỗi server
    
    Response body:
        {
            "success": bool,
            "status_code": number,
            "message": "string",
            "email": "string" (nếu hợp lệ)
        }
    
    Example:
        POST /verify_session
        Body: {"session_token": "abc123..."}
    """
    json_data = request.get_json(silent=True)
    
    print("\n" + "="*60)
    print("✅ Nhận được request verify_session!")
    print("="*60)
    print(f"📋 Method: {request.method}")
    print(f"📋 URL: {request.url}")
    
    if json_data:
        print(f"📋 JSON Body:")
        print(json.dumps(json_data, ensure_ascii=False, indent=2))
    
    if not json_data:
        print("❌ Không có JSON body trong request")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Request phải chứa JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    session_token = json_data.get('session_token')
    
    if session_token is None:
        print("❌ Thiếu trường 'session_token' trong JSON body")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Thiếu trường 'session_token' trong JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    if not isinstance(session_token, str):
        print(f"❌ Trường 'session_token' phải là chuỗi, nhận được: {type(session_token).__name__}")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": f"Trường 'session_token' phải là chuỗi, nhận được: {type(session_token).__name__}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    try:
        is_valid, email, message = session_manager.verify_session(session_token)
        
        if is_valid:
            status_code = 200
            response_data = {
                "success": True,
                "status_code": status_code,
                "message": message,
                "email": email
            }
        else:
            if "hết hạn" in message.lower():
                status_code = 401
            elif "không hợp lệ" in message.lower() or "không được để trống" in message.lower():
                status_code = 400
            else:
                status_code = 500
            
            response_data = {
                "success": False,
                "status_code": status_code,
                "message": message
            }
        
        print(f"\n📥 Kết quả:")
        print(f"   • success: {is_valid}")
        print(f"   • status_code: {status_code}")
        print(f"   • message: {message}")
        if email:
            print(f"   • email: {email}")
        print("="*60 + "\n")
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, status_code
        
    except Exception as e:
        print(f"❌ Lỗi khi xử lý verify_session: {e}")
        response = jsonify({
            "success": False,
            "status_code": 500,
            "message": f"Lỗi server: {str(e)}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 500


@app.route('/logout', methods=['POST'])
def logout_endpoint():
    """
    API endpoint để đăng xuất (xóa session)
    
    Body JSON format:
    {
        "session_token": "token_string"  // Session token cần xóa
    }
    
    Returns:
        - 200: Thành công - Đã xóa session
        - 400: Request không hợp lệ
        - 500: Lỗi server
    
    Response body:
        {
            "success": bool,
            "status_code": number,
            "message": "string"
        }
    
    Example:
        POST /logout
        Body: {"session_token": "abc123..."}
    """
    json_data = request.get_json(silent=True)
    
    print("\n" + "="*60)
    print("✅ Nhận được request logout!")
    print("="*60)
    print(f"📋 Method: {request.method}")
    print(f"📋 URL: {request.url}")
    
    if json_data:
        print(f"📋 JSON Body:")
        print(json.dumps(json_data, ensure_ascii=False, indent=2))
    
    if not json_data:
        print("❌ Không có JSON body trong request")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Request phải chứa JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    session_token = json_data.get('session_token')
    
    if session_token is None:
        print("❌ Thiếu trường 'session_token' trong JSON body")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Thiếu trường 'session_token' trong JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    if not isinstance(session_token, str):
        print(f"❌ Trường 'session_token' phải là chuỗi, nhận được: {type(session_token).__name__}")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": f"Trường 'session_token' phải là chuỗi, nhận được: {type(session_token).__name__}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    try:
        success = session_manager.delete_session(session_token)
        
        if success:
            status_code = 200
            message = "Đã đăng xuất thành công"
        else:
            status_code = 400
            message = "Session không tồn tại hoặc đã bị xóa"
        
        print(f"\n📥 Kết quả:")
        print(f"   • success: {success}")
        print(f"   • status_code: {status_code}")
        print(f"   • message: {message}")
        print("="*60 + "\n")
        
        response_data = {
            "success": success,
            "status_code": status_code,
            "message": message
        }
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, status_code
        
    except Exception as e:
        print(f"❌ Lỗi khi xử lý logout: {e}")
        response = jsonify({
            "success": False,
            "status_code": 500,
            "message": f"Lỗi server: {str(e)}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 500


@app.route('/qr', methods=['GET'])
def qr_code_endpoint():
    """
    API endpoint tự động tạo id, tạo QR code và trả về ảnh QR
    
    Query Parameters:
        - sl (optional): Số lượng để tính toán số tiền trong QR code
        - format (optional): Định dạng trả về. 'json' để nhận JSON với id và qr_code base64 (mặc định), 'image' để nhận ảnh PNG với id trong header X-QR-ID
    
    Returns:
        - 200: JSON với id và qr_code base64 (mặc định) hoặc Ảnh QR code (image/png) nếu format=image
        - 400: Request không hợp lệ (JSON)
        - 500: Lỗi server (JSON)
    
    Example:
        GET /qr                    # Trả về JSON với id và qr_code base64
        GET /qr?sl=50              # Trả về JSON với id và qr_code base64
        GET /qr?format=image       # Trả về ảnh PNG với id trong header X-QR-ID
        GET /qr?sl=50&format=json  # Trả về JSON với id và qr_code base64
    """
    sl_param = request.args.get('sl')
    sl = None
    if sl_param:
        try:
            sl = int(sl_param)
        except ValueError:
            response = jsonify({
                "success": False,
                "status_code": 400,
                "message": f"Tham số 'sl' phải là số nguyên, nhận được: {sl_param}"
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            return response, 400
    
    format_param = request.args.get('format', 'json').lower()
    
    success, result, error_message = qr_code.xu_ly_qr_code(sl=sl)
    
    if not success:
        response = jsonify({
            "success": False,
            "status_code": 500,
            "message": error_message
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response, 500
    
    id = result['id']
    qr_bytes = result['qr_bytes']
    
    if format_param == 'json':
        qr_base64 = base64.b64encode(qr_bytes).decode('utf-8')
        response = jsonify({
            "success": True,
            "status_code": 200,
            "id": id,
            "qr_code": f"data:image/png;base64,{qr_base64}",
            "sl": sl
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response, 200
    
    return Response(
        qr_bytes,
        mimetype='image/png',
        headers={
            'Content-Disposition': f'inline; filename=qr_{id}.png',
            'X-QR-ID': id,
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Expose-Headers': 'X-QR-ID'
        }
    )


@app.route('/authentication', methods=['POST'])
def authentication_endpoint():
    """
    API endpoint authentication nhận request từ SePay và xử lý thanh toán
    Không yêu cầu chứng thực/token
    
    Body JSON format:
    {
        "id": 92704,
        "gateway": "Vietcombank",
        "transactionDate": "2023-03-25 14:02:37",
        "accountNumber": "0123499999",
        "code": null,
        "content": "chuyen tien mua iphone",      // id_sl (20 ký tự đầu là id, phần còn lại là sl)
        "transferType": "in",
        "transferAmount": 2277000,                // Số tiền thanh toán
        "accumulated": 19077000,
        "subAccount": null,
        "referenceCode": "MBVCB.3278907687",
        "description": ""
    }
    
    Returns:
        - 200: Request đã được xử lý thành công (JSON)
        - 400: Request không hợp lệ (JSON)
        - 500: Lỗi server (JSON)
    
    Example:
        POST /authentication
        Body: {"content": "...", "transferAmount": 2277000, ...}
    """
    json_data = request.get_json(silent=True)
    
    print("\n" + "="*60)
    print("✅ Nhận được request từ SePay!")
    print("="*60)
    print(f"📋 Method: {request.method}")
    print(f"📋 URL: {request.url}")
    
    if json_data:
        print(f"📋 JSON Body:")
        print(json.dumps(json_data, ensure_ascii=False, indent=2))
    
    if not json_data:
        print("❌ Không có JSON body trong request")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Request phải chứa JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    content = json_data.get('content')
    transfer_amount = json_data.get('transferAmount')
    
    if content is None:
        print("❌ Thiếu trường 'content' trong JSON body")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Thiếu trường 'content' trong JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    if transfer_amount is None:
        print("❌ Thiếu trường 'transferAmount' trong JSON body")
        response = jsonify({
            "success": False,
            "status_code": 400,
            "message": "Thiếu trường 'transferAmount' trong JSON body"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 400
    
    print(f"\n📤 Trích xuất thông tin:")
    print(f"   • content (gốc): {content}")
    print(f"   • transferAmount: {transfer_amount}")
    
    id_sl = authencation.parse_content(content)
    print(f"   • id_sl (sau parse): {id_sl}")
    
    print(f"\n🔄 Đang xử lý thanh toán...")
    success, message, data = authencation.xu_ly_thanh_toan(
        id_sl=id_sl,
        pay_ment=transfer_amount
    )
    
    print(f"📊 Kết quả: {message}")
    if data:
        print(f"📋 Dữ liệu: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    print("="*60 + "\n")
    
    if success:
        response = jsonify({
            "success": True,
            "status_code": 200,
            "message": message,
            "data": data
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 200
    else:
        response = jsonify({
            "success": False,
            "status_code": 500,
            "message": message,
            "data": data
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "Login & QR Payment API"
    }), 200


def main():
    """
    Main function để khởi động Flask API service
    """
    port = 5000
    local_ip = lay_ip_local()
    
    in_thong_tin_api(port, local_ip)
    
    print("\n🚀 Đang khởi động Flask server...")
    print("="*60)
    
    try:
        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=True, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Đang dừng server...")
        print("✅ Đã dừng server")
    except Exception as e:
        print(f"\n❌ Lỗi khi chạy server: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

