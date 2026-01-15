"""
Script để xem nội dung database
Sử dụng: python scripts/view_database.py
"""
import sqlite3
import os
from datetime import datetime

def view_database():
    # Đường dẫn database: từ scripts/ -> ../instance/payment.db
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'payment.db')
    db_path = os.path.abspath(db_path)
    
    if not os.path.exists(db_path):
        print(f"[ERROR] Database khong ton tai tai: {db_path}")
        return
    
    print("="*80)
    print("DATABASE VIEWER")
    print("="*80)
    print(f"Database: {db_path}")
    print("="*80)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Để có thể truy cập bằng tên cột
    cursor = conn.cursor()
    
    try:
        # Lấy danh sách các bảng
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n[INFO] Co {len(tables)} bang trong database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Xem từng bảng
        for table_name in [t[0] for t in tables]:
            print("\n" + "="*80)
            print(f"BANG: {table_name.upper()}")
            print("="*80)
            
            # Lấy cấu trúc bảng
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("\nCau truc:")
            print("-" * 80)
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = "NOT NULL" if col[3] else "NULL"
                default = f" DEFAULT {col[4]}" if col[4] else ""
                pk = " PRIMARY KEY" if col[5] else ""
                print(f"  {col_name:20} {col_type:15} {not_null:10}{default}{pk}")
            
            # Đếm số dòng
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"\nSo dong: {count}")
            
            # Hiển thị dữ liệu
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                print("\nDu lieu:")
                print("-" * 80)
                
                # In header
                col_names = [col[1] for col in columns]
                header = " | ".join(f"{name:20}" for name in col_names)
                print(header)
                print("-" * 80)
                
                # In dữ liệu
                for row in rows:
                    values = []
                    for i, col in enumerate(columns):
                        value = row[i]
                        if value is None:
                            value = "NULL"
                        elif isinstance(value, (int, float)):
                            value = str(value)
                        elif isinstance(value, str):
                            # Giới hạn độ dài string
                            if len(value) > 30:
                                value = value[:27] + "..."
                            value = value.replace("\n", "\\n")
                        else:
                            value = str(value)
                        values.append(f"{value:20}")
                    print(" | ".join(values))
            else:
                print("\n[INFO] Bang trong (khong co du lieu)")
        
        print("\n" + "="*80)
        
    except sqlite3.Error as e:
        print(f"[ERROR] Loi khi doc database: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    view_database()


