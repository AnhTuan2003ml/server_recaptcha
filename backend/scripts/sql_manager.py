"""
SQL Manager - Công cụ quản lý database bằng SQL commands
Sử dụng: python scripts/sql_manager.py
"""
import sqlite3
import os
import sys
from datetime import datetime

def print_help():
    print("\n" + "="*80)
    print("SQL MANAGER - QUAN LY DATABASE")
    print("="*80)
    print("\nCac lenh co ban:")
    print("  .help          - Hien thi help nay")
    print("  .tables        - Liet ke tat ca cac bang")
    print("  .schema [table]- Hien thi cau truc bang (neu khong co table thi hien thi tat ca)")
    print("  .count [table] - Dem so dong trong bang")
    print("  .clear         - Xoa man hinh")
    print("  .exit / .quit  - Thoat")
    print("\nCac lenh SQL:")
    print("  SELECT * FROM users;")
    print("  INSERT INTO users (email, password_hash) VALUES ('test@test.com', 'hash');")
    print("  UPDATE users SET credit = 1000 WHERE id = 1;")
    print("  DELETE FROM users WHERE id = 1;")
    print("\nLuu y:")
    print("  - Moi lenh SQL phai ket thuc bang dau cham phay (;)")
    print("  - Co the nhap nhieu dong, ket thuc bang ;")
    print("  - Lenh bat dau bang dau cham (.) la lenh dac biet")
    print("="*80 + "\n")

def execute_sql(cursor, sql, show_result=True):
    """Thực thi SQL và hiển thị kết quả"""
    try:
        cursor.execute(sql)
        
        # Kiểm tra xem có kết quả trả về không (SELECT)
        if cursor.description:
            # Có kết quả - SELECT query
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            if show_result:
                if len(rows) == 0:
                    print("[INFO] Khong co ket qua")
                else:
                    # In header
                    print("\n" + "-"*80)
                    header = " | ".join(f"{col:20}" for col in columns)
                    print(header)
                    print("-"*80)
                    
                    # In dữ liệu
                    for row in rows:
                        values = []
                        for i, value in enumerate(row):
                            if value is None:
                                value = "NULL"
                            elif isinstance(value, (int, float)):
                                value = str(value)
                            elif isinstance(value, str):
                                if len(value) > 30:
                                    value = value[:27] + "..."
                                value = value.replace("\n", "\\n")
                            else:
                                value = str(value)
                            values.append(f"{value:20}")
                        print(" | ".join(values))
                    print("-"*80)
                    print(f"[INFO] Co {len(rows)} dong")
            
            return rows
        else:
            # Không có kết quả - INSERT, UPDATE, DELETE, etc.
            affected = cursor.rowcount
            if show_result:
                print(f"[SUCCESS] Thanh cong! {affected} dong bi anh huong")
            return affected
            
    except sqlite3.Error as e:
        print(f"[ERROR] Loi SQL: {e}")
        return None

def handle_special_command(cursor, conn, command):
    """Xử lý các lệnh đặc biệt bắt đầu bằng dấu chấm"""
    cmd = command.strip().lower()
    
    if cmd == ".help":
        print_help()
        return True
    
    elif cmd == ".tables":
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("\nCac bang trong database:")
        for table in tables:
            print(f"  - {table[0]}")
        return True
    
    elif cmd.startswith(".schema"):
        parts = cmd.split()
        if len(parts) > 1:
            # Schema của một bảng cụ thể
            table_name = parts[1]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"\nCau truc bang {table_name}:")
            print("-"*80)
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = "NOT NULL" if col[3] else "NULL"
                default = f" DEFAULT {col[4]}" if col[4] else ""
                pk = " PRIMARY KEY" if col[5] else ""
                print(f"  {col_name:20} {col_type:15} {not_null:10}{default}{pk}")
        else:
            # Schema của tất cả các bảng
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                print(f"\nCau truc bang {table_name}:")
                print("-"*80)
                for col in columns:
                    col_name = col[1]
                    col_type = col[2]
                    not_null = "NOT NULL" if col[3] else "NULL"
                    default = f" DEFAULT {col[4]}" if col[4] else ""
                    pk = " PRIMARY KEY" if col[5] else ""
                    print(f"  {col_name:20} {col_type:15} {not_null:10}{default}{pk}")
        return True
    
    elif cmd.startswith(".count"):
        parts = cmd.split()
        if len(parts) > 1:
            table_name = parts[1]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"\nSo dong trong bang {table_name}: {count}")
        else:
            # Đếm tất cả các bảng
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print("\nSo dong trong cac bang:")
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  {table_name:20} : {count}")
        return True
    
    elif cmd == ".clear":
        os.system('cls' if os.name == 'nt' else 'clear')
        return True
    
    elif cmd in [".exit", ".quit"]:
        return False
    
    else:
        print(f"[ERROR] Lenh khong hop le: {command}")
        print("Nhap .help de xem cac lenh co ban")
        return True

def main():
    # Đường dẫn database: từ scripts/ -> ../instance/payment.db
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'payment.db')
    db_path = os.path.abspath(db_path)
    
    if not os.path.exists(db_path):
        print(f"[ERROR] Database khong ton tai tai: {db_path}")
        return
    
    print("="*80)
    print("SQL MANAGER - QUAN LY DATABASE")
    print("="*80)
    print(f"Database: {db_path}")
    print("Nhap .help de xem huong dan")
    print("="*80)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    sql_buffer = []
    
    try:
        while True:
            try:
                # Nhập lệnh
                if sql_buffer:
                    prompt = "... "
                else:
                    prompt = "sql> "
                
                line = input(prompt).strip()
                
                if not line:
                    continue
                
                # Kiểm tra lệnh đặc biệt
                if line.startswith("."):
                    if not handle_special_command(cursor, conn, line):
                        break
                    continue
                
                # Thêm vào buffer
                sql_buffer.append(line)
                
                # Kiểm tra xem có kết thúc bằng ; không
                if line.endswith(";"):
                    # Ghép các dòng lại thành một câu SQL
                    sql = " ".join(sql_buffer)
                    sql_buffer = []
                    
                    # Thực thi
                    execute_sql(cursor, sql)
                    
                    # Commit nếu là lệnh thay đổi dữ liệu
                    if sql.strip().upper().startswith(("INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER")):
                        conn.commit()
                        print("[INFO] Da commit thay doi")
                
            except KeyboardInterrupt:
                print("\n[INFO] Nhan Ctrl+C de thoat")
                sql_buffer = []
            except EOFError:
                print("\n[INFO] Thoat...")
                break
            except Exception as e:
                print(f"[ERROR] Loi: {e}")
                sql_buffer = []
    
    finally:
        conn.close()
        print("\n[INFO] Da dong ket noi database")

if __name__ == '__main__':
    main()


