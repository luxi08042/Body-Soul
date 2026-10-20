<script setup>
import NavBar from "@/components/navbar/NavBar.vue";
import {onErrorCaptured, onMounted, ref} from "vue";
import {useUserStore} from "@/stores/user.js";
import api from "@/js/http/api.js";
import {useRoute, useRouter} from "vue-router";

const user = useUserStore()
const route = useRoute()
const router = useRouter()
const pageError = ref('')

// 捕获子组件渲染错误，避免整页白屏看不到原因
onErrorCaptured((err) => {
  console.error('[页面渲染出错]', err)
  pageError.value = err?.message || String(err)
  return false
})

onMounted(async () => {
  try {
    const res = await api.get('/api/user/account/get_user_info/')
    const data = res.data
    if (data.result === 'success') {
      user.setUserInfo(data)
    }
  } catch (err) {
  } finally {
    user.setHasPulledUserInfo(true)

    if (route.meta.needLogin && !user.isLogin()) {
      await router.replace({
        name: 'user-account-login-index',
      })
    }
  }
})
</script>

<template>
  <div>
    <div v-if="pageError" class="alert alert-error m-4 text-sm">
      页面出错：{{ pageError }}
      <button class="btn btn-xs" @click="pageError = ''">关闭</button>
    </div>
    <NavBar>
      <RouterView />
    </NavBar>
  </div>
</template>

<style scoped>

</style>
