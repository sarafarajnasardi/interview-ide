import { createRouter, createWebHistory } from "vue-router"

import HomeView from "../views/HomeView.vue"
import InterviewRoom from "../views/InterviewRoom.vue"

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),

  routes: [
    {
      path: "/",
      name: "home",
      component: HomeView,
    },
    {
      path: "/interview/:roomId",
      name: "interview",
      component: InterviewRoom,
    },
  ],
})

export default router