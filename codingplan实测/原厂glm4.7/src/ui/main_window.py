"""
主窗口 - PySide6 图形界面
"""

import sys
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QPushButton, QComboBox,
    QTextEdit, QFileDialog, QFileDialog, QMessageBox, QInputDialog,
    QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QDragEnterEvent, QDropEvent

from src.core.watermark import DocxWatermarkTool
from src.db.models import Database, KeyManager


class WatermarkWorker(QThread):
    """水印处理工作线程"""
    finished = Signal(dict)
    log = Signal(str)

    def __init__(self, mode, tool, **kwargs):
        super().__init__()
        self.mode = mode
        self.tool = tool
        self.kwargs = kwargs

    def run(self):
        if self.mode == 'embed':
            self.log.emit('正在嵌入水印...')
            result = self.tool.embed_watermark(**self.kwargs)
        else:
            self.log.emit('正在分析水印...')
            result = self.tool.analyze_docx(**self.kwargs)

        self.finished.emit(result)


class EmbedTab(QWidget):
    """水印嵌入标签页"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        self.load_keys()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()

        # 文件选择组
        file_group = QGroupBox('1. 选择原始文档')
        file_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText('拖拽文件到此处或点击浏览...')
        self.file_input.setDragEnabled(True)
        self.browse_btn = QPushButton('浏览...')
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(self.browse_btn)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # 溯源信息组
        info_group = QGroupBox('2. 输入溯源信息')
        info_layout = QFormLayout()
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText('如：张三-123')
        self.dept_input = QLineEdit()
        self.dept_input.setPlaceholderText('如：销售部')
        self.project_input = QLineEdit()
        self.project_input.setPlaceholderText('如：Project_Alpha')
        info_layout.addRow('用户标识*:', self.user_input)
        info_layout.addRow('部门名称:', self.dept_input)
        info_layout.addRow('项目名称:', self.project_input)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # 安全设置组
        security_group = QGroupBox('3. 安全设置')
        security_layout = QHBoxLayout()
        security_layout.addWidget(QLabel('密钥:'))
        self.key_combo = QComboBox()
        self.key_combo.setMinimumWidth(200)
        security_layout.addWidget(self.key_combo)

        self.new_key_btn = QPushButton('新建')
        self.new_key_btn.clicked.connect(self._new_key)
        security_layout.addWidget(self.new_key_btn)

        self.import_btn = QPushButton('导入')
        self.import_btn.clicked.connect(self._import_key)
        security_layout.addWidget(self.import_btn)

        self.export_btn = QPushButton('导出')
        self.export_btn.clicked.connect(self._export_key)
        security_layout.addWidget(self.export_btn)

        self.delete_btn = QPushButton('删除')
        self.delete_btn.clicked.connect(self._delete_key)
        security_layout.addWidget(self.delete_btn)

        security_group.setLayout(security_layout)
        layout.addWidget(security_group)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self.embed_btn = QPushButton('开始嵌入水印')
        self.embed_btn.clicked.connect(self.start_embed)
        self.embed_btn.setStyleSheet('QPushButton { font-size: 14px; padding: 10px; }')
        btn_layout.addStretch()
        btn_layout.addWidget(self.embed_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 日志输出
        layout.addWidget(QLabel('日志输出:'))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择 Word 文档', '', 'Word 文档 (*.docx)'
        )
        if file_path:
            self.file_input.setText(file_path)

    def load_keys(self):
        """加载密钥列表"""
        self.key_combo.clear()
        keys = self.main_window.key_manager.get_all_keys()
        for key in keys:
            self.key_combo.addItem(key['key_name'], key['key_name'])

        if self.key_combo.count() == 0:
            self.key_combo.addItem('（无密钥）', None)

    def _new_key(self):
        """新建密钥"""
        name, ok = QInputDialog.getText(self, '新建密钥', '请输入密钥名称:')
        if ok and name:
            password, ok = QInputDialog.getText(self, '设置密码', '请输入密钥密码:', echo=QLineEdit.Password)
            if ok and password:
                try:
                    self.main_window.key_manager.create_key(name, password)
                    self.log(f'[+] 密钥 "{name}" 创建成功')
                    self.load_keys()
                    # 同步到分析页面
                    self.main_window.refresh_analyze_keys()
                except ValueError as e:
                    QMessageBox.warning(self, '错误', str(e))

    def _import_key(self):
        """导入密钥"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择密钥备份文件', '', 'JSON 文件 (*.json)'
        )
        if file_path:
            result = self.main_window.key_manager.import_keys(file_path)
            if result['success']:
                self.log(f'[+] 导入成功：{result["imported"]} 个密钥')
                if result['skipped'] > 0:
                    self.log(f'[i] 跳过：{result["skipped"]} 个重复密钥')
                self.load_keys()
                self.main_window.refresh_analyze_keys()
            else:
                QMessageBox.warning(self, '错误', result.get('error', '导入失败'))

    def _export_key(self):
        """导出密钥"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, '保存密钥备份', 'keys_backup.json', 'JSON 文件 (*.json)'
        )
        if file_path:
            result = self.main_window.key_manager.export_keys(file_path)
            if result['success']:
                self.log(f'[+] 导出成功：{result["count"]} 个密钥')
            else:
                QMessageBox.warning(self, '错误', result.get('error', '导出失败'))

    def _delete_key(self):
        """删除密钥"""
        current_key = self.key_combo.currentData()
        if not current_key:
            return

        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除密钥 "{current_key}" 吗？',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.main_window.key_manager.delete_key(current_key):
                self.log(f'[+] 密钥 "{current_key}" 已删除')
                self.load_keys()
                self.main_window.refresh_analyze_keys()
            else:
                QMessageBox.warning(self, '错误', '删除失败')

    def start_embed(self):
        """开始嵌入水印"""
        # 验证输入
        file_path = self.file_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, '错误', '请选择原始文档')
            return

        if not Path(file_path).exists():
            QMessageBox.warning(self, '错误', '文件不存在')
            return

        user_info = self.user_input.text().strip()
        if not user_info:
            QMessageBox.warning(self, '错误', '请输入用户标识')
            return

        key_name = self.key_combo.currentData()
        if not key_name:
            QMessageBox.warning(self, '错误', '请选择或创建密钥')
            return

        # 获取密钥密码
        key_data = self.main_window.key_manager.get_key_by_name(key_name)
        if not key_data:
            QMessageBox.warning(self, '错误', '无法获取密钥信息')
            return

        # 准备输出路径
        input_path = Path(file_path)
        output_dir = input_path.parent / 'watermarked'
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{input_path.stem}_watermarked{input_path.suffix}"

        # 创建水印工具并启动工作线程
        tool = DocxWatermarkTool(key_data['key_password'])
        self.worker = WatermarkWorker(
            'embed',
            tool,
            input_path=str(input_path),
            output_path=str(output_path),
            user_info=user_info,
            department=self.dept_input.text().strip(),
            project=self.project_input.text().strip()
        )
        self.worker.log.connect(self.log)
        self.worker.finished.connect(self.on_embed_finished)
        self.embed_btn.setEnabled(False)
        self.worker.start()

    def on_embed_finished(self, result):
        """嵌入完成"""
        self.embed_btn.setEnabled(True)
        if result['success']:
            self.log(f'[+] 成功在 {result["positions_processed"]} 个位置嵌入水印')
            self.log(f'[+] 备份层写入: {"是" if result["backup_written"] else "否"}')
            self.log(f'[+] 输出文件已保存')
            QMessageBox.information(self, '成功', '水印嵌入成功！')
        else:
            self.log(f'[-] 嵌入失败: {result.get("error", "未知错误")}')
            QMessageBox.warning(self, '失败', result.get('error', '嵌入失败'))

    def log(self, message: str):
        """输出日志"""
        self.log_output.append(message)


class AnalyzeTab(QWidget):
    """分析溯源标签页"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        self.load_keys()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()

        # 文件选择组
        file_group = QGroupBox('1. 选择待分析文档')
        file_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText('拖拽文件到此处或点击浏览...')
        self.browse_btn = QPushButton('浏览...')
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(self.browse_btn)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # 安全设置组
        security_group = QGroupBox('2. 安全设置')
        security_layout = QHBoxLayout()
        security_layout.addWidget(QLabel('尝试使用密钥:'))
        self.key_combo = QComboBox()
        self.key_combo.setMinimumWidth(200)
        security_layout.addWidget(self.key_combo)
        security_layout.addStretch()
        security_group.setLayout(security_layout)
        layout.addWidget(security_group)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self.analyze_btn = QPushButton('开始分析对比')
        self.analyze_btn.clicked.connect(self.start_analyze)
        self.analyze_btn.setStyleSheet('QPushButton { font-size: 14px; padding: 10px; }')
        btn_layout.addStretch()
        btn_layout.addWidget(self.analyze_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 分析结果
        layout.addWidget(QLabel('分析结果:'))
        self.result_group = QGroupBox()
        result_layout = QVBoxLayout()
        self.watermark_found_label = QLabel('是否发现水印: 否')
        self.integrity_label = QLabel('水印完整度: --')
        self.info_label = QLabel('溯源信息: --')
        self.source_label = QLabel('提取来源: --')

        # 设置字体
        font = QFont()
        font.setPointSize(10)
        self.info_label.setFont(font)

        result_layout.addWidget(self.watermark_found_label)
        result_layout.addWidget(self.integrity_label)
        result_layout.addWidget(self.source_label)
        result_layout.addWidget(QLabel('-' * 50))
        result_layout.addWidget(self.info_label)
        self.result_group.setLayout(result_layout)
        layout.addWidget(self.result_group)

        # 提取日志
        layout.addWidget(QLabel('提取详情日志:'))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择 Word 文档', '', 'Word 文档 (*.docx)'
        )
        if file_path:
            self.file_input.setText(file_path)

    def load_keys(self):
        """加载密钥列表"""
        self.key_combo.clear()
        keys = self.main_window.key_manager.get_all_keys()
        for key in keys:
            self.key_combo.addItem(key['key_name'], key['key_name'])

        if self.key_combo.count() == 0:
            self.key_combo.addItem('（无密钥）', None)

    def refresh_keys(self):
        """刷新密钥列表"""
        self.load_keys()

    def start_analyze(self):
        """开始分析"""
        file_path = self.file_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, '错误', '请选择待分析文档')
            return

        if not Path(file_path).exists():
            QMessageBox.warning(self, '错误', '文件不存在')
            return

        key_name = self.key_combo.currentData()
        if not key_name:
            QMessageBox.warning(self, '错误', '请选择密钥')
            return

        # 获取密钥密码
        key_data = self.main_window.key_manager.get_key_by_name(key_name)
        if not key_data:
            QMessageBox.warning(self, '错误', '无法获取密钥信息')
            return

        # 创建水印工具并启动工作线程
        tool = DocxWatermarkTool(key_data['key_password'])
        self.worker = WatermarkWorker(
            'analyze',
            tool,
            file_path=file_path
        )
        self.worker.log.connect(self.log)
        self.worker.finished.connect(self.on_analyze_finished)
        self.analyze_btn.setEnabled(False)
        self.worker.start()

    def on_analyze_finished(self, result):
        """分析完成"""
        self.analyze_btn.setEnabled(True)

        if result['success']:
            data = result['watermark_data']
            self.watermark_found_label.setText('是否发现水印: 是')
            self.integrity_label.setText(f'水印完整度: {result["integrity"]}%')
            self.source_label.setText(f'提取来源: {result.get("extraction_source", "未知")}')

            info_text = f"溯源信息: {data['uid']}"
            if data.get('department'):
                info_text += f"\n部门: {data['department']}"
            if data.get('project'):
                info_text += f"\n项目: {data['project']}"
            info_text += f"\n时间: {data['timestamp']}"
            self.info_label.setText(info_text)

            self.log('[+] 分析成功！')
            self.log(f'[+] 提取来源: {result.get("extraction_source", "未知")}')
        else:
            self.watermark_found_label.setText('是否发现水印: 否')
            self.integrity_label.setText('水印完整度: --')
            self.info_label.setText('溯源信息: --')
            self.source_label.setText('提取来源: --')
            self.log(f'[-] 分析失败: {result.get("error", "未知错误")}')

    def log(self, message: str):
        """输出日志"""
        self.log_output.append(message)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Word 智能水印溯源系统 v1.1.0')
        self.setGeometry(100, 100, 900, 700)

        # 初始化数据库
        self.database = Database('watermark.db')
        self.key_manager = KeyManager(self.database)

        # 确保存在默认密钥
        self._ensure_default_key()

        # 创建界面
        self.init_ui()

    def _ensure_default_key(self):
        """确保存在默认密钥"""
        existing = self.key_manager.get_all_keys()
        if not existing:
            self.key_manager.create_key('默认密钥', 'docx_watermark_default_key_2024')

    def init_ui(self):
        """初始化界面"""
        # 创建标签页
        tab_widget = QTabWidget()
        self.embed_tab = EmbedTab(self)
        self.analyze_tab = AnalyzeTab(self)
        tab_widget.addTab(self.embed_tab, '水印嵌入')
        tab_widget.addTab(self.analyze_tab, '分析溯源')

        # 设置为中心部件
        self.setCentralWidget(tab_widget)

    def refresh_analyze_keys(self):
        """刷新分析页面的密钥列表"""
        self.analyze_tab.refresh_keys()

    def closeEvent(self, event):
        """关闭事件"""
        self.database.close()
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用 Fusion 样式
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
