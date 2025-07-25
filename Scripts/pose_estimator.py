import cv2
import mediapipe as mp
import os  # 環境変数を設定するために追加

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

def set_mediapipe_device(device):
    global pose, face_mesh, hands
    try:
        if device == "CPU":
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # CPUを使用する設定
        else:
            os.environ["CUDA_VISIBLE_DEVICES"] = device.split(":")[-1]  # GPU名からインデックスを抽出して設定
        
        # Mediapipeインスタンスを再初期化
        pose = mp_pose.Pose(model_complexity=1)  # model_complexityはPoseクラスにのみ適用
        face_mesh = mp_face_mesh.FaceMesh()  # FaceMeshはデフォルト設定を使用
        hands = mp_hands.Hands()  # Handsもデフォルト設定を使用
    except Exception as e:
        print(f"Error initializing Mediapipe with device {device}: {e}")

def get_pose_image(frame):
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results_pose = pose.process(image)
    results_face = face_mesh.process(image)
    results_hands = hands.process(image)

    pose_data = []
    expression_data = []
    hand_data = []
    fingertip_data = []

    if results_pose.pose_landmarks:
        mp_drawing.draw_landmarks(image, results_pose.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        pose_data = [(mp_pose.PoseLandmark(i).name, lmk.x, lmk.y, lmk.z) for i, lmk in enumerate(results_pose.pose_landmarks.landmark)]

    if results_face.multi_face_landmarks:
        expression_data = [
            (f"FaceLandmark_{i}", lmk.x, lmk.y, lmk.z)
            for face_landmarks in results_face.multi_face_landmarks
            for i, lmk in enumerate(face_landmarks.landmark)
        ]
        for face_landmarks in results_face.multi_face_landmarks:
            mp_drawing.draw_landmarks(image, face_landmarks, mp_face_mesh.FACEMESH_CONTOURS)

    if results_hands.multi_hand_landmarks and results_hands.multi_handedness:
        hand_data = [
            (f"{handedness.classification[0].label}_HandLandmark_{i}", lmk.x, lmk.y, lmk.z)
            for hand_landmarks, handedness in zip(results_hands.multi_hand_landmarks, results_hands.multi_handedness)
            for i, lmk in enumerate(hand_landmarks.landmark)
        ]
        fingertip_data = [
            (f"{handedness.classification[0].label}_Fingertip_{i}", hand_landmarks.landmark[i].x, hand_landmarks.landmark[i].y, hand_landmarks.landmark[i].z)
            for hand_landmarks, handedness in zip(results_hands.multi_hand_landmarks, results_hands.multi_handedness)
            for i in [4, 8, 12, 16, 20]
        ]
        for hand_landmarks in results_hands.multi_hand_landmarks:
            for i in [4, 8, 12, 16, 20]:
                cv2.circle(image, 
                           (int(hand_landmarks.landmark[i].x * image.shape[1]), 
                            int(hand_landmarks.landmark[i].y * image.shape[0])), 
                           5, (0, 255, 0), -1)

    return image, pose_data, [expression_data], [hand_data], [fingertip_data]
