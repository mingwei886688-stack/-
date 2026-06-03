#!/usr/bin/env python3
"""文件大助 Web 版 — 启动器"""
import sys
import os
import socket
import webbrowser
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import create_app


def _find_port(start=5050, end=5060):
    """找一个可用的端口"""
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start  # 全被占了就用默认的


def main():
    app = create_app()
    port = _find_port(5050, 5060)

    def open_browser():
        import time
        time.sleep(1)
        webbrowser.open(f"http://localhost:{port}")

    threading.Thread(target=open_browser, daemon=True).start()

    print(f"\n  文件大助 Web 版已启动 → http://localhost:{port}\n")
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
