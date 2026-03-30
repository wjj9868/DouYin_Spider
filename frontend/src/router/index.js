import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/works' },
  { path: '/works', component: () => import('@/views/Works.vue') },
  { path: '/users', component: () => import('@/views/Users.vue') },
  { path: '/search', component: () => import('@/views/Search.vue') },
  { path: '/followers', component: () => import('@/views/Followers.vue') },
  { path: '/comments', component: () => import('@/views/Comments.vue') },
  { path: '/live', component: () => import('@/views/Live.vue') },
  { path: '/tasks', component: () => import('@/views/Tasks.vue') },
  { path: '/scheduled-tasks', component: () => import('@/views/ScheduledTasks.vue') },
  { path: '/settings', component: () => import('@/views/Settings.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
