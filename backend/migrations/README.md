# Database Migrations

Thư mục này chứa các script migration để cập nhật cấu trúc database.

## Cách sử dụng

Chạy từ thư mục `backend/`:

```bash
python migrations/migrate_add_password.py
python migrations/migrate_add_password_to_otp.py
```

Hoặc:

```bash
cd migrations
python migrate_add_password.py
python migrate_add_password_to_otp.py
```

## Các migration scripts

- `migrate_add_password.py` - Thêm cột `password_hash` vào bảng `users`
- `migrate_add_password_to_otp.py` - Thêm cột `password_hash` vào bảng `otps`
- `migrate_add_user_key.py` - Thêm cột `key` (unique, 18 ký tự) vào bảng `users`


