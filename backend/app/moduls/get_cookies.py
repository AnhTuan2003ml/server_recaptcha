import os
import json
from typing import Tuple, Dict, Any, List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


# ==== PATH CƠ BẢN ====
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# File chứa danh sách tài khoản dạng "email - password"
# Sửa path để trỏ đúng tới _internal/config/config.txt
ACCOUNTS_FILE = os.path.join(BASE_DIR, "_internal", "config", "config.txt")

# File lưu cookies theo từng tài khoản
FLOW_COOKIES_FILE = os.path.join(BASE_DIR, "_internal", "config", "flow_cookies.json")

FLOW_URL = "https://labs.google/fx/tools/flow"
GOOGLE_SIGNIN_URL_PATTERN = "**/fx/api/auth/signin*"
FLOW_URL_PATTERN = "**/fx/tools/flow*"


def _read_accounts() -> List[Tuple[str, str]]:
    """
    Đọc danh sách tài khoản từ ACCOUNTS_FILE.
    Mỗi dòng: email - password
    """
    if not os.path.exists(ACCOUNTS_FILE):
        raise FileNotFoundError(f"Không tìm thấy file accounts: {ACCOUNTS_FILE}")

    accounts: List[Tuple[str, str]] = []
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Format: email - password
            if " - " in line:
                email, password = line.split(" - ", 1)
            elif "-" in line:
                email, password = line.split("-", 1)
            else:
                # Bỏ qua dòng sai format
                continue
            accounts.append((email.strip(), password.strip()))

    if not accounts:
        raise ValueError("File accounts rỗng hoặc không có dòng hợp lệ")

    return accounts


def get_account_by_index(index: int) -> Tuple[str, str]:
    """
    Lấy (email, password) theo index (1-based) trong file config.txt
    Ví dụ: index=1 -> dòng 1: sm8827365@id.veo2ultramaster.org - Tranduy@
    """
    if index < 1:
        raise ValueError("Index phải >= 1 (1-based)")

    accounts = _read_accounts()
    try:
        return accounts[index - 1]
    except IndexError:
        raise IndexError(f"Không có tài khoản ở dòng {index}, file chỉ có {len(accounts)} dòng hợp lệ")


def _ensure_cookies_dir():
    cookies_dir = os.path.dirname(FLOW_COOKIES_FILE)
    os.makedirs(cookies_dir, exist_ok=True)


def _load_all_cookies() -> Dict[str, Any]:
    if not os.path.exists(FLOW_COOKIES_FILE):
        return {}
    try:
        with open(FLOW_COOKIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except Exception:
        return {}


def _save_all_cookies(data: Dict[str, Any]) -> None:
    _ensure_cookies_dir()
    with open(FLOW_COOKIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_cookies_for_account(email: str, cookies: List[Dict[str, Any]]) -> None:
    """
    Lưu cookies theo từng tài khoản vào FLOW_COOKIES_FILE
    Cấu trúc:
    {
        "email1": {
            "cookies": [...],
            "last_login": <timestamp>
        },
        ...
    }
    """
    import time

    all_data = _load_all_cookies()
    all_data[email] = {
        "cookies": cookies,
        "last_login": int(time.time()),
    }
    _save_all_cookies(all_data)


def login_flow_and_save_cookies(account_index: int, headless: bool = True) -> List[Dict[str, Any]]:
    """
    Logic chính:
    - Lấy tk/mk theo dòng index trong config.txt
    - Dùng Playwright truy cập https://labs.google/fx/tools/flow
    - Click nút "Create with Flow"
    - Chờ sang trang signin Google
      + Dán email vào input#identifierId rồi Enter
      + Dán password vào input[name=Passwd] rồi Enter
    - Đợi URL quay về https://labs.google/fx/tools/flow
    - Lấy cookies và lưu theo từng tài khoản

    Trả về: danh sách cookies (thô) của Playwright cho tài khoản đó.
    """
    email, password = get_account_by_index(account_index)

    with sync_playwright() as p:
        browser = None
        context = None
        try:
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 720},
            )
            page = context.new_page()

            # 1. Truy cập Flow (giảm timeout để đỡ chờ lâu)
            page.goto(FLOW_URL, wait_until="networkidle", timeout=30_000)

            # 2. Click nút "Create with Flow"
            # Ưu tiên tìm theo text cho ổn định
            try:
                page.get_by_text("Create with Flow", exact=True).click(timeout=20_000)
            except PlaywrightTimeoutError:
                # fallback theo CSS class mà user cung cấp (có thể thay đổi theo thời gian)
                page.locator(
                    "button.sc-c177465c-1.QvjLS.sc-c0d0216b-0.kjNfNe >> text=Create with Flow"
                ).click(timeout=20_000)

            # 3. Chờ sang trang signin Google
            #   Hoặc pattern chung: accounts.google.com
            try:
                page.wait_for_url(
                    GOOGLE_SIGNIN_URL_PATTERN,
                    timeout=20_000,  # giảm từ 60s xuống 20s
                )
            except PlaywrightTimeoutError:
                # Nếu URL khác nhưng vẫn là trang login Google thì tiếp tục nếu thấy input email
                page.wait_for_selector("input#identifierId", timeout=20_000)

            # 4. Nhập email (giảm timeout để không chờ quá lâu)
            page.wait_for_selector("input#identifierId", timeout=15_000)
            page.fill("input#identifierId", email)
            page.keyboard.press("Enter")

            # 5. Nhập password
            page.wait_for_selector("input[name='Passwd']", timeout=20_000)
            page.fill("input[name='Passwd']", password)
            page.keyboard.press("Enter")

            # 6. Chờ quay lại Flow sau khi login thành công
            page.wait_for_url(FLOW_URL_PATTERN, timeout=60_000)

            # 7. Lấy cookies và lưu theo tài khoản
            cookies = context.cookies()
            save_cookies_for_account(email, cookies)

            return cookies

        finally:
            if context is not None:
                context.close()
            if browser is not None:
                browser.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Login Flow and save cookies")
    parser.add_argument("--index", type=int, default=1, help="Dòng tài khoản trong config.txt (1-based)")
    parser.add_argument("--headless", action="store_true", help="Chạy ẩn (headless)")

    args = parser.parse_args()
    cookies = login_flow_and_save_cookies(args.index, headless=args.headless)
    # In log thân thiện với Windows console (tránh UnicodeEncodeError)
    try:
        print(f"Đã lấy {len(cookies)} cookies cho tài khoản dòng {args.index}")
    except UnicodeEncodeError:
        # Fallback ASCII only
        print(f"Da lay {len(cookies)} cookies cho tai khoan dong {args.index}")
