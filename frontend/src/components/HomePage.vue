<template>
  <div class="home-page">
    <h1>功能列表</h1>
    <p>By 2023212042 庄则栋  2023211972 张容祥</p>
    <div class="function-list">
      <div class="function-item" @click="goToPeopleCounter">
        <h2>人群照片人数检测</h2>
        <p>上传照片，智能识别照片中的人数</p>
      </div>
      <div class="function-item" @click="goToClassCounter">
        <h2>班级出勤率检测</h2>
        <p>上传教室照片，智能统计出勤人数和出勤率</p>
      </div>
      <div class="function-item" @click="goToFaceRecognition">
        <h2>人脸识别</h2>
        <p>正对摄像头，识别身份</p>
      </div>
      <div class="function-item" @click="goToFaceEnrollment">
        <h2>人脸录入</h2>
        <p>正对摄像头，录入人脸</p>
      </div>
      <div class="function-item" @click="goToData">
        <h2>数据管理</h2>
        <p>管理教学班级信息, 学生信息和选课信息</p>
      </div>
    </div>
  </div>
</template>

<script>
import { useRouter } from "vue-router";

export default {
  name: "HomePage",
  setup() {
    const router = useRouter();

    const goToPeopleCounter = () => {
      router.push("/people-counter");
    };
    const goToClassCounter = () => {
      router.push("/class-counter");
    };

    const goToFaceRecognition = () => {
      router.push("/face-recognition");
    };

    const goToFaceEnrollment = () => {
      router.push("/face-enrollment");
    };

    const goToData = () => {
      router.push("/data");
    };

    return {
      goToPeopleCounter,
      goToClassCounter,
      goToFaceRecognition,
      goToFaceEnrollment,
      goToData
    };
  },
};
</script>

<style scoped>
.home-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px 20px;
  text-align: center;
}

.function-list {
  margin-top: 40px;
}

.function-item {
  background-color: #f5f5f5;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 16px;
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
}

.function-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.function-item h2 {
  margin-bottom: 10px;
  color: #333;
}

.function-item p {
  color: #666;
  font-size: 16px;
}
</style>
