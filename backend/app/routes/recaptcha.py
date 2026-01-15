"""
API Routes - Chuyển từ api.py gốc
"""
from flask import Blueprint, jsonify, request
from app.moduls.recaptcha_browser import get_captcha_token
from app.moduls.payment import payment_manager
from app.moduls.read_db import read_payment_db
from core.database_manager import update_database_record, add_database_record, delete_database_record
from core.admin_html import generate_embedded_admin_html
from task_queue import task_queue, submit_image_generation_batch
import time
import threading

# Tạo blueprint để export khi import
api_bp = Blueprint('api', __name__)

api_bp = Blueprint('api', __name__)

# Enable CORS manually for API endpoints
@api_bp.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# ===== API ENDPOINTS =====

# ===== API ENDPOINTS =====

@api_bp.route('/get_captcha_token', methods=['GET'])
def get_captcha_token_api():
    """
    API endpoint để lấy captcha token trực tiếp từ recaptcha_browser.py
    Yêu cầu: apikey=<user_api_key>
    Mỗi lần thành công sẽ trừ credit tương ứng với chi phí của user (mặc định 1 credit)
    """
    try:
        # Lấy API key từ query parameter
        api_key = request.args.get('apikey')

        if not api_key:
            return jsonify({
                'success': False,
                'error': 'Missing API key',
                'message': 'Vui lòng cung cấp apikey trong query parameter'
            }), 400

        print(f"🔑 [API] Checking API key: {api_key}")

        # Kiểm tra user theo API key
        user = payment_manager.get_user_by_api_key(api_key)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid API key',
                'message': 'API key không hợp lệ'
            }), 401

        print(f"👤 [API] User found: {user['email']} (ID: {user['id']}, Credit: {user['credit']})")

        # Lấy chi phí cho mỗi request của user này
        cost_per_request = payment_manager.get_user_cost_per_request(user['id'])

        # Kiểm tra credit đủ để thực hiện
        if not payment_manager.check_user_credit(user['id'], cost_per_request):
            return jsonify({
                'success': False,
                'error': 'Insufficient credit',
                'message': f'Không đủ credit để thực hiện yêu cầu này (cần {cost_per_request} credit)',
                'current_credit': user['credit'],
                'required_credit': cost_per_request
            }), 402  # 402 Payment Required

        print(f"🚀 [API] Starting token generation (cost: {cost_per_request} credit) - Thread ID: {threading.current_thread().ident}")

        # Vòng lặp thử lại liên tục cho đến khi có token hoặc hết credit
        max_attempts = 50  # Giới hạn để tránh vòng lặp vô hạn
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            print(f"🔄 [API] Attempt #{attempt} - Thread ID: {threading.current_thread().ident}")

            # Kiểm tra lại credit trước mỗi lần thử (có thể user đã nạp thêm)
            current_credit = payment_manager.get_user_credit(user['id'])
            if not payment_manager.check_user_credit(user['id'], cost_per_request):
                print(f"💰 [API] User {user['email']} hết credit sau {attempt} lần thử")
                return jsonify({
                    'success': False,
                    'error': 'Insufficient credit',
                    'message': f'Không đủ credit để thực hiện yêu cầu này (cần {cost_per_request} credit)',
                    'current_credit': current_credit,
                    'required_credit': cost_per_request,
                    'attempts_made': attempt
                }), 402

            # Gọi hàm get_captcha_token từ recaptcha_browser.py
            token = get_captcha_token()

            if token:
                token_length = len(token)
                print(f"✅ [API] Token generated successfully after {attempt} attempts (Length: {token_length} characters)")

                # Trừ credit sau khi thành công
                credit_deducted = payment_manager.deduct_credit(user['id'], cost_per_request)
                if not credit_deducted:
                    print("⚠️ [API] Warning: Credit deduction failed")
                    # Vẫn trả về token nhưng ghi log warning

                # Lấy credit mới sau khi trừ
                new_credit = payment_manager.get_user_credit(user['id'])

                # Trả về token thành công
                return jsonify({
                    'success': True,
                    'captcha_token': token,
                    'message': f'Lấy Token thành công sau {attempt} lần thử (Dài {token_length} ký tự)',
                    'length': token_length,
                    'timestamp': int(time.time()),
                    'user_id': user['id'],
                    'credit_deducted': cost_per_request,
                    'credit_remaining': new_credit,
                    'attempts_made': attempt
                })

            # Nếu không có token, chờ một chút trước khi thử lại
            if attempt < max_attempts:
                wait_time = 0.5  # Chờ cố định 0.5s trước khi thử proxy key khác
                print(f"⏳ [API] Attempt #{attempt} failed, waiting {wait_time}s before retry...")
                time.sleep(wait_time)

        # Nếu vượt quá số lần thử tối đa
        print(f"❌ [API] Failed after {max_attempts} attempts, giving up")
        return jsonify({
            'success': False,
            'error': 'Không thể tạo captcha token sau nhiều lần thử',
            'message': f'Token generation failed after {max_attempts} attempts',
            'attempts_made': attempt
        }), 503

    except Exception as e:
        print(f"❌ [API] Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Lỗi: {str(e)}'
        }), 500

@api_bp.route('/generate_images', methods=['POST'])
def generate_images_batch():
    """
    API endpoint để tạo nhiều ảnh song song
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        user_id = data.get('user_id', 'anonymous')
        requests_list = data.get('requests', [])

        if not requests_list:
            return jsonify({
                'success': False,
                'error': 'No requests provided'
            }), 400

        if len(requests_list) > 10:  # Limit batch size
            return jsonify({
                'success': False,
                'error': 'Maximum 10 requests per batch'
            }), 400

        print(f"📦 [API] Received batch request with {len(requests_list)} items from user {user_id}")

        # Submit batch to queue
        batch_result = submit_image_generation_batch(user_id, requests_list)

        return jsonify({
            'success': True,
            'batch_id': batch_result['batch_id'],
            'task_ids': batch_result['task_ids'],
            'total_tasks': batch_result['total_tasks'],
            'estimated_completion_seconds': batch_result['estimated_completion'],
            'message': f'Submitted {len(requests_list)} image generation tasks',
            'check_status_url': f'/batch/{batch_result["batch_id"]}',
            'timestamp': int(time.time())
        })

    except Exception as e:
        print(f"❌ [API] Batch generation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    API endpoint để check status của một task
    """
    try:
        task_status = task_queue.get_task_status(task_id)

        if not task_status:
            return jsonify({
                'success': False,
                'error': 'Task not found'
            }), 404

        return jsonify({
            'success': True,
            'task': task_status
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/batch/<batch_id>', methods=['GET'])
def get_batch_status(batch_id):
    """
    API endpoint để check status của cả batch
    """
    try:
        batch_status = task_queue.get_batch_status(batch_id)

        if 'error' in batch_status:
            return jsonify({
                'success': False,
                'error': batch_status['error']
            }), 404

        return jsonify({
            'success': True,
            'batch': batch_status
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/queue/stats', methods=['GET'])
def get_queue_stats():
    """
    API endpoint để lấy thống kê queue
    """
    try:
        stats = task_queue.get_queue_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/', methods=['GET'])
def home():
    """
    Trang chủ API - trả về thông tin API
    """
    return jsonify({
        'message': 'AI Generation API with Parallel Processing',
        'version': '2.0',
        'features': [
            'Parallel task processing',
            'Batch image generation',
            'Credit system integration',
            'Real-time task monitoring'
        ],
        'endpoints': {
            'get_captcha_token': 'GET /get_captcha_token?apikey=YOUR_KEY - Lấy captcha token',
            'generate_images': 'POST /generate_images - Tạo nhiều ảnh song song',
            'task_status': 'GET /task/{task_id} - Check task status',
            'batch_status': 'GET /batch/{batch_id} - Check batch status',
            'queue_stats': 'GET /queue/stats - Queue statistics',
            'read_database': 'GET /read_database - Đọc dữ liệu database (JSON)',
            'update_database': 'POST /update_database - Cập nhật dữ liệu database',
            'add_database': 'POST /add_database - Thêm record mới vào database',
            'delete_database': 'POST /delete_database - Xóa record khỏi database',
            'admin_page': 'GET /admin - Giao diện admin dashboard (full CRUD)'
        },
        'limits': {
            'max_batch_size': 10,
            'max_concurrent_tasks': 4
        },
        'note': 'Hệ thống tự động cập nhật credit sau khi hoàn thành tasks thành công.'
    })

@api_bp.route('/read_database', methods=['GET'])
def read_database():
    """
    API endpoint để đọc dữ liệu database - trả về JSON
    """
    try:
        # Lấy dữ liệu database từ moduls/read_db.py
        database_data = read_payment_db()

        if "error" in database_data:
            return jsonify({
                'success': False,
                'error': database_data['error']
            }), 500

        return jsonify({
            'success': True,
            'database': database_data,
            'timestamp': int(time.time())
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Lỗi khi đọc database: {str(e)}'
        }), 500

@api_bp.route('/admin', methods=['GET'])
def admin_page():
    """
    Serve admin HTML page với data embedded
    """
    try:
        # Lấy dữ liệu database
        database_data = read_payment_db()

        if "error" in database_data:
            return f"""
            <!DOCTYPE html>
            <html>
            <head><title>Admin - Error</title></head>
            <body>
                <h1>LOI DATABASE</h1>
                <p>{database_data['error']}</p>
                <a href="/">Quay lai trang chu</a>
            </body>
            </html>
            """, 500

        # Tạo HTML với data embedded từ core module
        html = generate_embedded_admin_html(database_data)
        return html

    except Exception as e:
        import traceback
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Admin - Error</title></head>
        <body>
            <h1>LOI HE THONG</h1>
            <p>{str(e)}</p>
            <pre>{traceback.format_exc()}</pre>
            <a href="/">Quay lai trang chu</a>
        </body>
        </html>
        """, 500

@api_bp.route('/update_database', methods=['POST'])
def update_database():
    """
    API endpoint để cập nhật dữ liệu database
    """
    try:
        data = request.get_json()

        if not data or 'table' not in data or 'id' not in data or 'column' not in data or 'value' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        table_name = data['table']
        row_id = data['id']
        column = data['column']
        value = data['value']

        # Sử dụng function từ core module
        success, message = update_database_record(table_name, row_id, column, value)

        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400

    except Exception as e:
        print(f"API Update error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/add_database', methods=['POST'])
def add_database():
    """
    API endpoint để thêm record mới vào database
    """
    try:
        data = request.get_json()

        if not data or 'table' not in data or 'data' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing table or data'
            }), 400

        table_name = data['table']
        row_data = data['data']

        if not isinstance(row_data, dict) or not row_data:
            return jsonify({
                'success': False,
                'error': 'Invalid data format'
            }), 400

        # Sử dụng function từ core module
        success, message, new_id = add_database_record(table_name, row_data)

        if success:
            return jsonify({
                'success': True,
                'message': message,
                'id': new_id
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400

    except Exception as e:
        print(f"API Add error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/delete_database', methods=['POST'])
def delete_database():
    """
    API endpoint để xóa record khỏi database
    """
    try:
        data = request.get_json()

        if not data or 'table' not in data or 'id' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing table or id'
            }), 400

        table_name = data['table']
        row_id = data['id']

        # Sử dụng function từ core module
        success, message = delete_database_record(table_name, row_id)

        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400

    except Exception as e:
        print(f"API Delete error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/admin/add', methods=['POST'])
def admin_add_record():
    """
    Admin API endpoint to add new record to database
    """
    try:
        data = request.get_json()

        if not data or 'table_name' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing table_name'
            }), 400

        table_name = data['table_name']
        row_data = {k: v for k, v in data.items() if k != 'table_name'}

        success, message, new_id = add_database_record(table_name, row_data)

        if success:
            return jsonify({
                'success': True,
                'message': message,
                'new_id': new_id
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400

    except Exception as e:
        print(f"❌ Admin add error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/admin/update', methods=['POST'])
def admin_update_record():
    """
    Admin API endpoint to update database record
    """
    try:
        data = request.get_json()

        if not data or 'table_name' not in data or 'record_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing table_name or record_id'
            }), 400

        table_name = data['table_name']
        record_id = data['record_id']

        # Get all fields to update
        update_data = {k: v for k, v in data.items() if k not in ['table_name', 'record_id']}

        if not update_data:
            return jsonify({
                'success': False,
                'error': 'No data to update'
            }), 400

        # Update each field individually
        errors = []
        for column, value in update_data.items():
            success, message = update_database_record(table_name, record_id, column, value)
            if not success:
                errors.append(f"{column}: {message}")

        if errors:
            return jsonify({
                'success': False,
                'error': 'Some updates failed: ' + '; '.join(errors)
            }), 400

        return jsonify({
            'success': True,
            'message': f'Record {record_id} updated successfully'
        })

    except Exception as e:
        print(f"❌ Admin update error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/admin/delete', methods=['POST'])
def admin_delete_record():
    """
    Admin API endpoint to delete database record
    """
    try:
        data = request.get_json()

        if not data or 'table_name' not in data or 'record_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing table_name or record_id'
            }), 400

        table_name = data['table_name']
        record_id = data['record_id']

        success, message = delete_database_record(table_name, record_id)

        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400

    except Exception as e:
        print(f"❌ Admin delete error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Logic để chạy standalone hoặc chung với main app
def run_recaptcha_server(port=5000, host='0.0.0.0'):
    """Function để chạy recaptcha server với port tùy chỉnh"""
    import sys
    import os

    if port == 5000:
        # Chạy chung với main app - import main app và đăng ký recaptcha blueprint
        print("🚀 Running with main app on port 5000...")
        try:
            from app import create_app

            # Tạo main app
            main_app = create_app()

            # Đăng ký recaptcha blueprint vào main app
            main_app.register_blueprint(api_bp)  # API routes không cần prefix

            print(f"📍 Available at: http://{host}:{port}")
            print(f"🔗 Get captcha token: http://{host}:{port}/get_captcha_token")
            print("💡 Captcha service is integrated with main app")
            main_app.run(debug=True, host=host, port=port)
        except ImportError as e:
            print(f"❌ Cannot import main app: {e}")
            print("💡 Make sure you're running from the backend directory")
            sys.exit(1)
    else:
        # Tạo và chạy server riêng
        print(f"🚀 Starting standalone Recaptcha API Server on port {port}...")
        try:
            from flask import Flask, Blueprint, jsonify, request
            from flask_cors import CORS
            import time

            # Tạo Flask app riêng
            standalone_app = Flask(__name__)

            # Enable CORS
            @standalone_app.after_request
            def add_cors_headers(response):
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
                return response

            # Import các module cần thiết
            from app.moduls.recaptcha_browser import get_captcha_token
            from app.moduls.payment import payment_manager
            print("✅ All modules imported successfully")
        except ImportError as e:
            print(f"❌ Import error: {e}")
            print("💡 Make sure you're running from the backend directory")
            sys.exit(1)

        # Tạo blueprint và đăng ký routes
        standalone_api_bp = Blueprint('api', __name__)

        # Enable CORS manually for API endpoints
        @standalone_api_bp.after_request
        def add_cors_headers_blueprint(response):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response

        # Route: /get_captcha_token (simplified version)
        @standalone_api_bp.route('/get_captcha_token', methods=['GET'])
        def get_captcha_token_api():
            """API endpoint để lấy captcha token"""
            try:
                api_key = request.args.get('apikey')
                if not api_key:
                    return jsonify({'success': False, 'error': 'Missing API key'}), 400

                print(f"🔑 [API] Checking API key: {api_key}")
                user = payment_manager.get_user_by_api_key(api_key)
                if not user:
                    return jsonify({'success': False, 'error': 'Invalid API key'}), 401

                print(f"👤 [API] User found: {user['email']} (ID: {user['id']}, Credit: {user['credit']})")
                cost_per_request = payment_manager.get_user_cost_per_request(user['id'])

                if not payment_manager.check_user_credit(user['id'], cost_per_request):
                    return jsonify({
                        'success': False,
                        'error': 'Insufficient credit',
                        'current_credit': user['credit'],
                        'required_credit': cost_per_request
                    }), 402

                print(f"🚀 [API] Starting token generation (cost: {cost_per_request} credit)")
                max_attempts = 50
                attempt = 0

                while attempt < max_attempts:
                    attempt += 1
                    print(f"🔄 [API] Attempt #{attempt}")

                    current_credit = payment_manager.get_user_credit(user['id'])
                    if not payment_manager.check_user_credit(user['id'], cost_per_request):
                        return jsonify({
                            'success': False,
                            'error': 'Insufficient credit',
                            'current_credit': current_credit,
                            'required_credit': cost_per_request
                        }), 402

                    token = get_captcha_token()
                    if token:
                        token_length = len(token)
                        print(f"✅ [API] Token generated successfully after {attempt} attempts")

                        credit_deducted = payment_manager.deduct_credit(user['id'], cost_per_request)
                        new_credit = payment_manager.get_user_credit(user['id'])

                        return jsonify({
                            'success': True,
                            'captcha_token': token,
                            'message': f'Lấy Token thành công sau {attempt} lần thử',
                            'length': token_length,
                            'timestamp': int(time.time()),
                            'user_id': user['id'],
                            'credit_deducted': cost_per_request,
                            'credit_remaining': new_credit,
                            'attempts_made': attempt
                        })

                    if attempt < max_attempts:
                        wait_time = 0.5
                        print(f"⏳ [API] Attempt #{attempt} failed, waiting {wait_time}s before retry...")
                        time.sleep(wait_time)

                print(f"❌ [API] Failed after {max_attempts} attempts")
                return jsonify({
                    'success': False,
                    'error': 'Token generation failed',
                    'attempts_made': attempt
                }), 503

            except Exception as e:
                print(f"❌ [API] Error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        # Route: /
        @standalone_api_bp.route('/', methods=['GET'])
        def home():
            return jsonify({
                'message': 'Recaptcha API Server (Standalone)',
                'version': '1.0',
                'endpoints': {
                    'get_captcha_token': 'GET /get_captcha_token?apikey=YOUR_KEY',
                    'admin_page': 'GET /admin - Admin dashboard'
                }
            })

        # Route: /admin (Standalone version)
        @standalone_api_bp.route('/admin', methods=['GET'])
        def admin_page():
            """
            Serve admin HTML page với data embedded (Standalone version)
            """
            try:
                # Import các module cần thiết
                from app.moduls.read_db import read_payment_db
                from core.admin_html import generate_embedded_admin_html

                # Lấy dữ liệu database
                database_data = read_payment_db()

                if "error" in database_data:
                    return f"""
                    <!DOCTYPE html>
                    <html>
                    <head><title>Admin - Error</title></head>
                    <body>
                        <h1>LOI DATABASE</h1>
                        <p>{database_data['error']}</p>
                        <a href="/">Quay lai trang chu</a>
                    </body>
                    </html>
                    """, 500

                # Tạo HTML với data embedded từ core module
                html = generate_embedded_admin_html(database_data)
                return html

            except Exception as e:
                import traceback
                return f"""
                <!DOCTYPE html>
                <html>
                <head><title>Admin - Error</title></head>
                <body>
                    <h1>LOI HE THONG</h1>
                    <p>{str(e)}</p>
                    <pre>{traceback.format_exc()}</pre>
                    <a href="/">Quay lai trang chu</a>
                </body>
                </html>
                """, 500

        # Admin CRUD routes for standalone service
        @standalone_api_bp.route('/admin/add', methods=['POST'])
        def admin_add_record():
            """Standalone admin API endpoint to add new record"""
            try:
                data = request.get_json()
                if not data or 'table_name' not in data:
                    return jsonify({'success': False, 'error': 'Missing table_name'}), 400

                table_name = data['table_name']
                insert_data = {k: v for k, v in data.items() if k != 'table_name'}

                from core.database_manager import add_database_record
                success, message, new_id = add_database_record(table_name, insert_data)

                if success:
                    return jsonify({'success': True, 'message': message, 'new_id': new_id})
                else:
                    return jsonify({'success': False, 'error': message}), 400
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        @standalone_api_bp.route('/admin/update', methods=['POST'])
        def admin_update_record():
            """Standalone admin API endpoint to update record"""
            try:
                data = request.get_json()
                if not data or 'table_name' not in data or 'record_id' not in data:
                    return jsonify({'success': False, 'error': 'Missing table_name or record_id'}), 400

                table_name = data['table_name']
                record_id = data['record_id']
                update_data = {k: v for k, v in data.items() if k not in ['table_name', 'record_id']}

                if not update_data:
                    return jsonify({'success': False, 'error': 'No data to update'}), 400

                # Import function from database_manager
                from core.database_manager import update_database_record

                # Update each field individually
                errors = []
                for column, value in update_data.items():
                    success, message = update_database_record(table_name, record_id, column, value)
                    if not success:
                        errors.append(f"{column}: {message}")

                if errors:
                    return jsonify({'success': False, 'error': 'Some updates failed: ' + '; '.join(errors)}), 400

                return jsonify({'success': True, 'message': f'Record {record_id} updated successfully'})
            except Exception as e:
                print(f"❌ Admin update error: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @standalone_api_bp.route('/admin/delete', methods=['POST'])
        def admin_delete_record():
            """Standalone admin API endpoint to delete record"""
            try:
                data = request.get_json()
                if not data or 'table_name' not in data or 'record_id' not in data:
                    return jsonify({'success': False, 'error': 'Missing table_name or record_id'}), 400

                table_name = data['table_name']
                record_id = data['record_id']

                from core.database_manager import delete_database_record
                success, message = delete_database_record(table_name, record_id)

                if success:
                    return jsonify({'success': True, 'message': message})
                else:
                    return jsonify({'success': False, 'error': message}), 400
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        # Đăng ký blueprint với prefix /recaptcha để match với tunnel routing
        standalone_app.register_blueprint(standalone_api_bp, url_prefix='/recaptcha')

        print(f"📍 Standalone server available at: http://{host}:{port}")
        print(f"🔗 Get token: http://{host}:{port}/get_captcha_token")
        print("⚠️  Note: Token generation may take 1-2 minutes")
        print(f"💡 If port {port} is busy, try different port")

        try:
            standalone_app.run(debug=True, host=host, port=port)
        except KeyboardInterrupt:
            print("\n👋 Standalone server shutting down...")
        except Exception as e:
            print(f"❌ Error starting standalone server: {e}")
            if "Address already in use" in str(e):
                print(f"💡 Port {port} is already in use. Try different port")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Recaptcha API Server')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to run the server on (default: 5000)')
    parser.add_argument('--host', default='127.0.0.1',
                       help='Host to bind to (default: 127.0.0.1)')

    args = parser.parse_args()
    run_recaptcha_server(port=args.port, host=args.host)
