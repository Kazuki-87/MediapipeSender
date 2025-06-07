import socket
import json
import os  # 設定ファイルを読み込むために追加

# 設定ファイルを読み込む
config_path = os.path.join(os.path.dirname(__file__), "../config/PoseSenderApp.config")
with open(config_path, "r") as config_file:
    config = json.load(config_file)

def send_udp_data(pose_data, expression_data=None, hand_data=None, fingertip_data=None, ip=config["ip"], port=config["port"]):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = json.dumps({
        "pose": pose_data,
        "expression": expression_data,  # 顔のデータを送信
        "hand": hand_data,
        "fingertips": fingertip_data  # 指先データを送信
    }).encode()
    sock.sendto(message, (ip, port))
