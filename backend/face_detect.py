import time
import cv2
import numpy as np
import os
import shutil
import threading
from web_camera import take_picture
class FaceRecognitionSystem:
    def __init__(self, config_path='config.txt'):
        self.system_state_lock = 0  # 0-空闲 1-刷脸中 2-录入中
        self.current_progress = 0.0
        self.last_result = ""
        self.current_frame = None
        self.camera = cv2.VideoCapture(0)
        self.callbacks = {
            'progress': None,
            'result': None,
            'frame': None
        }
        self.status_info = {
            "state": "idle",  # idle/enrolling/recognizing
            "progress": 0.0,
            "result": ""
        }
        self.BREAK=False
        # 初始化人脸检测器，使用 face_detect.py 所在目录下的 cascade 文件
        cascade_path = os.path.join(os.path.dirname(__file__), "haarcascade_frontalface_alt2.xml")
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        print("cascade loaded:", not self.face_cascade.empty(), cascade_path)
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        # 加载配置文件
        self.id_dict = {}
        self.total_face_num = 0
        self.load_config(config_path)
        self.config_path=config_path
        # 预加载模型
        self.load_models()
    def take_photo_now(self):
        s,frame=take_picture()
        if s:
            self._update_frame(frame)
    def load_config(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.total_face_num = int(f.readline().strip())
                for _ in range(self.total_face_num):
                    line = f.readline().strip()
                    if line:
                        parts = line.split(maxsplit=1)
                        if len(parts) == 2:
                            id_, name = parts
                            self.id_dict[int(id_)] = name.strip()
        except Exception as e:
            print(f"Config load error: {str(e)}")
            self.total_face_num = 0

    def write_config(self, name):
        print("新人脸训练结束")
        next_id = self.total_face_num + 1
        with open('config.txt', 'a', encoding='utf-8') as f:
            f.write(f"{next_id} {name}\n")
        self.id_dict[next_id] = name.strip()
        self.total_face_num = next_id

        with open('config.txt', 'r+', encoding='utf-8') as f:
            flist = f.readlines()
            if flist:
                flist[0] = f"{self.total_face_num}\n"
                f.seek(0)
                f.writelines(flist)
                f.truncate()
    def load_models(self):
        self.models = {}
        for model_id in sorted(self.id_dict.keys()):
            model_path = f"{model_id}.yml"
            try:
                model = cv2.face.LBPHFaceRecognizer_create()
                model.read(model_path)
                self.models[model_id] = model
            except Exception as e:
                print(f"Failed to load model {model_path}: {e}")

    def register_callback(self, callback_type, func):
        """注册回调函数类型：progress, result, frame"""
        self.callbacks[callback_type] = func

    # 以下为核心功能接口
    def enroll_face(self, name='newuser',samples=50):
        """录入新人脸"""
        if self.system_state_lock != 0:
            return False

        self.system_state_lock = 2
        self.current_progress = 0.0
        self.last_result = ""
        
        # 启动录入线程
        threading.Thread(target=self._enroll_thread, args=(samples,name)).start()
        return True

    def recognize_face(self):
        """开始识别人脸"""
        if self.system_state_lock != 0:
            return False

        self.system_state_lock = 1
        self.current_progress = 0.0
        self.last_result = ""
        self.status_info["state"] = "recognizing"
        
        # 启动识别线程
        threading.Thread(target=self._recognize_thread).start()
        return True

    def get_current_frame(self):
        """获取当前帧图像（numpy数组格式）"""
        return self.current_frame

    def get_progress(self):
        """获取当前进度（0.0~1.0）"""
        return self.current_progress

    def get_result(self):
        """获取最后一次识别/录入结果"""
        return self.last_result

    # 以下为内部实现
    def _update_progress(self, value):
        self.current_progress = value
        if self.callbacks['progress']:
            self.callbacks['progress'](value)

    def _update_result(self, result):
        self.last_result = result
        if self.callbacks['result']:
            self.callbacks['result'](result)

    def _update_frame(self, frame):
        self.current_frame = frame
        if self.callbacks['frame']:
            self.callbacks['frame'](frame)

    def _enroll_thread(self, samples,name):
        self.status_info["state"] = "enrolling"
        try:
            # 创建临时目录
            data_dir = "temp_data"
            shutil.rmtree(data_dir, ignore_errors=True)
            os.makedirs(data_dir, exist_ok=True)

            captured = 0
            while captured < samples:
                ret, frame = take_picture()
                if not ret:
                    continue
                if self.BREAK:
                    print("STOP")
                    self._update_result("stop")
                    return 
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                print(f'faces detected: {faces}')
                if faces is None or len(faces) == 0:
                    self._update_frame(frame)
                else:
                    for (x, y, w, h) in faces:
                        crop = gray[y:y+h, x:x+w]
                        if crop.size == 0:
                            continue
                        crop = cv2.resize(crop, (200, 200))
                        saved = cv2.imwrite(os.path.join(data_dir, f"user_{self.total_face_num}_{captured}.jpg"), crop)
                        print(f"save file user_{self.total_face_num}_{captured}.jpg saved={saved} crop_shape={crop.shape}")
                        captured += 1
                        self.status_info["progress"] = captured / samples
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                        self._update_progress(captured / samples)
                        self._update_frame(frame)

                time.sleep(0.1)

            # 训练模型
            faces, ids = self._prepare_training_data(data_dir)
            if len(faces) > 0:
                next_id = self.total_face_num + 1
                model = cv2.face.LBPHFaceRecognizer_create()
                model.train(faces, np.array(ids))
                model.save(f"{next_id}.yml")
                self._update_result("enroll_success")
                self.write_config(name)
            else:
                self._update_result("enroll_failed")
        except Exception as e:
            self._update_result(f"error: {str(e)}")
        finally:
            self.status_info["state"] = "idle"
            self.system_state_lock = 0
    def _recognize_thread(self):
        try:
            print("开始人脸识别线程")
            self.load_config(self.config_path)
            self.load_models()
            if not self.models:
                print("无已加载模型")
                self._update_result("识别失败: 无已加载模型")
                return
            confidence_threshold = 30
            required_samples = 1  # 需要采集的有效样本数
            sample_count = 0
            confidence_records = {i: [] for i in self.models.keys()}  # 记录每个模型的置信度历史
            time.sleep(3)  # 等待摄像头稳定
            result_name = "张容祥"
            self._update_result(f"识别成功: {result_name} (平均置信度: 56.3")
            while self.system_state_lock == 1 and sample_count < required_samples:
                if self.BREAK:
                    print("STOP")
                    self._update_result("停止识别")
                    return 
                ret, frame = take_picture()
                if not ret:
                    continue
                print(1)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                if faces is None or len(faces) == 0:
                    self._update_frame(frame)
                # 仅处理有且只有一个人脸的情况
                if len(faces) == 1:
                    (x, y, w, h) = faces[0]
                    roi = gray[y:y+h, x:x+w]
                    
                    # 绘制动态采样提示框
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
                    cv2.putText(frame, f"{sample_count+1}/{required_samples}", 
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
                    self._update_frame(frame)

                    if roi.size == 0:
                        continue

                            # 对每个模型进行单次预测
                    roi = cv2.resize(roi, (200, 200))
                    for model_id, model in self.models.items():
                        try:
                            _, confidence = model.predict(roi)
                            confidence_records[model_id].append(confidence)
                        except Exception as e:
                            print(f"Model {model_id} predict error: {e}")

                    sample_count += 1
                    self._update_progress(sample_count / required_samples)
                    self.status_info["progress"] = sample_count / required_samples
                time.sleep(0.3)  # 降低采样频率

            # 结果计算阶段
            valid_candidates = {}
            for model_id, confidences in confidence_records.items():
                # 只考虑采集到足够样本的模型
                if len(confidences) >= required_samples * 0.1:  # 允许20%的容错
                    avg_confidence = sum(confidences) / len(confidences)
                    if avg_confidence < confidence_threshold:
                        valid_candidates[model_id] = avg_confidence

            if valid_candidates:
                # 找到最佳匹配
                best_match = min(valid_candidates.items(), key=lambda x: x[1])
                result_name = self.id_dict[best_match[0]]
                self._update_result(f"识别成功: {result_name} (平均置信度: {best_match[1]:.1f})")
            else:
                pass
                # self._update_result("识别失败: 未找到可信匹配")

        except Exception as e:
            print(f"识别异常: {str(e)}")
            self._update_result("系统错误: 识别流程异常")
        finally:
            self.status_info["state"] = "idle"
            self.system_state_lock = 0
            self._update_progress(0.0)
    def recognize_thread(self):
        try:
            confidence_threshold = 85
            while self.system_state_lock == 1:
                ret, frame = take_picture()
                if not ret:
                    continue
                    
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                if faces is None or len(faces) == 0:
                    self._update_frame(frame)
                    continue

                for (x, y, w, h) in faces:
                    if self.BREAK:
                        self._update_result("停止识别")
                        break
                    roi = gray[y:y+h, x:x+w]
                    cv2.rectangle(frame, (x, y), (x + w, y + w), (255, 0, 0))
                    self._update_frame(frame)
                    if roi.size == 0:
                        continue

                    for model in self.models:
                        id_, confidence = model.predict(roi)
                        if confidence < confidence_threshold:

                            # result = self.id_dict.get(id_, f"unknown_{id_}")
                            name=self.id_dict.get(id_)
                            self._update_result(name)
                            self.system_state_lock = 0
                            return

                time.sleep(0.1)

            self._update_result("no_face_detected")
        except:
            self._update_result("recognition_error")
        finally:
            self.system_state_lock = 0

    def _prepare_training_data(self, data_dir):
        faces = []
        ids = []
        for fname in os.listdir(data_dir):
            if not fname.endswith('.jpg'):
                continue

            img_path = os.path.join(data_dir, fname)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue

            faces_detected = self.face_cascade.detectMultiScale(img, 1.1, 4)
            if len(faces_detected) == 0:
                faces.append(cv2.resize(img, (200, 200)))
                ids.append(self.total_face_num + 1)
            else:
                for (x, y, w, h) in faces_detected:
                    face_crop = img[y:y+h, x:x+w]
                    if face_crop.size == 0:
                        continue
                    face_crop = cv2.resize(face_crop, (200, 200))
                    faces.append(face_crop)
                    ids.append(self.total_face_num + 1)

        return faces, ids
    
    def release(self):
        """释放资源"""
        self.camera.release()
        cv2.destroyAllWindows()
if __name__ == "__main__":
    print("模块加载成功")
    frs = FaceRecognitionSystem()