import sqlite3
import os
from datetime import datetime
import uuid

class PaymentManager:
    def __init__(self, db_path=None):
        if db_path is None:
            # Tìm đường dẫn đến payment.db trong thư mục instance
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(os.path.dirname(current_dir))
            db_path = os.path.join(backend_dir, 'instance', 'payment.db')

        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Đảm bảo database tồn tại"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file not found: {self.db_path}")

    def _get_connection(self):
        """Tạo kết nối database"""
        return sqlite3.connect(self.db_path)

    def get_user_by_api_key(self, api_key):
        """
        Lấy thông tin user theo API key
        Returns: dict với thông tin user hoặc None nếu không tìm thấy
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, email, credit, created_at, password_hash, key
                FROM users
                WHERE key = ?
            """, (api_key,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'id': row[0],
                    'email': row[1],
                    'credit': row[2],
                    'created_at': row[3],
                    'password_hash': row[4],
                    'key': row[5]
                }
            return None

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    def generate_api_key(self, user_id):
        """
        Tạo API key mới cho user
        Returns: API key string hoặc None nếu thất bại
        """
        try:
            # Tạo API key duy nhất
            api_key = str(uuid.uuid4())

            conn = self._get_connection()
            cursor = conn.cursor()

            # Cập nhật API key cho user
            cursor.execute("UPDATE users SET key = ? WHERE id = ?", (api_key, user_id))
            conn.commit()
            conn.close()

            print(f"Generated API key for user {user_id}: {api_key}")
            return api_key

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    def get_user_cost_per_request(self, user_id):
        """
        Lấy chi phí cho mỗi request của user từ config
        Returns: số credit cần trừ cho mỗi request
        """
        try:
            # Load cost trực tiếp từ quota_config.json
            import json
            import os

            # Tìm đường dẫn đến quota_config.json
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(os.path.dirname(current_dir))
            config_path = os.path.join(backend_dir, 'config', 'quota_config.json')

            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            return int(config.get('cost', 300))

        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not load cost from config ({e}), using default 300")
            return 300

    def add_credit(self, user_id, amount):
        """
        Thêm credit cho user
        Returns: True nếu thành công, False nếu thất bại
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Lấy credit hiện tại
            cursor.execute("SELECT credit FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()

            if not row:
                conn.close()
                return False

            # Cộng credit
            new_credit = row[0] + amount
            cursor.execute("UPDATE users SET credit = ? WHERE id = ?", (new_credit, user_id))
            conn.commit()
            conn.close()

            print(f"User {user_id} credit added: {amount}, total: {new_credit}")
            return True

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def check_user_credit(self, user_id, required_credit=1):
        """
        Kiểm tra user có đủ credit không
        Returns: True nếu đủ credit, False nếu không đủ
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT credit FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return row[0] >= required_credit
            return False

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def deduct_credit(self, user_id, amount=1):
        """
        Trừ credit của user
        Returns: True nếu thành công, False nếu thất bại
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Kiểm tra credit hiện tại
            cursor.execute("SELECT credit FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()

            if not row or row[0] < amount:
                conn.close()
                return False

            # Trừ credit
            new_credit = row[0] - amount
            cursor.execute("UPDATE users SET credit = ? WHERE id = ?", (new_credit, user_id))
            conn.commit()
            conn.close()

            print(f"User {user_id} credit deducted: {amount}, remaining: {new_credit}")
            return True

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def get_user_credit(self, user_id):
        """
        Lấy số credit hiện tại của user
        Returns: số credit hoặc None nếu lỗi
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT credit FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()

            return row[0] if row else None

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

# Instance global để sử dụng trong API
payment_manager = PaymentManager()
