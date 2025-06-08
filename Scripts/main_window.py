from PyQt5.QtWidgets import QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QComboBox, QCheckBox, QFileDialog
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
import cv2
import os
import subprocess  # GPU名を取得するために追加
import json  # 設定ファイルを読み込むために追加
from pose_estimator import get_pose_image, set_mediapipe_device  # 新しい関数をインポート
from udp_sender import send_data  # 修正された関数名をインポート

class MainWindow(QMainWindow):
    def __init__(self):
        # 設定ファイルを読み込む
        config_path = os.path.join(os.path.dirname(__file__), "../config/PoseSenderApp.config")
        with open(config_path, "r") as config_file:
            config = json.load(config_file)

        self.vcam_offset = config["vcam_offset"]  # VCAMオフセットを設定
        self.ip = config["ip"]  # IPを設定
        self.port = config["port"]  # ポートを設定
        self.camera_list_path = os.path.join(os.path.dirname(__file__), "../camera_list.txt")
        super().__init__()
        self.setWindowTitle("Pose Sender App")
        self.image_label = QLabel()
        self.camera_button = QPushButton("Start Camera")
        self.video_button = QPushButton("Open Video")
        self.camera_button.clicked.connect(self.toggle_camera)
        self.video_button.clicked.connect(self.open_video)

        self.camera_selector = QComboBox()
        self.populate_camera_selector()  # Dynamically populate camera list
        self.camera_selector.currentIndexChanged.connect(self.change_camera)

        self.display_resolution = (640, 480)  # 表示用の解像度
        self.resolution_selector = QComboBox()
        resolutions = ["640x480", "320x240", "640x360"]  # デフォルトサイズを最初に表示
        self.resolution_selector.addItems(resolutions)
        self.resolution_selector.setCurrentIndex(0)  # デフォルトサイズを選択
        self.resolution_selector.currentIndexChanged.connect(self.change_display_resolution)

        self.hide_camera_checkbox = QCheckBox("Hide Camera")
        self.hide_camera_checkbox.stateChanged.connect(self.toggle_camera_visibility)

        self.device_selector = QComboBox()  # CPU/GPU選択用プルダウンを追加
        self.populate_device_selector()  # GPU名を取得して表示
        self.device_selector.setCurrentIndex(0)  # デフォルトはCPU
        self.device_selector.currentIndexChanged.connect(self.change_device)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.camera_button)
        layout.addWidget(self.video_button)
        layout.addWidget(self.camera_selector)
        layout.addWidget(self.resolution_selector)
        layout.addWidget(self.hide_camera_checkbox)
        layout.addWidget(self.device_selector)  # レイアウトに追加

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

    def get_python_camera_names(self):
        # camera_list.txtを読み込んでカメラ名を取得
        if os.path.exists(self.camera_list_path):
            with open(self.camera_list_path, "r") as file:
                cameras = [line.strip() for line in file.readlines()]
            return cameras
        else:
            print("camera_list.txt not found. Falling back to OpenCV detection.")
            cameras = []
            index = 0
            while True:
                cap = cv2.VideoCapture(index + self.vcam_offset)  # VCAMオフセットを適用
                if not cap.isOpened():
                    break
                cameras.append(f"Camera {index}")
                cap.release()
                index += 1
            return cameras

    def populate_camera_selector(self):
        self.camera_selector.clear()
        python_cameras = self.get_python_camera_names()  # OpenCVで取得したカメラ名
        if not python_cameras:
            self.camera_selector.addItem("No cameras found")
        else:
            for index, name in enumerate(python_cameras):
                self.camera_selector.addItem(name)

    def populate_device_selector(self):
        self.device_selector.clear()
        self.device_selector.addItem("CPU")  # CPUを追加
        try:
            result = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                gpu_names = result.stdout.strip().split("\n")
                for gpu_name in gpu_names:
                    self.device_selector.addItem(gpu_name)  # GPU名を追加
            else:
                print(f"Error fetching GPU devices: {result.stderr}")
                print("Falling back to CPU-only mode.")
        except FileNotFoundError:
            print("nvidia-smi command not found. Ensure NVIDIA drivers are installed.")
            print("Falling back to CPU-only mode.")

    def toggle_camera(self):
        if self.cap is None:
            if self.camera_selector.currentText() == "No cameras found":
                print("No cameras available to start.")
                return
            
            # カメラ起動前にデバイス設定を適用
            selected_device = "CPU" if self.device_selector.currentIndex() == 0 else self.device_selector.currentText()
            set_mediapipe_device(selected_device)  # pose_estimator.pyに設定を渡す
            
            selected_index = self.camera_selector.currentIndex() + self.vcam_offset  # VCAMオフセットを適用
            self.cap = cv2.VideoCapture(selected_index)  # インデックスを使用してカメラを開く
            print(f"Using camera: Camera {selected_index - self.vcam_offset}")  # 選択したカメラ名を表示
            self.timer.start(30)  # フレーム更新を開始
        else:
            # カメラが起動している場合、停止
            self.timer.stop()
            self.cap.release()
            self.cap = None

    def open_video(self):
        video_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi)")
        if video_path:
            self.cap = cv2.VideoCapture(video_path)
            self.timer.start(30)

    def change_camera(self, index):
        if self.cap:
            self.cap.release()
            self.cap = cv2.VideoCapture(index + self.vcam_offset)  # VCAMオフセットを適用

    def change_display_resolution(self, index):
        resolutions = [(640, 480), (320, 240), (640, 360)]  # 表示用解像度
        self.display_resolution = resolutions[index]
        self.resize(self.display_resolution[0], self.display_resolution[1])  # ウィンドウサイズを変更
        self.image_label.setFixedSize(self.display_resolution[0], self.display_resolution[1])  # QLabelのサイズを変更

    def toggle_camera_visibility(self, state):
        self.image_label.setVisible(state == 0)

    def change_device(self, index):
        device = "CPU" if index == 0 else self.device_selector.itemText(index)  # GPU名を取得
        self.timer.stop()  # 姿勢推定を停止
        set_mediapipe_device(device)  # pose_estimator.pyに設定を渡す
        self.timer.start(30)  # 姿勢推定を再開

    def update_frame(self):
        if self.cap is None:  # self.capがNoneの場合は処理をスキップ
            return
        
        ret, frame = self.cap.read()
        if not ret:
            return
        
        # 処理用の画像
        pose_frame, pose_data, expression_data, hand_data, fingertip_data = get_pose_image(frame)  # 指先データを取得
        send_data(pose_data, expression_data[0], hand_data[0], fingertip_data[0])  # 修正された関数を使用

        # 表示用の画像（左右反転とサイズ変更）
        flipped_frame = cv2.flip(pose_frame, 1)
        resized_frame = cv2.resize(flipped_frame, self.display_resolution)  # 表示用解像度に変更
        if not self.hide_camera_checkbox.isChecked():
            image = QImage(resized_frame.data, resized_frame.shape[1], resized_frame.shape[0], QImage.Format_RGB888)
            self.image_label.setPixmap(QPixmap.fromImage(image))
