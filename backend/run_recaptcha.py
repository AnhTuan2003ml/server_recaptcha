#!/usr/bin/env python3
"""
Standalone Recaptcha API Server Runner
Usage:
  python run_recaptcha.py --port 5000  # Chạy chung với main app
  python run_recaptcha.py --port 5001  # Chạy server riêng trên port 5001
"""

import sys
import os

# Thêm thư mục gốc vào Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Recaptcha API Server Runner')
    parser.add_argument('--port', type=int, default=5001,
                       help='Port to run the server on (default: 5001)')
    parser.add_argument('--host', default='0.0.0.0',
                       help='Host to bind to (default: 0.0.0.0)')

    args = parser.parse_args()

    # Import và chạy logic từ recaptcha.py
    from app.routes.recaptcha import run_recaptcha_server
    run_recaptcha_server(port=args.port, host=args.host) 