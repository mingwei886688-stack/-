"""Flask 应用 — 文件大助 Web 版"""
import os
import sys
import uuid
import tempfile
import threading
import time
from flask import Flask, session, render_template

from pdf_tools.merger import PDFMerger
from pdf_tools.editor import PDFEditor
from table_tools.merger import TableMerger
from table_tools.matcher import TableMatcher


def _get_base_dir():
    """获取资源根目录（兼容 PyInstaller 打包）"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


_base = _get_base_dir()


class Workspace:
    """每个浏览器会话一个工作区，持有所有工具实例和临时文件"""

    def __init__(self):
        self.id = str(uuid.uuid4())[:8]
        self.tmpdir = tempfile.mkdtemp(prefix="fileassistant_")
        self.pdf_merger = PDFMerger()
        self.pdf_editor = PDFEditor()
        self.table_merger = TableMerger()
        self.table_matcher = TableMatcher()

    def cleanup(self):
        import shutil
        try:
            shutil.rmtree(self.tmpdir, ignore_errors=True)
        except Exception:
            pass


# 全局工作区字典 { workspace_id: Workspace }
_workspaces: dict[str, Workspace] = {}
_workspace_lock = threading.Lock()
_cleanup_timer = None


def get_workspace() -> Workspace:
    """获取当前会话的工作区"""
    ws_id = session.get("workspace_id")
    with _workspace_lock:
        if not ws_id or ws_id not in _workspaces:
            ws = Workspace()
            ws_id = ws.id
            session["workspace_id"] = ws_id
            _workspaces[ws_id] = ws
        return _workspaces[ws_id]


def cleanup_old_workspaces():
    """清理超过 2 小时未使用的旧工作区"""
    global _cleanup_timer
    with _workspace_lock:
        now = time.time()
        to_remove = []
        for ws_id, ws in _workspaces.items():
            tmpdir_mtime = os.path.getmtime(ws.tmpdir) if os.path.exists(ws.tmpdir) else 0
            if now - tmpdir_mtime > 7200:
                ws.cleanup()
                to_remove.append(ws_id)
        for ws_id in to_remove:
            del _workspaces[ws_id]
    _cleanup_timer = threading.Timer(3600, cleanup_old_workspaces)
    _cleanup_timer.daemon = True
    _cleanup_timer.start()


# 启动定时清理
cleanup_old_workspaces()


def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(_base, "web", "templates"),
                static_folder=os.path.join(_base, "web", "static"))
    app.secret_key = os.urandom(24).hex()

    # 注册路由
    from web.routes.pdf import pdf_bp
    from web.routes.table import table_bp
    app.register_blueprint(pdf_bp, url_prefix="/api/pdf")
    app.register_blueprint(table_bp, url_prefix="/api/table")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/pdf-merge")
    def pdf_merge_page():
        return render_template("pdf_merge.html")

    @app.route("/pdf-edit")
    def pdf_edit_page():
        return render_template("pdf_edit.html")

    @app.route("/table-merge")
    def table_merge_page():
        return render_template("table_merge.html")

    @app.route("/table-match")
    def table_match_page():
        return render_template("table_match.html")

    return app
