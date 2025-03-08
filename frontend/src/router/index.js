import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import TextOnImageView from "../views/TextOnImageView.vue"
import GoodsView from "../views/GoodsView.vue"
import CreateProductView from "../views/CreateProductView.vue"
import DownloadFilesView from "../views/DownloadFilesView.vue"




const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/about',
      name: 'about',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/AboutView.vue'),
    },
    {
      path: '/images',
      name: 'images',
      component: TextOnImageView,
    },
    {
      path: '/dev',
      name: 'goods',
      component: GoodsView
    },
    {
      path: '/create_product',
      name: 'productCreation',
      component: CreateProductView
    },
    {
      path: '/files',
      name: 'downloadFiles',
      component: DownloadFilesView
    }
  ],
})


export default router
