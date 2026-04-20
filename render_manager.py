import sys
import os
import subprocess
import time
import json
import urllib.request
import urllib.parse
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar, 
    QTextEdit, QFileDialog, QFrame, QGridLayout, QStackedWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon

class SettingsManager:
    def __init__(self, filename="settings.json"):
        self.filename = filename
        self.defaults = {
            "blender_path": "",
            "blend_file": "",
            "output_folder": "",
            "theme": "Purple",
            "bot_token": "",
            "chat_id": ""
        }
        self.settings = self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    return {**self.defaults, **data}
            except:
                pass
        return self.defaults.copy()

    def save(self, data):
        self.settings.update(data)
        with open(self.filename, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get(self, key):
        return self.settings.get(key, self.defaults.get(key))

class RenderWorker(QThread):
    log_signal = pyqtSignal(str, bool)
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal(int, str) # return code, status_message

    def __init__(self, command, log_path, telegram_settings):
        super().__init__()
        self.command = command
        self.log_path = log_path
        self.telegram_settings = telegram_settings
        self.process = None

    def run(self):
        try:
            with open(self.log_path, "w") as log_file:
                self.process = subprocess.Popen(
                    self.command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )

                for line in self.process.stdout:
                    line = line.strip()
                    if line:
                        self.log_signal.emit(line, False)
                        log_file.write(line + "\n")
                        log_file.flush()
                        
                        if "RENDER_PROGRESS:" in line:
                            try:
                                progress_part = line.split("RENDER_PROGRESS:")[1].strip()
                                current, total = map(int, progress_part.split("/"))
                                self.progress_signal.emit(current, total)
                            except:
                                pass

                self.process.wait()
                
                status = "Success" if self.process.returncode == 0 else "Failed"
                if self.process.returncode == -15: status = "Aborted"
                
                self.send_telegram(f"Render {status}! Code: {self.process.returncode}")
                self.finished_signal.emit(self.process.returncode, status)

        except Exception as e:
            self.log_signal.emit(f"WORKER ERROR: {str(e)}", True)
            self.finished_signal.emit(-1, "Error")

    def stop(self):
        if self.process:
            self.process.terminate()

    def send_telegram(self, message):
        token = self.telegram_settings.get("bot_token")
        chat_id = self.telegram_settings.get("chat_id")
        if token and chat_id:
            try:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                data = urllib.parse.urlencode({'chat_id': chat_id, 'text': message}).encode('utf-8')
                request = urllib.request.Request(url, data=data)
                urllib.request.urlopen(request)
            except Exception as e:
                print(f"Telegram failed: {e}")

class BlenderRenderManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        self.setWindowTitle("Lumine Render Manager")
        self.resize(1200, 800)
        
        # Set Window Icon
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.worker = None
        self.themes = {
            "Blue": {"accent": "#4cc9f0", "glow": "rgba(76, 201, 240, 40)"},
            "Pink": {"accent": "#f72585", "glow": "rgba(247, 37, 133, 40)"},
            "Green": {"accent": "#06d6a0", "glow": "rgba(6, 214, 160, 40)"},
            "Orange": {"accent": "#fb8500", "glow": "rgba(251, 133, 0, 40)"},
            "Purple": {"accent": "#7209b7", "glow": "rgba(114, 9, 183, 40)"}
        }
        
        self.current_theme = self.settings_manager.get("theme")
        self.setup_ui()
        self.load_saved_settings()
        self.apply_styles()

    def setup_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # MAIN LAYOUT
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(0)

        # STACKED WIDGET
        self.pages = QStackedWidget()
        self.main_layout.addWidget(self.pages)

        # PAGE 1: RENDER
        self.page_render = QWidget()
        render_layout = QHBoxLayout(self.page_render)
        render_layout.setContentsMargins(10, 10, 10, 10)
        render_layout.setSpacing(15)

        # LEFT: Configuration
        self.left_panel = QFrame()
        self.left_panel.setObjectName("glassPanel")
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(25, 25, 25, 25)
        self.left_layout.setSpacing(20)

        # Header with Settings Icon
        header_layout = QHBoxLayout()
        header_label = QLabel("RENDER CONFIGURATION", objectName="headerLabel")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        self.btn_settings = QPushButton("\U00002699") # Gear icon
        self.btn_settings.setFixedSize(30, 30)
        self.btn_settings.setObjectName("iconBtn")
        self.btn_settings.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        header_layout.addWidget(self.btn_settings)
        
        self.left_layout.addLayout(header_layout)
        self.blender_path = self.add_input_row(self.left_layout, "Blender Exe:", "Select blender.exe", "*.exe")
        self.blend_file = self.add_input_row(self.left_layout, "Project File:", "Select .blend file", "*.blend")
        self.output_folder = self.add_input_row(self.left_layout, "Output Folder:", "Select folder", is_dir=True)

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

        grid.addWidget(QLabel("Start Frame:"), 2, 0)
        self.start_input = QLineEdit("1")
        grid.addWidget(self.start_input, 2, 1)

        grid.addWidget(QLabel("End Frame:"), 2, 2)
        self.end_input = QLineEdit("100")
        grid.addWidget(self.end_input, 2, 3)

        grid.addWidget(QLabel("Device:"), 3, 0)
        self.device_combo = QComboBox()
        self.device_combo.addItems(["OPTIX", "CUDA", "CPU"])
        grid.addWidget(self.device_combo, 3, 1)

        grid.addWidget(QLabel("Format:"), 3, 2)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPEG", "OPEN_EXR"])
        grid.addWidget(self.format_combo, 3, 3)
        self.left_layout.addLayout(grid)
        self.left_layout.addStretch()

        self.start_btn = QPushButton("START RENDER", objectName="startBtn")
        self.start_btn.clicked.connect(self.start_render)
        self.left_layout.addWidget(self.start_btn)

        self.abort_btn = QPushButton("ABORT RENDER", objectName="abortBtn")
        self.abort_btn.setEnabled(False)
        self.abort_btn.clicked.connect(self.stop_render)
        self.left_layout.addWidget(self.abort_btn)

        # RIGHT: Monitoring
        self.right_panel = QFrame()
        self.right_panel.setObjectName("glassPanel")
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(25, 25, 25, 25)
        right_layout.addWidget(QLabel("RENDER MONITOR", objectName="headerLabel"))
        
        self.log_display = QTextEdit(objectName="logDisplay", readOnly=True)
        right_layout.addWidget(self.log_display)
        
        self.progress_bar = QProgressBar()
        right_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Status: Idle", objectName="statusLabel")
        right_layout.addWidget(self.status_label)

        render_layout.addWidget(self.left_panel, 2)
        render_layout.addWidget(self.right_panel, 3)
        self.pages.addWidget(self.page_render)

        # PAGE 2: SETTINGS
        self.page_settings = QWidget()
        settings_layout = QVBoxLayout(self.page_settings)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        settings_layout.setSpacing(20)

        # Back Button
        back_btn = QPushButton("\U00002190 Back to Render", objectName="iconBtn")
        back_btn.setFixedWidth(150)
        back_btn.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        settings_layout.addWidget(back_btn)

        # Telegram Section
        tg_frame = QFrame(objectName="glassPanel")
        tg_layout = QVBoxLayout(tg_frame)
        tg_layout.setContentsMargins(20, 20, 20, 20)
        tg_layout.addWidget(QLabel("TELEGRAM NOTIFICATION", objectName="headerLabel"))
        
        tg_grid = QGridLayout()
        tg_grid.addWidget(QLabel("Bot Token:"), 0, 0)
        self.bot_token_input = QLineEdit()
        self.bot_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        tg_grid.addWidget(self.bot_token_input, 0, 1)
        
        tg_grid.addWidget(QLabel("Chat ID:"), 1, 0)
        self.chat_id_input = QLineEdit()
        tg_grid.addWidget(self.chat_id_input, 1, 1)
        tg_layout.addLayout(tg_grid)

        test_tg_btn = QPushButton("Test Telegram Connection", objectName="secondaryBtn")
        test_tg_btn.clicked.connect(self.test_telegram)
        tg_layout.addWidget(test_tg_btn)
        settings_layout.addWidget(tg_frame)

        # Theme Section
        theme_frame = QFrame(objectName="glassPanel")
        theme_layout = QVBoxLayout(theme_frame)
        theme_layout.setContentsMargins(20, 20, 20, 20)
        theme_layout.addWidget(QLabel("UI PREFERENCES", objectName="headerLabel"))
        
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Primary Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(self.themes.keys()))
        self.theme_combo.setCurrentText(self.current_theme)
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        theme_row.addWidget(self.theme_combo)
        theme_layout.addLayout(theme_row)
        settings_layout.addWidget(theme_frame)

        # About Me Section
        about_frame = QFrame(objectName="glassPanel")
        about_layout = QVBoxLayout(about_frame)
        about_layout.setContentsMargins(20, 20, 20, 20)
        about_layout.addWidget(QLabel("ABOUT MANAGER", objectName="headerLabel"))
        about_text = QLabel("Lumine Render Manager v2.0\nCreated by BramszsVisual\n\nA professional rendering workflow automation tool powered by PyQt6 and Blender API.")
        about_text.setWordWrap(True)
        about_text.setStyleSheet("color: rgba(255,255,255,200); font-size: 14px; line-height: 1.5;")
        about_layout.addWidget(about_text)
        settings_layout.addWidget(about_frame)
        
        settings_layout.addStretch()
        
        save_settings_btn = QPushButton("SAVE ALL SETTINGS", objectName="startBtn")
        save_settings_btn.clicked.connect(self.save_all_settings)
        settings_layout.addWidget(save_settings_btn)

        self.pages.addWidget(self.page_settings)

        # Nav Connections Removal (Replaced by inline lambdas)

    def add_input_row(self, parent_layout, label_text, dialog_title, filter_str="", is_dir=False):
        container = QVBoxLayout()
        container.addWidget(QLabel(label_text))
        row = QHBoxLayout()
        line_edit = QLineEdit()
        btn = QPushButton("\U0001F4C1", objectName="browseBtn")
        btn.setFixedWidth(40)
        
        def browse():
            if is_dir:
                path = QFileDialog.getExistingDirectory(self, dialog_title)
            else:
                path, _ = QFileDialog.getOpenFileName(self, dialog_title, "", filter_str)
            if path: line_edit.setText(os.path.normpath(path))

        btn.clicked.connect(browse)
        row.addWidget(line_edit)
        row.addWidget(btn)
        container.addLayout(row)
        parent_layout.addLayout(container)
        return line_edit

    def apply_styles(self):
        palette = self.themes[self.current_theme]
        acc = palette["accent"]
        glow = palette["glow"]

        # navBtn removal
        # iconBtn added
        # glassPanel update
        qss = f"""
        QMainWindow, QStackedWidget {{
            background-color: #0c0d12;
            background: qradialgradient(cx:0.2, cy:0.2, radius:0.8, fx:0.2, fy:0.2, stop:0 {glow}, stop:1 transparent),
                        qradialgradient(cx:0.8, cy:0.8, radius:0.8, fx:0.8, fy:0.8, stop:0 rgba(76, 201, 240, 20), stop:1 transparent),
                        qradialgradient(cx:0.5, cy:0.5, radius:1.2, fx:0.5, fy:0.5, stop:0 #0c0d12, stop:1 #1a1c2c);
        }}
        #iconBtn {{
            background-color: rgba(255, 255, 255, 20);
            border-radius: 8px;
            font-size: 16px;
            color: white;
            padding: 5px;
        }}
        #iconBtn:hover {{
            background-color: rgba(255, 255, 255, 40);
        }}
        #glassPanel {{
            background-color: rgba(255, 255, 255, 12);
            border: 1px solid rgba(255, 255, 255, 25);
            border-top: 1px solid rgba(255, 255, 255, 50);
            border-radius: 20px;
        }}
        #headerLabel {{
            font-size: 18px;
            font-weight: 800;
            color: white;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        QLabel {{ color: rgba(255, 255, 255, 180); font-size: 13px; }}
        QLineEdit, QComboBox {{
            background-color: rgba(0, 0, 0, 50);
            border: 1px solid rgba(255, 255, 255, 20);
            border-radius: 8px;
            padding: 10px;
            color: white;
        }}
        QLineEdit:focus, QComboBox:focus {{ border: 1px solid {acc}; }}
        #browseBtn {{
            background-color: rgba(255, 255, 255, 20);
            border-radius: 8px;
            color: white;
        }}
        #startBtn {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {acc}, stop:1 #b5179e);
            color: white; font-weight: 800; padding: 18px; border-radius: 12px;
            text-transform: uppercase; letter-spacing: 1px;
        }}
        #secondaryBtn {{
            background-color: rgba(255, 255, 255, 10);
            border: 1px solid {acc};
            color: {acc}; font-weight: bold; padding: 10px; border-radius: 8px;
        }}
        #abortBtn {{
            background-color: transparent; border: 1.5px solid rgba(220, 53, 69, 140);
            color: rgba(220, 53, 69, 220); padding: 12px; border-radius: 12px;
        }}
        #logDisplay {{
            background-color: rgba(0, 0, 0, 80); border-radius: 15px;
            color: #7fff00; font-family: 'Consolas'; font-size: 12px; padding: 10px;
        }}
        QProgressBar {{
            border: none; border-radius: 6px; background-color: rgba(255, 255, 255, 10); height: 10px;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {acc}, stop:1 white);
            border-radius: 6px;
        }}
        """
        self.setStyleSheet(qss)

    def load_saved_settings(self):
        m = self.settings_manager
        self.blender_path.setText(m.get("blender_path"))
        self.bot_token_input.setText(m.get("bot_token"))
        self.chat_id_input.setText(m.get("chat_id"))

    def save_all_settings(self):
        data = {
            "blender_path": self.blender_path.text(),
            "theme": self.theme_combo.currentText(),
            "bot_token": self.bot_token_input.text(),
            "chat_id": self.chat_id_input.text()
        }
        self.settings_manager.save(data)
        self.status_label.setText("Status: Settings Saved!")

    def change_theme(self, theme_name):
        self.current_theme = theme_name
        self.apply_styles()

    def test_telegram(self):
        token = self.bot_token_input.text()
        chat_id = self.chat_id_input.text()
        if token and chat_id:
            try:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                data = urllib.parse.urlencode({'chat_id': chat_id, 'text': "Test notification from Blender Render Manager!"}).encode('utf-8')
                request = urllib.request.Request(url, data=data)
                urllib.request.urlopen(request)
                self.status_label.setText("Status: Telegram Test Sent!")
            except Exception as e:
                self.status_label.setText(f"Status: TG Error: {str(e)[:20]}")

    def generate_script(self):
        template = """import bpy, os
device_type = '{device_input}'
cycles_prefs = bpy.context.preferences.addons['cycles'].preferences
if device_type in ['OPTIX', 'CUDA']:
    cycles_prefs.compute_device_type = device_type
    bpy.context.scene.cycles.device = 'GPU'
    cycles_prefs.refresh_devices()
    for d in cycles_prefs.devices:
        if d.type == device_type: d.use = True
else:
    bpy.context.scene.cycles.device = 'CPU'
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = {samples_input}
scene.render.fps = {fps_input}
scene.frame_start = {start_input}
scene.frame_end = {end_input}
scene.render.resolution_x = {resX_input}
scene.render.resolution_y = {resY_input}
scene.render.image_settings.file_format = '{format_input}'
outPath = r'{output_folder_input}'
if not os.path.exists(outPath): os.makedirs(outPath)
total_frames = scene.frame_end - scene.frame_start + 1
for idx, frame in enumerate(range(scene.frame_start, scene.frame_end + 1)):
    scene.frame_set(frame)
    scene.render.filepath = os.path.join(outPath, f'render_{{frame:04d}}')
    bpy.ops.render.render(write_still=True)
    print(f'RENDER_PROGRESS:{{idx+1}}/{{total_frames}}', flush=True)
"""
        res_val = self.res_combo.currentText().split('x')
        try:
            return template.format(
                device_input=self.device_combo.currentText(),
                samples_input=int(self.samples_input.text()),
                fps_input=int(self.fps_input.text()),
                start_input=int(self.start_input.text()),
                end_input=int(self.end_input.text()),
                resX_input=int(res_val[0]),
                resY_input=int(res_val[1]),
                format_input=self.format_combo.currentText(),
                output_folder_input=self.output_folder.text()
            )
        except: return None

    def start_render(self):
        blender_exe = self.blender_path.text()
        blend_file = self.blend_file.text()
        out_folder = self.output_folder.text()
        if not all([blender_exe, blend_file, out_folder]): return

        script_content = self.generate_script()
        if not script_content: return
        
        script_path = os.path.join(os.getcwd(), "temp_script.py")
        with open(script_path, "w") as f: f.write(script_content)

        tg_settings = {"bot_token": self.bot_token_input.text(), "chat_id": self.chat_id_input.text()}
        log_file_path = os.path.join(out_folder, f"render_log_{int(time.time())}.log")
        command = [blender_exe, "--background", blend_file, "--python", script_path]

        self.start_btn.setEnabled(False)
        self.abort_btn.setEnabled(True)
        self.log_display.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText("Status: Starting...")

        self.worker = RenderWorker(command, log_file_path, tg_settings)
        self.worker.log_signal.connect(lambda msg: self.log_display.append(msg))
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.render_finished)
        self.worker.start()

    def update_progress(self, current, total):
        self.progress_bar.setValue(int((current / total) * 100))
        self.status_label.setText(f"Status: Rendering {current}/{total}")

    def render_finished(self, code, status):
        self.start_btn.setEnabled(True)
        self.abort_btn.setEnabled(False)
        self.status_label.setText(f"Status: {status} ({code})")

    def stop_render(self):
        if self.worker:
            self.worker.stop()
            self.status_label.setText("Status: Aborting...")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BlenderRenderManager()
    window.show()
    sys.exit(app.exec())
