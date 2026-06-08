<template>
  <div class="management-container">
    <!-- 班级管理 -->
    <div class="section">
      <h2>班级管理</h2>
      <div class="form-group">
        <input v-model="classForm.class_name" placeholder="班级名称">
        <input v-model="classForm.teacher" placeholder="任课教师">
        <input v-model="classForm.student_num" placeholder="班级学生总数">
        <button
            @click="isEditingClass ? updateClass() : createClass()"
            class="action-btn"
        >
          {{ isEditingClass ? '更新班级' : '创建班级' }}
        </button>
      </div>
      <table>
        <thead>
        <tr>
          <th>ID</th>
          <th>班级名称</th>
          <th>班主任</th>
          <th>学生人数</th>
          <th>操作</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="cls in classes" :key="cls.id">
          <td>{{ cls.id }}</td>
          <td>{{ cls.class_name }}</td>
          <td>{{ cls.teacher }}</td>
          <td>{{ cls.student_num }}</td>
          <td>
            <button @click="editClass(cls)" class="action-btn edit-btn">编辑</button>
            <button @click="deleteClass(cls.id)" class="action-btn delete-btn">删除</button>
          </td>
        </tr>
        </tbody>
      </table>
    </div>

    <!-- 学生管理 -->
    <div class="section">
      <h2>学生管理</h2>
      <div class="form-group">
        <input v-model="studentForm.name" placeholder="学生姓名">
        <button
            @click="isEditingStudent ? updateStudent() : createStudent()"
            class="action-btn"
        >
          {{ isEditingStudent ? '更新学生' : '添加学生' }}
        </button>
      </div>
      <table>
        <thead>
        <tr>
          <th>ID</th>
          <th>姓名</th>
          <th>操作</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="student in students" :key="student.id">
          <td>{{ student.id }}</td>
          <td>{{ student.name }}</td>
          <td>
            <button @click="editStudent(student)" class="action-btn edit-btn">编辑</button>
            <button @click="deleteStudent(student.id)" class="action-btn delete-btn">删除</button>
          </td>
        </tr>
        </tbody>
      </table>
    </div>

    <!-- 选课管理 -->
    <div class="section">
      <h2>选课管理</h2>
      <div class="form-group">
        <input v-model="enrollmentForm.student_id" type="number" placeholder="学生ID">
        <input v-model="enrollmentForm.class_id" type="number" placeholder="班级ID">
        <button
            @click="isEditingEnrollment ? updateEnrollment() : createEnrollment()"
            class="action-btn"
        >
          {{ isEditingEnrollment ? '更新选课' : '添加选课' }}
        </button>
      </div>
      <table>
        <thead>
        <tr>
          <th>记录ID</th>
          <th>学生姓名</th>
          <th>班级名称</th>
          <th>操作</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="enroll in enrollments" :key="enroll.id">
          <td>{{ enroll.id }}</td>
          <td>{{ enroll.student }}</td>
          <td>{{ enroll.class_name }}</td>
          <td>
            <button @click="editEnrollment(enroll)" class="action-btn edit-btn">编辑</button>
            <button @click="deleteEnrollment(enroll.id)" class="action-btn delete-btn">删除</button>
          </td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

// 班级管理
const classes = ref([])
const classForm = ref({
  id: null,
  class_name: '',
  teacher: '',
  student_num: ''
})
const isEditingClass = ref(false)

// 学生管理
const students = ref([])
const studentForm = ref({ id: null, name: '' })
const isEditingStudent = ref(false)

// 选课管理
const enrollments = ref([])
const enrollmentForm = ref({
  id: null,
  student_id: '',
  class_id: ''
})
const isEditingEnrollment = ref(false)

// 通用数据获取
const fetchData = async () => {
  try {
    const [clsRes, stuRes, enrRes] = await Promise.all([
      axios.get('http://localhost:5000/classes'),
      axios.get('http://localhost:5000/students'),
      axios.get('http://localhost:5000/enrollments')
    ])
    classes.value = clsRes.data
    students.value = stuRes.data
    enrollments.value = enrRes.data
  } catch (error) {
    console.error('数据加载失败:', error)
  }
}

// 班级操作
const createClass = async () => {
  try {
    await axios.post('http://localhost:5000/classes', classForm.value)
    await fetchData()
    resetClassForm()
  } catch (error) {
    console.error('班级创建失败:', error)
  }
}

const updateClass = async () => {
  try {
    await axios.put(`http://localhost:5000/classes/${classForm.value.id}`, classForm.value)
    await fetchData()
    resetClassForm()
  } catch (error) {
    console.error('班级更新失败:', error)
  }
}

const editClass = (cls) => {
  classForm.value = { ...cls }
  isEditingClass.value = true
}

const deleteClass = async (id) => {
  try {
    await axios.delete(`http://localhost:5000/classes/${id}`)
    await fetchData()
  } catch (error) {
    console.error('班级删除失败:', error)
  }
}

// 学生操作
const createStudent = async () => {
  try {
    await axios.post('http://localhost:5000/students', studentForm.value)
    await fetchData()
    resetStudentForm()
  } catch (error) {
    console.error('学生创建失败:', error)
  }
}

const updateStudent = async () => {
  try {
    await axios.put(`http://localhost:5000/students/${studentForm.value.id}`, studentForm.value)
    await fetchData()
    resetStudentForm()
  } catch (error) {
    console.error('学生更新失败:', error)
  }
}

const editStudent = (student) => {
  studentForm.value = { ...student }
  isEditingStudent.value = true
}

const deleteStudent = async (id) => {
  try {
    await axios.delete(`http://localhost:5000/students/${id}`)
    await fetchData()
  } catch (error) {
    console.error('学生删除失败:', error)
  }
}

// 选课操作
const createEnrollment = async () => {
  try {
    await axios.post('http://localhost:5000/enrollments', {
      student_id: parseInt(enrollmentForm.value.student_id),
      class_id: parseInt(enrollmentForm.value.class_id)
    })
    await fetchData()
    resetEnrollmentForm()
  } catch (error) {
    console.error('选课失败:', error)
  }
}

const updateEnrollment = async () => {
  try {
    await axios.put(`http://localhost:5000/enrollments/${enrollmentForm.value.id}`, {
      student_id: parseInt(enrollmentForm.value.student_id),
      class_id: parseInt(enrollmentForm.value.class_id)
    })
    await fetchData()
    resetEnrollmentForm()
  } catch (error) {
    console.error('选课更新失败:', error)
  }
}

const editEnrollment = (enroll) => {
  enrollmentForm.value = {
    id: enroll.id,
    student_id: enroll.student_id,
    class_id: enroll.class_id
  }
  isEditingEnrollment.value = true
}

const deleteEnrollment = async (id) => {
  try {
    await axios.delete(`http://localhost:5000/enrollments/${id}`)
    await fetchData()
  } catch (error) {
    console.error('选课删除失败:', error)
  }
}

// 表单重置
const resetClassForm = () => {
  classForm.value = { id: null, class_name: '', teacher: '', student_num: '' }
  isEditingClass.value = false
}

const resetStudentForm = () => {
  studentForm.value = { id: null, name: '' }
  isEditingStudent.value = false
}

const resetEnrollmentForm = () => {
  enrollmentForm.value = { id: null, student_id: '', class_id: '' }
  isEditingEnrollment.value = false
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.management-container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 20px;
}

.section {
  margin-bottom: 3rem;
  padding: 1.5rem;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

h2 {
  color: #2c3e50;
  margin-bottom: 1.5rem;
}

.form-group {
  display: flex;
  gap: 10px;
  margin-bottom: 1.5rem;
}

input {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

th {
  background-color: #f8f9fa;
  font-weight: 500;
}

.action-btn {
  padding: 8px 16px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  margin: 2px;
}

.edit-btn {
  background: #67c23a;
}

.delete-btn {
  background: #f56c6c;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}

.edit-btn:hover {
  background: #85ce61;
}

.delete-btn:hover {
  background: #f78989;
}

.action-btn:active {
  transform: translateY(0);
}
</style>
