import socket
import json
import os  # 設定ファイルを読み込むために追加

# 設定ファイルを読み込む
config_path = os.path.join(os.path.dirname(__file__), "../config/PoseSenderApp.config")
with open(config_path, "r") as config_file:
    config = json.load(config_file)

def send_data(pose_data, expression_data, hand_data, fingertip_data):
    try:
        # UDPソケットを作成
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_address = (config["ip"], config["port"])  # 設定ファイルからIPとポートを取得

        # データをJSON形式に変換
        data = {
            "pose_data": pose_data,
            "expression_data": expression_data,
            "hand_data": hand_data,
            "fingertip_data": fingertip_data
        }
        json_data = json.dumps(data)

        # データを送信
        sock.sendto(json_data.encode('utf-8'), server_address)
    except Exception as e:
        print(f"Error sending data: {e}")
    finally:
        sock.close()
