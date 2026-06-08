<template>
  <div class="people-counter">
    <h1>教室到课人数/缺勤率统计</h1>

    <div class="class-selector">
      <label for="class-select">选择班级:</label>
      <select
          id="class-select"
          v-model="selectedClassId"
          :disabled="fetchingClasses"
          class="class-select"
      >
        <option value="">请选择班级</option>
        <option
            v-for="cls in classes"
            :key="cls.id"
            :value="cls.id"
        >
          {{ cls.class_name }} ({{ cls.teacher }})
        </option>
      </select>
      <span v-if="fetchingClasses" class="loading">加载中...</span>
    </div>

    <div class="upload-area" @dragover.prevent @drop.prevent="handleDrop">
      <div v-if="!imagePreview" class="upload-placeholder">
        <input
            type="file"
            accept="image/*"
            @change="handleFileChange"
            ref="fileInput"
            class="file-input"
        />
        <div class="upload-button" @click="openFileInput">
          <i class="upload-icon">📁</i>
          <span>点击或拖拽上传教室全景拍摄图片</span>
        </div>
      </div>

      <div v-else class="preview-container">
        <img :src="imagePreview" alt="预览图" class="preview-image" />
        <div class="preview-actions">
          <button @click="uploadImage" :disabled="uploading" class="analyze-button">
            {{ uploading ? '分析中...' : '开始分析' }}
          </button>
          <button @click="clearImage" class="clear-button">清除</button>
        </div>
      </div>
    </div>

    <div v-if="result" class="result-container">
      <h2>分析结果</h2>
      <div class="result-content">
        <div class="result-card">
          <div class="result-label">出勤总人数(估计值)</div>
          <div class="total-count">{{ result.predicted_count }}</div>
        </div>
        <div class="result-card">
          <div class="result-label">班级总人数</div>
          <div class="total-count">{{ result.student_num }}</div>
        </div>
        <div class="result-card">
          <div class="result-label">出勤率:</div>
          <div class="total-count">{{ result.attend_ratio }}%</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'PeopleCounter',
  setup() {
    // 图片相关状态
    const imageFile = ref(null)
    const imagePreview = ref(null)
    const result = ref(null)
    const uploading = ref(false)

    // 班级相关状态
    const classes = ref([])
    const selectedClassId = ref('')
    const fetchingClasses = ref(false)

    // 获取班级列表
    const loadClasses = async () => {
      fetchingClasses.value = true
      try {
        const response = await fetch('http://localhost:5000/classes')
        if (!response.ok) throw new Error('加载失败')
        classes.value = await response.json()
      } catch (error) {
        console.error('加载班级失败:', error)
        alert('班级列表加载失败')
      } finally {
        fetchingClasses.value = false
      }
    }

    // 文件处理方法保持不变
    const handleFileChange = (e) => {
      const file = e.target.files[0]
      if (file) {
        loadImagePreview(file)
      }
    }

    const handleDrop = (e) => {
      const file = e.dataTransfer.files[0]
      if (file && file.type.startsWith('image/')) {
        loadImagePreview(file)
      }
    }

    const openFileInput = () => {
      document.querySelector('.file-input').click()
    }

    const loadImagePreview = (file) => {
      imageFile.value = file
      const reader = new FileReader()
      reader.onload = (e) => {
        imagePreview.value = e.target.result
      }
      reader.readAsDataURL(file)
    }

    // 修改后的上传方法
    const uploadImage = async () => {
      if (!imageFile.value) return
      if (!selectedClassId.value) {
        alert('请先选择班级')
        return
      }

      uploading.value = true
      result.value = null

      try {
        const formData = new FormData()
        formData.append('image', imageFile.value)
        formData.append('class_id', selectedClassId.value)

        const response = await fetch('http://localhost:5000/api/predict_class', {
          method: 'POST',
          body: formData
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || '分析失败')
        }

        result.value = await response.json()
      } catch (error) {
        console.error('上传失败', error)
        alert(error.message || '分析失败，请重试')
      } finally {
        uploading.value = false
      }
    }

    const clearImage = () => {
      imageFile.value = null
      imagePreview.value = null
      result.value = null
      document.querySelector('.file-input').value = ''
    }

    // 组件加载时获取班级列表
    onMounted(() => {
      loadClasses()
    })

    return {
      imageFile,
      imagePreview,
      result,
      uploading,
      classes,
      selectedClassId,
      fetchingClasses,
      handleFileChange,
      handleDrop,
      openFileInput,
      uploadImage,
      clearImage
    }
  }
}
</script>

<style scoped>
.people-counter {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px 20px;
}

h1 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}

.class-selector {
  margin-bottom: 30px;
  display: flex;
  align-items: center;
  gap: 15px;
}

.class-select {
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #ddd;
  min-width: 300px;
  font-size: 16px;
}

.loading {
  color: #666;
  font-size: 0.9em;
}

.upload-area {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  margin-bottom: 30px;
  cursor: pointer;
  transition: border-color 0.3s;
}

.upload-area:hover {
  border-color: #666;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.file-input {
  display: none;
}

.upload-button {
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 12px 24px;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.upload-button:hover {
  background-color: #389f75;
}

.preview-container {
  position: relative;
}

.preview-image {
  max-width: 100%;
  max-height: 500px;
  object-fit: contain;
  background-color: #fafafa;
  border-radius: 4px;
}

.preview-actions {
  margin-top: 16px;
  display: flex;
  gap: 16px;
  justify-content: center;
}

.analyze-button {
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 12px 24px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.analyze-button:disabled {
  background-color: #a0d1b2;
  cursor: not-allowed;
}

.clear-button {
  background-color: #f1f1f1;
  color: #333;
  border: none;
  border-radius: 4px;
  padding: 12px 24px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.clear-button:hover {
  background-color: #e0e0e0;
}

.result-container {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 24px;
  margin-top: 40px;
}

.result-container h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #333;
}

.result-content {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.result-card {
  background-color: white;
  border-radius: 4px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.result-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.total-count {
  font-size: 24px;
  font-weight: bold;
  color: #42b983;
}
</style>
