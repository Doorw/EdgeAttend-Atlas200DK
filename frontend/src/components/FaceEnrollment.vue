<template>
  <div class="container">
    <div class="preview-box">
      <img
        :src="imageSrc"
        class="preview-image"
        alt="摄像头画面"
        v-if="imageSrc"
      />
      <div v-else class="loading">摄像头加载中...</div>
    </div>

    <div class="control-box">
      <div class="input-group">
        <input
          type="text"
          v-model="userName"
          placeholder="请输入您的姓名"
          class="name-input"
          :disabled="isEnrolling"
        />
      </div>

      <div class="button-group">
        <button
          class="action-btn enroll-btn"
          :class="{ disabled: isEnrolling || !userName }"
          @click="startEnrollment"
          :disabled="isEnrolling || !userName"
        >
          {{ isEnrolling ? "录入中..." : "开始人脸录入" }}
        </button>
        <button
          class="action-btn stop-btn"
          @click="stop"
          :disabled="!isEnrolling"
        >
          停止识别
        </button>
      </div>

      <div class="progress-container" v-if="isEnrolling">
        <div class="progress-bar" :style="{ width: progress + '%' }"></div>
        <span class="progress-text">{{ progress.toFixed(1) }}%</span>
      </div>

      <div class="status-message" v-if="statusMessage">
        {{ statusMessage }}
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  data() {
    return {
      userName: "",
      imageSrc: null,
      isEnrolling: false,
      progress: 0,
      statusMessage: "",
      imageInterval: null,
      statusInterval: null,
    };
  },
  mounted() {
    this.startImagePolling();
  },
  beforeDestroy() {
    clearInterval(this.imageInterval);
    clearInterval(this.statusInterval);
  },
  methods: {
    // 开始人脸录入
    async startEnrollment() {
      try {
        this.isEnrolling = true;
        this.progress = 0;
        this.statusMessage = "正在启动录入流程...";

        // 调用后端接口
        const response = await fetch(
          "http://localhost:5000/face-recognition/enroll_face",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ samples: 50, name: this.userName }),
          }
        );

        if (!response.ok) throw new Error("请求失败");

        this.statusMessage = "请保持正对摄像头...";
        this.startStatusPolling();
      } catch (error) {
        this.statusMessage = `录入失败: ${error.message}`;
        this.isEnrolling = false;
      }
    },
    async stop() {
      try {
        // 停止识别流程
        const response = await axios.get(
          "http://localhost:5000/face-recognition/stop"
        );

        if (response.status === 200) {
          this.statusMessage = "识别已停止";
          this.isEnrolling = false;
          clearInterval(this.statusInterval);
        } else {
          throw new Error("停止请求失败");
        }
      } catch (error) {
        this.handleError(error);
      }
    },
    // 启动画面轮询
    startImagePolling() {
      this.imageInterval = setInterval(async () => {
        try {
          const response = await fetch(
            "http://localhost:5000/face-recognition/get_image"
          );

          // 添加响应类型校验
          const contentType = response.headers.get("content-type");
          if (!contentType || !contentType.includes("application/json")) {
            throw new Error("Invalid response type");
          }

          const data = await response.json();

          // 添加数据有效性校验
          if (!data.image?.startsWith("data:image/jpeg;base64")) {
            throw new Error("Invalid image data");
          }

          this.imageSrc = data.image;
        } catch (error) {
          console.error("画面获取失败:", error);
          this.imageSrc = null; // 清空无效图像
        }
      }, 2000);
    },

    // 启动状态轮询
    startStatusPolling() {
      this.statusInterval = setInterval(async () => {
        try {
          const response = await fetch(
            "http://localhost:5000/face-recognition/get_status"
          );
          const status = await response.json();

          this.progress = status.progress * 100;

          if (status.state === "idle") {
            clearInterval(this.statusInterval);
            this.isEnrolling = false;
            if (status.result === "enroll_success") {
              this.statusMessage = "录入成功!";
            } else {
              this.statusMessage = "录入未完成";
            }
          }
        } catch (error) {
          console.error("状态获取失败:", error);
          clearInterval(this.statusInterval);
          this.isEnrolling = false;
          this.statusMessage = "状态查询失败";
        }
      }, 2000); // 每1秒检查一次状态
    },
    handleError(error) {
      this.statusMessage = `操作失败: ${error.message}`;
      this.isEnrolling = false;
      clearInterval(this.statusInterval);
    },
  },
};
</script>

<style scoped>
.container {
  max-width: 800px;
  margin: 2rem auto;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 10px;
}

.preview-box {
  width: 100%;
  height: 400px;
  background: #333;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.loading {
  color: white;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.control-box {
  margin-top: 1.5rem;
}

.input-group {
  margin-bottom: 1rem;
}

.name-input {
  width: 100%;
  padding: 12px;
  border: 2px solid #2196f3;
  border-radius: 5px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.name-input:focus {
  outline: none;
  border-color: #1976d2;
}

.button-group {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.action-btn {
  padding: 12px 24px;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.enroll-btn {
  background: #2196f3;
}

.enroll-btn:hover:not(.disabled) {
  background: #1976d2;
}

.stop-btn {
  background: #f44336;
}

.stop-btn:hover:not(.disabled) {
  background: #d32f2f;
}

.action-btn.disabled {
  background: #9e9e9e;
  cursor: not-allowed;
}

.progress-container {
  margin-top: 1rem;
  height: 24px;
  background: #ddd;
  border-radius: 12px;
  position: relative;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: #4caf50;
  transition: width 0.3s ease;
}

.progress-text {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-weight: bold;
}

.status-message {
  margin-top: 1rem;
  color: #666;
  font-size: 0.9em;
  text-align: center;
}
</style>
