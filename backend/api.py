import contextlib
from flask import Flask, request, jsonify
from flask_cors import CORS
import PIL.Image as Image
import numpy as np
import torch
from torch.autograd import Variable
from torchvision import transforms
from model import CANNet
from io import BytesIO
import base64
import threading
import time
import cv2
import sqlite3
from web_camera import take_picture
from face_detect import FaceRecognitionSystem

app = Flask(__name__)
CORS(app)

# 数据库初始化
def init_db():
    with contextlib.closing(connect_db()) as conn:
        conn.execute('PRAGMA foreign_keys = ON;')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS class (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_name TEXT NOT NULL,
                teacher TEXT NOT NULL,
                student_num INTEGER DEFAULT 0
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS student (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS student_class (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                class_id INTEGER,
                FOREIGN KEY(student_id) REFERENCES student(id),
                FOREIGN KEY(class_id) REFERENCES class(id)
            )
        ''')
        conn.commit()

def connect_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn

# 图像处理和模型初始化
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

model = CANNet()
model = model.cuda()
checkpoint = torch.load('model_best.pth.tar', map_location=torch.device('cuda'))
model.load_state_dict(checkpoint['state_dict'])
model.eval()

# 班级管理接口
@app.route('/classes', methods=['GET', 'POST'])
def classes_api():
    if request.method == 'POST':
        data = request.json
        with connect_db() as conn:
            conn.execute('''
                INSERT INTO class (class_name, teacher, student_num)
                VALUES (?, ?, ?)
            ''', (data['class_name'], data['teacher'], data.get('student_num', 0)))
            conn.commit()
        return jsonify({'message': '班级创建成功'}), 201

    with connect_db() as conn:
        cursor = conn.execute('SELECT * FROM class')
        return jsonify([dict(row) for row in cursor.fetchall()])

@app.route('/classes/<int:id>', methods=['PUT', 'DELETE'])
def class_operation(id):
    try:
        with connect_db() as conn:
            if request.method == 'PUT':
                data = request.json
                conn.execute('''
                    UPDATE class 
                    SET class_name=?, teacher=?, student_num=?
                    WHERE id=?
                ''', (data['class_name'], data['teacher'],
                     data.get('student_num', 0), id))
                conn.commit()
                return jsonify({'message': '班级更新成功'})

            elif request.method == 'DELETE':
                enrollments = conn.execute(
                    'SELECT id FROM student_class WHERE class_id=?',
                    (id,)
                ).fetchone()
                if enrollments:
                    return jsonify({'error': '存在关联选课记录，无法删除'}), 400

                conn.execute('DELETE FROM class WHERE id=?', (id,))
                conn.commit()
                return jsonify({'message': '班级删除成功'})

    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

# 学生管理接口
@app.route('/students', methods=['GET', 'POST'])
def students_api():
    if request.method == 'POST':
        data = request.json
        with connect_db() as conn:
            conn.execute('INSERT INTO student (name) VALUES (?)', (data['name'],))
            conn.commit()
        return jsonify({'message': '学生创建成功'}), 201

    with connect_db() as conn:
        cursor = conn.execute('SELECT * FROM student')
        return jsonify([dict(row) for row in cursor.fetchall()])

@app.route('/students/<int:id>', methods=['PUT', 'DELETE'])
def student_operation(id):
    try:
        with connect_db() as conn:
            if request.method == 'PUT':
                data = request.json
                conn.execute('''
                    UPDATE student 
                    SET name=?
                    WHERE id=?
                ''', (data['name'], id))
                conn.commit()
                return jsonify({'message': '学生信息更新成功'})

            elif request.method == 'DELETE':
                conn.execute('DELETE FROM student_class WHERE student_id=?', (id,))
                conn.execute('DELETE FROM student WHERE id=?', (id,))
                conn.commit()
                return jsonify({'message': '学生删除成功'})

    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

# 选课管理接口
@app.route('/enrollments', methods=['GET', 'POST'])
def enrollments_api():
    if request.method == 'POST':
        data = request.json
        with connect_db() as conn:
            student = conn.execute('SELECT id FROM student WHERE id=?',
                                   (data['student_id'],)).fetchone()
            cls = conn.execute('SELECT id FROM class WHERE id=?',
                               (data['class_id'],)).fetchone()

            if not student or not cls:
                return jsonify({'error': '无效的学生或班级ID'}), 400

            conn.execute('''
                INSERT INTO student_class (student_id, class_id)
                VALUES (?, ?)
            ''', (data['student_id'], data['class_id']))
            conn.commit()
        return jsonify({'message': '选课成功'}), 201

    with connect_db() as conn:
        cursor = conn.execute('''
            SELECT sc.id, s.name as student, c.class_name 
            FROM student_class sc
            JOIN student s ON sc.student_id = s.id
            JOIN class c ON sc.class_id = c.id
        ''')
        return jsonify([dict(row) for row in cursor.fetchall()])

@app.route('/enrollments/<int:id>', methods=['DELETE'])
def enrollment_operation(id):
    try:
        with connect_db() as conn:
            conn.execute('DELETE FROM student_class WHERE id=?', (id,))
            conn.commit()
            return jsonify({'message': '选课记录删除成功'})
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

# 人数预测接口
@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        file = request.files['image']
        img = Image.open(BytesIO(file.read())).convert('RGB')
        img = transform(img).cuda().unsqueeze(0)

        h, w = img.shape[2:4]
        h_d, w_d = h // 2, w // 2

        # 分块预测
        img_1 = Variable(img[:, :, :h_d, :w_d].cuda())
        img_2 = Variable(img[:, :, :h_d, w_d:].cuda())
        img_3 = Variable(img[:, :, h_d:, :w_d].cuda())
        img_4 = Variable(img[:, :, h_d:, w_d:].cuda())

        density_sum = sum(model(img).data.cpu().numpy().sum()
                          for img in [img_1, img_2, img_3, img_4])
        
        # 转换为Python原生float类型
        density_sum = float(density_sum)

        return jsonify({'predicted_count': str(round(density_sum, 2))})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/predict_class', methods=['POST'])
def predict_class():
    try:
        # 获取班级ID
        class_id = request.form.get('class_id')
        if not class_id:
            return jsonify({'error': 'Missing class ID'}), 400

        # 查询班级信息
        with connect_db() as conn:
            cursor = conn.execute(
                'SELECT student_num FROM class WHERE id = ?',
                (class_id,)
            )
            class_data = cursor.fetchone()
            if not class_data:
                return jsonify({'error': 'Class not found'}), 404
            total_students = class_data['student_num']

        # 验证学生人数
        if total_students <= 0:
            return jsonify({'error': 'Invalid student number in class'}), 400

        # 处理图像文件
        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded'}), 400

        file = request.files['image']
        img = Image.open(BytesIO(file.read())).convert('RGB')
        img = transform(img).cuda().unsqueeze(0)

        # 分块预测逻辑
        h, w = img.shape[2:4]
        h_d, w_d = h // 2, w // 2

        img_1 = Variable(img[:, :, :h_d, :w_d].cuda())
        img_2 = Variable(img[:, :, :h_d, w_d:].cuda())
        img_3 = Variable(img[:, :, h_d:, :w_d].cuda())
        img_4 = Variable(img[:, :, h_d:, w_d:].cuda())

        # 计算总密度
        density_sum = sum(model(img).data.cpu().numpy().sum()
                          for img in [img_1, img_2, img_3, img_4])
        
        # 转换为Python原生float类型，避免JSON序列化错误
        density_sum = float(density_sum)
        
        # 计算出勤率
        try:
            attendance_rate = round((density_sum / total_students) * 100, 2)
        except ZeroDivisionError:
            attendance_rate = 0.0

        return jsonify({
            'predicted_count': str(round(density_sum, 2)),
            'student_num': int(total_students),
            'attend_ratio': float(attendance_rate),
            'class_id': class_id
        })

    except Exception as e:
        app.logger.error(f'Prediction error: {str(e)}')
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


# 人脸识别相关功能
fr_system = FaceRecognitionSystem()
status_info = {"state": "idle", "progress": 0.0, "result": ""}
current_frame = None
status_lock = threading.Lock()


def init_system():
    global fr_system
    fr_system = FaceRecognitionSystem(config_path='config.txt')
    fr_system.register_callback('progress', lambda p: None)
    fr_system.register_callback('result', lambda r: None)
    fr_system.register_callback('frame', lambda f: None)


init_system()


# @app.route('/face-recognition/get_image', methods=['GET'])
# def get_image():
#     try:
#         global current_frame
#         if not current_frame:
#             _, frame = take_picture()
#             _, buffer = cv2.imencode('.jpg', frame)
#             current_frame = base64.b64encode(buffer).decode('utf-8')
#         return jsonify({
#             "image": f"data:image/jpeg;base64,{current_frame}",
#             "timestamp": time.time()
#         })
#     except Exception as e:
#         return jsonify({"error": str(e), "code": 500}), 500

@app.route('/face-recognition/get_image', methods=['GET'])
def get_image():
    try:
        success, frame = take_picture()

        if not success or frame is None:
            return jsonify({"error": "failed to capture image", "code": 500}), 500

        _, buffer = cv2.imencode('.jpg', frame)
        image_base64 = base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            "image": f"data:image/jpeg;base64,{image_base64}",
            "timestamp": time.time()
        })

    except Exception as e:
        return jsonify({"error": str(e), "code": 500}), 500
@app.route('/face-recognition/stop', methods=['GET'])
def stop():
    fr_system.BREAK = True
    time.sleep(1)
    fr_system.BREAK = False
    return jsonify({"message": "System stopped"})


@app.route('/face-recognition/get_status', methods=['GET'])
def get_status():
    with status_lock:
        return jsonify({
            "state": fr_system.status_info["state"],
            "progress": fr_system.status_info["progress"],
            "result": fr_system.last_result
        })


@app.route('/face-recognition/enroll_face', methods=['POST'])
def enroll_face():
    try:
        if fr_system.enroll_face(
                samples=request.json.get('samples', 50),
                name=request.json.get('name', 'newuser')
        ):
            return jsonify({"message": "Enrollment started"})
        return jsonify({"error": "System busy"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/face-recognition/recognize_face', methods=['POST'])
def recognize_face():
    try:
        print("收到识别请求")
        result = fr_system.recognize_face()
        print(f"识别启动结果: {result}")
        if result:
            return jsonify({"message": "Recognition started"})
        return jsonify({"error": "System busy"}), 503
    except Exception as e:
        print(f"识别启动异常: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
