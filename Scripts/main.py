from PyQt5.QtWidgets import QApplication
from main_window import MainWindow
import sys
import subprocess
import os
import json  # 設定ファイルを読み込むために追加

if __name__ == "__main__":
    # 設定ファイルを読み込む
    config_path = os.path.join(os.path.dirname(__file__), "../config/PoseSenderApp.config")
    with open(config_path, "r") as config_file:
        config = json.load(config_file)

    # アプリ起動時にcamera_enum.exeを実行
    exe_path = os.path.join(os.path.dirname(__file__), config["camera_enum_path"])
    try:
        subprocess.run([exe_path], check=True)
    except subprocess.SubprocessError as e:
        print(f"Error running camera_enum.exe: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
