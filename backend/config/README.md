# Configuration Files

Thư mục này chứa các file cấu hình của ứng dụng.

## Files

- `email_config.json` - Cấu hình email để gửi OTP
  - **Lưu ý**: File này chứa thông tin nhạy cảm (password)
  - Nên thêm vào `.gitignore` để không commit lên Git

- `quota_config.json` - Cấu hình hệ số nhân khi nạp tiền
  - Xác định hệ số nhân cho số tiền nạp vào tài khoản

## Cấu trúc email_config.json

```json
{
    "sender": "your-email@gmail.com",
    "password": "your-app-password"
}
```

**Lưu ý bảo mật:**
- Sử dụng App Password của Gmail (không phải mật khẩu chính)
- Không commit file này lên repository công khai
- Nên sử dụng environment variables trong môi trường production

## Cấu trúc quota_config.json

```json
{
    "quota": 2
}
```

**Giải thích:**
- `quota`: Hệ số nhân khi nạp tiền (số thực)
- Ví dụ: Nếu `quota = 2`, khi nạp 10,000 VND → credit sẽ được cộng 20,000 VND
- Giá trị mặc định là `1` nếu file không tồn tại hoặc có lỗi

**Ví dụ sử dụng:**
- `quota = 1`: Nạp bao nhiêu nhận bấy nhiêu (không nhân)
- `quota = 2`: Nạp 10,000 → nhận 20,000 (nhân đôi)
- `quota = 1.5`: Nạp 10,000 → nhận 15,000 (nhân 1.5 lần)


