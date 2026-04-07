"""
主窗口UI
包含嵌入和分析两个标签页
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QPushButton, QComboBox,
    QTextEdit, QFileDialog, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal


from ..core.watermark import DocxWatermarkTool, DEFAULT_PASSWORD
from ..db.models import Database, KeyManager


class EmbedThread(QThread):
    """嵌入水印的后台线程"""
    finished = Signal(dict)

    def __init__(self, tool, input_path, output_path, user_info, department, project):
        super().__init__()
        self.tool = tool
        self.input_path = input_path
        self.output_path = output_path
        self.user_info = user_info
        self.department = department
        self.project = project

    def run(self):
        result = self.tool.embed_watermark(
            self.input_path, self.output_path,
            self.user_info, self.department, self.project
        )
        self.finished.emit(result)


class AnalyzeThread(QThread):
    """分析水印的后台线程"""
    finished = Signal(dict)

    def __init__(self, tool, file_path):
        super().__init__()
        self.tool = tool
        self.file_path = file_path

    def run(self):
        result = self.tool.analyze_docx(self.file_path)
        self.finished.emit(result)


class EmbedTab(QWidget):
    """水印嵌入标签页"""

    def __init__(self, window=None):
        super().__init__()
        self.window = window
        self.db_key_manager = KeyManager()
        self.current_tool = None
        self._setup_ui()
        self._load_keys()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # 1. 文件选择
        file_group = QGroupBox("1. 选择原始文档")
        file_layout = QHBoxLayout()

        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("选择要添加水印的 .docx 文件")
        self.file_input.setReadOnly(True)

        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self._browse_file)

        file_layout.addWidget(self.file_input)
        file_layout.addWidget(self.browse_button)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # 2. 溯源信息输入
        info_group = QGroupBox("2. 输入溯源信息")
        info_layout = QVBoxLayout()

        info_layout.addWidget(QLabel("接收者信息 (姓名/工号/项目):"))
        self.user_info_input = QLineEdit()
        self.user_info_input.setPlaceholderText("例如: 张三-销售部-20231015")
        info_layout.addWidget(self.user_info_input)

        info_layout.addWidget(QLabel("部门 (可选):"))
        self.department_input = QLineEdit()
        info_layout.addWidget(self.department_input)

        info_layout.addWidget(QLabel("项目 (可选):"))
        self.project_input = QLineEdit()
        info_layout.addWidget(self.project_input)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # 3. 密钥选择
        key_group = QGroupBox("3. 安全设置")
        key_layout = QVBoxLayout()

        key_layout.addWidget(QLabel("选择或创建密钥:"))
        key_select_layout = QHBoxLayout()

        self.key_combo = QComboBox()
        self.key_combo.setMinimumWidth(300)

        self.new_key_button = QPushButton("新建密钥")
        self.new_key_button.clicked.connect(self._new_key)

        key_select_layout.addWidget(self.key_combo)
        key_select_layout.addWidget(self.new_key_button)
        key_layout.addLayout(key_select_layout)

        key_group.setLayout(key_layout)
        layout.addWidget(key_group)

        # 4. 嵌入按钮
        self.embed_button = QPushButton("开始嵌入水印")
        self.embed_button.setMinimumHeight(50)
        self.embed_button.setStyleSheet(
            "background-color: #4CAF50; color: white; font-size: 16px; font-weight: bold;"
        )
        self.embed_button.clicked.connect(self._start_embed)
        layout.addWidget(self.embed_button)

        # 5. 日志输出
        log_group = QGroupBox("日志输出")
        log_layout = QVBoxLayout()

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(200)

        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        layout.addStretch()
        self.setLayout(layout)

    def _browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文档文件", "", "Word 文档 (*.docx)"
        )
        if file_path:
            self.file_input.setText(file_path)

    def _load_keys(self):
        """加载密钥列表"""
        self.key_combo.clear()
        keys = self.db_key_manager.list_keys()

        # 检查是否有默认密钥
        default_exists = any(key['key_name'] == 'default' for key in keys)

        if not default_exists:
            # 创建默认密钥
            self.db_key_manager.create_key('default', DEFAULT_PASSWORD)
            self.log_output.append(f"[+] 已创建默认密钥")

        # 重新加载
        keys = self.db_key_manager.list_keys()
        for key in keys:
            self.key_combo.addItem(key['key_name'], key['key_name'])

        if self.key_combo.count() > 0:
            self.key_combo.setCurrentIndex(0)

    def _new_key(self):
        """新建密钥"""
        from .key_dialog import KeyDialog
        dialog = KeyDialog(self)
        if dialog.exec():
            key_name = dialog.get_key_name()
            password = dialog.get_password()

            if key_name and password:
                success = self.db_key_manager.create_key(key_name, password)
                if success:
                    self.log_output.append(f"[+] 成功创建密钥: {key_name}")
                    self._load_keys()
                    # 刷新分析页面的密钥列表
                    if self.window:
                        self.window.refresh_analyze_keys()
                else:
                    QMessageBox.warning(self, "错误", "创建密钥失败")

    def _start_embed(self):
        """开始嵌入水印"""
        input_path = self.file_input.text().strip()
        user_info = self.user_info_input.text().strip()

        if not input_path:
            QMessageBox.warning(self, "错误", "请选择原始文档")
            return

        if not user_info:
            QMessageBox.warning(self, "错误", "请输入溯源信息")
            return

        if not Path(input_path).exists():
            QMessageBox.warning(self, "错误", "文件不存在")
            return

        # 获取当前选择的密钥
        key_name = self.key_combo.currentData()
        if not key_name:
            QMessageBox.warning(self, "错误", "请选择密钥")
            return

        key_data = self.db_key_manager.get_key(key_name)
        if not key_data:
            QMessageBox.warning(self, "错误", "无法获取密钥信息")
            return

        # 创建水印工具
        self.current_tool = DocxWatermarkTool(
            master_password=key_data['password'],
            salt=key_data['salt']
        )

        # 准备输出路径
        input_path_obj = Path(input_path)
        output_dir = input_path_obj.parent / 'watermarked'
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"watermarked_{input_path_obj.name}")

        # 清空日志
        self.log_output.clear()
        self.log_output.append(f"[+] 开始处理: {input_path}")
        self.log_output.append(f"[+] 使用密钥: {key_name}")
        self.log_output.append(f"[+] 溯源信息: {user_info}")

        # 禁用按钮
        self.embed_button.setEnabled(False)
        self.browse_button.setEnabled(False)

        # 启动后台线程
        self.embed_thread = EmbedThread(
            self.current_tool,
            input_path,
            output_path,
            user_info,
            self.department_input.text().strip(),
            self.project_input.text().strip()
        )
        self.current_output_path = output_path
        self.embed_thread.finished.connect(self._on_embed_finished)
        self.embed_thread.start()

    def _on_embed_finished(self, result):
        """嵌入完成回调"""
        if result['success']:
            self.log_output.append(f"[+] 已在 {result['paragraphs_processed']} 个位置嵌入水印")
            if result['backup_written']:
                self.log_output.append(f"[+] 备份层写入成功: {', '.join(result['backup_written'])}")
            output_path = getattr(self, 'current_output_path', '')
            if output_path:
                self.log_output.append(f"[+] 成功保存至: {output_path}")
            QMessageBox.information(self, "成功", "水印嵌入成功！")
        else:
            self.log_output.append(f"[-] 嵌入失败: {result.get('error', '未知错误')}")
            QMessageBox.warning(self, "错误", f"水印嵌入失败: {result.get('error', '未知错误')}")

        # 恢复按钮
        self.embed_button.setEnabled(True)
        self.browse_button.setEnabled(True)


class AnalyzeTab(QWidget):
    """分析溯源标签页"""

    def __init__(self, window=None):
        super().__init__()
        self.window = window
        self.db_key_manager = KeyManager()
        self.current_tool = None
        self._setup_ui()
        self._load_keys()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # 1. 文件选择
        file_group = QGroupBox("1. 选择待分析文档 (支持拖拽)")
        file_layout = QHBoxLayout()

        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("选择或拖拽要分析的 .docx 文件")
        self.file_input.setReadOnly(True)

        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self._browse_file)

        file_layout.addWidget(self.file_input)
        file_layout.addWidget(self.browse_button)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # 2. 密钥选择
        key_group = QGroupBox("2. 安全设置")
        key_layout = QVBoxLayout()

        key_layout.addWidget(QLabel("选择密钥:"))
        key_select_layout = QHBoxLayout()

        self.key_combo = QComboBox()
        self.key_combo.setMinimumWidth(300)

        self.import_key_button = QPushButton("导入密钥")
        self.import_key_button.clicked.connect(self._import_key)

        key_select_layout.addWidget(self.key_combo)
        key_select_layout.addWidget(self.import_key_button)
        key_layout.addLayout(key_select_layout)

        key_group.setLayout(key_layout)
        layout.addWidget(key_group)

        # 3. 分析按钮
        self.analyze_button = QPushButton("开始分析对比")
        self.analyze_button.setMinimumHeight(50)
        self.analyze_button.setStyleSheet(
            "background-color: #2196F3; color: white; font-size: 16px; font-weight: bold;"
        )
        self.analyze_button.clicked.connect(self._start_analyze)
        layout.addWidget(self.analyze_button)

        # 4. 分析结果
        result_group = QGroupBox("分析结果")
        result_layout = QVBoxLayout()

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(150)
        self.result_text.setStyleSheet("font-size: 14px;")

        result_layout.addWidget(self.result_text)
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

        # 5. 日志输出
        log_group = QGroupBox("提取详情日志")
        log_layout = QVBoxLayout()

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)

        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        layout.addStretch()
        self.setLayout(layout)

        # 启用拖放
        self.setAcceptDrops(True)

    def _browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文档文件", "", "Word 文档 (*.docx)"
        )
        if file_path:
            self.file_input.setText(file_path)

    def _load_keys(self):
        """加载密钥列表"""
        self.key_combo.clear()
        keys = self.db_key_manager.list_keys()

        for key in keys:
            self.key_combo.addItem(key['key_name'], key['key_name'])

        if self.key_combo.count() > 0:
            self.key_combo.setCurrentIndex(0)

    def _import_key(self):
        """导入密钥"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择密钥文件", "", "JSON 文件 (*.json)"
        )
        if file_path:
            success = self.db_key_manager.import_keys(file_path)
            if success:
                self.log_output.append(f"[+] 成功导入密钥")
                self._load_keys()
                QMessageBox.information(self, "成功", "密钥导入成功！")
            else:
                QMessageBox.warning(self, "错误", "密钥导入失败")

    def _start_analyze(self):
        """开始分析"""
        file_path = self.file_input.text().strip()

        if not file_path:
            QMessageBox.warning(self, "错误", "请选择待分析文档")
            return

        if not Path(file_path).exists():
            QMessageBox.warning(self, "错误", "文件不存在")
            return

        # 获取当前选择的密钥
        key_name = self.key_combo.currentData()
        if not key_name:
            QMessageBox.warning(self, "错误", "请选择密钥")
            return

        key_data = self.db_key_manager.get_key(key_name)
        if not key_data:
            QMessageBox.warning(self, "错误", "无法获取密钥信息")
            return

        # 创建水印工具
        self.current_tool = DocxWatermarkTool(
            master_password=key_data['password'],
            salt=key_data['salt']
        )

        # 清空日志和结果
        self.log_output.clear()
        self.result_text.clear()

        self.log_output.append(f"[+] 开始分析: {file_path}")
        self.log_output.append(f"[+] 使用密钥: {key_name}")

        # 禁用按钮
        self.analyze_button.setEnabled(False)
        self.browse_button.setEnabled(False)

        # 启动后台线程
        self.analyze_thread = AnalyzeThread(self.current_tool, file_path)
        self.analyze_thread.finished.connect(self._on_analyze_finished)
        self.analyze_thread.start()

    def _on_analyze_finished(self, result):
        """分析完成回调"""
        if result['success'] and result['has_watermark']:
            watermark_data = result['watermark_data']
            integrity = result['integrity']
            extracted_from = result.get('extracted_from', '未知')

            self.log_output.append(f"[+] 水印提取成功")
            self.log_output.append(f"[+] 提取来源: {extracted_from}")
            self.log_output.append(f"[+] 数据完整度: {integrity}%")

            result_str = f"""是否发现水印: 是
水印完整度: {integrity}% ({'可信度高' if integrity >= 80 else '可信度低'})
{'*' * 50}
溯源信息: {watermark_data.get('uid', '未知')}
部门: {watermark_data.get('department', '未知')}
项目: {watermark_data.get('project', '未知')}
时间戳: {watermark_data.get('timestamp', '未知')}
{'*' * 50}"""
            self.result_text.setText(result_str)
            QMessageBox.information(self, "成功", "水印提取成功！")
        else:
            error_msg = result.get('error', '未知错误')
            self.log_output.append(f"[-] 分析失败: {error_msg}")
            self.result_text.setText(f"分析结果: {error_msg}")
            QMessageBox.warning(self, "错误", f"分析失败: {error_msg}")

        # 恢复按钮
        self.analyze_button.setEnabled(True)
        self.browse_button.setEnabled(True)

    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """拖拽放下事件"""
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.file_input.setText(files[0])


class KeyDialog(QWidget):
    """新建密钥对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog)
        self.setWindowTitle("新建密钥")
        self.setFixedSize(400, 200)
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)

        layout.addWidget(QLabel("密钥名称:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入密钥名称")
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("密钥密码:"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("输入密钥密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        button_layout = QHBoxLayout()

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)

        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

        layout.addStretch()
        self.setLayout(layout)

    def get_key_name(self):
        """获取密钥名称"""
        return self.name_input.text().strip()

    def get_password(self):
        """获取密钥密码"""
        return self.password_input.text().strip()

    def accept(self):
        """确定"""
        key_name = self.get_key_name()
        password = self.get_password()

        if not key_name:
            QMessageBox.warning(self, "错误", "请输入密钥名称")
            return

        if not password:
            QMessageBox.warning(self, "错误", "请输入密钥密码")
            return

        super().accept()


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Word智能水印溯源系统 v1.1.0")
        self.setFixedSize(900, 700)

        # 创建标签页
        self.tab_widget = QTabWidget()

        self.embed_tab = EmbedTab(self)
        self.analyze_tab = AnalyzeTab(self)

        self.tab_widget.addTab(self.embed_tab, "水印嵌入")
        self.tab_widget.addTab(self.analyze_tab, "分析溯源")

        self.setCentralWidget(self.tab_widget)

    def refresh_analyze_keys(self):
        """刷新分析页面的密钥列表"""
        self.analyze_tab._load_keys()


def main():
    """主函数"""
    import sys

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
