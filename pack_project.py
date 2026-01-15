import os

# ================= CẤU HÌNH =================
OUTPUT_FILE = "FULL_PROJECT_CONTEXT.txt"

INCLUDED_EXTENSIONS = {
    '.py', '.vue', '.ts', '.js', '.json',
    '.css', '.html', '.env.example', '.env'
    # ⚠️ Không nên lấy .env thật nếu có key
}

# ❌ BỎ QUA HOÀN TOÀN
IGNORE_DIRS = {
    'node_modules', 'venv', 'env', '__pycache__', '.git',
    '.vscode', '.idea', 'dist', 'build',
    'generated_images', 'final_videos', 'temp', '.nuxt', 'TEST',
}

# ✅ CHỈ LẤY CẤU TRÚC, KHÔNG ĐỌC FILE
STRUCTURE_ONLY_DIRS = {
    'storage'
}

IGNORE_FILES = {
    'package-lock.json', 'yarn.lock', 'poetry.lock',
    'pack_project.py', OUTPUT_FILE, '.DS_Store' ,'frontend.py'
}
# ============================================


def is_ignored(path, is_dir=False):
    name = os.path.basename(path)
    if is_dir:
        return name in IGNORE_DIRS
    return name in IGNORE_FILES


def get_file_content(file_path):
    try:
        if os.path.getsize(file_path) > 500 * 1024:
            return f"[FILE QUÁ LỚN - BỎ QUA]: {os.path.getsize(file_path)} bytes"

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        return f"[LỖI KHÔNG ĐỌC ĐƯỢC FILE]: {e}"


def generate_tree(startpath):
    tree = "PROJECT STRUCTURE:\n"

    for root, dirs, files in os.walk(startpath):
        base = os.path.basename(root)

        # ❌ bỏ qua hoàn toàn
        if base in IGNORE_DIRS:
            dirs[:] = []
            continue

        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * level
        tree += f"{indent}{base}/\n"

        # ✅ chỉ ghi cấu trúc
        if base in STRUCTURE_ONLY_DIRS:
            continue

        subindent = ' ' * 4 * (level + 1)
        for f in files:
            if f not in IGNORE_FILES:
                tree += f"{subindent}{f}\n"

    return tree


def main():
    root_dir = os.getcwd()
    print(f"🚀 Đang đóng gói dự án tại: {root_dir}")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        out.write("=== PROJECT CONTEXT EXPORT ===\n\n")
        out.write(generate_tree(root_dir))
        out.write("\n" + "=" * 60 + "\n\n")

        file_count = 0

        for root, dirs, files in os.walk(root_dir):
            base = os.path.basename(root)

            # ❌ bỏ qua hoàn toàn
            if base in IGNORE_DIRS:
                dirs[:] = []
                continue

            # ✅ chỉ lấy cấu trúc
            if base in STRUCTURE_ONLY_DIRS:
                continue

            for file in files:
                if file in IGNORE_FILES:
                    continue

                ext = os.path.splitext(file)[1].lower()
                if ext in INCLUDED_EXTENSIONS:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, root_dir)

                    print(f" -> Đang gói: {rel_path}")

                    content = get_file_content(file_path)

                    out.write(f"--- START FILE: {rel_path} ---\n")
                    out.write(content)
                    out.write(f"\n--- END FILE: {rel_path} ---\n\n")

                    file_count += 1

    print(f"\n✅ XONG! Đã đóng gói {file_count} file code.")
    print(f"📁 File kết quả: {os.path.join(root_dir, OUTPUT_FILE)}")
    print("👉 Upload file này sang chat mới để AI đọc toàn bộ context.")


if __name__ == "__main__":
    main()
