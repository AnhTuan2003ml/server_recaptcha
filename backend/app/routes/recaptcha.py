"""
API Routes - refactor & clean
- Giữ nguyên tất cả endpoints gốc
- Admin yêu cầu login trước khi vào /admin*
- Standalone: register blueprint với prefix /recaptcha
- Main app: register blueprint không prefix
"""
from __future__ import annotations

import time
import threading
from functools import wraps
from datetime import timedelta
from typing import Any, Dict, Tuple

from flask import (
    Blueprint,
    Flask,
    jsonify,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)

# ===== Imports nội bộ (giữ nguyên như code gốc) =====
from app.moduls.recaptcha_browser import get_captcha_token
from app.moduls.payment import payment_manager
from app.moduls.read_db import read_payment_db
from core.database_manager import update_database_record, add_database_record, delete_database_record
from core.admin_html import generate_embedded_admin_html


# =========================
# Helpers
# =========================
def _json_error(message: str, status: int = 400, **extra: Any):
    payload = {"success": False, "error": message}
    if extra:
        payload.update(extra)
    return jsonify(payload), status


def _bp_endpoint(name: str) -> str:
    """
    Tạo endpoint theo blueprint hiện tại.
    Tránh hardcode 'api.admin_login' gây BuildError khi chạy ở mode khác / trùng blueprint.
    """
    bp = request.blueprint or "api"
    return f"{bp}.{name}"


from functools import wraps
from flask import session, redirect, request

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("admin_logged_in"):
            return f(*args, **kwargs)

        # Nếu đang ở /recaptcha/... thì redirect về /recaptcha/login
        if request.path.startswith("/recaptcha/"):
            return redirect("/recaptcha/login?next=" + request.path)

        # Nếu chạy integrated (không prefix) thì về /login
        return redirect("/login?next=" + request.path)
    return decorated




# =========================
# Blueprint Factory (routes định nghĩa 1 lần)
# =========================
def create_api_blueprint() -> Blueprint:
    bp = Blueprint("api", __name__)

    # CORS (giữ behavior như code gốc)
    @bp.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    # -------------------------
    # Auth routes (giữ path gốc)
    # -------------------------
    @bp.route("/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")

            # TODO: đổi user/pass theo bạn
            if username == "admin" and password == "admin123@":
                session.permanent = True
                session["admin_logged_in"] = True
                # nếu có next thì quay lại, không thì về /admin (đúng path gốc)
                next_url = request.args.get("next") or url_for(_bp_endpoint("admin_page"))
                return redirect(next_url)

            return "Login failed", 401

        return render_template_string(
            """
            <!doctype html>
            <html>
            <head><meta charset="utf-8"><title>Admin Login</title></head>
            <body style="font-family:Arial;padding:24px">
              <h2>Admin Login</h2>
              <form method="post">
                <div><input name="username" placeholder="Username" autofocus></div><br>
                <div><input name="password" type="password" placeholder="Password"></div><br>
                <button type="submit">Login</button>
              </form>
            </body>
            </html>
            """
        )

    @bp.route("/logout", methods=["GET"])
    def admin_logout():
        session.clear()
        return redirect(url_for(_bp_endpoint("admin_login")))

    # -------------------------
    # API: get captcha token (giữ path gốc)
    # -------------------------
    @bp.route("/get_captcha_token", methods=["GET"])
    def get_captcha_token_api():
        """
        GET /get_captcha_token?apikey=...
        - Validate apikey
        - check credit (cost per request)
        - thử lấy token tối đa 50 lần, mỗi lần cách 0.5s
        - thành công thì deduct credit và trả token
        """
        api_key = request.args.get("apikey")
        if not api_key:
            return _json_error(
                "Missing API key",
                400,
                message="Vui lòng cung cấp apikey trong query parameter",
            )

        user = payment_manager.get_user_by_api_key(api_key)
        if not user:
            return _json_error("Invalid API key", 401, message="API key không hợp lệ")

        user_id = user["id"]
        cost_per_request = payment_manager.get_user_cost_per_request(user_id)

        if not payment_manager.check_user_credit(user_id, cost_per_request):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Insufficient credit",
                        "message": f"Không đủ credit để thực hiện yêu cầu này (cần {cost_per_request} credit)",
                        "current_credit": user.get("credit"),
                        "required_credit": cost_per_request,
                    }
                ),
                402,
            )

        max_attempts = 50
        wait_time = 0.5
        attempt = 0

        while attempt < max_attempts:
            attempt += 1

            # kiểm tra credit trước mỗi lần thử
            current_credit = payment_manager.get_user_credit(user_id)
            if not payment_manager.check_user_credit(user_id, cost_per_request):
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Insufficient credit",
                            "message": f"Không đủ credit để thực hiện yêu cầu này (cần {cost_per_request} credit)",
                            "current_credit": current_credit,
                            "required_credit": cost_per_request,
                            "attempts_made": attempt,
                        }
                    ),
                    402,
                )

            token = get_captcha_token()
            if token:
                token_length = len(token)

                # deduct credit (nếu fail vẫn trả token)
                payment_manager.deduct_credit(user_id, cost_per_request)
                new_credit = payment_manager.get_user_credit(user_id)

                return jsonify(
                    {
                        "success": True,
                        "captcha_token": token,
                        "message": f"Lấy Token thành công sau {attempt} lần thử (Dài {token_length} ký tự)",
                        "length": token_length,
                        "timestamp": int(time.time()),
                        "user_id": user_id,
                        "credit_deducted": cost_per_request,
                        "credit_remaining": new_credit,
                        "attempts_made": attempt,
                        "thread_id": threading.current_thread().ident,
                    }
                )

            if attempt < max_attempts:
                time.sleep(wait_time)

        return (
            jsonify(
                {
                    "success": False,
                    "error": "Không thể tạo captcha token sau nhiều lần thử",
                    "message": f"Token generation failed after {max_attempts} attempts",
                    "attempts_made": attempt,
                }
            ),
            503,
        )

    # -------------------------
    # API: info & db (giữ path gốc)
    # -------------------------
    @bp.route("/", methods=["GET"])
    def home():
        return jsonify(
            {
                "message": "AI Generation API with Parallel Processing",
                "version": "2.0",
                "features": [
                    "Parallel task processing",
                    "Batch image generation",
                    "Credit system integration",
                    "Real-time task monitoring",
                ],
                "endpoints": {
                    "get_captcha_token": "GET /get_captcha_token?apikey=YOUR_KEY",
                    "generate_images": "POST /generate_images",
                    "task_status": "GET /task/{task_id}",
                    "batch_status": "GET /batch/{batch_id}",
                    "queue_stats": "GET /queue/stats",
                    "read_database": "GET /read_database",
                    "update_database": "POST /update_database",
                    "add_database": "POST /add_database",
                    "delete_database": "POST /delete_database",
                    "admin_page": "GET /admin",
                    "login": "GET/POST /login",
                    "logout": "GET /logout",
                },
                "limits": {"max_batch_size": 10, "max_concurrent_tasks": 4},
            }
        )

    @bp.route("/read_database", methods=["GET"])
    def read_database():
        database_data = read_payment_db()
        if isinstance(database_data, dict) and "error" in database_data:
            return _json_error(database_data["error"], 500)
        return jsonify({"success": True, "database": database_data, "timestamp": int(time.time())})

    @bp.route("/update_database", methods=["POST"])
    def update_database():
        data = request.get_json(silent=True) or {}
        required = {"table", "id", "column", "value"}
        if not required.issubset(set(data.keys())):
            return _json_error("Missing required fields", 400)

        success, message = update_database_record(data["table"], data["id"], data["column"], data["value"])
        if success:
            return jsonify({"success": True, "message": message})
        return _json_error(message, 400)

    @bp.route("/add_database", methods=["POST"])
    def add_database():
        data = request.get_json(silent=True) or {}
        if "table" not in data or "data" not in data:
            return _json_error("Missing table or data", 400)
        if not isinstance(data["data"], dict) or not data["data"]:
            return _json_error("Invalid data format", 400)

        success, message, new_id = add_database_record(data["table"], data["data"])
        if success:
            return jsonify({"success": True, "message": message, "id": new_id})
        return _json_error(message, 400)

    @bp.route("/delete_database", methods=["POST"])
    def delete_database():
        data = request.get_json(silent=True) or {}
        if "table" not in data or "id" not in data:
            return _json_error("Missing table or id", 400)

        success, message = delete_database_record(data["table"], data["id"])
        if success:
            return jsonify({"success": True, "message": message})
        return _json_error(message, 400)

    # -------------------------
    # Admin pages & admin CRUD (giữ path gốc + bắt login)
    # -------------------------
    @bp.route("/admin", methods=["GET"])
    @login_required
    def admin_page():
        database_data = read_payment_db()
        if isinstance(database_data, dict) and "error" in database_data:
            return (
                f"""
                <!DOCTYPE html>
                <html><head><title>Admin - Error</title></head>
                <body>
                  <h1>LOI DATABASE</h1>
                  <p>{database_data['error']}</p>
                  <a href="/">Quay lai trang chu</a>
                </body></html>
                """,
                500,
            )

        return generate_embedded_admin_html(database_data)

    @bp.route("/admin/add", methods=["POST"])
    @login_required
    def admin_add_record():
        data = request.get_json(silent=True) or {}
        if "table_name" not in data:
            return _json_error("Missing table_name", 400)

        table_name = data["table_name"]
        row_data = {k: v for k, v in data.items() if k != "table_name"}

        success, message, new_id = add_database_record(table_name, row_data)
        if success:
            return jsonify({"success": True, "message": message, "new_id": new_id})
        return _json_error(message, 400)

    @bp.route("/admin/update", methods=["POST"])
    @login_required
    def admin_update_record():
        data = request.get_json(silent=True) or {}
        if "table_name" not in data or "record_id" not in data:
            return _json_error("Missing table_name or record_id", 400)

        table_name = data["table_name"]
        record_id = data["record_id"]
        update_data = {k: v for k, v in data.items() if k not in {"table_name", "record_id"}}

        if not update_data:
            return _json_error("No data to update", 400)

        errors = []
        for column, value in update_data.items():
            ok, msg = update_database_record(table_name, record_id, column, value)
            if not ok:
                errors.append(f"{column}: {msg}")

        if errors:
            return _json_error("Some updates failed: " + "; ".join(errors), 400)

        return jsonify({"success": True, "message": f"Record {record_id} updated successfully"})

    @bp.route("/admin/delete", methods=["POST"])
    @login_required
    def admin_delete_record():
        data = request.get_json(silent=True) or {}
        if "table_name" not in data or "record_id" not in data:
            return _json_error("Missing table_name or record_id", 400)

        success, message = delete_database_record(data["table_name"], data["record_id"])
        if success:
            return jsonify({"success": True, "message": message})
        return _json_error(message, 400)

    return bp


# Export blueprint cho main app import (giữ tên biến api_bp như cũ)
api_bp = create_api_blueprint()


# =========================
# Runner: integrated or standalone
# =========================
def run_recaptcha_server(port: int = 5000, host: str = "0.0.0.0"):
    """
    - port == 5000: chạy chung với main app (create_app)
    - port != 5000: standalone chạy riêng, register prefix /recaptcha
    """
    import sys

    if port == 5000:
        print("🚀 Running with main app on port 5000...")
        try:
            from app import create_app

            main_app = create_app()

            # NOTE: main_app PHẢI có secret_key để session hoạt động.
            # Bạn set trong create_app/config của dự án.
            main_app.register_blueprint(api_bp)  # không prefix

            print(f"📍 Available at: http://{host}:{port}")
            print(f"🔗 Get captcha token: http://{host}:{port}/get_captcha_token")
            print("💡 Captcha service is integrated with main app")
            main_app.run(debug=True, host=host, port=port)
        except ImportError as e:
            print(f"❌ Cannot import main app: {e}")
            print("💡 Make sure you're running from the backend directory")
            sys.exit(1)

    # Standalone
    print(f"🚀 Starting standalone Recaptcha API Server on port {port}...")
    standalone_app = Flask(__name__)
    standalone_app.secret_key = "CHANGE_THIS_SECRET_KEY_NOW"
    standalone_app.permanent_session_lifetime = timedelta(hours=2)

    @standalone_app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    # IMPORTANT: prefix /recaptcha (giữ y nguyên như hệ thống tunnel của bạn)
    standalone_app.register_blueprint(api_bp, url_prefix="/recaptcha")

    print(f"📍 Standalone server available at: http://{host}:{port}")
    print(f"🔗 Get token: http://{host}:{port}/recaptcha/get_captcha_token")
    print("💡 Admin: /recaptcha/admin (requires login at /recaptcha/login)")

    try:
        standalone_app.run(debug=True, host=host, port=port)
    except KeyboardInterrupt:
        print("\n👋 Standalone server shutting down...")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Recaptcha API Server")
    parser.add_argument("--port", type=int, default=5000, help="Port (default: 5000)")
    parser.add_argument("--host", default="127.0.0.1", help="Host (default: 127.0.0.1)")
    args = parser.parse_args()

    run_recaptcha_server(port=args.port, host=args.host)
