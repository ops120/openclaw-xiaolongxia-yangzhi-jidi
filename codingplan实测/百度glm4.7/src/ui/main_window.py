# -*- coding: utf-8 -*-
"""
主窗口 - 双标签页界面
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
    QComboBox, QFileDialog, QMessageBox, QGroupBox, QFormLayout,
    QProgressBar, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.watermark import DocxWatermarkTool
from src.db.models import Database, KeyManager, TraceLogManager
from src.utils.config import Config
from src.utils.logger import get_logger, setup_logger


class EmbedWorker(QThread):
    """水印嵌入工作线程"""
    finished = Signal(dict)
    progress = Signal(str)

    def __init__(self, tool, input_path, output_path, user_info, department, project):
        super().__init__()
        self.tool = tool
        self.input_path = input_path
        self.output_path = output_path
        self.user_info = user_info
        self.department = department
        self.project = project

    def run(self):
        self.progress.emit('开始嵌入水印...')
        result = self.tool.embed_watermark(
            self.input_path, self.output_path,
            self.user_info, self.department, self.project
        )
        self.finished.emit(result)


class AnalyzeWorker(QThread):
    """水印分析工作线程"""
    finished = Signal(dict)
    progress = Signal(str)

    def __init__(self, tool, file_path):
        super().__init__()
        self.tool = tool
        self.file_path = file_path

    def run(self):
        self.progress.emit('开始分析文档...')
        result = self.tool.analyze_docx(self.file_path)
        self.finished.emit(result)


class NewKeyDialog(QDialog):
    """新建密钥对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('新建密钥')
        self.setMinimumWidth(350)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('输入密钥名称（如：项目A密钥）')
        layout.addRow('密钥名称:', self.name_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText('输入密钥密码')
        layout.addRow('密码:', self.password_edit)

        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.Password)
        self.confirm_edit.setPlaceholderText('再次输入密码')
        layout.addRow('确认密码:', self.confirm_edit)

        # 生成随机密码按钮
        self.generate_btn = QPushButton('生成随机密码')
        self.generate_btn.clicked.connect(self._generate_password)
        layout.addRow('', self.generate_btn)

        # 对话框按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _generate_password(self):
        """生成随机密码"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
        password = ''.join(secrets.choice(alphabet) for _ in range(24))
        self.password_edit.setText(password)
        self.confirm_edit.setText(password)

    def _validate(self):
        """验证输入"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, '错误', '请输入密钥名称')
            return

        if not self.password_edit.text():
            QMessageBox.warning(self, '错误', '请输入密码')
            return

        if self.password_edit.text() != self.confirm_edit.text():
            QMessageBox.warning(self, '错误', '两次输入的密码不一致')
            return

        self.accept()

    def get_data(self):
        """获取输入数据"""
        return {
            'name': self.name_edit.text().strip(),
            'password': self.password_edit.text()
        }


class EmbedTab(QWidget):
    """水印嵌入标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.key_manager = KeyManager(self.db)
        self.trace_manager = TraceLogManager(self.db)
        self.config = Config()
        self.worker = None

        self._init_ui()
        self._load_keys()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 文档选择
        doc_group = QGroupBox('1. 选择原始文档')
        doc_layout = QHBoxLayout(doc_group)

        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText('选择 .docx 文件')
        self.file_edit.setReadOnly(True)
        doc_layout.addWidget(self.file_edit)

        browse_btn = QPushButton('浏览...')
        browse_btn.clicked.connect(self._browse_file)
        doc_layout.addWidget(browse_btn)

        layout.addWidget(doc_group)

        # 溯源信息
        info_group = QGroupBox('2. 输入溯源信息')
        info_layout = QFormLayout(info_group)

        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText('如：张三 - 工号123')
        info_layout.addRow('用户标识:', self.user_edit)

        self.dept_edit = QLineEdit()
        self.dept_edit.setPlaceholderText('如：销售部')
        self.dept_edit.setText(self.config.get('watermark.default_department', ''))
        info_layout.addRow('部门:', self.dept_edit)

        self.project_edit = QLineEdit()
        self.project_edit.setPlaceholderText('如：Project_Alpha')
        self.project_edit.setText(self.config.get('watermark.default_project', ''))
        info_layout.addRow('项目:', self.project_edit)

        layout.addWidget(info_group)

        # 安全设置
        security_group = QGroupBox('3. 安全设置')
        security_layout = QHBoxLayout(security_group)

        security_layout.addWidget(QLabel('密钥:'))

        self.key_combo = QComboBox()
        self.key_combo.setMinimumWidth(200)
        security_layout.addWidget(self.key_combo)

        new_key_btn = QPushButton('新建')
        new_key_btn.clicked.connect(self._new_key)
        security_layout.addWidget(new_key_btn)

        export_btn = QPushButton('导出')
        export_btn.clicked.connect(self._export_key)
        security_layout.addWidget(export_btn)

        import_btn = QPushButton('导入')
        import_btn.clicked.connect(self._import_key)
        security_layout.addWidget(import_btn)

        delete_btn = QPushButton('删除')
        delete_btn.clicked.connect(self._delete_key)
        security_layout.addWidget(delete_btn)

        security_layout.addStretch()

        layout.addWidget(security_group)

        # 操作按钮
        btn_layout = QHBoxLayout()

        self.embed_btn = QPushButton('开始嵌入水印')
        self.embed_btn.setMinimumHeight(40)
        self.embed_btn.clicked.connect(self._embed)
        btn_layout.addStretch()
        btn_layout.addWidget(self.embed_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 日志输出
        log_group = QGroupBox('日志输出')
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

    def _load_keys(self):
        """加载密钥列表"""
        self.key_combo.clear()
        keys = self.key_manager.get_all_keys()
        for key in keys:
            self.key_combo.addItem(key['key_name'], key['key_name'])

        if self.key_combo.count() == 0:
            # 创建默认密钥
            try:
                self.key_manager.create_key('默认密钥', 'default_password_2024')
                self._load_keys()
            except:
                pass

    def _browse_file(self):
        """选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择 Word 文档',
            '', 'Word 文档 (*.docx)'
        )
        if file_path:
            self.file_edit.setText(file_path)

    def _new_key(self):
        """新建密钥"""
        dialog = NewKeyDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.key_manager.create_key(data['name'], data['password'])
                self._load_keys()
                # 找到新创建的密钥并选中
                index = self.key_combo.findText(data['name'])
                if index >= 0:
                    self.key_combo.setCurrentIndex(index)
                QMessageBox.information(self, '成功', f'密钥 "{data["name"]}" 创建成功')
                # 刷新分析页面的密钥列表
                self.window().refresh_analyze_keys()
            except ValueError as e:
                QMessageBox.warning(self, '错误', str(e))

    def _export_key(self):
        """导出密钥"""
        key_name = self.key_combo.currentData()
        if not key_name:
            QMessageBox.warning(self, '错误', '请先选择密钥')
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, '导出密钥',
            f'{key_name}.json',
            'JSON 文件 (*.json)'
        )

        if save_path:
            json_data = self.key_manager.export_key(key_name)
            if json_data:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(json_data)
                QMessageBox.information(self, '成功', '密钥导出成功')
            else:
                QMessageBox.warning(self, '错误', '导出失败')

    def _import_key(self):
        """导入密钥"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '导入密钥',
            '', 'JSON 文件 (*.json)'
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = f.read()
                self.key_manager.import_key(json_data)
                self._load_keys()
                QMessageBox.information(self, '成功', '密钥导入成功')
                # 刷新分析页面的密钥列表
                self.window().refresh_analyze_keys()
            except ValueError as e:
                QMessageBox.warning(self, '错误', str(e))
            except Exception as e:
                QMessageBox.warning(self, '错误', f'导入失败: {e}')

    def _delete_key(self):
        """删除密钥"""
        key_name = self.key_combo.currentData()
        if not key_name:
            QMessageBox.warning(self, '错误', '请先选择密钥')
            return

        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除密钥 "{key_name}" 吗？\n删除后无法恢复！',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.key_manager.delete_key(key_name)
            self._load_keys()
            # 刷新分析页面的密钥列表
            self.window().refresh_analyze_keys()
            QMessageBox.information(self, '成功', '密钥已删除')

    def _log(self, message, success=True):
        """添加日志"""
        prefix = '[+] ' if success else '[-] '
        self.log_text.append(prefix + message)

    def _embed(self):
        """嵌入水印"""
        input_path = self.file_edit.text()
        if not input_path:
            QMessageBox.warning(self, '错误', '请选择原始文档')
            return

        user_info = self.user_edit.text().strip()
        if not user_info:
            QMessageBox.warning(self, '错误', '请输入用户标识')
            return

        key_name = self.key_combo.currentData()
        if not key_name:
            QMessageBox.warning(self, '错误', '请选择密钥')
            return

        # 获取密钥密码
        key = self.key_manager.get_key(key_name)
        if not key:
            QMessageBox.warning(self, '错误', '无法获取密钥信息')
            return

        # 生成输出路径
        input_file = Path(input_path)
        output_dir = input_file.parent / self.config.default_output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = Path(input_file).stem
        output_path = output_dir / f'{timestamp}_watermarked.docx'

        # 创建水印工具
        tool = DocxWatermarkTool(password=key['password'])

        # 禁用按钮
        self.embed_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度

        self.log_text.clear()
        self._log('密钥已就绪...')
        self._log(f'使用密钥: {key_name}')

        # 启动工作线程
        self.worker = EmbedWorker(
            tool, input_path, str(output_path),
            user_info, self.dept_edit.text(), self.project_edit.text()
        )
        self.worker.progress.connect(self._log)
        self.worker.finished.connect(self._on_embed_finished)
        self.worker.start()

    def _on_embed_finished(self, result):
        """嵌入完成回调"""
        self.progress_bar.setVisible(False)
        self.embed_btn.setEnabled(True)

        if result['success']:
            self._log(f'已在 {result["paragraphs_processed"]} 个段落中嵌入水印')
            self._log(f'备份层: {", ".join(result["backup_layers"])}')
            self._log(f'成功保存至: {result.get("output_path", "已完成")}')

            # 保存分发记录
            self.trace_manager.add_log(
                uid=self.user_edit.text(),
                user_info=self.user_edit.text(),
                department=self.dept_edit.text(),
                project=self.project_edit.text(),
                original_filename=self.file_edit.text()
            )

            QMessageBox.information(
                self, '成功',
                f'水印嵌入成功！\n输出文件: {result.get("output_path", "已完成")}'
            )
        else:
            self._log(f'错误: {result.get("error", "未知错误")}', success=False)
            QMessageBox.warning(self, '失败', f'水印嵌入失败: {result.get("error", "未知错误")}')

    def refresh_keys(self):
        """刷新密钥列表"""
        current = self.key_combo.currentText()
        self._load_keys()
        index = self.key_combo.findText(current)
        if index >= 0:
            self.key_combo.setCurrentIndex(index)


class AnalyzeTab(QWidget):
    """分析溯源标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.key_manager = KeyManager(self.db)
        self.worker = None

        self._init_ui()
        self._load_keys()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 文档选择
        doc_group = QGroupBox('1. 选择待分析文档')
        doc_layout = QHBoxLayout(doc_group)

        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText('选择待分析的 .docx 文件（支持拖拽）')
        self.file_edit.setReadOnly(True)
        doc_layout.addWidget(self.file_edit)

        browse_btn = QPushButton('浏览...')
        browse_btn.clicked.connect(self._browse_file)
        doc_layout.addWidget(browse_btn)

        layout.addWidget(doc_group)

        # 安全设置
        security_group = QGroupBox('2. 安全设置')
        security_layout = QHBoxLayout(security_group)

        security_layout.addWidget(QLabel('尝试使用密钥:'))

        self.key_combo = QComboBox()
        self.key_combo.setMinimumWidth(200)
        security_layout.addWidget(self.key_combo)

        security_layout.addStretch()

        layout.addWidget(security_group)

        # 操作按钮
        btn_layout = QHBoxLayout()

        self.analyze_btn = QPushButton('开始分析对比')
        self.analyze_btn.setMinimumHeight(40)
        self.analyze_btn.clicked.connect(self._analyze)
        btn_layout.addStretch()
        btn_layout.addWidget(self.analyze_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 分析结果
        result_group = QGroupBox('分析结果')
        result_layout = QVBoxLayout(result_group)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(200)
        result_layout.addWidget(self.result_text)

        layout.addWidget(result_group)

        # 提取详情日志
        log_group = QGroupBox('提取详情日志')
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

    def _load_keys(self):
        """加载密钥列表"""
        self.key_combo.clear()
        keys = self.key_manager.get_all_keys()
        for key in keys:
            self.key_combo.addItem(key['key_name'], key['key_name'])

    def refresh_keys(self):
        """刷新密钥列表"""
        current = self.key_combo.currentText()
        self._load_keys()
        index = self.key_combo.findText(current)
        if index >= 0:
            self.key_combo.setCurrentIndex(index)

    def _browse_file(self):
        """选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择待分析文档',
            '', 'Word 文档 (*.docx)'
        )
        if file_path:
            self.file_edit.setText(file_path)

    def _log(self, message):
        """添加日志"""
        self.log_text.append(message)

    def _analyze(self):
        """分析水印"""
        file_path = self.file_edit.text()
        if not file_path:
            QMessageBox.warning(self, '错误', '请选择待分析文档')
            return

        key_name = self.key_combo.currentData()
        if not key_name:
            QMessageBox.warning(self, '错误', '请选择密钥')
            return

        # 获取密钥密码
        key = self.key_manager.get_key(key_name)
        if not key:
            QMessageBox.warning(self, '错误', '无法获取密钥密码')
            return

        # 创建水印工具
        tool = DocxWatermarkTool(password=key['password'])

        # 禁用按钮
        self.analyze_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.log_text.clear()
        self.result_text.clear()
        self._log('开始分析...')

        # 启动工作线程
        self.worker = AnalyzeWorker(tool, file_path)
        self.worker.progress.connect(self._log)
        self.worker.finished.connect(self._on_analyze_finished)
        self.worker.start()

    def _on_analyze_finished(self, result):
        """分析完成回调"""
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)

        # 显示日志
        for log in result.get('log', []):
            self._log(log)

        # 显示结果
        if result['success'] and result['has_watermark']:
            data = result['watermark_data']

            result_html = '''
            <style>
                .result-box { padding: 10px; background: #f0f9eb; border-radius: 5px; }
                .label { font-weight: bold; color: #333; }
                .value { color: #0066cc; font-size: 14px; }
                .highlight { background: #fff3cd; padding: 5px; border-radius: 3px; }
            </style>
            <div class="result-box">
                <p><span class="label">是否发现水印:</span> <span class="value">是</span></p>
                <p><span class="label">水印完整度:</span> <span class="value">{integrity}%</span></p>
                <p><span class="label">提取来源:</span> <span class="value">{source}</span></p>
                <hr>
                <p class="highlight"><span class="label">溯源信息:</span> <span class="value">{uid}</span></p>
                <p><span class="label">部门:</span> <span class="value">{department}</span></p>
                <p><span class="label">项目:</span> <span class="value">{project}</span></p>
                <p><span class="label">时间戳:</span> <span class="value">{timestamp}</span></p>
            </div>
            '''.format(
                integrity=result.get('integrity', 100),
                source=result.get('source', '未知'),
                uid=data.get('uid', '未知'),
                department=data.get('department', '-'),
                project=data.get('project', '-'),
                timestamp=data.get('timestamp', '未知')
            )

            self.result_text.setHtml(result_html)
        else:
            error = result.get('error', '未知错误')
            self.result_text.setHtml(f'''
            <div style="padding: 10px; background: #fef0f0; border-radius: 5px; color: #f56c6c;">
                <p><b>分析失败</b></p>
                <p>{error}</p>
            </div>
            ''')


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle('Word 智能水印溯源系统 v1.1.0')
        self.setMinimumSize(800, 600)
        self.resize(900, 700)

        # 设置字体
        font = QFont('Microsoft YaHei', 9)
        self.setFont(font)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # 创建标签页
        self.tab_widget = QTabWidget()

        self.embed_tab = EmbedTab()
        self.analyze_tab = AnalyzeTab()

        self.tab_widget.addTab(self.embed_tab, '水印嵌入')
        self.tab_widget.addTab(self.analyze_tab, '分析溯源')

        layout.addWidget(self.tab_widget)

        # 状态栏
        self.statusBar().showMessage('就绪')

    def refresh_analyze_keys(self):
        """刷新分析页面的密钥列表"""
        self.analyze_tab.refresh_keys()

    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(
            self, '确认退出',
            '确定要退出程序吗？',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


def run_gui():
    """运行 GUI 应用"""
    # 设置日志
    setup_logger('INFO')

    # 创建应用
    app = QApplication(sys.argv)

    # 设置应用样式
    app.setStyle('Fusion')

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 运行应用
    sys.exit(app.exec())


if __name__ == '__main__':
    run_gui()
