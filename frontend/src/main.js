import { createApp } from 'vue'
import App from './App.vue'
import { createRouter, createWebHistory } from 'vue-router'
import HelloWorld from './components/HelloWorld.vue'
import ReadingPlan from './components/ReadingPlan.vue'
import './assets/pixel-theme.css'

const routes = [
  { path: '/', component: HelloWorld },
  { path: '/plan', component: ReadingPlan }
]
const router = createRouter({
  history: createWebHistory(),
  routes
})

createApp(App).use(router).mount('#app')
