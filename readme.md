# Payment System - Hệ Thống Thanh Toán QR Code

## 📋 Mục Lục

1. [Tổng Quan](#tổng-quan)
2. [Kiến Trúc Hệ Thống](#kiến-trúc-hệ-thống)
3. [Cài Đặt và Chạy](#cài-đặt-và-chạy)
4. [Cách Vận Hành](#cách-vận-hành)
5. [API Endpoints](#api-endpoints)
6. [Database Models](#database-models)
7. [Bảo Mật](#bảo-mật)
8. [Cấu Hình](#cấu-hình)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Tổng Quan

Hệ thống thanh toán QR Code với các tính năng:

- ✅ **Xác thực người dùng**: Đăng ký/Đăng nhập bằng Email + OTP hoặc Password
- ✅ **Tạo QR Code**: Tạo mã QR thanh toán với thời gian hết hạn 5 phút
- ✅ **Thanh toán thực tế**: Tích hợp SePay webhook để nhận thanh toán từ ngân hàng
- ✅ **Thanh toán test**: Endpoint test để giả lập thanh toán
- ✅ **Real-time Updates**: Server-Sent Events (SSE) để cập nhật trạng thái thanh toán real-time
- ✅ **Lịch sử giao dịch**: Xem lịch sử tất cả các giao dịch

### Công Nghệ Sử Dụng

**Backend:**

- Python 3.12+
- Flask (REST API)
- SQLAlchemy (ORM)
- SQLite Database
- Server-Sent Events (SSE)

**Frontend:**

- Vue.js 3
- Nuxt.js 3
- TypeScript
- Pinia (State Management)

---

## 🏗️ Kiến Trúc Hệ Thống

### Cấu Trúc Thư Mục

```
server_new/
├── backend/                 # Backend Flask API
│   ├── app/
│   │   ├── __init__.py      # Flask app factory
│   │   ├── extensions.py    # DB, CORS extensions
│   │   ├── models/          # Database models
│   │   │   ├── user.py      # User, Session, OTP models
│   │   │   └── transaction.py  # Transaction model
│   │   ├── routes/          # API routes
│   │   │   ├── auth.py      # Authentication endpoints
│   │   │   ├── user.py      # User endpoints
│   │   │   └── payment.py   # Payment endpoints (QR, webhook, SSE)
│   │   └── services/        # Business logic services
│   │       └── email_service.py
│   ├── config/
│   │   ├── email_config.json    # Email configuration
│   │   └── quota_config.json    # Quota & Cost configuration
│   ├── config.py            # Flask configuration
│   ├── run.py               # Application entry point
│   └── requirements.txt     # Python dependencies
│
├── frontend/                # Frontend Nuxt.js app
│   ├── app/
│   │   ├── pages/           # Vue pages
│   │   │   ├── index.vue    # Main dashboard (QR, payment)
│   │   │   ├── login.vue    # Login page
│   │   │   └── register.vue # Register page
│   │   ├── stores/
│   │   │   └── auth.ts      # Pinia auth store
│   │   └── assets/
│   └── package.json
│
└── README.md               # This file
```

---

## 🚀 Cài Đặt và Chạy

### Prerequisites

- Python 3.12+
- Node.js 18+
- npm hoặc yarn

### Backend Setup

```bash
# 1. Tạo virtual environment
cd backend
python -m venv venv

# 2. Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Cấu hình environment variables (optional)
# Tạo file .env hoặc set trong config.py:
# SECRET_KEY=your-secret-key
# WEBHOOK_SECRET=your-webhook-secret

# 5. Chạy server
python run.py
```

Backend sẽ chạy tại: `http://localhost:5000`

### Frontend Setup

```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Cấu hình API base URL trong nuxt.config.ts
# apiBase: 'http://localhost:5000/api'

# 3. Chạy dev server
npm run dev
```

Frontend sẽ chạy tại: `http://localhost:3000`

---

## ⚙️ Cách Vận Hành

### 1. Flow Đăng Ký/Đăng Nhập

```
User → Frontend → Backend
  ↓
[Đăng ký]
1. User nhập email + password
2. Backend gửi OTP qua email
3. User nhập OTP để xác thực
4. Backend tạo user + session token
5. Frontend lưu token và chuyển đến dashboard

[Đăng nhập]
1. User nhập email + password (hoặc OTP)
2. Backend verify và tạo session token
3. Frontend lưu token và chuyển đến dashboard
```

### 2. Flow Thanh Toán QR Code

```
Step 1: User tạo QR Code
├─ Frontend gọi: POST /api/payment/qr
├─ Backend tạo transaction (status: pending)
├─ Backend tạo QR code với memo: AUTO{trans_id}-{amount}END
└─ Frontend hiển thị QR code và bắt đầu SSE connection

Step 2: User thanh toán
├─ User mở app ngân hàng
├─ Quét QR code
└─ Chuyển tiền theo số tiền trong QR

Step 3: SePay xác nhận
├─ SePay gửi webhook: POST /api/payment/webhook
├─ Backend parse content: AUTO{trans_id}-{amount}END
├─ Backend tìm transaction pending
├─ Backend cộng điểm: user.credit += (transfer_amount * quota)
├─ Backend cập nhật: tx.status = 'success'
└─ Backend gửi SSE event cho user

Step 4: Frontend cập nhật (Real-time)
├─ Frontend nhận SSE event: 'payment_success'
├─ Frontend đóng modal nạp tiền
├─ Frontend hiển thị toast thông báo trên dashboard
├─ Frontend refresh user data (cập nhật số dư)
└─ Toast tự động ẩn sau 5 giây
```

### 3. Server-Sent Events (SSE) Flow

```
1. User tạo QR code
   → Frontend gọi /payment/sync-session (set cookie)
   → Frontend tạo EventSource connection: /payment/stream?token=...

2. Backend SSE Stream
   → Check authentication (cookie hoặc token)
   → Listen events từ queue[user_id]
   → Push events đến frontend real-time

3. Khi thanh toán thành công
   → Webhook gọi send_payment_event(user_id, event_data)
   → Event được thêm vào queue[user_id]
   → SSE stream đọc từ queue và gửi đến frontend
   → Frontend nhận event và cập nhật UI
```

---

## 📡 API Endpoints

### Authentication (`/api/auth`)

#### `POST /api/auth/register`

Đăng ký tài khoản mới (gửi OTP)

```json
Request: { "email": "user@example.com", "password": "password123" }
Response: { "success": true, "message": "Mã OTP đã được gửi" }
```

#### `POST /api/auth/register/verify`

Xác thực OTP và tạo tài khoản

```json
Request: { "email": "user@example.com", "otp": "123456" }
Response: { "success": true, "token": "...", "message": "Đăng ký thành công" }
```

#### `POST /api/auth/login/otp`

Gửi OTP cho đăng nhập

```json
Request: { "email": "user@example.com" }
Response: { "success": true, "message": "Mã OTP đã được gửi" }
```

#### `POST /api/auth/login`

Đăng nhập bằng password hoặc OTP

```json
Request: { "email": "user@example.com", "password": "..." } hoặc { "email": "...", "otp": "123456" }
Response: { "success": true, "token": "...", "remember": false }
```

#### `POST /api/auth/change-password`

Đổi mật khẩu

```json
Headers: { "Authorization": "token" }
Request: { "old_password": "...", "new_password": "..." }
Response: { "success": true, "message": "Đổi mật khẩu thành công" }
```

### User (`/api/user`)

#### `GET /api/user/me`

Lấy thông tin user hiện tại

```json
Headers: { "Authorization": "token" }
Response: { "id": 1, "email": "user@example.com", "credit": 1000000 }
```

### Payment (`/api/payment`)

#### `POST /api/payment/qr`

Tạo QR code thanh toán

```json
Headers: { "Authorization": "token" }
Request: { "amount": 100000 }
Response: {
  "success": true,
  "trans_id": "userkey123AB",
  "qr_url": "https://img.vietqr.io/image/...",
  "memo": "AUTOuserkey123AB-100000END",
  "expires_at": "2024-01-07T16:35:00+07:00",
  "expires_in_seconds": 300
}
```

#### `POST /api/payment/webhook`

Webhook nhận thanh toán từ SePay (không cần auth, nhưng có secret key)

```json
Headers: { "X-Webhook-Secret": "webhook-secret-key" }  # Optional
Request: {
  "content": "MBVCB... AUTOuserkey123AB-100000END ...",
  "transferAmount": 100000,
  ...
}
Response: { "success": true, "message": "Topup success" }
```

#### `GET /api/payment/stream?token=...`

SSE endpoint để nhận payment events real-time

```
Headers: Cookie (Flask session) hoặc token trong query
Response: text/event-stream
Events:
  - payment_success: { "trans_id": "...", "actual_amount": 200000, "new_credit": 1200000, ... }
  - heartbeat: Giữ connection
```

#### `POST /api/payment/sync-session`

Sync Flask session từ token (cho SSE)

```json
Headers: { "Authorization": "token" }
Response: { "success": true, "message": "Session synced" }
```

#### `GET /api/payment/qr/check/<trans_id>`

Kiểm tra trạng thái QR code (backup, không cần thiết khi dùng SSE)

```json
Headers: { "Authorization": "token" }
Response: {
  "valid": true,
  "status": "pending|success|cancelled|expired",
  "remaining_seconds": 250,
  "transfer_amount": 100000,
  "actual_amount": 200000,
  "new_credit": 1200000
}
```

#### `POST /api/payment/test/simulate-payment`

Test thanh toán (giống hệt webhook thật)

```json
Headers: { "Authorization": "token" }
Request: { "trans_id": "userkey123AB", "transfer_amount": 100000 }  # transfer_amount optional
Response: {
  "success": true,
  "transfer_amount": 100000,
  "quota": 2.0,
  "actual_amount": 200000,
  "new_credit": 1200000
}
```

#### `POST /api/payment/deduct`

Trừ credit (test)

```json
Headers: { "Authorization": "token" }
Response: {
  "success": true,
  "cost": 300,
  "old_credit": 1000000,
  "new_credit": 999700
}
```

#### `GET /api/payment/history`

Lấy lịch sử giao dịch

```json
Headers: { "Authorization": "token" }
Response: {
  "success": true,
  "transactions": [
    {
      "id": "userkey123AB",
      "amount": 100000,
      "status": "success",
      "content": "AUTOuserkey123AB-100000END",
      "created_at": "2024-01-07T16:30:00+07:00"
    }
  ],
  "total": 10
}
```

---

## 🗄️ Database Models

### User Model

```python
- id: Integer (Primary Key)
- email: String(120), unique, not null
- key: String(18), unique, not null  # 18 ký tự random key
- password_hash: String(255), nullable
- credit: Integer, default=0
- created_at: DateTime
```

### Session Model

```python
- token: String(64), Primary Key
- user_id: Integer (Foreign Key → users.id)
- expires_at: Float (Unix timestamp)
```

### Transaction Model

```python
- id: String(20), Primary Key  # Format: {user.key}{2 random chars}
- user_id: Integer (Foreign Key → users.id)
- amount: Integer, not null  # Số tiền thực tế user chuyển (được cập nhật từ webhook)
- status: String(20), default='pending'  # pending, success, cancelled
- content: String(200), nullable
- created_at: DateTime
```

### OTP Model

```python
- email: String(120), Primary Key
- otp_code: String(6), not null
- expires_at: Float (Unix timestamp)
- password_hash: String(255), nullable  # Lưu tạm khi đăng ký
```

---

## 🔒 Bảo Mật

### 1. Authentication & Authorization

#### Token-Based Authentication

- Tất cả API endpoints (trừ webhook) yêu cầu token trong header `Authorization`
- Token được lưu trong database (`sessions` table) với thời gian hết hạn
- Token tự động expire sau 2-5 ngày tùy vào `remember` flag

#### Webhook Authentication (Optional)

```python
# Nếu set WEBHOOK_SECRET trong config, webhook yêu cầu:
Headers: { "X-Webhook-Secret": "your-secret-key" }
```

### 2. Input Validation

- ✅ Validate số tiền: `amount > 0`, `amount >= 10000`
- ✅ Validate `trans_id` format: length 18-20, alphanumeric
- ✅ Validate JSON input tồn tại
- ✅ Sanitize user inputs

### 3. Race Condition Protection

#### Database Lock

```python
# Sử dụng SELECT FOR UPDATE để lock row
tx = db.session.query(Transaction).filter_by(
    id=trans_id,
    status='pending'
).with_for_update().first()

# Đảm bảo chỉ 1 request có thể xử lý transaction cùng lúc
# Tránh double spending khi webhook bị gọi nhiều lần
```

### 4. SQL Injection Prevention

- ✅ Sử dụng SQLAlchemy ORM cho tất cả queries
- ✅ Không có raw SQL queries
- ✅ Parameterized queries tự động

### 5. XSS Protection

- ✅ Cookie HttpOnly: JavaScript không thể đọc session cookie
- ✅ Cookie Secure: Chỉ gửi qua HTTPS (production)
- ✅ Cookie SameSite: CSRF protection

### 6. CORS Configuration

```python
# Backend config
cors.init_app(app, supports_credentials=True)
# Cho phép credentials (cookies) cross-origin
```

### 7. Error Handling

- ✅ Không expose internal errors ra client
- ✅ Generic error messages cho production
- ✅ Detailed logging cho debugging

### 8. Session Security

```python
# Flask session cookie
SESSION_COOKIE_HTTPONLY = True      # Prevent XSS
SESSION_COOKIE_SECURE = True        # HTTPS only (production)
SESSION_COOKIE_SAMESITE = 'Lax'     # CSRF protection
PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
```

### 9. Password Security

- ✅ Password hashing: `werkzeug.security.generate_password_hash`
- ✅ Bcrypt algorithm (mặc định của werkzeug)
- ✅ Password không được lưu plaintext

### 10. Transaction Expiry

- ✅ QR code tự động hết hạn sau 5 phút
- ✅ Transaction pending quá 5 phút → `cancelled`
- ✅ Auto-expire check chạy trước mỗi operation

---

## ⚙️ Cấu Hình

### Backend Configuration (`backend/config.py`)

```python
# Database
SQLALCHEMY_DATABASE_URI = 'sqlite:///payment.db'

# Security
SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-secret'
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')  # Optional

# Session Cookie
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # True in production
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = 86400

# Payment
BANK_ID = "MB"
ACCOUNT_NO = "0123456789"
TEMPLATE = "compact"
```

### Quota Configuration (`backend/config/quota_config.json`)

```json
{
  "quota": 2.0, // Hệ số nhân: actual_amount = transfer_amount * quota
  "cost": 300 // Chi phí mỗi lần trừ điểm (test)
}
```

### Email Configuration (`backend/config/email_config.json`)

```json
{
  "sender": "your-email@gmail.com",
  "password": "app-password"
}
```

### Frontend Configuration (`frontend/nuxt.config.ts`)

```typescript
runtimeConfig: {
  public: {
    apiBase: "http://localhost:5000/api";
  }
}
```

---

## 🔄 Luồng Xử Lý Thanh Toán Chi Tiết

### A. Tạo QR Code

```
1. User nhập số tiền (>= 10,000 VND)
   ↓
2. Frontend: POST /api/payment/qr { amount: 100000 }
   ↓
3. Backend:
   - Validate user (token)
   - Validate amount > 0 và >= 10000
   - Auto-expire transactions cũ
   - Tạo trans_id: {user.key}{2 random chars} (20 chars)
   - Lưu transaction: { id, user_id, amount, status='pending' }
   - Tạo memo: AUTO{trans_id}-{amount}END
   - Tạo QR URL: https://img.vietqr.io/image/{bank}-{acc}-{template}.png?amount={amount}&addInfo={memo}
   ↓
4. Frontend nhận QR URL
   - Hiển thị QR code
   - Bắt đầu countdown (5 phút)
   - Gọi /payment/sync-session (set cookie)
   - Tạo SSE connection: /payment/stream?token=...
```

### B. Thanh Toán Thực Tế (SePay Webhook)

```
1. User quét QR và thanh toán trong app ngân hàng
   ↓
2. SePay xác nhận thanh toán
   ↓
3. SePay gửi webhook: POST /api/payment/webhook
   Body: {
     "content": "...AUTOuserkey123AB-100000END...",
     "transferAmount": 100000
   }
   ↓
4. Backend xử lý:
   a. Verify webhook secret (nếu có)
   b. Validate transfer_amount > 0
   c. Parse content: regex AUTO([A-Za-z0-9]+)-(\d+)END
   d. Lấy trans_id từ content
   e. Lock transaction: SELECT ... FOR UPDATE
   f. Check transaction tồn tại và status='pending'
   g. Check transaction chưa hết hạn (5 phút)
   h. Cập nhật: tx.amount = transfer_amount
   i. Tính: actual_amount = transfer_amount * quota
   j. Cộng điểm: user.credit += actual_amount
   k. Cập nhật: tx.status = 'success'
   l. Commit database
   m. Gửi SSE event: send_payment_event(user_id, {...})
   ↓
5. SSE Stream gửi event đến frontend:
   event: payment_success
   data: {
     "trans_id": "userkey123AB",
     "transfer_amount": 100000,
     "quota": 2.0,
     "actual_amount": 200000,
     "new_credit": 1200000
   }
   ↓
6. Frontend nhận event:
   - Dừng SSE và countdown
   - Hiển thị toast: "✅ Thanh toán thành công! Đã cộng 200,000 điểm..."
   - Đóng modal nạp tiền
   - Refresh user data: auth.fetchUser()
   - Toast tự ẩn sau 5 giây
```

### C. Tính Toán Điểm

```
Số điểm được cộng = Số tiền thực tế user chuyển × Quota

Ví dụ:
- User tạo QR: 100,000 VND
- User chuyển thực tế: 100,000 VND
- Quota: 2.0
- Điểm được cộng: 100,000 × 2.0 = 200,000 điểm
- Số dư mới: 1,000,000 + 200,000 = 1,200,000 điểm
```

---

## 🔐 Chi Tiết Bảo Mật

### 1. Webhook Security

**Vấn đề:** Webhook endpoint công khai, không có authentication mặc định

**Giải pháp:**

```python
# Set WEBHOOK_SECRET trong environment
export WEBHOOK_SECRET="your-secret-key-here"

# Webhook verify secret
if webhook_secret:
    provided_secret = request.headers.get('X-Webhook-Secret')
    if not provided_secret or provided_secret != webhook_secret:
        return 401 Unauthorized
```

**Deploy:** Đảm bảo SePay có thể gửi header `X-Webhook-Secret` khi gọi webhook

### 2. Race Condition Protection

**Vấn đề:** Nếu webhook bị gọi nhiều lần, có thể cộng tiền nhiều lần

**Giải pháp:**

```python
# Database row lock
tx = db.session.query(Transaction).filter_by(
    id=trans_id,
    status='pending'
).with_for_update().first()  # Lock row

# Chỉ xử lý nếu status='pending'
if tx.status == 'pending':
    # Process payment
    tx.status = 'success'  # Đánh dấu đã xử lý
```

**Kết quả:** Chỉ request đầu tiên xử lý, các request sau bị block hoặc thấy status='success' → skip

### 3. Transaction Expiry

**Vấn đề:** QR code không có giới hạn thời gian

**Giải pháp:**

```python
QR_EXPIRY_MINUTES = 5

# Auto-expire transactions cũ
def check_and_expire_transactions():
    expiry_time = datetime.utcnow() - timedelta(minutes=5)
    expired = Transaction.query.filter(
        Transaction.status == 'pending',
        Transaction.created_at < expiry_time
    ).all()
    for tx in expired:
        tx.status = 'cancelled'
```

**Kết quả:** Transaction tự động cancelled sau 5 phút, không thể thanh toán

### 4. Memory Leak Prevention (SSE)

**Vấn đề:** Event queue không được cleanup → memory leak

**Giải pháp:**

```python
# Cleanup queue khi SSE connection đóng
def event_stream():
    try:
        # Listen events...
    finally:
        # Xóa queue nếu rỗng
        if user_events[user_id].empty():
            del user_events[user_id]
```

### 5. Input Validation

**Tất cả inputs đều được validate:**

```python
# Số tiền
amount = float(amount)
if amount <= 0: return 400
if amount < 10000: return 400

# Transaction ID
if len(trans_id) < 18 or len(trans_id) > 20: return 400

# JSON input
if not data: return 400
```

---

## 🧪 Testing

### Test Thanh Toán

1. **Tạo QR code:**

   ```bash
   POST /api/payment/qr
   Headers: Authorization: your-token
   Body: { "amount": 100000 }
   ```

2. **Test thanh toán (giống webhook thật):**

   ```bash
   POST /api/payment/test/simulate-payment
   Headers: Authorization: your-token
   Body: { "trans_id": "userkey123AB" }
   ```

3. **Kết quả:**
   - Backend cộng điểm
   - SSE event được gửi
   - Frontend tự động cập nhật UI

---

## 🐛 Troubleshooting

### Lỗi: SSE không nhận được events

**Nguyên nhân:**

- Cookie không được set
- Token không hợp lệ
- SSE connection bị đóng

**Giải pháp:**

1. Check browser console → Xem có lỗi CORS không
2. Check Network tab → Xem SSE request có 200 OK không
3. Verify: Đã gọi `/payment/sync-session` trước khi connect SSE

### Lỗi: Webhook không cộng tiền

**Nguyên nhân:**

- Content không match format `AUTO{id}-{amount}END`
- Transaction đã hết hạn
- Transaction không tồn tại hoặc đã success

**Giải pháp:**

1. Check backend logs → Xem có log "📩 Webhook" không
2. Verify content format đúng
3. Check transaction trong database

### Lỗi: CORS

**Nguyên nhân:**

- Frontend và backend khác origin
- CORS headers không đúng

**Giải pháp:**

```python
# Backend đã config:
cors.init_app(app, supports_credentials=True)
```

### Lỗi: Token expired

**Nguyên nhân:**

- Token đã hết hạn (2-5 ngày)

**Giải pháp:**

- User cần login lại

---

## 📝 Ghi Chú Quan Trọng

### Production Checklist

- [ ] Set `SECRET_KEY` trong environment variable
- [ ] Set `WEBHOOK_SECRET` trong environment variable
- [ ] Set `SESSION_COOKIE_SECURE = True` (HTTPS only)
- [ ] Thay đổi `WEBHOOK_SECRET` default value
- [ ] Thay đổi `SECRET_KEY` default value
- [ ] Setup HTTPS/SSL certificate
- [ ] Backup database định kỳ
- [ ] Setup logging system (thay vì print)
- [ ] Monitor SSE connections
- [ ] Rate limiting cho webhook endpoint

### Environment Variables

```bash
# .env file hoặc system environment
SECRET_KEY=your-super-secret-key-change-this
WEBHOOK_SECRET=your-webhook-secret-key
FLASK_ENV=production  # Để enable HTTPS cookie
```

---

## 📞 Support

Nếu gặp vấn đề, check:

1. Backend logs (console output)
2. Frontend browser console (F12)
3. Network tab (xem API requests)
4. Database (dùng `backend/scripts/view_database.py`)

---

## 📄 License

Private project
