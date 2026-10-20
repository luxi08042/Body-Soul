<script setup>
import {ref} from "vue";
import {useRouter} from "vue-router";
import api from "@/js/http/api.js";
import BlogEditor from "@/views/blog/components/BlogEditor.vue";

const router = useRouter()
const submitting = ref(false)

async function handleSubmit(payload) {
    submitting.value = true
    try {
        const formData = new FormData()
        formData.append('title', payload.title)
        formData.append('content', payload.content)
        formData.append('tags', payload.tags)
        formData.append('is_public', payload.is_public ? 'true' : 'false')
        if (payload.cover_photo) {
            formData.append('cover_photo', payload.cover_photo)
        }

        const res = await api.post('/api/blog/create/', formData)
        if (res.data.result === 'success') {
            router.push({name: 'blog-list'})
        } else {
            alert(res.data.result)
        }
    } finally {
        submitting.value = false
    }
}
</script>

<template>
  <div class="p-4 lg:p-8 w-full">
    <h1 class="text-2xl font-bold mb-6">写博客</h1>
    <BlogEditor :submitting="submitting" @submit="handleSubmit" />
  </div>
</template>

<style scoped>

</style>