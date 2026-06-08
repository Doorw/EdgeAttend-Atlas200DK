<template>
  <div class="face-recognition-container">
    <!-- 操作按钮区域 -->
    <div class="control-section">
      <button
        @click="startRecognition"
        :disabled="isRecognizing"
        class="action-btn"
      >
        {{ isRecognizing ? "识别中..." : "开始人脸识别" }}
      </button>
      <button @click="stop" class="action-btn">
        停止识别
      </button>
    </div>

    <!-- 视频展示区域 -->
    <div class="video-section">
      <div class="video-wrapper">
        <img
          :src="currentFrame"
          alt="实时视频流"
          class="video-frame"
          v-if="currentFrame"
        />
        <div v-else class="loading-prompt">摄像头初始化中...</div>
      </div>
    </div>

    <!-- 识别结果展示 -->
    <div class="result-section">
      <h3>识别结果：</h3>
      <div class="result-box">
        {{ recognitionResult || "等待识别结果..." }}
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "FaceRecognition",
  data() {
    return {
      apiBaseUrl: "http://localhost:5000",
      isRecognizing: false, // 识别状态
      currentFrame: null, // 当前帧Base64数据
      recognitionResult: "", // 识别结果
      frameInterval: null, // 帧更新定时器
      statusInterval: null, // 状态轮询定时器
    };
  },
  mounted() {
    // 启动视频帧更新
    this.startFrameUpdate();
    this.startStatusPolling();
  },
  methods: {
    async startRecognition() {
      try {
        this.isRecognizing = true;
        this.recognitionResult = "正在启动识别...";

        // 1. 启动识别流程
        const response = await axios.post(
          `${this.apiBaseUrl}/face-recognition/recognize_face`
        );

        if (response.data.message === "Recognition started") {
          this.recognitionResult = "识别已启动";
          // 2. 启动帧更新
          this.startFrameUpdate();
          // 3. 启动状态轮询
          this.startStatusPolling();
        } else {
          this.recognitionResult = response.data.error || "启动识别失败";
          this.isRecognizing = false;
          this.stopPolling();
        }
      } catch (error) {
        this.handleError(error);
      }
    },
    async stop() {
      try {
        // 1. 停止识别流程
        const response = await axios.get(
          `${this.apiBaseUrl}/face-recognition/stop`
        );

        if (response.status === 200) {
          this.recognitionResult = "识别已停止";
          this.isRecognizing = false;
          this.stopPolling();
        } else {
          throw new Error("停止识别失败");
        }
      } catch (error) {
        this.handleError(error);
      }
    },
    // 启动视频帧更新
   startFrameUpdate() {
     
      this.frameInterval = setInterval(async () => {
        try {
          const response = await axios.get(
            `${this.apiBaseUrl}/face-recognition/get_image`
          );
          if (response.data && response.data.image) {
            this.currentFrame = response.data.image;
          }
          console.log("获取图片成功");
        } catch (error) {
          console.error("帧获取失败:", error);
        }
      }, 2000); // 2000ms获取一次帧
    },

    // 启动状态轮询
    startStatusPolling() {
      this.statusInterval = setInterval(async () => {
        try {
          const response = await axios.get(
            `${this.apiBaseUrl}/face-recognition/get_status`
          );
          const state = response.data.state;
          const result = response.data.result;
          if (result) {
            this.recognitionResult = result;
          } else if (state) {
            this.recognitionResult = this.formatResult(state);
          }
          // 识别完成或未运行时停止轮询
          if (state !== "recognizing" && state !== "enrolling") {
            this.stopPolling();
          }
        } catch (error) {
          console.error("状态获取失败:", error);
        }
      }, 2000); // 秒轮询一次
    },

    // 格式化识别结果
    formatResult(result) {
      const resultMap = {
        idle: "空闲中，识别未开始",
        recognizing: "识别中",
        enrolling: "录入中",
        no_face_detected: "未检测到人脸",
        recognition_error: "识别错误",
      };
      return resultMap[result] || result;
    },

    // 停止所有轮询
    stopPolling() {
      clearInterval(this.frameInterval);
      clearInterval(this.statusInterval);
      this.isRecognizing = false;
    },

    // 错误处理
    handleError(error) {
      console.error("请求错误:", error);
      const serverMessage =
        error.response?.data?.error ||
        error.response?.data?.message ||
        error.message ||
        "识别服务不可用";
      this.recognitionResult = serverMessage;
      this.isRecognizing = false;
      this.stopPolling();
    },
  },
  beforeUnmount() {
    // 组件销毁前清理定时器
    this.stopPolling();
  },
};
</script>

<style scoped>
.face-recognition-container {
  max-width: 800px;
  margin: 2rem auto;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.control-section {
  text-align: center;
  margin-bottom: 2rem;
}

.action-btn {
  padding: 12px 24px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s;
  margin: 0 5px; /* 添加间距 */
}

.action-btn:disabled {
  background: #a0cfff;
  cursor: not-allowed;
}

.action-btn:hover:not(:disabled) {
  background: #79bbff;
}

.video-section {
  margin-bottom: 2rem;
}

.video-wrapper {
  width: 100%;
  height: 400px;
  background: #000;
  border-radius: 4px;
  overflow: hidden;
}

.video-frame {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.loading-prompt {
  color: white;
  text-align: center;
  line-height: 400px;
}

.result-section h3 {
  color: #606266;
  margin-bottom: 1rem;
}

.result-box {
  min-height: 60px;
  padding: 1rem;
  background: white;
  border-radius: 4px;
  border: 1px solid #ebeef5;
  font-size: 1.2rem;
  color: #303133;
}
</style>
