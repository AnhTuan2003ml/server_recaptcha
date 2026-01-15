import sqlite3
import os

def read_payment_db():
    """
    Đọc và trả về nội dung của payment.db dưới dạng dictionary
    """
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'instance', 'payment.db')

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Không tìm thấy file payment.db tại: {db_path}")

    try:
        # Kết nối đến database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Lấy danh sách các bảng
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            return {"error": "Không có bảng nào trong database"}

        database_data = {
            "tables": {},
            "summary": {
                "total_users": 0,
                "total_sessions": 0,
                "total_transactions": 0,
                "total_otps": 0,
                "total_credit": 0,
                "database_size": len(tables)
            }
        }

        for table in tables:
            table_name = table[0]

            # Lấy cấu trúc bảng
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            # Lấy dữ liệu từ bảng
            cursor.execute(f"SELECT * FROM {table_name};")
            rows = cursor.fetchall()

            # Chuyển đổi dữ liệu thành dict
            table_data = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    row_dict[column_names[i]] = value
                table_data.append(row_dict)

            database_data["tables"][table_name] = {
                'columns': column_names,
                'data': table_data,
                'count': len(table_data)
            }

            # Tính tổng số records
            if table_name == 'users':
                database_data["summary"]["total_users"] = len(table_data)
                # Tính tổng credit
                database_data["summary"]["total_credit"] = sum(user['credit'] for user in table_data)
            elif table_name == 'sessions':
                database_data["summary"]["total_sessions"] = len(table_data)
            elif table_name == 'transactions':
                database_data["summary"]["total_transactions"] = len(table_data)
            elif table_name == 'otps':
                database_data["summary"]["total_otps"] = len(table_data)

        # Đóng kết nối
        conn.close()

        return database_data

    except sqlite3.Error as e:
        raise Exception(f"Lỗi SQLite: {e}")
    except Exception as e:
        raise Exception(f"Lỗi: {e}")

if __name__ == "__main__":
    read_payment_db()
