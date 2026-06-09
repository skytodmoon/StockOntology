import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Dashboard',
      component: () => import('@/views/Dashboard.vue'),
    },
    {
      path: '/graph',
      name: 'Graph',
      component: () => import('@/views/GraphView.vue'),
    },
    {
      path: '/analysis',
      name: 'Analysis',
      component: () => import('@/views/Analysis.vue'),
    },
    {
      path: '/prediction',
      name: 'Prediction',
      component: () => import('@/views/Prediction.vue'),
    },
    {
      path: '/events',
      name: 'Events',
      component: () => import('@/views/Events.vue'),
    },
    {
      path: '/company/:code',
      name: 'CompanyDetail',
      component: () => import('@/views/CompanyDetail.vue'),
    },
  ],
})

export default router
