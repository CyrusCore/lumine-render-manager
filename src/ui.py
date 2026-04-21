import sys
import os
import time
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar, 
    QTextEdit, QFileDialog, QFrame, QGridLayout, QStackedWidget,
    QListWidget, QListWidgetItem, QAbstractItemView,
    QSpacerItem, QSizePolicy, QButtonGroup, QDialog
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QColor, QFont

from .settings import SettingsManager
from .worker import RenderWorker
from .styles import THEMES, get_stylesheet

class CustomModal(QDialog):
    def __init__(self, parent, title, message, is_confirm=False, theme_accent="#7209b7"):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.theme_accent = theme_accent
        self.result_value = False
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        container = QFrame(objectName="modalContainer")
        container.setFixedSize(400, 220)
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(30, 30, 30, 30)
        c_layout.setSpacing(15)
        
        title_label = QLabel(title.upper(), objectName="modalTitle")
        title_label.setStyleSheet(f"color: {theme_accent}; font-weight: 900; letter-spacing: 2px;")
        c_layout.addWidget(title_label)
        
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 13px;")
        c_layout.addWidget(msg_label)
        
        c_layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        if is_confirm:
            cancel_btn = QPushButton("CANCEL")
            cancel_btn.setObjectName("modalSecondaryBtn")
            cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(cancel_btn)
            
        ok_btn = QPushButton("CONFIRM" if is_confirm else "GOT IT")
        ok_btn.setObjectName("modalPrimaryBtn")
        ok_btn.setStyleSheet(f"background: {theme_accent}; color: white; font-weight: 800; border-radius: 10px; padding: 10px;")
        ok_btn.clicked.connect(self.accept_modal)
        btn_layout.addWidget(ok_btn)
        
        c_layout.addLayout(btn_layout)
        layout.addWidget(container)
        
        self.apply_styles()

    def accept_modal(self):
        self.result_value = True
        self.accept()

    def apply_styles(self):
        self.setStyleSheet(f"""
            #modalContainer {{
                background-color: #0c0d12;
                background: qradialgradient(cx:0.5, cy:0.5, radius:1.2, fx:0.5, fy:0.5, stop:0 #1a1c2c, stop:1 #0c0d12);
                border: 1.5px solid rgba(255, 255, 255, 12);
                border-radius: 24px;
            }}
            #modalSecondaryBtn {{
                background: rgba(255,255,255,8);
                color: rgba(255,255,255,180);
                border-radius: 12px;
                padding: 12px 25px;
                font-weight: 700;
                font-size: 11px;
                border: 1px solid rgba(255,255,255,10);
            }}
            #modalSecondaryBtn:hover {{ background: rgba(255,255,255,15); color: white; }}
            #modalPrimaryBtn {{
                font-size: 11px;
                letter-spacing: 1.5px;
                border: 1px solid rgba(255,255,255,20);
            }}
            #modalPrimaryBtn:hover {{ border-color: white; }}
        """)

class BlenderRenderManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        self.setWindowTitle("Lumine Render Manager")
        self.resize(1300, 850)
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setAcceptDrops(True)
        
        # Handle PyInstaller path for assets
        if hasattr(sys, '_MEIPASS'):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent.parent
            
        icon_path = base_path / "assets" / "logo.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        self.worker = None
        self.current_theme = self.settings_manager.get("theme")
        self.render_start_time = 0
        self.queue_data = [] 
        self.current_queue_index = -1
        self.is_updating_ui = False 
        self.render_mode = "Batch"
        
        self.setup_ui()
        self.load_saved_settings()
        self.apply_styles()
        self.set_mode("Batch")

    def show_notify(self, title, message):
        acc = THEMES.get(self.current_theme, THEMES["Purple"])["accent"]
        CustomModal(self, title, message, False, acc).exec()

    def show_confirm(self, title, message):
        acc = THEMES.get(self.current_theme, THEMES["Purple"])["accent"]
        modal = CustomModal(self, title, message, True, acc)
        return modal.exec() == QDialog.DialogCode.Accepted

    def setup_ui(self):
        self.container = QWidget(objectName="mainContainer")
        self.setCentralWidget(self.container)
        
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- TOP TITLE BAR ---
        self.title_bar = QFrame(objectName="titleBar")
        self.title_bar.setFixedHeight(70)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(25, 0, 25, 0)
        
        app_title = QLabel("LUMINE", objectName="appTitle")
        title_layout.addWidget(app_title)
        
        title_layout.addStretch()
        
        # New "Pill" Mode Selector
        self.mode_container = QFrame(objectName="modePill")
        self.mode_container.setFixedSize(220, 42)
        mode_l = QHBoxLayout(self.mode_container)
        mode_l.setContentsMargins(4, 4, 4, 4)
        mode_l.setSpacing(0)
        
        self.btn_batch = QPushButton("BATCH")
        self.btn_batch.setCheckable(True)
        self.btn_batch.setChecked(True)
        self.btn_batch.setObjectName("pillBtn")
        self.btn_batch.clicked.connect(lambda: self.set_mode("Batch"))
        
        self.btn_single = QPushButton("SINGLE")
        self.btn_single.setCheckable(True)
        self.btn_single.setObjectName("pillBtn")
        self.btn_single.clicked.connect(lambda: self.set_mode("Single"))
        
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.btn_batch)
        self.mode_group.addButton(self.btn_single)
        
        mode_l.addWidget(self.btn_batch)
        mode_l.addWidget(self.btn_single)
        title_layout.addWidget(self.mode_container)
        
        title_layout.addStretch()

        self.btn_app_settings = QPushButton("\U00002699")
        self.btn_app_settings.setFixedSize(35, 35)
        self.btn_app_settings.setObjectName("iconBtn")
        self.btn_app_settings.clicked.connect(self.toggle_settings_page)
        title_layout.addWidget(self.btn_app_settings)
        
        title_layout.addSpacing(15)
        
        self.btn_minimize = QPushButton("\U00002013", objectName="winCtrlBtn")
        self.btn_minimize.clicked.connect(self.showMinimized)
        self.btn_close = QPushButton("\U00002715", objectName="winCtrlBtnClose")
        self.btn_close.clicked.connect(self.close)
        
        title_layout.addWidget(self.btn_minimize)
        title_layout.addWidget(self.btn_close)
        
        self.main_layout.addWidget(self.title_bar)

        self.content_stack = QStackedWidget()
        self.main_layout.addWidget(self.content_stack)

        # PAGE 1: WORKSPACE
        self.page_workspace = QWidget()
        workspace_layout = QHBoxLayout(self.page_workspace)
        workspace_layout.setContentsMargins(25, 25, 25, 25)
        workspace_layout.setSpacing(25)

        # LEFT: QUEUE
        self.queue_panel = QFrame(objectName="glassPanel")
        queue_layout = QVBoxLayout(self.queue_panel)
        queue_layout.setContentsMargins(20, 25, 20, 25)
        queue_layout.addWidget(QLabel("RENDER QUEUE", objectName="headerLabel"))
        
        self.queue_list = QListWidget(objectName="queueList")
        self.queue_list.currentRowChanged.connect(self.on_queue_selection_changed)
        queue_layout.addWidget(self.queue_list)
        
        queue_actions = QHBoxLayout()
        self.btn_add = QPushButton("+ ADD PROJECT")
        self.btn_add.setObjectName("secondaryBtn")
        self.btn_add.clicked.connect(self.browse_and_add)
        self.btn_clear = QPushButton("CLEAR")
        self.btn_clear.setObjectName("secondaryBtn")
        self.btn_clear.clicked.connect(self.clear_queue_confirm)
        queue_actions.addWidget(self.btn_add)
        queue_actions.addWidget(self.btn_clear)
        queue_layout.addLayout(queue_actions)
        workspace_layout.addWidget(self.queue_panel, 2)

        # CENTER: SETTINGS
        settings_panel = QFrame(objectName="glassPanel")
        self.config_layout = QVBoxLayout(settings_panel)
        self.config_layout.setContentsMargins(25, 30, 25, 30)
        self.config_layout.setSpacing(20)
        
        self.config_layout.addWidget(QLabel("CONFIGURATION", objectName="headerLabel"))
        
        self.blend_file = self.add_input_row(self.config_layout, "Project File (.blend):", "Select project", "*.blend")
        self.blender_path = self.add_input_row(self.config_layout, "Blender Executable:", "Select blender.exe", "*.exe")
        self.output_folder = self.add_input_row(self.config_layout, "Output Directory:", "Select folder", is_dir=True)

        grid = QGridLayout()
        grid.setSpacing(15)
        grid.addWidget(QLabel("Resolution:"), 0, 0)
        self.res_combo = QComboBox()
        self.res_combo.addItems(["1920x1080", "2560x1440", "3840x2160", "7680x4320"])
        grid.addWidget(self.res_combo, 0, 1)
        grid.addWidget(QLabel("FPS:"), 0, 2)
        self.fps_input = QLineEdit("30")
        grid.addWidget(self.fps_input, 0, 3)
        grid.addWidget(QLabel("Samples:"), 1, 0)
        self.samples_input = QLineEdit("128")
        grid.addWidget(self.samples_input, 1, 1)
        grid.addWidget(QLabel("Device:"), 1, 2)
        self.device_combo = QComboBox()
        self.device_combo.addItems(["OPTIX", "CUDA", "CPU"])
        grid.addWidget(self.device_combo, 1, 3)
        grid.addWidget(QLabel("Frames:"), 2, 0)
        f_layout = QHBoxLayout()
        self.start_input = QLineEdit("1")
        self.end_input = QLineEdit("100")
        f_layout.addWidget(self.start_input)
        f_layout.addWidget(QLabel("-", styleSheet="color: rgba(255,255,255,0.3);"))
        f_layout.addWidget(self.end_input)
        grid.addLayout(f_layout, 2, 1)
        grid.addWidget(QLabel("Format:"), 2, 2)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPEG", "OPEN_EXR"])
        grid.addWidget(self.format_combo, 2, 3)
        self.config_layout.addLayout(grid)

        # Sync listeners
        for w in [self.res_combo, self.device_combo, self.format_combo]:
            w.currentIndexChanged.connect(self.sync_current_item_settings)
        for w in [self.fps_input, self.samples_input, self.start_input, self.end_input, self.blend_file, self.blender_path, self.output_folder]:
            w.textChanged.connect(self.sync_current_item_settings)

        self.config_layout.addStretch()
        self.start_btn = QPushButton("EXECUTE RENDER", objectName="startBtn")
        self.start_btn.clicked.connect(self.handle_render_trigger)
        self.config_layout.addWidget(self.start_btn)
        self.abort_btn = QPushButton("ABORT RENDER", objectName="abortBtn")
        self.abort_btn.setEnabled(False)
        self.abort_btn.clicked.connect(self.stop_render)
        self.config_layout.addWidget(self.abort_btn)
        workspace_layout.addWidget(settings_panel, 3)

        # RIGHT: MONITOR
        monitor_panel = QFrame(objectName="glassPanel")
        monitor_layout = QVBoxLayout(monitor_panel)
        monitor_layout.setContentsMargins(20, 25, 20, 25)
        monitor_layout.addWidget(QLabel("LIVE MONITOR", objectName="headerLabel"))
        self.log_display = QTextEdit(objectName="logDisplay", readOnly=True)
        self.log_display.setMinimumHeight(300)
        monitor_layout.addWidget(self.log_display)
        
        prog_v_layout = QVBoxLayout()
        prog_v_layout.setSpacing(12)
        prog_v_layout.setContentsMargins(0, 10, 0, 0)
        
        self.batch_label = QLabel("Batch Progress: 0/0")
        prog_v_layout.addWidget(self.batch_label)
        self.batch_progress = QProgressBar()
        prog_v_layout.addWidget(self.batch_progress)
        
        self.current_label = QLabel("Task Progress:")
        prog_v_layout.addWidget(self.current_label)
        self.current_progress = QProgressBar()
        prog_v_layout.addWidget(self.current_progress)
        
        self.status_label = QLabel("Status: Ready", objectName="statusLabel")
        prog_v_layout.addWidget(self.status_label)
        monitor_layout.addLayout(prog_v_layout)
        workspace_layout.addWidget(monitor_panel, 3)

        self.content_stack.addWidget(self.page_workspace)
        self.setup_app_settings_page()

    def setup_app_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(60, 40, 60, 60)
        layout.setSpacing(30)
        
        tg_frame = QFrame(objectName="glassPanel")
        tg_l = QVBoxLayout(tg_frame)
        tg_l.setContentsMargins(30, 30, 30, 30)
        tg_l.addWidget(QLabel("TELEGRAM INTEGRATION", objectName="headerLabel"))
        tg_grid = QGridLayout()
        tg_grid.setSpacing(15)
        tg_grid.addWidget(QLabel("Bot Token:"), 0, 0)
        self.bot_token_input = QLineEdit()
        self.bot_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        tg_grid.addWidget(self.bot_token_input, 0, 1)
        tg_grid.addWidget(QLabel("Chat ID:"), 1, 0)
        self.chat_id_input = QLineEdit()
        tg_grid.addWidget(self.chat_id_input, 1, 1)
        tg_l.addLayout(tg_grid)
        
        test_btn = QPushButton("TEST CONNECTION")
        test_btn.setObjectName("secondaryBtn")
        test_btn.clicked.connect(self.test_telegram)
        tg_l.addWidget(test_btn)
        layout.addWidget(tg_frame)
        
        theme_frame = QFrame(objectName="glassPanel")
        th_l = QVBoxLayout(theme_frame)
        th_l.setContentsMargins(30, 30, 30, 30)
        th_l.addWidget(QLabel("INTERFACE PREFERENCES", objectName="headerLabel"))
        row = QHBoxLayout()
        row.addWidget(QLabel("Global Accent Color:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(self.current_theme)
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        row.addWidget(self.theme_combo)
        th_l.addLayout(row)
        layout.addWidget(theme_frame)
        
        layout.addStretch()
        save_btn = QPushButton("APPLY & SAVE PREFERENCES")
        save_btn.setObjectName("startBtn")
        save_btn.clicked.connect(self.save_all_settings)
        layout.addWidget(save_btn)
        self.content_stack.addWidget(page)

    def toggle_settings_page(self):
        new_idx = 1 if self.content_stack.currentIndex() == 0 else 0
        self.content_stack.setCurrentIndex(new_idx)
        icon = "\U00002190" if new_idx == 1 else "\U00002699"
        self.btn_app_settings.setText(icon)

    def set_mode(self, mode):
        self.render_mode = mode
        is_batch = mode == "Batch"
        self.queue_panel.setVisible(is_batch)
        self.batch_progress.setVisible(is_batch)
        self.batch_label.setVisible(is_batch)
        self.blend_file.container.setVisible(not is_batch)
        
        self.page_workspace.layout().setStretch(0, 2 if is_batch else 0)
        self.page_workspace.layout().setStretch(1, 3)
        self.page_workspace.layout().setStretch(2, 3)
        
        self.status_label.setText(f"Status: Mode set to {mode}")

    def add_input_row(self, layout, label, title, filter_str="", is_dir=False):
        container = QWidget()
        l_layout = QVBoxLayout(container)
        l_layout.setContentsMargins(0, 0, 0, 0)
        l_layout.setSpacing(5)
        l = QLabel(label)
        l.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 11px; font-weight: 700; margin-left: 5px;")
        l_layout.addWidget(l)
        row = QHBoxLayout()
        edit = QLineEdit()
        btn = QPushButton("\U0001F4C2")
        btn.setObjectName("browseBtn")
        btn.setFixedSize(36, 36)
        def browse():
            if is_dir: path = QFileDialog.getExistingDirectory(self, title)
            else: path, _ = QFileDialog.getOpenFileName(self, title, "", filter_str)
            if path: edit.setText(os.path.normpath(path))
        btn.clicked.connect(browse)
        row.addWidget(edit)
        row.addWidget(btn)
        l_layout.addLayout(row)
        layout.addWidget(container)
        edit.container = container 
        return edit

    def browse_and_add(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Add Projects", "", "*.blend")
        for path in paths: self.add_to_queue(os.path.normpath(path))

    def add_to_queue(self, file_path):
        if any(item["path"] == file_path for item in self.queue_data): return
        
        item_settings = {
            "blender_path": self.blender_path.text(),
            "output_folder": self.output_folder.text(),
            "resolution": self.res_combo.currentText(),
            "fps": self.fps_input.text(),
            "samples": self.samples_input.text(),
            "start_frame": self.start_input.text(),
            "end_frame": self.end_input.text(),
            "device": self.device_combo.currentText(),
            "format": self.format_combo.currentText()
        }
        
        self.queue_data.append({"path": file_path, "settings": item_settings})
        li = QListWidgetItem(Path(file_path).name)
        li.setToolTip(file_path)
        self.queue_list.addItem(li)
        self.queue_list.setCurrentRow(self.queue_list.count() - 1)

    def on_queue_selection_changed(self, index):
        if index < 0 or index >= len(self.queue_data) or self.is_updating_ui: return
        self.is_updating_ui = True
        s = self.queue_data[index]["settings"]
        self.blender_path.setText(s["blender_path"])
        self.output_folder.setText(s["output_folder"])
        self.res_combo.setCurrentText(s["resolution"])
        self.fps_input.setText(s["fps"])
        self.samples_input.setText(s["samples"])
        self.start_input.setText(s["start_frame"])
        self.end_input.setText(s["end_frame"])
        self.device_combo.setCurrentText(s["device"])
        self.format_combo.setCurrentText(s["format"])
        self.is_updating_ui = False

    def sync_current_item_settings(self):
        if self.is_updating_ui or self.render_mode != "Batch": return
        idx = self.queue_list.currentRow()
        if idx < 0: return
        self.queue_data[idx]["settings"] = {
            "blender_path": self.blender_path.text(),
            "output_folder": self.output_folder.text(),
            "resolution": self.res_combo.currentText(),
            "fps": self.fps_input.text(),
            "samples": self.samples_input.text(),
            "start_frame": self.start_input.text(),
            "end_frame": self.end_input.text(),
            "device": self.device_combo.currentText(),
            "format": self.format_combo.currentText()
        }

    def clear_queue_confirm(self):
        if self.worker: return
        if self.show_confirm("Clear Queue", "Are you sure you want to remove all projects?"):
            self.queue_data.clear()
            self.queue_list.clear()

    def apply_styles(self):
        palette = THEMES.get(self.current_theme, THEMES["Purple"])
        self.setStyleSheet(get_stylesheet(self.current_theme, palette))

    def load_saved_settings(self):
        m = self.settings_manager
        self.blender_path.setText(m.get("blender_path"))
        self.output_folder.setText(m.get("output_folder"))
        self.bot_token_input.setText(m.get("bot_token"))
        self.chat_id_input.setText(m.get("chat_id"))
        self.res_combo.setCurrentText(m.get("resolution"))
        self.fps_input.setText(m.get("fps"))
        self.samples_input.setText(m.get("samples"))
        self.start_input.setText(m.get("start_frame"))
        self.end_input.setText(m.get("end_frame"))
        self.device_combo.setCurrentText(m.get("device"))
        self.format_combo.setCurrentText(m.get("format"))

    def save_all_settings(self):
        data = {
            "blender_path": self.blender_path.text(),
            "output_folder": self.output_folder.text(),
            "theme": self.theme_combo.currentText(),
            "bot_token": self.bot_token_input.text(),
            "chat_id": self.chat_id_input.text(),
            "resolution": self.res_combo.currentText(),
            "fps": self.fps_input.text(),
            "samples": self.samples_input.text(),
            "start_frame": self.start_input.text(),
            "end_frame": self.end_input.text(),
            "device": self.device_combo.currentText(),
            "format": self.format_combo.currentText()
        }
        self.settings_manager.save(data)
        self.show_notify("Settings Saved", "Preferences have been applied and stored.")

    def change_theme(self, t):
        self.current_theme = t
        self.apply_styles()

    def test_telegram(self):
        t, c = self.bot_token_input.text(), self.chat_id_input.text()
        if not t or not c: 
            self.show_notify("Error", "Enter bot token and chat ID first.")
            return
        try:
            import urllib.request, urllib.parse
            u = f"https://api.telegram.org/bot{t}/sendMessage"
            d = urllib.parse.urlencode({'chat_id': c, 'text': "Test from Lumine Manager!"}).encode('utf-8')
            urllib.request.urlopen(urllib.request.Request(u, data=d), timeout=10)
            self.show_notify("Success", "Test notification sent successfully!")
        except Exception as e: self.show_notify("Connection Failed", str(e))

    def handle_render_trigger(self):
        if self.render_mode == "Single":
            p = self.blend_file.text()
            if not p: return self.show_notify("Error", "Select a project file first!")
            self.queue_data = [{"path": p, "settings": self.get_ui_settings()}]
        elif not self.queue_data:
            return self.show_notify("Error", "The batch queue is empty.")
        
        self.current_queue_index = 0
        self.batch_progress.setMaximum(len(self.queue_data))
        self.batch_progress.setValue(0)
        self.start_btn.setEnabled(False)
        self.abort_btn.setEnabled(True)
        self.process_next_item()

    def get_ui_settings(self):
        return {
            "blender_path": self.blender_path.text(),
            "output_folder": self.output_folder.text(),
            "resolution": self.res_combo.currentText(),
            "fps": self.fps_input.text(),
            "samples": self.samples_input.text(),
            "start_frame": self.start_input.text(),
            "end_frame": self.end_input.text(),
            "device": self.device_combo.currentText(),
            "format": self.format_combo.currentText()
        }

    def process_next_item(self):
        if self.current_queue_index >= len(self.queue_data):
            return self.finalize_batch("Completed")
            
        item = self.queue_data[self.current_queue_index]
        s = item["settings"]
        
        import tempfile
        script_path = Path(tempfile.gettempdir()) / f"lum_script_{int(time.time())}.py"
        with open(script_path, "w", encoding='utf-8') as f:
            f.write(self.generate_script_logic(s))

        tg = {"bot_token": self.bot_token_input.text(), "chat_id": self.chat_id_input.text()}
        log_path = Path(s["output_folder"]) / f"log_{Path(item['path']).stem}.log"
        cmd = [s["blender_path"], "--background", item["path"], "--python", str(script_path)]

        self.log_display.clear()
        self.current_progress.setValue(0)
        self.status_label.setText(f"Status: Rendering {Path(item['path']).name}")
        self.render_start_time = time.time()

        self.worker = RenderWorker(cmd, str(log_path), tg)
        self.worker.log_signal.connect(lambda msg: self.log_display.append(msg))
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.on_item_finished)
        self.worker.start()

    def generate_script_logic(self, s):
        res_w, res_h = map(int, s["resolution"].split('x'))
        return f"""import bpy, os
cycles_prefs = bpy.context.preferences.addons['cycles'].preferences
if '{s["device"]}' in ['OPTIX', 'CUDA']:
    cycles_prefs.compute_device_type = '{s["device"]}'
    bpy.context.scene.cycles.device = 'GPU'
    cycles_prefs.refresh_devices()
    for d in cycles_prefs.devices:
        if d.type == '{s["device"]}': d.use = True
else:
    bpy.context.scene.cycles.device = 'CPU'
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = {s["samples"]}
scene.render.fps = {s["fps"]}
scene.frame_start = {s["start_frame"]}
scene.frame_end = {s["end_frame"]}
scene.render.resolution_x = {res_w}
scene.render.resolution_y = {res_h}
scene.render.image_settings.file_format = '{s["format"]}'
outPath = r'{s["output_folder"]}'
if not os.path.exists(outPath): os.makedirs(outPath)
for idx, frame in enumerate(range(scene.frame_start, scene.frame_end + 1)):
    scene.frame_set(frame)
    scene.render.filepath = os.path.join(outPath, f'render_{{frame:04d}}')
    bpy.ops.render.render(write_still=True)
    print(f'RENDER_PROGRESS:{{idx+1}}/{{scene.frame_end - scene.frame_start + 1}}', flush=True)
"""

    def update_progress(self, curr, total):
        p = int((curr / total) * 100)
        self.current_progress.setValue(p)
        elapsed = time.time() - self.render_start_time
        if curr > 0:
            eta = (elapsed / curr) * (total - curr)
            self.status_label.setText(f"Status: ({p}%) | ETA: {self.format_time(eta)}")

    def format_time(self, s):
        if s > 3600: return f"{int(s//3600)}h {int((s%3600)//60)}m"
        return f"{int(s//60)}m {int(s%60)}s"

    def on_item_finished(self, code, status):
        self.current_queue_index += 1
        self.batch_progress.setValue(self.current_queue_index)
        self.batch_label.setText(f"Batch Progress: {self.current_queue_index}/{len(self.queue_data)}")
        if status == "Aborted": self.finalize_batch("Aborted")
        else: self.process_next_item()

    def finalize_batch(self, s):
        self.start_btn.setEnabled(True)
        self.abort_btn.setEnabled(False)
        self.status_label.setText(f"Status: {s}")
        self.worker = None
        self.show_notify("Lumine Render", f"Processing has {s.lower()} successfully.")

    def stop_render(self):
        if self.worker:
            self.worker.stop()
            self.status_label.setText("Status: Aborting...")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'drag_pos'):
            delta = event.globalPosition().toPoint() - self.drag_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.drag_pos = event.globalPosition().toPoint()

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = BlenderRenderManager()
    window.show()
    sys.exit(app.exec())
