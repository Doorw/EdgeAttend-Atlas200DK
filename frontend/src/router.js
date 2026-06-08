import { createRouter, createWebHistory } from 'vue-router'
import HomePage from './components/HomePage.vue'
import PeopleCounter from './components/PeopleCounter.vue'
import ClassCounter from './components/ClassCounter.vue'
import FaceEnrollment from './components/FaceEnrollment.vue'
import FaceRecognition from './components/FaceRecognition.vue'
import DataTableCRUD from "@/components/DataTableCRUD.vue";
const routes = [
    { path: '/', component: HomePage },
    { path: '/people-counter', component: PeopleCounter },
    {path: '/class-counter', component: ClassCounter},
    {path: '/face-enrollment', component: FaceEnrollment},
    {path: '/face-recognition', component: FaceRecognition},
    {path: '/data', component: DataTableCRUD}
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
