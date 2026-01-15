# Scripts

Thư mục này chứa các utility scripts để quản lý và xem database.

## Cách sử dụng

Chạy từ thư mục `backend/`:

```bash
python scripts/sql_manager.py
python scripts/view_database.py
```

Hoặc:

```bash
cd scripts
python sql_manager.py
python view_database.py
```

## Các scripts

- `sql_manager.py` - Công cụ quản lý database bằng SQL commands (CLI)
  - Cho phép chạy các câu lệnh SQL trực tiếp
  - Hỗ trợ các lệnh đặc biệt: `.help`, `.tables`, `.schema`, `.count`, etc.

- `view_database.py` - Xem toàn bộ nội dung database
  - Hiển thị cấu trúc tất cả các bảng
  - Hiển thị dữ liệu trong từng bảng


