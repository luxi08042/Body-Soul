<script setup>
import {onMounted, ref} from "vue";
import {useRoute} from "vue-router";
import api from "@/js/http/api.js";
import BlogDetail from "@/views/blog/BlogDetailContent.vue";

const route = useRoute()
const blog = ref(null)
const loading = ref(true)
const notFound = ref(false)

onMounted(async () => {
    try {
        const res = await api.get(`/api/blog/detail/${route.params.blog_id}/`)
        if (res.data.result === 'success') {
            blog.value = res.data.blog
        } else {
            notFound.value = true
        }
    } finally {
        loading.value = false
    }
})
</script>

<template>
  <div class="p-4 lg:p-8 w-full">
    <div v-if="loading" class="flex justify-center py-20">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <div v-else-if="notFound" class="text-center py-20 opacity-60">
      这篇博客不存在或已被删除
    </div>

    <BlogDetail v-else :blog="blog" />
  </div>
</template>

<style scoped>

</style>