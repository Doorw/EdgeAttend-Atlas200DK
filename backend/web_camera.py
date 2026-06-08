import requests
from PIL import Image
from io import BytesIO
import cv2
import numpy as np

# Atlas200DK 摄像头服务地址
URL = "http://192.168.0.2:7000/snapshot"


def take_picture():
    try:
        # 开发板 camera_server.py 提供的是普通 HTTP 图片接口，用 GET 即可
        response = requests.get(URL, timeout=40)

        if response.status_code != 200:
            print(f"Failed to retrieve image, status code: {response.status_code}")
            print(response.text[:300])
            return False, None

        # 将响应内容解析为图片
        image = Image.open(BytesIO(response.content)).convert("RGB")

        # PIL -> numpy
        image_np = np.array(image)

        # 调整尺寸，保持你原来的 640x480
        img_resized = cv2.resize(image_np, (640, 480))

        # RGB -> BGR，供 OpenCV / 后续人脸识别使用
        image_bgr = cv2.cvtColor(img_resized, cv2.COLOR_RGB2BGR)

        return True, image_bgr

    except Exception as e:
        print(f"Failed to retrieve image from Atlas200DK camera: {e}")
        return False, None


# 单独测试用
if __name__ == "__main__":
    success, image = take_picture()
    print("success:", success)

    if success:
        print("image shape:", image.shape)
        cv2.imshow("Atlas Camera Image", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()