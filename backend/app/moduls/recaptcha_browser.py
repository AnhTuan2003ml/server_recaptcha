# File: recaptcha_browser.py
import json
import os
import time
import random
import threading
import requests
from playwright.sync_api import sync_playwright
from .get_proxy import get_proxy_from_api

# --- CẤU HÌNH ---
# Dùng đường dẫn tương đối để đảm bảo chạy từ main.py vẫn tìm thấy
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COOKIES_PATH = os.path.join(BASE_DIR, "_internal", "config", "cookies.json")
SITE_KEY = "6LdsFiUsAAAAAIjVDZcuLhaHiDn5nnHVXVRQGeMV"
TARGET_URL = "https://labs.google/fx/tools/flow" # Hoặc image-fx tuỳ nhu cầu

# Global proxy rotation state - thread-safe
_proxy_rotation_index = 0
_proxy_keys_cache = []
_proxy_lock = threading.Lock()
# Thread-local storage for proxy assignment
_thread_local = threading.local()

def get_proxy_api_keys():
    """Đọc danh sách proxy API keys từ file proxy.txt (mỗi dòng một key)"""
    global _proxy_keys_cache
    try:
        proxy_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "proxy.txt")
        with open(proxy_file, 'r', encoding='utf-8') as f:
            proxy_keys = [line.strip() for line in f.readlines() if line.strip()]
            if proxy_keys:
                _proxy_keys_cache = proxy_keys
                return proxy_keys
            else:
                print("⚠️ [PROXY] File proxy.txt rỗng")
                _proxy_keys_cache = []
                return []
    except FileNotFoundError:
        print("⚠️ [PROXY] File proxy.txt không tồn tại")
        _proxy_keys_cache = []
        return []
    except Exception as e:
        print(f"⚠️ [PROXY] Lỗi đọc file proxy.txt: {e}")
        _proxy_keys_cache = []
        return []

def get_next_proxy_key():
    """Lấy proxy key riêng cho từng thread - đảm bảo không bị trùng"""
    global _proxy_rotation_index, _proxy_keys_cache

    thread_id = threading.current_thread().ident

    with _proxy_lock:
        if not _proxy_keys_cache:
            # Re-read file if cache empty
            get_proxy_api_keys()
            if not _proxy_keys_cache:
                return None

        # Mỗi thread có proxy key riêng - assign một lần duy nhất
        if not hasattr(_thread_local, 'assigned_proxy'):
            # Assign proxy key cho thread này (có thể trùng nếu hết proxy keys)
            proxy_key = _proxy_keys_cache[_proxy_rotation_index]
            _thread_local.assigned_proxy = proxy_key
            _proxy_rotation_index = (_proxy_rotation_index + 1) % len(_proxy_keys_cache)

            print(f"[PROXY] Thread {thread_id} assigned proxy key: {proxy_key[:20]}... (index {_proxy_rotation_index-1})")
        else:
            proxy_key = _thread_local.assigned_proxy
            # Chỉ log khi thread gọi lần đầu, không log các lần sau để tránh spam

        return proxy_key

def load_project_cookies():
    if not os.path.exists(COOKIES_PATH):
        # Thử tìm ở thư mục cha nếu chạy từ thư mục con
        parent_path = os.path.join(BASE_DIR, "_internal", "config", "cookies.json")
        if os.path.exists(parent_path):
            with open(parent_path, 'r', encoding='utf-8') as f: return _parse_cookies(json.load(f))
        return []
    
    try:
        with open(COOKIES_PATH, 'r', encoding='utf-8') as f:
            return _parse_cookies(json.load(f))
    except: return []

def _parse_cookies(data):
    """Hàm phụ trợ để parse cookies"""
    cookies = []
    for name, info in data.items():
        if isinstance(info, dict):
            c = {
                "name": name, 
                "value": info.get("value"), 
                "domain": info.get("domain"), 
                "path": info.get("path", "/"), 
                "secure": info.get("secure", True)
            }
            if "expiry" in info: c["expires"] = info["expiry"]
            cookies.append(c)
    return cookies

def human_interaction(page):
    """Giả lập hành vi người thật - random movements và cuộn"""
    # Đợi ngắn như người dùng đang quan sát nhanh
    time.sleep(random.uniform(0.3, 0.8))
    # Random movements trong vùng chân browser
    movements = 6  # Tăng số lần di chuyển

    for _ in range(movements):
        # Random position trong vùng chân browser (800-1280 x 500-720)
        target_x = random.randint(800, 1280)
        target_y = random.randint(500, 720)

        # Đảm bảo trong viewport
        target_x = max(0, min(target_x, 1280))
        target_y = max(0, min(target_y, 720))

        # Random steps (8-15) và speed (0.15-0.4s)
        steps = random.randint(8, 15)
        delay = random.uniform(0.15, 0.4)

        page.mouse.move(target_x, target_y, steps=steps)
        time.sleep(delay)

    # Hành vi cuộn giống người: cuộn nhiều lần với pattern tự nhiên
    scroll_patterns = [
        (0, 300),   # Cuộn xuống sâu
        (0, 200),   # Cuộn thêm
        (0, -50),   # Cuộn lên chút (như đọc lại)
        (0, 400),   # Cuộn sâu hơn
        (0, 250),   # Cuộn thêm nữa
    ]

    for scroll_x, scroll_y in scroll_patterns:
        page.mouse.wheel(scroll_x, scroll_y)
        # Thời gian dừng giữa các lần cuộn (như người đọc)
        if scroll_y > 0:  # Cuộn xuống
            time.sleep(random.uniform(0.8, 1.5))
        else:  # Cuộn lên
            time.sleep(random.uniform(0.5, 1.0))

    # Click với hesitation (do dự như người thật)
    time.sleep(random.uniform(0.3, 0.7))

    try:
        # Click random trong vùng chân browser
        click_x = random.randint(900, 1280)
        click_y = random.randint(550, 720)
        click_x = max(0, min(click_x, 1280))
        click_y = max(0, min(click_y, 720))
        page.click("body", position={"x": click_x, "y": click_y})
    except:
        pass

    # Thêm hesitation cuối cùng
    time.sleep(random.uniform(0.2, 0.5))

# Không còn dùng global browser instance - mỗi request tạo browser riêng

def get_proxy_from_api_with_retry(api_key: str) -> str:
    """
    Lấy proxy từ API với đầy đủ retry logic bao gồm /current endpoint
    """
    return get_proxy_from_api(api_key)

def _parse_proxy_string(proxy_string: str) -> dict:
    """Parse proxy string thành dict cho Playwright"""
    if not proxy_string:
        return {}

    try:
        # Loại bỏ protocol (http://)
        if proxy_string.startswith('http://'):
            proxy_string = proxy_string[7:]

        # Tách username:password@server:port hoặc server:port
        if '@' in proxy_string:
            auth_part, server_part = proxy_string.split('@', 1)
            username, password = auth_part.split(':', 1)
        else:
            server_part = proxy_string
            username = password = None

        server, port = server_part.split(':', 1)

        proxy_config = {
            'server': f'http://{server}:{port}'
        }

        if username and password:
            proxy_config['username'] = username
            proxy_config['password'] = password

        return proxy_config

    except Exception as e:
        print(f"⚠️ [BROWSER] Lỗi parse proxy string: {e}")
        return {}

def create_browser_instance():
    """
    Tạo browser instance mới cho mỗi request.
    Mỗi request có proxy riêng biệt, thread-safe.
    Trả về: tuple (page, playwright, browser, context, creation_time)
    """
    print("🚀 [BROWSER] Tạo browser instance mới cho request...")

    try:
        from playwright.sync_api import sync_playwright

        # Lấy proxy riêng cho request này - thử tất cả proxy keys cho đến khi tìm được proxy hoạt động
        proxy_string = None
        proxy_keys = get_proxy_api_keys()  # Lấy tất cả proxy keys

        if not proxy_keys:
            print("❌ [BROWSER] Không có proxy keys để thử")
            return None, None, None, None, None

        print(f"[BROWSER] Co {len(proxy_keys)} proxy keys, thu lan luot cho den khi tim duoc proxy...")

        # Thử từng proxy key cho đến khi tìm được proxy hoạt động
        for i, proxy_key in enumerate(proxy_keys):
            print(f"[BROWSER] Thu proxy key #{i+1}/{len(proxy_keys)}: {proxy_key[:20]}...")
            proxy_string = get_proxy_from_api_with_retry(proxy_key)

            if proxy_string:
                print(f"[BROWSER] Proxy key #{i+1} thanh cong!")
                break
            else:
                print(f"[BROWSER] Proxy key #{i+1} fail, thu proxy tiep theo...")

        if not proxy_string:
            print("❌ [BROWSER] Tất cả proxy keys đều fail")
            return None, None, None, None, None

        proxy_config = {}
        if proxy_string:
            proxy_config = _parse_proxy_string(proxy_string)
            if proxy_config:
                print(f"✅ [BROWSER] Sử dụng proxy: {proxy_config['server']}")
            else:
                print("⚠️ [BROWSER] Không thể parse proxy")
        else:
            print("⚠️ [BROWSER] Không lấy được proxy từ API")

        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=False,  # Để False cho Google tin tưởng
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            proxy=proxy_config if proxy_config else None
        )

        cookies = load_project_cookies()
        if cookies: context.add_cookies(cookies)

        page = context.new_page()

        # Navigate to target URL với error handling
        try:
            page.goto(TARGET_URL, timeout=30000)  # Giảm timeout xuống 30s
            page.wait_for_timeout(1000)  # Giảm wait time

            # Kiểm tra xem page có load được không
            title = page.title()
            if "ERR_PROXY_CONNECTION_FAILED" in title or "No internet" in title or "proxy server" in title.lower():
                print("❌ [BROWSER] Proxy connection failed detected in page title")
                cleanup_browser_instance(playwright, browser, context, page)
                return None, None, None, None, None

            human_interaction(page)

            # Đợi ReCAPTCHA load với timeout
            page.wait_for_function("() => window.grecaptcha && window.grecaptcha.enterprise", timeout=15000)

        except Exception as nav_error:
            error_msg = str(nav_error)
            print(f"❌ [BROWSER] Navigation failed: {error_msg}")

            # Check for proxy-related errors
            if any(keyword in error_msg.lower() for keyword in ["proxy", "connection", "timeout", "network", "err_"]):
                print("🌐 [BROWSER] Proxy/network error detected - force cleanup")
                cleanup_browser_instance(playwright, browser, context, page)
                return None, None, None, None, None
            else:
                # Re-raise other errors
                raise nav_error

        creation_time = time.time()
        print(f"✅ [BROWSER] Browser instance mới đã sẵn sàng! (ID: {creation_time})")

        # Trả về tuple (page, playwright, browser, context, creation_time)
        return page, playwright, browser, context, creation_time

    except Exception as e:
        print(f"❌ [BROWSER] Lỗi tạo browser instance: {e}")
        return None, None, None, None, None

def cleanup_browser_instance(playwright, browser, context, page):
    """Cleanup browser instance sau khi sử dụng"""
    try:
        if page: page.close()
        if context: context.close()
        if browser: browser.close()
        if playwright: playwright.stop()

        # Thread-local cleanup (proxy indices are maintained per thread)
        print("🧹 [BROWSER] Browser instance đã được cleanup")
    except Exception as e:
        print(f"⚠️ [BROWSER] Lỗi cleanup browser: {e}")

def get_captcha_token():
    """
    Hàm chính để gọi từ bên ngoài.
    Tạo browser instance riêng cho mỗi request với timeout 30s.
    Mỗi request hoàn toàn độc lập - browser instance, proxy riêng.
    Trả về: Chuỗi Token (String) hoặc None nếu lỗi.
    """
    thread_id = threading.current_thread().ident
    print(f"🔄 [BROWSER] Thread {thread_id}: Tạo browser instance và lấy Token...")

    # Tạo browser instance mới cho request này
    # Không retry browser creation nữa vì proxy rotation đã handle
    page, playwright, browser, context, creation_time = create_browser_instance()

    if not page:
        print("❌ [BROWSER] Không thể tạo browser instance (tất cả proxy keys fail)")
        return None

    try:
        # Kiểm tra thời gian tồn tại trước khi thực thi
        elapsed_time = time.time() - creation_time
        if elapsed_time > 20:  # Giảm từ 30s xuống 20s
            print(f"⏰ [BROWSER] Browser đã tồn tại {elapsed_time:.1f}s > 20s, force cleanup")
            return None

        print(f"⏱️ [BROWSER] Browser age: {elapsed_time:.1f}s, proceeding...")

        # Thực thi lấy token với retry logic cho connection errors
        max_retries = 2
        for attempt in range(max_retries):
            try:
                token = page.evaluate(f"""
                    async () => {{
                        return await window.grecaptcha.enterprise.execute('{SITE_KEY}', {{action: 'FLOW_GENERATION'}})
                    }}
                """)

                # Kiểm tra lại thời gian sau khi thực thi
                total_elapsed = time.time() - creation_time
                if total_elapsed > 20:
                    print(f"⏰ [BROWSER] Browser đã tồn tại {total_elapsed:.1f}s > 20s trong quá trình thực thi, discarding token")
                    return None

                if token:
                    print(f"✅ [BROWSER] Lấy Token thành công (Dài {len(token)} ký tự, Browser age: {total_elapsed:.1f}s)")
                    return token
                else:
                    print("⚠️ [BROWSER] Không nhận được token")
                    return None

            except Exception as eval_error:
                error_msg = str(eval_error)
                if any(keyword in error_msg.lower() for keyword in ["connection", "closed", "proxy", "network", "timeout"]):
                    if attempt < max_retries - 1:
                        print(f"🔄 [BROWSER] Connection/proxy error (attempt {attempt + 1}/{max_retries}), reloading page...")
                        try:
                            # Thử reload page
                            page.reload(timeout=8000)
                            page.wait_for_function("() => window.grecaptcha && window.grecaptcha.enterprise", timeout=8000)
                            # Thực hiện lại human interaction nhẹ
                            time.sleep(random.uniform(0.2, 0.5))
                            for _ in range(2):
                                x = random.randint(900, 1200)
                                y = random.randint(600, 720)
                                page.mouse.move(x, y, steps=5)
                                time.sleep(random.uniform(0.1, 0.2))
                            continue
                        except Exception as reload_error:
                            reload_msg = str(reload_error)
                            print(f"⚠️ [BROWSER] Reload failed: {reload_msg}")
                            # Nếu reload cũng fail vì proxy, thì đây là proxy bad
                            if any(keyword in reload_msg.lower() for keyword in ["proxy", "connection", "network"]):
                                print("🌐 [BROWSER] Proxy appears to be bad, will try different proxy on next browser creation")
                                return None  # Force new browser creation with different proxy
                            continue
                    else:
                        print(f"❌ [BROWSER] Connection errors persisted after {max_retries} attempts")
                        return None
                else:
                    # Không phải connection error, raise lại
                    raise eval_error

    except Exception as e:
        error_time = time.time() - creation_time
        error_msg = str(e)
        print(f"⚠️ [BROWSER] Lỗi lấy token sau {error_time:.1f}s: {error_msg}")

        # Check for specific connection errors
        if any(keyword in error_msg.lower() for keyword in ["connection", "closed", "timeout", "network"]):
            print("🌐 [BROWSER] Detected connection/network error - browser may have been blocked")
        elif "recaptcha" in error_msg.lower():
            print("🤖 [BROWSER] ReCAPTCHA related error - may need different approach")

        return None

    finally:
        # Luôn cleanup browser instance sau khi sử dụng
        cleanup_browser_instance(playwright, browser, context, page)

# Không còn cần hàm close_browser_instance vì mỗi request tự cleanup

# Đoạn này để test file này chạy độc lập
if __name__ == "__main__":
    t = get_captcha_token()
    print("Token test:", t)