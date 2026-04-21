import json
import os
from pathlib import Path

class SettingsManager:
    def __init__(self, filename="settings.json"):
        self.filename = Path(filename)
        self.defaults = {
            "blender_path": "",
            "blend_file": "",
            "output_folder": "",
            "theme": "Purple",
            "bot_token": "",
            "chat_id": "",
            "resolution": "1920x1080",
            "fps": "30",
            "samples": "128",
            "start_frame": "1",
            "end_frame": "100",
            "device": "OPTIX",
            "format": "PNG"
        }
        self.settings = self.load()

    def load(self):
        if self.filename.exists():
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {**self.defaults, **data}
            except Exception as e:
                print(f"Error loading settings: {e}")
        return self.defaults.copy()

    def save(self, data=None):
        if data:
            self.settings.update(data)
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key):
        return self.settings.get(key, self.defaults.get(key))
