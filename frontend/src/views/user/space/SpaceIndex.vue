<script setup>
import UserInfoField from "@/views/user/space/components/UserInfoField.vue";
import BlogCard from "@/views/user/space/components/BlogCard.vue";
import {nextTick, onBeforeUnmount, onMounted, ref, useTemplateRef, watch} from "vue";
import {useRoute, useRouter} from "vue-router";
import api from "@/js/http/api.js";
import Character from "@/components/character/Character.vue";
import {useUserStore} from "@/stores/user.js";

const userProfile = ref(null)
const characters = ref([])
const blogs = ref([])
const isLoading = ref(false)
const hasCharacters = ref(true)
const hasBlogs = ref(true)
const activeTab = ref('character')
const sentinelRef = useTemplateRef('sentinel-ref')
const route = useRoute()
const router = useRouter()
const user = useUserStore()

const pageUserId = () => Number(route.params.user_id)
const isSelf = () => user.id === pageUserId()

function reset() {
  userProfile.value = null
  characters.value = []
  blogs.value = []
  isLoading.value = false
  hasCharacters.value = true
  hasBlogs.value = true
  loadMore()
}

watch(() => route.params.user_id, () => {
  reset()
})

function checkSentinelVisible() {  // 判断哨兵是否能被看到
  if (!sentinelRef.value) return false

  const rect = sentinelRef.value.getBoundingClientRect()
  return rect.top < window.innerHeight && rect.bottom > 0
}

async function loadMore() {
  if (isLoading.value) return

  // 按当前标签页分别判断是否还有更多
  if (activeTab.value === 'character' && !hasCharacters.value) return
  if (activeTab.value === 'blog' && !hasBlogs.value) return

  isLoading.value = true

  let newItems = []
  try {
    if (activeTab.value === 'character') {
      const res = await api.get('/api/create/character/get_list/', {
        params: {
          items_count: characters.value.length,
          user_id: pageUserId(),
        }
      })
      const data = res.data
      if (data.result === 'success') {
        userProfile.value = data.user_profile
        newItems = data.characters
      }
    } else {
      const res = await api.get('/api/blog/user_list/', {
        params: {
          items_count: blogs.value.length,
          user_id: pageUserId(),
        }
      })
      const data = res.data
      if (data.result === 'success') {
        userProfile.value = data.user_profile
        newItems = data.blogs
      }
    }
  } catch (err) {
  } finally {
    isLoading.value = false

    if (newItems.length === 0) {
      if (activeTab.value === 'character') {
        hasCharacters.value = false
      } else {
        hasBlogs.value = false
      }
    } else {
      if (activeTab.value === 'character') {
        characters.value.push(...newItems)
      } else {
        blogs.value.push(...newItems)
      }
      await nextTick()

      if (checkSentinelVisible()) {
        await loadMore()
      }
    }
  }
}

function switchTab(tab) {
  if (activeTab.value === tab) return
  activeTab.value = tab
  // 切到博客时若还没加载过则拉一次
  if (tab === 'blog' && blogs.value.length === 0 && hasBlogs.value) {
    loadMore()
  }
}

let observer = null
onMounted(async () => {
  await loadMore()

  observer = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          loadMore()
        }
      })
    },
    {root: null, rootMargin: '2px', threshold: 0}
  )
  observer.observe(sentinelRef.value)
})

function removeCharacter(characterId) {
  characters.value = characters.value.filter(c => c.id !== characterId)
}

function removeBlog(blogId) {
  blogs.value = blogs.value.filter(b => b.id !== blogId)
}

/**
 * 博客更新后的回调。
 * 后端已返回最新数据时直接就地替换，避免整表重新拉取导致卡片状态错乱；
 * 没有新数据时才退化为整表刷新。
 */
async function refreshBlogs(updatedBlog) {
  if (updatedBlog) {
    const idx = blogs.value.findIndex(b => b.id === updatedBlog.id)
    if (idx !== -1) {
      const next = blogs.value.slice()
      next[idx] = updatedBlog
      blogs.value = next
      return
    }
  }

  const res = await api.get('/api/blog/user_list/', {
    params: {items_count: 0, user_id: pageUserId()}
  })
  if (res.data.result === 'success') {
    blogs.value = res.data.blogs
    hasBlogs.value = res.data.blogs.length > 0
  }
}

onBeforeUnmount(() => {
  observer?.disconnect()
})
</script>

<template>
  <div class="flex flex-col items-center mb-12">
    <UserInfoField :userProfile="userProfile" />

    <div class="flex items-center gap-2 mt-8">
      <button
          class="btn btn-sm"
          :class="activeTab === 'character' ? 'btn-neutral' : 'btn-ghost'"
          @click="switchTab('character')"
      >
        角色
      </button>
      <button
          class="btn btn-sm"
          :class="activeTab === 'blog' ? 'btn-neutral' : 'btn-ghost'"
          @click="switchTab('blog')"
      >
        博客
      </button>
    </div>

    <!-- 角色列表 -->
    <template v-if="activeTab === 'character'">
      <div class="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-9 mt-12 justify-items-center w-full px-9">
        <Character
            v-for="character in characters"
            :key="character.id"
            :character="character"
            :canEdit="true"
            @remove="removeCharacter"
        />
      </div>
      <div v-if="isLoading && characters.length === 0" class="text-gray-500 mt-12">加载中...</div>
      <div v-else-if="!hasCharacters && characters.length === 0" class="text-gray-500 mt-12">
        还没有创建角色
      </div>
    </template>

    <!-- 博客列表 -->
    <template v-else-if="activeTab === 'blog'">
      <div class="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-6 mt-12 w-full px-9">
        <BlogCard
            v-for="blog in blogs"
            :key="blog.id"
            :blog="blog"
            :canEdit="isSelf()"
            @remove="removeBlog"
            @updated="refreshBlogs"
        />
      </div>
      <div v-if="isLoading && blogs.length === 0" class="text-gray-500 mt-12">加载中...</div>
      <div v-else-if="!hasBlogs && blogs.length === 0" class="text-gray-500 mt-12">
        还没有写过博客
      </div>
    </template>

    <div ref="sentinel-ref" class="h-2 mt-8"></div>
    <div v-if="isLoading && (characters.length > 0 || blogs.length > 0)" class="text-gray-500 mt-4">加载中...</div>
    <div v-else-if="!hasCharacters && !hasBlogs" class="text-gray-500 mt-4">没有更多了</div>
  </div>
</template>

<style scoped>

</style>