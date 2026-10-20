<script setup>
import {onMounted, ref} from "vue";
import {useRouter} from "vue-router";
import api from "@/js/http/api.js";

const router = useRouter()
const blogs = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await api.get('/api/blog/list/')
    if (res.data.result === 'success') {
      blogs.value = res.data.blogs
    }
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="p-4 lg:p-8 max-w-6xl mx-auto w-full">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">博客</h1>
      <button class="btn btn-primary" @click="router.push({name: 'blog-create'})">
        写博客
      </button>
    </div>

    <div v-if="loading" class="flex justify-center py-20">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <div v-else-if="blogs.length === 0" class="text-center py-20 opacity-60">
      还没有人写过博客，来做第一个吧
    </div>

    <div v-else class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      <div
          v-for="blog in blogs"
          :key="blog.id"
          class="card bg-base-100 shadow-sm hover:shadow-lg transition-shadow cursor-pointer"
          @click="router.push({name: 'blog-detail', params: {blog_id: blog.id}})"
      >
        <figure v-if="blog.cover_photo" class="h-40">
          <img :src="blog.cover_photo" :alt="blog.title" class="w-full object-cover" />
        </figure>
        <div class="card-body">
          <h2 class="card-title text-lg">{{ blog.title }}</h2>
          <div class="flex flex-wrap gap-1">
            <span v-for="tag in blog.tags" :key="tag" class="badge badge-sm badge-outline">{{ tag }}</span>
          </div>
          <div class="flex items-center gap-2 mt-2">
            <img :src="blog.photo" :alt="blog.username" class="w-7 h-7 rounded-full" />
            <span class="text-sm opacity-70">{{ blog.username }}</span>
            <span class="text-sm opacity-50 ml-auto">{{ blog.create_time.slice(0, 10) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>

</style>