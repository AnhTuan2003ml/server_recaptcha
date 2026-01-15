<div align="center">

<img src="assets/header.gif" width="150" height="auto">

**Recaptcha-V3** is a bypasser Google Recaptcha V3 with URL.

</div>

## **Installation**

**Using** `poetry`

```
git clone https://github.com/x404xx/Recaptcha-V3.git
cd Recaptcha-V3
poetry shell
poetry install
```

**Using** `pip`

```
git clone https://github.com/x404xx/Recaptcha-V3.git
cd Recaptcha-V3
virtualenv env
env/scripts/activate
pip install -r requirements.txt
```

## Url

```
https://antcpt.com/score_detector/
https://2captcha.com/demo/recaptcha-v3-enterprise
```

## Usage

```
python main.py
```

### API Server
```
# Khởi động API server (default port 5001)
python api.py

# Chạy trên port khác nếu cần
python api.py --port 5000

# Test single browser instance
python test_single_browser.py
```

#### API Endpoints
- **GET** `/` - Trang chủ API
- **GET** `/get_captcha_token` - Lấy captcha token trực tiếp

#### API Response Format
```json
{
  "success": true,
  "captcha_token": "token_string_here",
  "message": "Lấy Token thành công (Dài 1657 ký tự)",
  "length": 1657,
  "timestamp": 1704067200
}
```

#### Example Usage
```bash
# 1. Lấy captcha token
curl http://localhost:5000/get_captcha_token

# 2. Tạo batch images (song song)
curl -X POST http://localhost:5000/generate_images \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your_user_id",
    "requests": [
      {
        "seed": 12345,
        "imageModelName": "GEM_PIX_2",
        "imageAspectRatio": "IMAGE_ASPECT_RATIO_LANDSCAPE",
        "prompt": "A beautiful sunset"
      },
      {
        "seed": 67890,
        "imageModelName": "GEM_PIX_2",
        "imageAspectRatio": "IMAGE_ASPECT_RATIO_PORTRAIT",
        "prompt": "A cute cat"
      }
    ]
  }'

# 3. Check batch status
curl http://localhost:5000/batch/YOUR_BATCH_ID

# 4. Check single task status
curl http://localhost:5000/task/YOUR_TASK_ID

# 5. Get queue statistics
curl http://localhost:5000/queue/stats

# 6. API information
curl http://localhost:5000/
```

#### Key Features
- **Single Browser Instance**: Sử dụng 1 browser duy nhất cho tất cả requests, khởi tạo ngay khi server start
- **Thread-Safe**: Browser được khởi tạo trong main thread để tránh lỗi threading
- **Sequential Processing**: Xử lý requests lần lượt với delay 1s để tránh rate limiting
- **Batch Processing**: Submit nhiều requests cùng lúc với monitoring real-time
- **Credit Integration**: Tự động cập nhật credit sau khi hoàn thành
- **Queue Management**: Hệ thống queue với cleanup tự động

## Output

<div align="center">

**antcpt.com**

<img src="assets/ant.png" width="500" height="auto">

**2captcha.com**

<img src="assets/twocap.png" width="500" height="auto">

</div>

## Todo

-   [x] Correct get api type

> Sometimes the API type is not shown in the HTML. We need to implement it correctly to retrieve the API type.

## **Legal Disclaimer**

> This was made for educational purposes only, nobody which directly involved in this project is responsible for any damages caused. **_You are responsible for your actions._**
