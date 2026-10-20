import { createRouter, createWebHistory } from 'vue-router'
import HomepageIndex from "@/views/homepage/HomepageIndex.vue";
import FriendIndex from "@/views/friend/FriendIndex.vue";
import CreateIndex from "@/views/create/CreateIndex.vue";
import NotFoundIndex from "@/views/error/NotFoundIndex.vue";
import LoginIndex from "@/views/user/account/LoginIndex.vue";
import RegisterIndex from "@/views/user/account/RegisterIndex.vue";
import SpaceIndex from "@/views/user/space/SpaceIndex.vue";
import ProfileIndex from "@/views/user/profile/ProfileIndex.vue";
import {useUserStore} from "@/stores/user.js";
import UpdateCharacter from "@/views/create/character/UpdateCharacter.vue";
import BlogList from "@/views/blog/BlogList.vue";
import BlogDetailPage from "@/views/blog/BlogDetailPage.vue";
import BlogCreate from "@/views/blog/BlogCreate.vue";
import MultiAgentChat from "@/views/multiagent/MultiAgentChat.vue";
import MultiAgentIndex from "@/views/multiagent/MultiAgentIndex.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: HomepageIndex,
      name: 'homepage-index',
      meta: {
        needLogin: false,
      },
    },
    {
      path: '/friend/',
      component: FriendIndex,
      name: 'friend-index',
      meta: {
        needLogin: true,
      },
    },
    {
      path: '/create/',
      component: CreateIndex,
      name: 'create-index',
      meta: {
        needLogin: true,
      },
    },
    {
      path: '/create/character/update/:character_id/',
      component: UpdateCharacter,
      name: 'update-character',
      meta: {
        needLogin: true,
      },
    },
    {
      path: '/404/',
      component: NotFoundIndex,
      name: '404',
      meta: {
        needLogin: false,
      },
    },
    {
      path: '/user/account/login/',
      component: LoginIndex,
      name: 'user-account-login-index',
      meta: {
        needLogin: false,
      },
    },
    {
      path: '/user/account/register/',
      component: RegisterIndex,
      name: 'user-account-register-index',
      meta: {
        needLogin: false,
      },
    },
    {
      path: '/user/space/:user_id/',
      component: SpaceIndex,
      name: 'user-space-index',
      meta: {
        needLogin: false,
      },
    },
    {
      path: '/user/profile/',
      component: ProfileIndex,
      name: 'user-profile-index',
      meta: {
        needLogin: true,
      },
    },
    {
      path: '/blog/',
      component: BlogList,
      name: 'blog-list',
      meta: {
        needLogin: false,
      },
    },
    {
      path: '/blog/create/',
      component: BlogCreate,
      name: 'blog-create',
      meta: {
        needLogin: true,
      },
    },
    {
      path: '/blog/detail/:blog_id/',
      component: BlogDetailPage,
      name: 'blog-detail',
      meta: {
        needLogin: false,
      },
    },
    {
      path: '/multiagent/',
      component: MultiAgentIndex,
      name: 'multi-agent-index',
      meta: {
        needLogin: true,
      },
    },
    {
      path: '/multiagent/:room_id/',
      component: MultiAgentChat,
      name: 'multi-agent-room',
      meta: {
        needLogin: true,
      },
    },
    {
      path: '/:pathMatch(.*)*',
      component: NotFoundIndex,
      name: 'not-found',
      meta: {
        needLogin: false,
      },
    },
  ],
})

router.beforeEach((to, from) => {
  const user = useUserStore()
  if (to.meta.needLogin && user.hasPulledUserInfo && !user.isLogin()) {
    return {
      name: 'user-account-login-index'
    }
  }
  return true
})

export default router