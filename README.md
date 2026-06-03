# 📁 文件大助

办公杂项桌面工具箱，集成 **PDF 处理** 和 **表格处理** 两大模块。

## 功能

### PDF 工具
- **PDF 合并** — 拖拽多个 PDF，自由排序，一键合并导出
- **PDF 编辑** — 删除/旋转/提取页面，可视化操作

### 表格工具
- **表格合并** — 多文件/多 Sheet 的垂直追加和水平拼接
- **表头匹配** — 可视化 XLOOKUP，自定义匹配键，拉取查找表数据

## 安装与运行

```bash
# 1. 进入项目目录
cd 文件大助

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python src/main.py
```

## 系统要求

- macOS 12+（Apple Silicon / Intel）
- Python 3.10+
- 8GB+ RAM 推荐

## 技术栈

- Python + PySide6（桌面 UI）
- pypdf / pdfplumber（PDF 处理）
- pandas / openpyxl（表格处理）

## 项目结构

```
文件大助/
├── src/
│   ├── main.py              # 应用入口
│   ├── main_window.py       # 主窗口（左侧导航 + 右侧工作区）
│   ├── core/                # 核心框架（模块基类、事件总线、配置管理）
│   ├── common/              # 公共组件（拖放区、预览表格、样式主题）
│   ├── pdf_tools/           # PDF 模块（合并+编辑 逻辑+UI）
│   └── table_tools/         # 表格模块（合并+匹配 逻辑+UI）
├── tests/                   # 测试
├── requirements.txt
└── README.md
```
