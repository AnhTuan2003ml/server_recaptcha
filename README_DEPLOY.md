# 🚀 Hướng Dẫn Deploy & Sử Dụng

## 📋 Tổng Quan

Hệ thống gồm 3 phần:
- **Frontend**: Nuxt.js (port 3000) - Giao diện web
- **Backend**: Flask (port 5000) - API chính + thanh toán
- **Recaptcha**: Flask (port 5001) - API recaptcha + admin

## 🌐 Public URLs (Domain Thật)

### Frontend (Port 3000)
```
🌐 https://web.nanoproai.shop/web
```
Ví dụ: Truy cập web app tại URL trên

### Backend API (Port 5000)
```
🔗 https://api.nanoproai.shop/api
```
Ví dụ:
- Payment Webhook: `https://api.nanoproai.shop/api/payment/webhook`
- Other APIs: `https://api.nanoproai.shop/api/...`

### Recaptcha API (Port 5001) - Service Riêng Biệt
```
🤖 https://recaptcha.nanoproai.shop/recaptcha
```
**Note**: Đây là API service riêng biệt, không liên quan đến giao diện web.

Ví dụ:
- Captcha Token: `https://recaptcha.nanoproai.shop/recaptcha/get_captcha_token?apikey=YOUR_KEY`
- Admin Dashboard: `https://recaptcha.nanoproai.shop/recaptcha/admin` (chỉ để quản lý)

## 🛠️ Hướng Dẫn Deploy

### Bước 1: Khởi động Services

```bash
# Terminal 1: Backend chính (port 5000)
cd backend
python run.py

# Terminal 2: Recaptcha service (port 5001)
cd backend
python run_recaptcha.py --port 5001

# Terminal 3: Frontend (port 3000)
cd frontend
npm run dev
```

### Bước 2: Cấu hình Domain (nếu dùng domain thật)

Nếu bạn dùng domain thật như `nanoproai.shop`:
- `web.nanoproai.shop` → trỏ đến server port 3000
- `api.nanoproai.shop` → trỏ đến server port 5000
- `recaptcha.nanoproai.shop` → trỏ đến server port 5001

### Bước 3: Hoặc Tạo Cloudflare Tunnels

Nếu dùng tunnel thay vì domain thật:

```bash
# Tunnel cho Frontend (port 3000)
cloudflared tunnel --url http://localhost:3000

# Tunnel cho Backend (port 5000)
cloudflared tunnel --url http://localhost:5000

# Tunnel cho Recaptcha (port 5001)
cloudflared tunnel --url http://localhost:5001
```

### Bước 4: Cập Nhật Config

Cập nhật `frontend/nuxt.config.ts` với URLs phù hợp:

**Cho Domain thật:**
```typescript
runtimeConfig: {
  public: {
    apiBase: 'https://api.nanoproai.shop/api'
  }
},

vite: {
  server: {
    allowedHosts: [
      'web.nanoproai.shop',
      'api.nanoproai.shop',
      'recaptcha.nanoproai.shop'
    ],
  }
}
```

**Cho Tunnel:**
```typescript
runtimeConfig: {
  public: {
    // 🚨 Dán tunnel URL của BACKEND (port 5000) vào đây
    apiBase: 'https://[backend-tunnel].trycloudflare.com/api'
  }
},

vite: {
  server: {
    // 🚨 Dán tunnel URL của FRONTEND (port 3000) vào đây
    allowedHosts: ['[frontend-tunnel].trycloudflare.com', 'localhost'],
  }
}
```

### Bước 5: Restart Frontend

```bash
cd frontend
npm run dev  # Restart để áp dụng config mới
```

**Note**: Hiện tại config đã được set cho domain `nanoproai.shop`. Nếu bạn đổi sang tunnel, hãy cập nhật URLs trong `nuxt.config.ts`.

## 📚 API Documentation

### Captcha Token (Recaptcha Service - Port 5001)
```bash
GET https://recaptcha.nanoproai.shop/recaptcha/get_captcha_token?apikey=YOUR_KEY
```
**Note**: API này chạy trên recaptcha service (port 5001), không phải backend chính (port 5000)

### Admin Dashboard (Recaptcha Service - Port 5001)
```bash
GET https://recaptcha.nanoproai.shop/recaptcha/admin
```

### Payment Webhook (Backend - Port 5000)
```bash
POST https://api.nanoproai.shop/api/payment/webhook
```

**Authentication**: Required
```json
Headers: {
  "Authorization": "Apikey npa_9f3c2e8a7b4d6c1e5f0a2d9b8c7e6a4"
}
```

### API Home (Recaptcha Service - Port 5001)
```bash
GET https://recaptcha.nanoproai.shop/recaptcha
```
Trả về thông tin các endpoints có sẵn.

## 🔧 Troubleshooting

### Lỗi 404 khi access admin
- Kiểm tra recaptcha service có chạy trên port 5001
- Kiểm tra tunnel cho port 5001 có hoạt động

### Lỗi CORS
- Frontend đang call localhost thay vì tunnel URL
- Kiểm tra `apiBase` trong `nuxt.config.ts`

### Tunnel không kết nối
- Kiểm tra service có chạy trên port tương ứng
- Kiểm tra firewall có block port
- Restart tunnel: `cloudflared tunnel --url http://localhost:PORT`

## 📞 Support

Nếu gặp vấn đề:
1. Check logs của từng service
2. Verify tunnel URLs
3. Test direct access: `http://localhost:PORT`
4. Check firewall rules

---

**🎉 Hệ thống đã sẵn sàng cho production!**
