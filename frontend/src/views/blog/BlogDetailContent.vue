<script setup>
import {computed} from "vue";
import {useRouter} from "vue-router";
import {renderMarkdown} from "@/js/utils/blog_markdown.js";

const props = defineProps(['blog'])
const router = useRouter()

const rendered = computed(() => renderMarkdown(props.blog?.content || ''))

// 路由不存在时不要让整页崩掉
function goToAuthor(userId) {
  try {
    router.push({name: 'user-space-index', params: {user_id: userId}})
  } catch (e) {
    console.warn('跳转到用户空间失败', e)
  }
}
</script>

<template>
  <article v-if="blog" class="max-w-3xl mx-auto w-full">
    <img
        v-if="blog.cover_photo"
        :src="blog.cover_photo"
        :alt="blog.title"
        class="w-full h-64 object-cover rounded-2xl shadow-sm mb-6"
    />

    <h1 class="text-3xl font-bold leading-tight">{{ blog.title }}</h1>

    <div class="flex items-center gap-3 my-5 pb-5 border-b border-base-300">
      <a href="#" @click.prevent="goToAuthor(blog.author_id)">
        <img :src="blog.photo" :alt="blog.username" class="w-10 h-10 rounded-full" />
      </a>
      <div>
        <div class="font-medium">{{ blog.username }}</div>
        <div class="text-sm opacity-60">{{ blog.create_time }}</div>
      </div>
      <div class="flex gap-1 ml-auto">
        <span v-for="tag in blog.tags" :key="tag" class="badge badge-sm badge-outline">{{ tag }}</span>
      </div>
    </div>

    <div class="prose-body" v-html="rendered"></div>
  </article>
</template>

<style scoped>
.prose-body :deep(h1) { font-size: 1.5rem; font-weight: 700; margin-top: 1.5rem; margin-bottom: 0.5rem; }
.prose-body :deep(h2) { font-size: 1.25rem; font-weight: 700; margin-top: 1.25rem; margin-bottom: 0.5rem; }
.prose-body :deep(h3) { font-size: 1.125rem; font-weight: 700; margin-top: 1rem; margin-bottom: 0.5rem; }
.prose-body :deep(p) { margin: 0.5rem 0; line-height: 1.75; }
.prose-body :deep(ul) { list-style: disc; padding-left: 2rem; margin: 0.5rem 0; }
.prose-body :deep(blockquote) {
  border-left: 4px solid var(--color-base-300);
  padding-left: 1rem;
  margin: 0.75rem 0;
  opacity: 0.8;
}
.prose-body :deep(pre) {
  background: var(--color-base-200);
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 1rem 0;
}
.prose-body :deep(code) {
  background: var(--color-base-200);
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
}
.prose-body :deep(a) {
  color: var(--color-primary);
  text-decoration: underline;
}
.prose-body :deep(img) {
  max-width: 100%;
  border-radius: 0.5rem;
  margin: 0.5rem 0;
}
</style>