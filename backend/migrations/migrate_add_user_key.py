"""
Script để migrate database - thêm cột key vào bảng users
Chạy script này một lần để cập nhật database
"""
import sqlite3
import os
import sys
import random
import string

# Set UTF-8 encoding cho Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def generate_unique_key(cursor, max_attempts=10):
    """Tạo key 18 ký tự unique"""
    for _ in range(max_attempts):
        key = ''.join(random.choices(string.ascii_letters + string.digits, k=18))
        cursor.execute("SELECT COUNT(*) FROM users WHERE key = ?", (key,))
        if cursor.fetchone()[0] == 0:
            return key
    return None

def migrate_database():
    # Đường dẫn database: từ migrations/ -> ../instance/payment.db
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'payment.db')
    db_path = os.path.abspath(db_path)
    
    if not os.path.exists(db_path):
        print(f"[ERROR] Database khong ton tai tai: {db_path}")
        print("[INFO] Database se duoc tao tu dong khi chay app")
        return
    
    print(f"[INFO] Dang mo database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Kiểm tra xem bảng users có tồn tại không
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("[ERROR] Bang users khong ton tai!")
            print("[INFO] Bang se duoc tao tu dong khi chay app")
            return
        
        # Kiểm tra xem cột key đã tồn tại chưa
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'key' in columns:
            print("[SUCCESS] Cot key da ton tai trong bang users, khong can migrate")
            return
        
        print("[INFO] Dang them cot key vao bang users...")
        
        # Thêm cột key (nullable tạm thời)
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN key VARCHAR(18) NULL
        """)
        
        # Tạo key cho các user hiện có (nếu có)
        cursor.execute("SELECT id FROM users WHERE key IS NULL")
        users_without_key = cursor.fetchall()
        
        if users_without_key:
            print(f"[INFO] Dang tao key cho {len(users_without_key)} user hien co...")
            for (user_id,) in users_without_key:
                user_key = generate_unique_key(cursor)
                if user_key:
                    cursor.execute("UPDATE users SET key = ? WHERE id = ?", (user_key, user_id))
                    print(f"  - User ID {user_id}: key = {user_key}")
                else:
                    print(f"  [WARNING] Khong the tao key cho user ID {user_id}")
        
        # Tạo unique index cho cột key
        try:
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_users_key ON users(key)
            """)
            print("[INFO] Da tao unique index cho cot key")
        except sqlite3.OperationalError as e:
            print(f"[WARNING] Khong the tao unique index: {e}")
        
        # Đặt NOT NULL constraint (SQLite không hỗ trợ ALTER COLUMN, nên chỉ cảnh báo)
        print("[INFO] Luu y: Cot key can duoc set NOT NULL trong schema, hien tai dang de NULL de ho tro user cu")
        
        conn.commit()
        print("[SUCCESS] Da them cot key vao bang users thanh cong!")
        
        # Kiểm tra lại
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"[INFO] Cac cot hien tai trong bang users: {', '.join(columns)}")
        
    except sqlite3.Error as e:
        print(f"[ERROR] Loi khi migrate: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("="*60)
    print("[INFO] Bat dau migrate database - them key vao users...")
    print("="*60)
    migrate_database()
    print("="*60)
    print("[SUCCESS] Hoan tat!")

