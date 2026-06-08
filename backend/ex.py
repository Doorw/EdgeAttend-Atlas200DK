from api import FaceRecognitionSystem
import time
import cv2
from threading import Thread
# 初始化系统
frs = FaceRecognitionSystem()

# 注册回调函数
def on_progress(p):
    print(f"当前进度: {p*100:.1f}%")

def on_result(r):
    print(f"识别结果: {r}")

def on_frame(frame):
    cv2.imshow('Live', frame)
    cv2.waitKey(1)

frs.register_callback('progress', on_progress)
frs.register_callback('result', on_result)
frs.register_callback('frame', on_frame)

# 开始录入人脸（非阻塞）
#frs.enroll_face(samples=50)

# # 开始识别人脸（非阻塞） 
frs.recognize_face()
# 同步获取状态
def get_status():
    while True:
        print(f"当前进度: {frs.get_progress()}, 最近结果: {frs.get_result()}")
        time.sleep(1)
Thread(target=get_status).start()
def get_image():
    while True:
        image = frs.get_current_frame()
        if image is not None:
            cv2.imshow('Live', image)
            cv2.waitKey(1)
        else:
            time.sleep(0.2)
        
Thread(target=get_image).start()

# 释放资源
frs.release()