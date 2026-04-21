import sys
from PyQt6.QtWidgets import QApplication
from src.ui import BlenderRenderManager

def main():
    app = QApplication(sys.argv)
    window = BlenderRenderManager()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
