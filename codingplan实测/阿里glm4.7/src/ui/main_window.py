"""
主窗口UI模块
"""
import sys
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QLineEdit, QComboBox, QTextEdit,
    QFileDialog, QMessageBox, QGroupBox, QFormLayout, QProgressBar,
    QSplitter
)
from PySide6.QtCore import Qt, Signal, Slot, QThread
from PySide6.QtGui import QFont

from ..core.watermark import WatermarkEngine
from ..db.models import Database, KeyManager
from ..utils.config import config
from ..utils.logger import logger


class EmbedThread(QThread):
    """水印嵌入线程"""
    finished = Signal(dict)
    log = Signal(str)

    def __init__(self, engine: WatermarkEngine, input_path: str, output_path: str,
                 user_info: str, department: str, project: str):
        super().__init__()
        self.engine = engine
        self.input_path = input_path
        self.output_path = output_path
        self.user_info = user_info
        self.department = department
        self.project = project

    def run(self):
        """执行嵌入操作"""
        try:
            self.log.emit(f"[+] 开始嵌入水印...")
            self.log.emit(f"[+] 源文件: {self.input_path}")
            self.log.emit(f"[+] 目标文件: {self.output_path}")

            result = self.engine.embed_watermark(
                self.input_path,
                self.output_path,
                self.user_info,
                self.department,
                self.project
            )

            if result['success']:
                self.log.emit(f"[+] 成功在 {result['paragraphs_processed']} 个位置嵌入水印")
                self.log.emit(f"[+] 备份层已写入: {', '.join(result['backup_written'])}")

                # 记录到数据库
                Database.add_trace_log(
                    uid=self.user_info,
                    user_info=self.user_info,
                    department=self.department,
                    project=self.project,
                    original_filename=Path(self.input_path).name
                )

            self.finished.emit(result)
        except Exception as e:
            logger.exception("嵌入水印失败")
            self.log.emit(f"[!] 错误: {str(e)}")
            self.finished.emit({'success': False, 'error': str(e)})


class AnalyzeThread(QThread):
    """水印分析线程"""
    finished = Signal(dict)
    log = Signal(str)

    def __init__(self, engine: WatermarkEngine, file_path: str):
        super().__init__()
        self.engine = engine
        self.file_path = file_path

    def run(self):
        """执行分析操作"""
        try:
            self.log.emit(f"[+] 开始分析水印...")
            self.log.emit(f"[+] 文件: {self.file_path}")

            result = self.engine.extract_watermark(self.file_path)

            if result['success']:
                self.log.emit(f"[+] 发现水印! 数据源: {result['source']}")
                self.log.emit(f"[+] 水印完整度: {result['integrity']}%")

                if result['watermark_data']:
                    data = result['watermark_data']
                    self.log.emit(f"[+] 溯源信息: {data.get('uid', 'N/A')}")
                    self.log.emit(f"[+] 部门: {data.get('department', 'N/A')}")
                    self.log.emit(f"[+] 项目: {data.get('project', 'N/A')}")
                    self.log.emit(f"[+] 时间戳: {data.get('timestamp', 'N/A')}")

            self.finished.emit(result)
        except Exception as e:
            logger.exception("分析水印失败")
            self.log.emit(f"[!] 错误: {str(e)}")
            self.finished.emit({'success': False, 'error': str(e)})


class EmbedTab(QWidget):
    """水印嵌入标签页"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        self._load_keys()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()

        # 文件选择组
        file_group = QGroupBox("文件选择")
        file_layout = QHBoxLayout()
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("选择原始文档...")
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self._browse_file)
        file_layout.addWidget(QLabel("原始文档:"))
        file_layout.addWidget(self.input_path_edit)
        file_layout.addWidget(self.browse_button)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # 溯源信息组
        info_group = QGroupBox("溯源信息")
        info_layout = QFormLayout()

        self.user_info_edit = QLineEdit()
        self.user_info_edit.setPlaceholderText("如: 张三-123")
        info_layout.addRow("用户标识:", self.user_info_edit)

        self.department_edit = QLineEdit()
        self.department_edit.setPlaceholderText("如: 销售部")
        info_layout.addRow("部门:", self.department_edit)

        self.project_edit = QLineEdit()
        self.project_edit.setPlaceholderText("如: Project_Alpha")
        info_layout.addRow("项目:", self.project_edit)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # 安全设置组
        security_group = QGroupBox("安全设置")
        security_layout = QFormLayout()

        self.key_combo = QComboBox()
        security_layout.addRow("密钥:", self.key_combo)

        self.new_key_button = QPushButton("新建密钥")
        self.new_key_button.clicked.connect(self._new_key)
        security_layout.addRow("", self.new_key_button)

        security_group.setLayout(security_layout)
        layout.addWidget(security_group)

        # 操作按钮
        button_layout = QHBoxLayout()
        self.embed_button = QPushButton("开始嵌入水印")
        self.embed_button.setMinimumHeight(40)
        self.embed_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        self.embed_button.clicked.connect(self._embed_watermark)
        button_layout.addStretch()
        button_layout.addWidget(self.embed_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 日志输出
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
            self,
            "选择原始文档",
            "",
            "Word文档 (*.docx)"
        )
        if file_path:
            self.input_path_edit.setText(file_path)

    def _load_keys(self):
        """加载密钥列表"""
        self.key_combo.clear()
        keys = Database.list_keys()
        for key in keys:
            self.key_combo.addItem(key['key_name'], key['key_name'])

        if self.key_combo.count() == 0:
            self.key_combo.addItem("无密钥", None)

    def _new_key(self):
        """新建密钥"""
        from PySide6.QtWidgets import QDialog, QLineEdit, QDialogButtonBox, QVBoxLayout, QLabel, QFormLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("新建密钥")
        dialog.setMinimumWidth(300)

        layout = QFormLayout()

        name_edit = QLineEdit()
        name_edit.setPlaceholderText("密钥名称")
        layout.addRow("名称:", name_edit)

        password_edit = QLineEdit()
        password_edit.setPlaceholderText("密钥密码（留空自动生成）")
        password_edit.setEchoMode(QLineEdit.Password)
        layout.addRow("密码:", password_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.Accepted:
            name = name_edit.text().strip()
            password = password_edit.text().strip()

            if not name:
                QMessageBox.warning(self, "警告", "密钥名称不能为空")
                return

            if KeyManager.create_new_key(name, password if password else None):
                QMessageBox.information(self, "成功", "密钥创建成功")
                self._load_keys()
                self.main_window.refresh_analyze_keys()
            else:
                QMessageBox.warning(self, "警告", "密钥创建失败，名称可能已存在")

    def _embed_watermark(self):
        """嵌入水印"""
        input_path = self.input_path_edit.text().strip()
        user_info = self.user_info_edit.text().strip()
        department = self.department_edit.text().strip()
        project = self.project_edit.text().strip()

        if not input_path:
            QMessageBox.warning(self, "警告", "请选择原始文档")
            return

        if not user_info:
            QMessageBox.warning(self, "警告", "请输入用户标识信息")
            return

        if not Path(input_path).exists():
            QMessageBox.warning(self, "警告", "文件不存在")
            return

        key_name = self.key_combo.currentData()
        if not key_name:
            QMessageBox.warning(self, "警告", "请先创建密钥")
            return

        # 确定输出路径
        input_file = Path(input_path)
        output_dir = input_file.parent / "watermarked"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{input_file.stem}_watermarked{input_file.suffix}"

        # 获取密钥密码
        key_data = Database.get_key(key_name)
        if not key_data:
            QMessageBox.warning(self, "警告", "无法获取密钥信息")
            return

        # 创建水印引擎
        engine = WatermarkEngine(password=key_data['password'], salt=key_data['salt'])

        # 清空日志
        self.log_output.clear()

        # 禁用按钮，显示进度条
        self.embed_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        # 创建并启动线程
        self.embed_thread = EmbedThread(
            engine, input_path, str(output_path),
            user_info, department, project
        )
        self.embed_thread.log.connect(self._append_log)
        self.embed_thread.finished.connect(self._embed_finished)
        self.embed_thread.start()

    def _append_log(self, message: str):
        """添加日志"""
        self.log_output.append(message)

    @Slot(dict)
    def _embed_finished(self, result: dict):
        """嵌入完成"""
        self.embed_button.setEnabled(True)
        self.progress_bar.setVisible(False)

        if result['success']:
            QMessageBox.information(
                self,
                "成功",
                f"水印嵌入成功！\n\n输出文件:\n{result.get('output_path', '见日志')}"
            )
        else:
            QMessageBox.critical(
                self,
                "失败",
                f"水印嵌入失败:\n{result.get('error', '未知错误')}"
            )


class AnalyzeTab(QWidget):
    """分析溯源标签页"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self._load_keys()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()

        # 文件选择组
        file_group = QGroupBox("待分析文档")
        file_layout = QHBoxLayout()
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("选择待分析文档（支持拖拽）...")
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self._browse_file)
        file_layout.addWidget(QLabel("文件路径:"))
        file_layout.addWidget(self.input_path_edit)
        file_layout.addWidget(self.browse_button)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # 安全设置组
        security_group = QGroupBox("安全设置")
        security_layout = QHBoxLayout()
        security_layout.addWidget(QLabel("使用密钥:"))
        self.key_combo = QComboBox()
        security_layout.addWidget(self.key_combo)
        security_group.setLayout(security_layout)
        layout.addWidget(security_group)

        # 操作按钮
        button_layout = QHBoxLayout()
        self.analyze_button = QPushButton("开始分析对比")
        self.analyze_button.setMinimumHeight(40)
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #107c10;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #0b5a0b;
            }
            QPushButton:pressed {
                background-color: #084208;
            }
        """)
        self.analyze_button.clicked.connect(self._analyze_watermark)
        button_layout.addStretch()
        button_layout.addWidget(self.analyze_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 分析结果
        result_group = QGroupBox("分析结果")
        result_layout = QVBoxLayout()

        self.result_label = QLabel("等待分析...")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("font-size: 14px; padding: 20px; color: #666;")
        result_layout.addWidget(self.result_label)

        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

        # 日志输出
        log_group = QGroupBox("提取详情日志")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(200)
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        layout.addStretch()
        self.setLayout(layout)

        # 设置拖放支持
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        """拖放进入事件"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """拖放放下事件"""
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file_path in files:
            if file_path.lower().endswith('.docx'):
                self.input_path_edit.setText(file_path)
                break

    def _browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择待分析文档",
            "",
            "Word文档 (*.docx)"
        )
        if file_path:
            self.input_path_edit.setText(file_path)

    def _load_keys(self):
        """加载密钥列表"""
        self.key_combo.clear()
        keys = Database.list_keys()
        for key in keys:
            self.key_combo.addItem(key['key_name'], key['key_name'])

        if self.key_combo.count() == 0:
            self.key_combo.addItem("无密钥", None)

    def refresh_keys(self):
        """刷新密钥列表"""
        self._load_keys()

    def _analyze_watermark(self):
        """分析水印"""
        file_path = self.input_path_edit.text().strip()

        if not file_path:
            QMessageBox.warning(self, "警告", "请选择待分析文档")
            return

        if not Path(file_path).exists():
            QMessageBox.warning(self, "警告", "文件不存在")
            return

        key_name = self.key_combo.currentData()
        if not key_name:
            QMessageBox.warning(self, "警告", "请选择密钥")
            return

        # 获取密钥密码
        key_data = Database.get_key(key_name)
        if not key_data:
            QMessageBox.warning(self, "警告", "无法获取密钥信息")
            return

        # 创建水印引擎
        engine = WatermarkEngine(password=key_data['password'], salt=key_data['salt'])

        # 清空日志
        self.log_output.clear()
        self.result_label.setText("正在分析...")
        self.result_label.setStyleSheet("font-size: 14px; padding: 20px; color: #666;")

        # 禁用按钮，显示进度条
        self.analyze_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        # 创建并启动线程
        self.analyze_thread = AnalyzeThread(engine, file_path)
        self.analyze_thread.log.connect(self._append_log)
        self.analyze_thread.finished.connect(self._analyze_finished)
        self.analyze_thread.start()

    def _append_log(self, message: str):
        """添加日志"""
        self.log_output.append(message)

    @Slot(dict)
    def _analyze_finished(self, result: dict):
        """分析完成"""
        self.analyze_button.setEnabled(True)
        self.progress_bar.setVisible(False)

        if result['success'] and result['has_watermark']:
            data = result['watermark_data']
            result_text = f"""
            <div style="text-align: center; padding: 20px;">
                <h2 style="color: #107c10;">✓ 发现水印</h2>
                <p style="font-size: 16px; color: #333;"><strong>水印完整度:</strong> {result['integrity']}%</p>
                <hr style="margin: 15px 0; border: 1px solid #ddd;">
                <table style="margin: 0 auto; text-align: left;">
                    <tr><td><strong>用户标识:</strong></td><td>{data.get('uid', 'N/A')}</td></tr>
                    <tr><td><strong>部门:</strong></td><td>{data.get('department', 'N/A')}</td></tr>
                    <tr><td><strong>项目:</strong></td><td>{data.get('project', 'N/A')}</td></tr>
                    <tr><td><strong>时间戳:</strong></td><td>{data.get('timestamp', 'N/A')}</td></tr>
                </table>
                <hr style="margin: 15px 0; border: 1px solid #ddd;">
                <p style="color: #666; font-size: 12px;">数据源: {result['source']}</p>
            </div>
            """
            self.result_label.setText(result_text)
        else:
            self.result_label.setText(f"""
            <div style="text-align: center; padding: 20px;">
                <h2 style="color: #d13438;">✗ 未发现水印</h2>
                <p style="color: #666;">{result.get('error', '文档中未检测到水印信息')}</p>
            </div>
            """)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(f"{config.app_name} v{config.version}")
        self.setMinimumSize(config.get('ui.window_width', 1000), config.get('ui.window_height', 700))

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建布局
        layout = QVBoxLayout(central_widget)

        # 标题
        title_label = QLabel(f"{config.app_name}")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #0078d4; padding: 10px;")
        layout.addWidget(title_label)

        # 创建标签页
        self.tab_widget = QTabWidget()
        self.embed_tab = EmbedTab(self)
        self.analyze_tab = AnalyzeTab()
        self.tab_widget.addTab(self.embed_tab, "水印嵌入")
        self.tab_widget.addTab(self.analyze_tab, "分析溯源")
        layout.addWidget(self.tab_widget)

        # 状态栏
        self.statusBar().showMessage(f"就绪 | {config.version}")

    def refresh_analyze_keys(self):
        """刷新分析页面的密钥列表"""
        self.analyze_tab.refresh_keys()


def main():
    """主函数"""
    # 初始化应用
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()