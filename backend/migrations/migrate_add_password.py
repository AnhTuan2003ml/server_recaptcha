"""
Script để migrate database - thêm cột password_hash vào bảng users
Chạy script này một lần để cập nhật database
"""
import sqlite3
import os
import sys

# Set UTF-8 encoding cho Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

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
        # Kiểm tra xem cột password_hash đã tồn tại chưa
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'password_hash' in columns:
            print("[SUCCESS] Cot password_hash da ton tai, khong can migrate")
            return
        
        print("[INFO] Dang them cot password_hash vao bang users...")
        
        # Thêm cột password_hash (nullable để hỗ trợ user cũ)
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN password_hash VARCHAR(255) NULL
        """)
        
        conn.commit()
        print("[SUCCESS] Da them cot password_hash thanh cong!")
        
        # Kiểm tra lại
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"[INFO] Cac cot hien tai: {', '.join(columns)}")
        
    except sqlite3.Error as e:
        print(f"[ERROR] Loi khi migrate: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("="*60)
    print("[INFO] Bat dau migrate database...")
    print("="*60)
    migrate_database()
    print("="*60)
    print("[SUCCESS] Hoan tat!")


