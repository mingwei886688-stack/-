"""PDF 相关路由"""
import os
import io
import base64
from flask import Blueprint, request, jsonify, send_file
from web.app import get_workspace

pdf_bp = Blueprint("pdf", __name__)


# ═══════════════════════════════════════════════════════════════
#  PDF 合并
# ═══════════════════════════════════════════════════════════════

@pdf_bp.route("/merge/upload", methods=["POST"])
def merge_upload():
    """上传 PDF 文件"""
    ws = get_workspace()
    files = request.files.getlist("files")
    added = []
    for f in files:
        if not f.filename.lower().endswith(".pdf"):
            continue
        save_path = os.path.join(ws.tmpdir, f.filename)
        f.save(save_path)
        ws.pdf_merger.add_file(save_path)
        added.append(f.filename)
    return jsonify({"added": len(added), "names": added, "total": ws.pdf_merger.file_count})


@pdf_bp.route("/merge/files", methods=["GET"])
def merge_files():
    """获取已添加的文件列表"""
    ws = get_workspace()
    files = []
    for i in range(ws.pdf_merger.file_count):
        info = ws.pdf_merger.get_file_info(i)
        files.append({
            "index": i,
            "name": os.path.basename(ws.pdf_merger.file_paths[i]),
            "pages": info.get("total_pages", 0),
            "range": info.get("page_range", (1, info.get("total_pages", 1))),  # pyright: ignore[reportReturnType]
        })
    return jsonify({"files": files, "total": ws.pdf_merger.file_count})


@pdf_bp.route("/merge/remove/<int:index>", methods=["DELETE"])
def merge_remove(index):
    """删除指定文件"""
    ws = get_workspace()
    if 0 <= index < ws.pdf_merger.file_count:
        ws.pdf_merger.remove_file(index)
        return jsonify({"ok": True, "total": ws.pdf_merger.file_count})
    return jsonify({"ok": False, "error": "索引无效"}), 400


@pdf_bp.route("/merge/reorder", methods=["POST"])
def merge_reorder():
    """重新排序文件"""
    ws = get_workspace()
    data = request.json
    new_order = data.get("order", [])
    if not isinstance(new_order, list):
        return jsonify({"ok": False, "error": "order 必须是数组"}), 400
    ws.pdf_merger.reorder_files(new_order)
    return jsonify({"ok": True, "total": ws.pdf_merger.file_count})


@pdf_bp.route("/merge/execute", methods=["GET", "POST"])
def merge_execute():
    """执行合并并返回下载"""
    ws = get_workspace()
    if ws.pdf_merger.file_count == 0:
        return jsonify({"ok": False, "error": "没有文件"}), 400
    out_path = os.path.join(ws.tmpdir, "merged_output.pdf")
    total_pages = ws.pdf_merger.merge(out_path)
    return send_file(out_path, as_attachment=True,
                     download_name=f"合并文档_{total_pages}页.pdf",
                     mimetype="application/pdf")


# ═══════════════════════════════════════════════════════════════
#  PDF 编辑
# ═══════════════════════════════════════════════════════════════

@pdf_bp.route("/edit/upload", methods=["POST"])
def edit_upload():
    """上传要编辑的 PDF"""
    ws = get_workspace()
    f = request.files.get("file")
    if not f:
        return jsonify({"ok": False, "error": "没有文件"}), 400
    save_path = os.path.join(ws.tmpdir, f.filename)
    f.save(save_path)
    ws.pdf_editor.load(save_path)
    return jsonify({"ok": True, "total_pages": ws.pdf_editor.total_pages})


@pdf_bp.route("/edit/thumbnails", methods=["GET"])
def edit_thumbnails():
    """获取页面缩略图（base64）"""
    ws = get_workspace()
    thumbs = []
    for i in range(ws.pdf_editor.total_pages):
        img = ws.pdf_editor.render_page(i)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        thumbs.append({"page": i + 1, "data": f"data:image/png;base64,{b64}"})
    return jsonify({"pages": thumbs, "total": ws.pdf_editor.total_pages})


@pdf_bp.route("/edit/delete", methods=["POST"])
def edit_delete():
    """删除指定页面（1-based页码）"""
    ws = get_workspace()
    pages = request.json.get("pages", [])
    pages_0 = [p - 1 for p in pages]  # 转0-based
    ws.pdf_editor.delete_pages(pages_0)
    return jsonify({"ok": True, "total_pages": ws.pdf_editor.total_pages})


@pdf_bp.route("/edit/rotate", methods=["POST"])
def edit_rotate():
    """旋转指定页面（1-based页码）"""
    ws = get_workspace()
    pages = request.json.get("pages", [])
    pages_0 = [p - 1 for p in pages]
    angle = request.json.get("angle", 90)
    ws.pdf_editor.rotate_pages(pages_0, angle)
    return jsonify({"ok": True, "total_pages": ws.pdf_editor.total_pages})


@pdf_bp.route("/edit/extract", methods=["POST"])
def edit_extract():
    """提取指定页面为新 PDF（1-based页码）"""
    ws = get_workspace()
    pages = request.json.get("pages", [])
    pages_0 = [p - 1 for p in pages]
    out_path = os.path.join(ws.tmpdir, "extracted.pdf")
    ws.pdf_editor.extract_pages(pages_0, out_path)
    return send_file(out_path, as_attachment=True,
                     download_name="提取的页面.pdf",
                     mimetype="application/pdf")


@pdf_bp.route("/edit/add-text", methods=["POST"])
def edit_add_text():
    """添加文字批注"""
    ws = get_workspace()
    data = request.json
    ws.pdf_editor.add_text(
        page=data["page"] - 1,
        x=data["x"], y=data["y"],
        text=data["text"],
        font_size=data.get("font_size", 12),
        color="#FF0000",
    )
    return jsonify({"ok": True})


@pdf_bp.route("/edit/redact", methods=["POST"])
def edit_redact():
    """遮盖文字"""
    ws = get_workspace()
    data = request.json
    ws.pdf_editor.redact_text(
        page=data["page"] - 1,
        x=data["x"], y=data["y"],
        width=data["width"], height=data["height"],
    )
    return jsonify({"ok": True})


@pdf_bp.route("/edit/save", methods=["POST"])
def edit_save():
    """保存编辑后的 PDF"""
    ws = get_workspace()
    out_path = os.path.join(ws.tmpdir, "edited_output.pdf")
    ws.pdf_editor.save(out_path)
    return send_file(out_path, as_attachment=True,
                     download_name="编辑后的文档.pdf",
                     mimetype="application/pdf")
