from flask import Blueprint, request, jsonify, current_app, Response, stream_with_context, session
from app.extensions import db
from app.models.user import User, Session
from app.models.transaction import Transaction
from datetime import datetime, timedelta, timezone
import random, string, re, time
import json
import os
from threading import Lock
from collections import defaultdict
import queue

# Múi giờ Việt Nam (UTC+7)
VIETNAM_TIMEZONE = timezone(timedelta(hours=7))

def to_vietnam_time(utc_dt):
    """Convert UTC datetime sang múi giờ Việt Nam"""
    if utc_dt is None:
        return None
    # Nếu datetime không có timezone info, giả sử nó là UTC
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    # Convert sang VN timezone
    return utc_dt.astimezone(VIETNAM_TIMEZONE)

payment_bp = Blueprint('payment', __name__)

# Thời gian hết hạn QR code (5 phút)
QR_EXPIRY_MINUTES = 5

# Event store để lưu events cho từng user (cho SSE)
user_events = defaultdict(queue.Queue)
events_lock = Lock()

def send_payment_event(user_id, event_data):
    """Gửi event cho user khi thanh toán thành công"""
    with events_lock:
        # Đảm bảo queue tồn tại cho user này
        if user_id not in user_events:
            user_events[user_id] = queue.Queue()
        
        event = {
            'type': 'payment_success',
            'data': event_data,
            'timestamp': time.time()
        }
        user_events[user_id].put(event)

def check_and_expire_transactions():
    """Kiểm tra và tự động chuyển các transaction quá 5 phút từ pending sang cancelled"""
    try:
        expiry_time = datetime.utcnow() - timedelta(minutes=QR_EXPIRY_MINUTES)
        
        # Tìm tất cả transaction pending quá 5 phút
        expired_transactions = Transaction.query.filter(
            Transaction.status == 'pending',
            Transaction.created_at < expiry_time
        ).all()
        
        if expired_transactions:
            for tx in expired_transactions:
                tx.status = 'cancelled'
            db.session.commit()
            print(f"⏰ Đã chuyển {len(expired_transactions)} transaction từ pending → cancelled (quá {QR_EXPIRY_MINUTES} phút)")
            return len(expired_transactions)
        
        return 0
    except Exception as e:
        print(f"[ERROR] Lỗi khi expire transactions: {e}")
        db.session.rollback()
        return 0

def is_transaction_expired(transaction):
    """Kiểm tra transaction đã hết hạn chưa (quá 5 phút)"""
    if not transaction or transaction.status != 'pending':
        return True
    
    expiry_time = transaction.created_at + timedelta(minutes=QR_EXPIRY_MINUTES)
    return datetime.utcnow() > expiry_time

# Cache config để tránh đọc file nhiều lần
_config_cache = None
_config_cache_time = 0
_config_cache_ttl = 60  # Cache 60 giây

def _load_config():
    """Load config từ file và cache lại"""
    global _config_cache, _config_cache_time
    
    # Kiểm tra cache còn valid không
    current_time = time.time()
    if _config_cache and (current_time - _config_cache_time) < _config_cache_ttl:
        return _config_cache
    
    # Đường dẫn đến file config: từ app/routes/ -> ../../config/quota_config.json
    config_path = os.path.join(
        os.path.dirname(__file__), 
        '..', '..', 'config',
        'quota_config.json'
    )
    config_path = os.path.abspath(config_path)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        _config_cache = config
        _config_cache_time = current_time
        return config
        
    except FileNotFoundError:
        print(f"[WARNING] Không tìm thấy file quota_config.json tại: {config_path}. Sử dụng giá trị mặc định")
        _config_cache = {'quota': 1.0, 'cost': 300}
        _config_cache_time = current_time
        return _config_cache
    except json.JSONDecodeError:
        print(f"[WARNING] File quota_config.json không hợp lệ tại: {config_path}. Sử dụng giá trị mặc định")
        _config_cache = {'quota': 1.0, 'cost': 300}
        _config_cache_time = current_time
        return _config_cache
    except Exception as e:
        print(f"[WARNING] Lỗi khi load quota config từ {config_path}: {e}. Sử dụng giá trị mặc định")
        _config_cache = {'quota': 1.0, 'cost': 300}
        _config_cache_time = current_time
        return _config_cache

def get_quota():
    """Load quota từ file quota_config.json"""
    config = _load_config()
    return float(config.get('quota', 1.0))

def get_cost():
    """Load cost từ file quota_config.json"""
    config = _load_config()
    return int(config.get('cost', 300))

# Middleware giả để lấy user từ token (Có thể tách ra file utils)
def get_user_from_token():
    token = request.headers.get('Authorization')
    if not token: return None
    db_session = Session.query.filter_by(token=token).first()
    if db_session and db_session.expires_at > time.time():
        return User.query.get(db_session.user_id)
    return None

def get_user_from_session_or_token():
    """Lấy user từ Flask session hoặc token (dùng cho SSE)"""
    # Ưu tiên Flask session (cookie)
    if 'user_id' in session:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        if user:
            return user
    
    # Fallback: check token từ header
    return get_user_from_token()

@payment_bp.route('/qr', methods=['POST'])
def create_qr():
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request"}), 400
            
        amount = data.get('amount')
        if not amount:
            return jsonify({"error": "Missing amount"}), 400
        
        # Validate số tiền
        try:
            amount = float(amount)
            if amount <= 0:
                return jsonify({"error": "Số tiền phải lớn hơn 0"}), 400
            if amount < 10000:
                return jsonify({"error": "Số tiền tối thiểu là 10,000 VND"}), 400
            amount = int(amount)
        except (ValueError, TypeError):
            return jsonify({"error": "Số tiền không hợp lệ"}), 400
        
        # Tự động expire các transaction cũ trước khi tạo mới
        check_and_expire_transactions()
        
        # Tạo mã giao dịch dựa trên user.key + suffix ngẫu nhiên (đảm bảo unique)
        # user.key là 18 chars, thêm 2 chars suffix = 20 chars (vừa đủ Transaction.id limit)
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=2))
        trans_id = f"{user.key}{suffix}"
        
        # Đảm bảo trans_id unique (retry nếu trùng)
        for _ in range(10):
            existing = Transaction.query.filter_by(id=trans_id).first()
            if not existing:
                break
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=2))
            trans_id = f"{user.key}{suffix}"
        else:
            return jsonify({"error": "Không thể tạo mã giao dịch duy nhất. Vui lòng thử lại."}), 500
        
        # Lưu vào DB - user_id vẫn dùng user.id (Integer Foreign Key) để đảm bảo hiệu suất và tính toàn vẹn
        new_trans = Transaction(id=trans_id, user_id=user.id, amount=amount)
        db.session.add(new_trans)
        db.session.commit()
        
        # Tính thời gian hết hạn và convert sang VN timezone
        expires_at_utc = new_trans.created_at + timedelta(minutes=QR_EXPIRY_MINUTES)
        expires_at_vn = to_vietnam_time(expires_at_utc)
        
        # Nội dung & Link QR
        memo = f"AUTO{trans_id}-{amount}END"
        bank_id = current_app.config['BANK_ID']
        acc_no = current_app.config['ACCOUNT_NO']
        template = current_app.config['TEMPLATE']
        
        qr_url = f"https://img.vietqr.io/image/{bank_id}-{acc_no}-{template}.png?amount={amount}&addInfo={memo}"
        
        return jsonify({
            "success": True,
            "trans_id": trans_id,
            "qr_url": qr_url,
            "memo": memo,
            "expires_at": expires_at_vn.isoformat() if expires_at_vn else None,  # Trả về thời gian hết hạn cho frontend (VN timezone)
            "expires_in_seconds": QR_EXPIRY_MINUTES * 60  # Số giây còn lại
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Create QR error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@payment_bp.route('/test/simulate-payment', methods=['POST'])
def test_simulate_payment():
    """Endpoint test để giả lập thanh toán - chỉ dùng trong môi trường dev
    
    Giống hệt webhook thật:
    - Lấy transfer_amount từ request (hoặc dùng tx.amount nếu không có)
    - Cập nhật tx.amount với transfer_amount
    - Tính actual_amount = transfer_amount * quota
    - Cộng vào user.credit
    - Gửi SSE event
    """
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request"}), 400
        
        trans_id = data.get('trans_id')
        if not trans_id:
            return jsonify({"error": "Thiếu trans_id"}), 400
        
        # Validate trans_id format (chỉ cho phép alphanumeric và đủ độ dài)
        if not isinstance(trans_id, str) or len(trans_id) < 18 or len(trans_id) > 20:
            return jsonify({"error": "trans_id không hợp lệ"}), 400
        
        # Tự động expire các transaction cũ
        check_and_expire_transactions()
        
        # Dùng database lock để tránh race condition
        tx = db.session.query(Transaction).filter_by(
            id=trans_id,
            user_id=user.id,
            status='pending'
        ).with_for_update().first()
        
        if not tx:
            return jsonify({"error": "Không tìm thấy giao dịch pending với trans_id này. Có thể đã hết hạn hoặc đã được xử lý."}), 404
        
        # Kiểm tra lại hết hạn sau khi lock
        if is_transaction_expired(tx):
            tx.status = 'cancelled'
            db.session.commit()
            return jsonify({"error": "QR code đã hết hạn (quá 5 phút). Vui lòng tạo QR code mới."}), 400
        
        # Lấy transfer_amount từ request (nếu có), nếu không thì dùng tx.amount ban đầu
        # Giống webhook: transfer_amount là số tiền thực tế user chuyển
        transfer_amount = data.get('transfer_amount') or tx.amount
        
        # Validate số tiền
        try:
            transfer_amount = float(transfer_amount)
            if transfer_amount <= 0:
                db.session.rollback()
                return jsonify({"error": "Số tiền phải lớn hơn 0"}), 400
            transfer_amount = int(transfer_amount)
        except (ValueError, TypeError):
            db.session.rollback()
            return jsonify({"error": "Số tiền không hợp lệ"}), 400
        
        # Lưu số tiền thực tế user đã chuyển vào transaction.amount (giống webhook)
        tx.amount = transfer_amount
        
        # Tính số điểm thực tế được cộng sau khi nhân với quota (giống webhook)
        quota = get_quota()
        actual_amount = int(transfer_amount * quota)
        
        # Reload user để đảm bảo có data mới nhất
        user = User.query.get(user.id)
        if not user:
            db.session.rollback()
            return jsonify({"error": "User not found"}), 404
        
        # Cộng điểm vào credit (đã nhân với quota) - giống webhook
        user.credit += actual_amount
        
        # Update trạng thái - giống webhook
        tx.status = 'success'
        
        db.session.commit()
        
        print(f"🧪 [TEST] Simulated payment: User {user.email} đã nạp {transfer_amount} VND (x{quota} = {actual_amount} điểm)")
        
        # Gửi SSE event cho user khi thanh toán thành công (giống webhook)
        send_payment_event(user.id, {
            'trans_id': trans_id,
            'transfer_amount': transfer_amount,
            'quota': quota,
            'actual_amount': actual_amount,
            'new_credit': user.credit
        })
        
        return jsonify({
            "success": True,
            "message": "Thanh toán test thành công!",
            "transfer_amount": transfer_amount,  # Số tiền thực tế user đã chuyển
            "quota": quota,
            "actual_amount": actual_amount,  # Số điểm thực tế được cộng
            "new_credit": user.credit
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Test simulate payment error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@payment_bp.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint nhận thanh toán từ SePay

    Logic mới: Tự động tăng credit cho user dựa trên số tiền chuyển vào tài khoản ngân hàng
    """
    try:
        # Verify API Key authentication
        auth_header = request.headers.get('Authorization', '')
        expected_api_key = 'npa_9f3c2e8a7b4d6c1e5f0a2d9b8c7e6a4'

        if not auth_header or not auth_header.startswith('Apikey '):
            print(f"❌ Webhook auth failed: Missing or invalid Authorization header")
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        provided_api_key = auth_header.replace('Apikey ', '', 1)
        if provided_api_key != expected_api_key:
            print(f"❌ Webhook auth failed: Invalid API key")
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        print(f"✅ Webhook auth successful")

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Invalid request"}), 400

        content = data.get('content', '')
        transfer_amount = data.get('transferAmount', 0)
        account_number = data.get('accountNumber', '')

        # Validate số tiền
        try:
            transfer_amount = float(transfer_amount)
            if transfer_amount <= 0:
                return jsonify({"success": False, "message": "Invalid amount"}), 400
            transfer_amount = int(transfer_amount)
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Invalid amount format"}), 400

        print(f"📩 Webhook: Account {account_number} - Amount: {transfer_amount} VND")

        # Kiểm tra tài khoản ngân hàng có khớp với config không
        expected_account = current_app.config['ACCOUNT_NO']
        if account_number != expected_account:
            print(f"⚠️ Account mismatch: received {account_number}, expected {expected_account}")
            return jsonify({"success": False, "message": "Invalid account"}), 400

        # Tự động expire các transaction cũ
        check_and_expire_transactions()

        # THỰC HIỆN LOGIC MỚI: Tăng credit dựa trên số tiền chuyển vào

        # Tính số điểm được cộng (nhân với quota)
        quota = get_quota()
        credit_to_add = int(transfer_amount * quota)

        # Tìm user có transaction pending với số tiền này
        # Hoặc có thể implement logic khác để xác định user
        pending_tx = db.session.query(Transaction).filter_by(
            status='pending',
            amount=transfer_amount  # Tìm transaction có cùng số tiền
        ).with_for_update().first()

        if pending_tx:
            # Nếu tìm thấy transaction pending khớp số tiền
            user = User.query.get(pending_tx.user_id)
            if user:
                # Cập nhật transaction
                pending_tx.status = 'success'

                # Cộng credit cho user
                user.credit += credit_to_add

                db.session.commit()
                print(f"✅ Webhook SUCCESS: User {user.email} nạp {transfer_amount} VND (x{quota} = +{credit_to_add} credit)")

                # Gửi SSE event
                send_payment_event(user.id, {
                    'trans_id': pending_tx.id,
                    'transfer_amount': transfer_amount,
                    'quota': quota,
                    'actual_amount': credit_to_add,
                    'new_credit': user.credit
                })

                return jsonify({"success": True, "message": f"Topup success: +{credit_to_add} credit"})
            else:
                print(f"❌ User not found for transaction {pending_tx.id}")
        else:
            # Logic fallback: Có thể cộng vào tài khoản admin hoặc ghi log để xử lý manual
            print(f"⚠️ No matching pending transaction found for {transfer_amount} VND")
            # Có thể implement logic để cộng vào tài khoản mặc định hoặc ghi log

        # Nếu không tìm thấy transaction phù hợp, vẫn trả success để SePay không retry
        return jsonify({"success": True, "message": "Webhook received"})

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Webhook error: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@payment_bp.route('/qr/check/<trans_id>', methods=['GET'])
def check_qr_status(trans_id):
    """Kiểm tra trạng thái QR code (còn hết hạn không)"""
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Validate trans_id format
    if not isinstance(trans_id, str) or len(trans_id) < 18 or len(trans_id) > 20:
        return jsonify({"error": "trans_id không hợp lệ"}), 400
    
    # Tự động expire các transaction cũ
    check_and_expire_transactions()
    
    # Reload user để lấy credit mới nhất
    user = User.query.get(user.id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    tx = Transaction.query.filter_by(id=trans_id, user_id=user.id).first()
    
    if not tx:
        return jsonify({
            "valid": False,
            "status": "not_found",
            "message": "Không tìm thấy giao dịch"
        }), 404
    
    # Kiểm tra status - nếu đã success, trả về thông tin chi tiết
    if tx.status == 'success':
        quota = get_quota()
        # tx.amount đã được cập nhật với số tiền thực tế user chuyển (transfer_amount)
        # Tính actual_amount (số điểm thực tế được cộng) = tx.amount * quota
        actual_amount = int(tx.amount * quota)
        
        return jsonify({
            "valid": True,
            "status": "success",
            "message": "Thanh toán thành công!",
            "transfer_amount": tx.amount,  # Số tiền thực tế user đã chuyển (VND)
            "quota": quota,
            "actual_amount": actual_amount,  # Số điểm thực tế được cộng = transfer_amount * quota
            "new_credit": user.credit,
            "created_at": to_vietnam_time(tx.created_at).isoformat() if tx.created_at else None
        })
    
    # Kiểm tra status cancelled
    if tx.status == 'cancelled':
        return jsonify({
            "valid": False,
            "status": "cancelled",
            "message": "Giao dịch đã bị hủy"
        })
    
    # Kiểm tra hết hạn
    if is_transaction_expired(tx):
        tx.status = 'cancelled'
        db.session.commit()
        return jsonify({
            "valid": False,
            "status": "expired",
            "message": "QR code đã hết hạn"
        })
    
    # Tính thời gian còn lại (vẫn dùng UTC để tính, nhưng trả về VN timezone)
    expiry_time_utc = tx.created_at + timedelta(minutes=QR_EXPIRY_MINUTES)
    expiry_time_vn = to_vietnam_time(expiry_time_utc)
    remaining_seconds = max(0, int((expiry_time_utc - datetime.utcnow()).total_seconds()))
    
    return jsonify({
        "valid": True,
        "status": "pending",
        "remaining_seconds": remaining_seconds,
        "expires_at": expiry_time_vn.isoformat() if expiry_time_vn else None  # Trả về VN timezone
    })

@payment_bp.route('/sync-session', methods=['POST'])
def sync_session():
    """Sync Flask session từ token (frontend gọi trước khi connect SSE)"""
    # Flask-CORS tự động handle OPTIONS và CORS headers
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Set Flask session với user_id
    session['user_id'] = user.id
    session.permanent = True
    
    return jsonify({"success": True, "message": "Session synced"})

@payment_bp.route('/stream', methods=['GET'])
def payment_stream():
    """SSE endpoint để push payment events real-time"""
    # Flask-CORS tự động handle OPTIONS và CORS headers
    
    # Lấy user từ session hoặc token (thử cả 2 cách)
    user = None
    
    # Cách 1: Từ Flask session (cookie)
    if 'user_id' in session:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
    
    # Cách 2: Từ token trong query parameter (vì EventSource không gửi header)
    if not user:
        token = request.args.get('token')
        if token:
            db_session = Session.query.filter_by(token=token).first()
            if db_session and db_session.expires_at > time.time():
                user = User.query.get(db_session.user_id)
                if user:
                    # Set session để lần sau không cần token
                    session['user_id'] = user.id
                    session.permanent = True
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    def event_stream():
        """Generator function để stream events"""
        user_id = user.id
        
        # Đảm bảo queue tồn tại
        with events_lock:
            if user_id not in user_events:
                user_events[user_id] = queue.Queue()
        
        try:
            while True:
                try:
                    # Lấy event từ queue (timeout 5s để check connection thường xuyên hơn)
                    try:
                        event = user_events[user_id].get(timeout=5)
                        
                        # Format SSE message
                        event_data = json.dumps(event['data'], ensure_ascii=False)
                        yield f"event: {event['type']}\n"
                        yield f"data: {event_data}\n\n"
                        
                    except queue.Empty:
                        # Gửi heartbeat để giữ connection
                        yield f": heartbeat\n\n"
                            
                except GeneratorExit:
                    # Client disconnected
                    raise
                except Exception as e:
                    # Log error nhưng tiếp tục loop
                    continue
        finally:
            # Cleanup: Xóa queue khi connection đóng (tránh memory leak)
            # Nhưng chỉ xóa nếu queue rỗng để tránh mất events đang chờ
            with events_lock:
                if user_id in user_events:
                    try:
                        # Thử get với timeout=0 để check queue có rỗng không
                        user_events[user_id].get(timeout=0)
                        # Nếu không có exception, queue không rỗng, không xóa
                    except queue.Empty:
                        # Queue rỗng, có thể xóa
                        del user_events[user_id]
    
    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # Disable buffering in nginx
            'Connection': 'keep-alive'
        }
    )

@payment_bp.route('/deduct', methods=['POST'])
def deduct_credit():
    """API để trừ credit từ tài khoản user (test)"""
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # Reload user để đảm bảo có data mới nhất
        user = User.query.get(user.id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Lấy cost từ config
        cost = get_cost()
        
        # Kiểm tra user có đủ credit không
        if user.credit < cost:
            return jsonify({
                "error": f"Số điểm không đủ. Cần {cost} điểm, hiện có {user.credit} điểm."
            }), 400
        
        # Trừ credit
        old_credit = user.credit
        user.credit -= cost
        
        # Đảm bảo credit không âm (safety check)
        if user.credit < 0:
            user.credit = 0
        
        db.session.commit()
        
        print(f"💰 User {user.email} đã trừ {cost} điểm (từ {old_credit} → {user.credit})")
        
        return jsonify({
            "success": True,
            "message": f"Đã trừ {cost} điểm thành công",
            "cost": cost,
            "old_credit": old_credit,
            "new_credit": user.credit
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Deduct credit error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@payment_bp.route('/history', methods=['GET'])
def get_transaction_history():
    """Lấy lịch sử giao dịch của user"""
    user = get_user_from_token()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Lấy tất cả transaction của user, sắp xếp theo thời gian mới nhất
    transactions = Transaction.query.filter_by(user_id=user.id)\
        .order_by(Transaction.created_at.desc())\
        .all()
    
    # Format dữ liệu để trả về (convert sang múi giờ Việt Nam)
    history = []
    for tx in transactions:
        vn_time = to_vietnam_time(tx.created_at) if tx.created_at else None
        history.append({
            "id": tx.id,
            "amount": tx.amount,
            "status": tx.status,
            "content": tx.content or f"AUTO{tx.id}-{tx.amount}END",
            "created_at": vn_time.isoformat() if vn_time else None
        })
    
    return jsonify({
        "success": True,
        "transactions": history,
        "total": len(history)
    })