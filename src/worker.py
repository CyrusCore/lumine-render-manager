import os
import subprocess
import urllib.request
import urllib.parse
from PyQt6.QtCore import QThread, pyqtSignal

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
            # Ensure output directory for log exists
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            
            with open(self.log_path, "w", encoding='utf-8') as log_file:
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
                            except (ValueError, IndexError):
                                pass

                self.process.wait()
                
                return_code = self.process.returncode
                status = "Success" if return_code == 0 else "Failed"
                # Handle abortion (SIGTERM on Linux/Mac is 15, on Windows it's 1 for terminate)
                if return_code in [-15, 1, 15]: 
                    status = "Aborted"
                
                self.send_telegram(f"Render {status}! Code: {return_code}")
                self.finished_signal.emit(return_code, status)

        except Exception as e:
            error_msg = f"WORKER ERROR: {str(e)}"
            self.log_signal.emit(error_msg, True)
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
                urllib.request.urlopen(request, timeout=10)
            except Exception as e:
                print(f"Telegram failed: {e}")
                self.log_signal.emit(f"TELEGRAM FAILED: {str(e)}", True)
