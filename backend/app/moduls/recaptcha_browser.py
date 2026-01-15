# File: recaptcha_browser.py
import json
import time
import random
import threading
import uuid
from queue import Queue
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright

# ================= CONFIG =================
SITE_KEY = "6LdsFiUsAAAAAIjVDZcuLhaHiDn5nnHVXVRQGeMV"
TARGET_URL = "https://labs.google/fx/tools/flow"

CDP_HOST = "localhost:8848"
API_KEY = "5a0e4018-ebb4-4d3b-87c6-20a6a539b0f9"

PROFILE_IDS = [
    "844173d0-5aca-4ccd-b3a9-4fe0146faed0",
    "b54f6744-62fc-40c4-b9f6-32e72e2ddabe",
    "07b23b3d-40e9-4fc0-8e47-8024b6a4f5e5",
]

# ================= GLOBAL STATE =================
job_queue = Queue()
result_map = {}
result_lock = threading.Lock()

_worker_thread = None
_worker_lock = threading.Lock()
# ===============================================


def human_interaction(page):
    time.sleep(random.uniform(0.5, 1.2))
    page.mouse.wheel(0, random.randint(200, 400))
    time.sleep(random.uniform(1.5, 3.0))
    page.mouse.move(
        random.randint(200, 1000),
        random.randint(200, 700),
        steps=random.randint(10, 20)
    )
    time.sleep(random.uniform(0.5, 1.2))


def playwright_worker():
    print("🧠 Playwright worker started")

    with sync_playwright() as p:
        contexts = []

        for pid in PROFILE_IDS:
            query = urlencode({
                "x-api-key": API_KEY,
                "config": json.dumps({"headless": False, "autoClose": False})
            })
            ws = f"ws://{CDP_HOST}/api/v2/connect/{pid}?{query}"
            browser = p.chromium.connect_over_cdp(ws)
            ctx = browser.contexts[0] if browser.contexts else browser.new_context()
            contexts.append(ctx)
            print(f"✅ Profile ready: {pid}")

        idx = 0

        while True:
            job_id = job_queue.get()
            context = contexts[idx % len(contexts)]
            idx += 1

            try:
                page = context.new_page()
                page.goto(TARGET_URL, wait_until="domcontentloaded")

                page.wait_for_function(
                    "() => window.grecaptcha && window.grecaptcha.enterprise",
                    timeout=15000
                )

                human_interaction(page)

                token = page.evaluate(f"""
                    async () => {{
                        return await window.grecaptcha.enterprise.execute(
                            '{SITE_KEY}', {{ action: 'FLOW_GENERATION' }}
                        )
                    }}
                """)

                with result_lock:
                    result_map[job_id] = token

                print(f"🔑 Token generated ({len(token)} chars)")
                page.close()

            except Exception as e:
                print("❌ Worker error:", e)
                with result_lock:
                    result_map[job_id] = None


def start_worker_once():
    global _worker_thread
    with _worker_lock:
        if _worker_thread and _worker_thread.is_alive():
            return

        _worker_thread = threading.Thread(
            target=playwright_worker,
            daemon=True
        )
        _worker_thread.start()


def get_captcha_token(timeout=60):
    start_worker_once()

    job_id = uuid.uuid4().hex
    job_queue.put(job_id)

    start = time.time()
    while time.time() - start < timeout:
        with result_lock:
            if job_id in result_map:
                return result_map.pop(job_id)
        time.sleep(0.25)

    raise TimeoutError("Token generation timeout")


# ================= TEST =================
if __name__ == "__main__":
    token = get_captcha_token()
    print("Token test:", token)
