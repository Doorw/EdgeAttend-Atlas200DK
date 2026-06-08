<template>
  <div class="people-counter">
    <h1>人群照片人数检测</h1>

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
          <span>点击或拖拽上传照片</span>
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
          <div class="result-label">总人数</div>
          <div class="total-count">{{ result.predicted_count }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { uploadImageAndGetCount } from '../services/api'

export default {
  name: 'PeopleCounter',
  setup() {
    const imageFile = ref(null)
    const imagePreview = ref(null)
    const result = ref(null)
    const uploading = ref(false)

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

    const uploadImage = async () => {
      if (!imageFile.value) return

      uploading.value = true
      result.value = null

      try {
        const formData = new FormData()
        formData.append('image', imageFile.value)

        const response = await uploadImageAndGetCount(formData)
        result.value = response
      } catch (error) {
        console.error('上传失败', error)
        alert('上传失败，请重试')
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

    return {
      imageFile,
      imagePreview,
      result,
      uploading,
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
}

.analyze-button {
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 12px 24px;
  font-size: 16px;
  cursor: pointer;
}

.clear-button {
  background-color: #f1f1f1;
  color: #333;
  border: none;
  border-radius: 4px;
  padding: 12px 24px;
  font-size: 16px;
  cursor: pointer;
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
