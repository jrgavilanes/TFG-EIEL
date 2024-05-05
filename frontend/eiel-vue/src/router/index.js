import { createRouter, createWebHistory } from 'vue-router'

import MapView from '@/views/MapView.vue'
import Login from '@/views/LoginView.vue'
import Main from '@/views/MainView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: Main,
    },
    {
      path: '/login',
      name: 'Login',
      component: Login,
    },
    {
      path: '/map',
      name: 'MapView',
      component: MapView
    },
  ]
})

export default router