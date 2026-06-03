"""表格相关路由"""
import os
import json
from flask import Blueprint, request, jsonify, send_file
from web.app import get_workspace

table_bp = Blueprint("table", __name__)


# ═══════════════════════════════════════════════════════════════
#  表格合并
# ═══════════════════════════════════════════════════════════════

@table_bp.route("/merge/upload", methods=["POST"])
def merge_upload():
    """上传表格文件"""
    ws = get_workspace()
    files = request.files.getlist("files")
    all_sheets = []
    for f in files:
        ext = f.filename.lower().rsplit(".", 1)[-1] if "." in f.filename else ""
        if ext not in ("xlsx", "xls", "csv"):
            continue
        save_path = os.path.join(ws.tmpdir, f.filename)
        f.save(save_path)
        try:
            sheets = ws.table_merger.load_file(save_path)
            for sn in sheets:
                key = f"{f.filename}::{sn}"
                ws.table_merger.load_sheet(save_path, sn)
                info = ws.table_merger._file_info.get(key, {})
                all_sheets.append({
                    "key": key,
                    "file": f.filename,
                    "sheet": sn,
                    "rows": info.get("row_count", 0),
                    "cols": len(info.get("headers", [])),
                })
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 400
    return jsonify({"ok": True, "sheets": all_sheets, "total": len(all_sheets)})


@table_bp.route("/merge/sheets", methods=["GET"])
def merge_sheets():
    """获取已加载的所有 Sheet"""
    ws = get_workspace()
    sheets = []
    for key in ws.table_merger.loaded_keys:
        info = ws.table_merger._file_info.get(key, {})
        sheets.append({
            "key": key,
            "file": info.get("file_name", ""),
            "sheet": info.get("sheet_name", ""),
            "rows": info.get("row_count", 0),
            "cols": len(info.get("headers", [])),
        })
    return jsonify({"sheets": sheets, "total": len(sheets)})


@table_bp.route("/merge/remove/<path:key>", methods=["DELETE"])
def merge_remove(key):
    """移除指定 Sheet"""
    ws = get_workspace()
    ws.table_merger.remove(key)
    return jsonify({"ok": True})


@table_bp.route("/merge/clear", methods=["POST"])
def merge_clear():
    """清空所有 Sheet"""
    ws = get_workspace()
    ws.table_merger.clear()
    return jsonify({"ok": True})


@table_bp.route("/merge/preview", methods=["POST"])
def merge_preview():
    """预览合并结果"""
    ws = get_workspace()
    data = request.json
    keys = data.get("keys", [])
    mode = data.get("mode", "vertical")
    if len(keys) < 2:
        return jsonify({"ok": False, "error": "至少需要2个Sheet"}), 400
    try:
        if mode == "vertical":
            merged = ws.table_merger.merge_vertical(keys)
        else:
            merged = ws.table_merger.merge_horizontal(keys)
        # 保存到临时文件用于导出
        temp_path = os.path.join(ws.tmpdir, "_merge_preview.xlsx")
        merged.to_excel(temp_path, index=False)
        preview_data = {
            "columns": list(merged.columns),
            "rows": merged.head(100).fillna("").values.tolist(),
            "total_rows": len(merged),
            "total_cols": len(merged.columns),
        }
        # 转换 rows 为可序列化格式
        preview_data["rows"] = [[str(v) if v is not None else "" for v in row] for row in preview_data["rows"]]
        return jsonify({"ok": True, "preview": preview_data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@table_bp.route("/merge/export", methods=["POST"])
def merge_export():
    """导出合并结果"""
    ws = get_workspace()
    data = request.json
    keys = data.get("keys", [])
    mode = data.get("mode", "vertical")
    fmt = data.get("format", "xlsx")
    try:
        if mode == "vertical":
            merged = ws.table_merger.merge_vertical(keys)
        else:
            merged = ws.table_merger.merge_horizontal(keys)
        ext = "xlsx" if fmt == "xlsx" else "csv"
        out_path = os.path.join(ws.tmpdir, f"merged_output.{ext}")
        ws.table_merger.export(merged, out_path)
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if ext == "xlsx" else "text/csv"
        return send_file(out_path, as_attachment=True,
                         download_name=f"合并表格.{ext}",
                         mimetype=mimetype)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


# ═══════════════════════════════════════════════════════════════
#  表头匹配
# ═══════════════════════════════════════════════════════════════

@table_bp.route("/match/upload-source", methods=["POST"])
def match_upload_source():
    """上传源表（我的表格）"""
    return _match_upload("source")


@table_bp.route("/match/upload-lookup", methods=["POST"])
def match_upload_lookup():
    """上传查找表（参考数据）"""
    return _match_upload("lookup")


def _match_upload(role):
    ws = get_workspace()
    f = request.files.get("file")
    if not f:
        return jsonify({"ok": False, "error": "没有文件"}), 400
    save_path = os.path.join(ws.tmpdir, f.filename)
    f.save(save_path)
    try:
        sheets = ws.table_matcher.load_file(save_path)
        return jsonify({"ok": True, "filename": f.filename, "sheets": sheets, "role": role})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@table_bp.route("/match/load-sheet", methods=["POST"])
def match_load_sheet():
    """加载指定 Sheet"""
    ws = get_workspace()
    data = request.json
    filename = data.get("filename", "")
    sheet = data.get("sheet", "")
    role = data.get("role", "")  # "source" or "lookup"
    file_path = os.path.join(ws.tmpdir, filename)
    try:
        key = ws.table_matcher.load_sheet(file_path, sheet)
        headers = ws.table_matcher.get_headers(key)
        return jsonify({"ok": True, "key": key, "headers": headers, "role": role})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@table_bp.route("/match/execute", methods=["POST"])
def match_execute():
    """执行匹配"""
    ws = get_workspace()
    data = request.json
    try:
        ws.table_matcher.set_match_config(
            source_key=data["source_key"],
            lookup_key=data["lookup_key"],
            match_pairs=[tuple(p) for p in data["match_pairs"]],
            pull_columns=data["pull_columns"],
            match_mode=data.get("match_mode", "精确匹配"),
        )
        result = ws.table_matcher.execute()
        unmatched = ws.table_matcher.get_unmatched_rows()
        preview = {
            "columns": list(result.columns),
            "rows": result.head(100).fillna("").values.tolist(),
            "total_rows": len(result),
            "unmatched": len(unmatched),
        }
        preview["rows"] = [[str(v) if v is not None else "" for v in row] for row in preview["rows"]]
        # 保存到临时文件用于导出
        temp_path = os.path.join(ws.tmpdir, "_match_result.xlsx")
        result.to_excel(temp_path, index=False)
        return jsonify({"ok": True, "preview": preview})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@table_bp.route("/match/export", methods=["POST"])
def match_export():
    """导出匹配结果"""
    ws = get_workspace()
    temp_path = os.path.join(ws.tmpdir, "_match_result.xlsx")
    if not os.path.exists(temp_path):
        return jsonify({"ok": False, "error": "请先执行匹配"}), 400
    fmt = request.json.get("format", "xlsx") if request.json else "xlsx"
    ext = "xlsx" if fmt == "xlsx" else "csv"
    out_path = os.path.join(ws.tmpdir, f"match_output.{ext}")
    if ext == "csv":
        import pandas as pd
        df = pd.read_excel(temp_path)
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
    else:
        import shutil
        shutil.copy(temp_path, out_path)
    mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if ext == "xlsx" else "text/csv"
    return send_file(out_path, as_attachment=True,
                     download_name=f"匹配结果.{ext}",
                     mimetype=mimetype)
